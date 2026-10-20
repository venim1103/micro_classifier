"""A deterministic NumPy planar rover simulator with circular obstacles.

Distances are meters; angles are radians; body axes are forward/left/up.
The 8x8 ToF grid uses synthetic point rays, not a VL53L8CX device model.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import deque
from dataclasses import asdict, dataclass
from fractions import Fraction
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class Config:
    dt: float = 0.05
    radius: float = 0.18
    max_speed: float = 0.6
    acceleration: float = 1.0
    max_turn_rate: float = 1.5
    field_of_view: float = math.pi / 4
    max_range: float = 4.0
    noise_std: float = 0.02
    dropout: float = 0.02
    latency_ticks: int = 2
    history_ticks: int = 8
    max_ticks: int = 400
    goal_tolerance: float = 0.25
    tick_cost: float = 0.01
    success_reward: float = 10.0
    collision_cost: float = 10.0
    tof_rate_hz: float | None = 15.0
    tof_mount_height: float | None = 0.15
    tof_mount_pitch: float = 0.0
    obstacle_height: float = 0.5
    wall_height: float = 1.0
    odometry_position_error: float = 0.0
    odometry_heading_error: float = 0.0
    odometry_latency_ticks: int = 0

    @classmethod
    def from_record(cls, record):
        """Preserve acquisition and planar geometry for older stored configs."""
        return cls(
            **{
                **record,
                "tof_rate_hz": record.get("tof_rate_hz"),
                "tof_mount_height": record.get("tof_mount_height"),
            }
        )

    def __post_init__(self):
        for name, value in asdict(self).items():
            if name in ("tof_rate_hz", "tof_mount_height") and value is None:
                continue
            try:
                finite = (
                    not isinstance(value, bool)
                    and isinstance(value, (int, float))
                    and math.isfinite(value)
                )
            except OverflowError:
                finite = False
            if not finite:
                raise ValueError(f"{name} must be finite")
        if self.tof_rate_hz is not None and not 0 < self.tof_rate_hz <= 15:
            raise ValueError(
                "8x8 ToF rate must be in (0, 15] Hz or None for legacy replay"
            )
        if self.tof_mount_height is not None and self.tof_mount_height <= 0:
            raise ValueError("ToF mounting height must be positive or None for replay")
        if abs(self.tof_mount_pitch) >= math.pi / 2:
            raise ValueError("ToF mounting pitch must be between -pi/2 and pi/2")
        if not 0 <= self.odometry_heading_error <= math.pi:
            raise ValueError("odometry heading error must be in [0, pi]")
        positive = (
            "dt",
            "radius",
            "max_speed",
            "acceleration",
            "max_turn_rate",
            "max_range",
            "goal_tolerance",
            "obstacle_height",
            "wall_height",
        )
        if any(getattr(self, name) <= 0 for name in positive):
            raise ValueError("time, geometry and motion limits must be positive")
        if not 0 < self.field_of_view < math.pi or not 0 <= self.dropout <= 1:
            raise ValueError("invalid sensor field of view or dropout probability")
        if (
            min(
                self.noise_std,
                self.tick_cost,
                self.success_reward,
                self.collision_cost,
                self.odometry_position_error,
            )
            < 0
        ):
            raise ValueError("noise and reward magnitudes must be nonnegative")
        for name in (
            "latency_ticks",
            "history_ticks",
            "max_ticks",
            "odometry_latency_ticks",
        ):
            value = getattr(self, name)
            if type(value) is not int or value < (
                0 if name in ("latency_ticks", "odometry_latency_ticks") else 1
            ):
                raise ValueError(f"invalid {name}")


@dataclass(frozen=True)
class Scenario:
    name: str = "clear"
    bounds: tuple[float, float] = (6.0, 6.0)
    start: tuple[float, float, float] = (1.0, 3.0, 0.0)
    goal: tuple[float, float] = (5.0, 3.0)
    obstacles: tuple[tuple[float, float, float], ...] = ()
    obstacle_heights: tuple[float, ...] = ()

    def validate(self, config):
        if len(self.bounds) != 2 or len(self.start) != 3 or len(self.goal) != 2:
            raise ValueError("invalid scenario dimensions")
        values = [*self.bounds, *self.start, *self.goal]
        if self.obstacle_heights and (
            len(self.obstacle_heights) != len(self.obstacles)
            or any(
                isinstance(height, bool)
                or not isinstance(height, (int, float))
                or height <= 0
                for height in self.obstacle_heights
            )
        ):
            raise ValueError("obstacle heights must match obstacles and be positive")
        values.extend(self.obstacle_heights)
        for obstacle in self.obstacles:
            if len(obstacle) != 3 or obstacle[2] <= 0:
                raise ValueError("obstacles require x, y and a positive radius")
            values.extend(obstacle)
        if not np.isfinite(values).all() or min(self.bounds) <= 2 * config.radius:
            raise ValueError("invalid scenario geometry")
        for point in (self.start[:2], self.goal):
            if swept_collision(
                point, point, config.radius, self.obstacles, self.bounds
            ):
                raise ValueError("start or goal is not in free space")


class RoverEnv:
    """Trainer API: reset -> (observation, info); step -> obs, reward, done, timeout, info.

    Observations contain only ego-state, body-frame goal, delayed noisy ToF and
    history. World geometry and true pose are separated in info for diagnostics.
    Actions are desired forward speed in m/s and turn rate in rad/s.
    """

    def __init__(self, config=None, scenario=None):
        self.config = config or Config()
        self.scenario = scenario or Scenario()
        self.scenario.validate(self.config)
        self.reset()

    def reset(self, *, seed=0):
        self.rng = np.random.default_rng(seed)
        self.odometry_rng = np.random.default_rng(
            np.random.SeedSequence(seed).spawn(1)[0]
        )
        self.seed = seed
        self.tick = 0
        self.position = np.array(self.scenario.start[:2], dtype=np.float64)
        self.yaw = self.scenario.start[2]
        self.speed = self.turn_rate = 0.0
        self.done = False
        self.pending = deque()
        self.pending_ego = deque()
        self.ego_sample_tick = None
        self.history = deque(maxlen=self.config.history_ticks)
        self.sensor_tick = None
        self.sensor_phase = -1
        self.sensor_period_ticks = (
            None
            if self.config.tof_rate_hz is None
            else 1
            / (Fraction(str(self.config.dt)) * Fraction(str(self.config.tof_rate_hz)))
        )
        self.tof = np.zeros((8, 8), dtype=np.float32)
        self.valid = np.zeros((8, 8), dtype=bool)
        self._update_sensor()
        self._record_history()
        return self._observation(), self._info(False, False)

    def _update_sensor(self):
        """Quantize acquisitions to decision ticks; deliver pending frames every tick."""
        phase = (
            self.tick
            if self.sensor_period_ticks is None
            else self.tick // self.sensor_period_ticks
        )
        if phase != self.sensor_phase:
            self._sample()
            self.sensor_phase = phase
        while self.pending and self.pending[0][0] <= self.tick:
            _, self.sensor_tick, self.tof, self.valid = self.pending.popleft()

    def _sample(self):
        config = self.config
        grid = tof_ranges(self.position, self.yaw, self.scenario, config)
        valid = (
            np.ones((8, 8), dtype=bool)
            if config.tof_mount_height is None
            else np.isfinite(grid) & (grid < config.max_range)
        )
        grid += self.rng.normal(0, config.noise_std, grid.shape)
        valid &= self.rng.random((8, 8)) >= config.dropout
        grid = np.where(valid, np.clip(grid, 0, config.max_range), 0).astype(np.float32)
        self.pending.append((self.tick + config.latency_ticks, self.tick, grid, valid))

    def _record_history(self):
        config = self.config
        position = self.position.copy()
        if config.odometry_position_error:
            angle = self.odometry_rng.uniform(-math.pi, math.pi)
            radius = config.odometry_position_error * math.sqrt(
                self.odometry_rng.random()
            )
            position += radius * np.array([math.cos(angle), math.sin(angle)])
        delta = np.asarray(self.scenario.goal) - position
        cosine, sine = math.cos(self.yaw), math.sin(self.yaw)
        if config.odometry_heading_error:
            error = self.odometry_rng.uniform(
                -config.odometry_heading_error, config.odometry_heading_error
            )
            error_cosine, error_sine = math.cos(error), math.sin(error)
            cosine, sine = (
                cosine * error_cosine - sine * error_sine,
                sine * error_cosine + cosine * error_sine,
            )
        goal = np.array(
            [cosine * delta[0] + sine * delta[1], -sine * delta[0] + cosine * delta[1]],
            dtype=np.float32,
        )
        ego = np.array([self.speed, self.turn_rate, *goal], dtype=np.float32)
        self.pending_ego.append(
            (self.tick + config.odometry_latency_ticks, self.tick, ego)
        )
        if self.ego_sample_tick is None:
            self.ego_sample_tick, self.ego = self.tick, ego
        while self.pending_ego and self.pending_ego[0][0] <= self.tick:
            _, self.ego_sample_tick, self.ego = self.pending_ego.popleft()
        self.history.append((self.ego.copy(), self.tof.copy(), self.valid.copy()))

    def _observation(self):
        ego = self.history[-1][0].copy()
        goal = ego[2:].copy()
        count = self.config.history_ticks
        ego_history = np.zeros((count, 4), dtype=np.float32)
        tof_history = np.zeros((count, 8, 8), dtype=np.float32)
        valid_history = np.zeros((count, 8, 8), dtype=bool)
        history_valid = np.zeros(count, dtype=bool)
        for offset, (past_ego, past_tof, past_valid) in enumerate(
            self.history, start=count - len(self.history)
        ):
            ego_history[offset], tof_history[offset], valid_history[offset] = (
                past_ego,
                past_tof,
                past_valid,
            )
            history_valid[offset] = True
        age_ticks = (
            self.tick - self.sensor_tick
            if self.sensor_tick is not None
            else self.tick + 1
        )
        observation = {
            "schema": "micro-classifier/sim-observation/1",
            "tick": self.tick,
            "time_s": self.tick * self.config.dt,
            "ego": ego,
            "goal_body_m": goal,
            "tof_m": self.tof.copy(),
            "tof_valid": self.valid.copy(),
            "tof_age_s": age_ticks * self.config.dt,
            "tof_sample_tick": self.sensor_tick,
            "history_ego": ego_history,
            "history_tof_m": tof_history,
            "history_tof_valid": valid_history,
            "history_valid": history_valid,
        }
        if self.config.odometry_latency_ticks:
            observation["ego_sample_tick"] = self.ego_sample_tick
            observation["ego_age_s"] = (
                self.tick - self.ego_sample_tick
            ) * self.config.dt
        return observation

    def _info(self, collision, success):
        return {
            "ground_truth": {"position_m": self.position.copy(), "yaw_rad": self.yaw},
            "collision": collision,
            "success": success,
            "distance_to_goal_m": float(
                np.linalg.norm(np.asarray(self.scenario.goal) - self.position)
            ),
        }

    def step(self, action):
        if self.done:
            raise RuntimeError("episode ended; call reset before step")
        action = np.asarray(action, dtype=np.float64)
        if action.shape != (2,) or not np.isfinite(action).all():
            raise ValueError("action must contain finite speed and turn rate")
        config = self.config
        old_distance = float(
            np.linalg.norm(np.asarray(self.scenario.goal) - self.position)
        )
        target = float(np.clip(action[0], 0, config.max_speed))
        self.speed += float(
            np.clip(
                target - self.speed,
                -config.acceleration * config.dt,
                config.acceleration * config.dt,
            )
        )
        self.turn_rate = float(
            np.clip(action[1], -config.max_turn_rate, config.max_turn_rate)
        )
        segments = max(1, math.ceil(abs(self.turn_rate) * config.dt / 0.1))
        seconds = config.dt / segments
        collision = False
        for _ in range(segments):
            position, yaw = integrate(
                self.position, self.yaw, self.speed, self.turn_rate, seconds
            )
            sagitta = (
                abs(self.speed / self.turn_rate)
                * (1 - math.cos(self.turn_rate * seconds / 2))
                if self.turn_rate
                else 0
            )
            if swept_collision(
                self.position,
                position,
                config.radius + sagitta,
                self.scenario.obstacles,
                self.scenario.bounds,
            ):
                collision = True
                self.speed = self.turn_rate = 0.0
                break
            self.position, self.yaw = position, yaw
        self.tick += 1
        self._update_sensor()
        self._record_history()
        info = self._info(collision, False)
        success = not collision and info["distance_to_goal_m"] <= config.goal_tolerance
        info["success"] = success
        terminated = collision or success
        truncated = self.tick >= config.max_ticks and not terminated
        self.done = terminated or truncated
        info["timeout"] = truncated
        info["applied_action"] = np.array([self.speed, self.turn_rate])
        reward = old_distance - info["distance_to_goal_m"] - config.tick_cost
        reward += config.success_reward * success - config.collision_cost * collision
        return self._observation(), float(reward), terminated, truncated, info


def ray_ranges(position, angles, obstacles, bounds, maximum):
    """First circle or arena-wall intersection for each world-frame ray."""
    position = np.asarray(position, dtype=np.float64)
    directions = np.stack((np.cos(angles), np.sin(angles)), axis=-1)
    ranges = np.full(len(directions), maximum, dtype=np.float64)
    for axis in range(2):
        for wall in (0.0, bounds[axis]):
            distance = np.divide(
                wall - position[axis],
                directions[:, axis],
                out=np.full(len(directions), np.inf),
                where=np.abs(directions[:, axis]) > 1e-12,
            )
            ranges = np.minimum(ranges, np.where(distance >= 0, distance, np.inf))
    for centre_x, centre_y, radius in obstacles:
        offset = position - np.array([centre_x, centre_y])
        projection = directions @ offset
        discriminant = projection**2 - (offset @ offset - radius**2)
        root = np.sqrt(np.maximum(discriminant, 0))
        near, far = -projection - root, -projection + root
        distance = np.where(near >= 0, near, far)
        ranges = np.minimum(
            ranges, np.where((discriminant >= 0) & (distance >= 0), distance, np.inf)
        )
    return ranges


def tof_directions(yaw, config):
    """World-frame unit rays, upper-to-lower rows and left-to-right columns."""
    angles = np.linspace(config.field_of_view / 2, -config.field_of_view / 2, 8)
    elevation, azimuth = np.meshgrid(angles, angles, indexing="ij")
    if config.tof_mount_height is None:
        elevation = np.zeros((8, 8))
    forward = np.cos(elevation) * np.cos(azimuth)
    left = np.cos(elevation) * np.sin(azimuth)
    up = np.sin(elevation)
    pitch = 0 if config.tof_mount_height is None else config.tof_mount_pitch
    cosine, sine = math.cos(pitch), math.sin(pitch)
    forward, up = cosine * forward + sine * up, -sine * forward + cosine * up
    cosine, sine = math.cos(yaw), math.sin(yaw)
    return np.stack(
        (cosine * forward - sine * left, sine * forward + cosine * left, up), axis=-1
    )


def tof_ranges(position, yaw, scenario, config):
    """Synthetic first returns from a floor, finite walls and capped cylinders."""
    if config.tof_mount_height is None:
        angles = yaw + np.linspace(
            config.field_of_view / 2, -config.field_of_view / 2, 8
        )
        ranges = ray_ranges(
            position, angles, scenario.obstacles, scenario.bounds, config.max_range
        )
        return np.broadcast_to(ranges, (8, 8)).copy()
    rays = tof_directions(yaw, config)
    directions, up = rays[..., :2], rays[..., 2]
    height = config.tof_mount_height
    ranges = np.divide(-height, up, out=np.full((8, 8), np.inf), where=up < 0)
    for axis in range(2):
        for wall in (0.0, scenario.bounds[axis]):
            distance = np.divide(
                wall - position[axis],
                directions[..., axis],
                out=np.full((8, 8), np.inf),
                where=directions[..., axis] != 0,
            )
            altitude = height + np.where(np.isfinite(distance), distance, 0) * up
            other_axis = 1 - axis
            across = (
                position[other_axis]
                + np.where(np.isfinite(distance), distance, 0)
                * directions[..., other_axis]
            )
            hit = (
                (distance >= 0)
                & (altitude >= 0)
                & (altitude <= config.wall_height)
                & (across >= 0)
                & (across <= scenario.bounds[other_axis])
            )
            ranges = np.minimum(ranges, np.where(hit, distance, np.inf))
    horizontal_squared = np.sum(directions**2, axis=-1)
    for index, (centre_x, centre_y, radius) in enumerate(scenario.obstacles):
        top = (
            scenario.obstacle_heights[index]
            if scenario.obstacle_heights
            else config.obstacle_height
        )
        offset = np.asarray(position) - [centre_x, centre_y]
        projection = directions @ offset
        discriminant = projection**2 - horizontal_squared * (
            offset @ offset - radius**2
        )
        root = np.sqrt(np.maximum(discriminant, 0))
        for sign in (-1, 1):
            distance = np.divide(
                -projection + sign * root,
                horizontal_squared,
                out=np.full((8, 8), np.inf),
                where=horizontal_squared > 0,
            )
            altitude = height + np.where(np.isfinite(distance), distance, 0) * up
            hit = (
                (discriminant >= 0)
                & (distance >= 0)
                & (altitude >= 0)
                & (altitude <= top)
            )
            ranges = np.minimum(ranges, np.where(hit, distance, np.inf))
        distance = np.divide(
            top - height, up, out=np.full((8, 8), np.inf), where=up != 0
        )
        relative = (
            offset
            + np.where(np.isfinite(distance), distance, 0)[..., None] * directions
        )
        hit = (distance >= 0) & (np.sum(relative**2, axis=-1) <= radius**2)
        ranges = np.minimum(ranges, np.where(hit, distance, np.inf))
    return ranges


def swept_collision(start, end, radius, obstacles, bounds):
    """Test the full segment, not just its endpoint, against inflated obstacles."""
    start, end = np.asarray(start), np.asarray(end)
    if np.any(np.minimum(start, end) <= radius) or np.any(
        np.maximum(start, end) >= np.asarray(bounds) - radius
    ):
        return True
    delta = end - start
    length_squared = float(delta @ delta)
    for centre_x, centre_y, obstacle_radius in obstacles:
        centre = np.array([centre_x, centre_y])
        fraction = (
            0
            if length_squared == 0
            else np.clip((centre - start) @ delta / length_squared, 0, 1)
        )
        closest = start + fraction * delta
        if np.linalg.norm(closest - centre) <= radius + obstacle_radius:
            return True
    return False


def integrate(position, yaw, speed, turn_rate, seconds):
    """Exact constant-twist unicycle motion over one integration interval."""
    angle = turn_rate * seconds
    midpoint = yaw + angle / 2
    distance = speed * seconds * np.sinc(angle / (2 * math.pi))
    next_position = np.asarray(position) + distance * np.array(
        [math.cos(midpoint), math.sin(midpoint)]
    )
    return next_position, (yaw + angle + math.pi) % (2 * math.pi) - math.pi


def make_scenario(name, seed=0):
    rng = np.random.default_rng(seed)
    if name == "clear":
        return Scenario()
    if name == "obstacle":
        return Scenario(
            name=name, obstacles=((3.0, 3.0 + rng.uniform(-0.15, 0.15), 0.35),)
        )
    if name == "corridor":
        obstacles = tuple(
            (float(column), row, 0.3)
            for column in np.arange(1.5, 5, 0.7)
            for row in (2.1, 3.9)
        )
        return Scenario(name=name, obstacles=obstacles)
    if name == "slalom":
        return Scenario(name=name, obstacles=((2.2, 3.25, 0.3), (3.6, 2.75, 0.3)))
    raise ValueError(f"unknown scenario: {name}")


class ReactivePolicy:
    """Illustrative sensor-only reactive policy, not an operational safety controller."""

    def __init__(self, config):
        self.config = config
        self.avoid_side = 0

    def __call__(self, observation):
        config = self.config
        valid = observation["tof_valid"]
        if (
            not valid.any()
            or observation["tof_age_s"] > (config.latency_ticks + 1) * config.dt
        ):
            return np.zeros(2)
        column_ranges = np.min(np.where(valid, observation["tof_m"], np.inf), axis=0)
        if not np.isfinite(column_ranges).all():
            return np.zeros(2)
        goal = observation["goal_body_m"]
        distance = float(np.linalg.norm(goal))
        bearing = math.atan2(goal[1], goal[0])
        speed = float(observation["ego"][0])
        margin = (
            config.radius
            + speed**2 / (2 * config.acceleration)
            + speed * observation["tof_age_s"]
            + 0.35
        )
        clearance = float(np.min(column_ranges[2:6]))
        if clearance < margin:
            if not self.avoid_side:
                self.avoid_side = (
                    1
                    if np.mean(column_ranges[:3]) >= np.mean(column_ranges[5:])
                    else -1
                )
            return np.array([0.0, self.avoid_side * config.max_turn_rate])
        if clearance > margin + 0.5:
            self.avoid_side = 0
        steering = float(
            np.clip(2 * bearing, -config.max_turn_rate, config.max_turn_rate)
        )
        if self.avoid_side:
            steering = self.avoid_side * config.max_turn_rate * 0.5
        desired_speed = min(config.max_speed, distance) * max(0.0, math.cos(bearing))
        if abs(bearing) > 0.7:
            desired_speed = 0.0
        return np.array([desired_speed, steering])


class ScriptedExpert:
    """Privileged map-aware reference using SciPy Dijkstra, not a deployed policy."""

    def __init__(self, env):
        from scipy.sparse import coo_array
        from scipy.sparse.csgraph import dijkstra

        self.env = env
        config, scenario = env.config, env.scenario
        spacing = 0.1
        margin = config.radius + 0.15
        horizontal = np.arange(margin, scenario.bounds[0] - margin, spacing)
        vertical = np.arange(margin, scenario.bounds[1] - margin, spacing)
        grid_x, grid_y = np.meshgrid(horizontal, vertical)
        points = np.stack((grid_x.ravel(), grid_y.ravel()), axis=1)
        self.path = None
        if not len(points):
            return
        free = np.ones(len(points), dtype=bool)
        for centre_x, centre_y, radius in scenario.obstacles:
            free &= (
                np.linalg.norm(points - [centre_x, centre_y], axis=1)
                > radius + margin + spacing / 2
            )
        identifiers = np.arange(len(points)).reshape(grid_x.shape)
        edges = [
            (identifiers[:, :-1].ravel(), identifiers[:, 1:].ravel()),
            (identifiers[:-1, :].ravel(), identifiers[1:, :].ravel()),
        ]
        left = np.concatenate([edge[0] for edge in edges])
        right = np.concatenate([edge[1] for edge in edges])
        keep = free[left] & free[right]
        left, right = left[keep], right[keep]
        graph = coo_array(
            (
                np.full(len(left) * 2, spacing),
                (np.concatenate((left, right)), np.concatenate((right, left))),
            ),
            shape=(len(points), len(points)),
        ).tocsr()
        start = int(
            np.argmin(
                np.where(free, np.linalg.norm(points - env.position, axis=1), np.inf)
            )
        )
        goal = int(
            np.argmin(
                np.where(free, np.linalg.norm(points - scenario.goal, axis=1), np.inf)
            )
        )
        distances, predecessors = dijkstra(
            graph, indices=start, return_predecessors=True
        )
        self.path = None
        if np.isfinite(distances[goal]) and free[start] and free[goal]:
            route = [goal]
            while route[-1] != start:
                route.append(int(predecessors[route[-1]]))
            self.path = [points[index] for index in reversed(route)] + [
                np.asarray(scenario.goal)
            ]

    def __call__(self, observation):
        env = self.env
        if not self.path or not observation["tof_valid"].any():
            return np.zeros(2)
        waypoint = None
        for candidate in reversed(self.path):
            if not swept_collision(
                env.position,
                candidate,
                env.config.radius + 0.1,
                env.scenario.obstacles,
                env.scenario.bounds,
            ):
                waypoint = candidate
                break
        if waypoint is None:
            return np.zeros(2)
        delta = waypoint - env.position
        error = (math.atan2(delta[1], delta[0]) - env.yaw + math.pi) % (
            2 * math.pi
        ) - math.pi
        steering = float(
            np.clip(3 * error, -env.config.max_turn_rate, env.config.max_turn_rate)
        )
        speed = min(
            env.config.max_speed,
            math.sqrt(2 * env.config.acceleration * float(np.linalg.norm(delta))),
        )
        if abs(error) > 0.3:
            speed = 0.0
        return np.array([speed, steering])


def json_value(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(f"not JSON serializable: {type(value).__name__}")


def rollout(env, policy=None):
    """Collect one deterministic episode; world truth stays separate from inputs."""
    observation, info = env.reset(seed=env.seed)
    policy = policy or ScriptedExpert(env)
    records = [
        {
            "schema": "micro-classifier/sim-episode/1",
            "kind": "metadata",
            "seed": env.seed,
            "scenario": asdict(env.scenario),
            "config": asdict(env.config),
            "policy": type(policy).__name__,
            "privileged_expert": isinstance(policy, ScriptedExpert),
            "limitations": [
                "Planar rays repeated vertically, not VL53L8CX emulation."
                if env.config.tof_mount_height is None
                else "Synthetic floor/cylinder point rays, not VL53L8CX emulation.",
                "Simulation-only physics and rewards, not measured hardware limits.",
                "No teacher labels, student or hardware safety validation.",
            ],
            "observation": observation,
            "info": info,
        }
    ]
    total_reward = 0.0
    while not env.done:
        action = np.asarray(policy(observation))
        following, reward, terminated, truncated, info = env.step(action)
        records.append(
            {
                "kind": "transition",
                "tick": observation["tick"],
                "action": action,
                "reward": reward,
                "terminated": terminated,
                "truncated": truncated,
                "observation": following,
                "info": info,
            }
        )
        total_reward += reward
        observation = following
    summary = {
        "kind": "summary",
        "ticks": env.tick,
        "total_reward": total_reward,
        "success": info["success"],
        "collision": info["collision"],
        "timeout": info["timeout"],
    }
    records.append(summary)
    return records, summary


def state_from_observation(observation):
    """Map the current planar sample to host FLU state; no truth or ToF payload."""
    from interface.protocol import UINT32_MAX, State

    tick, seconds = observation["tick"], observation["time_s"]
    if isinstance(tick, bool) or not isinstance(tick, int) or tick < 0:
        raise ValueError("observation tick must be a nonnegative integer")
    if not math.isfinite(seconds) or seconds < 0:
        raise ValueError("observation time must be finite and nonnegative")
    ego = np.asarray(observation["ego"])
    goal = np.asarray(observation["goal_body_m"])
    if ego.shape != (4,) or goal.shape != (2,):
        raise ValueError("observation requires planar ego and goal vectors")
    if ("ego_sample_tick" in observation) != ("ego_age_s" in observation):
        raise ValueError("ego sample tick and age must be supplied together")
    age = observation.get("ego_age_s", 0.0)
    sample_tick = observation.get("ego_sample_tick", tick)
    try:
        finite_age = (
            not isinstance(age, bool)
            and isinstance(age, (int, float))
            and math.isfinite(age)
        )
    except OverflowError:
        finite_age = False
    if (
        not finite_age
        or age < 0
        or type(sample_tick) is not int
        or not 0 <= sample_tick <= tick
    ):
        raise ValueError("invalid ego sample tick or age")
    expected_age = (tick - sample_tick) / tick * seconds if tick else 0.0
    if not math.isclose(age, expected_age, rel_tol=1e-6, abs_tol=1e-9):
        raise ValueError("ego age and sample tick disagree")
    if age >= UINT32_MAX / 1_000_000:
        raise ValueError("ego age cannot be represented by the wire contract")
    age_us = round(age * 1_000_000)
    if age_us >= UINT32_MAX:
        raise ValueError("ego age cannot be represented by the wire contract")
    return State(
        sequence=tick & UINT32_MAX,
        timestamp_us=round(seconds * 1_000_000) & UINT32_MAX,
        velocity_m_s=(float(ego[0]), 0.0, 0.0),
        angular_velocity_rad_s=(0.0, 0.0, float(ego[1])),
        goal_m=(float(goal[0]), float(goal[1]), 0.0),
        ages_us=(age_us, age_us, age_us, UINT32_MAX, UINT32_MAX),
    )


def with_wire_frames(records):
    """Return logs with exact state bytes; never fabricate model decisions."""
    from interface.protocol import (
        PROFILE_ID,
        PROFILE_VERSION,
        PROTOCOL_VERSION,
        SCHEMA_VERSION,
        encode_state,
    )

    exported = []
    for record in records:
        entry = dict(record)
        if "observation" in record:
            frame = encode_state(state_from_observation(record["observation"]))
            entry["state_frame_hex"] = frame.hex()
        if record["kind"] == "metadata":
            entry["wire_contract"] = {
                "schema": "micro-classifier/sim-wire/0",
                "protocol_version": PROTOCOL_VERSION,
                "schema_version": SCHEMA_VERSION,
                "profile_id": PROFILE_ID,
                "profile_version": PROFILE_VERSION,
                "state_frame_bytes": len(frame),
                "decision_frames": False,
                "health": "unknown, not simulated",
                "tof_history": "module-side observation only",
                "provisional": True,
            }
        exported.append(entry)
    return exported


def write_episode(path, records):
    """Write a new JSONL episode exclusively, never overwrite an existing log."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        for record in records:
            stream.write(
                json.dumps(record, default=json_value, sort_keys=True, allow_nan=False)
                + "\n"
            )


