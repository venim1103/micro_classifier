import json
import math
from copy import deepcopy
from pathlib import Path

import numpy as np
import pytest

from sim.labels import (
    answer_coverage,
    coverage_suite,
    draft_catalogue,
    draft_labels,
    smoke_suite,
    stopping_envelope,
)
from sim.rover import (
    Config,
    RoverEnv,
    Scenario,
    ScriptedExpert,
    integrate,
    json_value,
    make_scenario,
    ray_ranges,
    rollout,
    state_from_observation,
    swept_collision,
    with_wire_frames,
    write_episode,
)


@pytest.mark.parametrize("obstacle", [(2.4, 2.0, 0.01), (2.1, 2.185, 0.01)])
def test_navigation_proposal_full_ray_history_can_hide_a_swept_collision(obstacle):
    from sim.navigation import evaluate_synthetic
    from teacher.label_pipeline import prepare_request

    config = Config(noise_std=0, dropout=0)
    position = np.array([2.0, 2.0])
    bounds = (6.0, 6.0)
    angles = np.linspace(config.field_of_view / 2, -config.field_of_view / 2, 8)
    free_history, obstructed_history = [], []
    for offset in range(config.history_ticks):
        past = position - np.array(
            [
                (config.history_ticks - 1 - offset + config.latency_ticks)
                * config.max_speed
                * config.dt,
                0,
            ]
        )
        free_history.append(ray_ranges(past, angles, (), bounds, config.max_range))
        obstructed_history.append(
            ray_ranges(past, angles, (obstacle,), bounds, config.max_range)
        )
    np.testing.assert_array_equal(free_history, obstructed_history)
    assert not swept_collision(position, position, config.radius, (obstacle,), bounds)
    age = config.latency_ticks * config.dt
    stopping_distance = config.max_speed * (age + config.dt) + config.max_speed**2 / (
        2 * config.acceleration
    )
    end = position + np.array([stopping_distance, 0])
    assert not swept_collision(position, end, config.radius, (), bounds)
    assert swept_collision(position, end, config.radius, (obstacle,), bounds)

    ego_history = np.array(
        [
            [
                config.max_speed,
                0,
                3 + (config.history_ticks - 1 - offset) * config.max_speed * config.dt,
                0,
            ]
            for offset in range(config.history_ticks)
        ],
        dtype=np.float32,
    )
    states = []
    for history in (free_history, obstructed_history):
        tof_history = np.repeat(
            np.asarray(history, dtype=np.float32)[:, None, :], 8, axis=1
        )
        observation = {
            "schema": "micro-classifier/sim-observation/1",
            "tick": 15,
            "time_s": 15 * config.dt,
            "ego": ego_history[-1],
            "goal_body_m": ego_history[-1, 2:],
            "tof_m": tof_history[-1],
            "tof_valid": np.ones((8, 8), dtype=bool),
            "tof_age_s": age,
            "tof_sample_tick": 15 - config.latency_ticks,
            "history_ego": ego_history,
            "history_tof_m": tof_history,
            "history_tof_valid": np.ones((8, 8, 8), dtype=bool),
            "history_valid": np.ones(config.history_ticks, dtype=bool),
        }
        states.append(prepare_request(observation, config=config)["state"])
    assert states[0] == states[1]
    settings = {
        "speed": config.max_speed,
        "tof_age_s": age,
        "config": config,
        "synthetic_test_only": True,
    }
    clear_reference = evaluate_synthetic(
        Scenario(start=(2.0, 2.0, 0.0), goal=(5.0, 2.0)), **settings
    )
    blocked_reference = evaluate_synthetic(
        Scenario(start=(2.0, 2.0, 0.0), goal=(5.0, 2.0), obstacles=(obstacle,)),
        **settings,
    )
    assert clear_reference["answers"]["path_blocked"] == "false"
    assert blocked_reference["answers"]["path_blocked"] == "true"


@pytest.mark.parametrize("offset,blocked", [(-1e-6, True), (0, True), (1e-6, False)])
def test_navigation_proposal_circle_contact_counts_across_the_whole_sweep(
    offset, blocked
):
    start, end = (2.0, 2.0), (3.0, 2.0)
    radius = 0.125
    obstacles = ((2.5, 2.25 + offset, 0.125),)
    bounds = (6.0, 6.0)
    assert not swept_collision(start, start, radius, obstacles, bounds)
    assert not swept_collision(end, end, radius, obstacles, bounds)
    assert swept_collision(start, end, radius, obstacles, bounds) == blocked


@pytest.mark.parametrize("tier,distance", [(1, 0.05), (2, 0.14), (3, 0.27)])
def test_navigation_proposal_nominal_stopping_candidates(tier, distance):
    config = Config()
    speed = config.max_speed * tier / 3
    age = config.latency_ticks * config.dt
    reaction = age + config.dt
    assert reaction == pytest.approx(0.15)
    assert speed * reaction + speed**2 / (2 * config.acceleration) == pytest.approx(
        distance
    )
    assert reaction + speed / config.acceleration == pytest.approx(0.15 + tier * 0.2)


