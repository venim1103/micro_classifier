"""Privileged simulator sensor diagnostics, never task labels or physical metrology."""

import argparse
import hashlib
import json
import math
import platform
from copy import deepcopy
from dataclasses import asdict, replace
from fractions import Fraction
from itertools import pairwise
from pathlib import Path

import numpy as np

from sim.rover import (
    Config,
    RoverEnv,
    json_value,
    make_scenario,
    tof_directions,
    tof_ranges,
    write_episode,
)

SCENES = ("clear", "obstacle", "corridor", "slalom")
C1_SCHEMA = "micro-classifier/synthetic-c1-views/1"
_SYNTHETIC_ARITHMETIC_BITS = 4096


_SYNTHETIC_SINC_BITS = 65536


_SYNTHETIC_SINC_CELL_BITS = 65536
_SYNTHETIC_SINC_CELL_STEPS = 64


_SYNTHETIC_CELL_CHECK_BITS = 65536


_SYNTHETIC_BIND_CHECK_BITS = 65536


_SYNTHETIC_COMPOSITION_BITS = 65536


_SYNTHETIC_TARGET_CHECK_BITS = 65536


_SYNTHETIC_TARGET_JOIN_BITS = 65536


class _C1CommandArithmetic:
    """Work-limited rational arithmetic for the isolated command fixture."""

    def __init__(self, max_terms, max_bits, work):
        self.max_terms = max_terms
        self.max_bits = max_bits
        self.work = work

    def value(self, value):
        if type(value) not in (int, float):
            raise ValueError("command fixture values must be finite real numbers")
        try:
            number = float(value)
        except OverflowError as error:
            raise ValueError("command fixture value is unrepresentable") from error
        if not math.isfinite(number):
            raise ValueError("command fixture values must be finite real numbers")
        numerator, denominator = number.as_integer_ratio()
        if max(abs(numerator).bit_length(), denominator.bit_length()) > self.max_bits:
            raise ArithmeticError("integer_budget_exhausted")
        return Fraction(numerator, denominator)

    def binary(self, left, right, operation):
        left_num, left_den = (
            abs(left.numerator).bit_length(),
            left.denominator.bit_length(),
        )
        right_num, right_den = (
            abs(right.numerator).bit_length(),
            right.denominator.bit_length(),
        )
        if operation in ("add", "sub", "less"):
            growth = max(left_num + right_den, right_num + left_den) + 1
            denominator = left_den + right_den
        elif operation == "mul":
            growth, denominator = left_num + right_num, left_den + right_den
        elif operation == "div":
            if right == 0:
                raise ArithmeticError("undefined_fixture_arithmetic")
            growth, denominator = left_num + right_den, left_den + right_num
        else:
            raise ValueError("unsupported fixture operation")
        if max(growth, denominator) > self.max_bits:
            raise ArithmeticError("integer_budget_exhausted")
        if operation == "add":
            return left + right
        if operation == "sub":
            return left - right
        if operation == "mul":
            return left * right
        if operation == "div":
            return left / right
        return left < right

    def bounds(self, values):
        lower = upper = values[0]
        for value in values[1:]:
            if self.binary(value, lower, "less"):
                lower = value
            if self.binary(upper, value, "less"):
                upper = value
        return lower, upper

    def product(self, left, right):
        return self.bounds(
            [self.binary(first, second, "mul") for first in left for second in right]
        )

    def plus(self, left, right):
        return tuple(
            self.binary(first, second, "add") for first, second in zip(left, right)
        )

    def clip(self, value, lower, upper):
        if self.binary(value, lower, "less"):
            return lower
        if self.binary(upper, value, "less"):
            return upper
        return value

    def speed_step(self, speeds, target, change):
        return tuple(
            self.binary(
                speed,
                self.clip(self.binary(target, speed, "sub"), -change, change),
                "add",
            )
            for speed in speeds
        )

    def trig(self, angle):
        if self.max_terms == 0:
            raise ArithmeticError("series_term_budget_exhausted")
        if not self.binary(abs(angle), self.value(1), "less"):
            raise ArithmeticError("unsupported_arc_domain")
        square = self.binary(angle, angle, "mul")
        intervals = []
        for offset, initial in ((0, self.value(1)), (1, angle)):
            total, term = self.value(0), initial
            for index in range(8):
                if self.work["series_terms"] >= self.max_terms:
                    raise ArithmeticError("series_term_budget_exhausted")
                self.work["series_terms"] += 1
                if index:
                    divisor = self.value(
                        (2 * index - 1 + offset) * (2 * index + offset)
                    )
                    term = -self.binary(
                        self.binary(term, square, "mul"), divisor, "div"
                    )
                if index < 7:
                    total = self.binary(total, term, "add")
                else:
                    intervals.append(
                        self.bounds((total, self.binary(total, term, "add")))
                    )
        return intervals

    def outward(self, value, upward):
        number = float(value)
        if not math.isfinite(number):
            raise ArithmeticError("unsupported_outward_conversion")
        rounded = self.value(number)
        if (
            self.binary(rounded, value, "less")
            if upward
            else self.binary(value, rounded, "less")
        ):
            number = math.nextafter(number, math.inf if upward else -math.inf)
        if not math.isfinite(number):
            raise ArithmeticError("unsupported_outward_conversion")
        rounded = self.value(number)
        if (
            self.binary(rounded, value, "less")
            if upward
            else self.binary(value, rounded, "less")
        ):
            raise ArithmeticError("unsupported_outward_conversion")
        return number

    def box(self, point):
        return [
            [self.outward(lower, False), self.outward(upper, True)]
            for lower, upper in point
        ]


def _probe_synthetic_c1_discrete_motion(
    *,
    initial_speed,
    target_speed,
    turn_rate,
    error_evidence=None,
    profile=None,
    hold_ticks=1,
    max_braking_ticks=16,
    max_chords=128,
    max_terms=16,
    max_integer_bits=16384,
    synthetic_test_only=False,
):
    """Enclose an ideal discrete command/braking fixture, never an actual permit."""
    if synthetic_test_only is not True:
        raise ValueError("discrete command fixture requires synthetic_test_only=True")
    for limit, lower, upper in (
        (max_braking_ticks, 0, 16),
        (max_chords, 0, 128),
        (max_terms, 0, 16),
        (max_integer_bits, 1, 16384),
    ):
        if type(limit) is not int or not lower <= limit <= upper:
            raise ValueError("discrete command work limits must be bounded integers")
    work = {"command_ticks": 0, "braking_ticks": 0, "chords": 0, "series_terms": 0}
    result = {
        "schema": "micro-classifier/synthetic-c1-discrete-motion/1",
        "allowed_use": "conditional_ideal_motion_fixture_only",
        "training_approved": False,
        "real_input_qualified": False,
        "free_space_qualified": False,
        "numerically_certified": False,
        "source_qualified": False,
        "native_execution_qualified": False,
        "command_admission_qualified": False,
        "fixture_motion_enclosed": False,
        "status": "unknown",
        "reason": "error_evidence_missing",
        "work": work,
    }
    expected_profile = {
        "dt": 0.05,
        "acceleration": 1.0,
        "max_speed": 0.6,
        "max_turn_rate": 1.5,
        "radius": 0.18,
    }
    profile = expected_profile if profile is None else profile
    arithmetic = _C1CommandArithmetic(max_terms, max_integer_bits, work)
    try:
        raw_speeds = (
            initial_speed
            if type(initial_speed) in (tuple, list)
            else (initial_speed, initial_speed)
        )
        if len(raw_speeds) != 2:
            raise ValueError("initial speed requires a scalar or two endpoints")
        speeds = tuple(arithmetic.value(value) for value in raw_speeds)
        target, angular_rate = (
            arithmetic.value(target_speed),
            arithmetic.value(turn_rate),
        )
        if (
            type(hold_ticks) is not int
            or hold_ticks != 1
            or type(profile) is not dict
            or set(profile) != set(expected_profile)
            or any(type(profile[key]) is not float for key in expected_profile)
            or profile != expected_profile
        ):
            result["reason"] = "unsupported_profile_or_hold"
            return result
        if error_evidence is None:
            return result
        if (
            type(error_evidence) is not dict
            or set(error_evidence)
            != {"position_error_m", "heading_error_rad", "profile_exact"}
            or error_evidence["profile_exact"] is not True
        ):
            result["reason"] = "unsupported_error_evidence"
            return result
        position_error = arithmetic.value(error_evidence["position_error_m"])
        heading_error = arithmetic.value(error_evidence["heading_error_rad"])
        zero, one = arithmetic.value(0), arithmetic.value(1)
        seconds = arithmetic.value(profile["dt"])
        change = arithmetic.binary(
            arithmetic.value(profile["acceleration"]), seconds, "mul"
        )
        maximum = arithmetic.value(profile["max_speed"])
        yaw_maximum = arithmetic.value(profile["max_turn_rate"])
        if (
            arithmetic.binary(speeds[0], zero, "less")
            or arithmetic.binary(speeds[1], speeds[0], "less")
            or arithmetic.binary(maximum, speeds[1], "less")
            or arithmetic.binary(position_error, zero, "less")
            or arithmetic.binary(heading_error, zero, "less")
        ):
            result["reason"] = "unsupported_error_evidence"
            return result
        target = arithmetic.clip(target, zero, maximum)
        angular_rate = arithmetic.clip(angular_rate, -yaw_maximum, yaw_maximum)
        if max_chords == 0:
            raise ArithmeticError("chord_budget_exhausted")
        work["command_ticks"] = 1
        speeds = arithmetic.speed_step(speeds, target, change)
        command_speeds = speeds
        angle = arithmetic.binary(angular_rate, seconds, "mul")
        cosine, sine = arithmetic.trig(angle) if angle else ((one, one), (zero, zero))
        if angular_rate:
            inverse = arithmetic.binary(one, angular_rate, "div")
            unit_step = (
                arithmetic.product(sine, (inverse, inverse)),
                arithmetic.product(
                    (
                        arithmetic.binary(one, cosine[1], "sub"),
                        arithmetic.binary(one, cosine[0], "sub"),
                    ),
                    (inverse, inverse),
                ),
            )
        else:
            unit_step = ((seconds, seconds), (zero, zero))
        position = tuple(
            arithmetic.product(speeds, component) for component in unit_step
        )
        vertices = [((zero, zero), (zero, zero)), position]
        speed_steps = [speeds]
        work["chords"] = 1
        length_upper = arithmetic.binary(speeds[1], seconds, "mul")
        sagitta = arithmetic.binary(
            arithmetic.binary(length_upper, abs(angle), "mul"),
            arithmetic.value(8),
            "div",
        )
        while speeds[1] != zero:
            if work["braking_ticks"] >= max_braking_ticks:
                raise ArithmeticError("braking_budget_exhausted")
            if work["chords"] >= max_chords:
                raise ArithmeticError("chord_budget_exhausted")
            work["braking_ticks"] += 1
            work["chords"] += 1
            speeds = arithmetic.speed_step(speeds, zero, change)
            distances = arithmetic.product(speeds, (seconds, seconds))
            displacement = tuple(
                arithmetic.product(distances, direction) for direction in (cosine, sine)
            )
            position = tuple(
                arithmetic.plus(component, step)
                for component, step in zip(position, displacement)
            )
            vertices.append(position)
            speed_steps.append(speeds)
            length_upper = arithmetic.binary(length_upper, distances[1], "add")
        body_radius = arithmetic.binary(
            arithmetic.binary(
                arithmetic.value(profile["radius"]), position_error, "add"
            ),
            arithmetic.binary(length_upper, heading_error, "mul"),
            "add",
        )
        boxes = [arithmetic.box(point) for point in vertices]
        chords = [
            {
                "start_box_m": boxes[index],
                "end_box_m": boxes[index + 1],
                "radius_upper_m": arithmetic.outward(
                    arithmetic.binary(
                        body_radius, sagitta if index == 0 else zero, "add"
                    ),
                    True,
                ),
            }
            for index in range(work["chords"])
        ]
        result.update(
            status="enclosed_under_fixture_assumptions",
            reason="complete_ideal_command_and_discrete_braking_enclosure",
            fixture_motion_enclosed=True,
            assumption="stored_input_words_as_reals_not_native_execution",
            centerline_boxes_m=boxes,
            chords=chords,
            speed_intervals_m_s=[
                [arithmetic.outward(lower, False), arithmetic.outward(upper, True)]
                for lower, upper in speed_steps
            ],
            command_speed_interval_m_s=[
                arithmetic.outward(command_speeds[0], False),
                arithmetic.outward(command_speeds[1], True),
            ],
            command_sagitta_upper_m=arithmetic.outward(sagitta, True),
        )
    except ArithmeticError as error:
        result["reason"] = str(error)
    return result


def _check_synthetic_sinc_target_cell_join(
    expected_q_word, candidate_record, enclosure_record, *, synthetic_test_only=False
):
    """Join independently checked target and cell contents, never native evidence."""
    if synthetic_test_only is not True:
        raise ValueError("target-cell join requires synthetic_test_only=True")
    zero = type(expected_q_word) is int and expected_q_word in (0, 1 << 63)
    limits = (
        _SYNTHETIC_TARGET_JOIN_BITS,
        _SYNTHETIC_TARGET_CHECK_BITS,
        _SYNTHETIC_COMPOSITION_BITS,
        _SYNTHETIC_BIND_CHECK_BITS,
        None if zero else _SYNTHETIC_CELL_CHECK_BITS,
    )
    flags = {
        "training_approved",
        "real_input_qualified",
        "free_space_qualified",
        "numerically_certified",
        "producer_parity_qualified",
    }
    statuses = {
        "native_sinc_status": "unresolved_native_sinc_evidence",
        "motion_status": "unresolved_motion_evidence",
        "source_status": "unresolved_source_authority",
        "native_work_status": "unresolved_native_work_evidence",
        "consumer_status": "ineligible_isolated_candidate",
    }
    work = {
        "join_entries": 1,
        "target_entries": 0,
        "composition_entries": 0,
        "target": None,
        "composition": None,
    }
    result = {
        "identity": "synthetic_sinc_target_cell_join_v0",
        "allowed_use": "isolated_synthetic_sinc_target_cell_join_only",
        "status": "unresolved_synthetic_sinc_target_cell_join",
        "reason": "unsupported_target_cell_join",
        "configuration": {
            key: value if type(value) is int and 1 <= value <= 65536 else None
            for key, value in zip(
                (
                    "raw_copy_bit_limit",
                    "target_bit_limit",
                    "composition_bit_limit",
                    "binding_bit_limit",
                    "cell_bit_limit",
                ),
                limits,
                strict=True,
            )
        },
        **{flag: False for flag in flags},
        **statuses,
        "work": work,
    }
    if any(
        type(value) is not int or not 1 <= value <= 65536
        for value in limits[:4] + (() if zero else limits[4:])
    ):
        result["reason"] = "unsupported_target_join_configuration"
        return result
    limit = limits[0]
    profile = {"arctangent_terms": 32, "sinc_terms": 8, "rational_bit_limit": 65536}

    class JoinStop(ArithmeticError):
        pass

    def require(condition):
        if not condition:
            raise JoinStop("inconsistent_target_cell_join")

    def live():
        current = (
            _SYNTHETIC_TARGET_JOIN_BITS,
            _SYNTHETIC_TARGET_CHECK_BITS,
            _SYNTHETIC_COMPOSITION_BITS,
            _SYNTHETIC_BIND_CHECK_BITS,
            None if zero else _SYNTHETIC_CELL_CHECK_BITS,
        )
        require(all(type(value) is int for value in current[:4]))
        require(zero or type(current[4]) is int)
        require(current == limits)

    def shape(value, keys):
        require(type(value) is dict and len(value) == len(keys))
        require(
            all(type(key) is str and len(key) <= 32 and key in keys for key in value)
        )

    def number(value, minimum=None, maximum=None):
        require(type(value) is int)
        require(minimum is None or value >= minimum)
        require(maximum is None or value <= maximum)
        require(value.bit_length() <= limit)

    def sequence(value, length, check):
        require(type(value) is tuple and len(value) == length)
        for item in value:
            check(item)

    def pair(value):
        require(type(value) is tuple and len(value) == 2)
        number(value[0])
        number(value[1], 1)

    def interval(value):
        sequence(value, 2, pair)

    def configuration(value):
        shape(value, profile)
        for key in profile:
            number(value[key], 1, 65536)
        require(value == profile)

    def stages(value):
        shape(
            value,
            set()
            if zero
            else {
                "arctangent",
                "pi",
                "squared_argument",
                "coefficients",
                "polynomial",
                "remainder",
            },
        )
        if not zero:
            sequence(value["arctangent"], 2, interval)
            for key in ("pi", "squared_argument", "polynomial", "remainder"):
                interval(value[key])
            sequence(value["coefficients"], 8, pair)

    def neighbor(value):
        require(type(value) is tuple and len(value) == 2)
        number(value[0], 0, 0x7FEFFFFFFFFFFFFF)
        pair(value[1])

    def certificate(value):
        shape(
            value,
            {"word", "interval", "branch"}
            if zero
            else {
                "word",
                "interval",
                "neighbors",
                "boundaries",
                "closed_ties",
                "lower_order",
                "upper_order",
                "whole_interval_contained",
            },
        )
        number(value["word"], 1, 0x7FEFFFFFFFFFFFFE)
        interval(value["interval"])
        if zero:
            require(type(value["branch"]) is str and value["branch"] == "zero")
            require(value["word"] == 0x3FF0000000000000)
            require(value["interval"] == ((1, 1), (1, 1)))
        else:
            sequence(value["neighbors"], 3, neighbor)
            interval(value["boundaries"])
            require(type(value["closed_ties"]) is bool)
            require(type(value["whole_interval_contained"]) is bool)
            require(value["whole_interval_contained"] is True)
            for key in ("lower_order", "upper_order"):
                number(value[key], -1, 1)

    def producer_work(value):
        shape(value, {"rational_operations", "max_result_bits"})
        number(value["rational_operations"], 0, (1 << 64) - 1)
        number(value["max_result_bits"], 0, 65536)

    def input_record(value, candidate):
        common = {
            "allowed_use",
            "status",
            "reason",
            "target",
            "q_word",
            "work",
            "sign",
            "q_ratio",
            "configuration",
            "interval",
            "native_sinc_status",
            "motion_status",
        } | flags
        extra = (
            {
                "identity",
                "source_status",
                "native_work_status",
                "consumer_status",
                "certificate",
                "enclosure_binding",
            }
            if candidate
            else {"domain_ratio", "branch", "stages"}
        )
        shape(value, common | extra)
        selectors = {
            "allowed_use": "isolated_synthetic_sinc_word_candidate_only"
            if candidate
            else "isolated_synthetic_sinc_reference_only",
            "status": "candidate_mathematical_sinc_word"
            if candidate
            else "enclosed_mathematical_sinc",
            "reason": "conditional_mathematical_rounding_cell_only"
            if candidate
            else (
                "exact_mathematical_zero_branch"
                if zero
                else "real_pi_even_series_enclosure_only"
            ),
            "target": "real_pi_normalized_sinc_at_stored_binary64",
            "native_sinc_status": statuses["native_sinc_status"],
            "motion_status": statuses["motion_status"],
        }
        if candidate:
            selectors.update(
                identity="controlled_mathematical_sinc_rn64_candidate_v0",
                **{
                    key: statuses[key]
                    for key in (
                        "source_status",
                        "native_work_status",
                        "consumer_status",
                    )
                },
            )
        else:
            selectors["branch"] = "zero" if zero else "series"
        require(
            all(
                type(value[key]) is str and value[key] == expected
                for key, expected in selectors.items()
            )
        )
        require(all(type(value[key]) is bool and value[key] is False for key in flags))
        number(value["q_word"], 0, (1 << 64) - 1)
        number(value["sign"], 0, 1)
        require(
            value["q_word"] == expected_q_word
            and value["sign"] == expected_q_word >> 63
        )
        pair(value["q_ratio"])
        interval(value["interval"])
        configuration(value["configuration"])
        if candidate:
            certificate(value["certificate"])
            binding = value["enclosure_binding"]
            shape(binding, {"q_word", "sign", "q_ratio"})
            number(binding["q_word"], 0, (1 << 64) - 1)
            number(binding["sign"], 0, 1)
            pair(binding["q_ratio"])
            require(
                binding["q_word"] == expected_q_word
                and binding["sign"] == expected_q_word >> 63
            )
            declared = value["work"]
            shape(
                declared,
                {"enclosure_entries", "cell_entries", "enclosure"}
                | (set() if zero else {"cell"}),
            )
            number(declared["enclosure_entries"], 1, 1)
            number(declared["cell_entries"], 0 if zero else 1, 0 if zero else 1)
            producer_work(declared["enclosure"])
            if not zero:
                cell = declared["cell"]
                shape(
                    cell,
                    {
                        "search_iterations",
                        "endpoint_iterations",
                        "dyadic_decodes",
                        "midpoint_constructions",
                        "rational_comparisons",
                        "rational_constructions",
                        "max_result_bits",
                    },
                )
                for key in cell:
                    if key != "endpoint_iterations":
                        number(
                            cell[key],
                            0,
                            65536 if key == "max_result_bits" else (1 << 64) - 1,
                        )
                require(
                    type(cell["endpoint_iterations"]) is list
                    and len(cell["endpoint_iterations"]) == 2
                )
                for count in cell["endpoint_iterations"]:
                    number(count, 0, 64)
                require(sum(cell["endpoint_iterations"]) == cell["search_iterations"])
        else:
            pair(value["domain_ratio"])
            require(value["domain_ratio"] == (1, 64))
            stages(value["stages"])
            producer_work(value["work"])

    def owned(value):
        if type(value) is dict:
            return {key: owned(item) for key, item in value.items()}
        if type(value) is tuple:
            return tuple(owned(item) for item in value)
        if type(value) is list:
            return [owned(item) for item in value]
        return value

    report_keys = (
        {"identity", "allowed_use", "status", "reason", "configuration", "work"}
        | flags
        | set(statuses)
    )
    target_fields = {
        "q_word",
        "sign",
        "q_ratio",
        "target",
        "domain_ratio",
        "branch",
        "profile",
        "interval",
        "stages",
    }
    composition_fields = {
        "q_word",
        "sign",
        "q_ratio",
        "branch",
        "profile",
        "interval",
        "certificate",
    }

    def rational_work(value, cell, bit_limit, complete):
        keys = {
            "canonical_pair_checks",
            "dyadic_decodes",
            "rational_comparisons",
            "rational_constructions",
            "max_result_bits",
        }
        shape(value, keys | ({"midpoint_recomputations"} if cell else set()))
        for key in value:
            number(
                value[key], 0, bit_limit if key == "max_result_bits" else (1 << 64) - 1
            )
        if complete:
            expected = {
                "canonical_pair_checks": 7 if cell else (10 if zero else 35),
                "dyadic_decodes": 3 if cell else 1,
                "rational_comparisons": 3 if cell else (2 if zero else 8),
                "rational_constructions": 12 if cell else (11 if zero else 36),
            }
            if cell:
                expected["midpoint_recomputations"] = 2
            require(all(value[key] == count for key, count in expected.items()))

    def checked_report(value, target):
        require(type(value) is dict and len(value) in (16, 25 if target else 23))
        complete = len(value) != 16
        shape(
            value,
            report_keys
            | (
                (target_fields if target else composition_fields) if complete else set()
            ),
        )
        selectors = {
            "identity": "synthetic_sinc_target_content_check_v0"
            if target
            else "synthetic_sinc_composition_check_v0",
            "allowed_use": "isolated_synthetic_sinc_target_content_check_only"
            if target
            else "isolated_synthetic_sinc_composition_check_only",
            "status": (
                (
                    "checked_declared_mathematical_zero_content"
                    if zero
                    else "checked_declared_mathematical_sinc_content"
                )
                if target
                else (
                    "checked_declared_zero_binding"
                    if zero
                    else "checked_declared_binding_and_cell_content"
                )
            )
            if complete
            else (
                "unresolved_synthetic_sinc_target_content"
                if target
                else "unresolved_synthetic_sinc_composition"
            ),
            **statuses,
        }
        require(
            all(
                type(value[key]) is str and value[key] == expected
                for key, expected in selectors.items()
            )
        )
        require(type(value["reason"]) is str and len(value["reason"]) <= 64)
        require(all(type(value[key]) is bool and value[key] is False for key in flags))
        declared = value["configuration"]
        if target:
            expected = {
                "rational_bit_limit": limits[1],
                "integer_power_steps_limit": 256,
                "rational_constructions_limit": 512,
                "rational_operations_limit": 512,
                "rational_comparisons_limit": 256,
            }
        else:
            expected = {
                "raw_copy_bit_limit": limits[2],
                "binding_bit_limit": limits[3],
                "cell_bit_limit": limits[4],
            }
        shape(declared, expected)
        for key, expected_value in expected.items():
            if expected_value is None:
                require(declared[key] is None)
            else:
                number(declared[key], 1, 65536)
                require(declared[key] == expected_value)
        inner = value["work"]
        if target:
            maxima = {
                "canonical_pair_checks": 24,
                "dyadic_decodes": 1,
                "integer_power_steps": 256,
                "rational_constructions": 512,
                "rational_operations": 512,
                "rational_comparisons": 256,
                "max_result_bits": limits[1],
            }
            shape(inner, maxima)
            for key, maximum in maxima.items():
                number(inner[key], 0, maximum)
            if complete:
                counts = (4, 1, 0, 5, 0, 2) if zero else (24, 1, 147, 230, 131, 57)
                require(
                    all(
                        inner[key] == count
                        for key, count in zip(tuple(maxima)[:6], counts, strict=True)
                    )
                )
        else:
            shape(
                inner,
                {
                    "composition_entries",
                    "binding_entries",
                    "cell_entries",
                    "binding",
                    "cell",
                },
            )
            for key in ("composition_entries", "binding_entries", "cell_entries"):
                number(inner[key], 0, 1)
            require(inner["composition_entries"] == 1)
            if inner["binding"] is not None:
                rational_work(inner["binding"], False, limits[3], complete)
            if zero:
                require(inner["cell_entries"] == 0 and inner["cell"] is None)
            elif inner["cell"] is not None:
                rational_work(inner["cell"], True, limits[4], complete)
            if complete:
                require(inner["binding_entries"] == 1 and inner["binding"] is not None)
                require(inner["cell_entries"] == (0 if zero else 1))
                require(zero or inner["cell"] is not None)
        if complete:
            reason = (
                "independent_declared_stage_content_only"
                if target
                else (
                    "declared_zero_binding_only"
                    if zero
                    else "declared_binding_and_exact_cell_content_only"
                )
            )
            require(value["reason"] == reason)
            number(value["q_word"], 0, (1 << 64) - 1)
            number(value["sign"], 0, 1)
            pair(value["q_ratio"])
            interval(value["interval"])
            configuration(value["profile"])
            require(
                type(value["branch"]) is str
                and value["branch"] == ("zero" if zero else "series")
            )
            if target:
                require(
                    type(value["target"]) is str
                    and value["target"] == "real_pi_normalized_sinc_at_stored_binary64"
                )
                pair(value["domain_ratio"])
                stages(value["stages"])
            else:
                certificate(value["certificate"])
        work["target" if target else "composition"] = owned(inner)
        return complete

    try:
        number(expected_q_word, 0, (1 << 64) - 1)
        require((expected_q_word >> 52) & 2047 != 2047)
        input_record(candidate_record, True)
        input_record(enclosure_record, False)
        candidate, enclosure = owned(candidate_record), owned(enclosure_record)
        original_certificate = owned(candidate["certificate"])
        original_stages = owned(enclosure["stages"])
        original_interval = enclosure["interval"]
        original_ratio = enclosure["q_ratio"]
        require(
            candidate["interval"]
            == original_certificate["interval"]
            == original_interval
        )
        require(
            candidate["q_ratio"]
            == candidate["enclosure_binding"]["q_ratio"]
            == original_ratio
        )
        require(candidate["work"]["enclosure"] == enclosure["work"])
        target_input = owned(enclosure)
        composition_candidate, composition_enclosure = (
            owned(candidate),
            owned(enclosure),
        )
        live()
        work["target_entries"] += 1
        target = _check_synthetic_sinc_target_content(
            expected_q_word, target_input, synthetic_test_only=True
        )
        live()
        require(checked_report(target, True))
        target = owned(target)
        input_record(target_input, False)
        require(target_input == enclosure)
        require(
            target["q_word"] == expected_q_word
            and target["sign"] == expected_q_word >> 63
        )
        require(target["q_ratio"] == original_ratio and target["profile"] == profile)
        require(target["domain_ratio"] == enclosure["domain_ratio"])
        require(target["target"] == enclosure["target"])
        require(
            target["interval"] == original_interval
            and target["stages"] == original_stages
        )
        live()
        work["composition_entries"] += 1
        composition = _check_synthetic_sinc_composition(
            expected_q_word,
            composition_candidate,
            composition_enclosure,
            synthetic_test_only=True,
        )
        live()
        require(checked_report(composition, False))
        composition = owned(composition)
        input_record(composition_candidate, True)
        input_record(composition_enclosure, False)
        require(
            composition_candidate == candidate and composition_enclosure == enclosure
        )
        require(
            composition["q_word"] == expected_q_word
            and composition["sign"] == expected_q_word >> 63
        )
        require(
            composition["q_ratio"] == original_ratio
            and composition["profile"] == profile
        )
        require(composition["interval"] == original_interval == target["interval"])
        require(
            original_certificate
            == composition_candidate["certificate"]
            == composition["certificate"]
        )
        require(original_certificate["interval"] == original_interval)
        live()
        result.update(
            status="checked_conditional_zero_target_binding"
            if zero
            else "checked_conditional_sinc_target_cell_content",
            reason="conditional_zero_target_and_binding_only"
            if zero
            else "conditional_target_and_cell_correspondence_only",
            q_word=expected_q_word,
            sign=expected_q_word >> 63,
            q_ratio=original_ratio,
            target=enclosure["target"],
            domain_ratio=enclosure["domain_ratio"],
            branch="zero" if zero else "series",
            profile=owned(profile),
            interval=original_interval,
            stages=owned(original_stages),
            certificate=owned(original_certificate),
            work=owned(work),
        )
    except JoinStop as error:
        result["reason"] = str(error)
    return result