def render_episode(path, records):
    """Save a headless PNG showing the actual arena, rover footprint and trajectory."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle

    metadata = records[0]
    figure, axes = plt.subplots(figsize=(6, 6))
    bounds = metadata["scenario"]["bounds"]
    for centre_x, centre_y, radius in metadata["scenario"]["obstacles"]:
        axes.add_patch(Circle((centre_x, centre_y), radius, color="#3b3b3b"))
    positions = np.array(
        [
            record["info"]["ground_truth"]["position_m"]
            for record in records
            if "info" in record
        ]
    )
    axes.plot(positions[:, 0], positions[:, 1], color="#247b6c", linewidth=2)
    axes.add_patch(
        Circle(
            positions[-1], metadata["config"]["radius"], facecolor="#247b6c", alpha=0.6
        )
    )
    axes.scatter(*metadata["scenario"]["goal"], marker="x", s=80, color="#bd3a4e")
    axes.set(
        xlim=(0, bounds[0]),
        ylim=(0, bounds[1]),
        aspect="equal",
        xlabel="World X (m)",
        ylabel="World Y (m)",
    )
    axes.set_title(f"{metadata['scenario']['name']}, seed {metadata['seed']}")
    figure.tight_layout()
    figure.savefig(path, dpi=120)
    plt.close(figure)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scenario",
        choices=("clear", "obstacle", "corridor", "slalom"),
        default="clear",
    )
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--episodes", type=int, default=1)
    parser.add_argument("--policy", choices=("map", "reactive"), default="map")
    parser.add_argument("--output", type=Path, default=Path("sim/episodes"))
    parser.add_argument(
        "--config", type=Path, help="JSON overrides of simulation Config fields"
    )
    parser.add_argument(
        "--render", action="store_true", help="save a PNG trajectory for each episode"
    )
    parser.add_argument(
        "--wire",
        action="store_true",
        help="include exact provisional v0 state-frame bytes",
    )
    args = parser.parse_args()
    if args.seed < 0 or args.episodes < 1:
        parser.error("seed must be nonnegative and episodes positive")
    config = Config(**json.loads(args.config.read_text())) if args.config else Config()
    for seed in range(args.seed, args.seed + args.episodes):
        env = RoverEnv(config, make_scenario(args.scenario, seed))
        env.reset(seed=seed)
        policy = ReactivePolicy(config) if args.policy == "reactive" else None
        records, summary = rollout(env, policy)
        if args.wire:
            records = with_wire_frames(records)
        path = args.output / f"{args.scenario}-{seed:06}.jsonl"
        write_episode(path, records)
        if args.render:
            render_episode(path.with_suffix(".png"), records)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        print(
            json.dumps(
                {**summary, "seed": seed, "path": str(path), "sha256": digest},
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