@pytest.mark.parametrize("requested_tier", [1, 2])
def test_navigation_proposal_lower_request_does_not_erase_current_momentum(
    requested_tier,
):
    config = Config()
    position = np.array([2.0, 2.0])
    obstacles, bounds = ((2.35, 2.0, 0.02),), (6.0, 6.0)
    requested_speed = config.max_speed * requested_tier / 3
    current_speed = config.max_speed
    reaction = (config.latency_ticks + 1) * config.dt
    distances = [
        speed * reaction + speed**2 / (2 * config.acceleration)
        for speed in (requested_speed, max(current_speed, requested_speed))
    ]
    assert not swept_collision(
        position, position + [distances[0], 0], config.radius, obstacles, bounds
    )
    assert swept_collision(
        position, position + [distances[1], 0], config.radius, obstacles, bounds
    )


def test_synthetic_navigation_reference_includes_wall_contact_without_changing_simulator():
    from sim.navigation import _touches

    point, radius, bounds = (0.125, 2.0), 0.125, (6.0, 6.0)
    assert not swept_collision(point, point, radius, (), bounds)
    assert _touches(point, point, radius, (), bounds)
    assert not _touches((0.126, 2.0), (0.126, 2.0), radius, (), bounds)


def test_synthetic_navigation_reference_requires_opt_in_and_no_observation_input():
    from sim.navigation import evaluate_synthetic

    with pytest.raises(ValueError, match="synthetic-test-only"):
        evaluate_synthetic(Scenario(), speed=0.3)
    with pytest.raises(TypeError, match="not observations"):
        evaluate_synthetic({}, speed=0.3, synthetic_test_only=True)


@pytest.mark.parametrize(
    "goal,expected",
    [((5.0, 3.0), "centre"), ((5.0, 4.0), "left"), ((5.0, 2.0), "right")],
)
def test_synthetic_navigation_reference_open_geometry_goal_ranking(goal, expected):
    from sim.navigation import evaluate_synthetic

    result = evaluate_synthetic(
        Scenario(goal=goal), speed=0.6, tof_age_s=0.1, synthetic_test_only=True
    )
    assert result["answers"] == {
        "path_blocked": "false",
        "clear_sector": expected,
        "speed_tier": "3",
        "mode": None,
    }
    assert result["synthetic"] and not result["training_approved"]
    assert not result["reviewed_dataset"] and not result["physical_safety_claim"]
    assert result["mode_labels"] == 0
    json.dumps(result, allow_nan=False)


def test_synthetic_navigation_reference_at_rest_and_blocked_are_distinct():
    from sim.navigation import evaluate_synthetic

    stopped = evaluate_synthetic(Scenario(), speed=0, synthetic_test_only=True)
    assert stopped["answers"]["path_blocked"] == "false"
    assert stopped["answers"]["clear_sector"] is None
    obstacle = Scenario(obstacles=((1.3, 3.0, 0.1),))
    moving = evaluate_synthetic(
        obstacle, speed=0.6, tof_age_s=0.1, synthetic_test_only=True
    )
    assert moving["answers"] == {
        "path_blocked": "true",
        "clear_sector": "none",
        "speed_tier": "0",
        "mode": None,
    }


def test_synthetic_navigation_reference_budget_exhaustion_abstains():
    from sim.navigation import evaluate_synthetic

    result = evaluate_synthetic(
        Scenario(),
        speed=0.4,
        turn_rate=0.7,
        tof_age_s=0.1,
        max_segments=1,
        synthetic_test_only=True,
    )
    assert all(answer is None for answer in result["answers"].values())
    assert all(row["status"] == "unknown" for row in result["maneuvers"].values())


@pytest.mark.parametrize(
    "field,value",
    [
        ("speed", True),
        ("speed", -1),
        ("speed", 0.7),
        ("turn_rate", 2),
        ("tof_age_s", -1),
        ("tof_age_s", float("nan")),
        ("max_segments", True),
        ("max_segments", 4097),
    ],
)
def test_synthetic_navigation_reference_rejects_invalid_inputs(field, value):
    from sim.navigation import evaluate_synthetic

    settings = {"speed": 0.3, "synthetic_test_only": True, field: value}
    with pytest.raises(ValueError):
        evaluate_synthetic(Scenario(), **settings)


@pytest.mark.parametrize("turn_rate", [-0.7, 0.0, 0.7])
def test_synthetic_navigation_reference_curved_endpoints_match_high_order_quadrature(
    turn_rate,
):
    from sim.navigation import evaluate_synthetic

    scenario, config = Scenario(), Config()
    speed, reaction = 0.6, 0.15
    result = evaluate_synthetic(
        scenario,
        speed=speed,
        turn_rate=turn_rate,
        tof_age_s=0.1,
        synthetic_test_only=True,
    )
    nodes, weights = np.polynomial.legendre.leggauss(64)
    for name, angular_rate in (
        ("centre", 0),
        ("left", config.max_turn_rate),
        ("right", -config.max_turn_rate),
    ):
        endpoint = np.array(scenario.start[:2], dtype=float)
        yaw = scenario.start[2]
        for duration, angular, deceleration in (
            (reaction, turn_rate, 0),
            (speed / config.acceleration, angular_rate, config.acceleration),
        ):
            times = (nodes + 1) * duration / 2
            headings = yaw + angular * times
            velocity = (speed - deceleration * times)[:, None] * np.stack(
                [np.cos(headings), np.sin(headings)], axis=1
            )
            endpoint += duration / 2 * np.sum(weights[:, None] * velocity, axis=0)
            yaw += angular * duration
        row = result["maneuvers"][name]
        assert row["status"] == "clear"
        assert (
            np.linalg.norm(endpoint - row["endpoint_m"])
            <= row["endpoint_error_bound_m"] + 1e-12
        )