def _check_synthetic_sinc_target_content(
    expected_q_word, enclosure_record, *, synthetic_test_only=False
):
    """Check mathematical stage contents, never producer execution or native parity."""
    if synthetic_test_only is not True:
        raise ValueError("target checker requires synthetic_test_only=True")
    limit = _SYNTHETIC_TARGET_CHECK_BITS
    ceilings = {
        "integer_power_steps": 256,
        "rational_constructions": 512,
        "rational_operations": 512,
        "rational_comparisons": 256,
    }
    work = {
        "canonical_pair_checks": 0,
        "dyadic_decodes": 0,
        "integer_power_steps": 0,
        "rational_constructions": 0,
        "rational_operations": 0,
        "rational_comparisons": 0,
        "max_result_bits": 0,
    }
    flags = {
        "training_approved",
        "real_input_qualified",
        "free_space_qualified",
        "numerically_certified",
        "producer_parity_qualified",
    }
    result = {
        "identity": "synthetic_sinc_target_content_check_v0",
        "allowed_use": "isolated_synthetic_sinc_target_content_check_only",
        "status": "unresolved_synthetic_sinc_target_content",
        "reason": "unsupported_target_content",
        "configuration": {
            "rational_bit_limit": limit
            if type(limit) is int and 1 <= limit <= 65536
            else None,
            **{key + "_limit": value for key, value in ceilings.items()},
        },
        **{flag: False for flag in flags},
        "native_sinc_status": "unresolved_native_sinc_evidence",
        "motion_status": "unresolved_motion_evidence",
        "source_status": "unresolved_source_authority",
        "native_work_status": "unresolved_native_work_evidence",
        "consumer_status": "ineligible_isolated_candidate",
        "work": work,
    }
    if type(limit) is not int or not 1 <= limit <= 65536:
        result["reason"] = "unsupported_target_check_configuration"
        return result

    class TargetStop(ArithmeticError):
        pass

    def require(condition):
        if not condition:
            raise TargetStop("inconsistent_target_content")

    def preflight(*sizes):
        if (
            type(_SYNTHETIC_TARGET_CHECK_BITS) is not int
            or _SYNTHETIC_TARGET_CHECK_BITS != limit
        ):
            raise TargetStop("changed_target_check_configuration")
        if max(sizes) > limit:
            raise TargetStop("target_rational_work_limit")

    def reserve(key):
        preflight(1)
        if work[key] >= ceilings[key]:
            raise TargetStop("target_attempt_limit")
        work[key] += 1

    def shape(value, keys):
        require(type(value) is dict and len(value) == len(keys))
        require(
            all(type(key) is str and len(key) <= 32 and key in keys for key in value)
        )

    def integer(value, minimum, maximum):
        require(type(value) is int and minimum <= value <= maximum)
        preflight(value.bit_length())

    collected = []

    def pair(value):
        require(type(value) is tuple and len(value) == 2)
        require(all(type(part) is int for part in value) and value[1] > 0)
        preflight(*(part.bit_length() for part in value))
        collected.append(value)

    def interval(value):
        require(type(value) is tuple and len(value) == 2)
        for endpoint in value:
            pair(endpoint)

    def owned(value):
        if type(value) is dict:
            return {key: owned(item) for key, item in value.items()}
        if type(value) is tuple:
            return tuple(owned(item) for item in value)
        return value

    def rational(numerator, denominator=1):
        preflight(numerator.bit_length(), denominator.bit_length())
        reserve("rational_constructions")
        value = Fraction(numerator, denominator)
        numerator, denominator = value.numerator, value.denominator
        require(type(numerator) is int and type(denominator) is int and denominator > 0)
        size = max(numerator.bit_length(), denominator.bit_length())
        preflight(size)
        work["max_result_bits"] = max(work["max_result_bits"], size)
        return numerator, denominator

    def raw_multiply(left, right, *, power_step=False):
        preflight(left.bit_length() + right.bit_length())
        if power_step:
            reserve("integer_power_steps")
        value = left * right
        preflight(value.bit_length())
        return value

    def add(left, right):
        preflight(
            max(
                left[0].bit_length() + right[1].bit_length(),
                right[0].bit_length() + left[1].bit_length(),
            )
            + 1,
            left[1].bit_length() + right[1].bit_length(),
        )
        reserve("rational_operations")
        return rational(left[0] * right[1] + right[0] * left[1], left[1] * right[1])

    def multiply(left, right):
        preflight(
            left[0].bit_length() + right[0].bit_length(),
            left[1].bit_length() + right[1].bit_length(),
        )
        reserve("rational_operations")
        return rational(left[0] * right[0], left[1] * right[1])

    def divide(left, right):
        require(right[0] > 0)
        preflight(right[0].bit_length(), right[1].bit_length())
        reserve("rational_operations")
        return multiply(left, rational(right[1], right[0]))

    def compare(left, right):
        preflight(
            left[0].bit_length() + right[1].bit_length(),
            right[0].bit_length() + left[1].bit_length(),
        )
        reserve("rational_comparisons")
        first, second = left[0] * right[1], right[0] * left[1]
        preflight(first.bit_length(), second.bit_length())
        return (first > second) - (first < second)

    def interval_multiply(left, right):
        products = [multiply(first, second) for first in left for second in right]
        lower = upper = products[0]
        for product in products[1:]:
            if compare(product, lower) < 0:
                lower = product
            if compare(product, upper) > 0:
                upper = product
        return lower, upper

    profile = {
        "arctangent_terms": 32,
        "sinc_terms": 8,
        "rational_bit_limit": 65536,
    }
    stage_keys = {
        "arctangent",
        "pi",
        "squared_argument",
        "coefficients",
        "polynomial",
        "remainder",
    }
    keys = {
        "allowed_use",
        "status",
        "reason",
        "target",
        "domain_ratio",
        "configuration",
        "q_word",
        "q_ratio",
        "sign",
        "branch",
        "interval",
        "stages",
        "work",
        "native_sinc_status",
        "motion_status",
    } | flags
    try:
        integer(expected_q_word, 0, (1 << 64) - 1)
        exponent = (expected_q_word >> 52) & 2047
        require(exponent != 2047)
        sign = expected_q_word >> 63
        zero = expected_q_word & ((1 << 63) - 1) == 0
        branch = "zero" if zero else "series"
        shape(enclosure_record, keys)
        selectors = {
            "allowed_use": "isolated_synthetic_sinc_reference_only",
            "status": "enclosed_mathematical_sinc",
            "reason": "exact_mathematical_zero_branch"
            if zero
            else "real_pi_even_series_enclosure_only",
            "target": "real_pi_normalized_sinc_at_stored_binary64",
            "branch": branch,
            "native_sinc_status": "unresolved_native_sinc_evidence",
            "motion_status": "unresolved_motion_evidence",
        }
        require(
            all(
                type(enclosure_record[key]) is str and enclosure_record[key] == value
                for key, value in selectors.items()
            )
        )
        require(
            all(
                type(enclosure_record[key]) is bool and enclosure_record[key] is False
                for key in flags
            )
        )
        integer(enclosure_record["q_word"], 0, (1 << 64) - 1)
        integer(enclosure_record["sign"], 0, 1)
        require(enclosure_record["q_word"] == expected_q_word)
        require(enclosure_record["sign"] == sign)
        shape(enclosure_record["configuration"], profile)
        for key, value in profile.items():
            integer(enclosure_record["configuration"][key], 1, 65536)
            require(enclosure_record["configuration"][key] == value)
        declared_work = enclosure_record["work"]
        shape(declared_work, {"rational_operations", "max_result_bits"})
        integer(declared_work["rational_operations"], 0, (1 << 64) - 1)
        integer(declared_work["max_result_bits"], 0, 65536)
        pair(enclosure_record["q_ratio"])
        pair(enclosure_record["domain_ratio"])
        interval(enclosure_record["interval"])
        stages = enclosure_record["stages"]
        shape(stages, set() if zero else stage_keys)
        if not zero:
            require(
                type(stages["arctangent"]) is tuple and len(stages["arctangent"]) == 2
            )
            for value in stages["arctangent"]:
                interval(value)
            for key in ("pi", "squared_argument", "polynomial", "remainder"):
                interval(stages[key])
            require(
                type(stages["coefficients"]) is tuple
                and len(stages["coefficients"]) == 8
            )
            for value in stages["coefficients"]:
                pair(value)
        record = owned(enclosure_record)
        for value in collected:
            work["canonical_pair_checks"] += 1
            require(rational(*value) == value)
        require(record["domain_ratio"] == (1, 64))
        require(compare(*record["interval"]) <= 0)
        if not zero:
            for value in (
                *record["stages"]["arctangent"],
                record["stages"]["pi"],
                record["stages"]["squared_argument"],
                record["stages"]["polynomial"],
                record["stages"]["remainder"],
            ):
                require(compare(*value) <= 0)
        work["dyadic_decodes"] += 1
        if zero:
            ratio = rational(0, 1)
        else:
            significand = expected_q_word & ((1 << 52) - 1)
            if exponent:
                significand += 1 << 52
            shift = exponent - 1075 if exponent else -1074
            preflight(significand.bit_length() + max(0, shift), 1 + max(0, -shift))
            numerator = significand << max(0, shift)
            ratio = rational(-numerator if sign else numerator, 1 << max(0, -shift))
        require(record["q_ratio"] == ratio)
        require(compare((abs(ratio[0]), ratio[1]), (1, 64)) <= 0)
        expected_stages = {}
        computed_interval = ((1, 1), (1, 1))
        if not zero:
            arctangents = []
            for denominator in (5, 239):
                powers = [1]
                for _ in range(65):
                    powers.append(
                        raw_multiply(powers[-1], denominator, power_step=True)
                    )
                partial = (0, 1)
                for degree in range(32):
                    odd = 2 * degree + 1
                    term = rational(
                        -1 if degree % 2 else 1, raw_multiply(odd, powers[odd])
                    )
                    partial = add(partial, term)
                tail = rational(1, raw_multiply(65, powers[65]))
                arctangents.append((partial, add(partial, tail)))
            require(tuple(arctangents) == record["stages"]["arctangent"])
            pi_interval = (
                add(
                    multiply((16, 1), arctangents[0][0]),
                    multiply((-4, 1), arctangents[1][1]),
                ),
                add(
                    multiply((16, 1), arctangents[0][1]),
                    multiply((-4, 1), arctangents[1][0]),
                ),
            )
            require(compare((3, 1), pi_interval[0]) < 0)
            require(compare(*pi_interval) <= 0)
            require(compare(pi_interval[1], (4, 1)) < 0)
            require(pi_interval == record["stages"]["pi"])
            squared_q = multiply(ratio, ratio)
            squared_argument = tuple(
                multiply(squared_q, multiply(endpoint, endpoint))
                for endpoint in pi_interval
            )
            require(compare((0, 1), squared_argument[0]) < 0)
            require(compare(*squared_argument) <= 0)
            require(compare(squared_argument[1], (1, 256)) <= 0)
            require(squared_argument == record["stages"]["squared_argument"])
            factorial = 1
            coefficients = []
            for degree in range(1, 18):
                factorial = raw_multiply(factorial, degree, power_step=True)
                if degree % 2 and degree <= 15:
                    coefficients.append(
                        rational(-1 if (degree // 2) % 2 else 1, factorial)
                    )
            require(tuple(coefficients) == record["stages"]["coefficients"])
            polynomial = (coefficients[7], coefficients[7])
            for coefficient in reversed(coefficients[:7]):
                product = interval_multiply(polynomial, squared_argument)
                polynomial = tuple(add(endpoint, coefficient) for endpoint in product)
            require(polynomial == record["stages"]["polynomial"])
            tail_power = (1, 1)
            for _ in range(8):
                tail_power = multiply(tail_power, squared_argument[1])
            remainder = ((0, 1), divide(tail_power, (factorial, 1)))
            require(remainder == record["stages"]["remainder"])
            computed_interval = tuple(
                add(endpoint, tail)
                for endpoint, tail in zip(polynomial, remainder, strict=True)
            )
            require(compare(*computed_interval) <= 0)
            expected_stages = {
                "arctangent": tuple(arctangents),
                "pi": pi_interval,
                "squared_argument": squared_argument,
                "coefficients": tuple(coefficients),
                "polynomial": polynomial,
                "remainder": remainder,
            }
        require(record["interval"] == computed_interval)
        require(record["stages"] == expected_stages)
        preflight(1)
        result.update(
            status="checked_declared_mathematical_zero_content"
            if zero
            else "checked_declared_mathematical_sinc_content",
            reason="independent_declared_stage_content_only",
            q_word=expected_q_word,
            sign=sign,
            q_ratio=ratio,
            target="real_pi_normalized_sinc_at_stored_binary64",
            domain_ratio=(1, 64),
            branch=branch,
            profile=owned(profile),
            interval=computed_interval,
            stages=owned(expected_stages),
            work=owned(work),
        )
    except TargetStop as error:
        result["reason"] = str(error)
    return result


def _check_synthetic_sinc_composition(
    expected_q_word, candidate_record, enclosure_record, *, synthetic_test_only=False
):
    """Join declared binding and exact cell contents, never target or live evidence."""
    if synthetic_test_only is not True:
        raise ValueError("composition requires synthetic_test_only=True")
    zero = type(expected_q_word) is int and expected_q_word in (0, 1 << 63)
    limits = (
        _SYNTHETIC_COMPOSITION_BITS,
        _SYNTHETIC_BIND_CHECK_BITS,
        None if zero else _SYNTHETIC_CELL_CHECK_BITS,
    )
    flags = {
        "training_approved",
        "real_input_qualified",
        "free_space_qualified",
        "numerically_certified",
        "producer_parity_qualified",
    }
    statuses = {
        "native_sinc_status": "unresolved_native_sinc_evidence",
        "motion_status": "unresolved_motion_evidence",
        "source_status": "unresolved_source_authority",
        "native_work_status": "unresolved_native_work_evidence",
        "consumer_status": "ineligible_isolated_candidate",
    }
    work = {
        "composition_entries": 1,
        "binding_entries": 0,
        "cell_entries": 0,
        "binding": None,
        "cell": None,
    }
    result = {
        "identity": "synthetic_sinc_composition_check_v0",
        "allowed_use": "isolated_synthetic_sinc_composition_check_only",
        "status": "unresolved_synthetic_sinc_composition",
        "reason": "unsupported_composition",
        "configuration": {
            key: value if type(value) is int and 1 <= value <= 65536 else None
            for key, value in zip(
                ("raw_copy_bit_limit", "binding_bit_limit", "cell_bit_limit"),
                limits,
                strict=True,
            )
        },
        **{flag: False for flag in flags},
        **statuses,
        "work": work,
    }
    if any(
        type(value) is not int or not 1 <= value <= 65536
        for value in limits[:2] + (() if zero else limits[2:])
    ):
        result["reason"] = "unsupported_composition_configuration"
        return result
    limit = limits[0]
    profile = {"arctangent_terms": 32, "sinc_terms": 8, "rational_bit_limit": 65536}

    class CompositionStop(ArithmeticError):
        pass

    def require(condition):
        if not condition:
            raise CompositionStop("inconsistent_composition")

    def live():
        current = (
            _SYNTHETIC_COMPOSITION_BITS,
            _SYNTHETIC_BIND_CHECK_BITS,
            None if zero else _SYNTHETIC_CELL_CHECK_BITS,
        )
        require(all(type(value) is int for value in current[:2]))
        require(zero or type(current[2]) is int)
        require(current == limits)

    def shape(value, keys):
        require(type(value) is dict and len(value) == len(keys))
        require(
            all(type(key) is str and len(key) <= 32 and key in keys for key in value)
        )

    def number(value, minimum=None, maximum=None):
        require(type(value) is int)
        require(minimum is None or value >= minimum)
        require(maximum is None or value <= maximum)
        require(value.bit_length() <= limit)

    def sequence(value, length, check):
        require(type(value) is tuple and len(value) == length)
        for item in value:
            check(item)

    def pair(value):
        require(type(value) is tuple and len(value) == 2)
        number(value[0])
        number(value[1], 1)

    def interval(value):
        sequence(value, 2, pair)

    def configuration(value):
        shape(value, profile)
        for key in profile:
            number(value[key], 1, 65536)
        require(value == profile)

    def enclosure_work(value):
        shape(value, {"rational_operations", "max_result_bits"})
        number(value["rational_operations"], 0, (1 << 64) - 1)
        number(value["max_result_bits"], 0, 65536)

    def neighbor(value):
        require(type(value) is tuple and len(value) == 2)
        number(value[0], 0, 0x7FEFFFFFFFFFFFFF)
        pair(value[1])

    certificate_keys = {
        "word",
        "interval",
        "neighbors",
        "boundaries",
        "closed_ties",
        "lower_order",
        "upper_order",
        "whole_interval_contained",
    }

    def certificate(value):
        shape(value, {"word", "interval", "branch"} if zero else certificate_keys)
        number(value["word"], 1, 0x7FEFFFFFFFFFFFFE)
        interval(value["interval"])
        if zero:
            require(type(value["branch"]) is str and value["branch"] == "zero")
            require(value["word"] == 0x3FF0000000000000)
            require(value["interval"] == ((1, 1), (1, 1)))
        else:
            sequence(value["neighbors"], 3, neighbor)
            interval(value["boundaries"])
            for key in ("closed_ties", "whole_interval_contained"):
                require(type(value[key]) is bool)
            for key in ("lower_order", "upper_order"):
                number(value[key], -1, 1)

    common_keys = {
        "allowed_use",
        "status",
        "reason",
        "target",
        "q_word",
        "work",
        "sign",
        "q_ratio",
        "configuration",
        "interval",
        "native_sinc_status",
        "motion_status",
    } | flags

    def input_record(value, candidate):
        extra = (
            {
                "identity",
                "source_status",
                "native_work_status",
                "consumer_status",
                "certificate",
                "enclosure_binding",
            }
            if candidate
            else {"domain_ratio", "branch", "stages"}
        )
        shape(value, common_keys | extra)
        for key in common_keys | extra:
            if key in flags:
                require(type(value[key]) is bool and value[key] is False)
            elif key in {
                "identity",
                "allowed_use",
                "status",
                "reason",
                "target",
                "branch",
                "native_sinc_status",
                "motion_status",
                "source_status",
                "native_work_status",
                "consumer_status",
            }:
                require(type(value[key]) is str and len(value[key]) <= 64)
        number(value["q_word"], 0, (1 << 64) - 1)
        number(value["sign"], 0, 1)
        pair(value["q_ratio"])
        interval(value["interval"])
        configuration(value["configuration"])
        if candidate:
            certificate(value["certificate"])
            binding = value["enclosure_binding"]
            shape(binding, {"q_word", "sign", "q_ratio"})
            number(binding["q_word"], 0, (1 << 64) - 1)
            number(binding["sign"], 0, 1)
            pair(binding["q_ratio"])
            declared = value["work"]
            shape(
                declared,
                {"enclosure_entries", "cell_entries", "enclosure"}
                | (set() if zero else {"cell"}),
            )
            number(declared["enclosure_entries"], 1, 1)
            number(declared["cell_entries"], 0 if zero else 1, 0 if zero else 1)
            enclosure_work(declared["enclosure"])
            if not zero:
                cell = declared["cell"]
                shape(
                    cell,
                    {
                        "search_iterations",
                        "endpoint_iterations",
                        "dyadic_decodes",
                        "midpoint_constructions",
                        "rational_comparisons",
                        "rational_constructions",
                        "max_result_bits",
                    },
                )
                for key in cell:
                    if key != "endpoint_iterations":
                        number(
                            cell[key],
                            0,
                            65536 if key == "max_result_bits" else (1 << 64) - 1,
                        )
                require(
                    type(cell["endpoint_iterations"]) is list
                    and len(cell["endpoint_iterations"]) == 2
                )
                for count in cell["endpoint_iterations"]:
                    number(count, 0, 64)
                require(sum(cell["endpoint_iterations"]) == cell["search_iterations"])
        else:
            pair(value["domain_ratio"])
            enclosure_work(value["work"])
            stages = value["stages"]
            shape(
                stages,
                set()
                if zero
                else {
                    "arctangent",
                    "pi",
                    "squared_argument",
                    "coefficients",
                    "polynomial",
                    "remainder",
                },
            )
            if not zero:
                sequence(stages["arctangent"], 2, interval)
                for key in ("pi", "squared_argument", "polynomial", "remainder"):
                    interval(stages[key])
                sequence(stages["coefficients"], 8, pair)

    def owned(value):
        if type(value) is dict:
            return {key: owned(item) for key, item in value.items()}
        if type(value) is tuple:
            return tuple(owned(item) for item in value)
        if type(value) is list:
            return [owned(item) for item in value]
        return value

    report_keys = (
        {"identity", "allowed_use", "status", "reason", "configuration", "work"}
        | flags
        | set(statuses)
    )
    binding_fields = {
        "q_word",
        "sign",
        "q_ratio",
        "branch",
        "profile",
        "interval",
        "certificate",
    }

    def checked_report(value, binding):
        require(type(value) is dict and len(value) in (16, 23 if binding else 17))
        complete = len(value) != 16
        shape(
            value,
            report_keys
            | ((binding_fields if binding else {"certificate"}) if complete else set()),
        )
        selectors = {
            "identity": "synthetic_sinc_declared_binding_check_v0"
            if binding
            else "synthetic_cell_certificate_content_check_v0",
            "allowed_use": "isolated_synthetic_declared_binding_only"
            if binding
            else "isolated_synthetic_cell_content_check_only",
            "status": (
                "verified_declared_sinc_binding"
                if binding
                else "verified_synthetic_cell_content"
            )
            if complete
            else (
                "unresolved_sinc_declared_binding"
                if binding
                else "unresolved_synthetic_cell_content"
            ),
            **statuses,
        }
        for key, expected in selectors.items():
            require(type(value[key]) is str and value[key] == expected)
        require(type(value["reason"]) is str and len(value["reason"]) <= 64)
        for flag in flags:
            require(type(value[flag]) is bool and value[flag] is False)
        shape(value["configuration"], {"rational_bit_limit"})
        number(value["configuration"]["rational_bit_limit"], 1, 65536)
        require(
            value["configuration"]["rational_bit_limit"] == limits[1 if binding else 2]
        )
        inner_work = value["work"]
        shape(
            inner_work,
            {
                "canonical_pair_checks",
                "dyadic_decodes",
                "rational_comparisons",
                "rational_constructions",
                "max_result_bits",
            }
            | (set() if binding else {"midpoint_recomputations"}),
        )
        for key in inner_work:
            number(
                inner_work[key], 0, 65536 if key == "max_result_bits" else (1 << 64) - 1
            )
        if complete:
            require(
                value["reason"]
                == (
                    "declared_correspondence_only"
                    if binding
                    else "independent_exact_cell_content_only"
                )
            )
            certificate(value["certificate"])
            if binding:
                number(value["q_word"], 0, (1 << 64) - 1)
                number(value["sign"], 0, 1)
                pair(value["q_ratio"])
                interval(value["interval"])
                configuration(value["profile"])
                require(
                    type(value["branch"]) is str
                    and value["branch"] == ("zero" if zero else "series")
                )
        work["binding" if binding else "cell"] = owned(inner_work)
        return complete

    try:
        number(expected_q_word, 0, (1 << 64) - 1)
        require((expected_q_word >> 52) & 2047 != 2047)
        input_record(candidate_record, True)
        input_record(enclosure_record, False)
        candidate, enclosure = owned(candidate_record), owned(enclosure_record)
        original_certificate = owned(candidate["certificate"])
        original_interval = candidate["interval"]
        original_ratio = candidate["q_ratio"]
        enclosure_interval = enclosure["interval"]
        enclosure_ratio = enclosure["q_ratio"]
        small_ratio = candidate["enclosure_binding"]["q_ratio"]
        live()
        work["binding_entries"] += 1
        binding = _check_synthetic_sinc_declared_binding(
            expected_q_word,
            candidate,
            enclosure,
            synthetic_test_only=True,
        )
        live()
        require(checked_report(binding, True))
        require(
            binding["q_word"] == expected_q_word
            and binding["sign"] == expected_q_word >> 63
        )
        require(binding["q_ratio"] == original_ratio == enclosure_ratio == small_ratio)
        require(binding["interval"] == original_interval == enclosure_interval)
        require(binding["certificate"] == original_certificate)
        if not zero:
            cell_input = owned(binding["certificate"])
            live()
            work["cell_entries"] += 1
            cell = _check_synthetic_cell_certificate(
                cell_input, synthetic_test_only=True
            )
            live()
            require(checked_report(cell, False))
            certificate(cell_input)
            certificate(binding["certificate"])
            require(
                original_certificate
                == binding["certificate"]
                == cell_input
                == cell["certificate"]
            )
        live()
        result.update(
            status="checked_declared_zero_binding"
            if zero
            else "checked_declared_binding_and_cell_content",
            reason="declared_zero_binding_only"
            if zero
            else "declared_binding_and_exact_cell_content_only",
            q_word=expected_q_word,
            sign=expected_q_word >> 63,
            q_ratio=original_ratio,
            branch="zero" if zero else "series",
            profile=owned(profile),
            interval=original_interval,
            certificate=owned(original_certificate),
        )
    except CompositionStop as error:
        result["reason"] = str(error)
    return result


def _check_synthetic_sinc_declared_binding(
    expected_q_word, candidate_record, enclosure_record, *, synthetic_test_only=False
):
    """Check declared record correspondence, not enclosure truth or live authority."""
    if synthetic_test_only is not True:
        raise ValueError("binding checker requires synthetic_test_only=True")
    limit = _SYNTHETIC_BIND_CHECK_BITS
    work = {
        "canonical_pair_checks": 0,
        "dyadic_decodes": 0,
        "rational_comparisons": 0,
        "rational_constructions": 0,
        "max_result_bits": 0,
    }
    result = {
        "identity": "synthetic_sinc_declared_binding_check_v0",
        "allowed_use": "isolated_synthetic_declared_binding_only",
        "status": "unresolved_sinc_declared_binding",
        "reason": "unsupported_declared_binding",
        "configuration": {
            "rational_bit_limit": limit
            if type(limit) is int and 1 <= limit <= 65536
            else None
        },
        "training_approved": False,
        "real_input_qualified": False,
        "free_space_qualified": False,
        "numerically_certified": False,
        "producer_parity_qualified": False,
        "native_sinc_status": "unresolved_native_sinc_evidence",
        "motion_status": "unresolved_motion_evidence",
        "source_status": "unresolved_source_authority",
        "native_work_status": "unresolved_native_work_evidence",
        "consumer_status": "ineligible_isolated_candidate",
        "work": work,
    }
    if type(limit) is not int or not 1 <= limit <= 65536:
        result["reason"] = "unsupported_binding_check_configuration"
        return result

    class BindingStop(ArithmeticError):
        pass

    def require(condition):
        if not condition:
            raise BindingStop("inconsistent_declared_binding")

    def preflight(*sizes):
        if (
            type(_SYNTHETIC_BIND_CHECK_BITS) is not int
            or _SYNTHETIC_BIND_CHECK_BITS != limit
        ):
            raise BindingStop("changed_binding_check_configuration")
        if max(sizes) > limit:
            raise BindingStop("binding_rational_work_limit")

    def shape(value, keys):
        require(type(value) is dict and len(value) == len(keys))
        require(
            all(type(key) is str and len(key) <= 32 and key in keys for key in value)
        )

    def integer(value, low, high):
        require(type(value) is int and low <= value <= high)

    pairs = []

    def pair(value):
        require(type(value) is tuple and len(value) == 2)
        require(all(type(part) is int for part in value) and value[1] > 0)
        preflight(*(part.bit_length() for part in value))
        pairs.append(value)

    def interval(value):
        require(type(value) is tuple and len(value) == 2)
        for endpoint in value:
            pair(endpoint)

    def rational(numerator, denominator):
        preflight(numerator.bit_length(), denominator.bit_length())
        work["rational_constructions"] += 1
        value = Fraction(numerator, denominator)
        numerator, denominator = value.numerator, value.denominator
        require(type(numerator) is int and type(denominator) is int and denominator > 0)
        size = max(numerator.bit_length(), denominator.bit_length())
        preflight(size)
        work["max_result_bits"] = max(work["max_result_bits"], size)
        return numerator, denominator

    def compare(left, right):
        preflight(
            left[0].bit_length() + right[1].bit_length(),
            right[0].bit_length() + left[1].bit_length(),
        )
        work["rational_comparisons"] += 1
        first, second = left[0] * right[1], right[0] * left[1]
        return (first > second) - (first < second)

    def owned(value):
        if type(value) is dict:
            return {key: owned(item) for key, item in value.items()}
        if type(value) is tuple:
            return tuple(owned(item) for item in value)
        if type(value) is list:
            return [owned(item) for item in value]
        return value

    flags = {
        "training_approved",
        "real_input_qualified",
        "free_space_qualified",
        "numerically_certified",
        "producer_parity_qualified",
    }
    common = {
        "allowed_use",
        "status",
        "reason",
        "target",
        "q_word",
        "work",
        "sign",
        "q_ratio",
        "configuration",
        "interval",
    } | flags
    candidate_keys = common | {
        "identity",
        "native_sinc_status",
        "motion_status",
        "source_status",
        "native_work_status",
        "consumer_status",
        "certificate",
        "enclosure_binding",
    }
    enclosure_keys = common | {
        "domain_ratio",
        "native_sinc_status",
        "motion_status",
        "branch",
        "stages",
    }
    configuration = {
        "arctangent_terms": 32,
        "sinc_terms": 8,
        "rational_bit_limit": 65536,
    }
    try:
        integer(expected_q_word, 0, (1 << 64) - 1)
        exponent = (expected_q_word >> 52) & 2047
        require(exponent != 2047)
        sign = expected_q_word >> 63
        zero = expected_q_word & ((1 << 63) - 1) == 0
        branch = "zero" if zero else "series"
        for record, keys, selectors in (
            (
                candidate_record,
                candidate_keys,
                {
                    "identity": "controlled_mathematical_sinc_rn64_candidate_v0",
                    "allowed_use": "isolated_synthetic_sinc_word_candidate_only",
                    "status": "candidate_mathematical_sinc_word",
                    "reason": "conditional_mathematical_rounding_cell_only",
                    "source_status": "unresolved_source_authority",
                    "native_work_status": "unresolved_native_work_evidence",
                    "consumer_status": "ineligible_isolated_candidate",
                },
            ),
            (
                enclosure_record,
                enclosure_keys,
                {
                    "allowed_use": "isolated_synthetic_sinc_reference_only",
                    "status": "enclosed_mathematical_sinc",
                    "reason": "exact_mathematical_zero_branch"
                    if zero
                    else "real_pi_even_series_enclosure_only",
                    "branch": branch,
                },
            ),
        ):
            shape(record, keys)
            selectors.update(
                target="real_pi_normalized_sinc_at_stored_binary64",
                native_sinc_status="unresolved_native_sinc_evidence",
                motion_status="unresolved_motion_evidence",
            )
            require(
                all(
                    type(record[key]) is str and record[key] == value
                    for key, value in selectors.items()
                )
            )
            require(
                all(type(record[key]) is bool and record[key] is False for key in flags)
            )
            integer(record["q_word"], 0, (1 << 64) - 1)
            integer(record["sign"], 0, 1)
            require(record["q_word"] == expected_q_word and record["sign"] == sign)
            shape(record["configuration"], configuration)
            require(
                all(
                    type(record["configuration"][key]) is int
                    and record["configuration"][key] == value
                    for key, value in configuration.items()
                )
            )
            pair(record["q_ratio"])
            interval(record["interval"])
        pair(enclosure_record["domain_ratio"])
        require(enclosure_record["domain_ratio"] == (1, 64))
        binding = candidate_record["enclosure_binding"]
        shape(binding, {"q_word", "sign", "q_ratio"})
        integer(binding["q_word"], 0, (1 << 64) - 1)
        integer(binding["sign"], 0, 1)
        require(binding["q_word"] == expected_q_word and binding["sign"] == sign)
        pair(binding["q_ratio"])
        stages = enclosure_record["stages"]
        shape(
            stages,
            set()
            if zero
            else {
                "arctangent",
                "pi",
                "squared_argument",
                "coefficients",
                "polynomial",
                "remainder",
            },
        )
        if not zero:
            require(
                type(stages["arctangent"]) is tuple and len(stages["arctangent"]) == 2
            )
            for value in stages["arctangent"]:
                interval(value)
            for key in ("pi", "squared_argument", "polynomial", "remainder"):
                interval(stages[key])
            require(
                type(stages["coefficients"]) is tuple
                and len(stages["coefficients"]) == 8
            )
            for value in stages["coefficients"]:
                pair(value)
        certificate = candidate_record["certificate"]
        shape(
            certificate,
            {"word", "interval", "branch"}
            if zero
            else {
                "word",
                "interval",
                "neighbors",
                "boundaries",
                "closed_ties",
                "lower_order",
                "upper_order",
                "whole_interval_contained",
            },
        )
        integer(certificate["word"], 1, 0x7FEFFFFFFFFFFFFE)
        interval(certificate["interval"])
        if zero:
            require(
                type(certificate["branch"]) is str
                and certificate["branch"] == "zero"
                and certificate["word"] == 0x3FF0000000000000
            )
        else:
            require(
                type(certificate["neighbors"]) is tuple
                and len(certificate["neighbors"]) == 3
            )
            for neighbor in certificate["neighbors"]:
                require(type(neighbor) is tuple and len(neighbor) == 2)
                integer(neighbor[0], 0, 0x7FEFFFFFFFFFFFFF)
                pair(neighbor[1])
            interval(certificate["boundaries"])
            require(
                type(certificate["closed_ties"]) is bool
                and type(certificate["whole_interval_contained"]) is bool
                and certificate["whole_interval_contained"] is True
            )
            for key in ("lower_order", "upper_order"):
                integer(certificate[key], -1, 1)
        declared = candidate_record["work"]
        shape(
            declared,
            {"enclosure_entries", "cell_entries", "enclosure"}
            | (set() if zero else {"cell"}),
        )
        for enclosure_work in (enclosure_record["work"], declared["enclosure"]):
            shape(enclosure_work, {"rational_operations", "max_result_bits"})
            integer(enclosure_work["rational_operations"], 0, (1 << 64) - 1)
            integer(enclosure_work["max_result_bits"], 0, 65536)
        integer(declared["enclosure_entries"], 1, 1)
        integer(declared["cell_entries"], 0 if zero else 1, 0 if zero else 1)
        require(declared["enclosure"] == enclosure_record["work"])
        if not zero:
            cell = declared["cell"]
            shape(
                cell,
                {
                    "search_iterations",
                    "endpoint_iterations",
                    "dyadic_decodes",
                    "midpoint_constructions",
                    "rational_comparisons",
                    "rational_constructions",
                    "max_result_bits",
                },
            )
            for key in cell:
                if key != "endpoint_iterations":
                    integer(
                        cell[key],
                        0,
                        65536 if key == "max_result_bits" else (1 << 64) - 1,
                    )
            require(
                type(cell["endpoint_iterations"]) is list
                and len(cell["endpoint_iterations"]) == 2
            )
            for count in cell["endpoint_iterations"]:
                integer(count, 0, 64)
            require(sum(cell["endpoint_iterations"]) == cell["search_iterations"])
        candidate, enclosure = owned(candidate_record), owned(enclosure_record)
        for value in pairs:
            work["canonical_pair_checks"] += 1
            require(rational(*value) == value)
        work["dyadic_decodes"] += 1
        if zero:
            ratio = rational(0, 1)
        else:
            significand = expected_q_word & ((1 << 52) - 1)
            if exponent:
                significand += 1 << 52
            shift = exponent - 1075 if exponent else -1074
            preflight(significand.bit_length() + max(0, shift), 1 + max(0, -shift))
            numerator = significand << max(0, shift)
            ratio = rational(-numerator if sign else numerator, 1 << max(0, -shift))
        require(compare((abs(ratio[0]), ratio[1]), (1, 64)) <= 0)
        require(
            candidate["q_ratio"]
            == enclosure["q_ratio"]
            == candidate["enclosure_binding"]["q_ratio"]
            == ratio
        )
        common_interval = candidate["interval"]
        require(
            common_interval
            == enclosure["interval"]
            == candidate["certificate"]["interval"]
        )
        require(common_interval[0][0] > 0 and compare(*common_interval) <= 0)
        if zero:
            require(common_interval == ((1, 1), (1, 1)))
        else:
            stages = enclosure["stages"]
            for value in (
                *stages["arctangent"],
                stages["pi"],
                stages["squared_argument"],
                stages["polynomial"],
                stages["remainder"],
            ):
                require(compare(*value) <= 0)
        preflight(1)
        result.update(
            status="verified_declared_sinc_binding",
            reason="declared_correspondence_only",
            q_word=expected_q_word,
            sign=sign,
            q_ratio=ratio,
            branch=branch,
            profile=owned(configuration),
            interval=common_interval,
            certificate=owned(candidate["certificate"]),
        )
    except BindingStop as error:
        result["reason"] = str(error)
    return result


def _check_synthetic_cell_certificate(certificate, *, synthetic_test_only=False):
    """Independently verify supplied cell contents, never sinc inclusion or source."""
    if synthetic_test_only is not True:
        raise ValueError("cell checker requires synthetic_test_only=True")
    limit = _SYNTHETIC_CELL_CHECK_BITS
    work = {
        "canonical_pair_checks": 0,
        "dyadic_decodes": 0,
        "midpoint_recomputations": 0,
        "rational_comparisons": 0,
        "rational_constructions": 0,
        "max_result_bits": 0,
    }
    result = {
        "identity": "synthetic_cell_certificate_content_check_v0",
        "allowed_use": "isolated_synthetic_cell_content_check_only",
        "status": "unresolved_synthetic_cell_content",
        "reason": "unsupported_cell_certificate",
        "configuration": {
            "rational_bit_limit": limit
            if type(limit) is int and 1 <= limit <= 65536
            else None
        },
        "training_approved": False,
        "real_input_qualified": False,
        "free_space_qualified": False,
        "numerically_certified": False,
        "producer_parity_qualified": False,
        "native_sinc_status": "unresolved_native_sinc_evidence",
        "motion_status": "unresolved_motion_evidence",
        "source_status": "unresolved_source_authority",
        "native_work_status": "unresolved_native_work_evidence",
        "consumer_status": "ineligible_isolated_candidate",
        "work": work,
    }
    if type(limit) is not int or not 1 <= limit <= 65536:
        result["reason"] = "unsupported_cell_check_configuration"
        return result

    class CheckStop(ArithmeticError):
        pass

    def preflight(*sizes):
        if (
            type(_SYNTHETIC_CELL_CHECK_BITS) is not int
            or _SYNTHETIC_CELL_CHECK_BITS != limit
        ):
            raise CheckStop("changed_cell_check_configuration")
        if max(sizes) > limit:
            raise CheckStop("cell_check_rational_work_limit")

    def rational(numerator, denominator=1):
        preflight(numerator.bit_length(), denominator.bit_length())
        work["rational_constructions"] += 1
        value = Fraction(numerator, denominator)
        numerator, denominator = value.numerator, value.denominator
        if (
            type(numerator) is not int
            or type(denominator) is not int
            or denominator <= 0
        ):
            raise CheckStop("unsupported_cell_check_canonical_result")
        size = max(numerator.bit_length(), denominator.bit_length())
        preflight(size)
        work["max_result_bits"] = max(work["max_result_bits"], size)
        return numerator, denominator

    def decode(word):
        work["dyadic_decodes"] += 1
        exponent, significand = divmod(word, 1 << 52)
        if exponent:
            preflight(53)
            significand += 1 << 52
            shift = exponent - 1075
        else:
            shift = -1074
        preflight(significand.bit_length() + max(0, shift), 1 + max(0, -shift))
        return rational(significand << max(0, shift), 1 << max(0, -shift))

    def midpoint(left, right):
        preflight(
            max(
                left[0].bit_length() + right[1].bit_length(),
                right[0].bit_length() + left[1].bit_length(),
            )
            + 1,
            left[1].bit_length() + right[1].bit_length() + 1,
        )
        work["midpoint_recomputations"] += 1
        numerator = left[0] * right[1] + right[0] * left[1]
        denominator = (left[1] * right[1]) << 1
        return rational(numerator, denominator)

    def compare(left, right):
        preflight(
            left[0].bit_length() + right[1].bit_length(),
            right[0].bit_length() + left[1].bit_length(),
        )
        work["rational_comparisons"] += 1
        first = left[0] * right[1]
        second = right[0] * left[1]
        return (first > second) - (first < second)

    expected_keys = {
        "word",
        "interval",
        "neighbors",
        "boundaries",
        "closed_ties",
        "lower_order",
        "upper_order",
        "whole_interval_contained",
    }
    if type(certificate) is not dict or len(certificate) != 8:
        return result
    if any(
        type(key) is not str or len(key) > 24 or key not in expected_keys
        for key in certificate
    ):
        return result
    word = certificate["word"]
    if type(word) is not int or not 1 <= word < 0x7FEFFFFFFFFFFFFF:
        result["reason"] = "unsupported_cell_certificate_word"
        return result
    if (
        type(certificate["closed_ties"]) is not bool
        or type(certificate["whole_interval_contained"]) is not bool
        or any(
            type(certificate[name]) is not int or certificate[name] not in (-1, 0, 1)
            for name in ("lower_order", "upper_order")
        )
    ):
        return result
    interval = certificate["interval"]
    boundaries = certificate["boundaries"]
    neighbors = certificate["neighbors"]
    if (
        type(interval) is not tuple
        or len(interval) != 2
        or type(boundaries) is not tuple
        or len(boundaries) != 2
        or type(neighbors) is not tuple
        or len(neighbors) != 3
        or any(
            type(neighbor) is not tuple
            or len(neighbor) != 2
            or type(neighbor[0]) is not int
            or not 0 <= neighbor[0] <= 0x7FEFFFFFFFFFFFFF
            for neighbor in neighbors
        )
    ):
        return result
    pairs = interval + tuple(neighbor[1] for neighbor in neighbors) + boundaries
    try:
        for pair in pairs:
            if (
                type(pair) is not tuple
                or len(pair) != 2
                or any(type(component) is not int for component in pair)
                or pair[1] <= 0
            ):
                return result
            preflight(pair[0].bit_length(), pair[1].bit_length())
        snapshot = {
            "word": word,
            "interval": tuple((pair[0], pair[1]) for pair in interval),
            "neighbors": tuple(
                (neighbor[0], (neighbor[1][0], neighbor[1][1]))
                for neighbor in neighbors
            ),
            "boundaries": tuple((pair[0], pair[1]) for pair in boundaries),
            "closed_ties": certificate["closed_ties"],
            "lower_order": certificate["lower_order"],
            "upper_order": certificate["upper_order"],
            "whole_interval_contained": certificate["whole_interval_contained"],
        }
        for pair in pairs:
            work["canonical_pair_checks"] += 1
            if rational(*pair) != pair:
                raise CheckStop("noncanonical_cell_certificate_pair")
        lower, upper = snapshot["interval"]
        if lower[0] <= 0 or compare(lower, upper) > 0:
            raise CheckStop("unsupported_cell_certificate_interval")
        neighbor_words = (word - 1, word, word + 1)
        values = tuple(decode(neighbor) for neighbor in neighbor_words)
        expected_neighbors = tuple(zip(neighbor_words, values, strict=True))
        if snapshot["neighbors"] != expected_neighbors:
            raise CheckStop("inconsistent_cell_certificate_neighbors")
        expected_boundaries = (
            midpoint(values[0], values[1]),
            midpoint(values[1], values[2]),
        )
        if snapshot["boundaries"] != expected_boundaries:
            raise CheckStop("inconsistent_cell_certificate_boundaries")
        lower_order = compare(lower, expected_boundaries[0])
        upper_order = compare(upper, expected_boundaries[1])
        even = not word & 1
        contained = (lower_order > 0 or (lower_order == 0 and even)) and (
            upper_order < 0 or (upper_order == 0 and even)
        )
        if not contained:
            raise CheckStop("interval_outside_declared_cell")
        if (
            snapshot["closed_ties"] is not even
            or snapshot["lower_order"] != lower_order
            or snapshot["upper_order"] != upper_order
            or snapshot["whole_interval_contained"] is not True
        ):
            raise CheckStop("inconsistent_cell_certificate_claims")
        preflight(0)
        result.update(
            status="verified_synthetic_cell_content",
            reason="independent_exact_cell_content_only",
            certificate={
                "word": word,
                "interval": (lower, upper),
                "neighbors": expected_neighbors,
                "boundaries": expected_boundaries,
                "closed_ties": even,
                "lower_order": lower_order,
                "upper_order": upper_order,
                "whole_interval_contained": True,
            },
        )
    except CheckStop as error:
        result["reason"] = str(error)
    return result


def _certify_synthetic_sinc_cell(interval, *, synthetic_test_only=False):
    """Check one exact rounding cell, without claiming sinc interval inclusion."""
    if synthetic_test_only is not True:
        raise ValueError("cell candidate requires synthetic_test_only=True")
    limit = _SYNTHETIC_SINC_CELL_BITS
    steps = _SYNTHETIC_SINC_CELL_STEPS
    work = {
        "search_iterations": 0,
        "endpoint_iterations": [],
        "dyadic_decodes": 0,
        "midpoint_constructions": 0,
        "rational_comparisons": 0,
        "rational_constructions": 0,
        "max_result_bits": 0,
    }
    result = {
        "identity": "synthetic_sinc_interval_cell_candidate_v0",
        "allowed_use": "isolated_synthetic_cell_controls_only",
        "status": "unresolved_sinc_cell",
        "reason": "unsupported_cell_interval",
        "configuration": {"rational_bit_limit": limit, "endpoint_step_limit": steps},
        "training_approved": False,
        "real_input_qualified": False,
        "free_space_qualified": False,
        "numerically_certified": False,
        "producer_parity_qualified": False,
        "native_sinc_status": "unresolved_native_sinc_evidence",
        "motion_status": "unresolved_motion_evidence",
        "source_status": "unresolved_source_authority",
        "native_work_status": "unresolved_native_work_evidence",
        "consumer_status": "ineligible_isolated_candidate",
        "work": work,
    }
    if (
        type(limit) is not int
        or not 1 <= limit <= 65536
        or type(steps) is not int
        or not 1 <= steps <= 64
    ):
        result["reason"] = "unsupported_cell_configuration"
        return result

    class CellStop(ArithmeticError):
        pass

    def preflight(*sizes):
        if (
            type(_SYNTHETIC_SINC_CELL_BITS) is not int
            or type(_SYNTHETIC_SINC_CELL_STEPS) is not int
            or _SYNTHETIC_SINC_CELL_BITS != limit
            or _SYNTHETIC_SINC_CELL_STEPS != steps
        ):
            raise CellStop("changed_cell_configuration")
        if max(sizes) > limit:
            raise CellStop("cell_rational_work_limit")

    def bounded(value):
        size = max(value.numerator.bit_length(), value.denominator.bit_length())
        preflight(size)
        work["max_result_bits"] = max(work["max_result_bits"], size)
        return value

    def rational(numerator, denominator=1):
        preflight(numerator.bit_length(), denominator.bit_length())
        work["rational_constructions"] += 1
        return bounded(Fraction(numerator, denominator))

    def compare(left, right):
        preflight(
            left.numerator.bit_length() + right.denominator.bit_length(),
            right.numerator.bit_length() + left.denominator.bit_length(),
        )
        work["rational_comparisons"] += 1
        first = left.numerator * right.denominator
        second = right.numerator * left.denominator
        return (first > second) - (first < second)

    def decode(word):
        work["dyadic_decodes"] += 1
        if not 0 <= word <= 0x7FEFFFFFFFFFFFFF:
            raise CellStop("unsupported_cell_neighbor")
        exponent = (word >> 52) & 2047
        significand = (word & ((1 << 52) - 1)) | ((1 << 52) if exponent else 0)
        power = (exponent or 1) - 1075
        preflight(significand.bit_length() + max(0, power), 1 + max(0, -power))
        return rational(significand << max(0, power), 1 << max(0, -power))

    def midpoint(left, right):
        preflight(
            max(
                left.numerator.bit_length() + right.denominator.bit_length(),
                right.numerator.bit_length() + left.denominator.bit_length(),
            )
            + 1,
            left.denominator.bit_length() + right.denominator.bit_length() + 1,
        )
        work["midpoint_constructions"] += 1
        numerator = (
            left.numerator * right.denominator + right.numerator * left.denominator
        )
        denominator = (left.denominator * right.denominator) << 1
        return rational(numerator, denominator)

    def cell(word):
        if not 1 <= word < 0x7FEFFFFFFFFFFFFF:
            raise CellStop("unsupported_cell_edge")
        values = tuple(decode(neighbor) for neighbor in (word - 1, word, word + 1))
        return values, midpoint(values[0], values[1]), midpoint(values[1], values[2])

    def contains(lower, upper, word, boundaries):
        low_order = compare(lower, boundaries[0])
        high_order = compare(upper, boundaries[1])
        even = not word & 1
        return (
            low_order,
            high_order,
            (
                (low_order > 0 or (low_order == 0 and even))
                and (high_order < 0 or (high_order == 0 and even))
            ),
        )

    def endpoint_word(value):
        lower_word, upper_word = 1, 0x7FEFFFFFFFFFFFFF
        attempts = 0
        work["endpoint_iterations"].append(0)
        while lower_word < upper_word:
            if attempts >= steps:
                raise CellStop("cell_search_work_limit")
            preflight(0)
            attempts += 1
            work["search_iterations"] += 1
            work["endpoint_iterations"][-1] = attempts
            word = (lower_word + upper_word) // 2
            boundary = midpoint(decode(word), decode(word + 1))
            order = compare(value, boundary)
            if order < 0 or (order == 0 and not word & 1):
                upper_word = word
            else:
                lower_word = word + 1
        _, lower_boundary, upper_boundary = cell(lower_word)
        if not contains(value, value, lower_word, (lower_boundary, upper_boundary))[2]:
            raise CellStop("unsupported_cell_edge")
        return lower_word

    try:
        if type(interval) is not tuple or len(interval) != 2:
            return result
        endpoints = []
        for pair in interval:
            if (
                type(pair) is not tuple
                or len(pair) != 2
                or any(type(component) is not int for component in pair)
                or pair[1] <= 0
            ):
                return result
            value = rational(*pair)
            if (value.numerator, value.denominator) != pair:
                result["reason"] = "noncanonical_cell_interval"
                return result
            endpoints.append(value)
        lower, upper = endpoints
        if lower.numerator <= 0 or compare(lower, upper) > 0:
            return result
        first, second = endpoint_word(lower), endpoint_word(upper)
        if first != second:
            result["reason"] = "interval_crosses_rounding_cells"
            return result
        values, lower_boundary, upper_boundary = cell(first)
        lower_order, upper_order, contained = contains(
            lower, upper, first, (lower_boundary, upper_boundary)
        )
        if not contained:
            result["reason"] = "unresolved_whole_cell_containment"
            return result
        preflight(0)
        result.update(
            status="contained_synthetic_sinc_cell",
            reason="whole_interval_in_exact_ties_even_cell",
            certificate={
                "word": first,
                "interval": tuple(
                    (value.numerator, value.denominator) for value in endpoints
                ),
                "neighbors": tuple(
                    (neighbor, (value.numerator, value.denominator))
                    for neighbor, value in zip(
                        (first - 1, first, first + 1), values, strict=True
                    )
                ),
                "boundaries": (
                    (lower_boundary.numerator, lower_boundary.denominator),
                    (upper_boundary.numerator, upper_boundary.denominator),
                ),
                "closed_ties": not first & 1,
                "lower_order": lower_order,
                "upper_order": upper_order,
                "whole_interval_contained": True,
            },
        )
    except CellStop as error:
        result["reason"] = str(error)
    return result


def _candidate_synthetic_sinc_word(q_word, *, synthetic_test_only=False):
    """Bind a partial mathematical word candidate to one local sinc enclosure."""
    if synthetic_test_only is not True:
        raise ValueError("sinc word candidate requires synthetic_test_only=True")
    result = {
        "identity": "controlled_mathematical_sinc_rn64_candidate_v0",
        "allowed_use": "isolated_synthetic_sinc_word_candidate_only",
        "status": "unresolved_sinc_word_candidate",
        "reason": "unsupported_sinc_word",
        "target": "real_pi_normalized_sinc_at_stored_binary64",
        "q_word": None,
        "training_approved": False,
        "real_input_qualified": False,
        "free_space_qualified": False,
        "numerically_certified": False,
        "producer_parity_qualified": False,
        "native_sinc_status": "unresolved_native_sinc_evidence",
        "motion_status": "unresolved_motion_evidence",
        "source_status": "unresolved_source_authority",
        "native_work_status": "unresolved_native_work_evidence",
        "consumer_status": "ineligible_isolated_candidate",
        "work": {"enclosure_entries": 0, "cell_entries": 0},
    }
    if type(q_word) is not int or not 0 <= q_word < (1 << 64):
        return result
    result["q_word"] = q_word
    exponent = (q_word >> 52) & 2047
    if exponent == 2047:
        result["reason"] = "nonfinite_sinc_word"
        return result
    sign = q_word >> 63
    significand = (q_word & ((1 << 52) - 1)) | ((1 << 52) if exponent else 0)
    power = (exponent or 1) - 1075
    numerator = significand << max(0, power)
    value = Fraction(-numerator if sign else numerator, 1 << max(0, -power))
    result.update(sign=sign, q_ratio=(value.numerator, value.denominator))
    if abs(value) > Fraction(1, 64):
        result["reason"] = "outside_sinc_domain"
        return result
    result["work"]["enclosure_entries"] += 1
    enclosure = _enclose_synthetic_sinc_word(q_word, synthetic_test_only=True)
    if (
        type(enclosure) is not dict
        or type(enclosure.get("work")) is not dict
        or set(enclosure["work"]) != {"rational_operations", "max_result_bits"}
        or any(
            type(count) is not int or count < 0 for count in enclosure["work"].values()
        )
    ):
        result["reason"] = "inconsistent_sinc_enclosure_binding"
        return result
    result["work"]["enclosure"] = dict(enclosure["work"])
    if enclosure.get("status") != "enclosed_mathematical_sinc":
        result["reason"] = "unresolved_sinc_enclosure"
        return result
    expected_configuration = {
        "arctangent_terms": 32,
        "sinc_terms": 8,
        "rational_bit_limit": 65536,
    }
    configuration = enclosure.get("configuration")
    ratio = enclosure.get("q_ratio")
    if (
        type(enclosure.get("q_word")) is not int
        or enclosure["q_word"] != q_word
        or type(enclosure.get("sign")) is not int
        or enclosure["sign"] != sign
        or type(ratio) is not tuple
        or len(ratio) != 2
        or any(type(component) is not int for component in ratio)
        or ratio != result["q_ratio"]
        or enclosure.get("target") != result["target"]
        or type(configuration) is not dict
        or any(type(count) is not int for count in configuration.values())
        or configuration != expected_configuration
        or enclosure.get("branch") != ("zero" if not value else "series")
    ):
        result["reason"] = "inconsistent_sinc_enclosure_binding"
        return result
    interval = enclosure.get("interval")
    if (
        type(interval) is not tuple
        or len(interval) != 2
        or any(
            type(pair) is not tuple
            or len(pair) != 2
            or any(type(component) is not int for component in pair)
            or pair[1] <= 0
            or max(component.bit_length() for component in pair) > 65536
            for pair in interval
        )
    ):
        result["reason"] = "inconsistent_sinc_enclosure_binding"
        return result
    if not value:
        if interval != ((1, 1), (1, 1)):
            result["reason"] = "inconsistent_zero_sinc_enclosure"
            return result
        certificate = {
            "word": 0x3FF0000000000000,
            "interval": ((1, 1), (1, 1)),
            "branch": "zero",
        }
    else:
        result["work"]["cell_entries"] += 1
        cell_result = _certify_synthetic_sinc_cell(interval, synthetic_test_only=True)
        result["work"]["cell"] = deepcopy(cell_result["work"])
        if cell_result["status"] != "contained_synthetic_sinc_cell":
            result["reason"] = cell_result["reason"]
            return result
        certificate = deepcopy(cell_result["certificate"])
    result.update(
        status="candidate_mathematical_sinc_word",
        reason="conditional_mathematical_rounding_cell_only",
        configuration=dict(expected_configuration),
        interval=deepcopy(interval),
        certificate=certificate,
        enclosure_binding={
            "q_word": q_word,
            "sign": sign,
            "q_ratio": result["q_ratio"],
        },
    )
    return result


def _enclose_synthetic_sinc_word(q_word, *, synthetic_test_only=False):
    """Enclose real-pi sinc at a stored word, not the installed native program."""
    if synthetic_test_only is not True:
        raise ValueError("sinc reference requires synthetic_test_only=True")
    work = {"rational_operations": 0, "max_result_bits": 0}
    result = {
        "allowed_use": "isolated_synthetic_sinc_reference_only",
        "status": "unresolved_mathematical_sinc",
        "reason": "unsupported_sinc_word",
        "target": "real_pi_normalized_sinc_at_stored_binary64",
        "domain_ratio": (1, 64),
        "configuration": {
            "arctangent_terms": 32,
            "sinc_terms": 8,
            "rational_bit_limit": _SYNTHETIC_SINC_BITS,
        },
        "q_word": None,
        "training_approved": False,
        "real_input_qualified": False,
        "free_space_qualified": False,
        "numerically_certified": False,
        "producer_parity_qualified": False,
        "native_sinc_status": "unresolved_native_sinc_evidence",
        "motion_status": "unresolved_motion_evidence",
        "work": work,
    }

    class WorkLimit(ArithmeticError):
        pass

    def preflight(*sizes):
        if max(sizes) > _SYNTHETIC_SINC_BITS:
            raise WorkLimit("sinc_rational_work_limit")

    def bounded(value):
        size = max(value.numerator.bit_length(), value.denominator.bit_length())
        preflight(size)
        work["max_result_bits"] = max(work["max_result_bits"], size)
        return value

    def rational(numerator, denominator=1):
        preflight(numerator.bit_length(), denominator.bit_length())
        return bounded(Fraction(numerator, denominator))

    def add(left, right):
        preflight(
            max(
                left.numerator.bit_length() + right.denominator.bit_length(),
                right.numerator.bit_length() + left.denominator.bit_length(),
            )
            + 1,
            left.denominator.bit_length() + right.denominator.bit_length(),
        )
        work["rational_operations"] += 1
        return bounded(left + right)

    def multiply(left, right):
        preflight(
            left.numerator.bit_length() + right.numerator.bit_length(),
            left.denominator.bit_length() + right.denominator.bit_length(),
        )
        work["rational_operations"] += 1
        return bounded(left * right)

    def divide(left, right):
        return multiply(left, rational(right.denominator, right.numerator))

    def compare(left, right):
        preflight(
            left.numerator.bit_length() + right.denominator.bit_length(),
            right.numerator.bit_length() + left.denominator.bit_length(),
        )
        return (left > right) - (left < right)

    def interval_add(left, right):
        return add(left[0], right[0]), add(left[1], right[1])

    def interval_multiply(left, right):
        products = [multiply(first, second) for first in left for second in right]
        low = high = products[0]
        for product in products[1:]:
            if compare(product, low) < 0:
                low = product
            if compare(product, high) > 0:
                high = product
        return low, high

    def pairs(interval):
        return tuple((value.numerator, value.denominator) for value in interval)

    try:
        if type(q_word) is not int or not 0 <= q_word < (1 << 64):
            return result
        result["q_word"] = q_word
        exponent = (q_word >> 52) & 2047
        if exponent == 2047:
            result["reason"] = "nonfinite_sinc_word"
            return result
        sign = q_word >> 63
        significand = (q_word & ((1 << 52) - 1)) | ((1 << 52) if exponent else 0)
        power = (exponent or 1) - 1075
        preflight(significand.bit_length() + max(0, power), 1 + max(0, -power))
        numerator = significand << max(0, power)
        value = rational(-numerator if sign else numerator, 1 << max(0, -power))
        result.update(q_ratio=(value.numerator, value.denominator), sign=sign)
        if compare(abs(value), rational(1, 64)) > 0:
            result["reason"] = "outside_sinc_domain"
            return result
        if not value:
            result.update(
                status="enclosed_mathematical_sinc",
                reason="exact_mathematical_zero_branch",
                branch="zero",
                interval=((1, 1), (1, 1)),
                stages={},
            )
            return result

        one = rational(1)
        zero = rational(0)
        arctangents = []
        for denominator in (5, 239):
            base = rational(1, denominator)
            square = multiply(base, base)
            odd_power = base
            partial = zero
            for index in range(32):
                coefficient = rational((-1) ** index, 2 * index + 1)
                partial = add(partial, multiply(coefficient, odd_power))
                odd_power = multiply(odd_power, square)
            tail = divide(odd_power, rational(65))
            arctangents.append((partial, add(partial, tail)))
        pi_bounds = interval_add(
            interval_multiply(arctangents[0], (rational(16), rational(16))),
            interval_multiply(arctangents[1], (rational(-4), rational(-4))),
        )
        if (
            compare(rational(3), pi_bounds[0]) >= 0
            or compare(pi_bounds[0], pi_bounds[1]) > 0
            or compare(pi_bounds[1], rational(4)) >= 0
        ):
            result["reason"] = "unsupported_sinc_pi_bracket"
            return result
        squared_argument = interval_multiply(
            (multiply(value, value),) * 2,
            (
                multiply(pi_bounds[0], pi_bounds[0]),
                multiply(pi_bounds[1], pi_bounds[1]),
            ),
        )
        if compare(squared_argument[1], rational(1, 256)) > 0:
            result["reason"] = "outside_sinc_series_domain"
            return result
        factorial = one
        coefficients = []
        for degree in range(18):
            if degree:
                factorial = multiply(factorial, rational(degree))
            if degree % 2 and degree <= 15:
                coefficients.append(divide(rational((-1) ** (degree // 2)), factorial))
        polynomial = (coefficients[-1],) * 2
        for coefficient in reversed(coefficients[:-1]):
            polynomial = interval_add(
                interval_multiply(polynomial, squared_argument), (coefficient,) * 2
            )
        tail_power = one
        for _ in range(8):
            tail_power = multiply(tail_power, squared_argument[1])
        remainder = (zero, divide(tail_power, factorial))
        enclosure = interval_add(polynomial, remainder)
        if compare(enclosure[0], enclosure[1]) > 0:
            result["reason"] = "unsupported_sinc_interval_order"
            return result
        result.update(
            status="enclosed_mathematical_sinc",
            reason="real_pi_even_series_enclosure_only",
            branch="series",
            interval=pairs(enclosure),
            stages={
                "arctangent": tuple(pairs(interval) for interval in arctangents),
                "pi": pairs(pi_bounds),
                "squared_argument": pairs(squared_argument),
                "coefficients": tuple(
                    (coefficient.numerator, coefficient.denominator)
                    for coefficient in coefficients
                ),
                "polynomial": pairs(polynomial),
                "remainder": pairs(remainder),
            },
        )
    except WorkLimit as error:
        result["reason"] = str(error)
    return result


def _synthetic_binary64_value(word):
    if type(word) is not int or not 0 <= word < (1 << 64):
        raise ValueError("binary64 word must be an unsigned integer")
    sign = word >> 63
    exponent = (word >> 52) & 2047
    if exponent == 2047:
        raise ValueError("binary64 word must be finite")
    significand = (word & ((1 << 52) - 1)) | ((1 << 52) if exponent else 0)
    power = (exponent or 1) - 1075
    numerator = significand << max(0, power)
    denominator = 1 << max(0, -power)
    return Fraction(-numerator if sign else numerator, denominator), sign


def _synthetic_rn64(numerator, denominator=1, *, zero_sign=0):
    if (
        type(numerator) is not int
        or type(denominator) is not int
        or denominator <= 0
        or type(zero_sign) is not int
        or zero_sign not in (0, 1)
    ):
        raise ValueError("rounding requires integer rational and zero sign")
    if (
        max(numerator.bit_length(), denominator.bit_length())
        > _SYNTHETIC_ARITHMETIC_BITS
    ):
        raise ValueError("arithmetic work limit")
    sign = int(numerator < 0) if numerator else zero_sign
    numerator = abs(numerator)
    if not numerator:
        return sign << 63
    exponent = numerator.bit_length() - denominator.bit_length()
    if exponent >= 0:
        exponent -= int(numerator < (denominator << exponent))
    else:
        exponent -= int((numerator << -exponent) < denominator)
    if exponent > 1023:
        raise ValueError("rounded binary64 overflow")
    if exponent < -1075:
        return sign << 63
    quantum = max(exponent - 52, -1074)
    if (
        max(
            numerator.bit_length() + max(0, -quantum),
            denominator.bit_length() + max(0, quantum),
        )
        > _SYNTHETIC_ARITHMETIC_BITS
    ):
        raise ValueError("arithmetic work limit")
    scaled_numerator = numerator << max(0, -quantum)
    scaled_denominator = denominator << max(0, quantum)
    coefficient, remainder = divmod(scaled_numerator, scaled_denominator)
    complement = scaled_denominator - remainder
    coefficient += int(
        remainder > complement or (remainder == complement and coefficient & 1)
    )
    if coefficient >= (1 << 53):
        coefficient >>= 1
        quantum += 1
    if coefficient < (1 << 52):
        return (sign << 63) | coefficient
    exponent_field = quantum + 1075
    if exponent_field >= 2047:
        raise ValueError("rounded binary64 overflow")
    return (sign << 63) | (exponent_field << 52) | (coefficient - (1 << 52))


def _synthetic_binary64_operation(operation, left, right):
    if type(operation) is not str or operation not in ("add", "sub", "mul", "div"):
        raise ValueError("unsupported arithmetic operation")
    left_value, left_sign = _synthetic_binary64_value(left)
    right_value, right_sign = _synthetic_binary64_value(right)
    if operation == "sub":
        right_value, right_sign = -right_value, right_sign ^ 1
    if operation in ("add", "sub"):
        exact = left_value + right_value
        zero_sign = int(not left_value and not right_value and left_sign and right_sign)
    elif operation == "mul":
        exact = left_value * right_value
        zero_sign = left_sign ^ right_sign
    else:
        if not right_value:
            raise ValueError("arithmetic division by zero")
        exact = left_value / right_value
        zero_sign = left_sign ^ right_sign
    word = _synthetic_rn64(exact.numerator, exact.denominator, zero_sign=zero_sign)
    rounded, _ = _synthetic_binary64_value(word)
    error = rounded - exact
    return {
        "operation": operation,
        "operands": (left, right),
        "exact_ratio": (exact.numerator, exact.denominator),
        "zero_sign": zero_sign,
        "word": word,
        "rounding_error_ratio": (error.numerator, error.denominator),
    }


def _trace_synthetic_binary64_rows(
    *,
    heading_word,
    turn_word,
    duration_word,
    pi_word,
    two_word,
    word_format="binary64_1_11_52",
    synthetic_test_only=False,
):
    """Trace isolated literal words, never an owner, pose update or qualification."""
    if synthetic_test_only is not True:
        raise ValueError("arithmetic trace requires synthetic_test_only=True")
    result = {
        "allowed_use": "isolated_synthetic_arithmetic_trace_only",
        "supported": False,
        "reason": "unsupported_arithmetic_evidence",
        "training_approved": False,
        "real_input_qualified": False,
        "free_space_qualified": False,
        "numerically_certified": False,
        "producer_parity_qualified": False,
        "rows": (),
    }
    try:
        if type(word_format) is not str or word_format != "binary64_1_11_52":
            raise ValueError("unsupported arithmetic word format")
        values = tuple(
            _synthetic_binary64_value(word)[0]
            for word in (heading_word, turn_word, duration_word, pi_word, two_word)
        )
        if (duration_word, pi_word, two_word) != (
            0x3FA999999999999A,
            0x400921FB54442D18,
            0x4000000000000000,
        ):
            raise ValueError("unsupported arithmetic constant words")
        if abs(values[0]) > values[3] or abs(values[1]) > Fraction(3, 2):
            raise ValueError("unsupported arithmetic trace domain")
        cells = []

        def cell(name, operation, left, right):
            entry = _synthetic_binary64_operation(operation, left, right)
            cells.append({"name": name, **entry})
            return entry["word"]

        angle = cell("a", "mul", turn_word, duration_word)
        half = cell("half", "div", angle, two_word)
        midpoint = cell("m", "add", heading_word, half)
        denominator_q = cell("b_q", "mul", two_word, pi_word)
        argument = cell("q", "div", angle, denominator_q)
        first_sum = cell("x_1", "add", heading_word, angle)
        shifted = cell("x", "add", first_sum, pi_word)
        denominator_r = cell("b_r", "mul", two_word, pi_word)
        shifted_value, shifted_sign = _synthetic_binary64_value(shifted)
        period, period_sign = _synthetic_binary64_value(denominator_r)
        quotient = shifted_value / period
        truncated = abs(quotient.numerator) // quotient.denominator
        if quotient < 0:
            truncated = -truncated
        exact_residue = shifted_value - truncated * period
        residue = _synthetic_rn64(
            exact_residue.numerator, exact_residue.denominator, zero_sign=shifted_sign
        )
        residue_value, _ = _synthetic_binary64_value(residue)
        residue_error = residue_value - exact_residue
        cells.append(
            {
                "name": "z",
                "operation": "truncated_residue",
                "operands": (shifted, denominator_r),
                "truncated_quotient": truncated,
                "exact_ratio": (exact_residue.numerator, exact_residue.denominator),
                "zero_sign": shifted_sign,
                "word": residue,
                "rounding_error_ratio": (
                    residue_error.numerator,
                    residue_error.denominator,
                ),
            }
        )
        if not residue_value:
            corrected = period_sign << 63
            correction = "divisor_signed_zero"
        elif residue_value < 0:
            corrected = cell("u", "add", residue, denominator_r)
            correction = "negative_nonzero"
        else:
            corrected = residue
            correction = "none"
        final = cell("r_next", "sub", corrected, pi_word)
        rows = (
            {"row": "P1", "cells": tuple(cells[:1])},
            {"row": "P2", "cells": tuple(cells[1:3])},
            {"row": "P3", "cells": tuple(cells[3:5])},
            {"row": "P7", "cells": tuple(cells[5:])},
        )
        return {
            **result,
            "supported": True,
            "reason": "literal_word_trace_only",
            "inputs": (heading_word, turn_word, duration_word, pi_word, two_word),
            "rows": rows,
            "rounded_cells": len(cells),
            "residue_correction": correction,
            "intermediate_words": (
                angle,
                half,
                midpoint,
                denominator_q,
                argument,
                first_sum,
                shifted,
                denominator_r,
                residue,
                corrected,
                final,
            ),
        }
    except ValueError as error:
        result["reason"] = str(error)
        return result


def _c1_config(config):
    if config is not None and not isinstance(config, Config):
        raise ValueError("C1 config must be a Config instance")
    config = replace(
        config or Config(noise_std=0, dropout=0), tof_mount_pitch=math.pi / 8
    )
    if (
        config.field_of_view != math.pi / 4
        or config.tof_mount_height != 0.15
        or config.dt != 0.05
        or config.latency_ticks != 2
        or config.tof_rate_hz != 15
        or config.history_ticks != 8
        or any(
            (
                config.noise_std,
                config.dropout,
                config.odometry_position_error,
                config.odometry_heading_error,
                config.odometry_latency_ticks,
            )
        )
    ):
        raise ValueError("C1 requires its declared ideal geometry/timing/error profile")
    return config


def _c1_array(value, shape, kinds="iuf"):
    array = np.asarray(value)
    if array.shape != shape or array.dtype.kind not in kinds:
        raise ValueError("invalid C1 array shape or numeric type")
    if kinds != "b" and any(
        isinstance(item, (bool, np.bool_))
        for item in np.asarray(value, dtype=object).flat
    ):
        raise ValueError("C1 numeric evidence must not contain booleans")
    if not np.all(np.isfinite(array)) or np.any(np.abs(array) > np.finfo(float).max):
        raise ValueError("C1 arrays must be finite")
    return array


def capture_synthetic_c1_views(
    scenario, *, pose_m_rad, capture_tick, config=None, synthetic_test_only=False
):
    """Create an isolated ideal fixture, never a normal simulator observation."""
    if synthetic_test_only is not True:
        raise ValueError("C1 capture requires synthetic_test_only=True")
    config = _c1_config(config)
    if type(capture_tick) is not int or not 0 <= capture_tick <= 0xFFFFFFFF:
        raise ValueError("C1 capture tick must be a u32 integer")
    if capture_tick and capture_tick * 3 // 4 == (capture_tick - 1) * 3 // 4:
        raise ValueError("C1 capture tick does not follow nominal acquisition cadence")
    pose = _c1_array(pose_m_rad, (3,)).astype(float)
    scenario.validate(config)
    ranges = np.stack(
        [
            tof_ranges(pose[:2], pose[2] + index * math.pi / 4, scenario, config)
            for index in range(8)
        ]
    )
    valid = np.isfinite(ranges) & (ranges > 0) & (ranges < config.max_range)
    with np.errstate(over="ignore", invalid="ignore"):
        stored = np.where(valid, ranges, 0).astype(np.float32)
    valid &= np.isfinite(stored) & (stored > 0) & (stored < config.max_range)
    stored[~valid] = 0
    return {
        "schema": C1_SCHEMA,
        "allowed_use": "synthetic_visibility_fixtures_only",
        "training_approved": False,
        "real_input_qualified": False,
        "free_space_qualified": False,
        "config": asdict(config),
        "capture_ticks": np.full(8, capture_tick, dtype=np.uint32),
        "capture_poses_m_rad": np.tile(pose, (8, 1)),
        "tof_m": stored,
        "tof_valid": valid,
    }


def inspect_synthetic_c1_history(
    history,
    *,
    reference_tick,
    reference_pose_m_rad,
    max_age_ticks=3,
    config=None,
    synthetic_test_only=False,
):
    """Inspect bounded declared-exact fixtures; endpoints never qualify free volume."""
    if synthetic_test_only is not True:
        raise ValueError("C1 inspection requires synthetic_test_only=True")
    config = _c1_config(config)
    if (
        type(reference_tick) is not int
        or not 0 <= reference_tick <= 0xFFFFFFFF
        or type(max_age_ticks) is not int
        or not 0 <= max_age_ticks <= 8
    ):
        raise ValueError("C1 reference/age ticks require bounded integers")
    reference = _c1_array(reference_pose_m_rad, (3,)).astype(float)
    result = {
        "schema": "micro-classifier/synthetic-c1-inspection/1",
        "allowed_use": "synthetic_visibility_fixtures_only",
        "training_approved": False,
        "real_input_qualified": False,
        "free_space_qualified": False,
        "status": "unknown",
        "reason": "unsupported_history",
        "points_body_m": None,
        "point_valid": None,
        "unique_capture_count": 0,
        "assumed_max_age_ticks": max_age_ticks,
    }
    if not isinstance(history, (list, tuple)) or not 1 <= len(history) <= 8:
        return result
    previous = None
    unique = set()
    try:
        for index, record in enumerate(history):
            if not isinstance(record, dict) or set(record) != {
                "schema",
                "allowed_use",
                "training_approved",
                "real_input_qualified",
                "free_space_qualified",
                "config",
                "capture_ticks",
                "capture_poses_m_rad",
                "tof_m",
                "tof_valid",
            }:
                return result
            if (
                record["schema"] != C1_SCHEMA
                or record["allowed_use"] != result["allowed_use"]
                or any(
                    record[key] is not False
                    for key in (
                        "training_approved",
                        "real_input_qualified",
                        "free_space_qualified",
                    )
                )
                or json.dumps(record["config"], sort_keys=True, allow_nan=False)
                != json.dumps(asdict(config), sort_keys=True, allow_nan=False)
            ):
                return result
            ticks = _c1_array(record["capture_ticks"], (8,), "iu")
            poses = _c1_array(record["capture_poses_m_rad"], (8, 3))
            ranges = _c1_array(record["tof_m"], (8, 8, 8), "f")
            valid = _c1_array(record["tof_valid"], (8, 8, 8), "b")
            tick = int(ticks[0])
            snapshot_tick = reference_tick - len(history) + 1 + index
            if (
                not np.all(ticks == tick)
                or tick > 0xFFFFFFFF
                or tick > snapshot_tick - config.latency_ticks
                or (tick != 0 and tick * 3 // 4 == (tick - 1) * 3 // 4)
                or not np.all(poses == poses[0])
                or ranges.dtype != np.float32
                or np.any(valid & ((ranges <= 0) | (ranges >= config.max_range)))
                or np.any(~valid & (ranges != 0))
            ):
                return result
            if previous is not None and (
                tick < previous[0]
                or (
                    tick == previous[0]
                    and not all(
                        np.array_equal(first, second)
                        for first, second in zip(
                            (poses, ranges, valid), previous[1:], strict=True
                        )
                    )
                )
            ):
                return result
            previous = tick, poses, ranges, valid
            unique.add(tick)
    except (TypeError, ValueError, OverflowError):
        return result
    result["unique_capture_count"] = len(unique)
    age = reference_tick - tick
    result["latest_age_ticks"] = age
    if age > max_age_ticks:
        result["reason"] = "stale_capture"
        return result
    directions = np.stack(
        [tof_directions(index * math.pi / 4, config) for index in range(8)]
    )
    points = ranges[..., None].astype(float) * directions
    points[..., 2] += config.tof_mount_height
    acquired_yaw = math.atan2(math.sin(poses[0, 2]), math.cos(poses[0, 2]))
    reference_yaw = math.atan2(math.sin(reference[2]), math.cos(reference[2]))
    cosine, sine = (
        math.cos(acquired_yaw - reference_yaw),
        math.sin(acquired_yaw - reference_yaw),
    )
    reference_cosine, reference_sine = math.cos(reference_yaw), math.sin(reference_yaw)
    with np.errstate(over="ignore", invalid="ignore"):
        points[..., :2] = points[..., :2] @ np.array(
            [[cosine, sine], [-sine, cosine]]
        ) + (poses[0, :2] - reference[:2]) @ np.array(
            [[reference_cosine, -reference_sine], [reference_sine, reference_cosine]]
        )
    if not np.all(np.isfinite(points)) or not np.any(valid):
        result["reason"] = "unsupported_points"
        return result
    result.update(
        status="registered_fixture",
        reason="declared_exact_static_assumptions_only",
        points_body_m=np.where(valid[..., None], points, 0),
        point_valid=valid.copy(),
    )
    return result


def _c1_low_free_segments(record, inspection, reference_pose_m_rad, config):
    reference = _c1_array(reference_pose_m_rad, (3,)).astype(float)
    pose = record["capture_poses_m_rad"][0]
    cosine, sine = math.cos(reference[2]), math.sin(reference[2])
    origin = np.array(
        [
            *((pose[:2] - reference[:2]) @ np.array([[cosine, -sine], [sine, cosine]])),
            config.tof_mount_height,
        ]
    )
    ranges, valid = record["tof_m"], inspection["point_valid"]
    directions = np.divide(
        inspection["points_body_m"] - origin,
        ranges[..., None],
        out=np.zeros((8, 8, 8, 3)),
        where=valid[..., None],
    )
    guard = (
        256
        * np.finfo(float).eps
        * max(1.0, config.max_range, *np.abs(reference), *np.abs(pose))
    )
    downward = -directions[..., 2]
    near = (
        np.divide(
            config.tof_mount_height - 0.05,
            downward,
            out=np.full((8, 8, 8), np.inf),
            where=downward > 0,
        )
        + guard
    )
    floor = np.divide(
        config.tof_mount_height,
        downward,
        out=np.full((8, 8, 8), -np.inf),
        where=downward > 0,
    )
    lower_range = np.nextafter(ranges, np.float32(0)).astype(float)
    far = np.minimum(lower_range, floor) - guard
    selected = valid & (downward > 0) & (far > near)
    starts = origin + near[selected, None] * directions[selected]
    ends = origin + far[selected, None] * directions[selected]
    return np.stack((starts, ends), axis=1), guard


def _bind_synthetic_c1_state_intervals(
    source_state, state_frame, *, max_integer_bits=4096, synthetic_test_only=False
):
    """Bind exact source/decoded dyadics as fixture bounds, never source authority."""
    from interface.protocol import ProtocolError, State, decode_state, encode_state

    if synthetic_test_only is not True:
        raise ValueError("source intervals require synthetic_test_only=True")
    if type(source_state) is not State:
        raise TypeError("source intervals require a synthetic source State")
    if type(max_integer_bits) is not int or not 1 <= max_integer_bits <= 4096:
        raise ValueError("source interval integer limit must be from one through 4096")
    result = {
        "schema": "micro-classifier/synthetic-c1-source-intervals/1",
        "allowed_use": "conditional_source_word_fixture_only",
        "training_approved": False,
        "real_input_qualified": False,
        "numerically_certified": False,
        "source_qualified": False,
        "command_admission_qualified": False,
        "fixture_words_bound": False,
        "status": "unknown",
        "reason": "unsupported_state_frame",
        "component_pairs_checked": 0,
    }
    if type(state_frame) is not bytes:
        return result
    try:
        decoded = decode_state(state_frame)
        source_frame = encode_state(source_state)
    except (ProtocolError, OverflowError, TypeError):
        result["reason"] = "invalid_state_frame_or_source"
        return result
    if source_frame != state_frame:
        result["reason"] = "source_frame_binding_mismatch"
        return result
    if decoded.validity & 7 != 7:
        result["reason"] = "unsupported_host_validity"
        return result
    if decoded.ages_us[:3] != (0, 0, 0):
        result["reason"] = "stale_host_state"
        return result
    fields = {}
    for field in ("velocity_m_s", "angular_velocity_rad_s", "goal_m"):
        values = []
        for source, received in zip(
            getattr(source_state, field), getattr(decoded, field), strict=True
        ):
            result["component_pairs_checked"] += 1
            if type(source) not in (int, float):
                result["reason"] = "unsupported_source_numeric_type"
                return result
            if type(source) is int and source.bit_length() > max_integer_bits:
                result["reason"] = "source_integer_budget_exhausted"
                return result
            number = float(source)
            if type(source) is int and number != source:
                result["reason"] = "source_integer_not_exact_binary64"
                return result
            source = number
            left, left_denominator = source.as_integer_ratio()
            right, right_denominator = received.as_integer_ratio()
            denominator = max(left_denominator, right_denominator)
            left_scale, right_scale = (
                denominator // left_denominator,
                denominator // right_denominator,
            )
            if (
                denominator.bit_length() > max_integer_bits
                or left.bit_length() + left_scale.bit_length() > max_integer_bits
                or right.bit_length() + right_scale.bit_length() > max_integer_bits
                or max(
                    left.bit_length() + left_scale.bit_length(),
                    right.bit_length() + right_scale.bit_length(),
                )
                + 1
                > max_integer_bits
            ):
                result["reason"] = "source_integer_budget_exhausted"
                return result
            difference = Fraction(right * right_scale - left * left_scale, denominator)
            source_pair = (left, left_denominator)
            decoded_pair = (right, right_denominator)
            values.append(
                {
                    "source": source_pair,
                    "decoded": decoded_pair,
                    "interval": [source_pair, decoded_pair]
                    if source <= received
                    else [decoded_pair, source_pair],
                    "decoded_minus_source": (
                        difference.numerator,
                        difference.denominator,
                    ),
                    "source_hex": source.hex(),
                    "decoded_hex": received.hex(),
                }
            )
        fields[field] = values
    result.update(
        status="bound_under_fixture_assumptions",
        reason="exact_source_frame_and_decoded_dyadic_intervals",
        fixture_words_bound=True,
        state_frame=state_frame,
        sequence=decoded.sequence,
        timestamp_us=decoded.timestamp_us,
        fields=fields,
    )
    return result


def _bound_synthetic_c1_history_registration(
    source_states,
    state_frames,
    *,
    acquisition_tick,
    reference_tick,
    point_radius_m,
    assumptions=None,
    max_history_ticks=3,
    source_max_integer_bits=4096,
    max_integer_bits=16384,
    synthetic_test_only=False,
):
    """Bound paired stored-word history transforms, never measured registration."""
    from interface.protocol import decode_state

    if synthetic_test_only is not True:
        raise ValueError("history registration requires synthetic_test_only=True")
    for limit, lower, upper in (
        (max_history_ticks, 0, 3),
        (source_max_integer_bits, 1, 4096),
        (max_integer_bits, 1, 16384),
    ):
        if type(limit) is not int or not lower <= limit <= upper:
            raise ValueError("history registration limits must be bounded integers")
    work = {"binding_entries": 0, "intervals": 0}
    result = {
        "schema": "micro-classifier/synthetic-c1-history-registration/1",
        "allowed_use": "conditional_source_word_registration_fixture_only",
        **{
            flag: False
            for flag in (
                "training_approved",
                "real_input_qualified",
                "free_space_qualified",
                "numerically_certified",
                "source_qualified",
                "native_execution_qualified",
                "command_admission_qualified",
            )
        },
        "fixture_registration_bound": False,
        "status": "unknown",
        "reason": "unsupported_history_assumptions",
        "work": work,
    }
    required = {
        "starting_pose_exact",
        "nominal_tick_binding_exact",
        "stored_word_dt_exact",
        "interval_ending_twist_exact",
    }
    if (
        type(assumptions) is not dict
        or set(assumptions) != required
        or any(assumptions[key] is not True for key in required)
    ):
        return result
    if (
        type(acquisition_tick) is not int
        or type(reference_tick) is not int
        or not 0 <= acquisition_tick <= reference_tick <= 85899
    ):
        result["reason"] = "unsupported_history_ticks"
        return result
    count = reference_tick - acquisition_tick + 1
    if count - 1 > max_history_ticks:
        result["reason"] = "history_budget_exhausted"
        return result
    if (
        type(source_states) not in (tuple, list)
        or type(state_frames) not in (tuple, list)
        or len(source_states) != count
        or len(state_frames) != count
    ):
        result["reason"] = "incomplete_frame_history"
        return result
    arithmetic = _C1CommandArithmetic(0, max_integer_bits, work)
    bindings = []
    previous_sequence = None
    try:
        radius = arithmetic.value(point_radius_m)
        zero, seconds = arithmetic.value(0), arithmetic.value(0.05)
        if arithmetic.binary(radius, zero, "less") or arithmetic.binary(
            arithmetic.value(4), radius, "less"
        ):
            result["reason"] = "unsupported_point_radius"
            return result
        translation = heading = travel = zero
        for index, (source, frame) in enumerate(
            zip(source_states, state_frames, strict=True)
        ):
            work["binding_entries"] += 1
            binding = _bind_synthetic_c1_state_intervals(
                source,
                frame,
                max_integer_bits=source_max_integer_bits,
                synthetic_test_only=True,
            )
            if binding["fixture_words_bound"] is not True:
                result["reason"] = binding["reason"]
                return result
            decoded = decode_state(frame)
            if (
                decoded.timestamp_us != (acquisition_tick + index) * 50000
                or previous_sequence is not None
                and decoded.sequence != previous_sequence + 1
            ):
                result["reason"] = "frame_history_binding_mismatch"
                return result
            previous_sequence = decoded.sequence
            if decoded.task_id != 1 or decoded.faults != 0:
                result["reason"] = "unsupported_host_task_or_faults"
                return result
            fields = binding["fields"]
            for field, indices in (
                ("velocity_m_s", (1, 2)),
                ("angular_velocity_rad_s", (0, 1)),
                ("goal_m", (2,)),
            ):
                if any(
                    Fraction(*pair) != 0
                    for coordinate in indices
                    for pair in fields[field][coordinate]["interval"]
                ):
                    result["reason"] = "unsupported_planar_source_intervals"
                    return result
            speeds = tuple(
                Fraction(*pair) for pair in fields["velocity_m_s"][0]["interval"]
            )
            turns = tuple(
                Fraction(*pair)
                for pair in fields["angular_velocity_rad_s"][2]["interval"]
            )
            if (
                arithmetic.binary(speeds[0], zero, "less")
                or arithmetic.binary(arithmetic.value(0.6), speeds[1], "less")
                or arithmetic.binary(turns[0], arithmetic.value(-1.5), "less")
                or arithmetic.binary(arithmetic.value(1.5), turns[1], "less")
            ):
                result["reason"] = "source_interval_outside_motion_domain"
                return result
            bindings.append(binding)
            if index == 0:
                continue
            work["intervals"] += 1
            speed_delta = arithmetic.binary(speeds[1], speeds[0], "sub")
            turn_delta = arithmetic.binary(turns[1], turns[0], "sub")
            heading_step = arithmetic.binary(turn_delta, seconds, "mul")
            mean_heading = arithmetic.binary(
                heading,
                arithmetic.binary(heading_step, arithmetic.value(2), "div"),
                "add",
            )
            velocity_error = arithmetic.binary(
                speed_delta,
                arithmetic.binary(speeds[1], mean_heading, "mul"),
                "add",
            )
            translation = arithmetic.binary(
                translation,
                arithmetic.binary(velocity_error, seconds, "mul"),
                "add",
            )
            heading = arithmetic.binary(heading, heading_step, "add")
            travel = arithmetic.binary(
                travel, arithmetic.binary(speeds[1], seconds, "mul"), "add"
            )
        point_error = arithmetic.binary(
            translation,
            arithmetic.binary(arithmetic.binary(radius, travel, "add"), heading, "mul"),
            "add",
        )
        bounds = {
            "translation_m": translation,
            "heading_rad": heading,
            "registered_point_m": point_error,
        }
        upper = {key: arithmetic.outward(value, True) for key, value in bounds.items()}
    except ArithmeticError as error:
        result["reason"] = str(error)
        return result
    except ValueError:
        result["reason"] = "unsupported_registration_input"
        return result
    result.update(
        status="bounded_from_complete_word_history",
        reason="complete_interval_ending_discrepancy_propagated",
        fixture_registration_bound=True,
        acquisition_tick=acquisition_tick,
        reference_tick=reference_tick,
        point_radius_m=float(radius),
        upper_bounds=upper,
        rational_bounds={
            key: (value.numerator, value.denominator) for key, value in bounds.items()
        },
        source_bindings=deepcopy(bindings),
        assumptions=deepcopy(assumptions),
    )
    return result


def _probe_synthetic_c1_state_motion(
    source_state,
    state_frame,
    *,
    reference_tick,
    target_speed,
    turn_rate,
    error_evidence=None,
    profile=None,
    max_braking_ticks=16,
    max_chords=128,
    max_terms=16,
    source_max_integer_bits=4096,
    motion_max_integer_bits=16384,
    synthetic_test_only=False,
):
    """Propagate bound host-word speed intervals into the ideal motion fixture."""
    from interface.protocol import decode_state

    if synthetic_test_only is not True:
        raise ValueError("state motion requires synthetic_test_only=True")
    work = {"binding_entries": 0, "motion_entries": 0}
    result = {
        "schema": "micro-classifier/synthetic-c1-state-motion/1",
        "allowed_use": "conditional_source_word_motion_fixture_only",
        **{
            flag: False
            for flag in (
                "training_approved",
                "real_input_qualified",
                "free_space_qualified",
                "numerically_certified",
                "source_qualified",
                "native_execution_qualified",
                "command_admission_qualified",
            )
        },
        "fixture_motion_enclosed": False,
        "status": "unknown",
        "reason": "unsupported_reference_tick",
        "work": work,
    }
    if type(reference_tick) is not int or not 0 <= reference_tick <= 85899:
        return result
    work["binding_entries"] = 1
    binding = _bind_synthetic_c1_state_intervals(
        source_state,
        state_frame,
        max_integer_bits=source_max_integer_bits,
        synthetic_test_only=True,
    )
    result["source_intervals"] = deepcopy(binding)
    if binding["fixture_words_bound"] is not True:
        result["reason"] = binding["reason"]
        return result
    decoded = decode_state(state_frame)
    if decoded.timestamp_us != reference_tick * 50000:
        result["reason"] = "frame_tick_binding_mismatch"
        return result
    if decoded.task_id != 1 or decoded.faults != 0:
        result["reason"] = "unsupported_host_task_or_faults"
        return result
    fields = binding["fields"]
    for field, indices in (
        ("velocity_m_s", (1, 2)),
        ("angular_velocity_rad_s", (0, 1)),
        ("goal_m", (2,)),
    ):
        for index in indices:
            if any(Fraction(*pair) != 0 for pair in fields[field][index]["interval"]):
                result["reason"] = "unsupported_planar_source_intervals"
                return result
    speeds = tuple(Fraction(*pair) for pair in fields["velocity_m_s"][0]["interval"])
    yaw = tuple(
        Fraction(*pair) for pair in fields["angular_velocity_rad_s"][2]["interval"]
    )
    if (
        speeds[0] < 0
        or speeds[1] > Fraction(0.6)
        or yaw[0] < Fraction(-1.5)
        or yaw[1] > Fraction(1.5)
    ):
        result["reason"] = "source_interval_outside_motion_domain"
        return result
    if (
        type(target_speed) not in (int, float)
        or type(turn_rate) not in (int, float)
        or not 0 <= target_speed <= 0.6
        or not -1.5 <= turn_rate <= 1.5
    ):
        result["reason"] = "unsupported_command_domain"
        return result
    endpoints = tuple(float(speed) for speed in speeds)
    if any(
        Fraction(value) != speed for value, speed in zip(endpoints, speeds, strict=True)
    ):
        result["reason"] = "unsupported_speed_endpoint_conversion"
        return result
    work["motion_entries"] = 1
    motion = _probe_synthetic_c1_discrete_motion(
        initial_speed=endpoints,
        target_speed=target_speed,
        turn_rate=turn_rate,
        error_evidence=deepcopy(error_evidence),
        profile=deepcopy(profile),
        max_braking_ticks=max_braking_ticks,
        max_chords=max_chords,
        max_terms=max_terms,
        max_integer_bits=motion_max_integer_bits,
        synthetic_test_only=True,
    )
    if motion["fixture_motion_enclosed"] is not True:
        result["reason"] = motion["reason"]
        result["motion_work"] = deepcopy(motion["work"])
        return result
    result.update(
        status="enclosed_from_bound_source_fixture",
        reason="complete_source_word_speed_interval_propagated",
        fixture_motion_enclosed=True,
        initial_speed_interval_m_s=endpoints,
        motion=deepcopy(motion),
    )
    return result


def _probe_synthetic_c1_discrete_path_enclosure(
    history,
    motion,
    *,
    reference_tick,
    reference_pose_m_rad,
    current_body_clear=False,
    controlled_envelope=False,
    max_cells=32768,
    max_depth=10,
    radius_bands=8,
    config=None,
    point_error_evidence=None,
    synthetic_test_only=False,
):
    """Check C1 fixture prefixes against a complete supplied discrete path tube."""
    if synthetic_test_only is not True:
        raise ValueError("discrete path enclosure requires synthetic_test_only=True")
    for value, lower, upper in (
        (max_cells, 0, 65536),
        (max_depth, 0, 12),
        (radius_bands, 1, 16),
    ):
        if type(value) is not int or not lower <= value <= upper:
            raise ValueError("discrete path work limits require bounded integers")
    config = _c1_config(config)
    work = {"inspection_entries": 0, "prefix_entries": 0, "cell_entries": 0}
    flags = (
        "training_approved",
        "real_input_qualified",
        "free_space_qualified",
        "numerically_certified",
        "source_qualified",
        "native_execution_qualified",
        "command_admission_qualified",
    )
    result = {
        "schema": "micro-classifier/synthetic-c1-discrete-path-enclosure/1",
        "allowed_use": "conditional_ideal_path_fixture_only",
        **{flag: False for flag in flags},
        "fixture_enclosure_excluded": False,
        "status": "unknown",
        "reason": "unsupported_motion_fixture",
        "work": work,
        "cells_checked": 0,
    }
    if (
        type(motion) is not dict
        or any(type(key) is not str for key in motion)
        or motion.get("schema") != "micro-classifier/synthetic-c1-discrete-motion/1"
        or motion.get("allowed_use") != "conditional_ideal_motion_fixture_only"
        or motion.get("status") != "enclosed_under_fixture_assumptions"
        or motion.get("fixture_motion_enclosed") is not True
        or motion.get("assumption")
        != "stored_input_words_as_reals_not_native_execution"
        or any(motion.get(flag) is not False for flag in flags)
    ):
        return result
    boxes, chords = motion.get("centerline_boxes_m"), motion.get("chords")
    if (
        type(boxes) is not list
        or type(chords) is not list
        or not 1 <= len(chords) <= 128
        or len(boxes) != len(chords) + 1
    ):
        return result
    motion_work = motion.get("work")
    if (
        type(motion_work) is not dict
        or any(type(key) is not str for key in motion_work)
        or set(motion_work)
        != {"command_ticks", "braking_ticks", "chords", "series_terms"}
        or any(type(value) is not int for value in motion_work.values())
        or motion_work["command_ticks"] != 1
        or motion_work["braking_ticks"] != len(chords) - 1
        or not 0 <= motion_work["braking_ticks"] <= 16
        or motion_work["chords"] != len(chords)
        or not 0 <= motion_work["series_terms"] <= 16
    ):
        return result
    try:
        boxes = _c1_array(boxes, (len(boxes), 2, 2)).astype(float)
        if np.any(boxes[..., 0] > boxes[..., 1]) or np.any(boxes[0] != 0):
            return result
        speeds = _c1_array(motion.get("speed_intervals_m_s"), (len(chords), 2))
        if (
            np.any(speeds[:, 0] < 0)
            or np.any(speeds[:, 1] > config.max_speed)
            or np.any(speeds[:, 0] > speeds[:, 1])
            or np.any(speeds[-1] != 0)
        ):
            return result
        radii = []
        for index, chord in enumerate(chords):
            if (
                type(chord) is not dict
                or any(type(key) is not str for key in chord)
                or set(chord) != {"start_box_m", "end_box_m", "radius_upper_m"}
                or type(chord["radius_upper_m"]) not in (int, float)
            ):
                return result
            start = _c1_array(chord["start_box_m"], (2, 2))
            end = _c1_array(chord["end_box_m"], (2, 2))
            radius = float(_c1_array([chord["radius_upper_m"]], (1,))[0])
            if (
                not np.array_equal(start, boxes[index])
                or not np.array_equal(end, boxes[index + 1])
                or radius < config.radius
            ):
                return result
            radii.append(radius)
    except (TypeError, ValueError, OverflowError):
        return result
    if current_body_clear is not True:
        result["reason"] = "current_body_clear_not_established"
        return result
    if controlled_envelope is not True:
        result["reason"] = "controlled_envelope_not_established"
        return result
    if (
        config.radius,
        config.acceleration,
        config.max_speed,
        config.max_turn_rate,
        config.max_range,
        config.wall_height,
    ) != (0.18, 1, 0.6, 1.5, 4, 1):
        result["reason"] = "unsupported_dynamics_or_wall_profile"
        return result
    if point_error_evidence is not None:
        if (
            type(point_error_evidence) is not dict
            or set(point_error_evidence)
            != {
                "source_states",
                "state_frames",
                "history_assumptions",
                "prefix_history_binding_exact",
                "remaining_point_error_m",
                "point_radius_m",
            }
            or point_error_evidence["prefix_history_binding_exact"] is not True
        ):
            result["reason"] = "unsupported_point_error_evidence"
            return result
        if point_error_evidence["remaining_point_error_m"] is None:
            result["reason"] = "remaining_point_error_missing"
            return result
    work["inspection_entries"] = 1
    inspection = inspect_synthetic_c1_history(
        history,
        reference_tick=reference_tick,
        reference_pose_m_rad=reference_pose_m_rad,
        config=config,
        synthetic_test_only=True,
    )
    if inspection["status"] != "registered_fixture":
        result["reason"] = inspection["reason"]
        return result
    reference = _c1_array(reference_pose_m_rad, (3,)).astype(float)
    record = history[-1]
    pose = record["capture_poses_m_rad"][0]
    age = inspection["latest_age_ticks"] * config.dt
    guard = float(
        256
        * np.finfo(float).eps
        * max(
            1.0,
            config.max_range,
            *np.abs(reference),
            *np.abs(pose),
            *np.abs(boxes.flat),
        )
    )
    yaw_delta = math.atan2(
        math.sin(pose[2] - reference[2]), math.cos(pose[2] - reference[2])
    )
    if (
        math.hypot(float(pose[0]) - reference[0], float(pose[1]) - reference[1])
        > config.max_speed * age + guard
        or abs(yaw_delta) > config.max_turn_rate * age + guard
    ):
        result["reason"] = "unsupported_capture_to_reference_motion"
        return result
    work["prefix_entries"] = 1
    segments, prefix_guard = _c1_low_free_segments(
        record, inspection, reference, config
    )
    guard = max(guard, float(prefix_guard))
    if not len(segments):
        result["reason"] = "no_low_height_free_segments"
        return result
    path_guard = guard
    if point_error_evidence is not None:
        arithmetic = _C1CommandArithmetic(0, 16384, {})
        try:
            radius = arithmetic.value(point_error_evidence["point_radius_m"])
            remaining = arithmetic.value(
                point_error_evidence["remaining_point_error_m"]
            )
            zero = arithmetic.value(0)
            if (
                arithmetic.binary(radius, zero, "less")
                or arithmetic.binary(arithmetic.value(config.max_range), radius, "less")
                or arithmetic.binary(remaining, zero, "less")
            ):
                result["reason"] = "unsupported_point_error_domain"
                return result
            cosine, sine = math.cos(reference[2]), math.sin(reference[2])
            origin = (pose[:2] - reference[:2]) @ np.array(
                [[cosine, -sine], [sine, cosine]]
            )
            selected = []
            for segment in segments:
                enclosed = True
                for point in segment[:, :2]:
                    norm = zero
                    for coordinate, anchor in zip(point, origin, strict=True):
                        displacement = arithmetic.binary(
                            arithmetic.value(float(coordinate)),
                            arithmetic.value(float(anchor)),
                            "sub",
                        )
                        norm = arithmetic.binary(norm, abs(displacement), "add")
                    if arithmetic.binary(radius, norm, "less"):
                        enclosed = False
                if enclosed:
                    selected.append(segment)
            if not selected:
                result["reason"] = "no_point_radius_supported_prefixes"
                return result
            segments = np.asarray(selected)
            registration = _bound_synthetic_c1_history_registration(
                point_error_evidence["source_states"],
                point_error_evidence["state_frames"],
                acquisition_tick=int(record["capture_ticks"][0]),
                reference_tick=reference_tick,
                point_radius_m=point_error_evidence["point_radius_m"],
                assumptions=deepcopy(point_error_evidence["history_assumptions"]),
                synthetic_test_only=True,
            )
            if registration["fixture_registration_bound"] is not True:
                result["reason"] = registration["reason"]
                result["registration_work"] = deepcopy(registration["work"])
                return result
            combined = arithmetic.binary(
                arithmetic.binary(arithmetic.value(guard), remaining, "add"),
                arithmetic.value(registration["upper_bounds"]["registered_point_m"]),
                "add",
            )
            guard = arithmetic.outward(combined, True)
        except ArithmeticError as error:
            result["reason"] = str(error)
            return result
        except (TypeError, ValueError, OverflowError):
            result["reason"] = "unsupported_point_error_input"
            return result
        result.update(
            point_error_guard_m=guard,
            registration_bound=deepcopy(registration),
        )
    points = boxes[..., 0] + (boxes[..., 1] - boxes[..., 0]) / 2
    widths = np.maximum(points - boxes[..., 0], boxes[..., 1] - points)
    errors = np.sum(widths, axis=1)
    tube_radius = (
        float(np.max(np.asarray(radii) + np.maximum(errors[:-1], errors[1:])))
        + path_guard
    )
    if not math.isfinite(tube_radius) or not np.all(np.isfinite(points)):
        result["reason"] = "unsupported_path_bound"
        return result
    cosine, sine = math.cos(reference[2]), math.sin(reference[2])
    rotation = np.array([[cosine, sine], [-sine, cosine]])
    world_prefixes = segments[..., :2].reshape(-1, 2) @ rotation
    world_path = points @ rotation
    if not (
        np.all(
            world_prefixes.min(axis=0) < world_path.min(axis=0) - tube_radius - guard
        )
        and np.all(
            world_prefixes.max(axis=0) > world_path.max(axis=0) + tube_radius + guard
        )
    ):
        result["reason"] = "axis_aligned_wall_support_incomplete"
        return result
    work["cell_entries"] = 1
    cells = _c1_exclude_path_cells(
        segments[..., :2],
        points,
        tube_radius,
        current_body_clear=True,
        guard=guard,
        max_cells=max_cells,
        max_depth=max_depth,
        radius_bands=radius_bands,
    )
    result.update(cells)
    result.update(
        path_points_body_m=points.tolist(),
        path_tube_radius_m=tube_radius,
        free_segment_count=len(segments),
    )
    if cells["fixture_enclosure_excluded"]:
        result.update(
            status="excluded_under_fixture_assumptions",
            reason="complete_discrete_path_and_axis_aligned_walls_excluded",
        )
    return result


def _probe_synthetic_c1_command_path_enclosure(
    history,
    point_error_evidence,
    *,
    reference_tick,
    reference_pose_m_rad,
    target_speed,
    turn_rate,
    error_evidence=None,
    profile=None,
    current_body_clear=False,
    controlled_envelope=False,
    max_braking_ticks=16,
    max_chords=128,
    max_terms=16,
    max_cells=32768,
    max_depth=10,
    radius_bands=8,
    config=None,
    synthetic_test_only=False,
):
    """Compose one owned current-frame motion with conditional point margins."""
    from interface.protocol import State

    if synthetic_test_only is not True:
        raise ValueError("command path enclosure requires synthetic_test_only=True")
    for value, lower, upper in (
        (max_braking_ticks, 0, 16),
        (max_chords, 1, 128),
        (max_terms, 0, 16),
        (max_cells, 0, 65536),
        (max_depth, 0, 12),
        (radius_bands, 1, 16),
    ):
        if type(value) is not int or not lower <= value <= upper:
            raise ValueError("command path work limits require bounded integers")
    work = {"state_motion_entries": 0, "path_entries": 0}
    result = {
        "schema": "micro-classifier/synthetic-c1-command-path-enclosure/1",
        "allowed_use": "conditional_source_command_path_fixture_only",
        **{
            flag: False
            for flag in (
                "training_approved",
                "real_input_qualified",
                "free_space_qualified",
                "numerically_certified",
                "source_qualified",
                "native_execution_qualified",
                "command_admission_qualified",
            )
        },
        "fixture_command_path_excluded": False,
        "status": "unknown",
        "reason": "unsupported_point_error_evidence",
        "work": work,
    }
    if (
        type(point_error_evidence) is not dict
        or any(type(key) is not str for key in point_error_evidence)
        or set(point_error_evidence)
        != {
            "source_states",
            "state_frames",
            "history_assumptions",
            "prefix_history_binding_exact",
            "remaining_point_error_m",
            "point_radius_m",
        }
        or point_error_evidence["prefix_history_binding_exact"] is not True
    ):
        return result
    if point_error_evidence["remaining_point_error_m"] is None:
        result["reason"] = "remaining_point_error_missing"
        return result
    states = point_error_evidence["source_states"]
    frames = point_error_evidence["state_frames"]
    if (
        type(states) not in (list, tuple)
        or type(frames) not in (list, tuple)
        or not 1 <= len(states) == len(frames) <= 4
        or any(type(state) is not State for state in states)
        or any(
            type(frame) is not bytes or not 1 <= len(frame) <= 128 for frame in frames
        )
    ):
        result["reason"] = "unsupported_frame_history"
        return result
    if current_body_clear is not True:
        result["reason"] = "current_body_clear_not_established"
        return result
    if controlled_envelope is not True:
        result["reason"] = "controlled_envelope_not_established"
        return result
    config = _c1_config(config)
    if config.dt != 0.05:
        result["reason"] = "unsupported_command_tick_profile"
        return result
    owned = deepcopy(point_error_evidence)
    work["state_motion_entries"] = 1
    state_motion = _probe_synthetic_c1_state_motion(
        owned["source_states"][-1],
        owned["state_frames"][-1],
        reference_tick=reference_tick,
        target_speed=target_speed,
        turn_rate=turn_rate,
        error_evidence=deepcopy(error_evidence),
        profile=deepcopy(profile),
        max_braking_ticks=max_braking_ticks,
        max_chords=max_chords,
        max_terms=max_terms,
        synthetic_test_only=True,
    )
    result["state_motion_work"] = deepcopy(state_motion["work"])
    if state_motion["fixture_motion_enclosed"] is not True:
        result["reason"] = state_motion["reason"]
        if "motion_work" in state_motion:
            result["motion_work"] = deepcopy(state_motion["motion_work"])
        return result
    work["path_entries"] = 1
    enclosure = _probe_synthetic_c1_discrete_path_enclosure(
        history,
        state_motion["motion"],
        reference_tick=reference_tick,
        reference_pose_m_rad=reference_pose_m_rad,
        current_body_clear=True,
        controlled_envelope=True,
        max_cells=max_cells,
        max_depth=max_depth,
        radius_bands=radius_bands,
        config=config,
        point_error_evidence=owned,
        synthetic_test_only=True,
    )
    result["path_work"] = deepcopy(enclosure["work"])
    if enclosure["fixture_enclosure_excluded"] is not True:
        result["reason"] = enclosure["reason"]
        return result
    if (
        enclosure["registration_bound"]["source_bindings"][-1]
        != state_motion["source_intervals"]
    ):
        result["reason"] = "current_frame_history_binding_mismatch"
        return result
    result.update(
        status="excluded_from_bound_command_fixture",
        reason="generated_command_path_and_complete_point_errors_excluded",
        fixture_command_path_excluded=True,
        current_state_frame_hex=owned["state_frames"][-1].hex(),
        reference_tick=reference_tick,
        requested_command={
            "target_speed_m_s": target_speed,
            "turn_rate_rad_s": turn_rate,
        },
        state_motion=deepcopy(state_motion),
        path_enclosure=deepcopy(enclosure),
    )
    return result


def _c1_exclude_registered_path_cells(
    free_segments,
    path_points,
    tube_radius,
    source_states,
    state_frames,
    *,
    acquisition_tick,
    reference_tick,
    capture_origin_body_m,
    point_radius_m,
    prefix_history_binding_exact=False,
    other_point_error_m=None,
    assumptions=None,
    current_body_clear=False,
    controlled_envelope=False,
    guard=0.0,
    max_cells=32768,
    max_depth=10,
    radius_bands=8,
    max_history_ticks=3,
    source_max_integer_bits=4096,
    max_integer_bits=16384,
    synthetic_test_only=False,
):
    """Erode conditional relative prefixes by complete declared point errors."""
    if synthetic_test_only is not True:
        raise ValueError("registered path cells require synthetic_test_only=True")
    for limit, lower, upper in (
        (max_cells, 0, 65536),
        (max_depth, 0, 12),
        (radius_bands, 1, 16),
        (max_history_ticks, 0, 3),
        (source_max_integer_bits, 1, 4096),
        (max_integer_bits, 1, 16384),
    ):
        if type(limit) is not int or not lower <= limit <= upper:
            raise ValueError("registered cell limits must be bounded integers")
    work = {"registration_entries": 0, "prefix_points_checked": 0, "cell_entries": 0}
    result = {
        "schema": "micro-classifier/synthetic-c1-registered-path-cells/1",
        "allowed_use": "conditional_source_word_prefix_fixture_only",
        **{
            flag: False
            for flag in (
                "training_approved",
                "real_input_qualified",
                "free_space_qualified",
                "numerically_certified",
                "source_qualified",
                "native_execution_qualified",
                "command_admission_qualified",
            )
        },
        "fixture_enclosure_excluded": False,
        "status": "unknown",
        "reason": "prefix_history_binding_not_established",
        "work": work,
        "cells_checked": 0,
    }
    if prefix_history_binding_exact is not True:
        return result
    if other_point_error_m is None:
        result["reason"] = "remaining_point_error_missing"
        return result
    if current_body_clear is not True or controlled_envelope is not True:
        result["reason"] = "body_or_envelope_not_established"
        return result
    if (
        type(free_segments) is not np.ndarray
        or free_segments.ndim != 3
        or free_segments.shape[1:] != (2, 2)
        or not 1 <= len(free_segments) <= 512
    ):
        result["reason"] = "unsupported_relative_prefixes"
        return result
    arithmetic = _C1CommandArithmetic(0, max_integer_bits, work)
    try:
        segments = _c1_array(free_segments, free_segments.shape).astype(float)
        origin = _c1_array(capture_origin_body_m, (2,)).astype(float)
        origin = tuple(arithmetic.value(float(value)) for value in origin)
        radius = arithmetic.value(point_radius_m)
        remaining = arithmetic.value(other_point_error_m)
        numerical_guard = arithmetic.value(guard)
        zero = arithmetic.value(0)
        if any(
            arithmetic.binary(value, zero, "less")
            for value in (radius, remaining, numerical_guard)
        ):
            result["reason"] = "unsupported_point_error"
            return result
        for point in segments.reshape(-1, 2):
            work["prefix_points_checked"] += 1
            norm = zero
            for coordinate, anchor in zip(point, origin, strict=True):
                displacement = arithmetic.binary(
                    arithmetic.value(float(coordinate)), anchor, "sub"
                )
                norm = arithmetic.binary(norm, abs(displacement), "add")
            if arithmetic.binary(radius, norm, "less"):
                result["reason"] = "prefix_point_radius_not_enclosed"
                return result
        work["registration_entries"] = 1
        registration = _bound_synthetic_c1_history_registration(
            source_states,
            state_frames,
            acquisition_tick=acquisition_tick,
            reference_tick=reference_tick,
            point_radius_m=point_radius_m,
            assumptions=deepcopy(assumptions),
            max_history_ticks=max_history_ticks,
            source_max_integer_bits=source_max_integer_bits,
            max_integer_bits=max_integer_bits,
            synthetic_test_only=True,
        )
        if registration["fixture_registration_bound"] is not True:
            result["reason"] = registration["reason"]
            result["registration_work"] = deepcopy(registration["work"])
            return result
        total = arithmetic.binary(
            arithmetic.binary(numerical_guard, remaining, "add"),
            arithmetic.value(registration["upper_bounds"]["registered_point_m"]),
            "add",
        )
        combined_guard = arithmetic.outward(total, True)
        work["cell_entries"] = 1
        cells = _c1_exclude_path_cells(
            segments,
            path_points,
            tube_radius,
            current_body_clear=True,
            guard=combined_guard,
            max_cells=max_cells,
            max_depth=max_depth,
            radius_bands=radius_bands,
        )
    except ArithmeticError as error:
        result["reason"] = str(error)
        return result
    except (TypeError, ValueError, OverflowError):
        result["reason"] = "unsupported_registered_prefix_input"
        return result
    result.update(cells)
    result.update(
        combined_guard_m=combined_guard,
        registration_bound=deepcopy(registration),
        remaining_point_error_m=float(remaining),
    )
    if cells["fixture_enclosure_excluded"] is True:
        result.update(
            status="excluded_under_declared_registration_assumptions",
            reason="complete_point_error_eroded_prefix_cells_excluded",
        )
    return result


def _c1_exclude_path_cells(
    free_segments,
    path_points,
    tube_radius,
    *,
    current_body_clear=False,
    guard=0.0,
    max_cells=32768,
    max_depth=10,
    radius_bands=8,
    query_bound=None,
):
    """Check declared planar prefixes against a whole fixture path tube."""
    for value, lower, upper in (
        (max_cells, 0, 65536),
        (max_depth, 0, 12),
        (radius_bands, 1, 16),
    ):
        if type(value) is not int or not lower <= value <= upper:
            raise ValueError("path exclusion work limits require bounded integers")
    if (
        type(free_segments) is not np.ndarray
        or free_segments.ndim != 3
        or free_segments.shape[1:] != (2, 2)
        or len(free_segments) > 512
        or type(path_points) is not np.ndarray
        or path_points.ndim != 2
        or path_points.shape[1:] != (2,)
        or not 2 <= len(path_points) <= 129
    ):
        raise ValueError("path exclusion requires bounded planar arrays")
    free_segments = _c1_array(free_segments, free_segments.shape).astype(float)
    path_points = _c1_array(path_points, path_points.shape).astype(float)
    if any(type(value) not in (float, int) for value in (tube_radius, guard)):
        raise ValueError("path exclusion radii require finite numbers")
    tube_radius, guard = map(float, _c1_array([tube_radius, guard], (2,)))
    if tube_radius < 0.18 or guard < 0 or np.any(path_points[0] != 0):
        raise ValueError("path exclusion requires the declared current body")
    bound = float(np.linalg.norm(path_points, axis=1).max()) + tube_radius
    if query_bound is not None:
        if type(query_bound) not in (float, int):
            raise ValueError("path query bound requires a finite number")
        query_bound = float(_c1_array([query_bound], (1,))[0])
        if query_bound < bound:
            raise ValueError("path query bound must enclose the complete tube")
        bound = query_bound
    if not math.isfinite(bound):
        raise ValueError("path exclusion bound is not representable")
    result = {
        "fixture_enclosure_excluded": False,
        "reason": "current_body_clear_not_established",
        "cells_checked": 0,
    }
    if current_body_clear is not True:
        return result
    if not len(free_segments):
        result["reason"] = "no_low_height_free_segments"
        return result
    path_starts, path_steps = path_points[:-1], np.diff(path_points, axis=0)
    path_squared = np.sum(path_steps * path_steps, axis=1)
    starts = free_segments[:, 0]
    steps = free_segments[:, 1] - starts
    squared = np.sum(steps * steps, axis=1)
    for lower, upper in pairwise(np.linspace(0.05, 0.30, radius_bands + 1)):
        extent = bound + upper + guard
        pending = [(0.0, 0.0, extent, 0)]
        while pending:
            if result["cells_checked"] >= max_cells:
                result["reason"] = "cell_budget_exhausted"
                return result
            center_x, center_y, half, depth = pending.pop()
            result["cells_checked"] += 1
            center = np.array([center_x, center_y])
            norm, cell_radius = math.hypot(center_x, center_y), math.sqrt(2) * half
            if norm - cell_radius > extent + guard:
                continue
            path_relative = center - path_starts
            fractions = np.divide(
                np.sum(path_relative * path_steps, axis=1),
                path_squared,
                out=np.zeros_like(path_squared),
                where=path_squared > 0,
            )
            residual = path_relative - np.clip(fractions, 0, 1)[:, None] * path_steps
            separation = float(np.linalg.norm(residual, axis=1).min())
            if separation - cell_radius > tube_radius + upper + guard:
                continue
            if norm + cell_radius < 0.18 + lower - guard:
                continue
            relative = center - starts
            fractions = np.divide(
                np.sum(relative * steps, axis=1),
                squared,
                out=np.zeros_like(squared),
                where=squared > 0,
            )
            residual = relative - np.clip(fractions, 0, 1)[:, None] * steps
            separation = float(np.linalg.norm(residual, axis=1).min())
            if separation + cell_radius < lower - guard:
                continue
            if depth >= max_depth:
                result.update(
                    reason="unexcluded_center_cell",
                    unresolved_cell={
                        "center_m": center.tolist(),
                        "half_width_m": half,
                        "radius_interval_m": [float(lower), float(upper)],
                    },
                )
                return result
            child = half / 2
            pending.extend(
                (
                    center_x + horizontal * child,
                    center_y + vertical * child,
                    child,
                    depth + 1,
                )
                for horizontal in (-1, 1)
                for vertical in (-1, 1)
            )
    result.update(
        fixture_enclosure_excluded=True,
        reason="all_allowed_cylinder_centers_excluded_from_path_tube",
    )
    return result


def _c1_curved_centerline(speed, turn_rate, age, config, pieces, braking_turn_rate=0.0):
    position = np.zeros(2)
    points, yaw, error, deviation = [position.copy()], 0.0, 0.0, 0.0
    roundoff = 64 * np.finfo(float).eps * max(1.0, config.max_range)
    for duration, deceleration, angular_rate in (
        (age + config.dt, 0.0, turn_rate),
        (speed / config.acceleration, config.acceleration, braking_turn_rate),
    ):
        if duration == 0:
            continue
        seconds = duration / pieces
        for _ in range(pieces):
            midpoint_speed = max(0, speed - deceleration * seconds / 2)
            midpoint_yaw = yaw + angular_rate * seconds / 2
            position = position + seconds * midpoint_speed * np.array(
                [math.cos(midpoint_yaw), math.sin(midpoint_yaw)]
            )
            error += (
                2 * deceleration * abs(angular_rate) + speed * angular_rate**2
            ) * seconds**3 / 24 + roundoff
            deviation = max(
                deviation, (deceleration + speed * abs(angular_rate)) * seconds**2 / 8
            )
            points.append(position.copy())
            speed = max(0, speed - deceleration * seconds)
            yaw += angular_rate * seconds
    return np.asarray(points), error + deviation


def probe_synthetic_c1_enclosure(
    history,
    *,
    reference_tick,
    reference_pose_m_rad,
    speed,
    turn_rate=None,
    curved_segments=0,
    braking_turn_rate=None,
    current_body_clear=False,
    controlled_envelope=False,
    max_cells=32768,
    max_depth=10,
    radius_bands=8,
    config=None,
    synthetic_test_only=False,
):
    """Exclude a declared fixture disk, straight capsule or bounded curved tube."""
    if synthetic_test_only is not True:
        raise ValueError("C1 enclosure requires synthetic_test_only=True")
    config = _c1_config(config)
    speed = float(_c1_array([speed], (1,))[0])
    if not 0 <= speed <= config.max_speed:
        raise ValueError("C1 speed is outside the simulated motion limits")
    if turn_rate is not None:
        turn_rate = float(_c1_array([turn_rate], (1,))[0])
        if abs(turn_rate) > config.max_turn_rate:
            raise ValueError("C1 turn rate is outside the simulated motion limits")
    if type(curved_segments) is not int or not 0 <= curved_segments <= 128:
        raise ValueError("C1 curved segments require an integer from zero through 128")
    curved = curved_segments > 0
    if curved and turn_rate is None:
        raise ValueError("C1 curved enclosure requires a declared turn rate")
    if braking_turn_rate is not None:
        braking_turn_rate = float(_c1_array([braking_turn_rate], (1,))[0])
        if abs(braking_turn_rate) > config.max_turn_rate:
            raise ValueError(
                "C1 braking turn rate is outside the simulated motion limits"
            )
        if not curved:
            raise ValueError("C1 braking turn declaration requires the curved opt-in")
    if curved and braking_turn_rate is None:
        braking_turn_rate = 0.0
    for value, lower, upper in (
        (max_cells, 0, 65536),
        (max_depth, 0, 12),
        (radius_bands, 1, 16),
    ):
        if type(value) is not int or not lower <= value <= upper:
            raise ValueError("C1 enclosure work limits require bounded integers")
    result = {
        "schema": "micro-classifier/synthetic-c1-enclosure/1",
        "allowed_use": "controlled_synthetic_qualification_only",
        "training_approved": False,
        "real_input_qualified": False,
        "free_space_qualified": False,
        "numerically_certified": False,
        "status": "unknown",
        "reason": "current_body_clear_not_established",
        "fixture_enclosure_excluded": False,
        "cells_checked": 0,
        "radius_interval_m": [0.05, 0.30],
        "height_interval_m": [0.05, 1.0],
        "assumed_current_body_clear": current_body_clear is True,
        "assumed_controlled_envelope": controlled_envelope is True,
        "assumptions": {
            "static_floor_supported_cylinders": True,
            "axis_aligned_arena_walls_height_m": 1.0,
            "declared_exact_pose_and_first_return_model": True,
            "envelope_membership_independently_established": controlled_envelope
            is True,
            "declared_speed_and_reference_braking_model": True,
        },
    }
    if curved:
        result.update(
            schema="micro-classifier/synthetic-c1-curved-enclosure/1",
            assumed_turn_rate_rad_s=turn_rate,
            assumed_braking_turn_rate_rad_s=braking_turn_rate,
            assumed_segments_per_phase=curved_segments,
        )
        result["assumptions"]["declared_reaction_and_braking_turns"] = True
    elif turn_rate is not None:
        result.update(
            schema="micro-classifier/synthetic-c1-straight-enclosure/1",
            assumed_turn_rate_rad_s=turn_rate,
        )
        result["assumptions"]["straight_reaction_and_braking"] = turn_rate == 0
    inspection = inspect_synthetic_c1_history(
        history,
        reference_tick=reference_tick,
        reference_pose_m_rad=reference_pose_m_rad,
        config=config,
        synthetic_test_only=True,
    )
    if inspection["status"] != "registered_fixture":
        result["reason"] = inspection["reason"]
        return result
    if turn_rate is not None and turn_rate != 0 and not curved:
        result["reason"] = "unsupported_straight_maneuver"
        return result
    if current_body_clear is not True:
        return result
    if controlled_envelope is not True:
        result["reason"] = "controlled_envelope_not_established"
        return result
    if (
        config.radius,
        config.acceleration,
        config.max_speed,
        config.max_turn_rate,
        config.max_range,
        config.wall_height,
    ) != (0.18, 1, 0.6, 1.5, 4, 1):
        result["reason"] = "unsupported_dynamics_or_wall_profile"
        return result
    reference = _c1_array(reference_pose_m_rad, (3,)).astype(float)
    record = history[-1]
    pose = record["capture_poses_m_rad"][0]
    age = inspection["latest_age_ticks"] * config.dt
    yaw_delta = math.atan2(math.sin(pose[2]), math.cos(pose[2])) - math.atan2(
        math.sin(reference[2]), math.cos(reference[2])
    )
    yaw_delta = math.atan2(math.sin(yaw_delta), math.cos(yaw_delta))
    motion_guard = (
        256 * np.finfo(float).eps * max(1.0, *np.abs(reference), *np.abs(pose))
    )
    if (
        math.hypot(float(pose[0]) - reference[0], float(pose[1]) - reference[1])
        > config.max_speed * age + motion_guard
        or abs(yaw_delta) > config.max_turn_rate * age + motion_guard
    ):
        result["reason"] = "unsupported_capture_to_reference_motion"
        return result
    segments, guard = _c1_low_free_segments(record, inspection, reference, config)
    result["free_segment_count"] = len(segments)
    if not len(segments):
        result["reason"] = "no_low_height_free_segments"
        return result
    distance = speed * (age + config.dt) + speed * speed / (2 * config.acceleration)
    body_bound = config.radius + distance + guard
    straight = turn_rate is not None and not curved
    if curved:
        curve_points, curve_error = _c1_curved_centerline(
            speed, turn_rate, age, config, curved_segments, braking_turn_rate
        )
        tube_radius = config.radius + curve_error + guard
        body_bound += curve_error
        curve_starts, curve_steps = curve_points[:-1], np.diff(curve_points, axis=0)
        curve_squared = np.sum(curve_steps * curve_steps, axis=1)
        result.update(
            curved_centerline_body_m=curve_points.tolist(),
            centerline_error_allowance_m=curve_error,
            curved_tube_radius_m=tube_radius,
        )
    elif straight:
        result.update(
            straight_centerline_length_m=distance,
            capsule_radius_m=config.radius + guard,
        )
    else:
        result["sweep_enclosure_radius_m"] = body_bound
    cosine, sine = math.cos(reference[2]), math.sin(reference[2])
    world_relative = segments[..., :2].reshape(-1, 2) @ np.array(
        [[cosine, sine], [-sine, cosine]]
    )
    wall_tip = distance * np.array([cosine, sine]) if straight else np.zeros(2)
    wall_radius = config.radius + guard if straight else body_bound
    wall_min = np.minimum(0, wall_tip) - wall_radius - guard
    wall_max = np.maximum(0, wall_tip) + wall_radius + guard
    if curved:
        world_curve = curve_points @ np.array([[cosine, sine], [-sine, cosine]])
        wall_min = world_curve.min(axis=0) - tube_radius - guard
        wall_max = world_curve.max(axis=0) + tube_radius + guard
    if not (
        np.all(world_relative.min(axis=0) < wall_min)
        and np.all(world_relative.max(axis=0) > wall_max)
    ):
        result["reason"] = "axis_aligned_wall_support_incomplete"
        return result
    starts = segments[:, 0, :2]
    steps = segments[:, 1, :2] - starts
    squared = np.sum(steps * steps, axis=1)
    radii = np.linspace(0.05, 0.30, radius_bands + 1)
    for lower, upper in pairwise(radii):
        extent = body_bound + upper + guard
        pending = [(0.0, 0.0, extent, 0)]
        while pending:
            if result["cells_checked"] >= max_cells:
                result["reason"] = "cell_budget_exhausted"
                return result
            center_x, center_y, half, depth = pending.pop()
            result["cells_checked"] += 1
            center = np.array([center_x, center_y])
            norm, cell_radius = math.hypot(center_x, center_y), math.sqrt(2) * half
            if norm - cell_radius > extent + guard:
                continue
            if curved:
                curve_relative = center - curve_starts
                curve_fractions = np.divide(
                    np.sum(curve_relative * curve_steps, axis=1),
                    curve_squared,
                    out=np.zeros_like(curve_squared),
                    where=curve_squared > 0,
                )
                curve_residual = (
                    curve_relative
                    - np.clip(curve_fractions, 0, 1)[:, None] * curve_steps
                )
                curve_separation = float(np.linalg.norm(curve_residual, axis=1).min())
                if curve_separation - cell_radius > tube_radius + upper + guard:
                    continue
            if (
                straight
                and math.hypot(center_x - min(max(center_x, 0), distance), center_y)
                - cell_radius
                > config.radius + upper + 2 * guard
            ):
                continue
            if norm + cell_radius < config.radius + lower - guard:
                continue
            relative = center - starts
            fractions = np.divide(
                np.sum(relative * steps, axis=1),
                squared,
                out=np.zeros_like(squared),
                where=squared > 0,
            )
            residual = relative - np.clip(fractions, 0, 1)[:, None] * steps
            separation = float(np.linalg.norm(residual, axis=1).min())
            if separation + cell_radius < lower - guard:
                continue
            if depth >= max_depth:
                result.update(
                    reason="unexcluded_center_cell",
                    unresolved_cell={
                        "center_m": center.tolist(),
                        "half_width_m": half,
                        "radius_interval_m": [float(lower), float(upper)],
                    },
                )
                return result
            child = half / 2
            pending.extend(
                (
                    center_x + horizontal * child,
                    center_y + vertical * child,
                    child,
                    depth + 1,
                )
                for horizontal in (-1, 1)
                for vertical in (-1, 1)
            )
    result.update(
        status="excluded_under_fixture_assumptions",
        reason="all_allowed_cylinder_centers_and_axis_aligned_walls_excluded_from_curved_tube"
        if curved
        else "all_allowed_cylinder_centers_and_axis_aligned_walls_excluded_from_straight_capsule"
        if straight
        else "all_allowed_cylinder_centers_and_axis_aligned_walls_excluded",
        fixture_enclosure_excluded=True,
    )
    return result


def probe_synthetic_c1_occupied_witness(
    history,
    *,
    reference_tick,
    reference_pose_m_rad,
    speed,
    turn_rate,
    braking_turn_rate=0.0,
    curved_segments=16,
    controlled_envelope=False,
    config=None,
    synthetic_test_only=False,
):
    """Probe occupied returns inside a declared maneuver, never its outer tube."""
    if synthetic_test_only is not True:
        raise ValueError("C1 witness requires synthetic_test_only=True")
    config = _c1_config(config)
    speed, turn_rate, braking_turn_rate = map(
        float, _c1_array([speed, turn_rate, braking_turn_rate], (3,))
    )
    if not (
        0 <= speed <= config.max_speed
        and abs(turn_rate) <= config.max_turn_rate
        and abs(braking_turn_rate) <= config.max_turn_rate
    ):
        raise ValueError("C1 witness motion exceeds the simulated limits")
    if type(curved_segments) is not int or not 1 <= curved_segments <= 128:
        raise ValueError("C1 witness requires one through 128 segments per phase")
    result = {
        "schema": "micro-classifier/synthetic-c1-occupied-witness/1",
        "allowed_use": "controlled_synthetic_qualification_only",
        "training_approved": False,
        "real_input_qualified": False,
        "free_space_qualified": False,
        "numerically_certified": False,
        "status": "unknown",
        "reason": "controlled_envelope_not_established",
        "fixture_blocked_witness": False,
        "fixture_current_body_witness": False,
        "witness_indices": [],
        "assumed_controlled_envelope": controlled_envelope is True,
        "assumed_turn_rate_rad_s": turn_rate,
        "assumed_braking_turn_rate_rad_s": braking_turn_rate,
        "assumed_segments_per_phase": curved_segments,
        "assumptions": {
            "declared_exact_pose_and_first_return_model": True,
            "static_floor_supported_cylinders_and_axis_aligned_walls": True,
            "range_rounding_and_transform_allowances_only": True,
            "declared_reaction_and_braking_turns": True,
        },
    }
    inspection = inspect_synthetic_c1_history(
        history,
        reference_tick=reference_tick,
        reference_pose_m_rad=reference_pose_m_rad,
        config=config,
        synthetic_test_only=True,
    )
    if inspection["status"] != "registered_fixture":
        result["reason"] = inspection["reason"]
        return result
    if controlled_envelope is not True:
        return result
    if (
        config.radius,
        config.acceleration,
        config.max_speed,
        config.max_turn_rate,
        config.max_range,
        config.wall_height,
    ) != (0.18, 1, 0.6, 1.5, 4, 1):
        result["reason"] = "unsupported_dynamics_or_wall_profile"
        return result
    reference = _c1_array(reference_pose_m_rad, (3,)).astype(float)
    record = history[-1]
    pose = record["capture_poses_m_rad"][0]
    age = inspection["latest_age_ticks"] * config.dt
    guard = (
        256
        * np.finfo(float).eps
        * max(1.0, config.max_range, *np.abs(reference), *np.abs(pose))
    )
    yaw_delta = math.atan2(math.sin(pose[2]), math.cos(pose[2])) - math.atan2(
        math.sin(reference[2]), math.cos(reference[2])
    )
    yaw_delta = math.atan2(math.sin(yaw_delta), math.cos(yaw_delta))
    if (
        math.hypot(float(pose[0]) - reference[0], float(pose[1]) - reference[1])
        > config.max_speed * age + guard
        or abs(yaw_delta) > config.max_turn_rate * age + guard
    ):
        result["reason"] = "unsupported_capture_to_reference_motion"
        return result
    if guard >= config.radius:
        result["reason"] = "unsupported_numerical_scale"
        return result
    ranges = record["tof_m"]
    lower = np.nextafter(ranges, np.float32(0)).astype(float)
    upper = np.nextafter(ranges, np.float32(np.inf)).astype(float)
    errors = np.maximum(ranges.astype(float) - lower, upper - ranges) + guard
    points = inspection["points_body_m"]
    occupied = (
        inspection["point_valid"]
        & (points[..., 2] - errors > guard)
        & (points[..., 2] + errors < config.wall_height - guard)
    )
    result["occupied_return_count"] = int(np.count_nonzero(occupied))
    if not np.any(occupied):
        result["reason"] = "no_qualified_occupied_returns"
        return result
    centerline, curve_error = _c1_curved_centerline(
        speed, turn_rate, age, config, curved_segments, braking_turn_rate
    )
    differences = points[occupied][:, None, :2] - centerline[None, :, :]
    distances = np.hypot(differences[..., 0], differences[..., 1])
    support_at_vertices = (
        distances + errors[occupied, None] + curve_error + guard < config.radius
    )
    supported = np.any(support_at_vertices, axis=1)
    result.update(
        reason="no_strict_inner_footprint_witness",
        centerline_error_allowance_m=curve_error,
        occupied_point_error_upper_m=float(errors[occupied].max()),
        fixture_current_body_witness=bool(np.any(support_at_vertices[:, 0])),
        witness_indices=np.argwhere(occupied)[supported].tolist(),
    )
    if np.any(supported):
        result.update(
            status="blocked_under_fixture_assumptions",
            reason="occupied_return_enclosure_inside_maneuver_body",
            fixture_blocked_witness=True,
        )
    return result


def probe_synthetic_c1_questions(
    history,
    *,
    reference_tick,
    reference_pose_m_rad,
    speed,
    turn_rate,
    fixture_goal_m,
    current_body_clear=False,
    controlled_envelope=False,
    curved_segments=16,
    max_cells=32768,
    max_depth=10,
    radius_bands=8,
    config=None,
    synthetic_test_only=False,
):
    """Combine conditional C1 evidence into fixture-only candidate values."""
    if synthetic_test_only is not True:
        raise ValueError("C1 question feasibility requires synthetic_test_only=True")
    config = _c1_config(config)
    speed, turn_rate = map(float, _c1_array([speed, turn_rate], (2,)))
    goal = _c1_array(fixture_goal_m, (2,)).astype(float)
    reference = _c1_array(reference_pose_m_rad, (3,)).astype(float)
    if not 0 <= speed <= config.max_speed or abs(turn_rate) > config.max_turn_rate:
        raise ValueError("C1 question motion exceeds the simulated limits")
    for value, lower, upper in (
        (curved_segments, 1, 128),
        (max_cells, 0, 65536),
        (max_depth, 0, 12),
        (radius_bands, 1, 16),
    ):
        if type(value) is not int or not lower <= value <= upper:
            raise ValueError("C1 question work controls require bounded integers")
    result = {
        "schema": "micro-classifier/synthetic-c1-question-feasibility/1",
        "allowed_use": "controlled_synthetic_qualification_only",
        "training_approved": False,
        "real_input_qualified": False,
        "free_space_qualified": False,
        "numerically_certified": False,
        "status": "unknown",
        "reason": "current_body_clear_not_established",
        "candidate_values": {
            "path_blocked": None,
            "clear_sector": None,
            "speed_tier": None,
        },
        "fixture_goal_m": goal.tolist(),
        "queries": {},
        "unique_motion_queries": 0,
    }
    inspection = inspect_synthetic_c1_history(
        history,
        reference_tick=reference_tick,
        reference_pose_m_rad=reference,
        config=config,
        synthetic_test_only=True,
    )
    if inspection["status"] != "registered_fixture":
        result["reason"] = inspection["reason"]
        return result
    if current_body_clear is not True:
        return result
    if controlled_envelope is not True:
        result["reason"] = "controlled_envelope_not_established"
        return result
    cache = {}
    motions = [
        ("centre", speed, 0.0),
        ("left", speed, config.max_turn_rate),
        ("right", speed, -config.max_turn_rate),
        *[
            (f"tier_{tier}", max(speed, config.max_speed * tier / 3), 0.0)
            for tier in (1, 2, 3)
        ],
    ]
    for name, query_speed, braking_turn in motions:
        key = query_speed, braking_turn
        if key not in cache:
            settings = {
                "reference_tick": reference_tick,
                "reference_pose_m_rad": reference,
                "speed": query_speed,
                "turn_rate": turn_rate,
                "braking_turn_rate": braking_turn,
                "curved_segments": curved_segments,
                "controlled_envelope": True,
                "config": config,
                "synthetic_test_only": True,
            }
            exclusion = probe_synthetic_c1_enclosure(
                history,
                current_body_clear=True,
                max_cells=max_cells,
                max_depth=max_depth,
                radius_bands=radius_bands,
                **settings,
            )
            witness = probe_synthetic_c1_occupied_witness(history, **settings)
            clear = exclusion["fixture_enclosure_excluded"] is True
            blocked = witness["fixture_blocked_witness"] is True
            contradictory = (clear and blocked) or witness[
                "fixture_current_body_witness"
            ]
            cache[key] = {
                "status": "contradiction"
                if contradictory
                else "clear"
                if clear
                else "blocked"
                if blocked
                else "unknown",
                "speed_m_s": query_speed,
                "braking_turn_rate_rad_s": braking_turn,
                "exclusion": exclusion,
                "witness": witness,
            }
        result["queries"][name] = deepcopy(cache[key])
    result["unique_motion_queries"] = len(cache)
    states = {name: row["status"] for name, row in result["queries"].items()}
    if "contradiction" in states.values():
        result.update(
            status="inconsistent_fixture_evidence",
            reason="contradictory_fixture_evidence",
        )
        return result
    candidates = result["candidate_values"]
    candidates["path_blocked"] = {"clear": "false", "blocked": "true"}.get(
        states["centre"]
    )
    sector_names = ("centre", "left", "right")
    if speed > 0 and all(states[name] != "unknown" for name in sector_names):
        clear_names = [name for name in sector_names if states[name] == "clear"]
        if not clear_names:
            candidates["clear_sector"] = "none"
        else:
            yaw = math.atan2(math.sin(reference[2]), math.cos(reference[2]))
            cosine, sine = math.cos(yaw), math.sin(yaw)
            with np.errstate(over="ignore", invalid="ignore"):
                relative_goal = (goal - reference[:2]) @ np.array(
                    [[cosine, -sine], [sine, cosine]]
                )
            if np.all(np.isfinite(relative_goal)):
                distances, errors = {}, {}
                guard = (
                    256
                    * np.finfo(float).eps
                    * max(1.0, *np.abs(goal), *np.abs(reference))
                )
                for name in clear_names:
                    row = result["queries"][name]
                    points, allowance = _c1_curved_centerline(
                        speed,
                        turn_rate,
                        inspection["latest_age_ticks"] * config.dt,
                        config,
                        curved_segments,
                        row["braking_turn_rate_rad_s"],
                    )
                    distances[name] = math.dist(points[-1], relative_goal)
                    errors[name] = allowance + guard
                if all(math.isfinite(value) for value in distances.values()):
                    best = min(clear_names, key=distances.__getitem__)
                    upper = distances[best] + errors[best]
                    contenders = [
                        name
                        for name in clear_names
                        if distances[name] - errors[name] <= upper
                    ]
                    if len(contenders) == 1:
                        candidates["clear_sector"] = best
                    elif (
                        set(contenders) == {"left", "right"}
                        and turn_rate == 0
                        and relative_goal[1] == 0
                    ):
                        candidates["clear_sector"] = "left"
    tier_names = ("tier_1", "tier_2", "tier_3")
    if all(states[name] != "unknown" for name in tier_names):
        candidates["speed_tier"] = str(
            max(
                (tier for tier in (1, 2, 3) if states[f"tier_{tier}"] == "clear"),
                default=0,
            )
        )
    count = sum(value is not None for value in candidates.values())
    result.update(
        status="resolved_under_fixture_assumptions"
        if count == 3
        else "partial_fixture_evidence"
        if count
        else "unknown",
        reason="conditional_candidate_values_only"
        if count
        else "unresolved_fixture_evidence",
    )
    return result


def _reference_synthetic_c1_motion(motion, *, synthetic_test_only=False):
    """Enclose fixture mathematics, not library errors or source authority."""
    from fractions import Fraction

    if synthetic_test_only is not True:
        raise ValueError("C1 reference requires synthetic_test_only=True")
    result = {
        "allowed_use": "private_synthetic_motion_reference_only",
        "training_approved": False,
        "real_input_qualified": False,
        "free_space_qualified": False,
        "numerically_certified": False,
        "status": "unresolved_mathematical_reference",
        "reason": "unsupported_motion_record",
        "motion_status": "unresolved_motion_evidence",
        "clocks": {},
    }
    bit_limit = 65536
    order = 32

    def bounded(value):
        if (
            max(value.numerator.bit_length(), value.denominator.bit_length())
            > bit_limit
        ):
            raise ArithmeticError("rational_work_limit")
        return value

    def scalar(value):
        if type(value) not in (int, float):
            raise ValueError("unsupported_reference_scalar")
        if type(value) is int and value.bit_length() > bit_limit:
            raise ArithmeticError("rational_work_limit")
        if type(value) is float and not math.isfinite(value):
            raise ValueError("unsupported_reference_scalar")
        return bounded(Fraction(value))

    def vector(value, length):
        if type(value) not in (list, tuple) or len(value) != length:
            raise ValueError("unsupported_reference_vector")
        return tuple(scalar(item) for item in value)

    def add(left, right):
        if (
            max(
                left.numerator.bit_length() + right.denominator.bit_length(),
                right.numerator.bit_length() + left.denominator.bit_length(),
            )
            + 1
            > bit_limit
            or left.denominator.bit_length() + right.denominator.bit_length()
            > bit_limit
        ):
            raise ArithmeticError("rational_work_limit")
        return bounded(left + right)

    def multiply(left, right):
        if (
            left.numerator.bit_length() + right.numerator.bit_length() > bit_limit
            or left.denominator.bit_length() + right.denominator.bit_length()
            > bit_limit
        ):
            raise ArithmeticError("rational_work_limit")
        return bounded(left * right)

    def powers(value, count):
        values = [Fraction(1)]
        for _ in range(count - 1):
            values.append(multiply(values[-1], value))
        return values

    def interval_add(left, right):
        return add(left[0], right[0]), add(left[1], right[1])

    def interval_scale(interval, factor):
        values = [multiply(endpoint, factor) for endpoint in interval]
        return min(values), max(values)

    def trig(heading, sine):
        values = powers(heading, order + 1)
        total = Fraction(0)
        for degree in range(1 if sine else 0, order, 2):
            coefficient = Fraction((-1) ** (degree // 2), math.factorial(degree))
            total = add(total, multiply(coefficient, values[degree]))
        tail = multiply(abs(values[order]), Fraction(1, math.factorial(order)))
        return add(total, -tail), add(total, tail)

    def pi_interval():
        intervals = []
        for denominator in (5, 239):
            values = powers(Fraction(1, denominator), 2 * order + 2)
            partial = Fraction(0)
            for index in range(order):
                partial = add(
                    partial,
                    multiply(
                        values[2 * index + 1], Fraction((-1) ** index, 2 * index + 1)
                    ),
                )
            tail = multiply(values[2 * order + 1], Fraction(1, 2 * order + 1))
            intervals.append((partial, add(partial, tail)))
        return interval_add(
            interval_scale(intervals[0], Fraction(16)),
            interval_scale(intervals[1], Fraction(-4)),
        )

    def circular(heading, pi_bounds):
        if -pi_bounds[0] < heading < pi_bounds[0]:
            return ((0, (heading, heading)),)
        turns = 1 if heading >= 0 else -1
        shifted = interval_add(
            (heading, heading), interval_scale(pi_bounds, Fraction(-2 * turns))
        )
        if abs(heading) > pi_bounds[1]:
            return ((turns, shifted),)
        return ((0, (heading, heading)), (turns, shifted))

    try:
        if type(motion) is not dict or set(motion) != {
            "model",
            "clock_epoch",
            "seed_tick",
            "seed_pose_m_rad",
            "speed_m_s",
            "turn_rate_rad_s",
            "tick_period_us",
            "tick_period_s",
            "fixture_goal_m",
            "events",
        }:
            return result
        if (
            motion["model"] != "constant_twist_interval_ending_v1"
            or type(motion["clock_epoch"]) is not str
            or not motion["clock_epoch"]
            or type(motion["seed_tick"]) is not int
            or not 0 <= motion["seed_tick"] <= 85899
            or type(motion["tick_period_us"]) is not int
            or motion["tick_period_us"] != 50000
            or type(motion["tick_period_s"]) is not float
            or motion["tick_period_s"] != 0.05
        ):
            return result
        seed = vector(motion["seed_pose_m_rad"], 3)
        speed, turn = vector([motion["speed_m_s"], motion["turn_rate_rad_s"]], 2)
        goal = vector(motion["fixture_goal_m"], 2)
        if (
            not 0 <= speed <= Fraction(0.6)
            or abs(turn) > Fraction(3, 2)
            or abs(seed[2]) > Fraction(math.pi)
        ):
            return result
        events = motion["events"]
        if type(events) is not list or not 1 <= len(events) <= 8:
            return result
        stored = []
        for offset, event in enumerate(events):
            if (
                type(event) is not dict
                or set(event) != {"tick", "pose_m_rad", "fixture_state", "host_frame"}
                or type(event["tick"]) is not int
                or event["tick"] != motion["seed_tick"] + offset
                or event["tick"] > 85899
            ):
                return result
            pose = vector(event["pose_m_rad"], 3)
            if abs(pose[2]) > Fraction(math.pi):
                return result
            stored.append(pose)
        pi_bounds = pi_interval()
        heading_powers = powers(seed[2], order)
        turn_powers = powers(turn, order)
        clocks = {}
        for name, period in (
            ("nominal_us", Fraction(1, 20)),
            ("binary64_step", Fraction(0.05)),
        ):
            references = []
            for offset, pose in enumerate(stored):
                elapsed = multiply(Fraction(offset), period)
                heading = add(seed[2], multiply(turn, elapsed))
                phase = max(abs(seed[2]), abs(heading))
                if phase > 4:
                    raise ValueError("unsupported_reference_phase")
                time_powers = powers(elapsed, order + 1)
                totals = [Fraction(0), Fraction(0)]
                for degree in range(order):
                    integral = Fraction(0)
                    for exponent in range(degree + 1):
                        term = multiply(
                            heading_powers[degree - exponent], turn_powers[exponent]
                        )
                        term = multiply(term, time_powers[exponent + 1])
                        integral = add(
                            integral,
                            multiply(
                                term,
                                Fraction(math.comb(degree, exponent), exponent + 1),
                            ),
                        )
                    coefficient = Fraction(
                        (-1) ** (degree // 2), math.factorial(degree)
                    )
                    totals[degree % 2] = add(
                        totals[degree % 2], multiply(coefficient, integral)
                    )
                phase_power = powers(phase, order + 1)[order]
                tail = multiply(
                    multiply(speed, elapsed),
                    multiply(phase_power, Fraction(1, math.factorial(order))),
                )
                positions = []
                for axis, total in enumerate(totals):
                    centre = add(seed[axis], multiply(speed, total))
                    positions.append((add(centre, -tail), add(centre, tail)))
                cosine, sine = trig(pose[2], False), trig(pose[2], True)
                delta = [add(goal[axis], -pose[axis]) for axis in (0, 1)]
                body_goal = (
                    interval_add(
                        interval_scale(cosine, delta[0]), interval_scale(sine, delta[1])
                    ),
                    interval_add(
                        interval_scale(cosine, delta[1]),
                        interval_scale(sine, -delta[0]),
                    ),
                )
                clock_delta = multiply(
                    Fraction(offset), abs(add(Fraction(0.05), -Fraction(1, 20)))
                )
                references.append(
                    {
                        "tick": motion["seed_tick"] + offset,
                        "elapsed_s": elapsed,
                        "position_m": tuple(positions),
                        "unwrapped_heading_rad": (heading, heading),
                        "circular_heading_rad": circular(heading, pi_bounds),
                        "body_goal_m": body_goal,
                        "clock_discrepancy_m": multiply(speed, clock_delta),
                        "clock_discrepancy_rad": multiply(abs(turn), clock_delta),
                    }
                )
            clocks[name] = references
        result.update(
            status="enclosed_mathematical_reference",
            reason="rational_integral_with_analytic_tail_only",
            clocks=clocks,
            pi_rad=pi_bounds,
        )
    except ArithmeticError:
        result["reason"] = "rational_work_limit"
    except (ValueError, TypeError, KeyError, OverflowError):
        return result
    return result


def _audit_synthetic_controlled_candidate(
    bundle, *, expected_anchor=None, synthetic_test_only=False
):
    """Check bounded private records without inheriting producer verdicts."""
    from dataclasses import fields

    from interface.protocol import MAX_FRAME_SIZE, State, decode_state, encode_state
    from sim.rover import Scenario

    if synthetic_test_only is not True:
        raise ValueError("controlled audit requires synthetic_test_only=True")
    flags = (
        "training_approved",
        "real_input_qualified",
        "free_space_qualified",
        "numerically_certified",
        "producer_parity_qualified",
    )
    result = {
        "allowed_use": "private_synthetic_independent_candidate_audit_only",
        **{flag: False for flag in flags},
        "ownership_status": "unresolved_anchor",
        "content_status": "unresolved_evidence",
        **{
            name: "unresolved_evidence"
            for name in (
                "schema_status",
                "trace_status",
                "event_status",
                "codec_status",
                "capture_status",
                "copied_input_status",
            )
        },
        "reason": "unchecked_relations",
        "events_checked": 0,
        "trace_cells_checked": 0,
        "captures_checked": 0,
        "frames_checked": 0,
        "copied_records_checked": 0,
        "host_changed_fields": (),
        "unverified_relations": (
            "native_motion",
            "native_goal",
            "relative_transforms",
            "ray_returns",
            "pending_captures",
            "source_authority",
            "native_work_trusted_base",
        ),
    }

    def require(condition, reason):
        if not condition:
            raise ValueError(reason)

    def preflight(value, depth=0):
        require(depth <= 10, "unsupported_record_depth")
        kind = type(value)
        if kind is State:
            for field in fields(State):
                preflight(getattr(value, field.name), depth + 1)
        elif kind is dict:
            require(len(value) <= len(fields(Config)), "unsupported_mapping_size")
            require(
                all(type(key) is str and len(key) <= 64 for key in value),
                "unsupported_keys",
            )
            for item in value.values():
                preflight(item, depth + 1)
        elif kind in (tuple, list):
            require(len(value) <= 11, "unsupported_sequence_size")
            for item in value:
                preflight(item, depth + 1)
        elif kind is np.ndarray:
            require(value.shape in ((8,), (8, 3), (8, 8, 8)), "unsupported_array_shape")
            require(
                value.dtype.str in ("<u4", "<f8", "<f4", "|b1"),
                "unsupported_array_dtype",
            )
            require(
                value.flags.c_contiguous and np.all(np.isfinite(value)),
                "unsupported_array_storage",
            )
        elif kind is int:
            require(value.bit_length() <= 4096, "unsupported_integer_size")
        elif kind in (float, np.float64):
            require(math.isfinite(value), "unsupported_nonfinite_scalar")
        elif kind is str:
            require(len(value) <= 64, "unsupported_string_size")
        elif kind is bytes:
            require(len(value) <= MAX_FRAME_SIZE, "unsupported_frame_size")
        else:
            require(value is None or kind is bool, "unsupported_record_type")

    def keys(value, expected):
        require(
            type(value) is dict and set(value) == set(expected),
            "record_schema_mismatch",
        )

    def same(left, right):
        return _c1_source_binding_digest(left) == _c1_source_binding_digest(right)

    def word_value(word):
        require(type(word) is int and 0 <= word < 1 << 64, "finite_word_type_mismatch")
        magnitude = word & ((1 << 63) - 1)
        exponent, fraction = divmod(magnitude, 1 << 52)
        require(exponent < 2047, "nonfinite_word")
        coefficient = fraction + ((1 << 52) if exponent else 0)
        shift = (exponent if exponent else 1) - 1075
        value = Fraction(coefficient * (1 << max(shift, 0)), 1 << max(-shift, 0))
        return -value if word >> 63 else value

    def rational(pair):
        require(type(pair) is tuple and len(pair) == 2, "ratio_shape_mismatch")
        numerator, denominator = pair
        require(
            type(numerator) is int and type(denominator) is int and denominator > 0,
            "ratio_type_mismatch",
        )
        require(
            max(numerator.bit_length(), denominator.bit_length()) <= 4096,
            "unsupported_ratio_size",
        )
        require(math.gcd(numerator, denominator) == 1, "noncanonical_ratio")
        return Fraction(numerator, denominator)

    def rounded(exact, zero_sign, word):
        value = word_value(word)
        sign = int(exact < 0) if exact else zero_sign
        require(word >> 63 == sign, "rounded_sign_mismatch")
        magnitude = word & ((1 << 63) - 1)
        absolute = abs(exact)
        center = abs(value)
        lower = abs(word_value(magnitude - 1)) if magnitude else Fraction(0)
        upper = (
            word_value(magnitude + 1)
            if magnitude < 0x7FEFFFFFFFFFFFFF
            else Fraction(1 << 1024)
        )
        low_midpoint, high_midpoint = (lower + center) / 2, (center + upper) / 2
        require(low_midpoint <= absolute <= high_midpoint, "rounded_neighbor_mismatch")
        require(
            not magnitude & 1 or absolute not in (low_midpoint, high_midpoint),
            "rounded_tie_mismatch",
        )
        return value

    def verify_trace(trace, heading_word):
        keys(
            trace,
            (
                "allowed_use",
                "supported",
                "reason",
                *flags,
                "rows",
                "inputs",
                "rounded_cells",
                "residue_correction",
                "intermediate_words",
            ),
        )
        require(
            trace["allowed_use"] == "isolated_synthetic_arithmetic_trace_only"
            and trace["supported"] is True
            and trace["reason"] == "literal_word_trace_only",
            "trace_declaration_mismatch",
        )
        require(all(trace[flag] is False for flag in flags), "trace_flag_mismatch")
        inputs = (
            heading_word,
            candidate["turn_word"],
            candidate["duration_word"],
            candidate["pi_word"],
            candidate["two_word"],
        )
        require(same(trace["inputs"], inputs), "trace_input_mismatch")
        rows = trace["rows"]
        require(type(rows) is tuple and len(rows) == 4, "trace_rows_mismatch")
        for row, name in zip(rows, ("P1", "P2", "P3", "P7"), strict=True):
            keys(row, ("row", "cells"))
            require(
                row["row"] == name and type(row["cells"]) is tuple,
                "trace_row_order_mismatch",
            )
        require(
            tuple(len(row["cells"]) for row in rows) in ((1, 2, 2, 5), (1, 2, 2, 6)),
            "trace_cell_count_mismatch",
        )
        cells = tuple(entry for row in rows for entry in row["cells"])
        position = 0

        def check(name, operation, left, right):
            nonlocal position
            entry = cells[position]
            position += 1
            keys(
                entry,
                (
                    "name",
                    "operation",
                    "operands",
                    "exact_ratio",
                    "zero_sign",
                    "word",
                    "rounding_error_ratio",
                    *(
                        ("truncated_quotient",)
                        if operation == "truncated_residue"
                        else ()
                    ),
                ),
            )
            require(
                entry["name"] == name and entry["operation"] == operation,
                "trace_cell_order_mismatch",
            )
            require(same(entry["operands"], (left, right)), "trace_operand_mismatch")
            left_value, right_value = word_value(left), word_value(right)
            left_sign, right_sign = left >> 63, right >> 63
            if operation in ("add", "sub"):
                if operation == "sub":
                    right_value, right_sign = -right_value, right_sign ^ 1
                exact = left_value + right_value
                zero_sign = int(
                    not left_value and not right_value and left_sign and right_sign
                )
            elif operation == "mul":
                exact, zero_sign = left_value * right_value, left_sign ^ right_sign
            elif operation == "div":
                require(bool(right_value), "zero_divisor")
                exact, zero_sign = left_value / right_value, left_sign ^ right_sign
            else:
                require(bool(right_value), "zero_period")
                quotient = left_value / right_value
                integer = abs(quotient.numerator) // quotient.denominator
                integer = -integer if quotient < 0 else integer
                require(
                    type(entry["truncated_quotient"]) is int
                    and entry["truncated_quotient"] == integer,
                    "truncated_quotient_mismatch",
                )
                exact, zero_sign = left_value - integer * right_value, left_sign
            require(
                type(entry["zero_sign"]) is int and entry["zero_sign"] == zero_sign,
                "zero_tag_mismatch",
            )
            require(rational(entry["exact_ratio"]) == exact, "exact_ratio_mismatch")
            value = rounded(exact, zero_sign, entry["word"])
            require(
                rational(entry["rounding_error_ratio"]) == value - exact,
                "rounding_error_mismatch",
            )
            result["trace_cells_checked"] += 1
            return entry["word"]

        heading, turn, duration, pi_word, two = inputs
        angle = check("a", "mul", turn, duration)
        half = check("half", "div", angle, two)
        midpoint = check("m", "add", heading, half)
        period_q = check("b_q", "mul", two, pi_word)
        argument = check("q", "div", angle, period_q)
        first = check("x_1", "add", heading, angle)
        shifted = check("x", "add", first, pi_word)
        period_r = check("b_r", "mul", two, pi_word)
        residue = check("z", "truncated_residue", shifted, period_r)
        if not word_value(residue):
            correction, corrected = "divisor_signed_zero", period_r & (1 << 63)
        elif word_value(residue) < 0:
            correction, corrected = (
                "negative_nonzero",
                check("u", "add", residue, period_r),
            )
        else:
            correction, corrected = "none", residue
        final = check("r_next", "sub", corrected, pi_word)
        require(position == len(cells), "extra_trace_cell")
        require(
            type(trace["rounded_cells"]) is int and trace["rounded_cells"] == position,
            "rounded_count_mismatch",
        )
        require(trace["residue_correction"] == correction, "correction_kind_mismatch")
        require(
            same(
                trace["intermediate_words"],
                (
                    angle,
                    half,
                    midpoint,
                    period_q,
                    argument,
                    first,
                    shifted,
                    period_r,
                    residue,
                    corrected,
                    final,
                ),
            ),
            "intermediate_words_mismatch",
        )
        return final

    def sequence(value, length, kind=tuple):
        require(
            type(value) is kind and len(value) == length, "sequence_schema_mismatch"
        )

    def numeric(value):
        require(
            type(value) in (int, float) and math.isfinite(value), "scalar_type_mismatch"
        )

    def state_schema(value):
        keys(value, (field.name for field in fields(State)))
        for name in ("sequence", "timestamp_us", "validity", "task_id", "faults"):
            require(type(value[name]) is int, "state_integer_type_mismatch")
        for name, length in (
            ("ages_us", 5),
            ("velocity_m_s", 3),
            ("angular_velocity_rad_s", 3),
            ("goal_m", 3),
        ):
            sequence(value[name], length)
            require(
                all(
                    type(item) is (int if name == "ages_us" else float)
                    for item in value[name]
                ),
                "state_vector_type_mismatch",
            )
        require(type(value["battery_fraction"]) is float, "state_scalar_type_mismatch")

    def config_schema(value):
        keys(value, (field.name for field in fields(Config)))
        for name, item in value.items():
            if name in (
                "latency_ticks",
                "history_ticks",
                "max_ticks",
                "odometry_latency_ticks",
            ):
                require(type(item) is int, "config_integer_type_mismatch")
            else:
                numeric(item)

    def identity(value):
        require(
            type(value) is str
            and len(value) == 64
            and all(character in "0123456789abcdef" for character in value),
            "identity_type_mismatch",
        )

    def file_schema(value):
        keys(value, ("sim/diagnostics.py", "sim/rover.py", "interface/protocol.py"))
        for item in value.values():
            identity(item)

    def array_schema(value, shape, dtype):
        require(
            type(value) is np.ndarray and value.shape == shape,
            "unsupported_array_shape",
        )
        require(value.dtype.str == dtype, "unsupported_array_dtype")
        require(value.flags.c_contiguous, "unsupported_array_storage")

    def records_schema(source, candidate):
        keys(
            source,
            (
                "allowed_use",
                *flags[:4],
                "relative_input",
                "fixture_state",
                "private_source",
                "source_files",
                "binding_sha256",
            ),
        )
        require(
            source["allowed_use"] == "private_synthetic_source_record_only"
            and all(source[flag] is False for flag in flags[:4]),
            "source_declaration_mismatch",
        )
        require(type(source["fixture_state"]) is State, "source_state_type_mismatch")
        state_schema(
            {
                field.name: getattr(source["fixture_state"], field.name)
                for field in fields(State)
            }
        )
        file_schema(source["source_files"])
        file_schema(candidate["source_files"])
        identity(source["binding_sha256"])
        private, relative = source["private_source"], source["relative_input"]
        keys(
            private,
            (
                "producer_identity",
                "calibration_identity",
                "clock_epoch",
                "reference_epoch",
                "reference_tick",
                "reference_pose_m_rad",
                "fixture_goal_m",
                "fixture_state",
                "host_frame",
                "arena_yaw_rad",
                "config",
                "scenario",
                "history",
            ),
        )
        identity(private["producer_identity"])
        identity(private["calibration_identity"])
        state_schema(private["fixture_state"])
        config_schema(private["config"])
        sequence(private["reference_pose_m_rad"], 3, list)
        sequence(private["fixture_goal_m"], 2, list)
        require(
            type(private["reference_tick"]) is int
            and type(private["host_frame"]) is bytes
            and type(private["arena_yaw_rad"]) is float
            and type(private["clock_epoch"]) is str
            and type(private["reference_epoch"]) is str,
            "source_reference_type_mismatch",
        )
        for item in (*private["reference_pose_m_rad"], *private["fixture_goal_m"]):
            numeric(item)
        scenario = private["scenario"]
        keys(scenario, (field.name for field in fields(Scenario)))
        require(type(scenario["name"]) is str, "scenario_name_type_mismatch")
        for name, length in (("bounds", 2), ("start", 3), ("goal", 2)):
            sequence(scenario[name], length)
            for item in scenario[name]:
                numeric(item)
        require(
            type(scenario["obstacles"]) is tuple
            and len(scenario["obstacles"]) <= 11
            and type(scenario["obstacle_heights"]) is tuple
            and len(scenario["obstacle_heights"]) <= 11,
            "scenario_object_type_mismatch",
        )
        for obstacle in scenario["obstacles"]:
            sequence(obstacle, 3)
            for item in obstacle:
                numeric(item)
        for item in scenario["obstacle_heights"]:
            numeric(item)
        keys(
            relative,
            (
                "schema",
                "allowed_use",
                *flags[:4],
                "status",
                "reason",
                "reference_tick",
                "config",
                "history",
                "fixture_goal_body_m",
                "fixture_arena_yaw_rad",
                "numerical_source_scale",
            ),
        )
        require(
            relative["schema"] == "micro-classifier/synthetic-c1-relative-input/1"
            and relative["allowed_use"] == "controlled_synthetic_qualification_only"
            and all(relative[flag] is False for flag in flags[:4]),
            "relative_declaration_mismatch",
        )
        require(
            type(relative["reference_tick"]) is int
            and type(relative["status"]) is str
            and type(relative["reason"]) is str,
            "relative_metadata_type_mismatch",
        )
        config_schema(relative["config"])
        if relative["fixture_goal_body_m"] is not None:
            sequence(relative["fixture_goal_body_m"], 2, list)
            require(
                all(type(item) is float for item in relative["fixture_goal_body_m"]),
                "relative_goal_type_mismatch",
            )
        require(
            relative["fixture_arena_yaw_rad"] is None
            or type(relative["fixture_arena_yaw_rad"]) is float,
            "relative_axis_type_mismatch",
        )
        require(
            relative["numerical_source_scale"] is None
            or type(relative["numerical_source_scale"]) in (float, np.float64),
            "relative_scale_type_mismatch",
        )
        for history in (private["history"], relative["history"]):
            require(
                type(history) is list and len(history) <= 8, "unsupported_history_size"
            )
        for event in private["history"]:
            keys(
                event,
                (
                    "clock_epoch",
                    "capture_id",
                    "delivery_tick",
                    "snapshot_tick",
                    "capture",
                ),
            )
            require(
                type(event["clock_epoch"]) is str
                and type(event["capture_id"]) is str
                and type(event["delivery_tick"]) is int
                and type(event["snapshot_tick"]) is int,
                "capture_metadata_type_mismatch",
            )
            capture = event["capture"]
            keys(
                capture,
                (
                    "schema",
                    "allowed_use",
                    *flags[:3],
                    "config",
                    "capture_ticks",
                    "capture_poses_m_rad",
                    "tof_m",
                    "tof_valid",
                ),
            )
            require(
                capture["schema"] == C1_SCHEMA
                and capture["allowed_use"] == "synthetic_visibility_fixtures_only"
                and all(capture[flag] is False for flag in flags[:3]),
                "capture_declaration_mismatch",
            )
            config_schema(capture["config"])
            for name, shape, dtype in (
                ("capture_ticks", (8,), "<u4"),
                ("capture_poses_m_rad", (8, 3), "<f8"),
                ("tof_m", (8, 8, 8), "<f4"),
                ("tof_valid", (8, 8, 8), "|b1"),
            ):
                array_schema(capture[name], shape, dtype)
        for record in relative["history"]:
            keys(
                record,
                ("capture_ticks", "capture_poses_body_m_rad", "tof_m", "tof_valid"),
            )
            for name, shape, dtype in (
                ("capture_ticks", (8,), "<u4"),
                ("capture_poses_body_m_rad", (8, 3), "<f8"),
                ("tof_m", (8, 8, 8), "<f4"),
                ("tof_valid", (8, 8, 8), "|b1"),
            ):
                array_schema(record[name], shape, dtype)
        for event in candidate["events"]:
            keys(
                event,
                (
                    "tick",
                    "kind",
                    "pose_m_rad",
                    "pose_words",
                    "previous_pose_words",
                    "trace",
                    "fixture_state",
                    "host_frame",
                ),
            )
            state_schema(event["fixture_state"])
            require(
                type(event["host_frame"]) is bytes
                and type(event["kind"]) is str
                and type(event["tick"]) is int,
                "event_metadata_type_mismatch",
            )
            sequence(event["pose_m_rad"], 3)
            sequence(event["pose_words"], 3)
            require(
                all(type(item) is float for item in event["pose_m_rad"]),
                "pose_scalar_type_mismatch",
            )
            for word in event["pose_words"]:
                word_value(word)
            if event["previous_pose_words"] is not None:
                sequence(event["previous_pose_words"], 3)
                for word in event["previous_pose_words"]:
                    word_value(word)
            trace = event["trace"]
            if trace is None:
                continue
            keys(
                trace,
                (
                    "allowed_use",
                    "supported",
                    "reason",
                    *flags,
                    "rows",
                    "inputs",
                    "rounded_cells",
                    "residue_correction",
                    "intermediate_words",
                ),
            )
            require(
                type(trace["supported"]) is bool
                and type(trace["rounded_cells"]) is int
                and all(
                    type(trace[name]) is str
                    for name in ("allowed_use", "reason", "residue_correction")
                )
                and all(type(trace[flag]) is bool for flag in flags),
                "trace_metadata_type_mismatch",
            )
            sequence(trace["inputs"], 5)
            sequence(trace["intermediate_words"], 11)
            for word in (*trace["inputs"], *trace["intermediate_words"]):
                word_value(word)
            sequence(trace["rows"], 4)
            for row in trace["rows"]:
                keys(row, ("row", "cells"))
                require(
                    type(row["row"]) is str
                    and type(row["cells"]) is tuple
                    and len(row["cells"]) <= 6,
                    "trace_row_schema_mismatch",
                )
                for cell in row["cells"]:
                    require(type(cell) is dict, "trace_cell_schema_mismatch")
                    keys(
                        cell,
                        (
                            "name",
                            "operation",
                            "operands",
                            "exact_ratio",
                            "zero_sign",
                            "word",
                            "rounding_error_ratio",
                            *(
                                ("truncated_quotient",)
                                if cell.get("operation") == "truncated_residue"
                                else ()
                            ),
                        ),
                    )
                    sequence(cell["operands"], 2)
                    for word in (*cell["operands"], cell["word"]):
                        word_value(word)
                    rational(cell["exact_ratio"])
                    rational(cell["rounding_error_ratio"])
                    require(
                        type(cell["name"]) is str
                        and type(cell["operation"]) is str
                        and type(cell["zero_sign"]) is int
                        and cell["zero_sign"] in (0, 1),
                        "trace_cell_type_mismatch",
                    )
                    if "truncated_quotient" in cell:
                        require(
                            type(cell["truncated_quotient"]) is int,
                            "quotient_type_mismatch",
                        )

    stage = "schema_status"
    try:
        keys(bundle, ("allowed_use", *flags, "candidate", "source", "binding_sha256"))
        require(
            bundle["allowed_use"]
            == "private_synthetic_controlled_motion_candidate_only",
            "candidate_use_mismatch",
        )
        require(all(bundle[flag] is False for flag in flags), "candidate_flag_mismatch")
        candidate = bundle["candidate"]
        keys(
            candidate,
            (
                "lane",
                "model",
                "arithmetic_kind",
                "clock_epoch",
                "seed_tick",
                "seed_pose_words",
                "speed_word",
                "turn_word",
                "duration_word",
                "pi_word",
                "two_word",
                "tick_period_us",
                "nominal_seconds_ratio",
                "source_files",
                "events",
            ),
        )
        require(
            candidate["lane"] == "experimental_controlled_binary64_owner_v1",
            "candidate_lane_mismatch",
        )
        require(
            candidate["model"] == "constant_twist_controlled_binary64_candidate_v1",
            "candidate_model_mismatch",
        )
        events = candidate["events"]
        require(
            type(events) is tuple and 1 <= len(events) <= 8, "unsupported_event_count"
        )
        records_schema(bundle["source"], candidate)
        require(
            type(candidate["seed_tick"]) is int
            and type(candidate["tick_period_us"]) is int,
            "candidate_clock_type_mismatch",
        )
        sequence(candidate["nominal_seconds_ratio"], 2)
        require(
            all(type(item) is int for item in candidate["nominal_seconds_ratio"]),
            "candidate_ratio_type_mismatch",
        )
        sequence(candidate["seed_pose_words"], 3)
        for word in (
            *candidate["seed_pose_words"],
            *(
                candidate[name]
                for name in (
                    "speed_word",
                    "turn_word",
                    "duration_word",
                    "pi_word",
                    "two_word",
                )
            ),
        ):
            word_value(word)
        require(
            type(candidate["clock_epoch"]) is str
            and len(candidate["clock_epoch"]) == 32
            and all(
                character in "0123456789abcdef"
                for character in candidate["clock_epoch"]
            ),
            "epoch_type_mismatch",
        )
        require(
            type(candidate["arithmetic_kind"]) is str, "arithmetic_kind_type_mismatch"
        )
        identity(bundle["binding_sha256"])
        if expected_anchor is not None:
            keys(
                expected_anchor,
                (
                    "current",
                    "lane",
                    "model",
                    "clock_epoch",
                    "source_files",
                    "calibration_identity",
                    "reference_tick",
                    "binding_sha256",
                ),
            )
            require(
                type(expected_anchor["current"]) is bool
                and type(expected_anchor["reference_tick"]) is int
                and all(
                    type(expected_anchor[name]) is str
                    for name in ("lane", "model", "clock_epoch")
                ),
                "anchor_type_mismatch",
            )
            file_schema(expected_anchor["source_files"])
            identity(expected_anchor["calibration_identity"])
            identity(expected_anchor["binding_sha256"])
            preflight(expected_anchor)
        preflight(bundle)
        payload = {
            key: value for key, value in bundle.items() if key != "binding_sha256"
        }
        payload["source"] = {
            **payload["source"],
            "fixture_state": asdict(payload["source"]["fixture_state"]),
        }
        require(
            type(bundle["binding_sha256"]) is str
            and _c1_source_binding_digest(payload) == bundle["binding_sha256"],
            "candidate_digest_mismatch",
        )
        if expected_anchor is not None:
            keys(
                expected_anchor,
                (
                    "current",
                    "lane",
                    "model",
                    "clock_epoch",
                    "source_files",
                    "calibration_identity",
                    "reference_tick",
                    "binding_sha256",
                ),
            )
            declared = {
                "current": True,
                **{
                    name: candidate[name]
                    for name in ("lane", "model", "clock_epoch", "source_files")
                },
                "calibration_identity": bundle["source"]["private_source"][
                    "calibration_identity"
                ],
                "reference_tick": events[-1]["tick"],
                "binding_sha256": bundle["binding_sha256"],
            }
            result["ownership_status"] = (
                "anchor_matches"
                if same(expected_anchor, declared)
                else "unresolved_anchor"
                if expected_anchor["current"] is not True
                else "anchor_mismatch"
            )
        result[stage] = "consistent_checked_relations"
        stage = "event_status"
        seed_tick = candidate["seed_tick"]
        require(
            type(seed_tick) is int and 0 <= seed_tick <= 85899, "seed_tick_mismatch"
        )
        require(
            same(
                (
                    candidate["duration_word"],
                    candidate["pi_word"],
                    candidate["two_word"],
                ),
                (0x3FA999999999999A, 0x400921FB54442D18, 0x4000000000000000),
            ),
            "constant_words_mismatch",
        )
        require(
            type(candidate["tick_period_us"]) is int
            and candidate["tick_period_us"] == 50000
            and same(candidate["nominal_seconds_ratio"], (1, 20)),
            "clock_constants_mismatch",
        )
        require(
            0 <= word_value(candidate["speed_word"]) <= Fraction(3, 5)
            and abs(word_value(candidate["turn_word"])) <= Fraction(3, 2),
            "twist_domain_mismatch",
        )
        require(
            candidate["arithmetic_kind"] == "mixed_controlled_native_unqualified",
            "arithmetic_kind_mismatch",
        )
        elapsed = []
        for index, event in enumerate(events):
            keys(
                event,
                (
                    "tick",
                    "kind",
                    "pose_m_rad",
                    "pose_words",
                    "previous_pose_words",
                    "trace",
                    "fixture_state",
                    "host_frame",
                ),
            )
            require(
                type(event["tick"]) is int
                and event["tick"] == seed_tick + index <= 85899,
                "event_tick_mismatch",
            )
            require(
                event["kind"] == ("seed" if index == 0 else "interval_ending"),
                "event_kind_mismatch",
            )
            require(
                same(
                    event["previous_pose_words"],
                    None if index == 0 else events[index - 1]["pose_words"],
                ),
                "previous_pose_mismatch",
            )
            if index == 0:
                require(
                    event["trace"] is None
                    and same(event["pose_words"], candidate["seed_pose_words"]),
                    "seed_record_mismatch",
                )
            import struct

            require(
                type(event["pose_m_rad"]) is tuple
                and len(event["pose_m_rad"]) == 3
                and type(event["pose_words"]) is tuple
                and len(event["pose_words"]) == 3,
                "pose_shape_mismatch",
            )
            for scalar, word in zip(
                event["pose_m_rad"], event["pose_words"], strict=True
            ):
                word_value(word)
                require(
                    type(scalar) is float
                    and struct.unpack("<Q", struct.pack("<d", scalar))[0] == word,
                    "pose_word_mismatch",
                )
            require(
                abs(word_value(event["pose_words"][2]))
                <= word_value(candidate["pi_word"]),
                "heading_domain_mismatch",
            )
            nominal, binary = (
                Fraction(index, 20),
                index * word_value(candidate["duration_word"]),
            )
            elapsed.append(
                {
                    "tick": event["tick"],
                    "nominal_ratio": (nominal.numerator, nominal.denominator),
                    "binary_ratio": (binary.numerator, binary.denominator),
                }
            )
            result["events_checked"] += 1
        result[stage] = "consistent_checked_relations"
        result["elapsed_clocks"] = tuple(elapsed)
        stage = "trace_status"
        for event in events[1:]:
            require(event["trace"] is not None, "unsupported_missing_trace")
            final_word = verify_trace(event["trace"], event["previous_pose_words"][2])
            require(final_word == event["pose_words"][2], "stored_heading_mismatch")
        result[stage] = "consistent_checked_relations"
        stage = "codec_status"
        source = bundle["source"]
        private = source["private_source"]
        for event in events:
            state = State(**event["fixture_state"])
            require(
                state.sequence == event["tick"] & 0xFFFF
                and state.timestamp_us == event["tick"] * 50000,
                "state_clock_mismatch",
            )
            speed = struct.unpack("<d", struct.pack("<Q", candidate["speed_word"]))[0]
            turn = struct.unpack("<d", struct.pack("<Q", candidate["turn_word"]))[0]
            expected = State(
                sequence=state.sequence,
                timestamp_us=state.timestamp_us,
                velocity_m_s=(speed, 0.0, 0.0),
                angular_velocity_rad_s=(0.0, 0.0, turn),
                goal_m=state.goal_m,
            )
            require(
                same(asdict(state), asdict(expected)),
                "state_twist_or_defaults_mismatch",
            )
            require(encode_state(state) == event["host_frame"], "state_frame_mismatch")
            decoded = decode_state(event["host_frame"])
            require(
                encode_state(decoded) == event["host_frame"],
                "codec_round_trip_mismatch",
            )
            changed = tuple(
                field.name
                for field in fields(State)
                if not same(getattr(state, field.name), getattr(decoded, field.name))
            )
            if changed:
                result["host_changed_fields"] += ((event["tick"], changed),)
            result["frames_checked"] += 1
        require(
            same(events[-1]["fixture_state"], asdict(source["fixture_state"]))
            and same(events[-1]["fixture_state"], private["fixture_state"])
            and events[-1]["host_frame"] == private["host_frame"],
            "last_state_frame_mismatch",
        )
        result[stage] = "consistent_checked_relations"
        stage = "capture_status"
        relative, config = source["relative_input"], private["config"]
        require(
            same(candidate["source_files"], source["source_files"])
            and private["producer_identity"]
            == _c1_source_binding_digest(source["source_files"])
            and private["calibration_identity"] == _c1_source_binding_digest(config),
            "source_identity_link_mismatch",
        )
        source_payload = {
            "relative_input": relative,
            "fixture_state": asdict(source["fixture_state"]),
            "host_frame": private["host_frame"],
            "private_source": private,
        }
        require(
            _c1_source_binding_digest(source_payload) == source["binding_sha256"],
            "source_digest_mismatch",
        )
        require(same(relative["config"], config), "relative_config_mismatch")
        require(
            config["dt"] == 0.05
            and config["latency_ticks"] == 2
            and config["history_ticks"] == 8
            and config["noise_std"] == 0.0
            and config["dropout"] == 0.0
            and config["max_range"] == 4.0,
            "unsupported_capture_profile",
        )
        require(
            private["clock_epoch"]
            == private["reference_epoch"]
            == candidate["clock_epoch"],
            "reference_epoch_mismatch",
        )
        require(
            private["reference_tick"]
            == relative["reference_tick"]
            == events[-1]["tick"]
            and same(tuple(private["reference_pose_m_rad"]), events[-1]["pose_m_rad"]),
            "reference_event_mismatch",
        )
        require(
            same(tuple(private["fixture_goal_m"]), private["scenario"]["goal"]),
            "source_goal_copy_mismatch",
        )
        history = private["history"]
        ledger = {event["tick"]: event for event in events}
        eligible = tuple(tick for tick in ledger if tick == 0 or tick % 4 != 1)
        expected_snapshots = tuple(
            tick
            for tick in ledger
            if any(captured + 2 <= tick for captured in eligible)
        )[-8:]
        previous = None
        for entry in history:
            capture = entry["capture"]
            snapshot = entry["snapshot_tick"]
            require(snapshot in ledger, "unsupported_missing_snapshot_ledger")
            delivered = tuple(tick for tick in eligible if tick + 2 <= snapshot)
            require(bool(delivered), "unsupported_missing_capture_ledger")
            captured = delivered[-1]
            require(
                entry["clock_epoch"] == candidate["clock_epoch"]
                and entry["capture_id"] == f"{candidate['clock_epoch']}:{captured}"
                and entry["delivery_tick"] == captured + 2
                and np.all(capture["capture_ticks"] == captured),
                "capture_clock_mismatch",
            )
            require(same(capture["config"], config), "capture_config_mismatch")
            pose_bytes = struct.pack("<ddd", *ledger[captured]["pose_m_rad"])
            require(
                all(
                    row.tobytes() == pose_bytes
                    for row in capture["capture_poses_m_rad"]
                ),
                "capture_pose_link_mismatch",
            )
            ranges, valid = capture["tof_m"], capture["tof_valid"]
            require(
                not np.any(valid & ((ranges <= 0) | (ranges >= 4)))
                and np.all(ranges[~valid].view(np.uint32) == 0),
                "capture_masked_range_mismatch",
            )
            fingerprint = _c1_source_binding_digest(capture)
            if previous is not None and previous[0] == captured:
                require(
                    previous[1:] == (entry["capture_id"], fingerprint),
                    "held_capture_changed",
                )
            previous = captured, entry["capture_id"], fingerprint
            result["captures_checked"] += 1
        require(
            tuple(entry["snapshot_tick"] for entry in history) == expected_snapshots
            and bool(history),
            "unsupported_incomplete_delivered_history",
        )
        result[stage] = "consistent_checked_relations"
        stage = "copied_input_status"
        require(
            len(relative["history"]) == len(history),
            "unsupported_incomplete_copied_history",
        )
        for record, entry in zip(relative["history"], history, strict=True):
            for name in ("capture_ticks", "tof_m", "tof_valid"):
                require(
                    same(record[name], entry["capture"][name]),
                    "relative_payload_copy_mismatch",
                )
            result["copied_records_checked"] += 1
        result[stage] = "consistent_checked_relations"
        result["content_status"] = "consistent_checked_relations"
        result["reason"] = "bounded_declared_relations_only"
    except (ValueError, KeyError, TypeError, OverflowError) as error:
        result[stage] = (
            "unresolved_evidence"
            if str(error).startswith("unsupported_")
            else "inconsistent_record"
        )
        result["content_status"] = result[stage]
        result["reason"] = str(error)
    return result


class _SyntheticC1ControlledMotionOwner:
    """Stage a private mixed-arithmetic fixture, never qualify motion or wire."""

    _FLAGS = (
        "training_approved",
        "real_input_qualified",
        "free_space_qualified",
        "numerically_certified",
        "producer_parity_qualified",
    )

    def __init__(
        self,
        scenario,
        *,
        seed_tick,
        position_m,
        heading_word,
        speed,
        turn_word,
        synthetic_test_only=False,
    ):
        if synthetic_test_only is not True:
            raise ValueError("controlled owner requires synthetic_test_only=True")
        if type(seed_tick) is not int or not 0 <= seed_tick <= 85899:
            raise ValueError("controlled owner requires a nonwrapping seed tick")
        if type(position_m) not in (tuple, list) or len(position_m) != 2:
            raise ValueError("controlled owner requires two binary64 coordinates")
        position_words = tuple(self._word(value) for value in position_m)
        speed_word = self._word(speed)
        heading, turn = self._scalar(heading_word), self._scalar(turn_word)
        if not 0 <= speed <= 0.6 or abs(turn) > 1.5 or abs(heading) > math.pi:
            raise ValueError("unsupported controlled owner seed or twist")
        self._seed_tick = seed_tick
        self._seed_words = (*position_words, heading_word)
        self._speed = speed
        self._speed_word = speed_word
        self._turn_word = turn_word
        self._turn = turn
        self._discarded = False
        self._lane = "experimental_controlled_binary64_owner_v1"
        self._model = "constant_twist_controlled_binary64_candidate_v1"
        if (
            self._word(math.pi) != 0x400921FB54442D18
            or self._word(0.05) != 0x3FA999999999999A
            or self._word(2.0) != 0x4000000000000000
            or np.dtype(float).itemsize != 8
        ):
            raise ValueError("unsupported controlled owner native scalar format")
        recorder = _SyntheticC1SourceRecorder(scenario, synthetic_test_only=True)
        pose = (*position_m, heading)
        event = self._prepare_event(recorder, seed_tick, pose, None, None)
        self._validate_event(recorder, event)
        self._root = {"recorder": recorder, "events": (event,), "binding": None}

    @staticmethod
    def _scalar(word):
        import struct

        _synthetic_binary64_value(word)
        value = struct.unpack("<d", struct.pack("<Q", word))[0]
        if struct.unpack("<Q", struct.pack("<d", value))[0] != word:
            raise ValueError("controlled owner word conversion changed")
        return value

    @staticmethod
    def _word(value):
        import struct

        if type(value) is not float or not math.isfinite(value):
            raise ValueError(
                "controlled owner requires finite builtin binary64 scalars"
            )
        return struct.unpack("<Q", struct.pack("<d", value))[0]

    def _check_root(self):
        if self._discarded:
            raise ValueError("controlled owner discarded after ambiguous publication")
        if (
            self._lane != "experimental_controlled_binary64_owner_v1"
            or self._model != "constant_twist_controlled_binary64_candidate_v1"
            or self._word(self._speed) != self._speed_word
            or self._word(self._turn) != self._turn_word
            or self._word(math.pi) != 0x400921FB54442D18
        ):
            raise ValueError("controlled owner lane, twist or constant changed")
        recorder = self._root["recorder"]
        if recorder._source_files() != recorder._identities:
            raise ValueError("controlled owner source files changed; use a new owner")

    def _prepare_event(self, recorder, tick, pose, trace, previous_words):
        from interface.protocol import State, encode_state

        pose_words = tuple(self._word(value) for value in pose)
        if abs(pose[2]) > math.pi:
            raise ValueError("unsupported controlled owner heading")
        heading = math.atan2(math.sin(pose[2]), math.cos(pose[2]))
        cosine, sine = math.cos(heading), math.sin(heading)
        delta_x, delta_y = np.asarray(recorder._scenario.goal) - pose[:2]
        state = State(
            sequence=tick & 0xFFFF,
            timestamp_us=tick * 50000,
            velocity_m_s=(self._speed, 0.0, 0.0),
            angular_velocity_rad_s=(0.0, 0.0, self._turn),
            goal_m=(
                float(delta_x * cosine + delta_y * sine),
                float(delta_y * cosine - delta_x * sine),
                0.0,
            ),
        )
        frame = encode_state(state)
        recorder.record_tick(tick, pose_m_rad=pose, fixture_state=state)
        return {
            "tick": tick,
            "kind": "seed" if trace is None else "interval_ending",
            "pose_m_rad": tuple(pose),
            "pose_words": pose_words,
            "previous_pose_words": previous_words,
            "trace": deepcopy(trace),
            "fixture_state": asdict(state),
            "host_frame": frame,
        }

    def _validate_event(self, recorder, event):
        tick, pose, state, frame = recorder._current
        if (
            event["tick"] != tick
            or event["host_frame"] != frame
            or event["fixture_state"] != asdict(state)
            or event["pose_words"] != tuple(self._word(float(value)) for value in pose)
            or event["pose_words"]
            != tuple(self._word(value) for value in event["pose_m_rad"])
        ):
            raise ValueError("controlled owner staged event binding mismatch")

    def _publish(self, prepared):
        self._root = prepared

    def _commit(self, prepared):
        try:
            self._publish(prepared)
        except BaseException:
            self._discarded = True
            raise

    def advance(self, tick):
        self._check_root()
        root = self._root
        if (
            type(tick) is not int
            or tick != root["events"][-1]["tick"] + 1
            or tick > 85899
            or len(root["events"]) >= 8
        ):
            raise ValueError("controlled owner requires bounded consecutive ticks")
        previous = root["events"][-1]
        previous_words = tuple(self._word(value) for value in previous["pose_m_rad"])
        if previous_words != previous["pose_words"]:
            raise ValueError("controlled owner previous pose words changed")
        trace = _trace_synthetic_binary64_rows(
            heading_word=previous_words[2],
            turn_word=self._turn_word,
            duration_word=0x3FA999999999999A,
            pi_word=0x400921FB54442D18,
            two_word=0x4000000000000000,
            synthetic_test_only=True,
        )
        if trace["supported"] is not True:
            raise ValueError(f"unsupported controlled owner trace: {trace['reason']}")
        words = trace["intermediate_words"]
        midpoint, argument, heading = map(self._scalar, (words[2], words[4], words[10]))
        distance = self._speed * 0.05 * np.sinc(argument)
        position = np.asarray(previous["pose_m_rad"][:2]) + distance * np.array(
            [math.cos(midpoint), math.sin(midpoint)]
        )
        pose = (float(position[0]), float(position[1]), heading)
        recorder = deepcopy(root["recorder"])
        event = self._prepare_event(recorder, tick, pose, trace, previous_words)
        self._validate_event(recorder, event)
        self._check_root()
        prepared = {
            "recorder": recorder,
            "events": (*root["events"], event),
            "binding": None,
        }
        self._commit(prepared)

    @staticmethod
    def _digest(bundle):
        payload = {
            key: value for key, value in bundle.items() if key != "binding_sha256"
        }
        payload["source"] = {
            **payload["source"],
            "fixture_state": asdict(payload["source"]["fixture_state"]),
        }
        return _c1_source_binding_digest(payload)

    def snapshot(self):
        self._check_root()
        recorder = deepcopy(self._root["recorder"])
        source = recorder.snapshot()
        bundle = {
            "allowed_use": "private_synthetic_controlled_motion_candidate_only",
            **{flag: False for flag in self._FLAGS},
            "candidate": {
                "lane": self._lane,
                "model": self._model,
                "arithmetic_kind": "mixed_controlled_native_unqualified",
                "clock_epoch": recorder._epoch,
                "seed_tick": self._seed_tick,
                "seed_pose_words": self._seed_words,
                "speed_word": self._speed_word,
                "turn_word": self._turn_word,
                "duration_word": 0x3FA999999999999A,
                "pi_word": 0x400921FB54442D18,
                "two_word": 0x4000000000000000,
                "tick_period_us": 50000,
                "nominal_seconds_ratio": (1, 20),
                "source_files": dict(recorder._identities),
                "events": deepcopy(self._root["events"]),
            },
            "source": source,
        }
        binding = self._digest(bundle)
        bundle["binding_sha256"] = binding
        self._check_root()
        self._commit({**self._root, "recorder": recorder, "binding": binding})
        return bundle

    def audit(self, bundle):
        self._check_root()
        binding = self._root["binding"]
        if binding is None:
            raise ValueError("controlled owner needs a current snapshot")
        result = {
            "allowed_use": "private_synthetic_controlled_motion_audit_only",
            **{flag: False for flag in self._FLAGS},
            "ownership_status": "inconsistent_candidate_record",
            "arithmetic_status": "unqualified_word_trace_evidence",
            "source_status": "unqualified_candidate_source",
            "wire_status": "unqualified_candidate_wire",
            "motion_status": "unresolved_motion_evidence",
            "events_checked": 0,
        }
        if (
            type(bundle) is not dict
            or set(bundle)
            != {"allowed_use", *self._FLAGS, "candidate", "source", "binding_sha256"}
            or bundle["allowed_use"]
            != "private_synthetic_controlled_motion_candidate_only"
            or any(bundle[flag] is not False for flag in self._FLAGS)
            or type(bundle["binding_sha256"]) is not str
        ):
            return result
        try:
            if bundle["binding_sha256"] != binding or self._digest(bundle) != binding:
                return result
        except (KeyError, ValueError, TypeError, OverflowError):
            return result
        result.update(
            ownership_status="candidate_binding_matches",
            arithmetic_status="supported_declared_word_trace",
            events_checked=len(self._root["events"]),
        )
        return result


class _SyntheticC1MotionOwner:
    """Own a bounded constant-twist fixture, not a simulator rollout."""

    def __init__(
        self,
        scenario,
        *,
        seed_tick,
        pose_m_rad,
        speed,
        turn_rate,
        synthetic_test_only=False,
    ):
        if synthetic_test_only is not True:
            raise ValueError("C1 motion owner requires synthetic_test_only=True")
        if type(seed_tick) is not int or not 0 <= seed_tick <= 85899:
            raise ValueError("C1 motion owner requires a nonwrapping seed tick")
        pose = _c1_array(pose_m_rad, (3,)).astype(float).copy()
        if any(isinstance(value, (bool, np.bool_)) for value in (speed, turn_rate)):
            raise ValueError("C1 motion owner requires numeric twist values")
        speed, turn_rate = map(float, _c1_array([speed, turn_rate], (2,)))
        config = _c1_config(None)
        if (
            not 0 <= speed <= config.max_speed
            or abs(turn_rate) > config.max_turn_rate
            or abs(pose[2]) > math.pi
        ):
            raise ValueError("unsupported C1 motion seed or twist")
        self._recorder = _SyntheticC1SourceRecorder(scenario, synthetic_test_only=True)
        self._seed_tick = seed_tick
        self._seed_pose = pose.copy()
        self._speed = speed
        self._turn_rate = turn_rate
        self._events = []
        self._binding = None
        self._record(seed_tick, pose)

    def _record(self, tick, pose):
        from interface.protocol import State, encode_state

        heading = math.atan2(math.sin(pose[2]), math.cos(pose[2]))
        cosine, sine = math.cos(heading), math.sin(heading)
        delta_x, delta_y = np.asarray(self._recorder._scenario.goal) - pose[:2]
        state = State(
            sequence=tick,
            timestamp_us=tick * 50000,
            velocity_m_s=(self._speed, 0.0, 0.0),
            angular_velocity_rad_s=(0.0, 0.0, self._turn_rate),
            goal_m=(
                float(delta_x * cosine + delta_y * sine),
                float(delta_y * cosine - delta_x * sine),
                0.0,
            ),
        )
        event = {
            "tick": tick,
            "pose_m_rad": pose.tolist(),
            "fixture_state": asdict(state),
            "host_frame": encode_state(state),
        }
        self._recorder.record_tick(tick, pose_m_rad=pose, fixture_state=state)
        self._events.append(event)
        self._binding = None

    def advance(self, tick):
        from sim.rover import integrate

        if (
            type(tick) is not int
            or tick != self._events[-1]["tick"] + 1
            or tick > 85899
            or len(self._events) >= 8
        ):
            raise ValueError("C1 motion owner requires bounded consecutive ticks")
        previous = self._events[-1]["pose_m_rad"]
        position, heading = integrate(
            previous[:2], previous[2], self._speed, self._turn_rate, 0.05
        )
        pose = _c1_array([*position, heading], (3,)).astype(float)
        if abs(pose[2]) > math.pi:
            raise ValueError("unsupported C1 motion heading")
        self._record(tick, pose)

    def snapshot(self):
        source = self._recorder.snapshot()
        motion = {
            "model": "constant_twist_interval_ending_v1",
            "clock_epoch": self._recorder._epoch,
            "seed_tick": self._seed_tick,
            "seed_pose_m_rad": self._seed_pose.tolist(),
            "speed_m_s": self._speed,
            "turn_rate_rad_s": self._turn_rate,
            "tick_period_us": 50000,
            "tick_period_s": 0.05,
            "fixture_goal_m": list(self._recorder._scenario.goal),
            "events": deepcopy(self._events),
        }
        self._binding = _c1_source_binding_digest(
            {
                "motion": motion,
                "source": {**source, "fixture_state": asdict(source["fixture_state"])},
            }
        )
        return {
            "allowed_use": "private_synthetic_motion_record_only",
            "training_approved": False,
            "real_input_qualified": False,
            "free_space_qualified": False,
            "numerically_certified": False,
            "motion": motion,
            "source": source,
            "binding_sha256": self._binding,
        }

    def audit(self, bundle):
        if self._binding is None:
            raise ValueError("C1 motion owner needs a current snapshot")
        if (
            type(bundle) is not dict
            or set(bundle)
            != {
                "allowed_use",
                "training_approved",
                "real_input_qualified",
                "free_space_qualified",
                "numerically_certified",
                "motion",
                "source",
                "binding_sha256",
            }
            or bundle["allowed_use"] != "private_synthetic_motion_record_only"
            or any(
                bundle[key] is not False
                for key in (
                    "training_approved",
                    "real_input_qualified",
                    "free_space_qualified",
                    "numerically_certified",
                )
            )
        ):
            raise ValueError("unsupported private C1 motion bundle")
        result = {
            "allowed_use": "private_synthetic_motion_audit_only",
            "training_approved": False,
            "real_input_qualified": False,
            "free_space_qualified": False,
            "numerically_certified": False,
            "ownership_status": "inconsistent_source_record",
            "motion_status": "unresolved_motion_evidence",
            "motion_reason": "owner_binding_mismatch",
            "events_checked": 0,
            "source_audit": None,
        }
        try:
            binding = _c1_source_binding_digest(
                {
                    "motion": bundle["motion"],
                    "source": {
                        **bundle["source"],
                        "fixture_state": asdict(bundle["source"]["fixture_state"]),
                    },
                }
            )
        except (KeyError, ValueError, TypeError, OverflowError):
            return result
        if bundle["binding_sha256"] != self._binding or binding != self._binding:
            return result
        result["ownership_status"] = "consistent_under_fixture_assumptions"
        checked = _check_synthetic_c1_motion(bundle["motion"], bundle["source"])
        result.update(
            motion_status=checked["status"],
            motion_reason=checked["reason"],
            events_checked=checked["events_checked"],
            source_audit=self._recorder.audit(bundle["source"]),
        )
        return result


def _check_synthetic_c1_motion(motion, source):
    """Check private event references independently; unsupported curves abstain."""
    from fractions import Fraction

    from interface.protocol import State, encode_state

    result = {
        "status": "unresolved_motion_evidence",
        "reason": "unsupported_motion_record",
        "events_checked": 0,
    }

    def inconsistent(reason):
        result.update(status="inconsistent_motion_record", reason=reason)
        return result

    def rational(value):
        return Fraction.from_float(float(value))

    def outward(lower, upper):
        rounded_lower, rounded_upper = float(lower), float(upper)
        if rational(rounded_lower) > lower:
            rounded_lower = math.nextafter(rounded_lower, -math.inf)
        if rational(rounded_upper) < upper:
            rounded_upper = math.nextafter(rounded_upper, math.inf)
        return rational(rounded_lower), rational(rounded_upper)

    try:
        if type(motion) is not dict or set(motion) != {
            "model",
            "clock_epoch",
            "seed_tick",
            "seed_pose_m_rad",
            "speed_m_s",
            "turn_rate_rad_s",
            "tick_period_us",
            "tick_period_s",
            "fixture_goal_m",
            "events",
        }:
            return result
        if (
            motion["model"] != "constant_twist_interval_ending_v1"
            or type(motion["seed_tick"]) is not int
            or not 0 <= motion["seed_tick"] <= 85899
            or type(motion["tick_period_us"]) is not int
            or motion["tick_period_us"] != 50000
            or type(motion["tick_period_s"]) is not float
            or motion["tick_period_s"] != 0.05
        ):
            return result
        seed = _c1_array(motion["seed_pose_m_rad"], (3,)).astype(float)
        speed, turn = map(
            float, _c1_array([motion["speed_m_s"], motion["turn_rate_rad_s"]], (2,))
        )
        if not 0 <= speed <= 0.6 or abs(turn) > 1.5 or abs(seed[2]) > math.pi:
            return result
        events = motion["events"]
        if type(events) is not list or not 1 <= len(events) <= 8:
            return result
        private = source["private_source"]
        if (
            type(motion["clock_epoch"]) is not str
            or not motion["clock_epoch"]
            or private["clock_epoch"] != motion["clock_epoch"]
            or private["reference_epoch"] != motion["clock_epoch"]
        ):
            return inconsistent("motion_clock_epoch_mismatch")
        goal = _c1_array(motion["fixture_goal_m"], (2,)).astype(float)
        if not np.array_equal(goal, private["fixture_goal_m"]) or not np.array_equal(
            goal, private["scenario"]["goal"]
        ):
            return inconsistent("motion_world_goal_mismatch")
        straight = turn == 0 and seed[2] == 0
        step_lower, step_upper = outward(
            rational(speed) * rational(0.05), rational(speed) * rational(0.05)
        )
        step_lower = min(step_lower, rational(speed) / 20)
        step_upper = max(step_upper, rational(speed) / 20)
        lower = upper = rational(seed[0])
        retained = {}
        for index, event in enumerate(events):
            if type(event) is not dict or set(event) != {
                "tick",
                "pose_m_rad",
                "fixture_state",
                "host_frame",
            }:
                return result
            tick = event["tick"]
            if (
                type(tick) is not int
                or tick != motion["seed_tick"] + index
                or tick > 85899
            ):
                return inconsistent("motion_tick_discontinuity")
            pose = _c1_array(event["pose_m_rad"], (3,)).astype(float)
            state = State(**event["fixture_state"])
            if (
                state.timestamp_us != tick * 50000
                or state.velocity_m_s != (speed, 0, 0)
                or state.angular_velocity_rad_s != (0, 0, turn)
                or state.ages_us[:3] != (0, 0, 0)
                or state.validity & 7 != 7
            ):
                return inconsistent("host_twist_or_clock_mismatch")
            if (
                type(event["host_frame"]) is not bytes
                or encode_state(state) != event["host_frame"]
            ):
                return inconsistent("motion_host_frame_mismatch")
            if index == 0 and not np.array_equal(pose, seed):
                return inconsistent("motion_seed_mismatch")
            if straight:
                if index:
                    lower, upper = outward(lower + step_lower, upper + step_upper)
                if (
                    not lower <= rational(pose[0]) <= upper
                    or pose[1] != seed[1]
                    or pose[2] != 0
                ):
                    return inconsistent("straight_reference_mismatch")
                for axis in (0, 1):
                    expected = rational(goal[axis]) - rational(pose[axis])
                    goal_lower, goal_upper = outward(expected, expected)
                    if (
                        not goal_lower <= rational(state.goal_m[axis]) <= goal_upper
                        or state.goal_m[2] != 0
                    ):
                        return inconsistent("motion_body_goal_mismatch")
            retained[tick] = pose
            result["events_checked"] += 1
        if (
            private["reference_tick"] != events[-1]["tick"]
            or not np.array_equal(
                private["reference_pose_m_rad"], retained[events[-1]["tick"]]
            )
            or _c1_source_binding_digest(private["fixture_state"])
            != _c1_source_binding_digest(events[-1]["fixture_state"])
            or private["host_frame"] != events[-1]["host_frame"]
        ):
            return inconsistent("motion_reference_event_mismatch")
        for event in private["history"]:
            capture = event["capture"]
            ticks = _c1_array(capture["capture_ticks"], (8,), "iu")
            poses = _c1_array(capture["capture_poses_m_rad"], (8, 3))
            if (
                event["clock_epoch"] != motion["clock_epoch"]
                or int(ticks[0]) not in retained
                or not np.all(ticks == ticks[0])
                or not np.all(poses == retained[int(ticks[0])])
            ):
                return inconsistent("motion_acquisition_event_mismatch")
    except (KeyError, TypeError, ValueError, OverflowError):
        return result
    result.update(
        status="consistent_under_fixture_assumptions"
        if straight
        else "unresolved_motion_evidence",
        reason="rational_straight_enclosure"
        if straight
        else "independent_curved_or_heading_enclosure_missing",
    )
    return result


class _SyntheticC1SourceRecorder:
    """Own ideal fixture events in memory, without a rollout or runtime consumer."""

    def __init__(self, scenario, *, synthetic_test_only=False):
        from uuid import uuid4

        from sim.rover import Scenario

        if synthetic_test_only is not True:
            raise ValueError("C1 recorder requires synthetic_test_only=True")
        if not isinstance(scenario, Scenario):
            raise TypeError("C1 recorder requires a fixture Scenario")
        self._config = _c1_config(None)
        self._scenario = deepcopy(scenario)
        self._scenario.validate(self._config)
        self._identities = self._source_files()
        self._epoch = uuid4().hex
        self._pending = []
        self._history = []
        self._latest = None
        self._current = None
        self._binding = None

    @staticmethod
    def _source_files():
        root = Path(__file__).resolve().parent.parent
        return {
            name: hashlib.sha256((root / name).read_bytes()).hexdigest()
            for name in ("sim/diagnostics.py", "sim/rover.py", "interface/protocol.py")
        }

    def record_tick(self, tick, *, pose_m_rad, fixture_state):
        from interface.protocol import State, encode_state

        if (
            type(tick) is not int
            or not 0 <= tick <= 0xFFFFFFFF // 50000
            or (self._current is not None and tick != self._current[0] + 1)
        ):
            raise ValueError(
                "C1 recorder requires consecutive nonwrapping fixture ticks"
            )
        if not isinstance(fixture_state, State):
            raise TypeError("C1 recorder requires a fixture State")
        pose = _c1_array(pose_m_rad, (3,)).astype(float).copy()
        state = deepcopy(fixture_state)
        frame = encode_state(state)
        if state.timestamp_us != tick * 50000:
            raise ValueError("C1 recorder State timestamp must match the fixture tick")
        pending = list(self._pending)
        if tick == 0 or tick % 4 != 1:
            capture = capture_synthetic_c1_views(
                self._scenario,
                pose_m_rad=pose,
                capture_tick=tick,
                synthetic_test_only=True,
            )
            pending.append(
                {
                    "clock_epoch": self._epoch,
                    "capture_id": f"{self._epoch}:{tick}",
                    "delivery_tick": tick + self._config.latency_ticks,
                    "capture": deepcopy(capture),
                }
            )
        ready = [event for event in pending if event["delivery_tick"] <= tick]
        latest = ready[-1] if ready else self._latest
        history = list(self._history)
        if latest is not None:
            history.append({**latest, "snapshot_tick": tick})
        self._pending = [event for event in pending if event["delivery_tick"] > tick]
        self._history = history[-self._config.history_ticks :]
        self._latest = latest
        self._current = tick, pose, state, frame
        self._binding = None

    def snapshot(self):
        if self._current is None or not self._history:
            raise ValueError("C1 recorder needs a delivered fixture capture")
        if self._source_files() != self._identities:
            raise ValueError("C1 recorder source files changed; use a new recorder")
        tick, pose, state, frame = self._current
        source = {
            "producer_identity": _c1_source_binding_digest(self._identities),
            "calibration_identity": _c1_source_binding_digest(asdict(self._config)),
            "clock_epoch": self._epoch,
            "reference_epoch": self._epoch,
            "reference_tick": tick,
            "reference_pose_m_rad": pose.tolist(),
            "fixture_goal_m": list(self._scenario.goal),
            "fixture_state": asdict(state),
            "host_frame": frame,
            "arena_yaw_rad": 0.0,
            "config": asdict(self._config),
            "scenario": asdict(self._scenario),
            "history": deepcopy(self._history),
        }
        relative = prepare_synthetic_c1_relative_input(
            [event["capture"] for event in self._history],
            reference_tick=tick,
            reference_pose_m_rad=pose,
            fixture_goal_m=self._scenario.goal,
            synthetic_test_only=True,
        )
        binding = _c1_source_binding_digest(
            {
                "relative_input": relative,
                "fixture_state": asdict(state),
                "host_frame": frame,
                "private_source": source,
            }
        )
        self._binding = binding
        return {
            "allowed_use": "private_synthetic_source_record_only",
            "training_approved": False,
            "real_input_qualified": False,
            "free_space_qualified": False,
            "numerically_certified": False,
            "relative_input": relative,
            "fixture_state": deepcopy(state),
            "private_source": source,
            "source_files": dict(self._identities),
            "binding_sha256": binding,
        }

    def audit(self, bundle):
        if self._binding is None:
            raise ValueError(
                "C1 recorder needs a snapshot of its current reference event"
            )
        if (
            type(bundle) is not dict
            or set(bundle)
            != {
                "allowed_use",
                "training_approved",
                "real_input_qualified",
                "free_space_qualified",
                "numerically_certified",
                "relative_input",
                "fixture_state",
                "private_source",
                "source_files",
                "binding_sha256",
            }
            or bundle["allowed_use"] != "private_synthetic_source_record_only"
            or any(
                bundle[key] is not False
                for key in (
                    "training_approved",
                    "real_input_qualified",
                    "free_space_qualified",
                    "numerically_certified",
                )
            )
        ):
            raise ValueError("unsupported private C1 source bundle")
        result = _audit_synthetic_c1_source_binding(
            bundle["relative_input"],
            fixture_state=bundle["fixture_state"],
            private_source=bundle["private_source"],
            expected_binding=self._binding,
            synthetic_test_only=True,
        )
        if (
            bundle["binding_sha256"] != self._binding
            or _c1_source_binding_digest(bundle["source_files"])
            != _c1_source_binding_digest(self._identities)
            or self._source_files() != self._identities
        ):
            result.update(
                status="inconsistent_source_record",
                reason="recorder_identity_or_binding_mismatch",
            )
        return result


def _c1_source_binding_digest(record):
    """Fingerprint private fixture evidence, not attest its truth or independence."""

    def pack(value):
        if isinstance(value, (np.ndarray, np.generic)):
            array = np.asarray(value)
            if array.dtype.kind not in "biuf" or not np.all(np.isfinite(array)):
                raise ValueError("source binding requires finite numeric arrays")
            return {
                "kind": "array" if isinstance(value, np.ndarray) else "numpy_scalar",
                "dtype": array.dtype.str,
                "shape": array.shape,
                "order": "C",
                "sha256": hashlib.sha256(array.tobytes(order="C")).hexdigest(),
            }
        if type(value) is dict:
            if any(type(key) is not str for key in value):
                raise ValueError("source binding keys must be strings")
            return {key: pack(item) for key, item in value.items()}
        if type(value) in (list, tuple):
            return {type(value).__name__: [pack(item) for item in value]}
        if type(value) is bytes:
            return {"bytes": value.hex()}
        if value is None or type(value) in (str, bool, int, float):
            return {type(value).__name__: value}
        raise ValueError("unsupported private source binding value")

    return hashlib.sha256(
        json.dumps(pack(record), sort_keys=True, allow_nan=False).encode("ascii")
    ).hexdigest()


def _audit_synthetic_c1_source_binding(
    relative_input,
    *,
    fixture_state,
    private_source,
    expected_binding,
    synthetic_test_only=False,
):
    """Compare private ideal fixtures, never supply evidence to a decision query."""
    from interface.protocol import State, decode_state, encode_state

    if synthetic_test_only is not True:
        raise ValueError("C1 source audit requires synthetic_test_only=True")
    result = {
        "allowed_use": "private_synthetic_source_audit_only",
        "training_approved": False,
        "real_input_qualified": False,
        "free_space_qualified": False,
        "numerically_certified": False,
        "status": "unresolved_source_evidence",
        "reason": "unsupported_source_record",
        "binding_sha256": None,
        "host_changed_fields": (),
    }

    def stop(reason, status="unresolved_source_evidence"):
        result.update(reason=reason, status=status)
        return result

    if not isinstance(fixture_state, State):
        raise TypeError("C1 source audit requires a synthetic State")
    if type(expected_binding) is not str or len(expected_binding) != 64:
        return stop("missing_source_binding")
    try:
        host_frame = encode_state(fixture_state)
        binding = _c1_source_binding_digest(
            {
                "relative_input": relative_input,
                "fixture_state": asdict(fixture_state),
                "host_frame": host_frame,
                "private_source": private_source,
            }
        )
        result["binding_sha256"] = binding
        if binding != expected_binding:
            return stop("source_binding_mismatch", "inconsistent_source_record")
        if type(private_source) is not dict or set(private_source) != {
            "producer_identity",
            "calibration_identity",
            "clock_epoch",
            "reference_epoch",
            "reference_tick",
            "reference_pose_m_rad",
            "fixture_goal_m",
            "fixture_state",
            "host_frame",
            "arena_yaw_rad",
            "config",
            "scenario",
            "history",
        }:
            return stop("missing_source_record_fields")
        if any(
            type(private_source[key]) is not str or not private_source[key]
            for key in ("producer_identity", "calibration_identity", "clock_epoch")
        ):
            return stop("missing_source_identity")
        if private_source["reference_epoch"] != private_source["clock_epoch"]:
            return stop("reference_clock_epoch_mismatch")
        config = _c1_config(None)
        config_digest = _c1_source_binding_digest(asdict(config))
        if type(relative_input) is not dict or set(relative_input) != {
            "schema",
            "allowed_use",
            "training_approved",
            "real_input_qualified",
            "free_space_qualified",
            "numerically_certified",
            "status",
            "reason",
            "reference_tick",
            "config",
            "history",
            "fixture_goal_body_m",
            "fixture_arena_yaw_rad",
            "numerical_source_scale",
        }:
            return stop("unsupported_candidate_fields")
        if (
            relative_input["schema"] != "micro-classifier/synthetic-c1-relative-input/1"
            or relative_input["allowed_use"]
            != "controlled_synthetic_qualification_only"
            or relative_input["status"] != "relative_fixture"
            or any(
                relative_input[key] is not False
                for key in (
                    "training_approved",
                    "real_input_qualified",
                    "free_space_qualified",
                    "numerically_certified",
                )
            )
            or _c1_source_binding_digest(relative_input["config"]) != config_digest
            or _c1_source_binding_digest(private_source["config"]) != config_digest
        ):
            return stop("unsupported_candidate_scope_or_profile")
        tick = relative_input["reference_tick"]
        if (
            type(tick) is not int
            or not 0 <= tick <= 85899
            or type(private_source["reference_tick"]) is not int
            or private_source["reference_tick"] != tick
            or fixture_state.timestamp_us != tick * 50000
        ):
            return stop("reference_clock_mismatch")
        decoded = decode_state(host_frame)
        for field in (
            "velocity_m_s",
            "angular_velocity_rad_s",
            "goal_m",
            "battery_fraction",
        ):
            original = np.asarray(getattr(fixture_state, field), dtype=np.float64)
            restored = np.asarray(getattr(decoded, field), dtype=np.float64)
            if original.tobytes() != restored.tobytes():
                result["host_changed_fields"] += (field,)
        if result["host_changed_fields"]:
            return stop("host_round_trip_changed")
        if type(private_source["host_frame"]) is not bytes or (
            private_source["host_frame"] != host_frame
        ):
            return stop("private_host_frame_mismatch", "inconsistent_source_record")
        if _c1_source_binding_digest(
            asdict(fixture_state)
        ) != _c1_source_binding_digest(private_source["fixture_state"]):
            return stop("private_host_state_mismatch", "inconsistent_source_record")
        velocity = _c1_array(fixture_state.velocity_m_s, (3,))
        angular = _c1_array(fixture_state.angular_velocity_rad_s, (3,))
        host_goal = _c1_array(fixture_state.goal_m, (3,))
        if (
            fixture_state.validity & 7 != 7
            or fixture_state.ages_us[:3] != (0, 0, 0)
            or np.any(velocity[1:])
            or np.any(angular[:2])
            or host_goal[2] != 0
            or not 0 <= velocity[0] <= config.max_speed
            or abs(angular[2]) > config.max_turn_rate
        ):
            return stop("unsupported_fixture_host_state")
        goal_body = _c1_array(relative_input["fixture_goal_body_m"], (2,))
        if not np.array_equal(host_goal[:2], goal_body):
            return stop("host_goal_binding_mismatch", "inconsistent_source_record")
        reference = _c1_array(private_source["reference_pose_m_rad"], (3,))
        world_goal = _c1_array(private_source["fixture_goal_m"], (2,))
        yaw = math.atan2(math.sin(reference[2]), math.cos(reference[2]))
        cosine, sine = math.cos(yaw), math.sin(yaw)
        delta_x, delta_y = world_goal - reference[:2]
        if not np.array_equal(
            goal_body,
            [delta_x * cosine + delta_y * sine, delta_y * cosine - delta_x * sine],
        ):
            return stop("unresolved_goal_registration")
        arena = _c1_array(
            [private_source["arena_yaw_rad"], relative_input["fixture_arena_yaw_rad"]],
            (2,),
        )
        if arena[0] != 0 or arena[1] != -yaw:
            return stop("arena_axis_mismatch", "inconsistent_source_record")
        history, source_history = relative_input["history"], private_source["history"]
        if (
            type(history) is not list
            or type(source_history) is not list
            or not 1 <= len(history) == len(source_history) <= 8
        ):
            return stop("unsupported_source_history")
        previous = None
        capture_ids = {}
        scale = max(1.0, config.max_range, *np.abs(reference), *np.abs(world_goal))
        relative_scale = max(1.0, *np.abs(goal_body))
        for index, (record, event) in enumerate(
            zip(history, source_history, strict=True)
        ):
            if type(event) is not dict or set(event) != {
                "clock_epoch",
                "capture_id",
                "delivery_tick",
                "snapshot_tick",
                "capture",
            }:
                return stop("missing_capture_lineage")
            if type(record) is not dict or set(record) != {
                "capture_ticks",
                "capture_poses_body_m_rad",
                "tof_m",
                "tof_valid",
            }:
                return stop("unsupported_candidate_capture")
            capture = event["capture"]
            if type(capture) is not dict or set(capture) != {
                "schema",
                "allowed_use",
                "training_approved",
                "real_input_qualified",
                "free_space_qualified",
                "config",
                "capture_ticks",
                "capture_poses_m_rad",
                "tof_m",
                "tof_valid",
            }:
                return stop("unsupported_private_capture")
            if (
                capture["schema"] != C1_SCHEMA
                or capture["allowed_use"] != "synthetic_visibility_fixtures_only"
                or any(
                    capture[key] is not False
                    for key in (
                        "training_approved",
                        "real_input_qualified",
                        "free_space_qualified",
                    )
                )
                or _c1_source_binding_digest(capture["config"]) != config_digest
            ):
                return stop("private_capture_profile_mismatch")
            ticks = _c1_array(capture["capture_ticks"], (8,), "iu")
            poses = _c1_array(capture["capture_poses_m_rad"], (8, 3))
            ranges = _c1_array(capture["tof_m"], (8, 8, 8), "f")
            valid = _c1_array(capture["tof_valid"], (8, 8, 8), "b")
            captured = int(ticks[0])
            snapshot = tick - len(history) + 1 + index
            due = snapshot - config.latency_ticks
            expected_capture = due - (due % 4 == 1)
            if (
                event["clock_epoch"] != private_source["clock_epoch"]
                or type(event["snapshot_tick"]) is not int
                or event["snapshot_tick"] != snapshot
                or type(event["delivery_tick"]) is not int
                or event["delivery_tick"] != captured + config.latency_ticks
                or captured != expected_capture
                or not np.all(ticks == captured)
                or ticks.dtype != np.uint32
                or not np.all(poses == poses[0])
                or ranges.dtype != np.float32
                or np.any(valid & ((ranges <= 0) | (ranges >= config.max_range)))
                or np.any(~valid & (ranges != 0))
            ):
                return stop(
                    "capture_clock_or_payload_mismatch", "inconsistent_source_record"
                )
            capture_id = event["capture_id"]
            if type(capture_id) is not str or not capture_id:
                return stop("missing_capture_identity")
            if capture_id in capture_ids and capture_ids[capture_id] != captured:
                return stop("reused_capture_identity", "inconsistent_source_record")
            capture_ids[capture_id] = captured
            fingerprint = _c1_source_binding_digest(capture)
            if (
                previous is not None
                and captured == previous[0]
                and (capture_id != previous[1] or fingerprint != previous[2])
            ):
                return stop("held_capture_changed", "inconsistent_source_record")
            previous = captured, capture_id, fingerprint
            for key in ("capture_ticks", "tof_m", "tof_valid"):
                shape = (8,) if key == "capture_ticks" else (8, 8, 8)
                kinds = (
                    "iu"
                    if key == "capture_ticks"
                    else "b"
                    if key == "tof_valid"
                    else "f"
                )
                candidate = _c1_array(record[key], shape, kinds)
                if _c1_source_binding_digest(candidate) != _c1_source_binding_digest(
                    capture[key]
                ):
                    return stop(
                        "candidate_payload_mismatch", "inconsistent_source_record"
                    )
            relative_poses = _c1_array(record["capture_poses_body_m_rad"], (8, 3))
            delta_x, delta_y = poses[0, :2] - reference[:2]
            acquired = math.atan2(math.sin(poses[0, 2]), math.cos(poses[0, 2]))
            heading = math.atan2(math.sin(acquired - yaw), math.cos(acquired - yaw))
            expected_pose = [
                delta_x * cosine + delta_y * sine,
                delta_y * cosine - delta_x * sine,
                heading,
            ]
            if relative_poses.dtype != np.float64 or not np.all(
                relative_poses == expected_pose
            ):
                return stop("unresolved_capture_registration")
            scale = max(scale, float(np.abs(poses).max()))
            relative_scale = max(relative_scale, float(np.abs(relative_poses).max()))
        declared_scale = _c1_array([relative_input["numerical_source_scale"]], (1,))[0]
        if declared_scale != max(scale, relative_scale):
            return stop("numerical_source_scale_mismatch", "inconsistent_source_record")
        if 1024 * np.finfo(float).eps * declared_scale >= config.radius:
            return stop("unsupported_numerical_scale")
        scene = private_source["scenario"]
        if type(scene) is not dict or set(scene) != {
            "name",
            "bounds",
            "start",
            "goal",
            "obstacles",
            "obstacle_heights",
        }:
            return stop("unsupported_private_domain")
        bounds = _c1_array(scene["bounds"], (2,))
        _c1_array(scene["start"], (3,))
        _c1_array(scene["goal"], (2,))
        obstacles = (
            _c1_array(scene["obstacles"], (len(scene["obstacles"]), 3))
            if scene["obstacles"]
            else np.empty((0, 3))
        )
        heights = (
            _c1_array(scene["obstacle_heights"], (len(obstacles),))
            if scene["obstacle_heights"]
            else np.full(len(obstacles), config.obstacle_height)
        )
        if (
            np.any(bounds <= 2 * config.radius)
            or np.any((obstacles[:, 2] < 0.05) | (obstacles[:, 2] > 0.30))
            or np.any((heights < 0.05) | (heights > 1.0))
            or config.wall_height != 1.0
        ):
            return stop("private_domain_not_established")
        guard = 256 * np.finfo(float).eps * max(scale, *bounds, 1.0)
        clearances = [
            *reference[:2] - config.radius,
            *(bounds - reference[:2] - config.radius),
        ]
        clearances.extend(
            math.hypot(center_x - reference[0], center_y - reference[1])
            - radius
            - config.radius
            for center_x, center_y, radius in obstacles
        )
        if min(clearances) <= guard:
            return stop("private_body_clearance_not_established")
    except (KeyError, TypeError, ValueError, OverflowError):
        return stop("malformed_private_source_or_candidate")
    result.update(
        status="consistent_under_fixture_assumptions",
        reason="bound_ideal_source_records_only",
    )
    return result


def prepare_synthetic_c1_relative_input(
    history,
    *,
    reference_tick,
    reference_pose_m_rad,
    fixture_goal_m,
    config=None,
    synthetic_test_only=False,
):
    """Convert existing exact fixtures, not observations, to a relative boundary."""
    if synthetic_test_only is not True:
        raise ValueError("C1 relative input requires synthetic_test_only=True")
    config = _c1_config(config)
    reference = _c1_array(reference_pose_m_rad, (3,)).astype(float)
    goal = _c1_array(fixture_goal_m, (2,)).astype(float)
    result = {
        "schema": "micro-classifier/synthetic-c1-relative-input/1",
        "allowed_use": "controlled_synthetic_qualification_only",
        "training_approved": False,
        "real_input_qualified": False,
        "free_space_qualified": False,
        "numerically_certified": False,
        "status": "unknown",
        "reason": "unsupported_history",
        "reference_tick": reference_tick,
        "config": asdict(config),
        "history": [],
        "fixture_goal_body_m": None,
        "fixture_arena_yaw_rad": None,
        "numerical_source_scale": None,
    }
    inspection = inspect_synthetic_c1_history(
        history,
        reference_tick=reference_tick,
        reference_pose_m_rad=reference,
        config=config,
        synthetic_test_only=True,
    )
    if inspection["status"] != "registered_fixture":
        result["reason"] = inspection["reason"]
        return result
    scale = max(
        1.0,
        config.max_range,
        *np.abs(reference),
        *np.abs(goal),
        *(float(np.abs(record["capture_poses_m_rad"]).max()) for record in history),
    )
    result["numerical_source_scale"] = scale
    if 256 * np.finfo(float).eps * scale >= config.radius:
        result["reason"] = "unsupported_numerical_scale"
        return result
    yaw = math.atan2(math.sin(reference[2]), math.cos(reference[2]))
    rotation = np.array(
        [[math.cos(yaw), -math.sin(yaw)], [math.sin(yaw), math.cos(yaw)]]
    )
    with np.errstate(over="ignore", invalid="ignore"):
        relative_goal = (goal - reference[:2]) @ rotation
        for record in history:
            poses = record["capture_poses_m_rad"]
            headings = np.arctan2(np.sin(poses[:, 2]), np.cos(poses[:, 2])) - yaw
            relative_poses = np.column_stack(
                (
                    (poses[:, :2] - reference[:2]) @ rotation,
                    np.arctan2(np.sin(headings), np.cos(headings)),
                )
            )
            if not np.all(np.isfinite(relative_poses)):
                result.update(history=[], reason="unsupported_relative_coordinates")
                return result
            result["history"].append(
                {
                    "capture_ticks": record["capture_ticks"].copy(),
                    "capture_poses_body_m_rad": relative_poses,
                    "tof_m": record["tof_m"].copy(),
                    "tof_valid": record["tof_valid"].copy(),
                }
            )
    if not np.all(np.isfinite(relative_goal)):
        result.update(history=[], reason="unsupported_relative_coordinates")
        return result
    result.update(
        status="relative_fixture",
        reason="declared_exact_relative_fixture_only",
        fixture_goal_body_m=relative_goal.tolist(),
        fixture_arena_yaw_rad=-yaw,
        numerical_source_scale=max(
            scale,
            float(np.abs(relative_goal).max()),
            *(
                float(np.abs(record["capture_poses_body_m_rad"]).max())
                for record in result["history"]
            ),
        ),
    )
    return result


def probe_synthetic_c1_relative_questions(
    relative_input,
    *,
    fixture_state,
    fixture_current_body_clear=False,
    fixture_controlled_envelope=False,
    fixture_transform_error_m=0.0,
    fixture_heading_error_rad=0.0,
    fixture_clock_error_s=0.0,
    curved_segments=16,
    max_cells=32768,
    max_depth=10,
    radius_bands=8,
    config=None,
    synthetic_test_only=False,
):
    """Compare declared exact relative fixtures, never consume a live host state."""
    from interface.protocol import State, encode_state

    if synthetic_test_only is not True:
        raise ValueError("C1 relative questions require synthetic_test_only=True")
    config = _c1_config(config)
    errors = _c1_array(
        [fixture_transform_error_m, fixture_heading_error_rad, fixture_clock_error_s],
        (3,),
    )
    if np.any(errors < 0):
        raise ValueError("C1 fixture errors must be nonnegative")
    for value, lower, upper in (
        (curved_segments, 1, 128),
        (max_cells, 0, 65536),
        (max_depth, 0, 12),
        (radius_bands, 1, 16),
    ):
        if type(value) is not int or not lower <= value <= upper:
            raise ValueError("C1 relative work controls require bounded integers")
    result = {
        "schema": "micro-classifier/synthetic-c1-relative-questions/1",
        "allowed_use": "controlled_synthetic_qualification_only",
        "training_approved": False,
        "real_input_qualified": False,
        "free_space_qualified": False,
        "numerically_certified": False,
        "status": "unknown",
        "reason": "unsupported_relative_input",
        "candidate_values": {
            "path_blocked": None,
            "clear_sector": None,
            "speed_tier": None,
        },
        "queries": {},
        "unique_motion_queries": 0,
        "numerical_source_scale": None,
        "canonical_guard_scale": None,
    }
    if np.any(errors):
        result["reason"] = "unqualified_transform_or_clock_error"
        return result
    if not isinstance(relative_input, dict) or set(relative_input) != {
        "schema",
        "allowed_use",
        "training_approved",
        "real_input_qualified",
        "free_space_qualified",
        "numerically_certified",
        "status",
        "reason",
        "reference_tick",
        "config",
        "history",
        "fixture_goal_body_m",
        "fixture_arena_yaw_rad",
        "numerical_source_scale",
    }:
        return result
    if (
        relative_input["schema"] != "micro-classifier/synthetic-c1-relative-input/1"
        or relative_input["allowed_use"] != result["allowed_use"]
        or any(
            relative_input[key] is not False
            for key in (
                "training_approved",
                "real_input_qualified",
                "free_space_qualified",
                "numerically_certified",
            )
        )
    ):
        return result
    if relative_input["status"] != "relative_fixture":
        result["reason"] = relative_input["reason"]
        return result
    if not isinstance(fixture_state, State):
        raise TypeError("C1 fixture_state must be a synthetic State")
    encode_state(fixture_state)
    tick = relative_input["reference_tick"]
    if type(tick) is not int or not 0 <= tick <= 0xFFFFFFFF:
        raise ValueError("C1 reference tick requires a u32 integer")
    if (
        fixture_state.validity & 7 != 7
        or fixture_state.ages_us[:3] != (0, 0, 0)
        or fixture_state.timestamp_us != tick * 50000
    ):
        result["reason"] = "unsupported_host_validity_age_or_clock"
        return result
    velocity = _c1_array(fixture_state.velocity_m_s, (3,))
    angular = _c1_array(fixture_state.angular_velocity_rad_s, (3,))
    goal = _c1_array(fixture_state.goal_m, (3,))
    if np.any(velocity[1:]) or np.any(angular[:2]) or goal[2] != 0:
        result["reason"] = "unsupported_nonplanar_host_state"
        return result
    if not np.array_equal(
        goal[:2], _c1_array(relative_input["fixture_goal_body_m"], (2,))
    ):
        result["reason"] = "fixture_goal_binding_mismatch"
        return result
    if (
        not 0 <= velocity[0] <= config.max_speed
        or abs(angular[2]) > config.max_turn_rate
    ):
        raise ValueError("C1 fixture motion exceeds the simulated limits")
    if (
        fixture_current_body_clear is not True
        or fixture_controlled_envelope is not True
    ):
        result["reason"] = "fixture_body_or_domain_not_established"
        return result
    if json.dumps(
        relative_input["config"], sort_keys=True, allow_nan=False
    ) != json.dumps(asdict(config), sort_keys=True, allow_nan=False):
        return result
    scale, arena_yaw = map(
        float,
        _c1_array(
            [
                relative_input["numerical_source_scale"],
                relative_input["fixture_arena_yaw_rad"],
            ],
            (2,),
        ),
    )
    if scale < max(1, config.max_range, *np.abs(goal)) or abs(arena_yaw) > math.pi:
        return result
    result["numerical_source_scale"] = scale
    if 1024 * np.finfo(float).eps * scale >= config.radius:
        result["reason"] = "unsupported_numerical_scale"
        return result
    anchor = math.ldexp(1.0, math.frexp(scale)[1] + 2)
    result.update(numerical_source_scale=scale, canonical_guard_scale=anchor)
    if 256 * np.finfo(float).eps * anchor >= config.radius:
        result["reason"] = "unsupported_numerical_scale"
        return result
    yaw = -arena_yaw
    rotation = np.array(
        [[math.cos(yaw), math.sin(yaw)], [-math.sin(yaw), math.cos(yaw)]]
    )
    history = relative_input["history"]
    if not isinstance(history, (list, tuple)) or not 1 <= len(history) <= 8:
        return result
    canonical = []
    for record in history:
        if not isinstance(record, dict) or set(record) != {
            "capture_ticks",
            "capture_poses_body_m_rad",
            "tof_m",
            "tof_valid",
        }:
            return result
        poses = _c1_array(record["capture_poses_body_m_rad"], (8, 3)).astype(float)
        if np.abs(poses).max() > scale or np.any(np.abs(poses[:, 2]) > math.pi):
            return result
        world_poses = np.column_stack(
            (
                anchor + poses[:, :2] @ rotation,
                poses[:, 2] + yaw,
            )
        )
        canonical.append(
            {
                "schema": C1_SCHEMA,
                "allowed_use": "synthetic_visibility_fixtures_only",
                "training_approved": False,
                "real_input_qualified": False,
                "free_space_qualified": False,
                "config": asdict(config),
                "capture_ticks": record["capture_ticks"],
                "capture_poses_m_rad": world_poses,
                "tof_m": record["tof_m"],
                "tof_valid": record["tof_valid"],
            }
        )
    inspection = inspect_synthetic_c1_history(
        canonical,
        reference_tick=tick,
        reference_pose_m_rad=[anchor, anchor, yaw],
        config=config,
        synthetic_test_only=True,
    )
    if inspection["status"] != "registered_fixture":
        result["reason"] = inspection["reason"]
        return result
    age = inspection["latest_age_ticks"] * config.dt
    motion_guard = 64 * np.finfo(float).eps
    if (
        math.hypot(*poses[0, :2]) > config.max_speed * age + motion_guard
        or abs(poses[0, 2]) > config.max_turn_rate * age + motion_guard
    ):
        result["reason"] = "unsupported_capture_to_reference_motion"
        return result
    world_goal = anchor + goal[:2] @ rotation
    evidence = probe_synthetic_c1_questions(
        canonical,
        reference_tick=tick,
        reference_pose_m_rad=[anchor, anchor, yaw],
        speed=float(velocity[0]),
        turn_rate=float(angular[2]),
        fixture_goal_m=world_goal,
        current_body_clear=True,
        controlled_envelope=True,
        curved_segments=curved_segments,
        max_cells=max_cells,
        max_depth=max_depth,
        radius_bands=radius_bands,
        config=config,
        synthetic_test_only=True,
    )
    for key in (
        "status",
        "reason",
        "candidate_values",
        "queries",
        "unique_motion_queries",
    ):
        result[key] = evidence[key]
    if result["status"] != "inconsistent_fixture_evidence" and result["queries"]:
        states = {name: row["status"] for name, row in result["queries"].items()}
        names = ("centre", "left", "right")
        clear = [name for name in names if states[name] == "clear"]
        if (
            velocity[0] > 0
            and all(states[name] != "unknown" for name in names)
            and clear
        ):
            ranks = {}
            for name in clear:
                points, error = _c1_curved_centerline(
                    float(velocity[0]),
                    float(angular[2]),
                    age,
                    config,
                    curved_segments,
                    result["queries"][name]["braking_turn_rate_rad_s"],
                )
                ranks[name] = (
                    math.dist(points[-1], goal[:2]),
                    error
                    + 256 * np.finfo(float).eps * max(anchor, *np.abs(world_goal)),
                )
            best = min(clear, key=lambda name: ranks[name][0])
            upper = sum(ranks[best])
            contenders = [
                name
                for name, (distance, error) in ranks.items()
                if distance - error <= upper
            ]
            result["candidate_values"]["clear_sector"] = (
                best
                if len(contenders) == 1
                else "left"
                if set(contenders) == {"left", "right"}
                and angular[2] == 0
                and goal[1] == 0
                else None
            )
            count = sum(
                value is not None for value in result["candidate_values"].values()
            )
            result.update(
                status="resolved_under_fixture_assumptions"
                if count == 3
                else "partial_fixture_evidence",
                reason="conditional_candidate_values_only"
                if count == 3
                else "relative_goal_rank_unresolved",
            )
    return result


def _probe_synthetic_c1_wire_rejection(
    relative_input,
    *,
    fixture_state_frame,
    fixture_source_state,
    fixture_current_body_clear=False,
    fixture_controlled_envelope=False,
    fixture_transform_error_m=0.0,
    fixture_heading_error_rad=0.0,
    fixture_clock_error_s=0.0,
    curved_segments=16,
    max_cells=32768,
    max_depth=10,
    radius_bands=8,
    config=None,
    synthetic_test_only=False,
):
    """Serialize conditional fixture evidence as unusable rejection diagnostics."""
    import logging

    from interface.protocol import (
        RULES_QUESTIONS,
        Answer,
        Decision,
        ProtocolError,
        State,
        Status,
        decode_state,
        encode_decision,
        encode_state,
    )

    if synthetic_test_only is not True:
        raise ValueError("C1 wire diagnostics require synthetic_test_only=True")
    if type(fixture_source_state) is not State:
        raise TypeError("C1 wire diagnostics require a synthetic source State")
    source_frame = encode_state(fixture_source_state)
    state = None
    result = {
        "schema": "micro-classifier/synthetic-c1-wire-rejection/1",
        "allowed_use": "conditional_fixture_wire_diagnostics_only",
        "training_approved": False,
        "real_input_qualified": False,
        "free_space_qualified": False,
        "numerically_certified": False,
        "source_input_qualified": False,
        "host_command_admitted": False,
        "status": "rejection_diagnostics_only",
        "reason": "unsupported_fixture_state_frame",
        "candidate_values": {
            "path_blocked": None,
            "clear_sector": None,
            "speed_tier": None,
        },
        "evidence": None,
        "decision_frame": None,
    }

    def rejected(reason, status=Status.REJECT_OUT_OF_DOMAIN):
        answers = []
        for question, (_, options) in RULES_QUESTIONS.items():
            value = result["candidate_values"][question.name.lower()]
            if value is not None:
                selected = options.index(value)
                answers.append(
                    Answer(
                        question,
                        tuple(
                            float(index == selected) for index in range(len(options))
                        ),
                        selected,
                    )
                )
        decision = Decision(
            sequence=0 if state is None else state.sequence,
            timestamp_us=0 if state is None else state.timestamp_us,
            status=status,
            answers=tuple(answers),
        )
        result["reason"] = reason
        result["decision_frame"] = encode_decision(decision)
        return result

    if type(fixture_state_frame) is not bytes:
        return rejected(
            "unsupported_fixture_state_frame", Status.REJECT_UNSUPPORTED_SCHEMA
        )
    try:
        state = decode_state(fixture_state_frame)
    except ProtocolError:
        return rejected("invalid_fixture_state_frame", Status.REJECT_UNSUPPORTED_SCHEMA)
    if fixture_state_frame != source_frame:
        return rejected("fixture_state_frame_binding_mismatch")
    if (
        any(
            type(value) not in (int, float)
            for values in (
                fixture_source_state.velocity_m_s,
                fixture_source_state.angular_velocity_rad_s,
                fixture_source_state.goal_m,
            )
            for value in values
        )
        or state != fixture_source_state
    ):
        return rejected("decoded_fixture_state_changed")
    if state.validity & 7 != 7:
        return rejected("unsupported_fixture_host_validity")
    if state.ages_us[:3] != (0, 0, 0):
        return rejected("stale_fixture_host_state", Status.REJECT_STALE_INPUT)
    try:
        evidence = probe_synthetic_c1_relative_questions(
            relative_input,
            fixture_state=state,
            fixture_current_body_clear=fixture_current_body_clear,
            fixture_controlled_envelope=fixture_controlled_envelope,
            fixture_transform_error_m=fixture_transform_error_m,
            fixture_heading_error_rad=fixture_heading_error_rad,
            fixture_clock_error_s=fixture_clock_error_s,
            curved_segments=curved_segments,
            max_cells=max_cells,
            max_depth=max_depth,
            radius_bands=radius_bands,
            config=config,
            synthetic_test_only=True,
        )
        if (
            type(evidence) is not dict
            or evidence.get("schema")
            != "micro-classifier/synthetic-c1-relative-questions/1"
            or evidence.get("allowed_use") != "controlled_synthetic_qualification_only"
            or any(
                evidence.get(key) is not False
                for key in (
                    "training_approved",
                    "real_input_qualified",
                    "free_space_qualified",
                    "numerically_certified",
                )
            )
        ):
            return rejected("unsupported_fixture_question_result", Status.FAULT)
        candidates = evidence.get("candidate_values")
        if type(candidates) is not dict or set(candidates) != set(
            result["candidate_values"]
        ):
            return rejected("unsupported_fixture_question_result", Status.FAULT)
        for question, (_, options) in RULES_QUESTIONS.items():
            value = candidates[question.name.lower()]
            if value is not None and (type(value) is not str or value not in options):
                return rejected("unsupported_fixture_question_result", Status.FAULT)
        count = sum(value is not None for value in candidates.values())
        status = evidence.get("status")
        if status == "inconsistent_fixture_evidence":
            result["evidence"] = deepcopy(evidence)
            return rejected("inconsistent_fixture_evidence")
        if (
            (status == "unknown" and count != 0)
            or (status == "partial_fixture_evidence" and not 1 <= count <= 2)
            or (status == "resolved_under_fixture_assumptions" and count != 3)
            or status
            not in (
                "unknown",
                "partial_fixture_evidence",
                "resolved_under_fixture_assumptions",
            )
        ):
            return rejected("unsupported_fixture_question_result", Status.FAULT)
        result["evidence"] = deepcopy(evidence)
        result["candidate_values"] = deepcopy(candidates)
    except (TypeError, ValueError, KeyError, OverflowError):
        return rejected("unsupported_fixture_question_input")
    except Exception:
        logging.getLogger(__name__).exception(
            "Conditional C1 question evaluation failed"
        )
        return rejected("fixture_question_computation_failed", Status.FAULT)
    if evidence["reason"] == "stale_capture":
        return rejected("stale_fixture_capture", Status.REJECT_STALE_INPUT)
    return rejected("unqualified_fixture_evidence")


class DiagnosticRoverEnv(RoverEnv):
    """Keep acquisition references outside the unchanged student observations."""

    def reset(self, *, seed=0):
        self.capture_trace = {}
        return super().reset(seed=seed)

    def _sample(self):
        ranges = np.minimum(
            tof_ranges(self.position, self.yaw, self.scenario, self.config),
            self.config.max_range,
        )
        capture = {
            "tick": self.tick,
            "time_s": self.tick * self.config.dt,
            "pose_m_rad": [*self.position.tolist(), float(self.yaw)],
            "noiseless_ranges_m": (
                ranges[0] if self.config.tof_mount_height is None else ranges
            ).tolist(),
            "ray_geometry": "legacy_planar"
            if self.config.tof_mount_height is None
            else "synthetic_floor_cylinders_8x8",
        }
        super()._sample()
        self.capture_trace[self.tick] = capture


def diagnostic_sample(env, observation):
    """Compare delivered ranges with shared-model truth, not independent evidence."""
    if not isinstance(env, DiagnosticRoverEnv):
        raise TypeError("diagnostic sample requires a traced simulator")
    if (
        observation["tick"] != env.tick
        or observation["tof_sample_tick"] != env.sensor_tick
    ):
        raise ValueError("diagnostic observation does not match simulator tick")
    reference_pose = [*env.position.tolist(), float(env.yaw)]
    capture = env.capture_trace.get(env.sensor_tick)
    diagnostic = {
        "privileged": True,
        "allowed_use": "quarantined_simulator_diagnostics_only",
        "training_approved": False,
        "real_input_qualified": False,
        "physical_safety_claim": False,
        "status": "no_delivery" if capture is None else "delivered",
        "reference_time_s": env.tick * env.config.dt,
        "reference_pose_m_rad": reference_pose,
        "delivered_capture": None if capture is None else deepcopy(capture),
        "valid_surface_zones": 0,
        "invalid_zones": int((~observation["tof_valid"]).sum()),
        "valid_clipped_zones": 0,
        "valid_reference_censored_zones": 0,
        "range_residual_m": None,
        "age_consistency_error_s": None,
        "unregistered_surface_displacement_m": None,
        "noiseless_registration_roundtrip_error_m": None,
    }
    if capture is not None:
        ranges = np.broadcast_to(np.asarray(capture["noiseless_ranges_m"]), (8, 8))
        observed, valid = observation["tof_m"], observation["tof_valid"]
        surface = (ranges > 0) & (ranges < env.config.max_range)
        unclipped = (observed > 0) & (observed < env.config.max_range)
        selected = valid & unclipped & surface
        diagnostic["valid_surface_zones"] = int(selected.sum())
        diagnostic["valid_clipped_zones"] = int((valid & ~unclipped).sum())
        diagnostic["valid_reference_censored_zones"] = int((valid & ~surface).sum())
        diagnostic["range_residual_m"] = [
            [
                float(observed[row, column] - ranges[row, column])
                if selected[row, column]
                else None
                for column in range(8)
            ]
            for row in range(8)
        ]
        sensor_points = (ranges[..., None] * tof_directions(0, env.config)).reshape(
            -1, 3
        )
        surface = surface.ravel()
        if env.config.tof_mount_height is None:
            sensor_points, surface = sensor_points[:8], surface[:8]
        acquisition_pose = capture["pose_m_rad"]
        cosine, sine = math.cos(acquisition_pose[2]), math.sin(acquisition_pose[2])
        world = (
            sensor_points[:, :2] @ np.array([[cosine, sine], [-sine, cosine]])
            + acquisition_pose[:2]
        )
        cosine, sine = math.cos(reference_pose[2]), math.sin(reference_pose[2])
        rotation = np.array([[cosine, -sine], [sine, cosine]])
        registered = (world - reference_pose[:2]) @ rotation
        restored = registered @ rotation.T + reference_pose[:2]
        diagnostic["unregistered_surface_displacement_m"] = [
            float(np.linalg.norm(sensor_points[column, :2] - registered[column]))
            if surface[column]
            else None
            for column in range(len(surface))
        ]
        diagnostic["noiseless_registration_roundtrip_error_m"] = [
            float(np.linalg.norm(restored[column] - world[column]))
            if surface[column]
            else None
            for column in range(len(surface))
        ]
        diagnostic["age_consistency_error_s"] = float(
            observation["tof_age_s"] - (observation["time_s"] - capture["time_s"])
        )
    return {"kind": "sample", "observation": observation, "diagnostic": diagnostic}


def collect_diagnostic_episode(scene, *, seed, ticks=32):
    """Collect a bounded diagnostic prefix without changing Config's horizon."""
    if scene not in SCENES:
        raise ValueError("diagnostic scene must be a known simulator scene")
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError("diagnostic seed must be a nonnegative integer")
    if isinstance(ticks, bool) or not isinstance(ticks, int) or not 1 <= ticks <= 32:
        raise ValueError("diagnostic collection requires 1 to 32 ticks")
    env = DiagnosticRoverEnv(Config(), make_scenario(scene, seed))
    observation, info = env.reset(seed=seed)
    records = [
        {
            "kind": "metadata",
            "schema": "micro-classifier/sensor-diagnostic-episode/1",
            "seed": seed,
            "scene": scene,
            "config": asdict(env.config),
            "scenario": asdict(env.scenario),
            "tick_limit": ticks,
            "policy": "diagnostic_turn_schedule/1",
            "policy_description": "Max-speed command; +max_turn_rate/3 before tick 16, negative thereafter.",
            "allowed_use": "quarantined_simulator_diagnostics_only",
            "training_approved": False,
            "reviewed": False,
            "family_group": None,
            "partition": None,
            "reference_independence": "shared_simulator_geometry_and_ray_model",
            "physical_metrology": False,
            "task_labels": False,
        },
        diagnostic_sample(env, observation),
    ]
    terminated = truncated = False
    for _ in range(ticks):
        action = [
            env.config.max_speed,
            env.config.max_turn_rate / 3 * (1 if env.tick < 16 else -1),
        ]
        observation, _, terminated, truncated, info = env.step(action)
        records.append(diagnostic_sample(env, observation))
        if terminated or truncated:
            break
    summary = {
        "kind": "summary",
        "ticks": env.tick,
        "observations": env.tick + 1,
        "collision": bool(info["collision"]),
        "success": bool(info["success"]),
        "environment_timeout": bool(truncated),
        "censored": not (terminated or truncated),
        "stop_reason": "environment_end"
        if terminated or truncated
        else "diagnostic_horizon",
    }
    records.append(summary)
    return records, summary


def _statistics(values):
    values = np.asarray(values, dtype=float)
    return {
        "count": int(values.size),
        "mean_m": float(values.mean()) if values.size else None,
        "rms_m": float(np.sqrt(np.mean(values * values))) if values.size else None,
        "observed_max_abs_m": float(np.max(np.abs(values))) if values.size else None,
    }


def summarize_diagnostics(records):
    """Summarize conditional observed values, never fit or accept error bounds."""
    samples = [record["diagnostic"] for record in records if record["kind"] == "sample"]
    residuals, ages, displacement, roundtrip = [], [], [], []
    for sample in samples:
        if sample["range_residual_m"] is not None:
            residuals.extend(
                value
                for row in sample["range_residual_m"]
                for value in row
                if value is not None
            )
        if sample["age_consistency_error_s"] is not None:
            ages.append(sample["age_consistency_error_s"])
        for name, destination in (
            ("unregistered_surface_displacement_m", displacement),
            ("noiseless_registration_roundtrip_error_m", roundtrip),
        ):
            if sample[name] is not None:
                destination.extend(value for value in sample[name] if value is not None)
    return {
        "observations": len(samples),
        "no_delivery_observations": sum(
            sample["status"] == "no_delivery" for sample in samples
        ),
        "invalid_zones": sum(sample["invalid_zones"] for sample in samples),
        "valid_clipped_zones": sum(sample["valid_clipped_zones"] for sample in samples),
        "valid_reference_censored_zones": sum(
            sample["valid_reference_censored_zones"] for sample in samples
        ),
        "exclusion_counters_overlap": True,
        "range_residual_m": _statistics(residuals),
        "age_consistency_error_s": {
            "count": len(ages),
            "observed_max_abs_s": max(map(abs, ages), default=None),
        },
        "unregistered_surface_displacement_m": _statistics(displacement),
        "noiseless_registration_roundtrip_error_m": _statistics(roundtrip),
    }


def _observation_digest(records):
    digest = hashlib.sha256()
    for record in records:
        if record["kind"] == "sample":
            digest.update(
                (
                    json.dumps(
                        record["observation"],
                        default=json_value,
                        sort_keys=True,
                        separators=(",", ":"),
                        allow_nan=False,
                    )
                    + "\n"
                ).encode()
            )
    return digest.hexdigest()


def run_diagnostic_study(output_dir, report_path, *, seed, ticks=32, scenes=SCENES):
    """Write at most four fresh diagnostic prefixes and a non-label report."""
    scenes = tuple(scenes)
    if (
        not 1 <= len(scenes) <= 4
        or len(set(scenes)) != len(scenes)
        or any(scene not in SCENES for scene in scenes)
    ):
        raise ValueError("study requires 1 to 4 distinct known scenes")
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError("diagnostic seed must be a nonnegative integer")
    if isinstance(ticks, bool) or not isinstance(ticks, int) or not 1 <= ticks <= 32:
        raise ValueError("diagnostic collection requires 1 to 32 ticks")
    output_dir, report_path = Path(output_dir), Path(report_path)
    if (
        output_dir.exists()
        or output_dir.is_symlink()
        or report_path.exists()
        or report_path.is_symlink()
    ):
        raise FileExistsError("diagnostic outputs must be fresh")
    resolved_output, resolved_report = output_dir.resolve(), report_path.resolve()
    if resolved_report.is_relative_to(
        resolved_output
    ) or resolved_output.is_relative_to(resolved_report):
        raise ValueError("report and diagnostic episode directory must not overlap")
    output_dir.mkdir(parents=True, exist_ok=False)
    episodes, all_records = [], []
    for index, scene in enumerate(scenes):
        records, summary = collect_diagnostic_episode(
            scene, seed=seed + index, ticks=ticks
        )
        path = output_dir / f"{scene}.jsonl"
        write_episode(path, records)
        episodes.append(
            {
                "path": path.as_posix(),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "bytes": path.stat().st_size,
                "observation_sha256": _observation_digest(records),
                "scene": scene,
                "seed": seed + index,
                "summary": summary,
                "diagnostics": summarize_diagnostics(records),
            }
        )
        all_records.extend(records)
    report = {
        "schema": "micro-classifier/sensor-diagnostic-study/1",
        "allowed_use": "quarantined_simulator_diagnostics_only",
        "training_approved": False,
        "real_input_qualified": False,
        "physical_safety_claim": False,
        "physical_metrology": False,
        "reviewed": False,
        "accepted_bounds": False,
        "task_labels": 0,
        "accepted_family_assignments": 0,
        "locked_splits": False,
        "reference_independence": "shared_simulator_geometry_and_ray_model",
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "source_sha256": {
            "sim/diagnostics.py": hashlib.sha256(
                Path(__file__).read_bytes()
            ).hexdigest(),
            "sim/rover.py": hashlib.sha256(
                Path(__file__).with_name("rover.py").read_bytes()
            ).hexdigest(),
        },
        "episodes": episodes,
        "diagnostics": summarize_diagnostics(all_records),
        "limitations": [
            "Software-model diagnostics, not independent physical metrology or task truth.",
            "Residuals exclude missing, clipped and reference-censored zones; this selection biases noise statistics.",
            "Repeated vertical zones and temporally related captures are not independent trials.",
            "Round-trip consistency shares transforms/reference geometry; it is not measured registration accuracy.",
            "Observed maxima are not hard error bounds or probabilistic coverage claims.",
            "Horizon stops are censored; no navigation-success or physical safety qualification.",
            "No witness application, labels, accepted cohort/splits, teacher or student training.",
        ],
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("x") as stream:
        json.dump(report, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--ticks", type=int, default=32)
    args = parser.parse_args(argv)
    report = run_diagnostic_study(
        args.output_dir, args.report, seed=args.seed, ticks=args.ticks
    )
    print(
        json.dumps(
            {
                "episodes": len(report["episodes"]),
                "observations": report["diagnostics"]["observations"],
            }
        )
    )


if __name__ == "__main__":
    main()