def test_synthetic_navigation_reference_unresolved_goal_ranking_abstains():
    from sim.navigation import evaluate_synthetic

    settings = {"speed": 0.6, "tof_age_s": 0.1, "synthetic_test_only": True}
    result = evaluate_synthetic(Scenario(), **settings)
    goal = tuple(
        (
            np.asarray(result["maneuvers"]["centre"]["endpoint_m"])
            + result["maneuvers"]["left"]["endpoint_m"]
        )
        / 2
    )
    unresolved = evaluate_synthetic(Scenario(goal=goal), **settings)
    assert all(row["status"] == "clear" for row in unresolved["maneuvers"].values())
    assert unresolved["answers"]["clear_sector"] is None


def test_synthetic_navigation_reference_symmetric_turn_tie_prefers_left():
    from sim.navigation import evaluate_synthetic

    result = evaluate_synthetic(
        Scenario(obstacles=((1.47, 3.0, 0.02),)),
        speed=0.6,
        tof_age_s=0.1,
        synthetic_test_only=True,
    )
    assert result["maneuvers"]["centre"]["status"] == "blocked"
    assert (
        result["maneuvers"]["left"]["status"]
        == result["maneuvers"]["right"]["status"]
        == "clear"
    )
    assert result["answers"]["clear_sector"] == "left"


@pytest.mark.parametrize(
    "gap,tier", [(0.025, "0"), (0.09, "1"), (0.2, "2"), (0.35, "3")]
)
def test_synthetic_navigation_reference_tier_capacity_and_current_momentum(gap, tier):
    from sim.navigation import evaluate_synthetic

    scenario = Scenario(obstacles=((1.19 + gap, 3.0, 0.01),))
    result = evaluate_synthetic(
        scenario, speed=0, tof_age_s=0.1, synthetic_test_only=True
    )
    assert result["answers"]["speed_tier"] == tier
    if tier == "2":
        moving = evaluate_synthetic(
            scenario, speed=0.6, tof_age_s=0.1, synthetic_test_only=True
        )
        assert moving["answers"]["speed_tier"] == "0"


def test_synthetic_navigation_reference_curved_contact_uncertainty_is_not_none():
    from sim.navigation import evaluate_synthetic

    settings = {"speed": 0.6, "tof_age_s": 0.1, "synthetic_test_only": True}
    empty = evaluate_synthetic(Scenario(), **settings)
    endpoint = np.asarray(empty["maneuvers"]["left"]["endpoint_m"])
    centre = endpoint + 0.19 * np.array([math.sin(0.9), -math.cos(0.9)])
    scene = Scenario(obstacles=((*centre, 0.01),))
    result = evaluate_synthetic(scene, **settings)
    assert result["maneuvers"]["left"]["status"] == "unknown"
    assert result["answers"]["clear_sector"] is None


def test_draft_catalogue_matches_wire_types_options_and_review_gate():
    from interface.protocol import CATALOGUE_VERSION, QUESTIONS, QuestionId

    catalogue = draft_catalogue()
    assert catalogue["catalogue_version"] == CATALOGUE_VERSION
    assert catalogue["review_status"] == "unreviewed_draft"
    assert catalogue["allowed_use"] == "simulation_smoke_and_pipeline_tests_only"
    assert catalogue["scope_approval"]["simulation_smoke"]
    assert not catalogue["scope_approval"]["live_teacher_labeling"]
    assert not catalogue["scope_approval"]["training"]
    assert not catalogue["physical_safety_claim"]
    assert len(catalogue["questions"]) == len(QUESTIONS)
    for row in catalogue["questions"]:
        identity = QuestionId(row["id"])
        kind, options = QUESTIONS[identity]
        assert (row["name"], row["type"], row["options"]) == (
            identity.name.lower(),
            kind.name.lower(),
            list(options),
        )


def test_draft_envelope_matches_config_arithmetic_and_age_monotonicity():
    config = Config()
    assert stopping_envelope(0.6, 0.1, config) == pytest.approx(0.45)
    assert stopping_envelope(0, 0.1, config) == config.radius
    assert stopping_envelope(0.6, 0.15, config) > stopping_envelope(0.6, 0.1, config)
    assert stopping_envelope(0.3, 0.1, config) < stopping_envelope(0.6, 0.1, config)


@pytest.mark.parametrize(
    "speed,age",
    [(-1, 0), (1, 0), (0, -1), (float("nan"), 0), (0, float("inf")), (True, 0)],
)
def test_draft_envelope_rejects_invalid_values(speed, age):
    with pytest.raises((TypeError, ValueError)):
        stopping_envelope(speed, age, Config())


@pytest.fixture
def draft_observation():
    config = Config(noise_std=0, dropout=0, latency_ticks=0)
    observation, _ = RoverEnv(config).reset(seed=5)
    observation["tof_m"] = np.full((8, 8), 2.0)
    return config, observation


def test_draft_clear_observation_is_serializable_and_unreviewed(draft_observation):
    config, observation = draft_observation
    result = draft_labels(observation, config)
    assert result["review_status"] == "unreviewed_draft"
    assert not result["training_approved"] and not result["physical_safety_claim"]
    assert result["answers"]["path_blocked"]["value"] == "false"
    assert result["answers"]["clear_sector"]["value"] == "centre"
    assert result["answers"]["speed_tier"]["value"] == "3"
    assert result["answers"]["mode"]["value"] is None
    assert result["answers"]["mode"]["reason"] == "human_review_required"
    assert json.loads(json.dumps(result, allow_nan=False)) == result
    assert draft_labels(observation, config) == result


@pytest.mark.parametrize(
    "offset,blocked", [(0, "true"), (-1e-6, "true"), (1e-6, "false")]
)
def test_draft_obstacle_boundary_is_inclusive(draft_observation, offset, blocked):
    config, observation = draft_observation
    observation["ego"] = np.array([0.3, 0, 4, 0])
    boundary = stopping_envelope(0.3, 0, config)
    observation["tof_m"][:, 3:5] = boundary + offset
    assert (
        draft_labels(observation, config)["answers"]["path_blocked"]["value"] == blocked
    )


@pytest.mark.parametrize("tier", [0, 1, 2, 3])
def test_draft_speed_tiers_have_config_relative_meanings(draft_observation, tier):
    config, observation = draft_observation
    boundary = stopping_envelope(config.max_speed * tier / 3, 0, config)
    observation["tof_m"][:, 3:5] = boundary + 1e-6
    assert draft_labels(observation, config)["answers"]["speed_tier"]["value"] == str(
        tier
    )


def test_draft_sector_orientation_ties_and_none_are_distinct(draft_observation):
    config, observation = draft_observation
    observation["tof_m"][:, 3:] = 1
    assert (
        draft_labels(observation, config)["answers"]["clear_sector"]["value"] == "left"
    )
    observation["tof_m"][:, 5:] = 3
    assert (
        draft_labels(observation, config)["answers"]["clear_sector"]["value"] == "right"
    )
    observation["tof_m"][:] = 0.1
    assert (
        draft_labels(observation, config)["answers"]["clear_sector"]["value"] == "none"
    )


def test_draft_partial_masks_do_not_invent_clearance(draft_observation):
    config, observation = draft_observation
    observation["tof_valid"][0, 0] = False
    observation["tof_m"][0, 0] = 0
    assert (
        draft_labels(observation, config)["answers"]["clear_sector"]["value"]
        == "centre"
    )
    observation["tof_valid"][:, 0] = False
    observation["tof_m"][:, 0] = 0
    answers = draft_labels(observation, config)["answers"]
    assert answers["clear_sector"]["value"] is None
    assert answers["path_blocked"]["value"] == "false"
    assert answers["speed_tier"]["value"] == "3"
    observation["tof_valid"][:, 3] = False
    observation["tof_m"][:, 3] = 0
    answers = draft_labels(observation, config)["answers"]
    assert answers["path_blocked"]["value"] is None
    assert answers["speed_tier"]["value"] is None


def test_draft_warmup_and_stale_samples_abstain(draft_observation):
    warmup, _ = RoverEnv().reset()
    result = draft_labels(warmup)
    assert all(answer["value"] is None for answer in result["answers"].values())
    config, observation = draft_observation
    observation["tick"] = 2
    observation["tof_age_s"] = 2 * config.dt
    result = draft_labels(observation, config)
    assert result["answers"]["path_blocked"]["reason"] == "stale_tof"


def test_draft_ignores_privileged_fields_and_never_mutates_inputs(draft_observation):
    config, observation = draft_observation
    original = deepcopy(observation)
    first = draft_labels(observation, config)
    np.testing.assert_equal(observation, original)
    observation.update(
        ground_truth={"collision": True}, expert_action=[0, 1], future=[42]
    )
    observation["history_ego"][:] = 1000
    assert draft_labels(observation, config) == first


@pytest.mark.parametrize(
    "field,value",
    [
        ("schema", "unknown"),
        ("tick", True),
        ("tof_sample_tick", 1),
        ("tof_age_s", 0.1),
        ("ego", [float("nan"), 0, 0, 0]),
        ("ego", [1, 0, 0, 0]),
        ("tof_m", np.full((8, 8), -1)),
        ("tof_m", np.full((8, 8), float("inf"))),
        ("tof_valid", np.ones((8, 8))),
    ],
)
def test_draft_rejects_malformed_observations(draft_observation, field, value):
    config, observation = draft_observation
    observation[field] = value
    with pytest.raises(ValueError):
        draft_labels(observation, config)


def test_draft_accepts_simulator_float32_speed_limit(draft_observation):
    config, observation = draft_observation
    observation["ego"][0] = config.max_speed
    assert float(observation["ego"][0]) > config.max_speed
    assert draft_labels(observation, config)["answers"]["speed_tier"]["value"] == "3"


@pytest.mark.parametrize("tier", [1, 2, 3])
def test_draft_speed_boundary_requires_strict_clearance(draft_observation, tier):
    config, observation = draft_observation
    fraction = draft_catalogue()["rules"]["speed_fractions"][tier]
    observation["tof_m"][:, 3:5] = stopping_envelope(
        config.max_speed * fraction, 0, config
    )
    assert draft_labels(observation, config)["answers"]["speed_tier"]["value"] == str(
        tier - 1
    )


def test_draft_freshness_boundary_is_inclusive(draft_observation):
    config, observation = draft_observation
    observation["tick"] = 1
    observation["tof_age_s"] = config.dt
    assert (
        draft_labels(observation, config)["answers"]["path_blocked"]["value"] == "false"
    )


def test_draft_beyond_sensor_envelope_abstains_instead_of_claiming_blocked():
    config = Config(max_range=0.2, noise_std=0, dropout=0, latency_ticks=0)
    observation, _ = RoverEnv(config).reset()
    observation["ego"][0] = config.max_speed
    result = draft_labels(observation, config)
    for name in ("path_blocked", "clear_sector", "speed_tier"):
        assert result["answers"][name]["value"] is None
        assert result["answers"][name]["reason"] == "envelope_outside_sensor_range"


def test_draft_config_and_input_provenance_change_independently(draft_observation):
    from dataclasses import replace

    config, observation = draft_observation
    first = draft_labels(observation, config)
    changed = draft_labels(observation, replace(config, radius=0.2))
    assert changed["config_sha256"] != first["config_sha256"]
    assert changed["input_sha256"] == first["input_sha256"]
    observation["tof_m"][0, 0] = 1
    changed = draft_labels(observation, config)
    assert changed["config_sha256"] == first["config_sha256"]
    assert changed["input_sha256"] != first["input_sha256"]
    assert changed["catalogue_sha256"] == first["catalogue_sha256"]
    assert changed["labeler_sha256"] == first["labeler_sha256"]


def test_draft_rejects_nonzero_invalid_cells_and_missing_fields(draft_observation):
    config, observation = draft_observation
    observation["tof_valid"][0, 0] = False
    with pytest.raises(ValueError, match="must contain zero"):
        draft_labels(observation, config)
    del observation["tof_m"]
    with pytest.raises(ValueError, match="missing required"):
        draft_labels(observation, config)


def test_label_coverage_preserves_zero_options_and_separates_abstentions(
    draft_observation,
):
    config, observation = draft_observation
    stale = deepcopy(observation)
    stale.update(tick=4, tof_age_s=4 * config.dt)
    warmup = deepcopy(observation)
    warmup.update(tof_sample_tick=None, tof_age_s=config.dt)
    warmup["tof_valid"][:] = False
    warmup["tof_m"][:] = 0
    labels = [draft_labels(value, config) for value in (observation, stale, warmup)]
    original = deepcopy(labels)
    coverage = answer_coverage(iter(labels))
    assert coverage["path_blocked"] == {
        "option_counts": {"false": 1, "true": 0},
        "answered": 1,
        "abstained": 2,
        "abstention_counts": {"stale_tof": 1, "no_tof_sample": 1},
        "missing_options": ["true"],
        "all_options_observed": False,
    }
    assert coverage["mode"]["answered"] == 0
    assert coverage["mode"]["abstention_counts"] == {"human_review_required": 3}
    assert coverage["speed_tier"]["missing_options"] == ["0", "1", "2"]
    assert all(row["answered"] + row["abstained"] == 3 for row in coverage.values())
    assert labels == original


def test_label_coverage_empty_input_does_not_claim_coverage():
    coverage = answer_coverage([])
    for question in draft_catalogue()["questions"]:
        row = coverage[question["name"]]
        assert row["missing_options"] == question["options"]
        assert row["answered"] == row["abstained"] == 0
        assert not row["all_options_observed"]


def test_label_coverage_study_is_bounded_reproducible_and_keeps_origins_separate(
    tmp_path,
):
    import hashlib

    output = tmp_path / "coverage"
    report = coverage_suite(output, seed=17)
    replay = coverage_suite(tmp_path / "replay", seed=17)
    assert report["cases"] == replay["cases"]
    assert report["synthetic_fixtures"] == replay["synthetic_fixtures"]
    assert len(report["cases"]) == 8 <= report["episode_limit"] == 16
    assert report["episode_observation_count"] == 8 * 33
    assert report["default_config"] == Config().__dict__
    assert report["config"] == {**Config().__dict__, "max_ticks": 32}
    assert report["config_overrides"] == {"max_ticks": 32}
    for flag in (
        "training_approved",
        "live_teacher_labeling_approved",
        "physical_safety_claim",
        "representative_task_coverage_claim",
        "policy_review_passed",
    ):
        assert not report[flag]
    for case in report["cases"]:
        path = output / case["file"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == case["sha256"]
        records = [json.loads(line) for line in path.read_text().splitlines()]
        assert records[0]["diagnostic_only"] and not records[0]["training_approved"]
        assert records[0]["policy_purpose"] == "coverage_probe_not_navigation_expert"
        config = Config(**report["config"])
        labels = [
            draft_labels(row["observation"], config)
            for row in records
            if "observation" in row
        ]
        assert labels == [
            row["simulation_label"] for row in records if "observation" in row
        ]
        assert answer_coverage(labels) == case["coverage"]
        assert not case["summary"]["collision"] and case["summary"]["timeout"]
    for case in report["synthetic_fixtures"]:
        assert case["origin"] == "synthetic_current_observation_only"
        assert case["label"] == draft_labels(case["observation"], config)
    assert len(report["synthetic_fixtures"]) == 12
    for name in ("path_blocked", "clear_sector", "speed_tier"):
        assert report["synthetic_coverage"][name]["all_options_observed"]
    assert report["episode_coverage"]["mode"]["answered"] == 0
    assert report["synthetic_coverage"]["mode"]["answered"] == 0
    assert report["synthetic_coverage"]["path_blocked"]["abstention_counts"] == {
        "no_tof_sample": 1,
        "stale_tof": 1,
        "incomplete_centre_coverage": 1,
    }
    assert (
        report["synthetic_coverage"]["clear_sector"]["abstention_counts"][
            "incomplete_sector_coverage"
        ]
        == 2
    )
    assert json.loads((output / "report.json").read_text()) == report
    with pytest.raises(FileExistsError):
        coverage_suite(output)


@pytest.mark.parametrize("seed", [-1, True, 2**63])
def test_label_coverage_study_rejects_invalid_seed_before_creating_output(
    tmp_path, seed
):
    output = tmp_path / "invalid-coverage"
    with pytest.raises(ValueError, match="seed"):
        coverage_suite(output, seed=seed)
    assert not output.exists()


@pytest.mark.parametrize("coverage", [False, True])
def test_label_coverage_cli_is_opt_in_and_preserves_default_smoke(
    tmp_path, monkeypatch, capsys, coverage
):
    from sim.labels import main

    called = []

    def run(output, *, seed):
        called.append((output, seed))
        return (
            {"episode_coverage": {"probe": True}}
            if coverage
            else {"all_scenes_succeeded": True}
        )

    def forbidden(*args, **kwargs):
        pytest.fail("nonselected smoke mode must not execute")

    monkeypatch.setattr("sim.labels.coverage_suite", run if coverage else forbidden)
    monkeypatch.setattr("sim.labels.smoke_suite", forbidden if coverage else run)
    output = tmp_path / "episodes"
    report_path = tmp_path / "report.json"
    arguments = [
        "labels",
        "--output",
        str(output),
        "--report",
        str(report_path),
        "--seed",
        "23",
    ]
    if coverage:
        arguments.append("--coverage-study")
    monkeypatch.setattr("sys.argv", arguments)
    main()
    assert called == [(output, 23)]
    summary = json.loads(capsys.readouterr().out)
    assert not summary["training_approved"]
    key = "episode_coverage" if coverage else "all_scenes_succeeded"
    assert summary[key] == json.loads(report_path.read_text())[key]
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 2 and len(called) == 1


def test_label_coverage_study_requires_smoke_approval_before_output(
    tmp_path, monkeypatch
):
    catalogue = draft_catalogue()
    catalogue["scope_approval"]["simulation_smoke"] = False
    monkeypatch.setattr("sim.labels.draft_catalogue", lambda: catalogue)
    output = tmp_path / "not-approved"
    with pytest.raises(ValueError, match="not approved"):
        coverage_suite(output)
    assert not output.exists()


def test_label_smoke_is_repeatable_exclusive_and_never_labels_mode(tmp_path):
    import hashlib

    config = Config(max_ticks=3)
    output = tmp_path / "smoke"
    report = smoke_suite(output, seed=7, config=config)
    replay = smoke_suite(tmp_path / "replay", seed=7, config=config)
    assert report["cases"] == replay["cases"]
    assert len(report["cases"]) == 4
    assert not report["training_approved"]
    assert not report["live_teacher_labeling_approved"]
    for row in report["cases"]:
        path = output / row["file"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"]
        records = [json.loads(line) for line in path.read_text().splitlines()]
        for record in records:
            if "observation" in record:
                labels = record["simulation_label"]
                assert labels == draft_labels(record["observation"], config)
                assert labels["answers"]["mode"]["value"] is None
        assert row["answer_counts"]["mode"] == {"abstain:human_review_required": 4}
    with pytest.raises(FileExistsError):
        smoke_suite(output, config=config)


@pytest.mark.parametrize("seed", [-1, True, 2**63])
def test_label_smoke_rejects_invalid_seed_before_creating_output(tmp_path, seed):
    output = tmp_path / "invalid"
    with pytest.raises(ValueError, match="seed"):
        smoke_suite(output, seed=seed)
    assert not output.exists()


def test_rays_hit_nearest_obstacle_and_wall():
    ranges = ray_ranges(
        [1, 2],
        np.array([0, math.pi / 2, math.pi]),
        ((3, 2, 0.5), (4, 2, 0.5)),
        (6, 6),
        4,
    )
    assert ranges == pytest.approx([1.5, 4, 1])


def test_parallel_and_tangent_rays_remain_finite():
    ranges = ray_ranges([1, 2], np.array([0, math.pi / 2]), ((3, 3, 1),), (6, 6), 4)
    assert ranges == pytest.approx([2, 4])
    assert np.isfinite(ranges).all()


def test_swept_collision_prevents_tunneling_and_checks_arena_boundary():
    assert swept_collision([1, 2], [5, 2], 0.2, ((3, 2, 0.1),), (6, 6))
    assert not swept_collision([1, 1], [5, 1], 0.2, ((3, 2, 0.1),), (6, 6))
    assert swept_collision([1, 1], [0.1, 1], 0.2, (), (6, 6))


def test_constant_twist_integrates_straight_and_curved_motion():
    position, yaw = integrate([1, 1], 0, 1, 0, 1)
    assert position == pytest.approx([2, 1])
    assert yaw == 0
    position, yaw = integrate([1, 1], 0, 1, math.pi / 2, 1)
    assert position == pytest.approx([1 + 2 / math.pi, 1 + 2 / math.pi])
    assert yaw == pytest.approx(math.pi / 2)


def test_reset_is_seeded_with_stable_shapes_and_no_ground_truth_leak():
    env = RoverEnv()
    first, _ = env.reset(seed=4)
    second, _ = env.reset(seed=4)
    assert first.keys() == second.keys()
    for key in first:
        np.testing.assert_equal(first[key], second[key])
    assert first["tof_m"].shape == (8, 8)
    assert first["history_tof_m"].shape == (8, 8, 8)
    assert first["history_ego"].shape == (8, 4)
    assert first["history_valid"].sum() == 1
    assert "ground_truth" not in first


def test_latency_dropout_and_sensor_timestamp_are_explicit():
    env = RoverEnv(Config(noise_std=0, dropout=0, latency_ticks=2))
    observation, _ = env.reset()
    assert not observation["tof_valid"].any()
    assert observation["tof_sample_tick"] is None
    observation, *_ = env.step([0, 0])
    assert not observation["tof_valid"].any()
    observation, *_ = env.step([0, 0])
    assert observation["tof_valid"].all()
    assert observation["tof_sample_tick"] == 0
    assert observation["tof_age_s"] == pytest.approx(0.1)
    dropped, _ = RoverEnv(Config(dropout=1, latency_ticks=0)).reset()
    assert not dropped["tof_valid"].any()
    assert np.isfinite(dropped["tof_m"]).all()


def test_actions_are_bounded_and_invalid_action_does_not_advance():
    env = RoverEnv()
    with pytest.raises(ValueError, match="finite"):
        env.step([float("nan"), 0])
    assert env.tick == 0
    observation, *_ = env.step([100, 100])
    assert observation["ego"][0] == pytest.approx(
        env.config.acceleration * env.config.dt
    )
    assert observation["ego"][1] == pytest.approx(env.config.max_turn_rate)


def test_goal_timeout_collision_and_reset_semantics():
    env = RoverEnv(scenario=Scenario(goal=(1.1, 3)))
    _, reward, terminated, truncated, info = env.step([0, 0])
    assert terminated and not truncated and info["success"] and reward > 0
    with pytest.raises(RuntimeError, match="reset"):
        env.step([0, 0])
    env = RoverEnv(Config(max_ticks=1))
    _, _, terminated, truncated, info = env.step([0, 0])
    assert not terminated and truncated and info["timeout"]
    env = RoverEnv(
        Config(dt=1, max_speed=5, acceleration=100), Scenario(obstacles=((3, 3, 0.2),))
    )
    _, reward, terminated, _, info = env.step([5, 0])
    assert terminated and info["collision"] and reward < 0
    assert info["ground_truth"]["position_m"] == pytest.approx([1, 3])


@pytest.mark.parametrize(
    "kwargs",
    [
        {"dt": 0},
        {"dropout": 2},
        {"latency_ticks": -1},
        {"history_ticks": 1.5},
        {"noise_std": float("nan")},
    ],
)
def test_invalid_simulation_configuration_is_rejected(kwargs):
    with pytest.raises(ValueError):
        Config(**kwargs)


def test_episode_logs_are_reproducible_and_never_overwritten(tmp_path):
    env = RoverEnv(Config(max_ticks=3), make_scenario("obstacle", 5))
    env.reset(seed=5)
    records, summary = rollout(env)
    duplicate, _ = rollout(env)
    assert json.dumps(records, default=json_value) == json.dumps(
        duplicate, default=json_value
    )
    assert summary["timeout"] and summary["ticks"] == 3
    path = tmp_path / "episode.jsonl"
    write_episode(path, records)
    decoded = [json.loads(line) for line in path.read_text().splitlines()]
    assert decoded[0]["schema"] == "micro-classifier/sim-episode/1"
    assert len(decoded) == 5
    with pytest.raises(FileExistsError):
        write_episode(path, records)


def test_scripted_expert_reaches_clear_goal_and_handles_missing_sensor():
    env = RoverEnv()
    observation, _ = env.reset()
    assert np.array_equal(ScriptedExpert(env)(observation), [0, 0])
    _, summary = rollout(env)
    assert summary["success"] and not summary["collision"]


@pytest.mark.parametrize("name", ["clear", "obstacle", "corridor", "slalom"])
def test_scenarios_are_seeded_valid_and_roll_out_without_nonfinite_values(name):
    scenario = make_scenario(name, 12)
    assert scenario == make_scenario(name, 12)
    env = RoverEnv(Config(max_ticks=10), scenario)
    records, _ = rollout(env)
    json.dumps(records, default=json_value, allow_nan=False)


@pytest.mark.parametrize("name", ["obstacle", "slalom"])
def test_map_expert_completes_obstacle_scenarios_without_collision(name):
    records, summary = rollout(RoverEnv(scenario=make_scenario(name, 0)))
    assert records[0]["privileged_expert"]
    assert summary["success"] and not summary["collision"]


def test_wire_export_encodes_current_host_inputs_and_unknown_health():
    from interface.protocol import UINT32_MAX, decode_state, encode_state

    records, _ = rollout(RoverEnv(Config(max_ticks=3)))
    exported = with_wire_frames(records)
    assert exported[0]["wire_contract"]["state_frame_bytes"] == 92
    assert not exported[0]["wire_contract"]["decision_frames"]
    assert exported[0]["privileged_expert"]
    for original, entry in zip(records, exported, strict=True):
        assert "state_frame_hex" not in original
        assert "decision_frame_hex" not in entry
        if "observation" not in entry:
            assert "state_frame_hex" not in entry
            continue
        frame = bytes.fromhex(entry["state_frame_hex"])
        packet = decode_state(frame)
        observation = entry["observation"]
        assert packet.sequence == observation["tick"]
        assert packet.timestamp_us == round(observation["time_s"] * 1_000_000)
        assert packet.velocity_m_s == pytest.approx((observation["ego"][0], 0, 0))
        assert packet.angular_velocity_rad_s == pytest.approx(
            (0, 0, observation["ego"][1])
        )
        assert packet.goal_m == pytest.approx((*observation["goal_body_m"], 0))
        assert packet.validity == 7
        assert packet.ages_us == (0, 0, 0, UINT32_MAX, UINT32_MAX)
        assert packet.battery_fraction == packet.faults == 0
        assert encode_state(packet) == frame


def test_wire_state_excludes_truth_action_tof_and_history():
    records, _ = rollout(RoverEnv(Config(max_ticks=2)))
    changed = deepcopy(records)
    for record in changed:
        if "observation" in record:
            record["info"]["ground_truth"] = {"unrelated": 12345}
            observation = record["observation"]
            observation["tof_m"][:] = 99
            observation["history_ego"][:] = 99
            observation["tof_age_s"] = 99
        if "action" in record:
            record["action"][:] = 99
    original = with_wire_frames(records)
    altered = with_wire_frames(changed)
    assert [entry.get("state_frame_hex") for entry in original] == [
        entry.get("state_frame_hex") for entry in altered
    ]


def test_wire_log_export_is_reproducible_and_json_round_trips(tmp_path):
    from interface.protocol import decode_state

    records, _ = rollout(RoverEnv(Config(max_ticks=3)))
    first = with_wire_frames(records)
    second = with_wire_frames(records)
    assert json.dumps(first, default=json_value) == json.dumps(
        second, default=json_value
    )
    path = tmp_path / "wire.jsonl"
    write_episode(path, first)
    decoded = [json.loads(line) for line in path.read_text().splitlines()]
    assert decoded[0]["wire_contract"]["provisional"]
    assert len([row for row in decoded if "state_frame_hex" in row]) == 4
    for row in decoded:
        if "state_frame_hex" in row:
            decode_state(bytes.fromhex(row["state_frame_hex"]))
    with pytest.raises(FileExistsError):
        write_episode(path, second)


def test_wire_counters_wrap_without_losing_observation_timing():
    from interface.protocol import UINT32_MAX

    observation, _ = RoverEnv().reset()
    observation["tick"] = UINT32_MAX + 3
    observation["time_s"] = (UINT32_MAX + 101) / 1_000_000
    packet = state_from_observation(observation)
    assert packet.sequence == 2
    assert packet.timestamp_us == 100


@pytest.mark.parametrize(
    "changes", [{"tick": -1}, {"tick": True}, {"time_s": float("nan")}, {"ego": [0, 0]}]
)
def test_wire_export_rejects_invalid_observation(changes):
    observation, _ = RoverEnv().reset()
    observation.update(changes)
    with pytest.raises(ValueError):
        state_from_observation(observation)


def test_wire_cli_exports_real_frames(tmp_path, monkeypatch, capsys):
    from sim.rover import main

    config = tmp_path / "config.json"
    config.write_text(json.dumps({"max_ticks": 3}))
    monkeypatch.setattr(
        "sys.argv",
        ["sim.rover", "--wire", "--output", str(tmp_path), "--config", str(config)],
    )
    main()
    summary = json.loads(capsys.readouterr().out)
    assert summary["ticks"] == 3 and summary["timeout"]
    rows = [json.loads(line) for line in Path(summary["path"]).read_text().splitlines()]
    assert rows[0]["wire_contract"]["protocol_version"] == 0
    assert len(bytes.fromhex(rows[0]["state_frame_hex"])) == 92
