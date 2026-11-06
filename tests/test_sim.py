import hashlib
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
    validate_observation,
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
    tof_directions,
    tof_ranges,
    with_wire_frames,
    write_episode,
)


@pytest.mark.parametrize(
    "case",
    (
        "straight",
        "bend",
        "enlarged_tube",
        "hidden_contact",
        "no_prefixes",
        "body_unknown",
        "cell_budget",
        "depth_budget",
        "small_query_bound",
        "small_radius",
        "boolean_radius",
        "nonfinite_radius",
    ),
)
def test_synthetic_c1_path_cells_exclude_complete_prefix_fixture(monkeypatch, case):
    from sim import diagnostics

    def forbidden(*args, **kwargs):
        raise AssertionError("path-cell fixtures must not query C1 or compute motion")

    for name in (
        "_c1_curved_centerline",
        "probe_synthetic_c1_enclosure",
        "_probe_synthetic_c1_discrete_motion",
    ):
        monkeypatch.setattr(diagnostics, name, forbidden)
    ordinates = np.linspace(-1.0, 1.0, 81)
    segments = np.array([[[-1.0, value], [1.0, value]] for value in ordinates])
    path = np.array([[0.0, 0.0], [0.15, 0.0]])
    radius = 0.18
    settings = {"current_body_clear": True, "guard": 1e-12}
    if case == "bend":
        path = np.array([[0.0, 0.0], [0.1, 0.04], [0.15, 0.06]])
    elif case == "enlarged_tube":
        radius = 0.25
    elif case == "hidden_contact":
        for index, ordinate in enumerate(ordinates):
            if abs(ordinate) < 0.05:
                segments[index, 1, 0] = 0.3 - math.sqrt(0.05**2 - ordinate**2) - 1e-12
        assert 0.3 > 0.18 + 0.05
        assert 0.3 - path[-1, 0] < radius + 0.05
    elif case == "no_prefixes":
        segments = np.empty((0, 2, 2))
    elif case == "body_unknown":
        settings["current_body_clear"] = False
    elif case == "cell_budget":
        settings["max_cells"] = 0
    elif case == "depth_budget":
        settings["max_depth"] = 0
    elif case == "small_query_bound":
        settings["query_bound"] = 0.125
    elif case == "small_radius":
        radius = 0.125
    elif case == "boolean_radius":
        radius = True
    elif case == "nonfinite_radius":
        radius = float("nan")
    original_segments, original_path = segments.copy(), path.copy()
    if case in (
        "small_query_bound",
        "small_radius",
        "boolean_radius",
        "nonfinite_radius",
    ):
        with pytest.raises(ValueError):
            diagnostics._c1_exclude_path_cells(segments, path, radius, **settings)
    else:
        result = diagnostics._c1_exclude_path_cells(segments, path, radius, **settings)
        clear = case in ("straight", "bend", "enlarged_tube")
        assert result["fixture_enclosure_excluded"] is clear
        reasons = {
            "hidden_contact": "unexcluded_center_cell",
            "no_prefixes": "no_low_height_free_segments",
            "body_unknown": "current_body_clear_not_established",
            "cell_budget": "cell_budget_exhausted",
            "depth_budget": "unexcluded_center_cell",
        }
        assert result["reason"] == (
            "all_allowed_cylinder_centers_excluded_from_path_tube"
            if clear
            else reasons[case]
        )
        assert 0 <= result["cells_checked"] <= settings.get("max_cells", 32768)
    np.testing.assert_array_equal(path, original_path)
    np.testing.assert_array_equal(segments, original_segments)


@pytest.mark.parametrize("case", range(16))
def test_synthetic_c1_source_intervals_bind_actual_wire(case, monkeypatch):
    import struct
    from dataclasses import replace
    from fractions import Fraction

    from interface.protocol import State, encode_state
    from sim import diagnostics

    source = State(
        sequence=22,
        timestamp_us=1100000,
        velocity_m_s=(0.5, 0.0, 0.0),
        goal_m=(3.0, 0.0, 0.0),
    )
    if case == 1:
        source = replace(source, velocity_m_s=(0.2, 0.0, 0.0))
    elif case == 2:
        source = replace(source, velocity_m_s=(0.35, 0.0, 0.0))
    elif case == 3:
        source = replace(source, velocity_m_s=(0.6, 0.0, 0.0))
    elif case == 4:
        source = replace(
            source, angular_velocity_rad_s=(0.0, 0.0, 0.2), goal_m=(-0.35, 0.2, 0.0)
        )
    elif case == 5:
        source = replace(source, velocity_m_s=(-0.0, 0.0, 0.0))
    elif case == 8:
        source = replace(source, ages_us=(50000, *source.ages_us[1:]))
    elif case == 9:
        source = replace(
            source,
            validity=6,
            velocity_m_s=(0.0, 0.0, 0.0),
            ages_us=(0xFFFFFFFF, *source.ages_us[1:]),
        )
    elif case == 13:
        source = replace(source, velocity_m_s=(math.ulp(0.0), 0.0, 0.0))
    elif case == 14:
        source = replace(source, goal_m=(2**53 + 1, 0.0, 0.0))
    frame = encode_state(source)
    if case == 6:
        frame = encode_state(replace(source, sequence=23))
    elif case == 7:
        frame = frame[:-1] + bytes([frame[-1] ^ 1])
    elif case == 12:
        frame = bytearray(frame)
    elif case == 15:
        source = replace(source, goal_m=(1 << 4096, 0.0, 0.0))
    settings = {
        "synthetic_test_only": case != 11,
        "max_integer_bits": 1 if case == 10 else 4096,
    }
    saved_source, saved_frame = source, deepcopy(frame)

    def forbidden(*args, **kwargs):
        raise AssertionError(
            "source-word fixtures must not inspect C1 or compute motion"
        )

    for name in (
        "inspect_synthetic_c1_history",
        "_probe_synthetic_c1_discrete_motion",
        "_probe_synthetic_c1_discrete_path_enclosure",
        "_probe_synthetic_c1_wire_rejection",
    ):
        monkeypatch.setattr(diagnostics, name, forbidden)
    if case == 11:
        with pytest.raises(ValueError, match="synthetic_test_only"):
            diagnostics._bind_synthetic_c1_state_intervals(source, frame, **settings)
    else:
        result = diagnostics._bind_synthetic_c1_state_intervals(
            source, frame, **settings
        )
        supported = case in (0, 1, 2, 3, 4, 5, 13)
        assert result["fixture_words_bound"] is supported
        assert result["component_pairs_checked"] <= 9
        for key in (
            "training_approved",
            "real_input_qualified",
            "numerically_certified",
            "source_qualified",
            "command_admission_qualified",
        ):
            assert result[key] is False
        if supported:
            assert result["state_frame"] == frame
            assert result["status"] == "bound_under_fixture_assumptions"
            for field in ("velocity_m_s", "angular_velocity_rad_s", "goal_m"):
                for value, record in zip(
                    getattr(source, field), result["fields"][field], strict=True
                ):
                    received = struct.unpack("<f", struct.pack("<f", value))[0]
                    lower, upper = (Fraction(*pair) for pair in record["interval"])
                    assert lower == min(Fraction(value), Fraction(received))
                    assert upper == max(Fraction(value), Fraction(received))
                    assert Fraction(*record["decoded_minus_source"]) == Fraction(
                        received
                    ) - Fraction(value)
                    assert record["source_hex"] == float(value).hex()
                    assert record["decoded_hex"] == received.hex()
            if case in (1, 2, 3):
                difference = Fraction(
                    *result["fields"]["velocity_m_s"][0]["decoded_minus_source"]
                )
                assert (difference > 0) is (case != 2)
            result["fields"]["velocity_m_s"][0]["interval"][0] = (123, 1)
        else:
            assert "fields" not in result and "state_frame" not in result
            reasons = {
                14: "source_integer_not_exact_binary64",
                15: "invalid_state_frame_or_source",
                6: "source_frame_binding_mismatch",
                7: "invalid_state_frame_or_source",
                8: "stale_host_state",
                9: "unsupported_host_validity",
                10: "source_integer_budget_exhausted",
                12: "unsupported_state_frame",
            }
            assert result["reason"] == reasons[case]
    assert source == saved_source and frame == saved_frame


@pytest.fixture(scope="module")
def c1_state_motion_ledger(request):
    ledger = dict.fromkeys(("bridge", "binding", "motion", "reference", "forbidden"), 0)
    yield ledger
    assert all(
        ledger[key] <= 32 for key in ("bridge", "binding", "motion", "reference")
    )
    assert ledger["forbidden"] == 0
    capture = request.config.pluginmanager.getplugin("capturemanager")
    if capture is None:
        print("C1 state-motion ledger:", json.dumps(ledger, sort_keys=True))
    else:
        with capture.global_and_fixture_disabled():
            print("C1 state-motion ledger:", json.dumps(ledger, sort_keys=True))


@pytest.mark.parametrize("case", range(16))
def test_synthetic_c1_state_motion_propagates_actual_frame(
    c1_state_motion_ledger, monkeypatch, case
):
    import struct
    from dataclasses import replace
    from fractions import Fraction

    from interface.protocol import State, encode_state
    from sim import diagnostics

    ledger = c1_state_motion_ledger
    for key, name in (
        ("binding", "_bind_synthetic_c1_state_intervals"),
        ("motion", "_probe_synthetic_c1_discrete_motion"),
    ):
        original = getattr(diagnostics, name)

        def counted(*args, _key=key, _original=original, **kwargs):
            ledger[_key] += 1
            assert ledger[_key] <= 32
            return _original(*args, **kwargs)

        monkeypatch.setattr(diagnostics, name, counted)

    def forbidden(*args, **kwargs):
        ledger["forbidden"] += 1
        raise AssertionError("state-motion bridge must not query C1 or execute a rover")

    for name in (
        "inspect_synthetic_c1_history",
        "capture_synthetic_c1_views",
        "_probe_synthetic_c1_discrete_path_enclosure",
        "_probe_synthetic_c1_wire_rejection",
        "_c1_curved_centerline",
    ):
        monkeypatch.setattr(diagnostics, name, forbidden)
    monkeypatch.setattr(RoverEnv, "reset", forbidden)
    monkeypatch.setattr(RoverEnv, "step", forbidden)
    speed, turn = (
        (0.2, 0.75) if case == 0 else (0.35, -0.75) if case == 1 else (0.5, 0.0)
    )
    if case == 3:
        speed = 0.0
    elif case == 4:
        speed = 0.6
    source = State(
        sequence=22,
        timestamp_us=1100000,
        velocity_m_s=(speed, 0.0, 0.0),
        goal_m=(3.0, 0.0, 0.0),
    )
    if case == 5:
        source = replace(source, velocity_m_s=(speed, math.ulp(0.0), 0.0))
    elif case == 6:
        source = replace(source, angular_velocity_rad_s=(0.01, 0.0, 0.0))
    elif case == 7:
        source = replace(source, goal_m=(3.0, 0.0, 0.01))
    elif case == 9:
        source = replace(source, timestamp_us=1150000)
    elif case == 11:
        source = replace(source, ages_us=(1, *source.ages_us[1:]))
    elif case == 12:
        source = replace(
            source, validity=23, faults=1, ages_us=(*source.ages_us[:4], 0)
        )
    frame = encode_state(source)
    if case == 10:
        frame = encode_state(replace(source, sequence=23))
    errors = {"position_error_m": 0.0, "heading_error_rad": 0.0, "profile_exact": True}
    if case == 13:
        errors = None
    settings = {
        "reference_tick": 22.0 if case == 8 else 22,
        "target_speed": 0.125 if case == 3 else 0.5,
        "turn_rate": turn,
        "error_evidence": errors,
        "max_braking_ticks": 0 if case == 14 else 16,
        "synthetic_test_only": case != 15,
    }
    saved_source, saved_errors = source, deepcopy(errors)
    before = dict(ledger)
    ledger["bridge"] += 1
    if case == 15:
        with pytest.raises(ValueError, match="synthetic_test_only"):
            diagnostics._probe_synthetic_c1_state_motion(source, frame, **settings)
        assert ledger["binding"] == before["binding"]
        assert ledger["motion"] == before["motion"]
    else:
        result = diagnostics._probe_synthetic_c1_state_motion(source, frame, **settings)
        supported = case in (0, 1, 2, 3)
        assert result["fixture_motion_enclosed"] is supported
        assert ledger["binding"] - before["binding"] == int(case != 8)
        assert ledger["motion"] - before["motion"] == int(case in (0, 1, 2, 3, 13, 14))
        assert result["work"] == {
            "binding_entries": int(case != 8),
            "motion_entries": int(case in (0, 1, 2, 3, 13, 14)),
        }
        for key in (
            "training_approved",
            "real_input_qualified",
            "free_space_qualified",
            "numerically_certified",
            "source_qualified",
            "native_execution_qualified",
            "command_admission_qualified",
        ):
            assert result[key] is False
        if supported:
            received = struct.unpack("<f", struct.pack("<f", speed))[0]
            assert result["initial_speed_interval_m_s"] == (
                min(speed, received),
                max(speed, received),
            )
            assert result["source_intervals"]["state_frame"] == frame
            assert result["status"] == "enclosed_from_bound_source_fixture"
            motion = result["motion"]
            if case in (0, 1):
                assert (
                    motion["command_speed_interval_m_s"][0]
                    < motion["command_speed_interval_m_s"][1]
                )
            for value in (speed, received):
                ledger["reference"] += 1
                reference = _c1_discrete_motion_reference(
                    {
                        "initial_speed": value,
                        "target_speed": settings["target_speed"],
                        "turn_rate": turn,
                    }
                )
                for index, box in enumerate(motion["centerline_boxes_m"]):
                    point = reference["vertices"][
                        min(index, len(reference["vertices"]) - 1)
                    ]
                    for coordinate, (lower, upper) in zip(point, box, strict=True):
                        assert (
                            Fraction(lower)
                            <= coordinate[0]
                            <= coordinate[1]
                            <= Fraction(upper)
                        )
            for key in (
                "training_approved",
                "real_input_qualified",
                "free_space_qualified",
                "numerically_certified",
                "source_qualified",
                "native_execution_qualified",
                "command_admission_qualified",
            ):
                assert motion[key] is False
            result["motion"]["centerline_boxes_m"][0][0][0] = 123.0
        else:
            reasons = {
                4: "source_interval_outside_motion_domain",
                5: "unsupported_planar_source_intervals",
                6: "unsupported_planar_source_intervals",
                7: "unsupported_planar_source_intervals",
                8: "unsupported_reference_tick",
                9: "frame_tick_binding_mismatch",
                10: "source_frame_binding_mismatch",
                11: "stale_host_state",
                12: "unsupported_host_task_or_faults",
                13: "error_evidence_missing",
                14: "braking_budget_exhausted",
            }
            assert result["reason"] == reasons[case]
            assert result["status"] == "unknown" and "motion" not in result
    assert source == saved_source and errors == saved_errors


@pytest.fixture(scope="module")
def c1_normal_motion_ledger(request):
    ledger = dict.fromkeys(
        (
            "wrapper",
            "mapper",
            "state_decode",
            "decision_decode",
            "bridge",
            "binding",
            "motion",
            "reference",
            "forbidden",
        ),
        0,
    )
    yield ledger
    assert all(
        ledger[key] <= (24 if key == "reference" else 32)
        for key in ledger
        if key != "forbidden"
    )
    assert ledger["forbidden"] == 0
    capture = request.config.pluginmanager.getplugin("capturemanager")
    if capture is None:
        print("C1 normal-motion ledger:", json.dumps(ledger, sort_keys=True))
    else:
        with capture.global_and_fixture_disabled():
            print("C1 normal-motion ledger:", json.dumps(ledger, sort_keys=True))


@pytest.mark.parametrize("case", range(24))
def test_synthetic_c1_normal_motion_uses_derived_frame_command(
    c1_normal_motion_ledger, monkeypatch, case
):
    import struct
    from dataclasses import replace
    from fractions import Fraction

    from interface.protocol import (
        RULES_QUESTIONS,
        Answer,
        Decision,
        State,
        Status,
        encode_decision,
        encode_state,
    )
    from sim import diagnostics, rules

    ledger = c1_normal_motion_ledger
    sector, tier = (case // 3, case % 3 + 1) if case < 9 else (0, 3)
    speed = 0.2 if case == 1 else 0.35 if case == 7 else 0.6 if case == 9 else 0.5
    source = State(
        sequence=22,
        timestamp_us=1100000,
        velocity_m_s=(speed, 0.0, 0.0),
        goal_m=(3.0, 1.0, 0.0),
    )
    if case == 11:
        source = replace(source, velocity_m_s=(speed, math.ulp(0.0), 0.0))
    elif case == 12:
        source = replace(source, ages_us=(1, *source.ages_us[1:]))
    frame = encode_state(source)
    if case == 10:
        source = replace(source, sequence=23)
    choices = (int(case == 16), sector, tier)
    answers = tuple(
        Answer(
            question,
            tuple(float(index == choice) for index in range(len(options))),
            choice,
        )
        for (question, (_, options)), choice in zip(
            RULES_QUESTIONS.items(), choices, strict=True
        )
    )
    decision = Decision(
        sequence=23 if case == 18 else 22,
        timestamp_us=1100000,
        status=Status.REJECT_OUT_OF_DOMAIN if case == 17 else Status.OK,
        answers=answers[:1] if case == 17 else answers,
    )
    decision_frame = encode_decision(decision)
    if case == 15:
        decision_frame = decision_frame[:-1] + bytes([decision_frame[-1] ^ 1])
    elif case == 21:
        frame = bytearray(frame)
    errors = (
        None
        if case == 13
        else {"position_error_m": 0.0, "heading_error_rad": 0.0, "profile_exact": True}
    )
    settings = {
        "reference_tick": True if case == 20 else 22,
        "config": Config(max_speed=0.5) if case == 19 else Config(),
        "error_evidence": errors,
        "max_braking_ticks": 0 if case == 14 else 16,
        "synthetic_test_only": case != 23,
    }
    if case == 22:
        settings["target_speed"] = 0.5
    saved = deepcopy((source, frame, decision_frame, settings))
    for key, module, name in (
        ("mapper", rules, "_map_synthetic_c1_normal_command"),
        ("state_decode", rules, "decode_state"),
        ("decision_decode", rules, "decode_decision"),
        ("bridge", diagnostics, "_probe_synthetic_c1_state_motion"),
        ("binding", diagnostics, "_bind_synthetic_c1_state_intervals"),
        ("motion", diagnostics, "_probe_synthetic_c1_discrete_motion"),
    ):
        original = getattr(module, name)

        def counted(*args, _key=key, _original=original, **kwargs):
            ledger[_key] += 1
            assert ledger[_key] <= 32
            return _original(*args, **kwargs)

        monkeypatch.setattr(module, name, counted)

    def forbidden(*args, **kwargs):
        ledger["forbidden"] += 1
        raise AssertionError(
            "normal motion must not select geometry, bypass mapping or execute a rover"
        )

    for name in (
        "inspect_synthetic_c1_history",
        "capture_synthetic_c1_views",
        "_probe_synthetic_c1_discrete_path_enclosure",
        "_probe_synthetic_c1_wire_rejection",
        "_c1_curved_centerline",
    ):
        monkeypatch.setattr(diagnostics, name, forbidden)
    for name in ("host_action", "wire_step", "decide", "run_diagnostics"):
        monkeypatch.setattr(rules, name, forbidden)
    monkeypatch.setattr(RoverEnv, "reset", forbidden)
    monkeypatch.setattr(RoverEnv, "step", forbidden)

    def check():
        ledger["wrapper"] += 1
        assert ledger["wrapper"] <= 32
        return diagnostics._probe_synthetic_c1_normal_state_motion(
            source, frame, decision_frame, **settings
        )

    before = dict(ledger)
    if case in (22, 23):
        with pytest.raises(
            TypeError if case == 22 else ValueError,
            match="target_speed" if case == 22 else "synthetic_test_only",
        ):
            check()
        assert (
            ledger["mapper"] == before["mapper"]
            and ledger["bridge"] == before["bridge"]
        )
    else:
        result = check()
        assert result["fixture_normal_motion_enclosed"] is (case < 9)
        assert ledger["mapper"] - before["mapper"] == int(case != 19)
        assert ledger["bridge"] - before["bridge"] == int(case < 15)
        assert ledger["binding"] - before["binding"] == int(case < 15)
        assert ledger["motion"] - before["motion"] == int(case < 9 or case in (13, 14))
        for flag in (
            "training_approved",
            "real_input_qualified",
            "free_space_qualified",
            "numerically_certified",
            "source_qualified",
            "native_execution_qualified",
            "command_admission_qualified",
        ):
            assert result[flag] is False
        if case < 9:
            assert result["status"] == "enclosed_from_mapped_active_frame_fixture"
            target, turn = Config().max_speed * tier / 3, (1.5, 0.0, -1.5)[sector]
            assert result["requested_command_words"] == {
                "target_speed_m_s": int.from_bytes(struct.pack(">d", target), "big"),
                "turn_rate_rad_s": int.from_bytes(struct.pack(">d", turn), "big"),
            }
            mapped = result["mapped_command"]
            assert (
                mapped["state_frame_hex"] == frame.hex()
                and mapped["decision_frame_hex"] == decision_frame.hex()
            )
            assert mapped["requested_command"] == {
                "target_speed_m_s": target,
                "turn_rate_rad_s": turn,
            }
            bridge = result["state_motion"]
            assert bridge["source_intervals"]["state_frame"] == frame
            received = struct.unpack("<f", struct.pack("<f", speed))[0]
            assert bridge["initial_speed_interval_m_s"] == (
                min(speed, received),
                max(speed, received),
            )
            motion = bridge["motion"]
            if case in (1, 7):
                assert (
                    motion["command_speed_interval_m_s"][0]
                    < motion["command_speed_interval_m_s"][1]
                )
            for value in (speed, received):
                ledger["reference"] += 1
                assert ledger["reference"] <= 24
                reference = _c1_discrete_motion_reference(
                    {"initial_speed": value, "target_speed": target, "turn_rate": turn}
                )
                for index, box in enumerate(motion["centerline_boxes_m"]):
                    point = reference["vertices"][
                        min(index, len(reference["vertices"]) - 1)
                    ]
                    for coordinate, (lower, upper) in zip(point, box, strict=True):
                        assert (
                            Fraction(lower)
                            <= coordinate[0]
                            <= coordinate[1]
                            <= Fraction(upper)
                        )
            if case == 0:
                preserved = deepcopy(result)
                mapped["requested_command"]["turn_rate_rad_s"] = 10.0
                motion["centerline_boxes_m"][0][0][0] = 123.0
                assert check() == preserved
        else:
            assert result["status"] == "unknown"
            assert (
                "mapped_command" not in result
                and "state_motion" not in result
                and "requested_command_words" not in result
            )
            assert (
                result["reason"]
                == {
                    9: "source_interval_outside_motion_domain",
                    10: "source_frame_binding_mismatch",
                    11: "unsupported_planar_source_intervals",
                    12: "stale_host_state",
                    13: "error_evidence_missing",
                    14: "braking_budget_exhausted",
                    15: "invalid_normal_frames",
                    16: "normal_selection_requests_braking",
                    17: "complete_active_ok_missing",
                    18: "normal_decision_binding_mismatch",
                    19: "unsupported_normal_motion_profile",
                    20: "unsupported_reference_tick",
                    21: "unsupported_normal_frames",
                }[case]
            )
    assert (source, frame, decision_frame, settings) == saved


@pytest.fixture(scope="module")
def c1_normal_request_ledger(request):
    ledger = dict.fromkeys(
        (
            "wrapper",
            "normal",
            "mapper",
            "state_decode",
            "decision_decode",
            "bridge",
            "binding",
            "motion",
            "digest",
            "forbidden",
        ),
        0,
    )
    yield ledger
    assert all(ledger[key] <= 32 for key in ledger if key != "forbidden")
    assert ledger["forbidden"] == 0
    capture = request.config.pluginmanager.getplugin("capturemanager")
    if capture is None:
        print("C1 normal-request ledger:", json.dumps(ledger, sort_keys=True))
    else:
        with capture.global_and_fixture_disabled():
            print("C1 normal-request ledger:", json.dumps(ledger, sort_keys=True))


@pytest.mark.parametrize("case", range(16))
def test_synthetic_c1_normal_request_freezes_declared_content(
    c1_normal_request_ledger, monkeypatch, case
):
    import hashlib
    import struct
    from dataclasses import asdict, replace

    from interface.protocol import (
        RULES_QUESTIONS,
        Answer,
        Decision,
        State,
        Status,
        encode_decision,
        encode_state,
    )
    from sim import diagnostics, rules

    ledger = c1_normal_request_ledger
    sector, tier = (case, case + 1) if case < 3 else (0, 3)
    speed = 0.2 if case == 1 else 0.35 if case == 2 else 0.5
    source = State(
        sequence=22,
        timestamp_us=1100000,
        velocity_m_s=(speed, 0.0, 0.0),
        goal_m=(3.0, 1.0, 0.0),
    )
    frame = encode_state(source)
    if case == 4:
        source = replace(source, sequence=23)
    choices = (int(case == 3), sector, tier)
    answers = tuple(
        Answer(
            question,
            tuple(float(index == choice) for index in range(len(options))),
            choice,
        )
        for (question, (_, options)), choice in zip(
            RULES_QUESTIONS.items(), choices, strict=True
        )
    )
    decision_frame = encode_decision(
        Decision(sequence=22, timestamp_us=1100000, status=Status.OK, answers=answers)
    )
    context = {
        "epoch": "a" * 32,
        "source_identity": "b" * 64,
        "c1_reference_identity": "c" * 64,
        "capture_tick": 20,
        "reference_tick": 22,
    }
    if case == 7:
        context["epoch"] = "A" * 32
    elif case == 8:
        context["source_identity"] = "x" * 64
    elif case == 9:
        context.pop("c1_reference_identity")
    elif case == 10:
        context["capture_tick"] = True
    elif case == 11:
        context["capture_tick"] = 23
    elif case == 12:
        context["capture_tick"] = 18
    elif case == 13:
        context["reference_tick"] = 23
    options = {
        "request_id": True if case == 5 else "d" * 31 if case == 6 else "d" * 32,
        "source_context": context,
        "reference_tick": 22,
        "error_evidence": {
            "position_error_m": 0.0,
            "heading_error_rad": 0.0,
            "profile_exact": True,
        },
        "synthetic_test_only": case != 15,
    }
    if case == 14:
        options["target_speed"] = 0.5
    saved = deepcopy((source, frame, decision_frame, options))
    for key, module, name in (
        ("normal", diagnostics, "_probe_synthetic_c1_normal_state_motion"),
        ("mapper", rules, "_map_synthetic_c1_normal_command"),
        ("state_decode", rules, "decode_state"),
        ("decision_decode", rules, "decode_decision"),
        ("bridge", diagnostics, "_probe_synthetic_c1_state_motion"),
        ("binding", diagnostics, "_bind_synthetic_c1_state_intervals"),
        ("motion", diagnostics, "_probe_synthetic_c1_discrete_motion"),
        ("digest", diagnostics, "_c1_source_binding_digest"),
    ):
        original = getattr(module, name)

        def counted(*args, _key=key, _original=original, **kwargs):
            ledger[_key] += 1
            assert ledger[_key] <= 32
            return _original(*args, **kwargs)

        monkeypatch.setattr(module, name, counted)

    def forbidden(*args, **kwargs):
        ledger["forbidden"] += 1
        raise AssertionError(
            "request preparation must not choose or attest a C1 capture, permit or actuation"
        )

    for name in (
        "inspect_synthetic_c1_history",
        "capture_synthetic_c1_views",
        "_probe_synthetic_c1_discrete_path_enclosure",
        "_probe_synthetic_c1_wire_rejection",
        "_audit_synthetic_c1_source_binding",
        "_c1_curved_centerline",
    ):
        monkeypatch.setattr(diagnostics, name, forbidden)
    for name in ("host_action", "wire_step", "decide", "run_diagnostics"):
        monkeypatch.setattr(rules, name, forbidden)
    monkeypatch.setattr(RoverEnv, "reset", forbidden)
    monkeypatch.setattr(RoverEnv, "step", forbidden)

    def check():
        ledger["wrapper"] += 1
        assert ledger["wrapper"] <= 32
        return diagnostics._prepare_synthetic_c1_normal_request(
            source, frame, decision_frame, **options
        )

    before = dict(ledger)
    if case in (14, 15):
        with pytest.raises(
            TypeError if case == 14 else ValueError,
            match="target_speed" if case == 14 else "synthetic_test_only",
        ):
            check()
        assert (
            ledger["normal"] == before["normal"]
            and ledger["digest"] == before["digest"]
        )
    else:
        result = check()
        assert result["fixture_request_prepared"] is (case < 3)
        assert ledger["normal"] - before["normal"] == int(case < 5)
        assert ledger["digest"] - before["digest"] == (4 if case < 3 else 0)
        assert result["request_id_uniqueness_qualified"] is False
        assert result["source_context_status"] == "declared_module_fixture_only"
        for flag in (
            "training_approved",
            "real_input_qualified",
            "free_space_qualified",
            "numerically_certified",
            "source_qualified",
            "native_execution_qualified",
            "command_admission_qualified",
        ):
            assert result[flag] is False
        if case < 3:
            record = result["request"]
            assert result["status"] == "prepared_declared_normal_request_fixture"
            assert record["request_id"] == options["request_id"]
            assert (
                record["phase"] == "NORMAL"
                and record["application_tick"] == 22
                and record["hold_ticks"] == 1
            )
            assert record["source_context"] == context and record[
                "config_record"
            ] == asdict(Config())
            assert (
                record["state_frame_hex"] == frame.hex()
                and record["decision_frame_hex"] == decision_frame.hex()
            )
            assert record["command_words"] == {
                "target_speed_m_s": int.from_bytes(
                    struct.pack(">d", Config().max_speed * tier / 3), "big"
                ),
                "turn_rate_rad_s": int.from_bytes(
                    struct.pack(">d", (1.5, 0.0, -1.5)[sector]), "big"
                ),
            }
            assert record["fallback"] == {
                "target_speed_word": 0,
                "turn_rate_word": 0,
                "braking_tick_limit": 16,
            }

            def pack(value):
                if type(value) is dict:
                    return {key: pack(item) for key, item in value.items()}
                if type(value) in (list, tuple):
                    return {type(value).__name__: [pack(item) for item in value]}
                return {type(value).__name__: value}

            expected = hashlib.sha256(
                json.dumps(pack(record), sort_keys=True, allow_nan=False).encode(
                    "ascii"
                )
            ).hexdigest()
            assert result["request_sha256"] == expected
            changed = deepcopy(record)
            changed["command_words"]["target_speed_m_s"] ^= 1
            assert (
                hashlib.sha256(
                    json.dumps(pack(changed), sort_keys=True, allow_nan=False).encode(
                        "ascii"
                    )
                ).hexdigest()
                != expected
            )
            if case == 0:
                preserved = deepcopy(result)
                record["source_context"]["epoch"] = "0" * 32
                record["command_words"]["turn_rate_rad_s"] = 0
                assert check() == preserved
        else:
            assert result["status"] == "unknown"
            assert "request" not in result and "request_sha256" not in result
            assert (
                result["reason"]
                == {
                    3: "normal_selection_requests_braking",
                    4: "source_frame_binding_mismatch",
                    5: "unsupported_request_identity",
                    6: "unsupported_request_identity",
                    7: "unsupported_declared_source_context",
                    8: "unsupported_declared_source_context",
                    9: "unsupported_declared_source_context",
                    10: "unsupported_declared_capture_tick",
                    11: "unsupported_declared_capture_tick",
                    12: "unsupported_declared_capture_tick",
                    13: "request_reference_binding_mismatch",
                }[case]
            )
    assert (source, frame, decision_frame, options) == saved


@pytest.fixture(scope="module")
def c1_request_binding_ledger(request):
    ledger = dict.fromkeys(
        (
            "checker",
            "prepare",
            "normal",
            "mapper",
            "state_decode",
            "decision_decode",
            "bridge",
            "binding",
            "motion",
            "digest",
            "forbidden",
        ),
        0,
    )
    yield ledger
    assert all(
        ledger[key] <= (128 if key == "digest" else 32)
        for key in ledger
        if key != "forbidden"
    )
    assert ledger["forbidden"] == 0
    capture = request.config.pluginmanager.getplugin("capturemanager")
    if capture is None:
        print("C1 request-binding ledger:", json.dumps(ledger, sort_keys=True))
    else:
        with capture.global_and_fixture_disabled():
            print("C1 request-binding ledger:", json.dumps(ledger, sort_keys=True))


@pytest.mark.parametrize("case", range(16))
def test_synthetic_c1_request_binding_rejects_changed_or_expired_content(
    c1_request_binding_ledger, monkeypatch, case
):
    from interface.protocol import (
        RULES_QUESTIONS,
        Answer,
        Decision,
        State,
        Status,
        encode_decision,
        encode_state,
    )
    from sim import diagnostics, rules

    ledger = c1_request_binding_ledger
    for key, module, name in (
        ("prepare", diagnostics, "_prepare_synthetic_c1_normal_request"),
        ("normal", diagnostics, "_probe_synthetic_c1_normal_state_motion"),
        ("mapper", rules, "_map_synthetic_c1_normal_command"),
        ("state_decode", rules, "decode_state"),
        ("decision_decode", rules, "decode_decision"),
        ("bridge", diagnostics, "_probe_synthetic_c1_state_motion"),
        ("binding", diagnostics, "_bind_synthetic_c1_state_intervals"),
        ("motion", diagnostics, "_probe_synthetic_c1_discrete_motion"),
        ("digest", diagnostics, "_c1_source_binding_digest"),
    ):
        original = getattr(module, name)

        def counted(*args, _key=key, _original=original, **kwargs):
            ledger[_key] += 1
            assert ledger[_key] <= (128 if _key == "digest" else 32)
            return _original(*args, **kwargs)

        monkeypatch.setattr(module, name, counted)

    def forbidden(*args, **kwargs):
        ledger["forbidden"] += 1
        raise AssertionError(
            "request matching must not query C1, grant a permit or execute a rover"
        )

    for name in (
        "inspect_synthetic_c1_history",
        "capture_synthetic_c1_views",
        "_probe_synthetic_c1_discrete_path_enclosure",
        "_probe_synthetic_c1_wire_rejection",
        "_audit_synthetic_c1_source_binding",
        "_c1_curved_centerline",
    ):
        monkeypatch.setattr(diagnostics, name, forbidden)
    for name in ("host_action", "wire_step", "decide", "run_diagnostics"):
        monkeypatch.setattr(rules, name, forbidden)
    monkeypatch.setattr(RoverEnv, "reset", forbidden)
    monkeypatch.setattr(RoverEnv, "step", forbidden)
    choices = (0, 1, 2)
    answers = tuple(
        Answer(
            question,
            tuple(float(index == choice) for index in range(len(options))),
            choice,
        )
        for (question, (_, options)), choice in zip(
            RULES_QUESTIONS.items(), choices, strict=True
        )
    )
    source = State(
        sequence=22,
        timestamp_us=1100000,
        velocity_m_s=(0.5, 0.0, 0.0),
        goal_m=(3.0, 1.0, 0.0),
    )
    retained = diagnostics._prepare_synthetic_c1_normal_request(
        source,
        encode_state(source),
        encode_decision(
            Decision(
                sequence=22, timestamp_us=1100000, status=Status.OK, answers=answers
            )
        ),
        request_id="d" * 32,
        source_context={
            "epoch": "a" * 32,
            "source_identity": "b" * 64,
            "c1_reference_identity": "c" * 64,
            "capture_tick": 20,
            "reference_tick": 22,
        },
        reference_tick=22,
        error_evidence={
            "position_error_m": 0.0,
            "heading_error_rad": 0.0,
            "profile_exact": True,
        },
        synthetic_test_only=True,
    )
    assert retained["fixture_request_prepared"] is True
    received = deepcopy(retained["request"])
    if case == 1:
        received["hold_ticks"] = True
    elif case == 2:
        received["command_words"]["target_speed_m_s"] ^= 1
    elif case == 3:
        received["decision_frame_hex"] = received["decision_frame_hex"][:-2] + "00"
    elif case == 4:
        received["source_context"]["epoch"] = "0" * 32
    elif case == 5:
        received["source_context"]["source_identity"] = "0" * 64
    elif case == 6:
        received["config_record"]["acceleration"] = 1
    elif case == 7:
        received["config_sha256"] = "0" * 64
    elif case == 8:
        received["request_id"] = "0" * 32
    elif case == 9:
        received["application_tick"] = 22.0
    elif case == 12:
        retained["source_qualified"] = True
    elif case == 13:
        received["extra"] = True
    elif case == 14:
        received = None
    options = {
        "current_tick": 23 if case == 10 else 21 if case == 11 else 22,
        "synthetic_test_only": case != 15,
    }
    saved = deepcopy((retained, received, options))

    def check():
        ledger["checker"] += 1
        assert ledger["checker"] <= 32
        return diagnostics._check_synthetic_c1_normal_request_binding(
            retained, received, **options
        )

    before = dict(ledger)
    if case == 15:
        with pytest.raises(ValueError, match="synthetic_test_only"):
            check()
        assert ledger["digest"] == before["digest"]
    else:
        result = check()
        assert result["fixture_request_matched"] is (case == 0)
        assert (
            result["guard_status"] == "UNKNOWN"
            and result["fixture_permission_granted"] is False
        )
        for flag in (
            "training_approved",
            "real_input_qualified",
            "free_space_qualified",
            "numerically_certified",
            "source_qualified",
            "native_execution_qualified",
            "command_admission_qualified",
        ):
            assert result[flag] is False
        if case == 0:
            assert result["status"] == "matched_declared_normal_request_content"
            assert result["reason"] == "source_and_full_guard_unqualified"
            assert result["request_sha256"] == retained["request_sha256"]
            assert result["application_tick"] == result["expires_at_tick"] == 22
            saved_result = deepcopy(result)
            result["request_sha256"] = "0" * 64
            assert check() == saved_result
        else:
            assert result["status"] == "unknown" and "request_sha256" not in result
            assert (
                result["reason"]
                == {
                    1: "unsupported_received_request",
                    2: "request_content_mismatch",
                    3: "request_content_mismatch",
                    4: "request_content_mismatch",
                    5: "request_content_mismatch",
                    6: "request_content_mismatch",
                    7: "request_content_mismatch",
                    8: "request_content_mismatch",
                    9: "unsupported_received_request",
                    10: "request_expired",
                    11: "request_not_application_tick",
                    12: "unsupported_retained_request",
                    13: "unsupported_received_request",
                    14: "unsupported_received_request",
                }[case]
            )
    assert (retained, received, options) == saved


@pytest.fixture(scope="module")
def c1_request_source_ledger(request):
    ledger = dict.fromkeys(
        (
            "recheck",
            "checker",
            "prepare",
            "normal",
            "mapper",
            "state_decode",
            "decision_decode",
            "bridge",
            "binding",
            "motion",
            "digest",
            "forbidden",
        ),
        0,
    )
    yield ledger
    assert ledger["recheck"] <= 32 and ledger["digest"] <= 128
    assert all(
        ledger[key] <= 48
        for key in ledger
        if key not in ("recheck", "digest", "forbidden")
    )
    assert ledger["forbidden"] == 0
    capture = request.config.pluginmanager.getplugin("capturemanager")
    if capture is None:
        print("C1 request-source ledger:", json.dumps(ledger, sort_keys=True))
    else:
        with capture.global_and_fixture_disabled():
            print("C1 request-source ledger:", json.dumps(ledger, sort_keys=True))


@pytest.mark.parametrize("case", range(16))
def test_synthetic_c1_request_source_rechecks_actual_inputs(
    c1_request_source_ledger, monkeypatch, case
):
    from dataclasses import replace

    from interface.protocol import (
        RULES_QUESTIONS,
        Answer,
        Decision,
        State,
        Status,
        encode_decision,
        encode_state,
    )
    from sim import diagnostics, rules

    ledger = c1_request_source_ledger
    for key, module, name in (
        ("checker", diagnostics, "_check_synthetic_c1_normal_request_binding"),
        ("prepare", diagnostics, "_prepare_synthetic_c1_normal_request"),
        ("normal", diagnostics, "_probe_synthetic_c1_normal_state_motion"),
        ("mapper", rules, "_map_synthetic_c1_normal_command"),
        ("state_decode", rules, "decode_state"),
        ("decision_decode", rules, "decode_decision"),
        ("bridge", diagnostics, "_probe_synthetic_c1_state_motion"),
        ("binding", diagnostics, "_bind_synthetic_c1_state_intervals"),
        ("motion", diagnostics, "_probe_synthetic_c1_discrete_motion"),
        ("digest", diagnostics, "_c1_source_binding_digest"),
    ):
        original = getattr(module, name)

        def counted(*args, _key=key, _original=original, **kwargs):
            ledger[_key] += 1
            assert ledger[_key] <= (128 if _key == "digest" else 48)
            return _original(*args, **kwargs)

        monkeypatch.setattr(module, name, counted)

    def forbidden(*args, **kwargs):
        ledger["forbidden"] += 1
        raise AssertionError(
            "request source recheck must not query C1 or execute a rover"
        )

    for name in (
        "inspect_synthetic_c1_history",
        "capture_synthetic_c1_views",
        "_probe_synthetic_c1_discrete_path_enclosure",
        "_probe_synthetic_c1_wire_rejection",
        "_audit_synthetic_c1_source_binding",
        "_c1_curved_centerline",
    ):
        monkeypatch.setattr(diagnostics, name, forbidden)
    for name in ("host_action", "wire_step", "decide", "run_diagnostics"):
        monkeypatch.setattr(rules, name, forbidden)
    monkeypatch.setattr(RoverEnv, "reset", forbidden)
    monkeypatch.setattr(RoverEnv, "step", forbidden)
    sector = case if case < 3 else 0
    choices = (0, sector, sector + 1)
    answers = tuple(
        Answer(
            question,
            tuple(float(index == choice) for index in range(len(options))),
            choice,
        )
        for (question, (_, options)), choice in zip(
            RULES_QUESTIONS.items(), choices, strict=True
        )
    )
    source = State(
        sequence=22,
        timestamp_us=1100000,
        velocity_m_s=((0.5, 0.2, 0.35)[case] if case < 3 else 0.5, 0.0, 0.0),
        goal_m=(3.0, 1.0, 0.0),
    )
    state_frame = encode_state(source)
    decision = Decision(
        sequence=22, timestamp_us=1100000, status=Status.OK, answers=answers
    )
    decision_frame = encode_decision(decision)
    error = {"position_error_m": 0.0, "heading_error_rad": 0.0, "profile_exact": True}
    retained = diagnostics._prepare_synthetic_c1_normal_request(
        source,
        state_frame,
        decision_frame,
        request_id="d" * 32,
        source_context={
            "epoch": "a" * 32,
            "source_identity": "b" * 64,
            "c1_reference_identity": "c" * 64,
            "capture_tick": 20,
            "reference_tick": 22,
        },
        reference_tick=22,
        error_evidence=error,
        synthetic_test_only=True,
    )
    assert retained["fixture_request_prepared"] is True
    received = deepcopy(retained["request"])
    config = Config()
    if case == 3:
        source = replace(source, sequence=99)
    elif case == 4:
        source = replace(source, goal_m=(2.0, 1.0, 0.0))
        state_frame = encode_state(source)
    elif case == 5:
        changed = replace(
            decision, answers=(answers[0], replace(answers[1], selected=2), answers[2])
        )
        decision_frame = encode_decision(changed)
    elif case == 6:
        config = replace(config, acceleration=0.5)
    elif case == 7:
        error = {**error, "position_error_m": 0.01}
    elif case == 8:
        error = None
    elif case == 10:
        received["command_words"]["target_speed_m_s"] ^= 1
    elif case == 11:
        retained["source_qualified"] = True
    options = {
        "current_tick": 23 if case == 9 else 22,
        "config": config,
        "error_evidence": error,
        "max_braking_ticks": 0 if case == 12 else 16,
        "source_max_integer_bits": 1 if case == 13 else 4096,
        "synthetic_test_only": case != 15,
    }
    if case == 14:
        options["target_speed"] = 0.4
    saved = deepcopy((retained, received, source, state_frame, decision_frame, options))

    def recheck():
        ledger["recheck"] += 1
        assert ledger["recheck"] <= 32
        return diagnostics._recheck_synthetic_c1_normal_request_source(
            retained, received, source, state_frame, decision_frame, **options
        )

    before = dict(ledger)
    if case in (14, 15):
        with pytest.raises(
            TypeError if case == 14 else ValueError,
            match="target_speed" if case == 14 else "synthetic_test_only",
        ):
            recheck()
        assert (
            ledger["checker"] == before["checker"]
            and ledger["prepare"] == before["prepare"]
        )
    else:
        result = recheck()
        assert result["fixture_request_source_rechecked"] is (case < 3)
        assert (
            result["fixture_permission_granted"] is False
            and result["guard_status"] == "UNKNOWN"
        )
        for flag in (
            "training_approved",
            "real_input_qualified",
            "free_space_qualified",
            "numerically_certified",
            "source_qualified",
            "native_execution_qualified",
            "command_admission_qualified",
        ):
            assert result[flag] is False
        if case < 3:
            assert (
                result["status"] == "rechecked_declared_current_request_source_fixture"
            )
            assert result["work"] == {"binding_entries": 2, "preparation_entries": 1}
            for key in (
                "request_sha256",
                "config_sha256",
                "source_state_sha256",
                "motion_sha256",
            ):
                assert result[key] == (
                    retained[key]
                    if key == "request_sha256"
                    else retained["request"][key]
                )
            if case == 0:
                original = deepcopy(result)
                result["motion_sha256"] = "0" * 64
                assert recheck() == original
        else:
            assert (
                result["status"] == "unknown"
                and "request_sha256" not in result
                and "motion_sha256" not in result
            )
            if case in (4, 5, 7, 10):
                assert result["reason"] == "request_content_mismatch"
            elif case == 3:
                assert result["reason"] == "source_frame_binding_mismatch"
            elif case == 6:
                assert result["reason"] == "unsupported_normal_motion_profile"
            elif case == 8:
                assert result["reason"] == "error_evidence_missing"
            elif case == 9:
                assert result["reason"] == "request_expired"
            elif case == 11:
                assert result["reason"] == "unsupported_retained_request"
            elif case == 12:
                assert result["reason"] == "braking_budget_exhausted"
            elif case == 13:
                assert "budget_exhausted" in result["reason"]
            if case in (9, 10, 11):
                assert (
                    ledger["prepare"] == before["prepare"]
                    and result["work"]["preparation_entries"] == 0
                )
    assert (retained, received, source, state_frame, decision_frame, options) == saved


@pytest.fixture(scope="module")
def c1_history_registration_ledger(request):
    ledger = dict.fromkeys(("bound", "binding", "reference", "forbidden"), 0)
    yield ledger
    assert ledger["bound"] <= 32 and ledger["binding"] <= 64
    assert ledger["reference"] <= 32 and ledger["forbidden"] == 0
    capture = request.config.pluginmanager.getplugin("capturemanager")
    if capture is None:
        print("C1 history-registration ledger:", json.dumps(ledger, sort_keys=True))
    else:
        with capture.global_and_fixture_disabled():
            print("C1 history-registration ledger:", json.dumps(ledger, sort_keys=True))


def _c1_history_registration_reference(states, point):
    import operator
    from fractions import Fraction

    assert 1 <= len(states) <= 4
    operations = {
        "add": operator.add,
        "sub": operator.sub,
        "mul": operator.mul,
        "div": operator.truediv,
    }
    terms = 0

    def binary(left, right, operation):
        bits = sum(
            abs(value.numerator).bit_length() + value.denominator.bit_length()
            for value in (left, right)
        )
        assert bits + 1 <= 16384
        if operation == "div":
            assert right != 0
        return operations[operation](left, right)

    def power(number, exponent):
        result = Fraction(1)
        for _ in range(exponent):
            result = binary(result, number, "mul")
        return result

    def product(left, right):
        values = [binary(first, second, "mul") for first in left for second in right]
        return min(values), max(values)

    def plus(left, right):
        return tuple(binary(first, second, "add") for first, second in zip(left, right))

    def minus(left, right):
        return binary(left[0], right[1], "sub"), binary(left[1], right[0], "sub")

    def trig(angle):
        nonlocal terms
        assert abs(angle) < 1
        intervals = []
        for offset in (0, 1):
            total = Fraction(0)
            for index in range(8):
                assert terms < 48
                terms += 1
                exponent = 2 * index + offset
                term = binary(
                    power(angle, exponent), Fraction(math.factorial(exponent)), "div"
                )
                total = binary(total, term if index % 2 == 0 else -term, "add")
            exponent = 16 + offset
            tail = abs(
                binary(
                    power(angle, exponent), Fraction(math.factorial(exponent)), "div"
                )
            )
            intervals.append((binary(total, tail, "sub"), binary(total, tail, "add")))
        return intervals

    zero, one, seconds = Fraction(0), Fraction(1), Fraction(0.05)
    position = [(zero, zero), (zero, zero)]
    heading = zero
    cosine, sine = (one, one), (zero, zero)
    for state in states[1:]:
        speed = Fraction(state.velocity_m_s[0])
        turn = Fraction(state.angular_velocity_rad_s[2])
        if turn:
            next_heading = binary(heading, binary(turn, seconds, "mul"), "add")
            next_cosine, next_sine = trig(next_heading)
            scale = binary(speed, turn, "div")
            delta = (
                product((scale, scale), minus(next_sine, sine)),
                product((scale, scale), minus(cosine, next_cosine)),
            )
            heading, cosine, sine = next_heading, next_cosine, next_sine
        else:
            distance = binary(speed, seconds, "mul")
            delta = (
                product((distance, distance), cosine),
                product((distance, distance), sine),
            )
        position = [plus(first, second) for first, second in zip(position, delta)]
    relative = [
        minus((Fraction(value), Fraction(value)), coordinate)
        for value, coordinate in zip(point, position)
    ]
    return (
        plus(product(cosine, relative[0]), product(sine, relative[1])),
        minus(product(cosine, relative[1]), product(sine, relative[0])),
    )


@pytest.mark.parametrize("case", range(16))
def test_synthetic_c1_history_registration_complete_frames(
    c1_history_registration_ledger, monkeypatch, case
):
    import struct
    from dataclasses import replace
    from fractions import Fraction

    from interface.protocol import State, decode_state, encode_state
    from sim import diagnostics

    ledger = c1_history_registration_ledger
    original = diagnostics._bind_synthetic_c1_state_intervals

    def counted(*args, **kwargs):
        ledger["binding"] += 1
        assert ledger["binding"] <= 64
        return original(*args, **kwargs)

    def forbidden(*args, **kwargs):
        ledger["forbidden"] += 1
        raise AssertionError("history bound must not query geometry or execute a rover")

    monkeypatch.setattr(diagnostics, "_bind_synthetic_c1_state_intervals", counted)
    for name in (
        "inspect_synthetic_c1_history",
        "capture_synthetic_c1_views",
        "_probe_synthetic_c1_state_motion",
        "_probe_synthetic_c1_discrete_motion",
        "_probe_synthetic_c1_discrete_path_enclosure",
        "prepare_synthetic_c1_relative_input",
        "_probe_synthetic_c1_wire_rejection",
        "_c1_curved_centerline",
    ):
        monkeypatch.setattr(diagnostics, name, forbidden)
    monkeypatch.setattr(RoverEnv, "reset", forbidden)
    monkeypatch.setattr(RoverEnv, "step", forbidden)
    early_speed, current_speed = (0.35, 0.375) if case == 1 else (0.2, 0.25)
    early_turn = 0.1 if case in (2, 5) else -0.1 if case == 3 else 0.0
    reference_tick = 20 if case == 4 else 23 if case == 5 else 22
    states = [
        State(
            sequence=tick,
            timestamp_us=tick * 50000,
            velocity_m_s=(
                early_speed if tick < reference_tick else current_speed,
                0.0,
                0.0,
            ),
            angular_velocity_rad_s=(
                0.0,
                0.0,
                early_turn if tick < reference_tick else 0.0,
            ),
        )
        for tick in range(20, reference_tick + 1)
    ]
    if case == 7:
        states[1] = replace(states[1], sequence=99)
    elif case == 8:
        states[1] = replace(states[1], timestamp_us=states[1].timestamp_us + 1)
    elif case == 9:
        states[1] = replace(states[1], ages_us=(1, *states[1].ages_us[1:]))
    elif case == 10:
        states[1] = replace(states[1], velocity_m_s=(early_speed, math.ulp(0.0), 0.0))
    elif case == 11:
        states[1] = replace(states[1], velocity_m_s=(0.6, 0.0, 0.0))
    frames = [encode_state(state) for state in states]
    if case == 6:
        states.pop(1)
        frames.pop(1)
    assumptions = dict.fromkeys(
        (
            "starting_pose_exact",
            "nominal_tick_binding_exact",
            "stored_word_dt_exact",
            "interval_ending_twist_exact",
        ),
        True,
    )
    if case == 12:
        assumptions = None
    settings = {
        "acquisition_tick": 20,
        "reference_tick": 22.0 if case == 13 else reference_tick,
        "point_radius_m": 4.0,
        "assumptions": assumptions,
        "max_history_ticks": 0 if case == 14 else 3,
        "synthetic_test_only": case != 15,
    }
    saved_states, saved_frames, saved_assumptions = (
        deepcopy(states),
        list(frames),
        deepcopy(assumptions),
    )
    before = dict(ledger)
    ledger["bound"] += 1
    if case == 15:
        with pytest.raises(ValueError, match="synthetic_test_only"):
            diagnostics._bound_synthetic_c1_history_registration(
                states, frames, **settings
            )
        assert ledger["binding"] == before["binding"]
        return
    result = diagnostics._bound_synthetic_c1_history_registration(
        states, frames, **settings
    )
    assert result["fixture_registration_bound"] is (case < 6)
    for key in (
        "training_approved",
        "real_input_qualified",
        "free_space_qualified",
        "numerically_certified",
        "source_qualified",
        "native_execution_qualified",
        "command_admission_qualified",
    ):
        assert result[key] is False
    if case < 6:
        assert result["status"] == "bounded_from_complete_word_history"
        assert result["work"] == {
            "binding_entries": reference_tick - 19,
            "intervals": reference_tick - 20,
        }
        assert [
            binding["state_frame"] for binding in result["source_bindings"]
        ] == frames
        bounds = {
            key: Fraction(*pair) for key, pair in result["rational_bounds"].items()
        }
        for key, value in bounds.items():
            assert value >= 0 and Fraction(result["upper_bounds"][key]) >= value
        if case in (0, 1):
            ledger["reference"] += 1
            received = struct.unpack("<f", struct.pack("<f", early_speed))[0]
            expected = abs(Fraction(received) - Fraction(early_speed)) * Fraction(0.05)
            assert expected > 0
            assert bounds["translation_m"] == bounds["registered_point_m"] == expected
            assert bounds["heading_rad"] == 0
        elif case in (2, 3, 5):
            assert bounds["heading_rad"] > 0
            assert bounds["registered_point_m"] > bounds["translation_m"] > 0
        elif case == 4:
            assert all(value == 0 for value in bounds.values())
        for coordinate in ("velocity_m_s", "angular_velocity_rad_s"):
            for field in result["source_bindings"][-1]["fields"][coordinate]:
                assert field["decoded_minus_source"] == (0, 1)
        ledger["reference"] += 2
        source_point = _c1_history_registration_reference(states, (4.0, 0.0))
        decoded_point = _c1_history_registration_reference(
            [decode_state(frame) for frame in frames], (4.0, 0.0)
        )
        coordinate_errors = [
            max(abs(first[0] - second[1]), abs(first[1] - second[0]))
            for first, second in zip(source_point, decoded_point)
        ]
        assert sum(value * value for value in coordinate_errors) <= (
            bounds["registered_point_m"] * bounds["registered_point_m"]
        )
        result["source_bindings"][0]["fields"].clear()
        result["assumptions"].clear()
        result["upper_bounds"]["registered_point_m"] = 123.0
        if case == 4:
            ledger["bound"] += 1
            repeated = diagnostics._bound_synthetic_c1_history_registration(
                states, frames, **settings
            )
            assert repeated["upper_bounds"]["registered_point_m"] == 0.0
            assert repeated["source_bindings"][0]["fields"]
    else:
        reasons = {
            6: "incomplete_frame_history",
            7: "frame_history_binding_mismatch",
            8: "frame_history_binding_mismatch",
            9: "stale_host_state",
            10: "unsupported_planar_source_intervals",
            11: "source_interval_outside_motion_domain",
            12: "unsupported_history_assumptions",
            13: "unsupported_history_ticks",
            14: "history_budget_exhausted",
        }
        assert result["reason"] == reasons[case]
        assert result["status"] == "unknown"
        assert "source_bindings" not in result and "upper_bounds" not in result
        if case == 14:
            ledger["bound"] += 1
            exhausted = diagnostics._bound_synthetic_c1_history_registration(
                states,
                frames,
                **{**settings, "max_history_ticks": 3, "max_integer_bits": 1},
            )
            assert exhausted["reason"] == "integer_budget_exhausted"
            assert exhausted["work"] == {"binding_entries": 0, "intervals": 0}
            assert (
                "upper_bounds" not in exhausted and "source_bindings" not in exhausted
            )
            ledger["bound"] += 1
            comparison_exhausted = diagnostics._bound_synthetic_c1_history_registration(
                states,
                frames,
                **{**settings, "max_history_ticks": 3, "max_integer_bits": 64},
            )
            assert comparison_exhausted["reason"] == "integer_budget_exhausted"
            assert comparison_exhausted["work"] == {
                "binding_entries": 1,
                "intervals": 0,
            }
            assert "upper_bounds" not in comparison_exhausted
            assert "source_bindings" not in comparison_exhausted
    assert states == saved_states and frames == saved_frames
    assert assumptions == saved_assumptions


@pytest.fixture(scope="module")
def c1_registered_cells_ledger(request):
    ledger = dict.fromkeys(
        ("wrapper", "history", "binding", "cells", "reference", "forbidden"), 0
    )
    yield ledger
    assert all(
        ledger[key] <= 32 for key in ("wrapper", "history", "cells", "reference")
    )
    assert ledger["binding"] <= 128 and ledger["forbidden"] == 0
    capture = request.config.pluginmanager.getplugin("capturemanager")
    if capture is None:
        print("C1 registered-cell ledger:", json.dumps(ledger, sort_keys=True))
    else:
        with capture.global_and_fixture_disabled():
            print("C1 registered-cell ledger:", json.dumps(ledger, sort_keys=True))


@pytest.mark.parametrize("case", range(16))
def test_synthetic_c1_registered_cells_declared_inputs(
    c1_registered_cells_ledger, monkeypatch, case
):
    from fractions import Fraction

    from interface.protocol import State, decode_state, encode_state
    from sim import diagnostics

    ledger = c1_registered_cells_ledger
    for key, name in (
        ("history", "_bound_synthetic_c1_history_registration"),
        ("binding", "_bind_synthetic_c1_state_intervals"),
        ("cells", "_c1_exclude_path_cells"),
    ):
        original = getattr(diagnostics, name)

        def counted(*args, _key=key, _original=original, **kwargs):
            ledger[_key] += 1
            assert ledger[_key] <= (128 if _key == "binding" else 32)
            return _original(*args, **kwargs)

        monkeypatch.setattr(diagnostics, name, counted)

    def forbidden(*args, **kwargs):
        ledger["forbidden"] += 1
        raise AssertionError("registered cells must not query C1 or execute a rover")

    for name in (
        "capture_synthetic_c1_views",
        "inspect_synthetic_c1_history",
        "prepare_synthetic_c1_relative_input",
        "_probe_synthetic_c1_state_motion",
        "_probe_synthetic_c1_discrete_motion",
        "_probe_synthetic_c1_discrete_path_enclosure",
        "_probe_synthetic_c1_wire_rejection",
        "_c1_curved_centerline",
    ):
        monkeypatch.setattr(diagnostics, name, forbidden)
    monkeypatch.setattr(RoverEnv, "reset", forbidden)
    monkeypatch.setattr(RoverEnv, "step", forbidden)
    segments = np.array(
        [
            [[float(value), -0.6], [float(value), 0.6]]
            for value in np.linspace(-0.6, 1, 81)
        ]
    )
    path = np.array([[0.0, 0.0], [0.25, 0.0]])
    early_speed, current_speed = (0.35, 0.375) if case == 1 else (0.2, 0.25)
    early_turn = 0.1 if case == 2 else -0.1 if case == 3 else 0.0
    reference_tick = 20 if case == 4 else 22
    states = [
        State(
            sequence=tick,
            timestamp_us=tick * 50000,
            velocity_m_s=(
                early_speed if tick < reference_tick else current_speed,
                0.0,
                0.0,
            ),
            angular_velocity_rad_s=(
                0.0,
                0.0,
                early_turn if tick < reference_tick else 0.0,
            ),
        )
        for tick in range(20, reference_tick + 1)
    ]
    frames = [encode_state(state) for state in states]
    ledger["reference"] += 1
    origin_reference = _c1_history_registration_reference(
        [decode_state(frame) for frame in frames], (0.0, 0.0)
    )
    origin = tuple(float((lower + upper) / 2) for lower, upper in origin_reference)
    origin_error = sum(
        max(abs(Fraction(value) - lower), abs(Fraction(value) - upper))
        for value, (lower, upper) in zip(origin, origin_reference)
    )
    numerical_guard = max(1e-12, math.nextafter(float(2 * origin_error), math.inf))
    assert Fraction(numerical_guard) >= 2 * origin_error
    settings = {
        "acquisition_tick": 20,
        "reference_tick": reference_tick,
        "capture_origin_body_m": origin,
        "point_radius_m": 0.25 if case == 10 else 4.0,
        "prefix_history_binding_exact": case != 7,
        "other_point_error_m": 0.05
        if case == 5
        else None
        if case == 6
        else -0.01
        if case == 11
        else 0.0,
        "assumptions": dict.fromkeys(
            (
                "starting_pose_exact",
                "nominal_tick_binding_exact",
                "stored_word_dt_exact",
                "interval_ending_twist_exact",
            ),
            True,
        ),
        "current_body_clear": case != 12,
        "controlled_envelope": True,
        "guard": numerical_guard,
        "max_cells": 0 if case == 13 else 32768,
        "max_integer_bits": 1 if case == 14 else 16384,
        "synthetic_test_only": case != 15,
    }
    if case == 8:
        settings["assumptions"] = None
    elif case == 9:
        states.pop(1)
        frames.pop(1)
    saved_segments, saved_path = segments.copy(), path.copy()
    saved_states, saved_frames, saved_settings = (
        deepcopy(states),
        list(frames),
        deepcopy(settings),
    )
    before = dict(ledger)
    ledger["wrapper"] += 1
    if case == 15:
        with pytest.raises(ValueError, match="synthetic_test_only"):
            diagnostics._c1_exclude_registered_path_cells(
                segments, path, 0.18, states, frames, **settings
            )
        assert ledger["history"] == before["history"]
        assert ledger["cells"] == before["cells"]
        return
    result = diagnostics._c1_exclude_registered_path_cells(
        segments, path, 0.18, states, frames, **settings
    )
    assert result["fixture_enclosure_excluded"] is (case < 5)
    for flag in (
        "training_approved",
        "real_input_qualified",
        "free_space_qualified",
        "numerically_certified",
        "source_qualified",
        "native_execution_qualified",
        "command_admission_qualified",
    ):
        assert result[flag] is False
    expected_history = int(case in (0, 1, 2, 3, 4, 5, 8, 9, 13))
    expected_cells = int(case in (0, 1, 2, 3, 4, 5, 13))
    assert ledger["history"] - before["history"] == expected_history
    assert ledger["cells"] - before["cells"] == expected_cells
    assert result["work"]["registration_entries"] == expected_history
    assert result["work"]["cell_entries"] == expected_cells
    if expected_cells:
        word_error = result["registration_bound"]["upper_bounds"]["registered_point_m"]
        expected_guard = (
            Fraction(numerical_guard)
            + Fraction(settings["other_point_error_m"])
            + Fraction(word_error)
        )
        assert Fraction(result["combined_guard_m"]) >= expected_guard
        assert result["work"]["prefix_points_checked"] == 162
        if case != 4:
            assert word_error > 0
        else:
            assert word_error == 0
        if case == 13:
            assert (
                result["reason"] == "cell_budget_exhausted"
                and result["cells_checked"] == 0
            )
        elif case == 5:
            assert result["status"] == "unknown"
        else:
            assert (
                result["status"] == "excluded_under_declared_registration_assumptions"
            )
        result["registration_bound"]["assumptions"].clear()
        result["combined_guard_m"] = 123.0
        if case == 0:
            ledger["wrapper"] += 1
            repeated = diagnostics._c1_exclude_registered_path_cells(
                segments, path, 0.18, states, frames, **settings
            )
            assert repeated["fixture_enclosure_excluded"] is True
            assert repeated["combined_guard_m"] != 123.0
            assert repeated["registration_bound"]["assumptions"]
    else:
        reasons = {
            6: "remaining_point_error_missing",
            7: "prefix_history_binding_not_established",
            8: "unsupported_history_assumptions",
            9: "incomplete_frame_history",
            10: "prefix_point_radius_not_enclosed",
            11: "unsupported_point_error",
            12: "body_or_envelope_not_established",
            14: "integer_budget_exhausted",
        }
        assert result["reason"] == reasons[case] and result["status"] == "unknown"
        assert "combined_guard_m" not in result and "registration_bound" not in result
        if case == 14:
            ledger["wrapper"] += 1
            with pytest.raises(ValueError, match="bounded integers"):
                diagnostics._c1_exclude_registered_path_cells(
                    segments,
                    path,
                    0.18,
                    states,
                    frames,
                    **{**settings, "max_integer_bits": 16385},
                )
            assert ledger["history"] == before["history"]
            assert ledger["cells"] == before["cells"]
    assert np.array_equal(segments, saved_segments) and np.array_equal(path, saved_path)
    assert (
        states == saved_states and frames == saved_frames and settings == saved_settings
    )


@pytest.fixture(scope="module")
def c1_discrete_path_fixtures(request):
    from sim import diagnostics

    counts = dict.fromkeys(
        ("capture", "producer", "adapter", "inspection", "prefix", "cell", "forbidden"),
        0,
    )
    records, motions = [], []
    for obstacles in ((), ((2.3, 2.0, 0.05),)):
        counts["capture"] += 1
        records.append(
            diagnostics.capture_synthetic_c1_views(
                Scenario(start=(2, 2, 0), obstacles=obstacles),
                pose_m_rad=[2, 2, 0],
                capture_tick=20,
                synthetic_test_only=True,
            )
        )
    for turn in (0.0, 1.5, -1.5):
        counts["producer"] += 1
        motions.append(
            diagnostics._probe_synthetic_c1_discrete_motion(
                initial_speed=0.5,
                target_speed=0.5,
                turn_rate=turn,
                error_evidence={
                    "position_error_m": 0.0,
                    "heading_error_rad": 0.0,
                    "profile_exact": True,
                },
                synthetic_test_only=True,
            )
        )
    yield {"records": records, "motions": motions, "counts": counts}
    assert counts["capture"] == 2 and counts["producer"] == 3
    assert all(counts[key] <= 32 for key in ("adapter", "inspection", "prefix", "cell"))
    assert counts["forbidden"] == 0
    capture = request.config.pluginmanager.getplugin("capturemanager")
    if capture is None:
        print("C1 discrete-path ledger:", json.dumps(counts, sort_keys=True))
    else:
        with capture.global_and_fixture_disabled():
            print("C1 discrete-path ledger:", json.dumps(counts, sort_keys=True))


@pytest.mark.parametrize("case", range(24))
def test_synthetic_c1_discrete_path_enclosure_clear_fixture(
    c1_discrete_path_fixtures, monkeypatch, case
):
    from sim import diagnostics

    fixtures = c1_discrete_path_fixtures
    counts = fixtures["counts"]
    for key, name in (
        ("adapter", "_probe_synthetic_c1_discrete_path_enclosure"),
        ("inspection", "inspect_synthetic_c1_history"),
        ("prefix", "_c1_low_free_segments"),
        ("cell", "_c1_exclude_path_cells"),
    ):
        original = getattr(diagnostics, name)

        def counted(*args, _original=original, _key=key, **kwargs):
            counts[_key] += 1
            assert counts[_key] <= 32
            return _original(*args, **kwargs)

        monkeypatch.setattr(diagnostics, name, counted)

    def forbidden(*args, **kwargs):
        counts["forbidden"] += 1
        raise AssertionError(
            "discrete path fixtures must not call old C1/runtime paths"
        )

    for name in (
        "_c1_curved_centerline",
        "probe_synthetic_c1_enclosure",
        "probe_synthetic_c1_occupied_witness",
        "probe_synthetic_c1_questions",
        "_probe_synthetic_c1_wire_rejection",
        "_probe_synthetic_c1_discrete_motion",
        "capture_synthetic_c1_views",
    ):
        monkeypatch.setattr(diagnostics, name, forbidden)
    monkeypatch.setattr(RoverEnv, "reset", forbidden)
    monkeypatch.setattr(RoverEnv, "step", forbidden)
    record = deepcopy(fixtures["records"][1 if case == 3 else 0])
    motion = deepcopy(fixtures["motions"][case if case in (1, 2) else 0])
    settings = {
        "reference_tick": 22,
        "reference_pose_m_rad": [2, 2, 0],
        "current_body_clear": True,
        "controlled_envelope": True,
        "synthetic_test_only": True,
    }
    reason = "unsupported_motion_fixture"
    if case == 3:
        reason = "unexcluded_center_cell"
        end = motion["centerline_boxes_m"][-1][0][0]
        assert 0.3 > 0.18 + 0.05
        assert 0.3 - end < 0.18 + 0.05
    elif case == 4:
        for box in motion["centerline_boxes_m"][1:]:
            box[0][1] += 0.01
        for index, chord in enumerate(motion["chords"]):
            chord["start_box_m"] = deepcopy(motion["centerline_boxes_m"][index])
            chord["end_box_m"] = deepcopy(motion["centerline_boxes_m"][index + 1])
    elif case == 5:
        settings["current_body_clear"] = False
        reason = "current_body_clear_not_established"
    elif case == 6:
        settings["controlled_envelope"] = False
        reason = "controlled_envelope_not_established"
    elif case == 7:
        settings["reference_tick"] = 24
        reason = "stale_capture"
    elif case == 8:
        record["tof_valid"][:] = False
        record["tof_m"][:] = 0
        reason = "unsupported_points"
    elif case == 9:
        settings["reference_pose_m_rad"] = [3, 2, 0]
        reason = "unsupported_capture_to_reference_motion"
    elif case == 10:
        settings["reference_pose_m_rad"] = [2, 2, 1.0]
        reason = "unsupported_capture_to_reference_motion"
    elif case == 11:
        motion["chords"][0]["extra"] = 0
    elif case == 12:
        motion["chords"][0]["end_box_m"][0][1] += 0.01
        motion["centerline_boxes_m"] = deepcopy(motion["centerline_boxes_m"])
        motion["centerline_boxes_m"][1][0][1] -= 0.01
    elif case == 13:
        motion["centerline_boxes_m"][1][0] = [0.1, 0.0]
    elif case == 14:
        motion["centerline_boxes_m"][1][0][1] = float("inf")
    elif case == 15:
        motion["chords"][0]["radius_upper_m"] = 0.125
    elif case == 16:
        motion["source_qualified"] = True
    elif case == 17:
        motion["speed_intervals_m_s"][-1] = [0.05, 0.05]
    elif case == 18:
        motion["work"]["chords"] = True
    elif case == 19:
        motion["chords"] = []
    elif case == 20:
        settings["max_cells"] = 0
        reason = "cell_budget_exhausted"
    elif case == 21:
        for chord in motion["chords"]:
            chord["radius_upper_m"] = 2.0
        reason = "axis_aligned_wall_support_incomplete"
    elif case == 22:
        settings["synthetic_test_only"] = False
    elif case == 23:
        settings["config"] = Config(noise_std=0, dropout=0, max_range=3.0)
        reason = "unsupported_dynamics_or_wall_profile"
    saved_record, saved_motion = deepcopy(record), deepcopy(motion)
    if case == 22:
        with pytest.raises(ValueError, match="synthetic_test_only"):
            diagnostics._probe_synthetic_c1_discrete_path_enclosure(
                [record], motion, **settings
            )
    else:
        result = diagnostics._probe_synthetic_c1_discrete_path_enclosure(
            [record], motion, **settings
        )
        clear = case in (0, 1, 2, 4)
        assert result["fixture_enclosure_excluded"] is clear
        assert result["reason"] == (
            "complete_discrete_path_and_axis_aligned_walls_excluded"
            if clear
            else reason
        )
        for flag in (
            "training_approved",
            "real_input_qualified",
            "free_space_qualified",
            "numerically_certified",
            "source_qualified",
            "native_execution_qualified",
            "command_admission_qualified",
        ):
            assert result[flag] is False
        assert all(value in (0, 1) for value in result["work"].values())
        assert result["cells_checked"] <= settings.get("max_cells", 32768)
        if clear:
            assert result["status"] == "excluded_under_fixture_assumptions"
            assert result["work"] == {
                "inspection_entries": 1,
                "prefix_entries": 1,
                "cell_entries": 1,
            }
            radius = result["path_tube_radius_m"]
            for point, box in zip(
                result["path_points_body_m"], motion["centerline_boxes_m"], strict=True
            ):
                for horizontal in box[0]:
                    for vertical in box[1]:
                        assert (
                            math.hypot(horizontal - point[0], vertical - point[1])
                            <= radius - 0.18
                        )
            if case == 4:
                assert radius >= 0.185
            result["path_points_body_m"][0][0] = 123.0
        else:
            assert result["status"] == "unknown"
    assert json.dumps(record, default=json_value, sort_keys=True) == json.dumps(
        saved_record, default=json_value, sort_keys=True
    )
    assert motion == saved_motion


@pytest.fixture(scope="module")
def c1_path_point_error_ledger(request):
    ledger = dict.fromkeys(
        ("adapter", "inspection", "prefix", "history", "binding", "cell", "forbidden"),
        0,
    )
    yield ledger
    assert all(
        ledger[key] <= (128 if key == "binding" else 32)
        for key in ("adapter", "inspection", "prefix", "history", "binding", "cell")
    )
    assert ledger["forbidden"] == 0
    capture = request.config.pluginmanager.getplugin("capturemanager")
    if capture is None:
        print("C1 path-point-error ledger:", json.dumps(ledger, sort_keys=True))
    else:
        with capture.global_and_fixture_disabled():
            print("C1 path-point-error ledger:", json.dumps(ledger, sort_keys=True))


@pytest.mark.parametrize("case", range(16))
def test_synthetic_c1_discrete_path_point_error_reaches_walls(
    c1_discrete_path_fixtures, c1_path_point_error_ledger, monkeypatch, case
):
    from dataclasses import replace
    from fractions import Fraction

    from interface.protocol import State, decode_state, encode_state
    from sim import diagnostics

    ledger = c1_path_point_error_ledger
    observed_prefixes = []
    for key, name in (
        ("inspection", "inspect_synthetic_c1_history"),
        ("prefix", "_c1_low_free_segments"),
        ("history", "_bound_synthetic_c1_history_registration"),
        ("binding", "_bind_synthetic_c1_state_intervals"),
        ("cell", "_c1_exclude_path_cells"),
    ):
        original = getattr(diagnostics, name)

        def counted(*args, _key=key, _original=original, **kwargs):
            ledger[_key] += 1
            assert ledger[_key] <= (128 if _key == "binding" else 32)
            output = _original(*args, **kwargs)
            if _key == "prefix":
                observed_prefixes.append(output[0].copy())
            return output

        monkeypatch.setattr(diagnostics, name, counted)

    def forbidden(*args, **kwargs):
        ledger["forbidden"] += 1
        raise AssertionError(
            "path point errors must not collect fixtures or run a rover"
        )

    for name in (
        "capture_synthetic_c1_views",
        "_probe_synthetic_c1_discrete_motion",
        "_probe_synthetic_c1_state_motion",
        "_c1_curved_centerline",
        "probe_synthetic_c1_enclosure",
        "probe_synthetic_c1_occupied_witness",
        "probe_synthetic_c1_questions",
        "_probe_synthetic_c1_wire_rejection",
    ):
        monkeypatch.setattr(diagnostics, name, forbidden)
    monkeypatch.setattr(RoverEnv, "reset", forbidden)
    monkeypatch.setattr(RoverEnv, "step", forbidden)
    record = deepcopy(c1_discrete_path_fixtures["records"][0])
    motion = deepcopy(c1_discrete_path_fixtures["motions"][0])
    early_speed = 0.5 if case == 2 else 0.35 if case == 1 else 0.2
    reference_tick = 22
    states = [
        State(
            sequence=tick,
            timestamp_us=tick * 50000,
            velocity_m_s=(early_speed if tick < reference_tick else 0.5, 0.0, 0.0),
        )
        for tick in range(20, reference_tick + 1)
    ]
    frames = [encode_state(state) for state in states]
    distance = sum(
        Fraction(decode_state(frame).velocity_m_s[0]) for frame in frames[1:]
    ) * Fraction(0.05)
    reference = [float(Fraction(2) + distance), 2.0, 0.0]
    assert abs(Fraction(reference[0]) - (Fraction(2) + distance)) < Fraction(1e-8)
    evidence = {
        "source_states": states,
        "state_frames": frames,
        "history_assumptions": dict.fromkeys(
            (
                "starting_pose_exact",
                "nominal_tick_binding_exact",
                "stored_word_dt_exact",
                "interval_ending_twist_exact",
            ),
            True,
        ),
        "prefix_history_binding_exact": True,
        "remaining_point_error_m": 1e-8,
        "point_radius_m": 4.0,
    }
    if case == 3:
        evidence["remaining_point_error_m"] = 1.0
    elif case == 4:
        evidence["remaining_point_error_m"] = 2.0
    elif case == 5:
        evidence["remaining_point_error_m"] = None
    elif case == 6:
        evidence["prefix_history_binding_exact"] = False
    elif case == 7:
        evidence["history_assumptions"] = None
    elif case == 8:
        states.pop(1)
        frames.pop(1)
    elif case == 9:
        frames[1] = encode_state(replace(states[1], sequence=99))
    elif case == 10:
        states[1] = replace(states[1], ages_us=(1, *states[1].ages_us[1:]))
        frames[1] = encode_state(states[1])
    elif case == 11:
        evidence["point_radius_m"] = 0.0
    elif case == 12:
        evidence["remaining_point_error_m"] = -0.01
    elif case == 14:
        motion["chords"][0]["radius_upper_m"] = 0.01
    settings = {
        "reference_tick": reference_tick,
        "reference_pose_m_rad": reference,
        "current_body_clear": True,
        "controlled_envelope": True,
        "max_cells": 0 if case == 13 else 32768,
        "synthetic_test_only": case != 15,
    }
    saved_record, saved_motion, saved_evidence = (
        deepcopy(record),
        deepcopy(motion),
        deepcopy(evidence),
    )
    before = dict(ledger)
    ledger["adapter"] += 1
    if case == 15:
        with pytest.raises(ValueError, match="synthetic_test_only"):
            diagnostics._probe_synthetic_c1_discrete_path_enclosure(
                [record], motion, point_error_evidence=evidence, **settings
            )
        assert ledger["inspection"] == before["inspection"]
        assert ledger["history"] == before["history"]
        return
    result = diagnostics._probe_synthetic_c1_discrete_path_enclosure(
        [record], motion, point_error_evidence=evidence, **settings
    )
    assert result["fixture_enclosure_excluded"] is (case in (0, 1, 2))
    expected_inspection = int(case not in (5, 6, 14))
    expected_history = int(case in (0, 1, 2, 3, 4, 7, 8, 9, 10, 13))
    expected_cell = int(case in (0, 1, 2, 3, 13))
    assert ledger["inspection"] - before["inspection"] == expected_inspection
    assert ledger["prefix"] - before["prefix"] == expected_inspection
    assert ledger["history"] - before["history"] == expected_history
    assert ledger["cell"] - before["cell"] == expected_cell
    for flag in (
        "training_approved",
        "real_input_qualified",
        "free_space_qualified",
        "numerically_certified",
        "source_qualified",
        "native_execution_qualified",
        "command_admission_qualified",
    ):
        assert result[flag] is False
    if case in (0, 1, 2, 3, 4, 13):
        word_error = result["registration_bound"]["upper_bounds"]["registered_point_m"]
        assert (word_error > 0) is (case != 2)
        assert Fraction(result["point_error_guard_m"]) >= (
            Fraction(word_error) + Fraction(evidence["remaining_point_error_m"])
        )
        if case in (0, 1, 2, 3, 13):
            assert result["free_segment_count"] > 0
    if case == 0:
        ledger["adapter"] += 1
        legacy = diagnostics._probe_synthetic_c1_discrete_path_enclosure(
            [record], motion, **settings
        )
        assert legacy["fixture_enclosure_excluded"] is True
        assert result["path_tube_radius_m"] == legacy["path_tube_radius_m"]
        assert result["path_points_body_m"] == legacy["path_points_body_m"]
        assert result["free_segment_count"] <= legacy["free_segment_count"]
        assert (
            "point_error_guard_m" not in legacy and "registration_bound" not in legacy
        )
        prefixes = observed_prefixes[0][..., :2].reshape(-1, 2)
        path = np.asarray(legacy["path_points_body_m"])
        wall_margin = min(
            *(path.min(axis=0) - legacy["path_tube_radius_m"] - prefixes.min(axis=0)),
            *(prefixes.max(axis=0) - path.max(axis=0) - legacy["path_tube_radius_m"]),
        )
        assert 1.0 < wall_margin < 2.0
        result["registration_bound"]["source_bindings"].clear()
        result["path_points_body_m"][0][0] = 123.0
        ledger["adapter"] += 1
        repeated = diagnostics._probe_synthetic_c1_discrete_path_enclosure(
            [record], motion, point_error_evidence=evidence, **settings
        )
        assert repeated["fixture_enclosure_excluded"] is True
        assert repeated["path_points_body_m"][0][0] == 0.0
        assert repeated["registration_bound"]["source_bindings"]
    elif case == 2:
        assert record["config"]["latency_ticks"] == 2
        ledger["adapter"] += 1
        unavailable = diagnostics._probe_synthetic_c1_discrete_path_enclosure(
            [record],
            motion,
            point_error_evidence={
                **evidence,
                "source_states": states[:1],
                "state_frames": frames[:1],
            },
            **{**settings, "reference_tick": 20, "reference_pose_m_rad": [2, 2, 0]},
        )
        assert unavailable["fixture_enclosure_excluded"] is False
        assert unavailable["reason"] == "unsupported_history"
        assert unavailable["work"] == {
            "inspection_entries": 1,
            "prefix_entries": 0,
            "cell_entries": 0,
        }
        assert "registration_bound" not in unavailable
    elif case not in (1, 2):
        reasons = {
            3: "unexcluded_center_cell",
            4: "axis_aligned_wall_support_incomplete",
            5: "remaining_point_error_missing",
            6: "unsupported_point_error_evidence",
            7: "unsupported_history_assumptions",
            8: "incomplete_frame_history",
            9: "source_frame_binding_mismatch",
            10: "stale_host_state",
            11: "no_point_radius_supported_prefixes",
            12: "unsupported_point_error_domain",
            13: "cell_budget_exhausted",
            14: "unsupported_motion_fixture",
        }
        assert result["reason"] == reasons[case] and result["status"] == "unknown"
        if case == 4:
            assert result["work"]["cell_entries"] == 0
    assert json.dumps(record, default=json_value, sort_keys=True) == json.dumps(
        saved_record, default=json_value, sort_keys=True
    )
    assert motion == saved_motion and evidence == saved_evidence


@pytest.fixture(scope="module")
def c1_command_path_ledger(request):
    ledger = dict.fromkeys(
        (
            "wrapper",
            "bridge",
            "binding",
            "motion",
            "path",
            "inspection",
            "prefix",
            "history",
            "cell",
            "reference",
            "forbidden",
        ),
        0,
    )
    yield ledger
    assert all(
        ledger[key] <= (128 if key == "binding" else 32)
        for key in ledger
        if key != "forbidden"
    )
    assert ledger["forbidden"] == 0
    capture = request.config.pluginmanager.getplugin("capturemanager")
    if capture is None:
        print("C1 command-path ledger:", json.dumps(ledger, sort_keys=True))
    else:
        with capture.global_and_fixture_disabled():
            print("C1 command-path ledger:", json.dumps(ledger, sort_keys=True))


@pytest.mark.parametrize("case", range(16))
def test_synthetic_c1_command_path_uses_owned_history(
    c1_discrete_path_fixtures, c1_command_path_ledger, monkeypatch, case
):
    from dataclasses import replace
    from fractions import Fraction

    from interface.protocol import State, decode_state, encode_state
    from sim import diagnostics

    ledger = c1_command_path_ledger
    generated = []
    for key, name in (
        ("bridge", "_probe_synthetic_c1_state_motion"),
        ("binding", "_bind_synthetic_c1_state_intervals"),
        ("motion", "_probe_synthetic_c1_discrete_motion"),
        ("path", "_probe_synthetic_c1_discrete_path_enclosure"),
        ("inspection", "inspect_synthetic_c1_history"),
        ("prefix", "_c1_low_free_segments"),
        ("history", "_bound_synthetic_c1_history_registration"),
        ("cell", "_c1_exclude_path_cells"),
    ):
        original = getattr(diagnostics, name)

        def counted(*args, _key=key, _original=original, **kwargs):
            ledger[_key] += 1
            assert ledger[_key] <= (128 if _key == "binding" else 32)
            output = _original(*args, **kwargs)
            if _key == "path":
                generated.append(deepcopy(args[1]))
                if case == 14:
                    output["registration_bound"]["source_bindings"][-1]["schema"] = (
                        "foreign"
                    )
            return output

        monkeypatch.setattr(diagnostics, name, counted)

    def forbidden(*args, **kwargs):
        ledger["forbidden"] += 1
        raise AssertionError("command-path composition must not collect or actuate")

    for name in (
        "capture_synthetic_c1_views",
        "_c1_curved_centerline",
        "probe_synthetic_c1_enclosure",
        "probe_synthetic_c1_occupied_witness",
        "probe_synthetic_c1_questions",
        "_probe_synthetic_c1_wire_rejection",
    ):
        monkeypatch.setattr(diagnostics, name, forbidden)
    monkeypatch.setattr(RoverEnv, "reset", forbidden)
    monkeypatch.setattr(RoverEnv, "step", forbidden)
    record = deepcopy(c1_discrete_path_fixtures["records"][0])
    current_speed = 0.2 if case == 3 else 0.6 if case == 4 else 0.5
    states = [
        State(
            sequence=tick,
            timestamp_us=tick * 50000,
            velocity_m_s=(0.2 if tick < 22 else current_speed, 0.0, 0.0),
        )
        for tick in range(20, 23)
    ]
    frames = [encode_state(state) for state in states]
    distance = sum(
        Fraction(decode_state(frame).velocity_m_s[0]) for frame in frames[1:]
    ) * Fraction(0.05)
    evidence = {
        "source_states": states,
        "state_frames": frames,
        "history_assumptions": dict.fromkeys(
            (
                "starting_pose_exact",
                "nominal_tick_binding_exact",
                "stored_word_dt_exact",
                "interval_ending_twist_exact",
            ),
            True,
        ),
        "prefix_history_binding_exact": True,
        "remaining_point_error_m": 1e-8,
        "point_radius_m": 4.0,
    }
    settings = {
        "reference_tick": 22,
        "reference_pose_m_rad": [float(Fraction(2) + distance), 2.0, 0.0],
        "target_speed": 0.5,
        "turn_rate": 1.5 if case == 1 else -1.5 if case == 2 else 0.0,
        "error_evidence": {
            "position_error_m": 0.0,
            "heading_error_rad": 0.0,
            "profile_exact": True,
        },
        "current_body_clear": True,
        "controlled_envelope": True,
        "synthetic_test_only": True,
    }
    if case == 5:
        states.pop(1)
        frames.pop(1)
    elif case == 6:
        settings["reference_tick"] = 21
    elif case == 7:
        evidence["remaining_point_error_m"] = None
    elif case == 8:
        evidence["prefix_history_binding_exact"] = False
    elif case == 9:
        settings["error_evidence"] = None
    elif case == 10:
        settings["error_evidence"]["profile_exact"] = False
    elif case == 11:
        evidence["remaining_point_error_m"] = 2.0
    elif case == 12:
        settings["current_body_clear"] = False
    elif case == 13:
        settings["max_braking_ticks"] = 0
    elif case == 15:
        settings["synthetic_test_only"] = False
    saved_record, saved_evidence = deepcopy(record), deepcopy(evidence)
    before = dict(ledger)
    ledger["wrapper"] += 1
    if case == 15:
        with pytest.raises(ValueError, match="synthetic_test_only"):
            diagnostics._probe_synthetic_c1_command_path_enclosure(
                [record], evidence, **settings
            )
        assert ledger["bridge"] == before["bridge"] and ledger["path"] == before["path"]
        return
    good = diagnostics._probe_synthetic_c1_command_path_enclosure(
        [record], evidence, **settings
    )
    supported = case in (0, 1, 2, 3)
    assert good["fixture_command_path_excluded"] is supported
    expected_bridge = int(case not in (7, 8, 12))
    expected_motion = int(case not in (4, 6, 7, 8, 12))
    expected_path = int(case in (0, 1, 2, 3, 5, 11, 14))
    assert ledger["bridge"] - before["bridge"] == expected_bridge
    assert ledger["motion"] - before["motion"] == expected_motion
    assert ledger["path"] - before["path"] == expected_path
    assert ledger["history"] - before["history"] == expected_path
    assert ledger["cell"] - before["cell"] == int(case in (0, 1, 2, 3, 14))
    assert good["work"] == {
        "state_motion_entries": expected_bridge,
        "path_entries": expected_path,
    }
    results = [good]
    if supported:
        assert good["current_state_frame_hex"] == frames[-1].hex()
        assert (
            good["state_motion"]["source_intervals"]
            == good["path_enclosure"]["registration_bound"]["source_bindings"][-1]
        )
        assert (
            good["path_enclosure"]["registration_bound"]["upper_bounds"][
                "registered_point_m"
            ]
            > 0
        )
        assert generated[0] == good["state_motion"]["motion"]
        assert good["requested_command"] == {
            "target_speed_m_s": settings["target_speed"],
            "turn_rate_rad_s": settings["turn_rate"],
        }
        interval = good["state_motion"]["initial_speed_interval_m_s"]
        assert interval == (
            min(current_speed, decode_state(frames[-1]).velocity_m_s[0]),
            max(current_speed, decode_state(frames[-1]).velocity_m_s[0]),
        )
        assert (interval[0] < interval[1]) is (case == 3)
        for value in interval:
            ledger["reference"] += 1
            assert ledger["reference"] <= 32
            reference = _c1_discrete_motion_reference(
                {
                    "initial_speed": value,
                    "target_speed": settings["target_speed"],
                    "turn_rate": settings["turn_rate"],
                }
            )
            for index, box in enumerate(generated[0]["centerline_boxes_m"]):
                point = reference["vertices"][
                    min(index, len(reference["vertices"]) - 1)
                ]
                for coordinate, (lower, upper) in zip(point, box, strict=True):
                    assert (
                        Fraction(lower)
                        <= coordinate[0]
                        <= coordinate[1]
                        <= Fraction(upper)
                    )
    else:
        reasons = {
            4: "source_interval_outside_motion_domain",
            5: "incomplete_frame_history",
            6: "frame_tick_binding_mismatch",
            7: "remaining_point_error_missing",
            8: "unsupported_point_error_evidence",
            10: "unsupported_error_evidence",
            11: "axis_aligned_wall_support_incomplete",
            12: "current_body_clear_not_established",
            13: "braking_budget_exhausted",
            14: "current_frame_history_binding_mismatch",
        }
        assert good["status"] == "unknown" and good["reason"]
        if case != 9:
            assert good["reason"] == reasons[case]
        assert "state_motion" not in good and "path_enclosure" not in good
    if case == 0:
        before = dict(ledger)
        changed = deepcopy(evidence)
        changed["state_frames"][-1] = encode_state(replace(states[-1], sequence=99))
        ledger["wrapper"] += 1
        bad = diagnostics._probe_synthetic_c1_command_path_enclosure(
            [record], changed, **settings
        )
        assert bad["fixture_command_path_excluded"] is False
        assert bad["reason"] == "source_frame_binding_mismatch"
        assert ledger["motion"] == before["motion"] and ledger["path"] == before["path"]
        missing = {**evidence, "remaining_point_error_m": None}
        ledger["wrapper"] += 1
        absent = diagnostics._probe_synthetic_c1_command_path_enclosure(
            [record], missing, **settings
        )
        assert absent["reason"] == "remaining_point_error_missing"
        assert absent["work"] == {"state_motion_entries": 0, "path_entries": 0}
        assert "state_motion" not in bad and "path_enclosure" not in bad
        good["state_motion"]["motion"]["centerline_boxes_m"][0][0][0] = 123.0
        good["path_enclosure"]["registration_bound"]["source_bindings"].clear()
        ledger["wrapper"] += 1
        repeated = diagnostics._probe_synthetic_c1_command_path_enclosure(
            [record], evidence, **settings
        )
        assert repeated["fixture_command_path_excluded"] is True
        assert repeated["state_motion"]["motion"]["centerline_boxes_m"][0][0][0] == 0.0
        assert repeated["path_enclosure"]["registration_bound"]["source_bindings"]
        results.extend((bad, absent, repeated))
    for result in results:
        for flag in (
            "training_approved",
            "real_input_qualified",
            "free_space_qualified",
            "numerically_certified",
            "source_qualified",
            "native_execution_qualified",
            "command_admission_qualified",
        ):
            assert result[flag] is False
    assert evidence == saved_evidence
    assert json.dumps(record, default=json_value, sort_keys=True) == json.dumps(
        saved_record, default=json_value, sort_keys=True
    )


@pytest.mark.parametrize("case", range(4))
def test_synthetic_c1_command_path_startup_and_command_domain(
    c1_discrete_path_fixtures, c1_command_path_ledger, monkeypatch, case
):
    from fractions import Fraction

    from interface.protocol import State, encode_state
    from sim import diagnostics

    ledger = c1_command_path_ledger
    for key, name in (
        ("bridge", "_probe_synthetic_c1_state_motion"),
        ("binding", "_bind_synthetic_c1_state_intervals"),
        ("motion", "_probe_synthetic_c1_discrete_motion"),
        ("path", "_probe_synthetic_c1_discrete_path_enclosure"),
        ("inspection", "inspect_synthetic_c1_history"),
        ("prefix", "_c1_low_free_segments"),
        ("history", "_bound_synthetic_c1_history_registration"),
        ("cell", "_c1_exclude_path_cells"),
    ):
        original = getattr(diagnostics, name)

        def counted(*args, _key=key, _original=original, **kwargs):
            ledger[_key] += 1
            assert ledger[_key] <= (128 if _key == "binding" else 32)
            return _original(*args, **kwargs)

        monkeypatch.setattr(diagnostics, name, counted)

    def forbidden(*args, **kwargs):
        ledger["forbidden"] += 1
        raise AssertionError(
            "startup fixture must not query sectors, collect or actuate"
        )

    for name in (
        "capture_synthetic_c1_views",
        "_c1_curved_centerline",
        "probe_synthetic_c1_enclosure",
        "probe_synthetic_c1_occupied_witness",
        "probe_synthetic_c1_questions",
        "_probe_synthetic_c1_wire_rejection",
    ):
        monkeypatch.setattr(diagnostics, name, forbidden)
    monkeypatch.setattr(RoverEnv, "reset", forbidden)
    monkeypatch.setattr(RoverEnv, "step", forbidden)
    record = deepcopy(c1_discrete_path_fixtures["records"][0])
    states = [State(sequence=tick, timestamp_us=tick * 50000) for tick in range(20, 23)]
    frames = [encode_state(state) for state in states]
    evidence = {
        "source_states": states,
        "state_frames": frames,
        "history_assumptions": dict.fromkeys(
            (
                "starting_pose_exact",
                "nominal_tick_binding_exact",
                "stored_word_dt_exact",
                "interval_ending_twist_exact",
            ),
            True,
        ),
        "prefix_history_binding_exact": True,
        "remaining_point_error_m": 1e-8,
        "point_radius_m": 4.0,
    }
    settings = {
        "reference_tick": 22,
        "reference_pose_m_rad": [2.0, 2.0, 0.0],
        "target_speed": 0.7 if case == 2 else 0.125,
        "turn_rate": 2.0 if case == 3 else 0.0,
        "error_evidence": {
            "position_error_m": 0.0,
            "heading_error_rad": 0.0,
            "profile_exact": True,
        },
        "current_body_clear": case != 1,
        "controlled_envelope": True,
        "synthetic_test_only": True,
    }
    saved_record, saved_evidence = deepcopy(record), deepcopy(evidence)
    before = dict(ledger)
    ledger["wrapper"] += 1
    result = diagnostics._probe_synthetic_c1_command_path_enclosure(
        [record], evidence, **settings
    )
    assert result["fixture_command_path_excluded"] is (case == 0)
    assert ledger["bridge"] - before["bridge"] == int(case != 1)
    assert ledger["motion"] - before["motion"] == int(case == 0)
    for key in ("path", "inspection", "prefix", "history", "cell"):
        assert ledger[key] - before[key] == int(case == 0)
    assert ledger["binding"] - before["binding"] == (4 if case == 0 else int(case != 1))
    if case == 0:
        ledger["reference"] += 1
        assert ledger["reference"] <= 32
        duration = Fraction(0.05)
        distance = duration * duration
        motion = result["state_motion"]["motion"]
        assert result["requested_command"] == {
            "target_speed_m_s": 0.125,
            "turn_rate_rad_s": 0.0,
        }
        assert result["state_motion"]["initial_speed_interval_m_s"] == (0.0, 0.0)
        assert motion["command_speed_interval_m_s"] == [0.05, 0.05]
        assert motion["work"] == {
            "command_ticks": 1,
            "braking_ticks": 1,
            "chords": 2,
            "series_terms": 0,
        }
        for box in motion["centerline_boxes_m"][1:]:
            assert Fraction(box[0][0]) <= distance <= Fraction(box[0][1])
            assert box[1] == [0.0, 0.0]
        assert (
            result["path_enclosure"]["registration_bound"]["upper_bounds"][
                "registered_point_m"
            ]
            == 0.0
        )
        assert result["current_state_frame_hex"] == frames[-1].hex()
    else:
        assert result["reason"] == (
            "current_body_clear_not_established"
            if case == 1
            else "unsupported_command_domain"
        )
        assert result["status"] == "unknown"
        assert "state_motion" not in result and "path_enclosure" not in result
    for flag in (
        "training_approved",
        "real_input_qualified",
        "free_space_qualified",
        "numerically_certified",
        "source_qualified",
        "native_execution_qualified",
        "command_admission_qualified",
    ):
        assert result[flag] is False
    assert evidence == saved_evidence
    assert json.dumps(record, default=json_value, sort_keys=True) == json.dumps(
        saved_record, default=json_value, sort_keys=True
    )


@pytest.fixture(scope="module")
def c1_initial_setup_ledger(request):
    counts = {"checker": 0, "digest": 0, "forbidden": 0}
    yield counts
    assert counts["checker"] <= 24 and counts["digest"] <= 16
    assert counts["forbidden"] == 0
    capture = request.config.pluginmanager.getplugin("capturemanager")
    if capture is None:
        print("C1 initial-setup ledger:", json.dumps(counts, sort_keys=True))
    else:
        with capture.global_and_fixture_disabled():
            print("C1 initial-setup ledger:", json.dumps(counts, sort_keys=True))


@pytest.mark.parametrize("case", range(16))
def test_synthetic_c1_initial_setup_owns_domain_and_body(
    c1_initial_setup_ledger, monkeypatch, case
):
    from dataclasses import replace
    from fractions import Fraction

    from sim import diagnostics

    ledger = c1_initial_setup_ledger
    scene = Scenario(
        start=(2.0, 2.0, 0.0),
        obstacles=((2.3, 2.0, 0.05),) if case in (1, 4, 5, 6, 12) else (),
    )
    settings = {"epoch": "a" * 32, "synthetic_test_only": True}
    expected = "declared_domain_and_initial_body_strictly_separated"
    if case == 2:
        scene = replace(scene, obstacles=((2.25, 2.0, 0.07),))
        assert Fraction(0.18) + Fraction(0.07) == Fraction(0.25)
        expected = "initial_body_contact_or_overlap"
    elif case == 3:
        scene = replace(scene, start=(0.18, 2.0, 0.0))
        expected = "initial_body_contact_or_overlap"
    elif case == 4:
        scene = replace(scene, obstacles=((2.3, 2.0, 0.005),))
        expected = "unsupported_initial_setup_domain"
    elif case == 5:
        scene = replace(scene, obstacle_heights=(0.01,))
        expected = "unsupported_initial_setup_domain"
    elif case == 6:
        scene = replace(scene, obstacle_heights=(0.5, 0.5))
        expected = "unsupported_initial_setup"
    elif case == 7:
        scene = {"initial_body_clear": True, "controlled_envelope": True}
        expected = "unsupported_initial_setup"
    elif case == 8:
        scene = replace(scene, start=(True, 2.0, 0.0))
        expected = "malformed_initial_setup_or_profile"
    elif case == 9:
        scene = replace(scene, start=(2**54 + 1, 2.0, 0.0))
        expected = "malformed_initial_setup_or_profile"
    elif case == 10:
        settings["epoch"] = True
        expected = "unsupported_setup_epoch"
    elif case == 11:
        settings["config"] = Config()
        expected = "malformed_initial_setup_or_profile"
    elif case == 12:
        settings["max_obstacles"] = 0
        expected = "setup_obstacle_budget_exhausted"
    elif case == 13:
        settings["max_integer_bits"] = 8
        expected = "integer_budget_exhausted"
    elif case == 14:
        settings["synthetic_test_only"] = False
    elif case == 15:
        settings["config"] = Config(noise_std=0, dropout=0, wall_height=0.5)
        expected = "unsupported_initial_setup_profile"
    saved_scene, saved_settings = deepcopy(scene), deepcopy(settings)
    original_digest = diagnostics._c1_source_binding_digest

    def digest(*args, **kwargs):
        ledger["digest"] += 1
        assert ledger["digest"] <= 16
        return original_digest(*args, **kwargs)

    def forbidden(*args, **kwargs):
        ledger["forbidden"] += 1
        raise AssertionError(
            "initial setup must not capture, move, query or audit current truth"
        )

    monkeypatch.setattr(diagnostics, "_c1_source_binding_digest", digest)
    for name in (
        "capture_synthetic_c1_views",
        "inspect_synthetic_c1_history",
        "_audit_synthetic_c1_source_binding",
        "_probe_synthetic_c1_discrete_motion",
        "_probe_synthetic_c1_command_path_enclosure",
        "probe_synthetic_c1_questions",
        "write_episode",
    ):
        monkeypatch.setattr(diagnostics, name, forbidden)
    monkeypatch.setattr(RoverEnv, "reset", forbidden)
    monkeypatch.setattr(RoverEnv, "step", forbidden)

    def check(**changes):
        ledger["checker"] += 1
        assert ledger["checker"] <= 24
        return diagnostics._check_synthetic_c1_initial_setup(
            scene, **{**settings, **changes}
        )

    if case == 14:
        with pytest.raises(ValueError, match="synthetic_test_only"):
            check()
        return
    result = check()
    assert result["reason"] == expected
    assert result["fixture_initial_body_clear"] is (case in (0, 1))
    assert result["fixture_controlled_envelope"] is (case in (0, 1))
    assert result["status"] == (
        "checked_declared_initial_fixture" if case in (0, 1) else "unknown"
    )
    for flag in (
        "training_approved",
        "real_input_qualified",
        "free_space_qualified",
        "numerically_certified",
        "source_qualified",
        "native_execution_qualified",
        "command_admission_qualified",
    ):
        assert result[flag] is False
    if case in (0, 1):
        assert result["work"] == {"obstacles_inspected": case, "body_checks": 4 + case}
        assert result["binding"]["epoch"] == settings["epoch"]
        assert result["binding"]["scenario"]["start"] == scene.start
        assert result["setup_sha256"] == digest(result["binding"])
        if case == 1:
            delta = Fraction(2.3) - Fraction(2.0)
            radii = Fraction(0.18) + Fraction(0.05)
            assert delta * delta > radii * radii
        else:
            saved = deepcopy(result)
            result["binding"]["scenario"]["start"] = (0.0, 0.0, 0.0)
            result["binding"]["config"]["radius"] = 10.0
            result["work"]["body_checks"] = 100
            assert check() == saved
            foreign = check(epoch="b" * 32)
            assert foreign["config_sha256"] == saved["config_sha256"]
            assert foreign["setup_sha256"] != saved["setup_sha256"]
    else:
        assert "binding" not in result and "setup_sha256" not in result
    assert scene == saved_scene and settings == saved_settings


@pytest.fixture(scope="module")
def c1_startup_path_fixtures(request):
    from sim import diagnostics

    counts = dict.fromkeys(
        (
            "capture",
            "setup_preparation",
            "wrapper",
            "setup",
            "digest",
            "binding",
            "command",
            "bridge",
            "motion",
            "path",
            "inspection",
            "prefix",
            "history",
            "cell",
            "forbidden",
        ),
        0,
    )
    records, setups = [], []
    for obstacles in ((), ((2.3, 2.0, 0.05),)):
        scene = Scenario(start=(2.0, 2.0, 0.0), obstacles=obstacles)
        counts["capture"] += 1
        records.append(
            diagnostics.capture_synthetic_c1_views(
                scene, pose_m_rad=scene.start, capture_tick=0, synthetic_test_only=True
            )
        )
        counts["setup_preparation"] += 1
        setups.append(
            diagnostics._check_synthetic_c1_initial_setup(
                scene, epoch="a" * 32, synthetic_test_only=True
            )
        )
    yield {"records": records, "setups": setups, "counts": counts}
    assert counts["capture"] == counts["setup_preparation"] == 2
    assert (
        counts["forbidden"] == 0 and counts["binding"] <= 192 and counts["digest"] <= 96
    )
    assert all(
        counts[key] <= 32
        for key in (
            "wrapper",
            "setup",
            "command",
            "bridge",
            "motion",
            "path",
            "inspection",
            "prefix",
            "history",
            "cell",
        )
    )
    capture = request.config.pluginmanager.getplugin("capturemanager")
    if capture is None:
        print("C1 startup-path ledger:", json.dumps(counts, sort_keys=True))
    else:
        with capture.global_and_fixture_disabled():
            print("C1 startup-path ledger:", json.dumps(counts, sort_keys=True))


@pytest.mark.parametrize("case", range(16))
def test_synthetic_c1_startup_path_uses_rechecked_rest_setup(
    c1_startup_path_fixtures, monkeypatch, case
):
    from dataclasses import replace
    from fractions import Fraction

    from interface.protocol import State, encode_state
    from sim import diagnostics

    fixtures = c1_startup_path_fixtures
    ledger = fixtures["counts"]
    for key, name in (
        ("setup", "_check_synthetic_c1_initial_setup"),
        ("digest", "_c1_source_binding_digest"),
        ("binding", "_bind_synthetic_c1_state_intervals"),
        ("command", "_probe_synthetic_c1_command_path_enclosure"),
        ("bridge", "_probe_synthetic_c1_state_motion"),
        ("motion", "_probe_synthetic_c1_discrete_motion"),
        ("path", "_probe_synthetic_c1_discrete_path_enclosure"),
        ("inspection", "inspect_synthetic_c1_history"),
        ("prefix", "_c1_low_free_segments"),
        ("history", "_bound_synthetic_c1_history_registration"),
        ("cell", "_c1_exclude_path_cells"),
    ):
        original = getattr(diagnostics, name)

        def counted(*args, _key=key, _original=original, **kwargs):
            ledger[_key] += 1
            assert ledger[_key] <= (
                192 if _key == "binding" else 96 if _key == "digest" else 32
            )
            return _original(*args, **kwargs)

        monkeypatch.setattr(diagnostics, name, counted)

    def forbidden(*args, **kwargs):
        ledger["forbidden"] += 1
        raise AssertionError(
            "startup join must not capture, choose questions, collect or actuate"
        )

    for name in (
        "capture_synthetic_c1_views",
        "_audit_synthetic_c1_source_binding",
        "probe_synthetic_c1_questions",
        "probe_synthetic_c1_relative_questions",
        "_probe_synthetic_c1_wire_rejection",
        "write_episode",
    ):
        monkeypatch.setattr(diagnostics, name, forbidden)
    monkeypatch.setattr(RoverEnv, "reset", forbidden)
    monkeypatch.setattr(RoverEnv, "step", forbidden)
    index = int(case == 1)
    record = deepcopy(fixtures["records"][index])
    states = [
        State(sequence=tick, timestamp_us=tick * 50000, goal_m=(3.0, 1.0, 0.0))
        for tick in range(3)
    ]
    if case == 2:
        states[1] = replace(states[1], velocity_m_s=(-0.0, 0.0, 0.0))
    elif case == 7:
        states[1] = replace(states[1], velocity_m_s=(0.2, 0.0, 0.0))
    frames = [encode_state(state) for state in states]
    evidence = {
        "epoch": "a" * 32,
        "initial_setup": deepcopy(fixtures["setups"][index]),
        "point_error_evidence": {
            "source_states": states,
            "state_frames": frames,
            "history_assumptions": dict.fromkeys(
                (
                    "starting_pose_exact",
                    "nominal_tick_binding_exact",
                    "stored_word_dt_exact",
                    "interval_ending_twist_exact",
                ),
                True,
            ),
            "prefix_history_binding_exact": True,
            "remaining_point_error_m": 1e-8,
            "point_radius_m": 4.0,
        },
    }
    settings = {
        "reference_tick": 2,
        "reference_pose_m_rad": [2.0, 2.0, 0.0],
        "error_evidence": {
            "position_error_m": 0.0,
            "heading_error_rad": 0.0,
            "profile_exact": True,
        },
        "synthetic_test_only": True,
    }
    if case == 3:
        evidence["initial_setup"] = {
            "fixture_initial_body_clear": True,
            "fixture_controlled_envelope": True,
        }
    elif case == 4:
        evidence["epoch"] = "b" * 32
    elif case == 5:
        evidence["initial_setup"]["binding"]["config"]["dt"] = 0.1
    elif case == 6:
        evidence["initial_setup"]["binding"]["scenario"]["start"] = (2.1, 2.0, 0.0)
    elif case == 8:
        del states[1]
        del frames[1]
    elif case == 9:
        frames[1] = encode_state(replace(states[1], sequence=9))
    elif case == 10:
        settings["reference_pose_m_rad"][0] = 2.1
    elif case == 11:
        evidence["initial_setup"]["work"]["body_checks"] = True
    elif case == 12:
        settings["error_evidence"] = None
    elif case == 13:
        settings["max_braking_ticks"] = 0
    elif case == 14:
        evidence["point_error_evidence"]["history_assumptions"][
            "starting_pose_exact"
        ] = False
    elif case == 15:
        settings["synthetic_test_only"] = False
    saved_record, saved_evidence, saved_settings = (
        deepcopy(record),
        deepcopy(evidence),
        deepcopy(settings),
    )

    def check():
        ledger["wrapper"] += 1
        assert ledger["wrapper"] <= 32
        return diagnostics._probe_synthetic_c1_startup_path_enclosure(
            [record], evidence, **settings
        )

    if case == 15:
        with pytest.raises(ValueError, match="synthetic_test_only"):
            check()
        return
    before = dict(ledger)
    result = check()
    assert result["fixture_startup_path_excluded"] is (case in (0, 1, 2))
    assert ledger["setup"] - before["setup"] == int(case not in (3, 4, 5, 11))
    assert ledger["command"] - before["command"] == int(case in (0, 1, 2, 12, 13))
    assert ledger["motion"] - before["motion"] == int(case in (0, 1, 2, 12, 13))
    for flag in (
        "training_approved",
        "real_input_qualified",
        "free_space_qualified",
        "numerically_certified",
        "source_qualified",
        "native_execution_qualified",
        "command_admission_qualified",
    ):
        assert result[flag] is False
    if case in (0, 1, 2):
        assert result["initial_setup"] == evidence["initial_setup"]
        assert result["command_path"]["requested_command"] == {
            "target_speed_m_s": 0.125,
            "turn_rate_rad_s": 0.0,
        }
        assert result["work"] == {
            "setup_entries": 1,
            "rest_binding_entries": 3,
            "command_entries": 1,
        }
        distance = Fraction(0.05) ** 2
        box = result["command_path"]["state_motion"]["motion"]["centerline_boxes_m"][-1]
        assert Fraction(box[0][0]) <= distance <= Fraction(box[0][1])
        if case == 0:
            saved_result = deepcopy(result)
            result["initial_setup"]["binding"]["scenario"]["start"] = (0.0, 0.0, 0.0)
            result["command_path"]["requested_command"]["target_speed_m_s"] = 0.6
            assert check() == saved_result
    else:
        assert (
            result["status"] == "unknown"
            and "initial_setup" not in result
            and "command_path" not in result
        )
        assert (
            result["reason"]
            == {
                3: "unsupported_startup_evidence",
                4: "startup_epoch_mismatch",
                5: "startup_config_mismatch",
                6: "startup_setup_content_mismatch",
                7: "initial_history_not_exact_rest",
                8: "unsupported_initial_rest_history",
                9: "source_frame_binding_mismatch",
                10: "startup_initial_pose_mismatch",
                11: "unsupported_startup_evidence",
                12: "error_evidence_missing",
                13: "braking_budget_exhausted",
                14: "unsupported_initial_rest_history",
            }[case]
        )
    assert evidence == saved_evidence and settings == saved_settings
    assert json.dumps(record, default=json_value, sort_keys=True) == json.dumps(
        saved_record, default=json_value, sort_keys=True
    )


def _c1_discrete_motion_reference(settings, *, max_terms=16, max_bits=16384):
    from fractions import Fraction

    used = 0

    def number(value):
        numerator, denominator = float(value).as_integer_ratio()
        if max(abs(numerator).bit_length(), denominator.bit_length()) > max_bits:
            raise ArithmeticError("reference_integer_budget_exhausted")
        return Fraction(numerator, denominator)

    def calculate(operation, first, second):
        first_bits = max(
            abs(first.numerator).bit_length(), first.denominator.bit_length()
        )
        second_bits = max(
            abs(second.numerator).bit_length(), second.denominator.bit_length()
        )
        if first_bits + second_bits + 1 > max_bits:
            raise ArithmeticError("reference_integer_budget_exhausted")
        if operation == "+":
            return first + second
        if operation == "-":
            return first - second
        if operation == "*":
            return first * second
        if operation == "/":
            return first / second
        return first < second

    def order(values):
        lowest = highest = values[0]
        for value in values[1:]:
            if calculate("<", value, lowest):
                lowest = value
            if calculate("<", highest, value):
                highest = value
        return lowest, highest

    def multiply(first, second):
        return order(
            [calculate("*", left, right) for left in first for right in second]
        )

    def clipped(value, lower, upper):
        if calculate("<", value, lower):
            return lower
        return upper if calculate("<", upper, value) else value

    zero, one, duration = number(0), number(1), number(0.05)
    acceleration_step = duration
    initial = settings["initial_speed"]
    speed = tuple(
        number(value)
        for value in (initial if type(initial) is tuple else (initial, initial))
    )
    target = clipped(number(settings["target_speed"]), zero, number(0.6))
    angular_rate = clipped(number(settings["turn_rate"]), number(-1.5), number(1.5))
    speed = tuple(
        calculate(
            "+",
            value,
            clipped(
                calculate("-", target, value), -acceleration_step, acceleration_step
            ),
        )
        for value in speed
    )
    first_speeds = speed
    integrals = []
    if angular_rate:
        if max_terms == 0:
            raise ArithmeticError("reference_term_budget_exhausted")
        square = calculate(
            "*",
            calculate("*", angular_rate, angular_rate),
            calculate("*", duration, duration),
        )
        for parity in (0, 1):
            partial, term = zero, zero
            for index in range(8):
                if used >= max_terms:
                    raise ArithmeticError("reference_term_budget_exhausted")
                used += 1
                if index == 0:
                    term = (
                        duration
                        if parity == 0
                        else calculate(
                            "/",
                            calculate(
                                "*", angular_rate, calculate("*", duration, duration)
                            ),
                            number(2),
                        )
                    )
                else:
                    divisor = number((2 * index + parity) * (2 * index + parity + 1))
                    term = -calculate("/", calculate("*", term, square), divisor)
                if index < 7:
                    partial = calculate("+", partial, term)
                else:
                    integrals.append(order((partial, calculate("+", partial, term))))
        sine = multiply((angular_rate, angular_rate), integrals[0])
        omega_integral = multiply((angular_rate, angular_rate), integrals[1])
        cosine = (
            calculate("-", one, omega_integral[1]),
            calculate("-", one, omega_integral[0]),
        )
    else:
        integrals = [(duration, duration), (zero, zero)]
        cosine, sine = (one, one), (zero, zero)
    point = tuple(multiply(speed, component) for component in integrals)
    vertices = [((zero, zero), (zero, zero)), point]
    speeds = [speed]
    while speed[1] != zero:
        assert len(speeds) <= 16
        speed = tuple(
            clipped(calculate("-", value, acceleration_step), zero, number(0.6))
            for value in speed
        )
        distance = multiply(speed, (duration, duration))
        movement = [multiply(distance, direction) for direction in (cosine, sine)]
        point = tuple(
            tuple(calculate("+", value, delta) for value, delta in zip(component, step))
            for component, step in zip(point, movement)
        )
        vertices.append(point)
        speeds.append(speed)
    deviation = calculate(
        "/",
        calculate(
            "*",
            calculate("*", first_speeds[1], abs(angular_rate)),
            calculate("*", duration, duration),
        ),
        number(8),
    )
    return {
        "vertices": vertices,
        "speeds": speeds,
        "deviation": deviation,
        "terms": used,
    }


@pytest.fixture(scope="module")
def c1_discrete_motion_fixtures(request):
    from sim import diagnostics

    ledger = {"cases": 0, "producer": 0, "reference": 0, "forbidden": 0}

    def producer(settings):
        ledger["producer"] += 1
        assert ledger["producer"] <= 32
        return diagnostics._probe_synthetic_c1_discrete_motion(**settings)

    def reference(settings, **limits):
        ledger["reference"] += 1
        assert ledger["reference"] <= 32
        return _c1_discrete_motion_reference(settings, **limits)

    def forbidden(*args, **kwargs):
        ledger["forbidden"] += 1
        raise AssertionError("motion fixtures cannot call C1/source/runtime paths")

    yield ledger, producer, reference, forbidden
    assert ledger["cases"] == 16
    assert ledger["producer"] <= 32 and ledger["reference"] <= 32
    assert ledger["forbidden"] == 0
    capture = request.config.pluginmanager.getplugin("capturemanager")
    message = "C1 discrete-motion ledger: " + json.dumps(ledger, sort_keys=True)
    if capture is None:
        print(message)
    else:
        with capture.global_and_fixture_disabled():
            print(message)


@pytest.mark.parametrize(
    "case", range(1, 17), ids=[f"G{number:02}" for number in range(1, 17)]
)
def test_synthetic_c1_discrete_motion(c1_discrete_motion_fixtures, monkeypatch, case):
    import struct
    from fractions import Fraction

    from sim import diagnostics

    ledger, producer, reference, forbidden = c1_discrete_motion_fixtures
    ledger["cases"] += 1
    for name in (
        "inspect_synthetic_c1_history",
        "probe_synthetic_c1_enclosure",
        "probe_synthetic_c1_occupied_witness",
        "probe_synthetic_c1_questions",
        "probe_synthetic_c1_relative_questions",
        "capture_synthetic_c1_views",
        "prepare_synthetic_c1_relative_input",
        "_probe_synthetic_c1_wire_rejection",
        "_c1_curved_centerline",
    ):
        monkeypatch.setattr(diagnostics, name, forbidden)
    monkeypatch.setattr(RoverEnv, "reset", forbidden)
    monkeypatch.setattr(RoverEnv, "step", forbidden)
    settings = {
        "initial_speed": 0.5,
        "target_speed": 0.5,
        "turn_rate": 0.0,
        "error_evidence": {
            "position_error_m": 0.0,
            "heading_error_rad": 0.0,
            "profile_exact": True,
        },
        "synthetic_test_only": True,
    }
    if case == 1:
        settings.update(initial_speed=0.0, target_speed=0.125)
    elif case == 3:
        settings["target_speed"] = 1.0
    elif case == 4:
        settings.update(initial_speed=0.125, target_speed=0.0)
    elif case in (5, 6, 15):
        settings["turn_rate"] = -1.5 if case == 6 else 1.5
    elif case in (7, 8):
        words = (
            (0x3FC999999999999A, 0x3FC99999A0000000)
            if case == 7
            else (0x3FD6666660000000, 0x3FD6666666666666)
        )
        settings.update(
            initial_speed=tuple(
                struct.unpack(">d", word.to_bytes(8, "big"))[0] for word in words
            ),
            turn_rate=0.75 if case == 7 else -0.75,
        )
    elif case == 9:
        settings["error_evidence"] = None
    elif case == 10:
        settings.update(initial_speed=True, target_speed=math.inf, turn_rate=math.nan)
    elif case == 11:
        settings.update(
            hold_ticks=2,
            profile={
                "dt": 0.05,
                "acceleration": 0.0,
                "max_speed": 0.6,
                "max_turn_rate": 1.5,
                "radius": 0.18,
            },
        )
    elif case in (13, 14):
        settings["max_braking_ticks" if case == 13 else "max_chords"] = 0
    original = deepcopy(settings)
    if case == 10:
        with pytest.raises(ValueError):
            producer(settings)
        assert settings["initial_speed"] is True
        assert settings["target_speed"] == math.inf and math.isnan(
            settings["turn_rate"]
        )
        return
    result = producer(settings)
    assert settings == original
    assert all(
        result[field] is False
        for field in (
            "training_approved",
            "real_input_qualified",
            "free_space_qualified",
            "numerically_certified",
            "source_qualified",
            "native_execution_qualified",
            "command_admission_qualified",
        )
    )
    if case in (9, 11, 13, 14):
        reasons = {
            9: "error_evidence_missing",
            11: "unsupported_profile_or_hold",
            13: "braking_budget_exhausted",
            14: "chord_budget_exhausted",
        }
        assert result["status"] == "unknown" and result["reason"] == reasons[case]
        assert result["fixture_motion_enclosed"] is False
        assert "chords" not in result and "centerline_boxes_m" not in result
        return
    assert result["status"] == "enclosed_under_fixture_assumptions"
    assert result["fixture_motion_enclosed"] is True
    if case in (15, 16):
        held = deepcopy(result)
        if case == 16:
            assert producer(settings) == result
        with pytest.raises(
            ArithmeticError,
            match="reference_term_budget_exhausted"
            if case == 15
            else "reference_integer_budget_exhausted",
        ):
            reference(settings, **({"max_terms": 0} if case == 15 else {"max_bits": 1}))
        assert result == held
        return
    expected = reference(settings)
    if case == 6:
        mirrored_settings = deepcopy(settings)
        mirrored_settings["turn_rate"] = 1.5
        mirrored = reference(mirrored_settings)
        for point, reflected in zip(expected["vertices"], mirrored["vertices"]):
            assert point[0] == reflected[0]
            assert point[1] == (-reflected[1][1], -reflected[1][0])
    assert (
        len(result["chords"])
        == len(expected["vertices"]) - 1
        == result["work"]["chords"]
        <= 128
    )
    assert result["work"]["command_ticks"] == 1
    assert result["work"]["braking_ticks"] == len(expected["speeds"]) - 1 <= 16
    assert result["speed_intervals_m_s"][-1] == [0.0, 0.0]
    assert result["work"]["series_terms"] == expected["terms"] <= 16
    for actual_point, exact_point in zip(
        result["centerline_boxes_m"], expected["vertices"]
    ):
        for (lower, upper), (exact_lower, exact_upper) in zip(
            actual_point, exact_point
        ):
            assert (
                Fraction.from_float(lower)
                <= exact_lower
                <= exact_upper
                <= Fraction.from_float(upper)
            )
    for actual_speed, exact_speed in zip(
        result["speed_intervals_m_s"], expected["speeds"]
    ):
        assert (
            Fraction.from_float(actual_speed[0])
            <= exact_speed[0]
            <= exact_speed[1]
            <= Fraction.from_float(actual_speed[1])
        )
    assert (
        Fraction.from_float(result["command_sagitta_upper_m"]) >= expected["deviation"]
    )
    for index, chord in enumerate(result["chords"]):
        radius = Fraction.from_float(0.18) + (
            expected["deviation"] if index == 0 else 0
        )
        assert Fraction.from_float(chord["radius_upper_m"]) >= radius
        assert chord["start_box_m"] == result["centerline_boxes_m"][index]
        assert chord["end_box_m"] == result["centerline_boxes_m"][index + 1]
    if case in (7, 8):
        assert expected["speeds"][0][0] < expected["speeds"][0][1]
        assert (
            result["command_speed_interval_m_s"][0]
            < result["command_speed_interval_m_s"][1]
        )
    if case == 1:
        assert result["command_speed_interval_m_s"] == [0.05, 0.05]
    if case == 12:
        second = producer(settings)
        held = deepcopy(second)
        result["chords"][0]["end_box_m"][0][0] = 123.0
        assert second == held and settings == original


@pytest.mark.parametrize(
    "word,numerator,denominator,sign",
    [
        (0x0000000000000000, 0, 1, 0),
        (0x8000000000000000, 0, 1, 1),
        (0x3FF0000000000000, 1, 1, 0),
        (0xBFF0000000000000, -1, 1, 1),
        (0x0000000000000001, 1, 1 << 1074, 0),
        (0x0010000000000000, 1, 1 << 1022, 0),
        (0x8000000000000001, -1, 1 << 1074, 1),
        (0x000FFFFFFFFFFFFF, (1 << 52) - 1, 1 << 1074, 0),
        (0x7FEFFFFFFFFFFFFF, ((1 << 53) - 1) << 971, 1, 0),
    ],
)
def test_synthetic_arithmetic_literal_word_roundtrip(
    word, numerator, denominator, sign
):
    from fractions import Fraction

    from sim.diagnostics import _synthetic_binary64_value, _synthetic_rn64

    value, actual_sign = _synthetic_binary64_value(word)
    assert value == Fraction(numerator, denominator)
    assert actual_sign == sign
    assert _synthetic_rn64(numerator, denominator, zero_sign=sign) == word


@pytest.mark.parametrize(
    "numerator,denominator,expected",
    [
        ((1 << 53) + 1, 1 << 53, 0x3FF0000000000000),
        ((1 << 53) + 3, 1 << 53, 0x3FF0000000000002),
        (1, 1 << 1075, 0x0000000000000000),
        (-1, 1 << 1075, 0x8000000000000000),
        (3, 1 << 1075, 0x0000000000000002),
        ((1 << 53) - 1, 1 << 1075, 0x0010000000000000),
        ((1 << 54) - 1, 1 << 53, 0x4000000000000000),
        (((1 << 53) - 1) << 971, 1, 0x7FEFFFFFFFFFFFFF),
        (((1 << 54) - 3) << 970, 1, 0x7FEFFFFFFFFFFFFE),
        (-((1 << 53) + 1), 1 << 53, 0xBFF0000000000000),
        ((1 << 54) - 1, 1 << 1076, 0x0010000000000000),
        ((1 << 52) - 1, 1 << 1074, 0x000FFFFFFFFFFFFF),
        (1, 1 << 1076, 0x0000000000000000),
    ],
)
def test_synthetic_arithmetic_literal_rounding(numerator, denominator, expected):
    from sim.diagnostics import _synthetic_rn64

    assert _synthetic_rn64(numerator, denominator) == expected


@pytest.mark.parametrize(
    "word",
    [
        True,
        -1,
        1 << 64,
        0x7FF0000000000000,
        0xFFF0000000000000,
        0x7FF8000000000000,
        None,
    ],
)
def test_synthetic_arithmetic_rejects_invalid_word(word):
    from sim.diagnostics import _synthetic_binary64_value

    with pytest.raises(ValueError):
        _synthetic_binary64_value(word)


@pytest.mark.parametrize(
    "numerator,denominator,zero_sign",
    [
        (True, 1, 0),
        (1, False, 0),
        (1, 0, 0),
        (1, -1, 0),
        (1, 1, True),
        (1, 1, 2),
        (1 << 4096, 1, 0),
        (1, 1 << 4096, 0),
        (((1 << 54) - 1) << 970, 1, 0),
        (1 << 4095, 1 << 4095, 0),
    ],
)
def test_synthetic_arithmetic_rejects_invalid_rounding(
    numerator, denominator, zero_sign
):
    from sim.diagnostics import _synthetic_rn64

    with pytest.raises(ValueError):
        _synthetic_rn64(numerator, denominator, zero_sign=zero_sign)


def _literal_binary64_fraction(word):
    from fractions import Fraction

    exponent = (word >> 52) & 2047
    significand = word & ((1 << 52) - 1)
    if exponent:
        significand += 1 << 52
    signed = -significand if word >> 63 else significand
    return Fraction(signed) * Fraction(2) ** ((exponent or 1) - 1075)


@pytest.mark.parametrize(
    "operation,left,right,expected",
    [
        ("add", 0x8000000000000000, 0x8000000000000000, 0x8000000000000000),
        ("add", 0x8000000000000000, 0x0000000000000000, 0x0000000000000000),
        ("add", 0x3FF0000000000000, 0xBFF0000000000000, 0x0000000000000000),
        ("add", 0x3FF0000000000000, 0x3CA0000000000000, 0x3FF0000000000000),
        ("add", 0x3FF0000000000001, 0x3CA0000000000000, 0x3FF0000000000002),
        ("sub", 0x8000000000000000, 0x0000000000000000, 0x8000000000000000),
        ("sub", 0x8000000000000000, 0x8000000000000000, 0x0000000000000000),
        ("sub", 0x3FF0000000000000, 0x3FF0000000000000, 0x0000000000000000),
        ("sub", 0x3FF0000000000000, 0x3CA0000000000000, 0x3FEFFFFFFFFFFFFF),
        ("mul", 0x8000000000000000, 0xBFF0000000000000, 0x0000000000000000),
        ("mul", 0x0000000000000000, 0xBFF0000000000000, 0x8000000000000000),
        ("mul", 0x0000000000000001, 0x3FE0000000000000, 0x0000000000000000),
        ("mul", 0x0000000000000001, 0xBFE0000000000000, 0x8000000000000000),
        ("mul", 0x4008000000000000, 0x3FE0000000000000, 0x3FF8000000000000),
        ("mul", 0x7FEFFFFFFFFFFFFF, 0x3FF0000000000000, 0x7FEFFFFFFFFFFFFF),
        ("div", 0x8000000000000000, 0x3FF0000000000000, 0x8000000000000000),
        ("div", 0x3FF0000000000000, 0x4008000000000000, 0x3FD5555555555555),
        ("div", 0x4000000000000000, 0x4008000000000000, 0x3FE5555555555555),
        ("div", 0x0010000000000000, 0x4000000000000000, 0x0008000000000000),
        ("div", 0x7FEFFFFFFFFFFFFF, 0x4000000000000000, 0x7FDFFFFFFFFFFFFF),
    ],
)
def test_synthetic_arithmetic_literal_operation(operation, left, right, expected):
    from fractions import Fraction

    from sim.diagnostics import _synthetic_binary64_operation

    cell = _synthetic_binary64_operation(operation, left, right)
    left_value, right_value = map(_literal_binary64_fraction, (left, right))
    if operation == "add":
        exact = left_value + right_value
    elif operation == "sub":
        exact = left_value - right_value
    elif operation == "mul":
        exact = left_value * right_value
    else:
        exact = left_value / right_value
    assert cell["word"] == expected
    assert cell["operation"] == operation and cell["operands"] == (left, right)
    assert Fraction(*cell["exact_ratio"]) == exact
    assert (
        Fraction(*cell["rounding_error_ratio"])
        == _literal_binary64_fraction(expected) - exact
    )


@pytest.mark.parametrize(
    "operation,left,right",
    [
        ("div", 0x3FF0000000000000, 0x0000000000000000),
        ("mul", 0x7FEFFFFFFFFFFFFF, 0x4000000000000000),
        ("pow", 0x3FF0000000000000, 0x3FF0000000000000),
        ([], 0x3FF0000000000000, 0x3FF0000000000000),
    ],
)
def test_synthetic_arithmetic_rejects_invalid_operation(operation, left, right):
    from sim.diagnostics import _synthetic_binary64_operation

    with pytest.raises(ValueError):
        _synthetic_binary64_operation(operation, left, right)


_ARITHMETIC_TRACE_LITERALS = (
    (
        0x0000000000000000,
        0x0000000000000000,
        (
            0x0000000000000000,
            0x0000000000000000,
            0x0000000000000000,
            0x401921FB54442D18,
            0x0000000000000000,
            0x0000000000000000,
            0x400921FB54442D18,
            0x401921FB54442D18,
            0x400921FB54442D18,
            0x400921FB54442D18,
            0x0000000000000000,
        ),
    ),
    (
        0x8000000000000000,
        0x8000000000000000,
        (
            0x8000000000000000,
            0x8000000000000000,
            0x8000000000000000,
            0x401921FB54442D18,
            0x8000000000000000,
            0x8000000000000000,
            0x400921FB54442D18,
            0x401921FB54442D18,
            0x400921FB54442D18,
            0x400921FB54442D18,
            0x0000000000000000,
        ),
    ),
    (
        0x3FF0000000000000,
        0x0000000000000000,
        (
            0x0000000000000000,
            0x0000000000000000,
            0x3FF0000000000000,
            0x401921FB54442D18,
            0x0000000000000000,
            0x3FF0000000000000,
            0x401090FDAA22168C,
            0x401921FB54442D18,
            0x401090FDAA22168C,
            0x401090FDAA22168C,
            0x3FF0000000000000,
        ),
    ),
    (
        0xBFF0000000000000,
        0x0000000000000000,
        (
            0x0000000000000000,
            0x0000000000000000,
            0xBFF0000000000000,
            0x401921FB54442D18,
            0x0000000000000000,
            0xBFF0000000000000,
            0x400121FB54442D18,
            0x401921FB54442D18,
            0x400121FB54442D18,
            0x400121FB54442D18,
            0xBFF0000000000000,
        ),
    ),
    (
        0x400921FB54442D18,
        0x0000000000000000,
        (
            0x0000000000000000,
            0x0000000000000000,
            0x400921FB54442D18,
            0x401921FB54442D18,
            0x0000000000000000,
            0x400921FB54442D18,
            0x401921FB54442D18,
            0x401921FB54442D18,
            0x0000000000000000,
            0x0000000000000000,
            0xC00921FB54442D18,
        ),
    ),
    (
        0xC00921FB54442D18,
        0x0000000000000000,
        (
            0x0000000000000000,
            0x0000000000000000,
            0xC00921FB54442D18,
            0x401921FB54442D18,
            0x0000000000000000,
            0xC00921FB54442D18,
            0x0000000000000000,
            0x401921FB54442D18,
            0x0000000000000000,
            0x0000000000000000,
            0xC00921FB54442D18,
        ),
    ),
    (
        0x0000000000000000,
        0x3FF0000000000000,
        (
            0x3FA999999999999A,
            0x3F9999999999999A,
            0x3F9999999999999A,
            0x401921FB54442D18,
            0x3F804C26BE3B06CF,
            0x3FA999999999999A,
            0x40098861BAAA937E,
            0x401921FB54442D18,
            0x40098861BAAA937E,
            0x40098861BAAA937E,
            0x3FA9999999999980,
        ),
    ),
    (
        0x0000000000000000,
        0xBFF0000000000000,
        (
            0xBFA999999999999A,
            0xBF9999999999999A,
            0xBF9999999999999A,
            0x401921FB54442D18,
            0xBF804C26BE3B06CF,
            0xBFA999999999999A,
            0x4008BB94EDDDC6B2,
            0x401921FB54442D18,
            0x4008BB94EDDDC6B2,
            0x4008BB94EDDDC6B2,
            0xBFA9999999999980,
        ),
    ),
    (
        0x400921FB54442D18,
        0x3FF8000000000000,
        (
            0x3FB3333333333334,
            0x3FA3333333333334,
            0x40096EC82110F9E5,
            0x401921FB54442D18,
            0x3F88723A1D588A38,
            0x4009BB94EDDDC6B2,
            0x40196EC82110F9E5,
            0x401921FB54442D18,
            0x3FB3333333333340,
            0x3FB3333333333340,
            0xC0088861BAAA937E,
        ),
    ),
    (
        0xC00921FB54442D18,
        0xBFF8000000000000,
        (
            0xBFB3333333333334,
            0xBFA3333333333334,
            0xC0096EC82110F9E5,
            0x401921FB54442D18,
            0xBF88723A1D588A38,
            0xC009BB94EDDDC6B2,
            0xBFB3333333333340,
            0x401921FB54442D18,
            0xBFB3333333333340,
            0x4018D52E8777604B,
            0x40088861BAAA937E,
        ),
    ),
    (
        0xC00921FB54442D18,
        0xBD04000000000000,
        (
            0xBCC0000000000000,
            0xBCB0000000000000,
            0xC00921FB54442D18,
            0x401921FB54442D18,
            0xBC945F306DC9C883,
            0xC00921FB54442D19,
            0xBCC0000000000000,
            0x401921FB54442D18,
            0xBCC0000000000000,
            0x401921FB54442D18,
            0x400921FB54442D18,
        ),
    ),
    (
        0x3FF0000000000000,
        0x3CF4000000000000,
        (
            0x3CB0000000000000,
            0x3CA0000000000000,
            0x3FF0000000000000,
            0x401921FB54442D18,
            0x3C845F306DC9C883,
            0x3FF0000000000001,
            0x401090FDAA22168C,
            0x401921FB54442D18,
            0x401090FDAA22168C,
            0x401090FDAA22168C,
            0x3FF0000000000000,
        ),
    ),
)


@pytest.fixture(scope="module")
def synthetic_sinc_binding_pool(request):
    import hashlib
    from pathlib import Path

    from sim import diagnostics

    assert not hasattr(request.config, "workerinput")
    counts = {
        "candidate": 0,
        "enclosure_nested": 0,
        "enclosure_direct": 0,
        "cell": 0,
        "snapshot": 0,
        "checker": 0,
    }
    journal = []
    origin, slot = "candidate", 0
    originals = (
        diagnostics._candidate_synthetic_sinc_word,
        diagnostics._enclose_synthetic_sinc_word,
        diagnostics._certify_synthetic_sinc_cell,
    )
    identities = {
        str(path): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (Path(diagnostics.__file__), Path(__file__))
    }

    def reserve(kind, maximum):
        assert counts[kind] < maximum
        counts[kind] += 1

    def invoke(kind, maximum, helper, argument):
        reserve(kind, maximum)
        entry = {"kind": kind, "slot": slot, "origin": origin, "outcome": "pending"}
        journal.append(entry)
        try:
            output = helper(argument, synthetic_test_only=True)
        except BaseException as error:
            entry["outcome"] = type(error).__name__
            raise
        entry["outcome"] = output["status"]
        return output

    def enclose(word, **keywords):
        assert keywords == {"synthetic_test_only": True}
        return invoke(
            "enclosure_nested" if origin == "candidate" else "enclosure_direct",
            12,
            originals[1],
            word,
        )

    def cell(interval, **keywords):
        assert origin == "candidate" and keywords == {"synthetic_test_only": True}
        return invoke("cell", 12, originals[2], interval)

    def freeze(value, depth=0):
        assert depth <= 8
        if type(value) is dict:
            assert len(value) <= 23 and all(
                type(key) is str and len(key) <= 32 for key in value
            )
            return {key: freeze(item, depth + 1) for key, item in value.items()}
        if type(value) in (tuple, list):
            assert len(value) <= 8
            values = [freeze(item, depth + 1) for item in value]
            return tuple(values) if type(value) is tuple else values
        assert type(value) in (int, str, bool)
        if type(value) is int:
            assert value.bit_length() <= 65536
        if type(value) is str:
            assert len(value) <= 64
        return value

    assert (
        diagnostics._SYNTHETIC_SINC_BITS,
        diagnostics._SYNTHETIC_SINC_CELL_BITS,
        diagnostics._SYNTHETIC_SINC_CELL_STEPS,
    ) == (65536, 65536, 64)
    records = []
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(diagnostics, "_enclose_synthetic_sinc_word", enclose)
        patch.setattr(diagnostics, "_certify_synthetic_sinc_cell", cell)
        for slot in range(12):
            word = _ARITHMETIC_TRACE_LITERALS[slot][2][4]
            origin = "candidate"
            candidate = invoke("candidate", 12, originals[0], word)
            origin = "companion_direct"
            enclosure = enclose(word, synthetic_test_only=True)
            assert (
                type(candidate) is dict
                and len(candidate) == 23
                and candidate["status"] == "candidate_mathematical_sinc_word"
            )
            assert (
                type(enclosure) is dict
                and len(enclosure) == 20
                and enclosure["status"] == "enclosed_mathematical_sinc"
            )
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
                "training_approved",
                "real_input_qualified",
                "free_space_qualified",
                "numerically_certified",
                "producer_parity_qualified",
            }
            assert set(candidate) == common | {
                "identity",
                "native_sinc_status",
                "motion_status",
                "source_status",
                "native_work_status",
                "consumer_status",
                "certificate",
                "enclosure_binding",
            }
            assert set(enclosure) == common | {
                "domain_ratio",
                "native_sinc_status",
                "motion_status",
                "branch",
                "stages",
            }
            zero = word & ((1 << 63) - 1) == 0
            assert set(enclosure["stages"]) == (
                set()
                if zero
                else {
                    "arctangent",
                    "pi",
                    "squared_argument",
                    "coefficients",
                    "polynomial",
                    "remainder",
                }
            )
            if not zero:
                assert set(candidate["work"]["cell"]) == {
                    "search_iterations",
                    "endpoint_iterations",
                    "dyadic_decodes",
                    "midpoint_constructions",
                    "rational_comparisons",
                    "rational_constructions",
                    "max_result_bits",
                }
                assert (
                    type(candidate["work"]["cell"]["endpoint_iterations"]) is list
                    and len(candidate["work"]["cell"]["endpoint_iterations"]) == 2
                )
            reserve("snapshot", 24)
            candidate = freeze(candidate)
            reserve("snapshot", 24)
            enclosure = freeze(enclosure)
            records.append((word, candidate, enclosure))
    assert (
        len(records) == 12
        and counts["candidate"]
        == counts["enclosure_nested"]
        == counts["enclosure_direct"]
        == 12
    )
    assert counts["snapshot"] == 24 and counts["cell"] <= 12
    assert all(
        hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest
        for path, digest in identities.items()
    )
    return {
        "records": tuple(records),
        "counts": counts,
        "journal": journal,
        "source_hashes": identities,
    }


@pytest.fixture(scope="module")
def synthetic_sinc_target_cell_join_checks(request, synthetic_sinc_binding_pool):
    from functools import wraps

    from sim import diagnostics

    names = (
        "_check_synthetic_sinc_target_content",
        "_check_synthetic_sinc_composition",
        "_check_synthetic_sinc_declared_binding",
        "_check_synthetic_cell_certificate",
    )
    originals = tuple(getattr(diagnostics, name) for name in names)
    assert all(
        helper.__code__.co_name == name
        for helper, name in zip(originals, names, strict=True)
    )
    kinds = ("target", "composition", "binding", "cell")
    maxima = dict(zip(kinds, (64, 64, 96, 96), strict=True))
    state = {
        "join": 0,
        "counts": dict.fromkeys(kinds, 0),
        "phases": {kind: {"join": 0, "old": 0} for kind in kinds},
        "journal": [],
        "fault": None,
        "joining": False,
    }

    def invoke(kind, helper, arguments, keywords):
        assert state["counts"][kind] < maxima[kind]
        state["counts"][kind] += 1
        phase = "join" if state["joining"] else "old"
        state["phases"][kind][phase] += 1
        entry = {"kind": kind, "phase": phase, "outcome": "pending"}
        state["journal"].append(entry)
        try:
            fault = state["fault"] if state["joining"] else None
            if kind == "target" and fault == "target_memory":
                raise MemoryError("injected join target delegation")
            output = helper(*arguments, **keywords)
            if kind == "target":
                if fault == "target_stage":
                    output["stages"]["pi"] = ((3, 1), output["stages"]["pi"][1])
                elif fault == "target_schema":
                    output["certificate"] = {}
                elif fault == "target_input":
                    arguments[1]["stages"]["pi"] = (
                        (3, 1),
                        arguments[1]["stages"]["pi"][1],
                    )
                elif fault == "binding_limit":
                    diagnostics._SYNTHETIC_BIND_CHECK_BITS = 1
            elif kind == "composition":
                if fault == "composition_boundary":
                    output["certificate"]["boundaries"] = (
                        (1, 1),
                        output["certificate"]["boundaries"][1],
                    )
                elif fault == "composition_schema":
                    output["stages"] = {}
                elif fault == "target_limit":
                    diagnostics._SYNTHETIC_TARGET_CHECK_BITS = 1
        except BaseException as error:
            entry["outcome"] = type(error).__name__
            raise
        entry["outcome"] = output["status"]
        return output

    def decorate(kind, helper):
        @wraps(helper)
        def wrapped(*arguments, **keywords):
            return invoke(kind, helper, arguments, keywords)

        return wrapped

    with pytest.MonkeyPatch.context() as patch:
        for name, kind, helper in zip(names, kinds, originals, strict=True):
            patch.setattr(diagnostics, name, decorate(kind, helper))
        patch.setattr(
            request.config, "_synthetic_sinc_join_checks", state, raising=False
        )
        try:
            yield state
        finally:
            reporter = request.config.pluginmanager.getplugin("terminalreporter")
            capture = request.config.pluginmanager.getplugin("capturemanager")
            if reporter is not None and capture is not None:
                with capture.global_and_fixture_disabled():
                    reporter.write_line(
                        f"Join attempt ledger: {state['join']}; families: {state['counts']}; "
                        f"phases: {state['phases']}; capture: {synthetic_sinc_binding_pool['counts']}"
                    )


@pytest.fixture(autouse=True)
def synthetic_sinc_join_legacy_reservations(request):
    checks = getattr(request.config, "_synthetic_sinc_join_checks", None)
    selected = request.node.name.split("[", 1)[0]
    if checks is None or selected not in {
        "test_synthetic_sinc_composition",
        "test_synthetic_sinc_declared_binding",
        "test_synthetic_cell_certificate_checker",
    }:
        yield
        return
    legacy = request.getfixturevalue("synthetic_sinc_composition_checks")
    old_start, new_start = len(legacy["journal"]), len(checks["journal"])
    yield
    for kind in ("binding", "cell"):
        old_rows = [row for row in legacy["journal"][old_start:] if row["kind"] == kind]
        new_rows = [row for row in checks["journal"][new_start:] if row["kind"] == kind]
        missing = len(old_rows) - len(new_rows)
        assert missing >= 0
        if missing:
            assert (
                kind == "cell"
                and missing == 1
                and old_rows[-1]["outcome"] == "MemoryError"
            )
            assert checks["counts"][kind] < 96
            checks["counts"][kind] += 1
            checks["phases"][kind]["old"] += 1
            checks["journal"].append(
                {
                    "kind": kind,
                    "phase": "old",
                    "outcome": "MemoryError",
                    "pre_body": True,
                }
            )


@pytest.mark.parametrize("control_index", range(16))
def test_synthetic_sinc_target_cell_join(
    control_index,
    synthetic_sinc_binding_pool,
    synthetic_sinc_target_cell_join_checks,
    monkeypatch,
):
    import ast
    import inspect
    from copy import deepcopy

    from sim import diagnostics

    pool, checks = synthetic_sinc_binding_pool, synthetic_sinc_target_cell_join_checks
    mapping = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 6, 7, 8, 9)
    word, original_candidate, original_enclosure = pool["records"][
        mapping[control_index]
    ]
    originals = deepcopy((original_candidate, original_enclosure))
    candidate, enclosure = deepcopy(originals)
    helper = diagnostics._check_synthetic_sinc_target_cell_join
    attempts = 0
    zero = word & ((1 << 63) - 1) == 0

    def forbidden(*arguments, **keywords):
        raise AssertionError("join reached an excluded producer/native path")

    for name in (
        "_enclose_synthetic_sinc_word",
        "_candidate_synthetic_sinc_word",
        "_certify_synthetic_sinc_cell",
        "_synthetic_binary64_value",
        "_synthetic_rn64",
        "_synthetic_binary64_operation",
        "_trace_synthetic_binary64_rows",
        "_reference_synthetic_c1_motion",
        "_audit_synthetic_controlled_candidate",
        "_SyntheticC1ControlledMotionOwner",
        "_SyntheticC1SourceRecorder",
        "prepare_synthetic_c1_relative_input",
    ):
        monkeypatch.setattr(diagnostics, name, forbidden)
    for name in ("sinc", "sin", "cos", "arctan2"):
        monkeypatch.setattr(diagnostics.np, name, forbidden)
    for name in ("sin", "cos", "atan2"):
        monkeypatch.setattr(diagnostics.math, name, forbidden)
    syntax = ast.parse(inspect.getsource(helper))
    assert not any(
        isinstance(node, (ast.Import, ast.ImportFrom))
        or isinstance(node, ast.Constant)
        and type(node.value) is float
        or isinstance(node, ast.Name)
        and node.id in {"Fraction", "float", "np", "math", "open", "deepcopy"}
        for node in ast.walk(syntax)
    )
    calls = [
        node.func.id
        for node in ast.walk(syntax)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id.startswith("_check_")
    ]
    assert calls == [
        "_check_synthetic_sinc_target_content",
        "_check_synthetic_sinc_composition",
    ]

    def check(expected=word, **keywords):
        nonlocal attempts
        assert attempts < 2 and checks["join"] < 32 and not checks["joining"]
        attempts += 1
        checks["join"] += 1
        checks["joining"] = True
        try:
            return helper(expected, candidate, enclosure, **keywords)
        finally:
            checks["joining"] = False
            checks["fault"] = None

    before = dict(checks["counts"])
    first = check(synthetic_test_only=True)
    saved = deepcopy(first)
    assert first["status"] == (
        "checked_conditional_zero_target_binding"
        if zero
        else "checked_conditional_sinc_target_cell_content"
    ), first
    assert len(first) == 26
    assert first["q_word"] == word and first["sign"] == word >> 63
    assert (
        first["q_ratio"] == enclosure["q_ratio"]
        and first["profile"] == enclosure["configuration"]
    )
    assert first["target"] == enclosure["target"] and first["domain_ratio"] == (1, 64)
    assert (
        first["interval"]
        == enclosure["interval"]
        == candidate["certificate"]["interval"]
    )
    assert (
        first["stages"] == enclosure["stages"]
        and first["certificate"] == candidate["certificate"]
    )
    assert set(first["work"]) == {
        "join_entries",
        "target_entries",
        "composition_entries",
        "target",
        "composition",
    }
    assert tuple(
        first["work"][key]
        for key in ("join_entries", "target_entries", "composition_entries")
    ) == (1, 1, 1)
    assert first["work"]["target"]["rational_constructions"] == (5 if zero else 230)
    assert first["work"]["composition"]["binding_entries"] == 1
    assert first["work"]["composition"]["cell_entries"] == (0 if zero else 1)
    assert first["configuration"]["cell_bit_limit"] == (None if zero else 65536)
    assert {key: checks["counts"][key] - before[key] for key in before} == {
        "target": 1,
        "composition": 1,
        "binding": 1,
        "cell": 0 if zero else 1,
    }
    if zero:
        assert first["work"]["composition"]["cell"] is None
        assert set(first["certificate"]) == {"word", "interval", "branch"}
    else:
        assert first["work"]["composition"]["cell"]["midpoint_recomputations"] == 2
    second_before = dict(checks["counts"])
    if control_index in (0, 1):
        with pytest.raises(ValueError, match="synthetic_test_only"):
            check(synthetic_test_only=False if control_index == 0 else 1)
    elif control_index == 15:
        second = check(synthetic_test_only=True)
        enclosure["stages"]["pi"] = ((0, 1), (0, 1))
        candidate["certificate"]["boundaries"] = ((0, 1), (0, 1))
        second["stages"]["pi"] = ((0, 1), (0, 1))
        second["certificate"]["boundaries"] = ((0, 1), (0, 1))
        second["work"]["target"]["rational_constructions"] = 999
        second["work"]["composition"]["binding"]["rational_constructions"] = 999
    else:
        expected = word
        if control_index == 2:
            enclosure.pop("stages")
        elif control_index == 3:
            expected = word ^ (1 << 63)
        elif control_index == 4:

            class HostileKey:
                def __hash__(self):
                    return hash("enclosure")

                def __eq__(self, other):
                    raise AssertionError("unexpected join key equality")

            value = candidate["work"].pop("enclosure")
            candidate["work"][HostileKey()] = value
        elif control_index in (5, 12):
            monkeypatch.setattr(
                diagnostics,
                "_SYNTHETIC_TARGET_JOIN_BITS",
                65537 if control_index == 5 else 1,
            )
        else:
            faults = {
                6: "target_stage",
                7: "target_schema",
                8: "target_input",
                9: "composition_boundary",
                10: "composition_schema",
                11: "binding_limit",
                13: "target_limit",
                14: "target_memory",
            }
            checks["fault"] = faults[control_index]
            if control_index == 11:
                monkeypatch.setattr(diagnostics, "_SYNTHETIC_BIND_CHECK_BITS", 65536)
            elif control_index == 13:
                monkeypatch.setattr(diagnostics, "_SYNTHETIC_TARGET_CHECK_BITS", 65536)
        if control_index == 14:
            with pytest.raises(MemoryError, match="injected join target delegation"):
                check(synthetic_test_only=True)
        else:
            rejected = check(expected, synthetic_test_only=True)
            assert rejected["status"] == "unresolved_synthetic_sinc_target_cell_join"
            assert (
                len(rejected) == 16
                and "certificate" not in rejected
                and "stages" not in rejected
            )
    if control_index <= 5 or control_index == 12:
        assert checks["counts"] == second_before
    elif control_index in (6, 7, 8, 11, 14):
        assert checks["counts"]["target"] == second_before["target"] + 1
        assert all(
            checks["counts"][key] == second_before[key]
            for key in ("composition", "binding", "cell")
        )
    assert attempts == 2 and first == saved
    assert (original_candidate, original_enclosure) == originals
    for flag in (
        "training_approved",
        "real_input_qualified",
        "free_space_qualified",
        "numerically_certified",
        "producer_parity_qualified",
    ):
        assert first[flag] is False
    assert first["consumer_status"] == "ineligible_isolated_candidate"


@pytest.fixture(scope="module")
def synthetic_sinc_target_checks(request, synthetic_sinc_binding_pool):
    from functools import wraps

    from sim import diagnostics

    state = {"attempts": 0, "journal": [], "work": []}
    original = diagnostics._check_synthetic_sinc_target_content

    @wraps(original)
    def checked(*arguments, **keywords):
        assert state["attempts"] < 32
        state["attempts"] += 1
        entry = {"outcome": "pending"}
        state["journal"].append(entry)
        try:
            output = original(*arguments, **keywords)
        except BaseException as error:
            entry["outcome"] = type(error).__name__
            raise
        entry["outcome"] = output["status"]
        state["work"].append(dict(output["work"]))
        return output

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(diagnostics, "_check_synthetic_sinc_target_content", checked)
        try:
            yield state
        finally:
            reporter = request.config.pluginmanager.getplugin("terminalreporter")
            capture = request.config.pluginmanager.getplugin("capturemanager")
            if reporter is not None and capture is not None:
                maxima = (
                    {
                        key: max(row[key] for row in state["work"])
                        for key in state["work"][0]
                    }
                    if state["work"]
                    else {}
                )
                outcomes = {
                    entry["outcome"]: sum(
                        other["outcome"] == entry["outcome"]
                        for other in state["journal"]
                    )
                    for entry in state["journal"]
                }
                with capture.global_and_fixture_disabled():
                    reporter.write_line(
                        f"Target attempt ledger: {state['attempts']}; outcomes: {outcomes}; "
                        f"work maxima: {maxima}; capture: {synthetic_sinc_binding_pool['counts']}"
                    )


@pytest.mark.parametrize("control_index", range(16))
def test_synthetic_sinc_target_content(
    control_index,
    synthetic_sinc_binding_pool,
    synthetic_sinc_target_checks,
    monkeypatch,
):
    import ast
    import inspect
    from copy import deepcopy

    from sim import diagnostics

    pool = synthetic_sinc_binding_pool
    mapping = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 6, 7, 8, 9)
    word, _, original_record = pool["records"][mapping[control_index]]
    original_saved = deepcopy(original_record)
    record = deepcopy(original_record)
    helper = diagnostics._check_synthetic_sinc_target_content
    attempts = 0

    def forbidden(*arguments, **keywords):
        raise AssertionError("target checker reached an excluded producer/native path")

    for name in (
        "_enclose_synthetic_sinc_word",
        "_candidate_synthetic_sinc_word",
        "_certify_synthetic_sinc_cell",
        "_check_synthetic_sinc_composition",
        "_check_synthetic_sinc_declared_binding",
        "_check_synthetic_cell_certificate",
        "_synthetic_binary64_value",
        "_synthetic_rn64",
        "_synthetic_binary64_operation",
        "_trace_synthetic_binary64_rows",
        "_reference_synthetic_c1_motion",
        "_audit_synthetic_controlled_candidate",
        "_SyntheticC1ControlledMotionOwner",
        "_SyntheticC1SourceRecorder",
        "prepare_synthetic_c1_relative_input",
    ):
        monkeypatch.setattr(diagnostics, name, forbidden)
    for name in ("sinc", "sin", "cos", "arctan2"):
        monkeypatch.setattr(diagnostics.np, name, forbidden)
    for name in ("sin", "cos", "atan2"):
        monkeypatch.setattr(diagnostics.math, name, forbidden)
    syntax = ast.parse(inspect.getsource(helper))
    assert not any(
        isinstance(node, (ast.Import, ast.ImportFrom))
        or isinstance(node, ast.Constant)
        and type(node.value) is float
        or isinstance(node, ast.Name)
        and node.id in {"float", "np", "math", "open", "deepcopy"}
        for node in ast.walk(syntax)
    )

    def check(expected=word, **keywords):
        nonlocal attempts
        assert attempts < 2
        attempts += 1
        return helper(expected, record, **keywords)

    first = check(synthetic_test_only=True)
    saved = deepcopy(first)
    zero = mapping[control_index] < 6
    assert first["status"] == (
        "checked_declared_mathematical_zero_content"
        if zero
        else "checked_declared_mathematical_sinc_content"
    ), first
    assert len(first) == 25
    assert first["q_word"] == word and first["sign"] == word >> 63
    assert first["q_ratio"] == record["q_ratio"]
    assert (
        first["interval"] == record["interval"] and first["stages"] == record["stages"]
    )
    assert first["profile"] == record["configuration"]
    assert first["work"]["canonical_pair_checks"] == (4 if zero else 24)
    assert first["work"]["dyadic_decodes"] == 1
    assert first["work"]["integer_power_steps"] == (0 if zero else 147)
    assert first["work"]["rational_constructions"] == (5 if zero else 230)
    assert first["work"]["rational_operations"] == (0 if zero else 131)
    assert first["work"]["rational_comparisons"] == (2 if zero else 57)
    for key, bound in (
        ("integer_power_steps", 256),
        ("rational_constructions", 512),
        ("rational_operations", 512),
        ("rational_comparisons", 256),
    ):
        assert 0 <= first["work"][key] <= bound
        assert first["configuration"][key + "_limit"] == bound
    assert first["work"]["max_result_bits"] <= 65536
    if control_index in (0, 1):
        monkeypatch.setattr(diagnostics, "Fraction", forbidden)
        with pytest.raises(ValueError, match="synthetic_test_only"):
            check(synthetic_test_only=False if control_index == 0 else 1)
    elif control_index == 15:
        second = check(synthetic_test_only=True)
        record["stages"]["pi"] = ((0, 1), (0, 1))
        record["work"]["rational_operations"] = 999
        second["stages"]["pi"] = ((0, 1), (0, 1))
        second["profile"]["sinc_terms"] = 0
        second["work"]["rational_operations"] = 999
        assert first == saved
    else:
        expected = word
        if control_index == 2:
            record.pop("interval")
        elif control_index == 3:
            expected = word ^ (1 << 63)
        elif control_index == 4:

            class HostileKey:
                def __hash__(self):
                    return hash("rational_operations")

                def __eq__(self, other):
                    raise AssertionError("unexpected target key equality")

            value = record["work"].pop("rational_operations")
            record["work"][HostileKey()] = value
        elif control_index == 5:
            monkeypatch.setattr(diagnostics, "_SYNTHETIC_TARGET_CHECK_BITS", 65537)
        elif control_index == 6:
            record["stages"]["pi"] = ((3, 1), record["stages"]["pi"][1])
        elif control_index == 7:
            arctangents = record["stages"]["arctangent"]
            record["stages"]["arctangent"] = (arctangents[0][::-1], arctangents[1])
        elif control_index == 8:
            coefficients = list(record["stages"]["coefficients"])
            numerator, denominator = coefficients[1]
            coefficients[1] = (numerator + denominator, denominator)
            record["stages"]["coefficients"] = tuple(coefficients)
        elif control_index in (9, 11):
            owner = record["stages"] if control_index == 9 else record
            key = "polynomial" if control_index == 9 else "interval"
            owner[key] = tuple(
                (numerator + denominator, denominator)
                for numerator, denominator in owner[key]
            )
        elif control_index == 10:
            lower, (numerator, denominator) = record["stages"]["remainder"]
            record["stages"]["remainder"] = (
                lower,
                (numerator + denominator, denominator),
            )
        elif control_index == 12:
            monkeypatch.setattr(diagnostics, "_SYNTHETIC_TARGET_CHECK_BITS", 1)
        elif control_index in (13, 14):
            original_fraction = diagnostics.Fraction
            constructions = 0
            monkeypatch.setattr(diagnostics, "_SYNTHETIC_TARGET_CHECK_BITS", 65536)

            def changed_constructor(*arguments, **keywords):
                nonlocal constructions
                constructions += 1
                assert constructions == 1
                if control_index == 14:
                    raise MemoryError("injected target allocation")
                value = original_fraction(*arguments, **keywords)
                diagnostics._SYNTHETIC_TARGET_CHECK_BITS = 1
                return value

            monkeypatch.setattr(diagnostics, "Fraction", changed_constructor)
        if control_index == 14:
            with pytest.raises(MemoryError, match="injected target allocation"):
                check(synthetic_test_only=True)
            assert constructions == 1
        else:
            rejected = check(expected, synthetic_test_only=True)
            assert rejected["status"] == "unresolved_synthetic_sinc_target_content"
            assert (
                len(rejected) == 16
                and "interval" not in rejected
                and "stages" not in rejected
            )
            if control_index == 13:
                assert constructions == rejected["work"]["rational_constructions"] == 1
    assert attempts == 2
    assert first == saved and original_record == original_saved
    for flag in (
        "training_approved",
        "real_input_qualified",
        "free_space_qualified",
        "numerically_certified",
        "producer_parity_qualified",
    ):
        assert first[flag] is False
    assert first["consumer_status"] == "ineligible_isolated_candidate"


@pytest.fixture(scope="module")
def synthetic_sinc_composition_checks(request, synthetic_sinc_binding_pool):
    from functools import wraps

    from sim import diagnostics

    counts = {"composition": 0, "binding": 0, "cell": 0}
    journal = []
    state = {"fault": None, "counts": counts, "journal": journal}
    originals = (
        diagnostics._check_synthetic_sinc_declared_binding,
        diagnostics._check_synthetic_cell_certificate,
    )

    def invoke(kind, helper, arguments, keywords):
        assert counts[kind] < 64
        counts[kind] += 1
        entry = {"kind": kind, "outcome": "pending"}
        journal.append(entry)
        try:
            if kind == "cell" and state["fault"] == "cell_memory":
                raise MemoryError("injected composition allocation")
            output = helper(*arguments, **keywords)
            if kind == "binding" and state["fault"] == "binding_profile":
                output.pop("profile")
            elif kind == "binding" and state["fault"] == "cell_limit":
                diagnostics._SYNTHETIC_CELL_CHECK_BITS = 1
            elif kind == "cell" and state["fault"] == "cell_interval":
                output["certificate"]["interval"] = (
                    (1, 1),
                    output["certificate"]["interval"][1],
                )
            elif kind == "cell" and state["fault"] == "cell_profile":
                output["word"] = output["certificate"]["word"]
        except BaseException as error:
            entry["outcome"] = type(error).__name__
            raise
        entry["outcome"] = output["status"]
        return output

    @wraps(originals[0])
    def binding(*arguments, **keywords):
        return invoke("binding", originals[0], arguments, keywords)

    @wraps(originals[1])
    def cell(*arguments, **keywords):
        return invoke("cell", originals[1], arguments, keywords)

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(diagnostics, "_check_synthetic_sinc_declared_binding", binding)
        patch.setattr(diagnostics, "_check_synthetic_cell_certificate", cell)
        try:
            yield state
        finally:
            reporter = request.config.pluginmanager.getplugin("terminalreporter")
            capture = request.config.pluginmanager.getplugin("capturemanager")
            if reporter is not None and capture is not None:
                with capture.global_and_fixture_disabled():
                    reporter.write_line(
                        f"Composition attempt ledger: {counts}; "
                        f"capture fixture: {synthetic_sinc_binding_pool['counts']}"
                    )


@pytest.mark.parametrize("control_index", range(16))
def test_synthetic_sinc_composition(
    control_index,
    synthetic_sinc_binding_pool,
    synthetic_sinc_composition_checks,
    monkeypatch,
):
    import ast
    import inspect
    from copy import deepcopy

    from sim import diagnostics

    pool = synthetic_sinc_binding_pool
    checks = synthetic_sinc_composition_checks
    mapping = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 6, 7, 8, 9)
    word, original_candidate, original_enclosure = pool["records"][
        mapping[control_index]
    ]
    originals = deepcopy((original_candidate, original_enclosure))
    candidate, enclosure = deepcopy(originals)
    helper = diagnostics._check_synthetic_sinc_composition
    attempts = 0
    checks["fault"] = None

    def forbidden(*arguments, **keywords):
        raise AssertionError("composition reached an excluded producer/native path")

    for name in (
        "_candidate_synthetic_sinc_word",
        "_enclose_synthetic_sinc_word",
        "_certify_synthetic_sinc_cell",
        "_synthetic_binary64_value",
        "_synthetic_rn64",
        "_synthetic_binary64_operation",
        "_trace_synthetic_binary64_rows",
        "_reference_synthetic_c1_motion",
        "_audit_synthetic_controlled_candidate",
        "_SyntheticC1ControlledMotionOwner",
        "_SyntheticC1SourceRecorder",
        "prepare_synthetic_c1_relative_input",
    ):
        monkeypatch.setattr(diagnostics, name, forbidden)
    syntax = ast.parse(inspect.getsource(helper))
    assert not any(
        isinstance(node, (ast.Import, ast.ImportFrom))
        or isinstance(node, ast.Constant)
        and type(node.value) is float
        for node in ast.walk(syntax)
    )
    assert not any(
        isinstance(node, ast.Name)
        and node.id in {"Fraction", "np", "math", "float", "open", "deepcopy"}
        for node in ast.walk(syntax)
    )

    def check(expected=word, **keywords):
        nonlocal attempts
        assert attempts < 2 and checks["counts"]["composition"] < 32
        attempts += 1
        checks["counts"]["composition"] += 1
        return helper(expected, candidate, enclosure, **keywords)

    before = dict(checks["counts"])
    first = check(synthetic_test_only=True)
    saved = deepcopy(first)
    zero = mapping[control_index] < 6
    assert first["status"] == (
        "checked_declared_zero_binding"
        if zero
        else "checked_declared_binding_and_cell_content"
    ), first
    assert first["q_word"] == word and first["sign"] == word >> 63
    assert first["certificate"] == candidate["certificate"]
    assert first["work"]["binding_entries"] == 1
    assert first["work"]["cell_entries"] == (0 if zero else 1)
    assert checks["counts"]["binding"] - before["binding"] == 1
    assert checks["counts"]["cell"] - before["cell"] == (0 if zero else 1)
    if zero:
        assert (
            first["work"]["cell"] is None
            and first["configuration"]["cell_bit_limit"] is None
        )
    else:
        assert first["work"]["binding"]["canonical_pair_checks"] == 35
        assert first["work"]["cell"]["canonical_pair_checks"] == 7
        assert first["work"]["binding"]["dyadic_decodes"] == 1
        assert first["work"]["cell"]["dyadic_decodes"] == 3
        assert first["work"]["cell"]["midpoint_recomputations"] == 2
        assert first["work"]["binding"]["rational_comparisons"] == 8
        assert first["work"]["cell"]["rational_comparisons"] == 3
        assert first["work"]["binding"]["rational_constructions"] == 36
        assert first["work"]["cell"]["rational_constructions"] == 12
    before_second = dict(checks["counts"])
    try:
        if control_index in (0, 1):
            with pytest.raises(ValueError, match="synthetic_test_only"):
                check(synthetic_test_only=False if control_index == 0 else 1)
        elif control_index == 14:
            checks["fault"] = "cell_memory"
            with pytest.raises(MemoryError, match="injected composition allocation"):
                check(synthetic_test_only=True)
        elif control_index == 15:
            second = check(synthetic_test_only=True)
            candidate["work"]["cell"]["endpoint_iterations"][0] = 99
            second["certificate"]["word"] = 0
            second["work"]["binding"]["canonical_pair_checks"] = 99
            second["work"]["cell"]["dyadic_decodes"] = 99
            assert first == saved
        else:
            expected = word
            if control_index == 2:
                candidate.pop("certificate")
            elif control_index == 3:
                expected = pool["records"][1][0]
            elif control_index == 4:

                class HostileKey:
                    def __hash__(self):
                        return hash("enclosure")

                    def __eq__(self, other):
                        raise AssertionError("unexpected composition key equality")

                declared = candidate["work"].pop("enclosure")
                candidate["work"][HostileKey()] = declared
            elif control_index == 5:
                monkeypatch.setattr(diagnostics, "_SYNTHETIC_COMPOSITION_BITS", 65537)
            elif control_index == 6:
                neighbors = candidate["certificate"]["neighbors"]
                candidate["certificate"]["neighbors"] = (
                    neighbors[0],
                    (neighbors[0][0], neighbors[1][1]),
                    neighbors[2],
                )
            elif control_index == 7:
                candidate["certificate"]["boundaries"] = candidate["certificate"][
                    "boundaries"
                ][::-1]
            elif control_index == 8:
                candidate["certificate"]["lower_order"] = float(
                    candidate["certificate"]["lower_order"]
                )
            elif control_index in (9, 10, 11, 13):
                checks["fault"] = {
                    9: "cell_interval",
                    10: "binding_profile",
                    11: "cell_profile",
                    13: "cell_limit",
                }[control_index]
                if control_index == 13:
                    monkeypatch.setattr(
                        diagnostics, "_SYNTHETIC_CELL_CHECK_BITS", 65536
                    )
            elif control_index == 12:
                monkeypatch.setattr(diagnostics, "_SYNTHETIC_COMPOSITION_BITS", 1)
            rejected = check(expected, synthetic_test_only=True)
            assert (
                rejected["status"] == "unresolved_synthetic_sinc_composition"
                and "certificate" not in rejected
            )
            if control_index in (2, 3, 4, 5, 8, 10, 12, 13):
                assert rejected["work"]["cell_entries"] == 0
        assert attempts == 2
        if control_index < 6 or control_index in (8, 10, 12, 13):
            assert checks["counts"]["cell"] == before_second["cell"]
    finally:
        checks["fault"] = None
    assert first == saved and (original_candidate, original_enclosure) == originals
    for flag in (
        "training_approved",
        "real_input_qualified",
        "free_space_qualified",
        "numerically_certified",
        "producer_parity_qualified",
    ):
        assert first[flag] is False
    assert first["consumer_status"] == "ineligible_isolated_candidate"


@pytest.mark.parametrize("control_index", range(16))
def test_synthetic_sinc_declared_binding(
    control_index, synthetic_sinc_binding_pool, monkeypatch
):
    import ast
    import inspect
    from copy import deepcopy

    from sim import diagnostics

    pool = synthetic_sinc_binding_pool
    mapping = (0, 1, 2, 3, 4, 5, 6, 1, 8, 9, 10, 11, 7, 1, 2, 3)
    word, original_candidate, original_enclosure = pool["records"][
        mapping[control_index]
    ]
    originals = deepcopy((original_candidate, original_enclosure))
    candidate, enclosure = deepcopy(originals)
    helper = diagnostics._check_synthetic_sinc_declared_binding
    attempts = 0

    def forbidden(*arguments, **keywords):
        raise AssertionError("binding checker reached an excluded producer/native path")

    for name in (
        "_candidate_synthetic_sinc_word",
        "_enclose_synthetic_sinc_word",
        "_certify_synthetic_sinc_cell",
        "_check_synthetic_cell_certificate",
        "_synthetic_binary64_value",
        "_synthetic_rn64",
        "_synthetic_binary64_operation",
        "_trace_synthetic_binary64_rows",
        "_reference_synthetic_c1_motion",
        "_audit_synthetic_controlled_candidate",
        "_SyntheticC1ControlledMotionOwner",
        "_SyntheticC1SourceRecorder",
        "prepare_synthetic_c1_relative_input",
    ):
        monkeypatch.setattr(diagnostics, name, forbidden)
    syntax = ast.parse(inspect.getsource(helper))
    assert not any(
        isinstance(node, (ast.Import, ast.ImportFrom))
        or isinstance(node, ast.Constant)
        and type(node.value) is float
        for node in ast.walk(syntax)
    )
    assert not any(
        isinstance(node, ast.Name)
        and node.id in {"np", "math", "float", "open", "deepcopy"}
        for node in ast.walk(syntax)
    )

    def check(expected=word, candidate_input=None, enclosure_input=None, **keywords):
        nonlocal attempts
        assert attempts < 2 and pool["counts"]["checker"] < 32
        attempts += 1
        pool["counts"]["checker"] += 1
        return helper(
            expected,
            candidate if candidate_input is None else candidate_input,
            enclosure if enclosure_input is None else enclosure_input,
            **keywords,
        )

    first = check(synthetic_test_only=True)
    saved = deepcopy(first)
    assert first["status"] == "verified_declared_sinc_binding", first["reason"]
    assert first["q_word"] == word and first["sign"] == word >> 63
    ratio = _literal_binary64_fraction(word)
    assert first["q_ratio"] == (ratio.numerator, ratio.denominator)
    zero = word & ((1 << 63) - 1) == 0
    assert first["work"]["canonical_pair_checks"] == (10 if zero else 35)
    assert first["work"]["rational_constructions"] == (11 if zero else 36)
    assert first["work"]["rational_comparisons"] == (2 if zero else 8)
    assert first["work"]["dyadic_decodes"] == 1
    if control_index in (0, 1):
        with pytest.raises(ValueError, match="synthetic_test_only"):
            check(synthetic_test_only=False if control_index == 0 else 1)
    elif control_index == 14:

        def allocate(*arguments):
            raise MemoryError("injected binding allocation")

        monkeypatch.setattr(diagnostics, "Fraction", allocate)
        with pytest.raises(MemoryError, match="injected binding allocation"):
            check(synthetic_test_only=True)
    elif control_index == 15:
        second = check(synthetic_test_only=True)
        candidate["configuration"]["sinc_terms"] = 99
        second["work"]["canonical_pair_checks"] = 99
        second["certificate"]["word"] = 0
        series_original = deepcopy(pool["records"][7][1])
        series_copy = deepcopy(series_original)
        series_copy["work"]["cell"]["endpoint_iterations"][0] = 99
        assert pool["records"][7][1] == series_original
        assert first == saved
    else:
        if control_index == 2:
            enclosure = deepcopy(pool["records"][1][2])
        elif control_index == 3:
            candidate["sign"] = float(candidate["sign"])
        elif control_index == 4:
            enclosure["configuration"]["sinc_terms"] = 8.0
        elif control_index == 5:
            candidate["certificate"]["interval"] = (
                ((1, 1), (1, 1)) if not zero else ((1, 1), (2, 1))
            )
        elif control_index == 6:
            enclosure["stages"].pop("pi")
        elif control_index == 7:
            candidate["certificate"]["branch"] = "series"
        elif control_index == 8:

            class HostileKey:
                def __hash__(self):
                    return hash("enclosure")

                def __eq__(self, other):
                    raise AssertionError("unexpected key equality hook")

            declared = candidate["work"].pop("enclosure")
            candidate["work"][HostileKey()] = declared
        elif control_index == 9:
            enclosure["domain_ratio"] = (2, 128)
        elif control_index == 10:
            enclosure["q_ratio"] = (1 << 65536, 1)
        elif control_index == 11:
            monkeypatch.setattr(diagnostics, "_SYNTHETIC_BIND_CHECK_BITS", 1)
        elif control_index == 12:
            monkeypatch.setattr(diagnostics, "_SYNTHETIC_BIND_CHECK_BITS", 65537)
        else:
            fraction = diagnostics.Fraction

            def changed(*arguments):
                output = fraction(*arguments)
                monkeypatch.setattr(diagnostics, "_SYNTHETIC_BIND_CHECK_BITS", 1)
                return output

            monkeypatch.setattr(diagnostics, "Fraction", changed)
        rejected = check(synthetic_test_only=True)
        assert (
            rejected["status"] == "unresolved_sinc_declared_binding"
            and "certificate" not in rejected
        )
        if control_index == 10:
            assert rejected["work"]["rational_constructions"] == 0
    assert attempts == 2 and (original_candidate, original_enclosure) == originals
    assert first == saved and first["work"]["max_result_bits"] <= 65536
    for flag in (
        "training_approved",
        "real_input_qualified",
        "free_space_qualified",
        "numerically_certified",
        "producer_parity_qualified",
    ):
        assert first[flag] is False
    assert first["consumer_status"] == "ineligible_isolated_candidate"


@pytest.mark.parametrize("control_index", range(16))
def test_synthetic_cell_certificate_checker(control_index, monkeypatch):
    import ast
    import inspect
    from copy import deepcopy
    from fractions import Fraction

    from sim import diagnostics

    unit = 0x3FF0000000000000
    largest = 0x7FEFFFFFFFFFFFFF
    center = Fraction(1)
    lower = center - Fraction(1, 1 << 54)
    upper = center + Fraction(1, 1 << 53)
    odd_center = center + Fraction(1, 1 << 52)
    odd_upper = center + Fraction(3, 1 << 53)
    tiny = Fraction(1, 1 << 1074)
    normal = Fraction(1, 1 << 1022)
    high = _literal_binary64_fraction(largest - 1)
    controls = (
        ((center, center), unit, True),
        ((lower, lower), unit, True),
        ((upper, upper), unit, True),
        (((upper + odd_center) / 2, odd_center), unit + 1, True),
        ((odd_upper, odd_upper), unit + 2, True),
        (((upper + odd_center) / 2, (odd_center + odd_upper) / 2), unit + 1, True),
        ((lower, upper), unit, True),
        ((upper - Fraction(1, 1 << 55), upper + Fraction(1, 1 << 55)), unit, False),
        ((tiny, tiny), 1, True),
        ((normal - tiny / 2, normal - tiny / 2), 0x0010000000000000, True),
        ((high, high), largest - 1, True),
        ((_literal_binary64_fraction(largest),) * 2, largest, False),
        ((Fraction(0), center), unit, False),
        ((tiny / 2, tiny / 2), 1, False),
        ((center, center), unit, False),
        ((center, center), unit, True),
    )

    def pair(value):
        return value.numerator, value.denominator

    def certificate(values, word):
        neighbor_word = min(word, largest - 1)
        adjacent = tuple(
            _literal_binary64_fraction(value)
            for value in (neighbor_word - 1, neighbor_word, neighbor_word + 1)
        )
        boundaries = ((adjacent[0] + adjacent[1]) / 2, (adjacent[1] + adjacent[2]) / 2)
        return {
            "word": word,
            "interval": tuple(pair(value) for value in values),
            "neighbors": tuple(
                (value, pair(decoded))
                for value, decoded in zip(
                    (neighbor_word - 1, neighbor_word, neighbor_word + 1),
                    adjacent,
                    strict=True,
                )
            ),
            "boundaries": tuple(pair(value) for value in boundaries),
            "closed_ties": word % 2 == 0,
            "lower_order": (values[0] > boundaries[0]) - (values[0] < boundaries[0]),
            "upper_order": (values[1] > boundaries[1]) - (values[1] < boundaries[1]),
            "whole_interval_contained": True,
        }

    values, word, expected = controls[control_index]
    record = certificate(values, word)
    if control_index == 14:
        record["interval"] = ((2, 2), (1, 1))
    unit_record = certificate((center, center), unit)
    helper = diagnostics._check_synthetic_cell_certificate
    calls = []
    outputs = []

    def check(value, **keywords):
        calls.append(value)
        assert len(calls) <= 2
        output = helper(value, **keywords)
        outputs.append(output)
        return output

    def forbidden(*arguments, **keywords):
        raise AssertionError("checker reached a producer/native/owner path")

    for name in (
        "_certify_synthetic_sinc_cell",
        "_candidate_synthetic_sinc_word",
        "_enclose_synthetic_sinc_word",
        "_synthetic_binary64_value",
        "_synthetic_rn64",
        "_synthetic_binary64_operation",
        "_trace_synthetic_binary64_rows",
        "_reference_synthetic_c1_motion",
        "_audit_synthetic_controlled_candidate",
        "_SyntheticC1ControlledMotionOwner",
        "_SyntheticC1SourceRecorder",
        "prepare_synthetic_c1_relative_input",
    ):
        monkeypatch.setattr(diagnostics, name, forbidden)
    for module, names in (
        (diagnostics.np, ("sinc", "sin", "cos", "arctan2")),
        (diagnostics.math, ("sin", "cos", "atan2")),
    ):
        for name in names:
            monkeypatch.setattr(module, name, forbidden)
    syntax = ast.parse(inspect.getsource(helper))
    assert not any(
        isinstance(node, ast.Constant) and type(node.value) is float
        for node in ast.walk(syntax)
    )
    assert not any(
        isinstance(node, (ast.Import, ast.ImportFrom)) for node in ast.walk(syntax)
    )
    assert not any(
        isinstance(node, ast.Name)
        and node.id in {"np", "math", "float", "open", "deepcopy"}
        for node in ast.walk(syntax)
    )
    result = check(record, synthetic_test_only=True)
    saved = deepcopy(result)
    if expected:
        assert result["status"] == "verified_synthetic_cell_content", result["reason"]
        assert result["certificate"] == record
        assert result["work"]["canonical_pair_checks"] == 7
        assert result["work"]["dyadic_decodes"] == 3
        assert result["work"]["midpoint_recomputations"] == 2
        assert result["work"]["rational_comparisons"] == 3
        assert result["work"]["rational_constructions"] == 12
    else:
        assert result["status"] == "unresolved_synthetic_cell_content"
        assert "certificate" not in result
    damaged = deepcopy(unit_record)
    if control_index in (0, 1):
        with pytest.raises(ValueError, match="synthetic_test_only"):
            check(damaged, synthetic_test_only=(False if control_index == 0 else 1))
    elif control_index == 10:
        allocations = []

        def allocate(*arguments):
            allocations.append(arguments)
            raise MemoryError("injected checker allocation failure")

        monkeypatch.setattr(diagnostics, "Fraction", allocate)
        with pytest.raises(MemoryError, match="injected checker allocation failure"):
            check(damaged, synthetic_test_only=True)
        assert len(allocations) == 1
    elif control_index == 15:
        repeated = check(record, synthetic_test_only=True)
        record["word"] = 0
        repeated["certificate"]["word"] = 0
        repeated["work"]["rational_constructions"] = 0
    else:
        if control_index == 2:
            damaged["word"] = True
        elif control_index == 3:
            neighbors = list(damaged["neighbors"])
            neighbors[1] = (unit, pair(odd_center))
            damaged["neighbors"] = tuple(neighbors)
        elif control_index == 4:
            damaged["boundaries"] = (pair(center), damaged["boundaries"][1])
        elif control_index == 5:
            damaged["closed_ties"] = False
        elif control_index == 6:
            damaged["lower_order"] = 1.0
        elif control_index == 7:
            damaged["interval"] = ((1 << 65536, 1), (1 << 65536, 1))
        elif control_index == 8:
            monkeypatch.setattr(diagnostics, "_SYNTHETIC_CELL_CHECK_BITS", 1)
        elif control_index == 9:
            original = diagnostics.Fraction
            allocations = []

            def allocate(*arguments):
                allocations.append(arguments)
                monkeypatch.setattr(diagnostics, "_SYNTHETIC_CELL_CHECK_BITS", 1)
                return original(*arguments)

            monkeypatch.setattr(diagnostics, "Fraction", allocate)
        elif control_index == 11:
            damaged["status"] = "verified_synthetic_cell_content"
        elif control_index == 12:

            class HostileDict(dict):
                def __len__(self):
                    raise AssertionError("checker called an input hook")

                def __iter__(self):
                    raise AssertionError("checker called an input hook")

                def __getitem__(self, key):
                    raise AssertionError("checker called an input hook")

                def __deepcopy__(self, memo):
                    raise AssertionError("checker called an input hook")

            damaged = HostileDict(damaged)
        elif control_index == 13:
            monkeypatch.setattr(diagnostics, "_SYNTHETIC_CELL_CHECK_BITS", 65537)
        else:
            damaged["whole_interval_contained"] = False
        rejected = check(damaged, synthetic_test_only=True)
        assert rejected["status"] == "unresolved_synthetic_cell_content"
        assert "certificate" not in rejected
        if control_index in (7, 8):
            assert rejected["work"]["rational_constructions"] == 0
            assert rejected["reason"] == "cell_check_rational_work_limit"
        elif control_index == 9:
            assert len(allocations) == 1
            assert rejected["reason"] == "changed_cell_check_configuration"
        elif control_index == 13:
            assert rejected["reason"] == "unsupported_cell_check_configuration"
    assert len(calls) == 2 and result == saved
    for output in outputs:
        assert output["work"]["canonical_pair_checks"] <= 7
        assert output["work"]["dyadic_decodes"] <= 3
        assert output["work"]["midpoint_recomputations"] <= 2
        assert output["work"]["rational_comparisons"] <= 3
        assert output["work"]["rational_constructions"] <= 12
        assert output["work"]["max_result_bits"] <= 65536
        for flag in (
            "training_approved",
            "real_input_qualified",
            "free_space_qualified",
            "numerically_certified",
            "producer_parity_qualified",
        ):
            assert output[flag] is False
        assert output["native_sinc_status"] == "unresolved_native_sinc_evidence"
        assert output["motion_status"] == "unresolved_motion_evidence"
        assert output["source_status"] == "unresolved_source_authority"
        assert output["native_work_status"] == "unresolved_native_work_evidence"
        assert output["consumer_status"] == "ineligible_isolated_candidate"


@pytest.mark.parametrize("control_index", range(16))
def test_synthetic_sinc_cell_candidate(control_index, monkeypatch):
    from copy import deepcopy
    from fractions import Fraction

    from sim import diagnostics

    unit = 0x3FF0000000000000
    largest = 0x7FEFFFFFFFFFFFFF
    center = Fraction(1)
    lower = center - Fraction(1, 1 << 54)
    upper = center + Fraction(1, 1 << 53)
    odd_center = center + Fraction(1, 1 << 52)
    odd_upper = center + Fraction(3, 1 << 53)
    tiny = Fraction(1, 1 << 1074)
    normal = Fraction(1, 1 << 1022)
    high = _literal_binary64_fraction(largest - 1)
    controls = (
        ((center, center), unit),
        ((lower, lower), unit),
        ((upper, upper), unit),
        (((upper + odd_center) / 2, odd_center), unit + 1),
        ((odd_upper, odd_upper), unit + 2),
        (((upper + odd_center) / 2, (odd_center + odd_upper) / 2), unit + 1),
        ((lower, upper), unit),
        ((upper - Fraction(1, 1 << 55), upper + Fraction(1, 1 << 55)), None),
        ((tiny, tiny), 1),
        ((normal - tiny / 2, normal - tiny / 2), 0x0010000000000000),
        ((high, high), largest - 1),
        ((_literal_binary64_fraction(largest),) * 2, None),
        ((Fraction(0), center), None),
        ((tiny / 2, tiny / 2), None),
        (None, None),
        ((center, center), unit),
    )
    values, expected = controls[control_index]
    interval = (
        tuple((value.numerator, value.denominator) for value in values)
        if values is not None
        else ((2, 2), (1, 1))
    )
    helper = diagnostics._certify_synthetic_sinc_cell
    attempts = []
    outputs = []

    def certify(value, **keywords):
        attempts.append(value)
        assert len(attempts) <= 2
        output = helper(value, **keywords)
        outputs.append(output)
        return output

    result = certify(interval, synthetic_test_only=True)
    saved = deepcopy(result)
    if expected is None:
        assert result["status"] == "unresolved_sinc_cell"
        assert "certificate" not in result
    else:
        certificate = result["certificate"]
        assert result["status"] == "contained_synthetic_sinc_cell"
        assert certificate["word"] == expected
        assert certificate["interval"] == interval
        adjacent = tuple(
            _literal_binary64_fraction(word)
            for word in (expected - 1, expected, expected + 1)
        )
        boundaries = ((adjacent[0] + adjacent[1]) / 2, (adjacent[1] + adjacent[2]) / 2)
        assert certificate["neighbors"] == tuple(
            (word, (value.numerator, value.denominator))
            for word, value in zip(
                (expected - 1, expected, expected + 1), adjacent, strict=True
            )
        )
        assert (
            tuple(Fraction(*pair) for pair in certificate["boundaries"]) == boundaries
        )
        assert certificate["closed_ties"] is (expected % 2 == 0)
        assert certificate["lower_order"] == (values[0] > boundaries[0]) - (
            values[0] < boundaries[0]
        )
        assert certificate["upper_order"] == (values[1] > boundaries[1]) - (
            values[1] < boundaries[1]
        )
        assert certificate["whole_interval_contained"] is True
    if control_index in (0, 1):
        with pytest.raises(ValueError, match="synthetic_test_only"):
            certify(interval, synthetic_test_only=(False if control_index == 0 else 1))
    elif control_index == 2:
        repeated = certify(interval, synthetic_test_only=True)
        repeated["certificate"]["word"] = 0
        repeated["work"]["endpoint_iterations"].clear()
    elif control_index in (8, 9, 10, 11, 13, 15):
        if control_index == 8:
            monkeypatch.setattr(diagnostics, "_SYNTHETIC_SINC_CELL_BITS", 1)
        elif control_index in (9, 10):
            original = diagnostics.Fraction
            allocations = []

            def allocate(*arguments):
                allocations.append(arguments)
                if control_index == 10:
                    raise MemoryError("injected cell allocation failure")
                monkeypatch.setattr(diagnostics, "_SYNTHETIC_SINC_CELL_BITS", 1)
                return original(*arguments)

            monkeypatch.setattr(diagnostics, "Fraction", allocate)
        elif control_index == 11:
            monkeypatch.setattr(diagnostics, "_SYNTHETIC_SINC_CELL_STEPS", 1)
        elif control_index == 13:
            monkeypatch.setattr(diagnostics, "_SYNTHETIC_SINC_CELL_BITS", 65537)
        else:
            monkeypatch.setattr(diagnostics, "_SYNTHETIC_SINC_CELL_STEPS", True)
        if control_index == 10:
            with pytest.raises(MemoryError, match="injected cell allocation failure"):
                certify(interval, synthetic_test_only=True)
            assert len(allocations) == 1
        else:
            rejected = certify(((1, 1), (1, 1)), synthetic_test_only=True)
            assert rejected["status"] == "unresolved_sinc_cell"
            assert "certificate" not in rejected
            reasons = {
                8: "cell_rational_work_limit",
                9: "changed_cell_configuration",
                11: "cell_search_work_limit",
                13: "unsupported_cell_configuration",
                15: "unsupported_cell_configuration",
            }
            assert rejected["reason"] == reasons[control_index]
            if control_index == 9:
                assert len(allocations) == 1
            if control_index == 11:
                assert rejected["work"]["search_iterations"] == 1
    else:
        malformed = {
            3: ((True, 1), (1, 1)),
            4: ((1.0, 1), (1, 1)),
            5: ((1, -1), (1, 1)),
            6: [(1, 1), (1, 1)],
            7: ((2, 1), (1, 1)),
            12: ((1 << 65536, 1), (1 << 65536, 1)),
            14: ((1, 1),),
        }
        rejected = certify(malformed[control_index], synthetic_test_only=True)
        assert rejected["status"] == "unresolved_sinc_cell"
        assert "certificate" not in rejected
        if control_index == 12:
            assert rejected["reason"] == "cell_rational_work_limit"
            assert rejected["work"]["rational_constructions"] == 0
    assert len(attempts) == 2 and result == saved
    for output in outputs:
        assert output["work"]["search_iterations"] <= 128
        assert output["work"]["dyadic_decodes"] <= 265
        assert output["work"]["midpoint_constructions"] <= 134
        assert output["work"]["rational_comparisons"] <= 135
        for flag in (
            "training_approved",
            "real_input_qualified",
            "free_space_qualified",
            "numerically_certified",
            "producer_parity_qualified",
        ):
            assert output[flag] is False


@pytest.mark.parametrize("literal_index", range(12))
def test_synthetic_sinc_word_candidate(literal_index, monkeypatch):
    import ast
    import inspect
    from copy import deepcopy
    from fractions import Fraction

    from sim import diagnostics

    helper = diagnostics._candidate_synthetic_sinc_word
    enclosure_helper = diagnostics._enclose_synthetic_sinc_word
    cell_helper = diagnostics._certify_synthetic_sinc_cell
    counts = {"word": 0, "enclosure": 0, "cell": 0}
    outputs = []

    def candidate(word, **keywords):
        counts["word"] += 1
        assert counts["word"] <= 2
        output = helper(word, **keywords)
        outputs.append(output)
        return output

    def enclose(word, **keywords):
        counts["enclosure"] += 1
        assert counts["enclosure"] <= 2
        return enclosure_helper(word, **keywords)

    def certify(interval, **keywords):
        counts["cell"] += 1
        assert counts["cell"] <= 2
        return cell_helper(interval, **keywords)

    def forbidden(*arguments, **keywords):
        raise AssertionError("candidate reached a producer/native/owner path")

    monkeypatch.setattr(diagnostics, "_enclose_synthetic_sinc_word", enclose)
    monkeypatch.setattr(diagnostics, "_certify_synthetic_sinc_cell", certify)
    for name in (
        "_synthetic_binary64_value",
        "_synthetic_rn64",
        "_synthetic_binary64_operation",
        "_trace_synthetic_binary64_rows",
        "_reference_synthetic_c1_motion",
        "_audit_synthetic_controlled_candidate",
        "_SyntheticC1ControlledMotionOwner",
        "_SyntheticC1SourceRecorder",
        "prepare_synthetic_c1_relative_input",
    ):
        monkeypatch.setattr(diagnostics, name, forbidden)
    for module, names in (
        (diagnostics.np, ("sinc", "sin", "cos", "arctan2")),
        (diagnostics.math, ("sin", "cos", "atan2")),
    ):
        for name in names:
            monkeypatch.setattr(module, name, forbidden)
    for function in (helper, cell_helper):
        syntax = ast.parse(inspect.getsource(function))
        assert not any(
            isinstance(node, ast.Constant) and type(node.value) is float
            for node in ast.walk(syntax)
        )
        assert not any(
            isinstance(node, (ast.Import, ast.ImportFrom)) for node in ast.walk(syntax)
        )
        assert not any(
            isinstance(node, ast.Name) and node.id in {"np", "math", "float", "open"}
            for node in ast.walk(syntax)
        )
    word = _ARITHMETIC_TRACE_LITERALS[literal_index][2][4]
    result = candidate(word, synthetic_test_only=True)
    saved = deepcopy(result)
    assert result["q_word"] == word and result["sign"] == word >> 63
    assert Fraction(*result["q_ratio"]) == _literal_binary64_fraction(word)
    assert result["work"]["enclosure_entries"] == 1
    assert result["status"] == "candidate_mathematical_sinc_word", result["reason"]
    certificate = result["certificate"]
    if word & ((1 << 63) - 1) == 0:
        assert certificate["word"] == 0x3FF0000000000000
        assert certificate["branch"] == "zero" and result["work"]["cell_entries"] == 0
    else:
        assert result["work"]["cell_entries"] == 1
        output_word = certificate["word"]
        values = tuple(
            _literal_binary64_fraction(value)
            for value in (output_word - 1, output_word, output_word + 1)
        )
        lower, upper = (Fraction(*pair) for pair in result["interval"])
        bounds = ((values[0] + values[1]) / 2, (values[1] + values[2]) / 2)
        assert (lower > bounds[0] and upper < bounds[1]) or (
            output_word % 2 == 0 and lower >= bounds[0] and upper <= bounds[1]
        )
        assert certificate["interval"] == result["interval"]
    if literal_index in (0, 1):
        with pytest.raises(ValueError, match="synthetic_test_only"):
            candidate(word, synthetic_test_only=(False if literal_index == 0 else 1))
    elif literal_index in (2, 3, 4, 5):
        rejected = candidate(
            {2: True, 3: -1, 4: 1 << 64, 5: 0x7FF8000000000000}[literal_index],
            synthetic_test_only=True,
        )
        assert rejected["status"] == "unresolved_sinc_word_candidate"
        assert "certificate" not in rejected
    elif literal_index in (6, 7, 8, 9, 10):

        def corrupted(word, **keywords):
            output = enclose(word, **keywords)
            if literal_index == 6:
                output["q_word"] = True
            elif literal_index == 7:
                output["sign"] = float(output["sign"])
            elif literal_index == 8:
                output["configuration"]["sinc_terms"] = 8.0
            elif literal_index == 9:
                output["q_ratio"] = (float(output["q_ratio"][0]), output["q_ratio"][1])
            else:
                output.pop("interval")
            return output

        monkeypatch.setattr(diagnostics, "_enclose_synthetic_sinc_word", corrupted)
        rejected = candidate(word, synthetic_test_only=True)
        assert rejected["reason"] == "inconsistent_sinc_enclosure_binding"
        assert "certificate" not in rejected and rejected["work"]["cell_entries"] == 0
    else:

        def allocate(*arguments):
            raise MemoryError("injected word allocation failure")

        monkeypatch.setattr(diagnostics, "Fraction", allocate)
        with pytest.raises(MemoryError, match="injected word allocation failure"):
            candidate(word, synthetic_test_only=True)
    assert counts["word"] == 2 and result == saved
    assert counts["enclosure"] <= 2 and counts["cell"] <= 2
    for output in outputs:
        for flag in (
            "training_approved",
            "real_input_qualified",
            "free_space_qualified",
            "numerically_certified",
            "producer_parity_qualified",
        ):
            assert output[flag] is False
        assert output["native_sinc_status"] == "unresolved_native_sinc_evidence"
        assert output["motion_status"] == "unresolved_motion_evidence"
        assert output["consumer_status"] == "ineligible_isolated_candidate"


@pytest.mark.parametrize("literal_index", range(12))
def test_synthetic_sinc_word_enclosure(literal_index, monkeypatch):
    import ast
    import inspect
    from fractions import Fraction

    from sim import diagnostics

    helper = diagnostics._enclose_synthetic_sinc_word
    attempts = []
    outputs = []

    def enclose(*arguments, **keywords):
        attempts.append((arguments, keywords))
        assert len(attempts) <= 2
        output = helper(*arguments, **keywords)
        outputs.append(output)
        return output

    def forbidden(*arguments, **keywords):
        raise AssertionError("sinc reference reached a producer/native/owner path")

    for name in (
        "_synthetic_binary64_value",
        "_synthetic_rn64",
        "_synthetic_binary64_operation",
        "_trace_synthetic_binary64_rows",
        "_reference_synthetic_c1_motion",
        "_audit_synthetic_controlled_candidate",
        "_SyntheticC1ControlledMotionOwner",
        "_SyntheticC1SourceRecorder",
        "prepare_synthetic_c1_relative_input",
    ):
        monkeypatch.setattr(diagnostics, name, forbidden)
    for module, names in (
        (diagnostics.np, ("sinc", "sin", "cos", "arctan2")),
        (diagnostics.math, ("sin", "cos", "atan2")),
    ):
        for name in names:
            monkeypatch.setattr(module, name, forbidden)
    syntax = ast.parse(inspect.getsource(helper))
    assert not any(
        isinstance(node, ast.Constant) and type(node.value) is float
        for node in ast.walk(syntax)
    )
    assert not any(
        isinstance(node, (ast.Import, ast.ImportFrom)) for node in ast.walk(syntax)
    )
    assert not any(
        isinstance(node, ast.Name) and node.id in {"np", "math", "float", "open"}
        for node in ast.walk(syntax)
    )

    word = _ARITHMETIC_TRACE_LITERALS[literal_index][2][4]
    result = enclose(word, synthetic_test_only=True)
    assert result["status"] == "enclosed_mathematical_sinc", result["reason"]
    assert result["q_word"] == word and result["sign"] == word >> 63
    value = _literal_binary64_fraction(word)
    assert Fraction(*result["q_ratio"]) == value
    assert result["configuration"] == {
        "arctangent_terms": 32,
        "sinc_terms": 8,
        "rational_bit_limit": 65536,
    }
    assert 0 < result["work"]["max_result_bits"] <= 65536
    lower, upper = (Fraction(*endpoint) for endpoint in result["interval"])
    assert 0 < lower <= upper <= 1
    if not value:
        assert result["branch"] == "zero" and lower == upper == 1
        assert result["stages"] == {}
        assert result["work"]["rational_operations"] == 0
    else:
        stages = result["stages"]
        assert result["branch"] == "series"
        arctangents = []
        for denominator, interval in zip((5, 239), stages["arctangent"], strict=True):
            partial = sum(
                Fraction(
                    (-1) ** index, (2 * index + 1) * denominator ** (2 * index + 1)
                )
                for index in range(32)
            )
            tail = Fraction(1, 65 * denominator**65)
            assert tuple(Fraction(*endpoint) for endpoint in interval) == (
                partial,
                partial + tail,
            )
            arctangents.append((partial, partial + tail))
        pi_lower, pi_upper = (Fraction(*endpoint) for endpoint in stages["pi"])
        assert 3 < pi_lower <= pi_upper < 4
        assert pi_lower == 16 * arctangents[0][0] - 4 * arctangents[1][1]
        assert pi_upper == 16 * arctangents[0][1] - 4 * arctangents[1][0]
        squared_lower, squared_upper = (
            Fraction(*endpoint) for endpoint in stages["squared_argument"]
        )
        assert squared_lower == value**2 * pi_lower**2
        assert squared_upper == value**2 * pi_upper**2
        assert 0 < squared_lower <= squared_upper <= Fraction(1, 256)
        assert stages["coefficients"] == tuple(
            ((-1) ** degree, math.factorial(2 * degree + 1)) for degree in range(8)
        )
        polynomial_lower, polynomial_upper = (
            Fraction(*endpoint) for endpoint in stages["polynomial"]
        )
        for endpoint in (squared_lower, squared_upper):
            expanded = sum(
                Fraction((-1) ** degree, math.factorial(2 * degree + 1))
                * endpoint**degree
                for degree in range(8)
            )
            assert polynomial_lower <= expanded <= polynomial_upper
        assert stages["remainder"][0] == (0, 1)
        tail = squared_upper**8 / math.factorial(17)
        assert Fraction(*stages["remainder"][1]) == tail
        assert lower == polynomial_lower and upper == polynomial_upper + tail
        assert 1 - squared_upper / 6 <= lower
        assert upper - lower <= 3 * (pi_upper - pi_lower) / 512 + Fraction(
            1, (1 << 64) * math.factorial(17)
        )
        for interval in (
            result["interval"],
            stages["pi"],
            stages["squared_argument"],
            stages["polynomial"],
            stages["remainder"],
        ):
            for numerator, denominator in interval:
                assert type(numerator) is type(denominator) is int
                assert denominator > 0 and math.gcd(numerator, denominator) == 1
                assert max(numerator.bit_length(), denominator.bit_length()) <= 65536

    if literal_index in (1, 2):
        with pytest.raises(ValueError, match="synthetic_test_only"):
            enclose(word, synthetic_test_only=(False if literal_index == 1 else 1))
    elif literal_index == 6:
        mirror_word = _ARITHMETIC_TRACE_LITERALS[7][2][4]
        mirror = enclose(mirror_word, synthetic_test_only=True)
        assert mirror["interval"] == result["interval"]
        assert mirror["stages"] == result["stages"]
        assert mirror["stages"] is not result["stages"]
        assert mirror["sign"] != result["sign"]
    elif literal_index in (9, 10, 11):
        original_fraction = diagnostics.Fraction
        allocations = []

        def guarded_fraction(*arguments):
            allocations.append(arguments)
            if len(allocations) == 64:
                if literal_index == 11:
                    raise MemoryError("injected sinc allocation failure")
                monkeypatch.setattr(diagnostics, "_SYNTHETIC_SINC_BITS", 1)
            return original_fraction(*arguments)

        if literal_index == 9:
            monkeypatch.setattr(diagnostics, "_SYNTHETIC_SINC_BITS", 1)
        else:
            monkeypatch.setattr(diagnostics, "Fraction", guarded_fraction)
        if literal_index == 11:
            with pytest.raises(MemoryError, match="injected sinc allocation failure"):
                enclose(word, synthetic_test_only=True)
            assert len(allocations) == 64
        else:
            rejected = enclose(
                0x0000000000000001 if literal_index == 9 else word,
                synthetic_test_only=True,
            )
            assert rejected["reason"] == "sinc_rational_work_limit"
            assert rejected["status"] == "unresolved_mathematical_sinc"
            assert "interval" not in rejected and "stages" not in rejected
            if literal_index == 9:
                assert rejected["q_word"] == 0x0000000000000001
                assert rejected["work"]["rational_operations"] == 0
            else:
                assert len(allocations) == 64
                assert rejected["work"]["rational_operations"] > 0
    else:
        rejected_words = {
            0: (True, "unsupported_sinc_word"),
            3: (-1, "unsupported_sinc_word"),
            4: (1 << 64, "unsupported_sinc_word"),
            5: (0x7FF0000000000000, "nonfinite_sinc_word"),
            7: (0x7FF8000000000000, "nonfinite_sinc_word"),
            8: (_ARITHMETIC_TRACE_LITERALS[8][1], "outside_sinc_domain"),
        }
        rejected_word, reason = rejected_words[literal_index]
        rejected = enclose(rejected_word, synthetic_test_only=True)
        assert rejected["status"] == "unresolved_mathematical_sinc"
        assert rejected["reason"] == reason
        assert "interval" not in rejected and "stages" not in rejected
    assert len(attempts) == 2
    assert result["configuration"]["rational_bit_limit"] == 65536
    assert result["q_word"] == word
    assert tuple(Fraction(*endpoint) for endpoint in result["interval"]) == (
        lower,
        upper,
    )
    for output in outputs:
        for flag in (
            "training_approved",
            "real_input_qualified",
            "free_space_qualified",
            "numerically_certified",
            "producer_parity_qualified",
        ):
            assert output[flag] is False
        assert output["native_sinc_status"] == "unresolved_native_sinc_evidence"
        assert output["motion_status"] == "unresolved_motion_evidence"


def _literal_trace_arguments(heading, turn):
    return {
        "heading_word": heading,
        "turn_word": turn,
        "duration_word": 0x3FA999999999999A,
        "pi_word": 0x400921FB54442D18,
        "two_word": 0x4000000000000000,
        "synthetic_test_only": True,
    }


@pytest.mark.parametrize("heading,turn,expected", _ARITHMETIC_TRACE_LITERALS)
def test_synthetic_arithmetic_scalar_trace_compatibility(heading, turn, expected):
    import struct

    from sim.diagnostics import _trace_synthetic_binary64_rows

    arguments = _literal_trace_arguments(heading, turn)
    input_words = tuple(
        arguments[name]
        for name in (
            "heading_word",
            "turn_word",
            "duration_word",
            "pi_word",
            "two_word",
        )
    )
    scalar_inputs = tuple(
        struct.unpack("<d", struct.pack("<Q", word))[0] for word in input_words
    )
    assert all(type(value) is float for value in scalar_inputs)
    assert (
        tuple(
            struct.unpack("<Q", struct.pack("<d", value))[0] for value in scalar_inputs
        )
        == input_words
    )
    heading_value, turn_value, duration, stored_pi, two_value = scalar_inputs
    assert (duration, stored_pi, two_value) == (0.05, math.pi, 2.0)

    angle = turn_value * duration
    half = angle / 2
    midpoint = heading_value + half
    denominator_q = 2 * math.pi
    argument = angle / denominator_q
    first_sum = heading_value + angle
    shifted = first_sum + math.pi
    denominator_r = 2 * math.pi
    residue = math.fmod(shifted, denominator_r)
    corrected = shifted % denominator_r
    final = corrected - math.pi
    if residue == 0.0:
        correction = "divisor_signed_zero"
        staged_correction = math.copysign(0.0, denominator_r)
    elif residue < 0:
        correction = "negative_nonzero"
        staged_correction = residue + denominator_r
    else:
        correction = "none"
        staged_correction = residue
    assert struct.pack("<d", corrected) == struct.pack("<d", staged_correction)
    native_words = tuple(
        struct.unpack("<Q", struct.pack("<d", value))[0]
        for value in (
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
        )
    )
    assert native_words == expected
    trace = _trace_synthetic_binary64_rows(**arguments)
    assert trace["supported"]
    assert trace["intermediate_words"] == native_words
    assert trace["residue_correction"] == correction
    residue_cell = next(
        cell for row in trace["rows"] for cell in row["cells"] if cell["name"] == "z"
    )
    assert residue_cell["rounding_error_ratio"] == (0, 1)
    assert trace["producer_parity_qualified"] is False


def _assert_literal_nearest_word(exact, word):
    magnitude = word & ((1 << 63) - 1)
    distance = abs(_literal_binary64_fraction(word) - exact)
    sign = word & (1 << 63)
    for neighbor in (magnitude - 1, magnitude + 1):
        if 0 <= neighbor <= 0x7FEFFFFFFFFFFFFF:
            neighbor_distance = abs(_literal_binary64_fraction(sign | neighbor) - exact)
            assert distance <= neighbor_distance
            if distance == neighbor_distance:
                assert not word & 1
    if exact:
        assert bool(sign) == (exact < 0)


@pytest.mark.parametrize("heading,turn,expected", _ARITHMETIC_TRACE_LITERALS)
def test_synthetic_arithmetic_literal_trace(heading, turn, expected):
    from fractions import Fraction

    from sim.diagnostics import _trace_synthetic_binary64_rows

    trace = _trace_synthetic_binary64_rows(**_literal_trace_arguments(heading, turn))
    assert trace["supported"] and trace["reason"] == "literal_word_trace_only"
    assert trace["intermediate_words"] == expected
    assert [row["row"] for row in trace["rows"]] == ["P1", "P2", "P3", "P7"]
    cells = [cell for row in trace["rows"] for cell in row["cells"]]
    negative_residue = _literal_binary64_fraction(expected[8]) < 0
    names = ["a", "half", "m", "b_q", "q", "x_1", "x", "b_r", "z"]
    if negative_residue:
        names.append("u")
    names.append("r_next")
    assert [cell["name"] for cell in cells] == names
    assert trace["rounded_cells"] == len(cells) == 10 + negative_residue
    by_name = {cell["name"]: cell for cell in cells}
    assert by_name["half"]["operands"] == (expected[0], 0x4000000000000000)
    assert by_name["m"]["operands"] == (heading, expected[1])
    assert by_name["q"]["operands"] == (expected[0], expected[3])
    assert by_name["x_1"]["operands"] == (heading, expected[0])
    assert by_name["x"]["operands"] == (expected[5], 0x400921FB54442D18)
    assert by_name["b_q"] is not by_name["b_r"]
    assert by_name["r_next"]["operands"] == (expected[9], 0x400921FB54442D18)
    for cell in cells:
        left, right = map(_literal_binary64_fraction, cell["operands"])
        operation = cell["operation"]
        if operation == "add":
            exact = left + right
        elif operation == "sub":
            exact = left - right
        elif operation == "mul":
            exact = left * right
        elif operation == "div":
            exact = left / right
        else:
            quotient = left / right
            truncated = abs(quotient.numerator) // quotient.denominator
            truncated *= -1 if quotient < 0 else 1
            assert cell["truncated_quotient"] == truncated
            exact = left - truncated * right
            assert abs(exact) < right
        assert Fraction(*cell["exact_ratio"]) == exact
        _assert_literal_nearest_word(exact, cell["word"])
        assert (
            Fraction(*cell["rounding_error_ratio"])
            == _literal_binary64_fraction(cell["word"]) - exact
        )
    for flag in (
        "training_approved",
        "real_input_qualified",
        "free_space_qualified",
        "numerically_certified",
        "producer_parity_qualified",
    ):
        assert trace[flag] is False
    if turn == 0xBD04000000000000:
        assert trace["residue_correction"] == "negative_nonzero"
        assert expected[9] == expected[7] and expected[10] == 0x400921FB54442D18
    if turn == 0x3CF4000000000000:
        unrounded_half = (
            _literal_binary64_fraction(turn)
            * _literal_binary64_fraction(0x3FA999999999999A)
            / 2
        )
        assert unrounded_half > Fraction(1, 1 << 53)
        assert expected[2] == 0x3FF0000000000000


@pytest.mark.parametrize(
    "changes,raises",
    [
        ({"synthetic_test_only": False}, True),
        ({"synthetic_test_only": 1}, True),
        ({"word_format": "binary32"}, False),
        ({"word_format": True}, False),
        ({"heading_word": True}, False),
        ({"heading_word": -1}, False),
        ({"heading_word": 0x7FF0000000000000}, False),
        ({"heading_word": 0x400921FB54442D19}, False),
        ({"turn_word": True}, False),
        ({"turn_word": 0x7FF8000000000000}, False),
        ({"turn_word": 0x3FF8000000000001}, False),
        ({"turn_word": 0xBFF8000000000001}, False),
        ({"duration_word": 0x3FA9999999999999}, False),
        ({"pi_word": 0x400921FB54442D19}, False),
        ({"two_word": 0x4000000000000001}, False),
    ],
)
def test_synthetic_arithmetic_trace_rejects_evidence(changes, raises):
    from sim.diagnostics import _trace_synthetic_binary64_rows

    arguments = {**_literal_trace_arguments(0, 0), **changes}
    if raises:
        with pytest.raises(ValueError, match="synthetic_test_only"):
            _trace_synthetic_binary64_rows(**arguments)
    else:
        trace = _trace_synthetic_binary64_rows(**arguments)
        assert trace["supported"] is False and trace["rows"] == ()
        assert "intermediate_words" not in trace and "inputs" not in trace


def test_synthetic_arithmetic_trace_work_and_late_failure_are_atomic(monkeypatch):
    from sim import diagnostics

    arguments = _literal_trace_arguments(0, 0)
    with monkeypatch.context() as patch:
        patch.setattr(diagnostics, "_SYNTHETIC_ARITHMETIC_BITS", 1)
        trace = diagnostics._trace_synthetic_binary64_rows(**arguments)
        assert not trace["supported"] and trace["reason"] == "arithmetic work limit"
        assert trace["rows"] == () and "intermediate_words" not in trace
    original = diagnostics._synthetic_binary64_operation
    calls = []

    def fail_at_last_cell(*operands):
        calls.append(operands)
        if len(calls) == 9:
            raise ValueError("injected final-cell stop")
        return original(*operands)

    monkeypatch.setattr(diagnostics, "_synthetic_binary64_operation", fail_at_last_cell)
    trace = diagnostics._trace_synthetic_binary64_rows(**arguments)
    assert len(calls) == 9 and trace["reason"] == "injected final-cell stop"
    assert trace["rows"] == () and "intermediate_words" not in trace


def test_synthetic_arithmetic_kernel_has_no_fp_or_owner_path():
    import ast
    import inspect

    from sim import diagnostics

    for name in (
        "_synthetic_binary64_value",
        "_synthetic_rn64",
        "_synthetic_binary64_operation",
        "_trace_synthetic_binary64_rows",
    ):
        tree = ast.parse(inspect.getsource(getattr(diagnostics, name)))
        identifiers = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        assert not identifiers & {
            "float",
            "np",
            "math",
            "integrate",
            "_SyntheticC1MotionOwner",
            "_SyntheticC1SourceRecorder",
            "collect_diagnostic_episode",
        }
        assert not any(
            isinstance(node, ast.Constant) and isinstance(node.value, float)
            for node in ast.walk(tree)
        )


def test_tof_floor_and_missing_returns_follow_synthetic_mount():
    config = Config(noise_std=0, dropout=0, latency_ticks=0)
    observation, _ = RoverEnv(config).reset()
    floor_distance = 0.15 / math.sin(config.field_of_view / 2)
    np.testing.assert_allclose(observation["tof_m"][-1], floor_distance, rtol=1e-6)
    assert observation["tof_valid"][-1].all()
    assert not observation["tof_valid"][0].any()
    assert not observation["tof_m"][0].any()


def test_tof_synthetic_rays_are_unit_length_and_pitch_is_positive_down():
    from dataclasses import replace

    config = Config()
    rays = tof_directions(0, config)
    np.testing.assert_allclose(np.linalg.norm(rays, axis=-1), 1, atol=1e-15)
    assert (rays[:, 0, 1] > 0).all() and (rays[:, -1, 1] < 0).all()
    assert (rays[0, :, 2] > 0).all() and (rays[-1, :, 2] < 0).all()
    down = tof_directions(0, replace(config, tof_mount_pitch=math.pi / 4))
    assert (down[..., 2] < 0).all()
    np.testing.assert_allclose(
        tof_directions(math.pi / 2, config)[..., 0], -rays[..., 1], atol=1e-15
    )


@pytest.mark.parametrize(
    "case",
    [
        "stationary",
        "rotated",
        "left",
        "right",
        "tiny",
        "clocks",
        "wrap",
        "held",
        "wrong_position",
        "wrong_yaw",
        "goal",
        "wire",
        "missing_primitive",
        "overlap",
        "limits",
        "foreign",
    ],
)
def test_synthetic_c1_rational_reference(monkeypatch, case):
    from fractions import Fraction

    from sim import diagnostics, rover

    def forbidden(*args, **kwargs):
        pytest.fail("rational references must not consume production computations")

    for name in (
        "probe_synthetic_c1_questions",
        "probe_synthetic_c1_relative_questions",
        "probe_synthetic_c1_enclosure",
        "probe_synthetic_c1_occupied_witness",
        "RoverEnv",
        "write_episode",
    ):
        monkeypatch.setattr(diagnostics, name, forbidden)
    scene = (
        Scenario(start=(2, 2, 0), goal=(5, 2), obstacles=((2.6, 2, 0.30),))
        if case == "wrong_position"
        else Scenario(start=(2, 2, 0), goal=(5, 2), obstacles=((2.4, 2, 0.005),))
        if case == "goal"
        else Scenario(start=(1, 1, 0), goal=(5, 2), obstacles=((2.4, 2, 0.30),))
        if case == "wire"
        else Scenario(start=(2, 2, 0), goal=(5, 2))
    )
    speed = 0 if case == "stationary" else 0.6 if case == "wire" else 0.5
    turn = (
        -0.5
        if case == "right"
        else 2**-40
        if case == "tiny"
        else 0
        if case in ("stationary", "rotated", "clocks", "wire")
        else 0.5
    )
    heading = (
        math.pi - 0.01 if case == "wrap" else 0.25 if case in ("rotated", "goal") else 0
    )
    owner = diagnostics._SyntheticC1MotionOwner(
        scene,
        seed_tick=20,
        pose_m_rad=[2, 2, heading],
        speed=speed,
        turn_rate=turn,
        synthetic_test_only=True,
    )
    original_integrate = rover.integrate

    def faulty_integrate(*arguments):
        position, yaw = original_integrate(*arguments)
        return (
            (position + [0, 0.02], yaw)
            if case == "wrong_position"
            else (position, yaw - 0.1)
        )

    if case in ("wrong_position", "wrong_yaw"):
        monkeypatch.setattr(rover, "integrate", faulty_integrate)
    for tick in range(21, 28):
        owner.advance(tick)
        if tick == 26 and case == "held":
            previous = owner.snapshot()
    bundle = owner.snapshot()
    before = owner.audit(bundle)
    motion = bundle["motion"]
    motion_before = deepcopy(motion)

    def reference_for(record):
        with monkeypatch.context() as blocked:
            for name in (
                "capture_synthetic_c1_views",
                "prepare_synthetic_c1_relative_input",
                "inspect_synthetic_c1_history",
                "_check_synthetic_c1_motion",
            ):
                blocked.setattr(diagnostics, name, forbidden)
            blocked.setattr(rover, "integrate", forbidden)
            for name in ("sin", "cos", "atan2"):
                blocked.setattr(math, name, forbidden)
            blocked.setattr(np, "sinc", forbidden)
            return diagnostics._reference_synthetic_c1_motion(
                record, synthetic_test_only=True
            )

    def trig_interval(angle, sine):
        total = sum(
            Fraction((-1) ** (degree // 2), math.factorial(degree)) * angle**degree
            for degree in range(1 if sine else 0, 48, 2)
        )
        tail = abs(angle) ** 48 / math.factorial(48)
        return total - tail, total + tail

    def scale(interval, factor):
        endpoints = [endpoint * factor for endpoint in interval]
        return min(endpoints), max(endpoints)

    def subtract(left, right):
        return left[0] - right[1], left[1] - right[0]

    reference = reference_for(motion)
    assert reference["status"] == "enclosed_mathematical_reference"
    assert reference["motion_status"] == "unresolved_motion_evidence"
    assert all(
        reference[name] is False
        for name in (
            "training_approved",
            "real_input_qualified",
            "free_space_qualified",
            "numerically_certified",
        )
    )
    seed_heading, exact_speed, exact_turn = map(Fraction, (heading, speed, turn))
    for clock in ("nominal_us", "binary64_step"):
        assert len(reference["clocks"][clock]) == 8
        period = Fraction(1, 20) if clock == "nominal_us" else Fraction(0.05)
        for offset, event in enumerate(reference["clocks"][clock]):
            elapsed = offset * period
            phase = seed_heading + exact_turn * elapsed
            assert event["elapsed_s"] == elapsed
            assert event["unwrapped_heading_rad"] == (phase, phase)
            for axis in (0, 1):
                if exact_turn:
                    start = trig_interval(seed_heading, axis == 0)
                    end = trig_interval(phase, axis == 0)
                    oracle = scale(
                        subtract(end, start) if axis == 0 else subtract(start, end),
                        exact_speed / exact_turn,
                    )
                else:
                    oracle = scale(
                        trig_interval(seed_heading, axis == 1), exact_speed * elapsed
                    )
                lower, upper = event["position_m"][axis]
                if offset and speed:
                    assert lower <= 2 + oracle[0] <= 2 + oracle[1] <= upper
                else:
                    assert lower == upper == 2
            assert event["clock_discrepancy_m"] == exact_speed * offset * abs(
                Fraction(0.05) - Fraction(1, 20)
            )
            assert event["clock_discrepancy_rad"] == abs(exact_turn) * offset * abs(
                Fraction(0.05) - Fraction(1, 20)
            )
            pose = tuple(map(Fraction, motion["events"][offset]["pose_m_rad"]))
            delta = (Fraction(5) - pose[0], Fraction(2) - pose[1])
            cosine, sine = trig_interval(pose[2], False), trig_interval(pose[2], True)
            for axis, terms in enumerate(
                (
                    (scale(cosine, delta[0]), scale(sine, delta[1])),
                    (scale(cosine, delta[1]), scale(sine, -delta[0])),
                )
            ):
                oracle = (terms[0][0] + terms[1][0], terms[0][1] + terms[1][1])
                lower, upper = event["body_goal_m"][axis]
                assert lower <= oracle[0] <= oracle[1] <= upper
    assert owner.audit(bundle) == before
    assert motion == motion_before
    if case == "stationary":
        assert all(
            event["position_m"] == ((Fraction(2), Fraction(2)),) * 2
            for event in reference["clocks"]["nominal_us"]
        )
    if case in ("left", "right"):
        mirrored = deepcopy(motion)
        mirrored["turn_rate_rad_s"] = -turn
        other = reference_for(mirrored)
        for event, reflected in zip(
            reference["clocks"]["nominal_us"],
            other["clocks"]["nominal_us"],
            strict=True,
        ):
            assert event["position_m"][0] == reflected["position_m"][0]
            assert event["position_m"][1] == (
                4 - reflected["position_m"][1][1],
                4 - reflected["position_m"][1][0],
            )
    if case == "tiny":
        last = reference["clocks"]["nominal_us"][-1]
        assert last["position_m"][0][0] < Fraction(2) + exact_speed * Fraction(7, 20)
        assert last["position_m"][1][0] > 2
    if case == "clocks":
        nominal = reference["clocks"]["nominal_us"][-1]
        binary = reference["clocks"]["binary64_step"][-1]
        assert nominal["elapsed_s"] != binary["elapsed_s"]
        assert (
            binary["position_m"][0][0] - nominal["position_m"][0][0]
            == binary["clock_discrepancy_m"]
            > 0
        )
    if case == "wrap":
        assert (
            motion["events"][0]["pose_m_rad"][2]
            > 0
            > motion["events"][1]["pose_m_rad"][2]
        )
        assert reference["clocks"]["nominal_us"][-1]["circular_heading_rad"][0][0] == 1
        mirrored = deepcopy(motion)
        mirrored["seed_pose_m_rad"][2] *= -1
        mirrored["turn_rate_rad_s"] *= -1
        assert (
            reference_for(mirrored)["clocks"]["nominal_us"][-1]["circular_heading_rad"][
                0
            ][0]
            == -1
        )
        lower, upper = reference["pi_rad"]
        assert lower < Fraction(22, 7) and upper > Fraction(3)
    if case == "held":
        old_capture = previous["source"]["private_source"]["history"][-1]
        new_capture = bundle["source"]["private_source"]["history"][-1]
        assert old_capture["capture_id"] == new_capture["capture_id"]
        old = reference_for(previous["motion"])["clocks"]["nominal_us"][-1]
        new = reference["clocks"]["nominal_us"][-1]
        assert old["position_m"] != new["position_m"]
        assert old["body_goal_m"] != new["body_goal_m"]
    if case in ("wrong_position", "wrong_yaw"):
        event = reference["clocks"]["nominal_us"][-1]
        pose = motion["events"][-1]["pose_m_rad"]
        interval = (
            event["position_m"][1]
            if case == "wrong_position"
            else event["unwrapped_heading_rad"]
        )
        assert (
            not interval[0]
            <= Fraction(pose[1 if case == "wrong_position" else 2])
            <= interval[1]
        )
        assert before["ownership_status"] == "consistent_under_fixture_assumptions"
        assert before["motion_status"] == "unresolved_motion_evidence"
    if case == "wire":
        assert before["source_audit"]["reason"] == "host_round_trip_changed"
        assert "velocity_m_s" in before["source_audit"]["host_changed_fields"]
    if case == "missing_primitive":
        assert (
            before["motion_status"]
            == reference["motion_status"]
            == "unresolved_motion_evidence"
        )
    if case == "overlap":
        lower, upper = reference["clocks"]["nominal_us"][-1]["position_m"][0]
        assert lower < upper
        partial = ((lower + upper) / 2, (lower + upper) / 2)
        containing = (lower - 1, upper + 1)
        disjoint = (upper + 1, upper + 2)
        assert max(lower, partial[0]) <= min(upper, partial[1])
        assert not partial[0] <= lower <= upper <= partial[1]
        assert containing[0] <= lower <= upper <= containing[1]
        assert max(lower, disjoint[0]) > min(upper, disjoint[1])
        assert reference["motion_status"] == "unresolved_motion_evidence"
    if case == "limits":
        for opt_in in (False, None, 1):
            with pytest.raises(ValueError, match="synthetic_test_only"):
                diagnostics._reference_synthetic_c1_motion(
                    motion, synthetic_test_only=opt_in
                )
        for field, value in (
            ("seed_tick", True),
            ("speed_m_s", float("nan")),
            ("turn_rate_rad_s", 2),
            ("seed_pose_m_rad", [2, 2, 5]),
            ("events", motion["events"] + [motion["events"][-1]]),
            ("fixture_goal_m", [False, 2]),
            ("tick_period_s", 0.1),
        ):
            invalid = deepcopy(motion)
            invalid[field] = value
            rejected = reference_for(invalid)
            assert rejected["status"] == "unresolved_mathematical_reference"
            assert rejected["clocks"] == {}
        oversized = deepcopy(motion)
        oversized["seed_pose_m_rad"][0] = 1 << 65536
        assert reference_for(oversized)["reason"] == "rational_work_limit"
    if case == "foreign":
        other = diagnostics._SyntheticC1MotionOwner(
            scene,
            seed_tick=20,
            pose_m_rad=[2, 2, heading],
            speed=speed,
            turn_rate=turn,
            synthetic_test_only=True,
        )
        for tick in range(21, 28):
            other.advance(tick)
        foreign = other.snapshot()
        assert (
            reference_for(foreign["motion"])["status"]
            == "enclosed_mathematical_reference"
        )
        assert owner.audit(foreign)["ownership_status"] == "inconsistent_source_record"


@pytest.mark.parametrize(
    "case",
    [
        "stationary",
        "straight",
        "left",
        "right",
        "held",
        "wrap",
        "stalled",
        "wrong_pose",
        "wrong_twist",
        "gap",
        "epoch",
        "rewritten_hold",
        "goal",
        "wire",
        "missing_numeric",
        "foreign",
    ],
)
def test_synthetic_c1_motion_owner(monkeypatch, case):
    from dataclasses import asdict

    from interface.protocol import State, encode_state
    from sim import diagnostics, rover

    def forbidden(*args, **kwargs):
        pytest.fail("motion fixtures must not query questions or collect episodes")

    for name in (
        "probe_synthetic_c1_questions",
        "probe_synthetic_c1_relative_questions",
        "probe_synthetic_c1_enclosure",
        "probe_synthetic_c1_occupied_witness",
        "RoverEnv",
        "write_episode",
    ):
        monkeypatch.setattr(diagnostics, name, forbidden)
    scene = (
        Scenario(start=(2, 2, 0), goal=(5, 2), obstacles=((2.6, 2, 0.30),))
        if case == "wrong_pose"
        else Scenario(start=(2, 2, 0), goal=(5, 2), obstacles=((2.4, 2, 0.005),))
        if case == "goal"
        else Scenario(start=(1, 1, 0), goal=(5, 2), obstacles=((2.4, 2, 0.30),))
        if case == "wire"
        else Scenario(start=(2, 2, 0), goal=(5, 2))
    )
    speed = 0 if case == "stationary" else 0.6 if case == "wire" else 0.5
    turn = 0.5 if case in ("left", "wrap") else -0.5 if case == "right" else 0
    seed = np.array(
        [
            2,
            2,
            math.pi - 0.01
            if case == "wrap"
            else 0.25
            if case == "missing_numeric"
            else 0,
        ]
    )
    owner = diagnostics._SyntheticC1MotionOwner(
        scene,
        seed_tick=20,
        pose_m_rad=seed,
        speed=speed,
        turn_rate=turn,
        synthetic_test_only=True,
    )
    seed[:] = 99
    original_integrate = rover.integrate
    original_record = owner._record

    def faulty_integrate(position, heading, *settings):
        if case == "stalled":
            return np.asarray(position), heading
        moved, angle = original_integrate(position, heading, *settings)
        return moved + [0, 0.01], angle + 0.01

    def faulty_record(tick, pose):
        original_record(tick, pose)
        event = owner._events[-1]
        if case == "wrong_twist":
            event["fixture_state"]["angular_velocity_rad_s"] = (0, 0, 0.25)
        else:
            event["fixture_state"]["goal_m"] = (99, 0, 0)
        event["host_frame"] = encode_state(State(**event["fixture_state"]))

    if case in ("stalled", "wrong_pose"):
        monkeypatch.setattr(rover, "integrate", faulty_integrate)
    elif case in ("wrong_twist", "goal"):
        monkeypatch.setattr(owner, "_record", faulty_record)
    for tick in range(21, 28):
        owner.advance(tick)
        if tick == 26 and case in ("held", "gap"):
            previous = owner.snapshot()
            if case == "gap":
                for invalid in (True, 26, 28, 85900):
                    with pytest.raises(ValueError, match="bounded consecutive"):
                        owner.advance(invalid)
                assert owner.snapshot()["binding_sha256"] == previous["binding_sha256"]
    if case in ("epoch", "rewritten_hold"):
        owner._recorder._history = deepcopy(owner._recorder._history)
        if case == "epoch":
            owner._recorder._history[-1]["clock_epoch"] = "substituted-epoch"
        else:
            owner._recorder._history[-1]["capture"]["capture_ticks"] += 1
    bundle = owner.snapshot()
    assert len(bundle["motion"]["events"]) == 8
    assert bundle["motion"]["tick_period_us"] == 50000
    assert bundle["motion"]["tick_period_s"] == 0.05
    assert bundle["motion"]["seed_pose_m_rad"][:2] == [2, 2]
    assert all(
        event["tick"] == 20 + index
        for index, event in enumerate(bundle["motion"]["events"])
    )
    if case == "held":
        old = previous["source"]["private_source"]["history"][-1]
        current = bundle["source"]["private_source"]["history"][-1]
        assert old["capture_id"] == current["capture_id"]
        for field in ("capture_ticks", "capture_poses_m_rad", "tof_m", "tof_valid"):
            assert np.array_equal(old["capture"][field], current["capture"][field])
        assert (
            previous["source"]["private_source"]["reference_pose_m_rad"]
            != bundle["source"]["private_source"]["reference_pose_m_rad"]
        )
        assert (
            previous["source"]["fixture_state"].goal_m
            != bundle["source"]["fixture_state"].goal_m
        )
        assert owner.audit(previous)["ownership_status"] == "inconsistent_source_record"
    if case == "wrap":
        assert bundle["motion"]["events"][0]["pose_m_rad"][2] > 0
        assert bundle["motion"]["events"][1]["pose_m_rad"][2] < 0
    if case == "gap":
        with pytest.raises(ValueError, match="bounded consecutive"):
            owner.advance(28)
        assert owner.snapshot()["binding_sha256"] == bundle["binding_sha256"]
    if case == "foreign":
        other = diagnostics._SyntheticC1MotionOwner(
            scene,
            seed_tick=20,
            pose_m_rad=[2, 2, 0],
            speed=speed,
            turn_rate=turn,
            synthetic_test_only=True,
        )
        for tick in range(21, 28):
            other.advance(tick)
        assert (
            owner.audit(other.snapshot())["ownership_status"]
            == "inconsistent_source_record"
        )
        bundle["motion"]["speed_m_s"] = 0.125
        bundle["binding_sha256"] = diagnostics._c1_source_binding_digest(
            {
                "motion": bundle["motion"],
                "source": {
                    **bundle["source"],
                    "fixture_state": asdict(bundle["source"]["fixture_state"]),
                },
            }
        )
    for name in (
        "capture_synthetic_c1_views",
        "prepare_synthetic_c1_relative_input",
        "inspect_synthetic_c1_history",
    ):
        monkeypatch.setattr(diagnostics, name, forbidden)
    monkeypatch.setattr(rover, "integrate", forbidden)
    result = owner.audit(bundle)
    assert set(result) == {
        "allowed_use",
        "training_approved",
        "real_input_qualified",
        "free_space_qualified",
        "numerically_certified",
        "ownership_status",
        "motion_status",
        "motion_reason",
        "events_checked",
        "source_audit",
    }
    assert all(
        result[field] is False
        for field in (
            "training_approved",
            "real_input_qualified",
            "free_space_qualified",
            "numerically_certified",
        )
    )
    assert "scenario" not in bundle["source"]["relative_input"]
    if case == "foreign":
        assert result["ownership_status"] == "inconsistent_source_record"
        assert result["source_audit"] is None
        del bundle["source"]["fixture_state"]
        assert owner.audit(bundle)["ownership_status"] == "inconsistent_source_record"
        return
    assert result["ownership_status"] == "consistent_under_fixture_assumptions"
    if case in (
        "stalled",
        "wrong_pose",
        "wrong_twist",
        "epoch",
        "rewritten_hold",
        "goal",
    ):
        assert result["motion_status"] == "inconsistent_motion_record"
        assert (
            result["motion_reason"]
            == {
                "stalled": "straight_reference_mismatch",
                "wrong_pose": "straight_reference_mismatch",
                "wrong_twist": "host_twist_or_clock_mismatch",
                "epoch": "motion_acquisition_event_mismatch",
                "rewritten_hold": "motion_acquisition_event_mismatch",
                "goal": "motion_body_goal_mismatch",
            }[case]
        )
    else:
        assert result["events_checked"] == 8
        assert result["motion_status"] == (
            "unresolved_motion_evidence"
            if case in ("left", "right", "wrap", "missing_numeric")
            else "consistent_under_fixture_assumptions"
        )
    if case in ("stationary", "stalled"):
        assert (
            result["source_audit"]["status"] == "consistent_under_fixture_assumptions"
        )
    if case == "wire":
        assert result["source_audit"]["reason"] == "host_round_trip_changed"
        assert "velocity_m_s" in result["source_audit"]["host_changed_fields"]
    if case == "straight":
        assert result["source_audit"]["reason"] == "host_round_trip_changed"
        assert "goal_m" in result["source_audit"]["host_changed_fields"]


@pytest.mark.parametrize(
    "case",
    [
        "clear",
        "blocked",
        "left_turn",
        "right_turn",
        "low_speed",
        "held_reference",
        "zero_cells",
        "missing_body",
        "missing_domain",
        "conflict",
        "binary32_change",
        "outside_domain",
        "body_contact",
        "candidate_copy",
        "stale_reference",
        "foreign_recorder",
    ],
)
def test_synthetic_c1_recorder_question_composition(monkeypatch, case):
    from dataclasses import asdict

    from interface.protocol import State, encode_state
    from sim import diagnostics
    from sim.navigation import evaluate_synthetic

    def forbidden(*args, **kwargs):
        pytest.fail("fixture composition must not collect episodes or recapture")

    for name in ("write_episode", "RoverEnv"):
        monkeypatch.setattr(diagnostics, name, forbidden)
    scene = (
        Scenario(start=(2, 2, 0), goal=(5, 2), obstacles=((2.4, 2, 0.005),))
        if case == "outside_domain"
        else Scenario(start=(1, 1, 0), goal=(5, 2), obstacles=((2.4, 2, 0.30),))
        if case == "body_contact"
        else Scenario(
            start=(2, 2, 0),
            goal=(5, 2),
            obstacles=((2.6, 2, 0.30),) if case == "blocked" else (),
        )
    )
    recorder = diagnostics._SyntheticC1SourceRecorder(scene, synthetic_test_only=True)
    speed = 0.6 if case == "binary32_change" else 0.125 if case == "low_speed" else 0.5
    turn = 0.5 if case == "left_turn" else -0.5 if case == "right_turn" else 0

    def record(owner, tick):
        owner.record_tick(
            tick,
            pose_m_rad=[2, 2, 0],
            fixture_state=State(
                timestamp_us=tick * 50000,
                velocity_m_s=(speed, 0, 0),
                angular_velocity_rad_s=(0, 0, turn),
                goal_m=(3, 0, 0),
            ),
        )

    for tick in range(20, 24):
        record(recorder, tick)
    bundle = recorder.snapshot()
    if case == "held_reference":
        events = bundle["private_source"]["history"]
        assert [event["snapshot_tick"] for event in events] == [22, 23]
        assert events[0]["capture_id"] == events[1]["capture_id"]
        record(recorder, 24)
        bundle = recorder.snapshot()
        assert bundle["relative_input"]["reference_tick"] == 24
        assert (
            bundle["relative_input"]["history"][-1]["capture_ticks"].tolist()
            == [22] * 8
        )
    elif case == "candidate_copy":
        bundle["relative_input"]["fixture_goal_body_m"][0] += 1
        bundle["binding_sha256"] = diagnostics._c1_source_binding_digest(
            {
                "relative_input": bundle["relative_input"],
                "fixture_state": asdict(bundle["fixture_state"]),
                "host_frame": encode_state(bundle["fixture_state"]),
                "private_source": bundle["private_source"],
            }
        )
    elif case == "stale_reference":
        record(recorder, 24)
        with pytest.raises(ValueError, match="current reference"):
            recorder.audit(bundle)
        recorder.snapshot()
    elif case == "foreign_recorder":
        other = diagnostics._SyntheticC1SourceRecorder(scene, synthetic_test_only=True)
        for tick in range(20, 24):
            record(other, tick)
        bundle = other.snapshot()

    for name in ("capture_synthetic_c1_views", "prepare_synthetic_c1_relative_input"):
        monkeypatch.setattr(diagnostics, name, forbidden)
    question_calls, coordinator_calls = [], []
    motion_calls = {"exclusion": [], "witness": []}
    original_question = diagnostics.probe_synthetic_c1_relative_questions
    original_coordinator = diagnostics.probe_synthetic_c1_questions
    original_exclusion = diagnostics.probe_synthetic_c1_enclosure
    original_witness = diagnostics.probe_synthetic_c1_occupied_witness
    oracle_assisted_fixture_admission = False

    def question(relative_input, **settings):
        assert oracle_assisted_fixture_admission is True
        assert relative_input is bundle["relative_input"]
        assert settings["fixture_state"] is bundle["fixture_state"]
        assert set(relative_input).isdisjoint(
            {"scenario", "private_source", "source_files", "host_frame"}
        )
        assert set(settings) == {
            "fixture_state",
            "fixture_current_body_clear",
            "fixture_controlled_envelope",
            "synthetic_test_only",
            "max_cells",
        }
        for capture in relative_input["history"]:
            assert set(capture) == {
                "capture_ticks",
                "capture_poses_body_m_rad",
                "tof_m",
                "tof_valid",
            }
        question_calls.append(relative_input["reference_tick"])
        return original_question(relative_input, **settings)

    def coordinator(history, **settings):
        assert oracle_assisted_fixture_admission is True
        coordinator_calls.append(settings["reference_tick"])
        return original_coordinator(history, **settings)

    def exclusion(history, **settings):
        motion_calls["exclusion"].append(
            (settings["speed"], settings["braking_turn_rate"])
        )
        assert len(motion_calls["exclusion"]) <= 6
        return original_exclusion(history, **settings)

    def witness(history, **settings):
        motion_calls["witness"].append(
            (settings["speed"], settings["braking_turn_rate"])
        )
        assert len(motion_calls["witness"]) <= 6
        result = original_witness(history, **settings)
        if case == "conflict":
            result["fixture_blocked_witness"] = True
        return result

    monkeypatch.setattr(diagnostics, "probe_synthetic_c1_relative_questions", question)
    monkeypatch.setattr(diagnostics, "probe_synthetic_c1_questions", coordinator)
    monkeypatch.setattr(diagnostics, "probe_synthetic_c1_enclosure", exclusion)
    monkeypatch.setattr(diagnostics, "probe_synthetic_c1_occupied_witness", witness)
    audit = recorder.audit(bundle)
    for output in (bundle, audit):
        assert all(
            output[key] is False
            for key in (
                "training_approved",
                "real_input_qualified",
                "free_space_qualified",
                "numerically_certified",
            )
        )
    assert question_calls == coordinator_calls == []
    assert motion_calls == {"exclusion": [], "witness": []}
    if case in ("binary32_change", "outside_domain", "body_contact"):
        assert audit["status"] == "unresolved_source_evidence"
        assert (
            audit["reason"]
            == {
                "binary32_change": "host_round_trip_changed",
                "outside_domain": "private_domain_not_established",
                "body_contact": "private_body_clearance_not_established",
            }[case]
        )
        if case == "binary32_change":
            assert audit["host_changed_fields"] == ("velocity_m_s",)
        return
    if case in ("candidate_copy", "stale_reference", "foreign_recorder"):
        assert audit["status"] == "inconsistent_source_record"
        return
    assert audit["status"] == "consistent_under_fixture_assumptions"
    oracle_assisted_fixture_admission = True
    result = diagnostics.probe_synthetic_c1_relative_questions(
        bundle["relative_input"],
        fixture_state=bundle["fixture_state"],
        fixture_current_body_clear=1 if case == "missing_body" else True,
        fixture_controlled_envelope=case != "missing_domain",
        max_cells=0 if case == "zero_cells" else 32768,
        synthetic_test_only=True,
    )
    assert len(question_calls) == 1
    assert motion_calls["exclusion"] == motion_calls["witness"]
    assert len(set(motion_calls["exclusion"])) == len(motion_calls["exclusion"])
    assert result["unique_motion_queries"] == len(motion_calls["exclusion"]) <= 6
    assert all(
        result[key] is False
        for key in (
            "training_approved",
            "real_input_qualified",
            "free_space_qualified",
            "numerically_certified",
        )
    )
    assert "mode" not in result["candidate_values"]
    if case in ("missing_body", "missing_domain"):
        assert result["status"] == "unknown"
        assert result["reason"] == "fixture_body_or_domain_not_established"
        assert coordinator_calls == []
    else:
        assert len(coordinator_calls) == 1
        assert result["unique_motion_queries"] == (6 if case == "low_speed" else 4)
        assert set(result["queries"]) == {
            "centre",
            "left",
            "right",
            "tier_1",
            "tier_2",
            "tier_3",
        }
        if case in ("zero_cells", "conflict"):
            assert result["status"] == (
                "unknown" if case == "zero_cells" else "inconsistent_fixture_evidence"
            )
        else:
            reference = evaluate_synthetic(
                scene,
                speed=speed,
                turn_rate=turn,
                tof_age_s=(0.10 if case == "held_reference" else 0.15),
                synthetic_test_only=True,
            )["answers"]
            assert result["status"] == "resolved_under_fixture_assumptions"
            assert result["candidate_values"] == {
                name: reference[name]
                for name in ("path_blocked", "clear_sector", "speed_tier")
            }
    if case in ("missing_body", "missing_domain", "zero_cells", "conflict"):
        assert all(value is None for value in result["candidate_values"].values())


@pytest.mark.parametrize(
    "case,scene_index,literal_index,speed",
    [
        ("straight", 0, 0, 0.5),
        ("left", 0, 6, 0.5),
        ("right", 1, 7, 0.5),
        ("wrap", 2, 8, 0.5),
        ("wire", 3, 0, 0.6),
        ("signed_zero", 0, 1, 0.0),
        ("late_failure", 1, 6, 0.5),
        ("ingress", 0, 0, 0.5),
    ],
)
def test_synthetic_c1_controlled_owner_staged_fixture(
    monkeypatch, case, scene_index, literal_index, speed
):
    import struct
    from fractions import Fraction

    from interface.protocol import decode_state
    from sim import diagnostics, rover

    counts = {
        "constructors": 0,
        "advances": 0,
        "records": 0,
        "captures": 0,
        "traces": 0,
        "audits": 0,
    }

    def counted(original, counter):
        def call(*args, **kwargs):
            counts[counter] += 1
            return original(*args, **kwargs)

        return call

    def forbidden(*args, **kwargs):
        pytest.fail("controlled fixtures must not query, reference or collect")

    for name in (
        "probe_synthetic_c1_questions",
        "probe_synthetic_c1_relative_questions",
        "probe_synthetic_c1_enclosure",
        "probe_synthetic_c1_occupied_witness",
        "_reference_synthetic_c1_motion",
        "_check_synthetic_c1_motion",
        "RoverEnv",
        "write_episode",
    ):
        monkeypatch.setattr(diagnostics, name, forbidden)
    candidate_class = diagnostics._SyntheticC1ControlledMotionOwner
    for owner_class in (candidate_class, diagnostics._SyntheticC1MotionOwner):
        for method, counter in (("__init__", "constructors"), ("advance", "advances")):
            monkeypatch.setattr(
                owner_class, method, counted(getattr(owner_class, method), counter)
            )
    monkeypatch.setattr(
        candidate_class, "audit", counted(candidate_class.audit, "audits")
    )
    recorder_class = diagnostics._SyntheticC1SourceRecorder
    monkeypatch.setattr(
        recorder_class, "record_tick", counted(recorder_class.record_tick, "records")
    )
    for name, counter in (
        ("capture_synthetic_c1_views", "captures"),
        ("_trace_synthetic_binary64_rows", "traces"),
    ):
        monkeypatch.setattr(
            diagnostics, name, counted(getattr(diagnostics, name), counter)
        )
    scenes = (
        Scenario(start=(2, 2, 0), goal=(5, 2)),
        Scenario(start=(2, 2, 0), goal=(5, 2), obstacles=((2.6, 2, 0.30),)),
        Scenario(start=(2, 2, 0), goal=(5, 2), obstacles=((2.4, 2, 0.005),)),
        Scenario(start=(1, 1, 0), goal=(5, 2), obstacles=((2.4, 2, 0.30),)),
    )
    scene = scenes[scene_index]
    heading_word, turn_word, expected_words = _ARITHMETIC_TRACE_LITERALS[literal_index]

    def scalar(word):
        return struct.unpack("<d", struct.pack("<Q", word))[0]

    settings = {
        "seed_tick": 20,
        "position_m": (2.0, 2.0),
        "heading_word": heading_word,
        "speed": speed,
        "turn_word": turn_word,
        "synthetic_test_only": True,
    }
    if case == "ingress":
        for change in ({"heading_word": True}, {"synthetic_test_only": 1}):
            with pytest.raises(ValueError):
                candidate_class(scene, **{**settings, **change})
        for bad in (True, -1, 1 << 64, 0x7FF0000000000000):
            with pytest.raises(ValueError):
                candidate_class._scalar(bad)
        for bad in (True, 1, np.float64(1), float("inf")):
            with pytest.raises(ValueError):
                candidate_class._word(bad)
        assert counts == {
            "constructors": 2,
            "advances": 0,
            "records": 0,
            "captures": 0,
            "traces": 0,
            "audits": 0,
        }
        print(f"controlled {case}: {counts}; published_events=0")
        return
    owner = candidate_class(scene, **settings)
    legacy = diagnostics._SyntheticC1MotionOwner(
        scene,
        seed_tick=20,
        pose_m_rad=(2.0, 2.0, scalar(heading_word)),
        speed=speed,
        turn_rate=scalar(turn_word),
        synthetic_test_only=True,
    )
    assert owner._root["recorder"]._scenario is not scene
    previous = None
    consumers = []
    original_cos, original_sin, original_sinc = math.cos, math.sin, np.sinc

    def observed(original, label):
        def call(value):
            consumers.append((label, candidate_class._word(float(value))))
            return original(value)

        return call

    for tick in range(21, 28):
        legacy.advance(tick)
        consumers.clear()
        with monkeypatch.context() as patch:
            patch.setattr(rover, "integrate", forbidden)
            patch.setattr(math, "cos", observed(original_cos, "cos"))
            patch.setattr(math, "sin", observed(original_sin, "sin"))
            patch.setattr(np, "sinc", observed(original_sinc, "sinc"))
            owner.advance(tick)
        event = owner._root["events"][-1]
        words = event["trace"]["intermediate_words"]
        assert consumers[:3] == [
            ("sinc", words[4]),
            ("cos", words[2]),
            ("sin", words[2]),
        ]
        assert event["pose_words"][2] == words[10]
        assert event["trace"]["inputs"] == (
            event["previous_pose_words"][2],
            turn_word,
            0x3FA999999999999A,
            0x400921FB54442D18,
            0x4000000000000000,
        )
        if tick == 21:
            assert words == expected_words
        if tick == 22:
            previous = owner.snapshot()
            root = owner._root
            trace_function = diagnostics._trace_synthetic_binary64_rows
            prepare_function = owner._prepare_event

            def fail_capture(*args, **kwargs):
                counts["captures"] += 1
                raise ValueError("controlled fixture preparation fault")

            def unsupported(*args, _trace=trace_function, **kwargs):
                trace = _trace(*args, **kwargs)
                return {
                    **trace,
                    "supported": False,
                    "rows": (),
                    "reason": "fixture unsupported",
                }

            def fail_prepared(*args, _prepare=prepare_function, **kwargs):
                _prepare(*args, **kwargs)
                raise MemoryError("controlled fixture late preparation fault")

            def mismatched_prepared(*args, _prepare=prepare_function, **kwargs):
                event = _prepare(*args, **kwargs)
                return {**event, "host_frame": b"fixture mismatched staged frame"}

            target, replacement, error = (
                ("capture_synthetic_c1_views", fail_capture, ValueError)
                if case == "straight"
                else (None, mismatched_prepared, ValueError)
                if case == "left"
                else ("_trace_synthetic_binary64_rows", unsupported, ValueError)
                if case == "right"
                else (None, fail_prepared, MemoryError)
                if case == "late_failure"
                else (None, None, None)
            )
            if error is not None:
                with monkeypatch.context() as patch:
                    if target:
                        patch.setattr(diagnostics, target, replacement)
                    else:
                        patch.setattr(owner, "_prepare_event", replacement)
                    with pytest.raises(error):
                        owner.advance(23)
                assert owner._root is root
                assert owner.snapshot()["binding_sha256"] == previous["binding_sha256"]
            for invalid in (True, 22, 24, 85900):
                with pytest.raises(ValueError, match="bounded consecutive"):
                    owner.advance(invalid)
            assert (
                owner.audit(previous)["ownership_status"] == "candidate_binding_matches"
            )
    bundle = owner.snapshot()
    events = bundle["candidate"]["events"]
    assert len(events) == 8
    assert events[0]["kind"] == "seed" and events[0]["trace"] is None
    assert events[0]["previous_pose_words"] is None
    assert events[0]["pose_words"][2] == heading_word
    assert bundle["candidate"]["seed_tick"] == 20
    assert bundle["candidate"]["seed_pose_words"] == events[0]["pose_words"]
    assert bundle["candidate"]["nominal_seconds_ratio"] == (1, 20)
    duration = _literal_binary64_fraction(bundle["candidate"]["duration_word"])
    assert 7 * duration != Fraction(7, 20)
    for index, (event, old) in enumerate(zip(events, legacy._events, strict=True)):
        assert event["tick"] == 20 + index
        assert event["pose_m_rad"] == tuple(old["pose_m_rad"])
        assert event["fixture_state"] == old["fixture_state"]
        assert event["host_frame"] == old["host_frame"]
        state = decode_state(event["host_frame"])
        assert state.timestamp_us == event["tick"] * 50000
        assert event["pose_words"] == tuple(
            candidate_class._word(value) for value in event["pose_m_rad"]
        )
        if index:
            assert event["previous_pose_words"] == events[index - 1]["pose_words"]
            assert event["trace"]["producer_parity_qualified"] is False
    result = owner.audit(bundle)
    assert result["ownership_status"] == "candidate_binding_matches"
    assert result["arithmetic_status"] == "supported_declared_word_trace"
    assert result["events_checked"] == 8
    assert result["motion_status"] == "unresolved_motion_evidence"
    assert result["wire_status"] == "unqualified_candidate_wire"
    assert result["source_status"] == "unqualified_candidate_source"
    assert all(result[flag] is False and bundle[flag] is False for flag in owner._FLAGS)
    assert owner.audit(previous)["ownership_status"] == "inconsistent_candidate_record"
    old = previous["source"]["private_source"]["history"][-1]
    new = bundle["source"]["private_source"]["history"][-1]
    assert (
        old["clock_epoch"] == new["clock_epoch"] == bundle["candidate"]["clock_epoch"]
    )
    assert all(
        item["delivery_tick"] == item["capture"]["capture_ticks"][0] + 2
        for item in bundle["source"]["private_source"]["history"]
    )
    held = bundle["source"]["private_source"]["history"][-2]
    assert held["capture_id"] == new["capture_id"]
    assert held["snapshot_tick"] + 1 == new["snapshot_tick"]
    for field in ("capture_ticks", "capture_poses_m_rad", "tof_m", "tof_valid"):
        assert np.array_equal(held["capture"][field], new["capture"][field])
    for mutate in ("lane", "trace", "frame", "clock", "history", "flag", "missing"):
        changed = deepcopy(bundle)
        if mutate == "lane":
            changed["candidate"]["lane"] = "substituted"
        elif mutate == "trace":
            changed["candidate"]["events"][1]["trace"]["inputs"] = (0,)
        elif mutate == "frame":
            changed["candidate"]["events"][1]["host_frame"] = b"invalid"
        elif mutate == "clock":
            changed["candidate"]["seed_tick"] = 22
        elif mutate == "history":
            changed["source"]["private_source"]["history"][-1]["snapshot_tick"] = 0
        elif mutate == "flag":
            changed["producer_parity_qualified"] = True
        else:
            del changed["candidate"]
        if mutate not in ("flag", "missing"):
            changed["binding_sha256"] = owner._digest(changed)
        assert (
            owner.audit(changed)["ownership_status"] == "inconsistent_candidate_record"
        )
    with pytest.raises(ValueError, match="bounded consecutive"):
        owner.advance(28)
    legacy.snapshot()
    with pytest.raises(ValueError, match="unsupported private C1 motion bundle"):
        legacy.audit(bundle)
    if case == "late_failure":
        publish = owner._publish

        def fail_publication(prepared):
            publish(prepared)
            raise RuntimeError("fixture ambiguous publication")

        with monkeypatch.context() as patch:
            patch.setattr(owner, "_publish", fail_publication)
            with pytest.raises(RuntimeError, match="ambiguous publication"):
                owner.snapshot()
        for operation in (
            owner.snapshot,
            lambda: owner.audit(bundle),
            lambda: owner.advance(28),
        ):
            with pytest.raises(ValueError, match="discarded"):
                operation()
    published = len(owner._root["events"]) + len(legacy._events)
    assert published == 16 and counts["constructors"] == 2
    assert counts["records"] <= 17 and counts["traces"] <= 8
    assert counts["captures"] <= 13
    print(f"controlled {case}: {counts}; published_events={published}")


@pytest.mark.parametrize(
    "case,scene_index,literal_index,speed",
    [
        ("straight", 0, 0, 0.5),
        ("left", 0, 6, 0.5),
        ("right", 1, 7, 0.5),
        ("wrap", 2, 8, 0.5),
        ("wire", 3, 0, 0.6),
        ("signed_zero", 0, 1, 0.0),
        ("late_failure", 1, 6, 0.5),
        ("ingress", 0, 0, 0.5),
    ],
)
def test_synthetic_controlled_candidate_independent_audit(
    monkeypatch, case, scene_index, literal_index, speed
):
    from dataclasses import asdict
    from fractions import Fraction

    from sim import diagnostics

    counts = {
        name: 0
        for name in (
            "constructors",
            "advances",
            "records",
            "captures",
            "traces",
            "receipt_audits",
            "auditor_attempts",
        )
    }

    def counted(original, name):
        def call(*args, **kwargs):
            counts[name] += 1
            return original(*args, **kwargs)

        return call

    for owner_class, method, name in (
        (diagnostics._SyntheticC1ControlledMotionOwner, "__init__", "constructors"),
        (diagnostics._SyntheticC1ControlledMotionOwner, "advance", "advances"),
        (diagnostics._SyntheticC1ControlledMotionOwner, "audit", "receipt_audits"),
        (diagnostics._SyntheticC1SourceRecorder, "record_tick", "records"),
    ):
        monkeypatch.setattr(
            owner_class, method, counted(getattr(owner_class, method), name)
        )
    for name, counter in (
        ("capture_synthetic_c1_views", "captures"),
        ("_trace_synthetic_binary64_rows", "traces"),
        ("_audit_synthetic_controlled_candidate", "auditor_attempts"),
    ):
        monkeypatch.setattr(
            diagnostics, name, counted(getattr(diagnostics, name), counter)
        )
    scenes = (
        Scenario(start=(2, 2, 0), goal=(5, 2)),
        Scenario(start=(2, 2, 0), goal=(5, 2), obstacles=((2.6, 2, 0.30),)),
        Scenario(start=(2, 2, 0), goal=(5, 2), obstacles=((2.4, 2, 0.005),)),
        Scenario(start=(1, 1, 0), goal=(5, 2), obstacles=((2.4, 2, 0.30),)),
    )
    heading, turn, literal_words = _ARITHMETIC_TRACE_LITERALS[literal_index]
    owner = diagnostics._SyntheticC1ControlledMotionOwner(
        scenes[scene_index],
        seed_tick=20,
        position_m=(2.0, 2.0),
        heading_word=heading,
        speed=speed,
        turn_word=turn,
        synthetic_test_only=True,
    )
    for tick in range(21, 28):
        owner.advance(tick)
    bundle = owner.snapshot()
    assert (
        bundle["candidate"]["events"][1]["trace"]["intermediate_words"] == literal_words
    )
    assert owner.audit(bundle)["ownership_status"] == "candidate_binding_matches"

    def retained_anchor(receipt):
        candidate = receipt["candidate"]
        return {
            "current": True,
            **{
                name: candidate[name]
                for name in ("lane", "model", "clock_epoch", "source_files")
            },
            "calibration_identity": receipt["source"]["private_source"][
                "calibration_identity"
            ],
            "reference_tick": 27,
            "binding_sha256": receipt["binding_sha256"],
        }

    anchor = retained_anchor(bundle)
    initial_anchor = deepcopy(anchor)
    initial_digest = owner._digest(bundle)
    initial_root = owner._root

    def forbidden(*args, **kwargs):
        pytest.fail("independent auditor called a producer, transform or query")

    def audit(value, **settings):
        before = dict(counts)
        with monkeypatch.context() as guard:
            for name in (
                "_synthetic_binary64_value",
                "_synthetic_rn64",
                "_synthetic_binary64_operation",
                "_trace_synthetic_binary64_rows",
                "capture_synthetic_c1_views",
                "prepare_synthetic_c1_relative_input",
                "_reference_synthetic_c1_motion",
                "_check_synthetic_c1_motion",
                "_audit_synthetic_c1_source_binding",
                "probe_synthetic_c1_questions",
                "probe_synthetic_c1_relative_questions",
                "probe_synthetic_c1_enclosure",
                "probe_synthetic_c1_occupied_witness",
                "RoverEnv",
                "write_episode",
            ):
                guard.setattr(diagnostics, name, forbidden)
            for owner_class in (
                diagnostics._SyntheticC1ControlledMotionOwner,
                diagnostics._SyntheticC1MotionOwner,
                diagnostics._SyntheticC1SourceRecorder,
            ):
                for method in ("__init__", "snapshot", "audit"):
                    guard.setattr(owner_class, method, forbidden)
            guard.setattr(
                diagnostics._SyntheticC1ControlledMotionOwner, "advance", forbidden
            )
            guard.setattr(
                diagnostics._SyntheticC1SourceRecorder, "record_tick", forbidden
            )
            result = diagnostics._audit_synthetic_controlled_candidate(
                value, **{"synthetic_test_only": True, **settings}
            )
        assert counts == {**before, "auditor_attempts": before["auditor_attempts"] + 1}
        return result

    def resign(value):
        source = value["source"]
        source["binding_sha256"] = diagnostics._c1_source_binding_digest(
            {
                "relative_input": source["relative_input"],
                "fixture_state": asdict(source["fixture_state"]),
                "host_frame": source["private_source"]["host_frame"],
                "private_source": source["private_source"],
            }
        )
        value["binding_sha256"] = owner._digest(value)

    first = audit(bundle)
    assert first["reason"] == "bounded_declared_relations_only"
    assert first["ownership_status"] == "unresolved_anchor"
    assert first["event_status"] == "consistent_checked_relations", first
    owned = audit(bundle, expected_anchor=anchor)
    assert owned["ownership_status"] == "anchor_matches"
    assert owned["content_status"] == "consistent_checked_relations", owned["reason"]
    assert owned["events_checked"] == owned["frames_checked"] == 8
    assert owned["captures_checked"] == owned["copied_records_checked"] == 6
    assert owned["trace_cells_checked"] >= 70
    clocks = owned["elapsed_clocks"]
    assert clocks[0]["nominal_ratio"] == clocks[0]["binary_ratio"] == (0, 1)
    assert Fraction(*clocks[-1]["nominal_ratio"]) == Fraction(7, 20)
    assert Fraction(*clocks[-1]["binary_ratio"]) == 7 * _literal_binary64_fraction(
        0x3FA999999999999A
    )
    assert clocks[-1]["nominal_ratio"] != clocks[-1]["binary_ratio"]
    if speed:
        assert owned["host_changed_fields"]
    for flag in (
        "training_approved",
        "real_input_qualified",
        "free_space_qualified",
        "numerically_certified",
        "producer_parity_qualified",
    ):
        assert owned[flag] is False
    assert {
        "native_motion",
        "native_goal",
        "relative_transforms",
        "source_authority",
        "pending_captures",
        "native_work_trusted_base",
    } <= set(owned["unverified_relations"])
    changed = deepcopy(bundle)
    event = changed["candidate"]["events"][1]
    if case == "straight":
        event["previous_pose_words"] = (0, 0, 0)
        reason = "previous_pose_mismatch"
    elif case == "left":
        cell = event["trace"]["rows"][0]["cells"][0]
        ratio = Fraction(*cell["exact_ratio"]) + 1
        cell["exact_ratio"] = ratio.numerator, ratio.denominator
        reason = "exact_ratio_mismatch"
    elif case == "right":
        event["trace"]["rows"][3]["cells"][3]["truncated_quotient"] += 1
        reason = "truncated_quotient_mismatch"
    elif case == "wrap":
        rows = event["trace"]["rows"]
        event["trace"]["rows"] = (rows[1], rows[0], *rows[2:])
        reason = "trace_row_order_mismatch"
    elif case == "wire":
        event["host_frame"] = event["host_frame"][:-1] + bytes(
            [event["host_frame"][-1] ^ 1]
        )
        reason = "state_frame_mismatch"
    elif case == "signed_zero":
        event["pose_words"] = (
            *event["pose_words"][:2],
            event["pose_words"][2] ^ (1 << 63),
        )
        reason = "pose_word_mismatch"
    elif case == "late_failure":
        history = changed["source"]["private_source"]["history"]
        history[1]["capture"] = deepcopy(history[1]["capture"])
        held = history[1]["capture"]
        index = tuple(np.argwhere(held["tof_valid"])[0])
        held["tof_m"][index] *= np.float32(0.9)
        reason = "held_capture_changed"
    else:
        changed["candidate"]["events"][0]["fixture_state"]["sequence"] = True
        changed["candidate"]["arithmetic_kind"] = np.float32(0)
        reason = "state_integer_type_mismatch"
    resign(changed)
    changed_digest = owner._digest(changed)
    broken = audit(changed, expected_anchor=anchor)
    assert broken["content_status"] == "inconsistent_record", broken["reason"]
    assert broken["reason"] == reason
    if case != "ingress":
        assert broken["ownership_status"] == "anchor_mismatch"
    assert owner._digest(bundle) == initial_digest and anchor == initial_anchor
    assert owner._digest(changed) == changed_digest and owner._root is initial_root

    extra = deepcopy(bundle)
    if case == "straight":
        original_snapshot = diagnostics._SyntheticC1SourceRecorder.snapshot

        def incomplete(recorder):
            source = original_snapshot(recorder)
            source["private_source"]["history"] = []
            source["relative_input"]["history"] = []
            source["binding_sha256"] = diagnostics._c1_source_binding_digest(
                {
                    "relative_input": source["relative_input"],
                    "fixture_state": asdict(source["fixture_state"]),
                    "host_frame": source["private_source"]["host_frame"],
                    "private_source": source["private_source"],
                }
            )
            return source

        with monkeypatch.context() as issuance:
            issuance.setattr(
                diagnostics._SyntheticC1SourceRecorder, "snapshot", incomplete
            )
            issued = owner.snapshot()
        last = audit(issued, expected_anchor=retained_anchor(issued))
        assert last["ownership_status"] == "anchor_matches"
        assert (
            last["trace_status"]
            == last["codec_status"]
            == "consistent_checked_relations"
        )
        assert last["content_status"] == "unresolved_evidence"
        assert last["reason"] == "unsupported_incomplete_delivered_history"
    elif case == "left":
        extra["candidate"]["events"][1]["trace"]["rows"][0]["cells"][0]["word"] += 1
        resign(extra)
        last = audit(extra, expected_anchor=anchor)
        assert last["reason"] == "rounded_neighbor_mismatch"
    elif case == "right":
        entry = extra["source"]["private_source"]["history"][0]["capture"]
        entry["capture_ticks"] = entry["capture_ticks"].astype(np.int64)
        resign(extra)
        last = audit(extra)
        assert last["reason"] == "unsupported_array_dtype"
    elif case == "wrap":
        extra["candidate"]["events"][1]["trace"] = None
        resign(extra)
        last = audit(extra)
        assert last["reason"] == "unsupported_missing_trace"
        assert last["event_status"] == "consistent_checked_relations"
    elif case == "wire":
        extra["candidate"]["events"][1]["trace"]["rows"][0]["cells"][0][
            "exact_ratio"
        ] = (1 << 4096, 1)
        with monkeypatch.context() as preflight:
            preflight.setattr(diagnostics, "_c1_source_binding_digest", forbidden)
            last = audit(extra)
        assert last["reason"] == "unsupported_ratio_size"
        assert last["content_status"] == "unresolved_evidence"
    elif case == "signed_zero":
        last = audit(bundle, expected_anchor={**anchor, "current": False})
        assert last["ownership_status"] == "unresolved_anchor"
        assert last["content_status"] == "consistent_checked_relations"
    elif case == "late_failure":
        record = extra["source"]["relative_input"]["history"][0]
        index = tuple(np.argwhere(record["tof_valid"])[0])
        record["tof_m"][index] *= np.float32(0.9)
        resign(extra)
        last = audit(extra)
        assert last["reason"] == "relative_payload_copy_mismatch"
    else:
        with pytest.raises(ValueError, match="synthetic_test_only=True"):
            audit(bundle, synthetic_test_only=1)
    assert counts == {
        "constructors": 1,
        "advances": 7,
        "records": 8,
        "captures": 6,
        "traces": 7,
        "receipt_audits": 1,
        "auditor_attempts": 4,
    }
    assert len(owner._root["events"]) == 8
    print(f"independent {case}: {counts}; published_events=8")


def test_synthetic_c1_source_recorder_owns_capture():
    from interface.protocol import State
    from sim.diagnostics import _SyntheticC1SourceRecorder

    recorder = _SyntheticC1SourceRecorder(
        Scenario(start=(2, 2, 0)), synthetic_test_only=True
    )
    pose = np.array([2.0, 2.0, 0.0])
    goal = [3, 1, 0]
    for tick in range(20, 24):
        recorder.record_tick(
            tick,
            pose_m_rad=pose,
            fixture_state=State(timestamp_us=tick * 50000, goal_m=goal),
        )
    pose[0], goal[0] = 99, 99
    bundle = recorder.snapshot()
    events = bundle["private_source"]["history"]
    assert [event["snapshot_tick"] for event in events] == [22, 23]
    assert [event["delivery_tick"] for event in events] == [22, 22]
    assert events[0]["capture_id"] == events[1]["capture_id"]
    assert bundle["fixture_state"].goal_m == [3, 1, 0]
    assert bundle["private_source"]["reference_pose_m_rad"] == [2.0, 2.0, 0.0]
    assert recorder.audit(bundle)["status"] == "consistent_under_fixture_assumptions"
    binding = bundle["binding_sha256"]
    bundle["private_source"]["history"][0]["capture"]["tof_m"][:] = 0
    assert recorder.snapshot()["binding_sha256"] == binding
    assert recorder.audit(bundle)["status"] == "inconsistent_source_record"


@pytest.mark.parametrize(
    "case",
    [
        "cadence",
        "bounded_history",
        "reference_event",
        "candidate_copy",
        "private_copy",
        "source_manifest",
        "foreign_recorder",
        "file_drift",
        "invalid_tick",
        "bad_state_timestamp",
        "warmup",
        "opt_in",
        "binary32_change",
        "outside_domain",
        "body_contact",
    ],
)
def test_synthetic_c1_source_recorder_boundaries(monkeypatch, case):
    from dataclasses import asdict

    from interface.protocol import State, encode_state
    from sim import diagnostics

    def forbidden(*args, **kwargs):
        pytest.fail("a private recorder must not query decisions or collect episodes")

    for name in (
        "probe_synthetic_c1_questions",
        "probe_synthetic_c1_relative_questions",
        "probe_synthetic_c1_enclosure",
        "probe_synthetic_c1_occupied_witness",
        "write_episode",
        "RoverEnv",
    ):
        monkeypatch.setattr(diagnostics, name, forbidden)
    scene = (
        Scenario(start=(2, 2, 0), goal=(5, 2), obstacles=((2.4, 2, 0.005),))
        if case == "outside_domain"
        else Scenario(start=(1, 1, 0), goal=(5, 2), obstacles=((2.4, 2, 0.30),))
        if case == "body_contact"
        else Scenario(start=(2, 2, 0))
    )
    recorder = diagnostics._SyntheticC1SourceRecorder(scene, synthetic_test_only=True)
    goal = (scene.goal[0] - 2, scene.goal[1] - 2, 0)

    def record(owner, tick, timestamp=None):
        owner.record_tick(
            tick,
            pose_m_rad=[2, 2, 0],
            fixture_state=State(
                timestamp_us=tick * 50000 if timestamp is None else timestamp,
                velocity_m_s=(0.6 if case == "binary32_change" else 0, 0, 0),
                goal_m=goal,
            ),
        )

    if case == "warmup":
        with pytest.raises(ValueError, match="delivered"):
            recorder.snapshot()
    for tick in range(
        20, 36 if case == "bounded_history" else 23 if case == "warmup" else 24
    ):
        record(recorder, tick)
        assert len(recorder._history) <= 8
        assert len(recorder._pending) <= 2
        if case == "warmup" and tick < 22:
            with pytest.raises(ValueError, match="delivered"):
                recorder.snapshot()
    bundle = recorder.snapshot()
    assert (
        diagnostics._c1_source_binding_digest(bundle["source_files"])
        == bundle["private_source"]["producer_identity"]
    )
    assert set(bundle["source_files"]) == {
        "sim/diagnostics.py",
        "sim/rover.py",
        "interface/protocol.py",
    }
    assert all(len(value) == 64 for value in bundle["source_files"].values())
    assert "scenario" not in bundle["relative_input"]
    assert "source_files" not in bundle["relative_input"]
    assert all(
        bundle[key] is False
        for key in (
            "training_approved",
            "real_input_qualified",
            "free_space_qualified",
            "numerically_certified",
        )
    )
    if case == "cadence":
        assert [
            event["capture"]["capture_ticks"][0]
            for event in bundle["private_source"]["history"]
        ] == [20, 20]
        assert [event["delivery_tick"] for event in recorder._pending] == [24, 25]
    elif case == "bounded_history":
        assert len(bundle["private_source"]["history"]) == 8
        assert [
            event["snapshot_tick"] for event in bundle["private_source"]["history"]
        ] == list(range(28, 36))
    elif case == "reference_event":
        old = bundle
        record(recorder, 24)
        with pytest.raises(ValueError, match="current reference"):
            recorder.audit(old)
        bundle = recorder.snapshot()
        assert bundle["private_source"]["reference_tick"] == 24
        assert bundle["binding_sha256"] != old["binding_sha256"]
        assert recorder.audit(old)["status"] == "inconsistent_source_record"
    elif case in ("candidate_copy", "private_copy", "source_manifest"):
        if case == "candidate_copy":
            bundle["relative_input"]["fixture_goal_body_m"][0] += 1
        elif case == "private_copy":
            bundle["private_source"]["scenario"]["name"] = "rewritten-source"
        else:
            bundle["source_files"]["sim/rover.py"] = "0" * 64
            bundle["private_source"]["producer_identity"] = (
                diagnostics._c1_source_binding_digest(bundle["source_files"])
            )
        bundle["binding_sha256"] = diagnostics._c1_source_binding_digest(
            {
                "relative_input": bundle["relative_input"],
                "fixture_state": asdict(bundle["fixture_state"]),
                "host_frame": encode_state(bundle["fixture_state"]),
                "private_source": bundle["private_source"],
            }
        )
    elif case == "foreign_recorder":
        other = diagnostics._SyntheticC1SourceRecorder(scene, synthetic_test_only=True)
        for tick in range(20, 24):
            record(other, tick)
        foreign = other.snapshot()
        assert (
            foreign["private_source"]["clock_epoch"]
            != bundle["private_source"]["clock_epoch"]
        )
        bundle = foreign
    elif case == "file_drift":
        changed = dict(bundle["source_files"], **{"sim/rover.py": "0" * 64})
        monkeypatch.setattr(recorder, "_source_files", lambda: changed)
        with pytest.raises(ValueError, match="source files changed"):
            recorder.snapshot()
    elif case == "invalid_tick":
        for tick in (True, 23, 25, 85900):
            with pytest.raises(ValueError, match="fixture ticks"):
                record(recorder, tick)
        assert recorder.snapshot()["binding_sha256"] == bundle["binding_sha256"]
    elif case == "bad_state_timestamp":
        with pytest.raises(ValueError, match="timestamp"):
            record(recorder, 24, timestamp=1200001)
        assert recorder.snapshot()["binding_sha256"] == bundle["binding_sha256"]
    elif case == "opt_in":
        with pytest.raises(ValueError, match="synthetic_test_only"):
            diagnostics._SyntheticC1SourceRecorder(scene, synthetic_test_only=1)
        bundle["training_approved"] = True
        with pytest.raises(ValueError, match="unsupported private"):
            recorder.audit(bundle)
        bundle["training_approved"] = False
    for name in (
        "capture_synthetic_c1_views",
        "prepare_synthetic_c1_relative_input",
        "inspect_synthetic_c1_history",
    ):
        monkeypatch.setattr(diagnostics, name, forbidden)
    result = recorder.audit(bundle)
    assert result["status"] == (
        "inconsistent_source_record"
        if case
        in (
            "candidate_copy",
            "private_copy",
            "source_manifest",
            "foreign_recorder",
            "file_drift",
        )
        else "unresolved_source_evidence"
        if case
        in (
            "binary32_change",
            "outside_domain",
            "body_contact",
        )
        else "consistent_under_fixture_assumptions"
    )
    assert set(result) == {
        "allowed_use",
        "training_approved",
        "real_input_qualified",
        "free_space_qualified",
        "numerically_certified",
        "status",
        "reason",
        "binding_sha256",
        "host_changed_fields",
    }
    assert all(
        result[key] is False
        for key in (
            "training_approved",
            "real_input_qualified",
            "free_space_qualified",
            "numerically_certified",
        )
    )
    if case == "binary32_change":
        assert result["reason"] == "host_round_trip_changed"
    elif case == "outside_domain":
        assert result["reason"] == "private_domain_not_established"
    elif case == "body_contact":
        assert result["reason"] == "private_body_clearance_not_established"


def test_synthetic_c1_source_binding_fingerprint():
    from sim.diagnostics import _c1_source_binding_digest

    record = {"epoch": "fixture-epoch", "ranges": np.array([0.5], dtype="<f4")}
    original = _c1_source_binding_digest(record)
    assert original == _c1_source_binding_digest(deepcopy(record))
    record["epoch"] = "different-epoch"
    assert original != _c1_source_binding_digest(record)
    record["epoch"] = "fixture-epoch"
    record["ranges"] = record["ranges"].astype(">f4")
    assert original != _c1_source_binding_digest(record)
    assert _c1_source_binding_digest({"value": True}) != _c1_source_binding_digest(
        {"value": 1}
    )
    assert _c1_source_binding_digest(np.float64(5)) != _c1_source_binding_digest(5.0)
    assert _c1_source_binding_digest(np.float64(5)) != _c1_source_binding_digest(
        np.array(5.0)
    )
    assert _c1_source_binding_digest({"frame": b"first"}) != _c1_source_binding_digest(
        {"frame": b"second"}
    )


@pytest.fixture
def c1_source(c1_history):
    from dataclasses import asdict

    from interface.protocol import State, encode_state
    from sim.diagnostics import prepare_synthetic_c1_relative_input

    scene = Scenario(start=(2, 2, 0))
    state = State(timestamp_us=1150000, velocity_m_s=(0.5, 0, 0), goal_m=(3, 1, 0))
    relative = prepare_synthetic_c1_relative_input(
        c1_history,
        reference_tick=23,
        reference_pose_m_rad=[2, 2, 0],
        fixture_goal_m=scene.goal,
        synthetic_test_only=True,
    )
    source = {
        "producer_identity": "declared-ideal-fixture-producer",
        "calibration_identity": "declared-ideal-c1-profile",
        "clock_epoch": "fixture-epoch-0",
        "reference_epoch": "fixture-epoch-0",
        "reference_tick": 23,
        "reference_pose_m_rad": [2.0, 2.0, 0.0],
        "fixture_goal_m": list(scene.goal),
        "fixture_state": asdict(state),
        "host_frame": encode_state(state),
        "arena_yaw_rad": 0.0,
        "config": deepcopy(relative["config"]),
        "scenario": asdict(scene),
        "history": [
            {
                "clock_epoch": "fixture-epoch-0",
                "capture_id": f"capture-{int(record['capture_ticks'][0])}",
                "delivery_tick": int(record["capture_ticks"][0]) + 2,
                "snapshot_tick": 16 + index,
                "capture": deepcopy(record),
            }
            for index, record in enumerate(c1_history)
        ],
    }
    return relative, state, source


@pytest.mark.parametrize(
    "case",
    [
        "consistent",
        "array_shape",
        "reference_rebind",
        "changed_payload",
        "mask",
        "endian",
        "boolean_tick",
        "missing_identity",
        "changed_identity",
        "calibration",
        "epoch",
        "missing_binding",
        "missing_delivery",
        "capture_epoch",
        "reused_capture_id",
        "late_delivery",
        "view_clock",
        "reversed_capture_time",
        "held_tamper",
        "changed_reference",
        "inverse_transform",
        "arena",
        "scale",
        "velocity_round_trip",
        "goal_round_trip",
        "goal_binding",
        "motion_binding",
        "outside_domain",
        "body_contact",
        "private_payload_leak",
        "opt_in",
    ],
)
def test_synthetic_c1_source_binding_audit(c1_source, monkeypatch, case):
    from dataclasses import asdict, replace

    from interface.protocol import encode_state
    from sim import diagnostics

    relative, state, source = c1_source

    def binding():
        return diagnostics._c1_source_binding_digest(
            {
                "relative_input": relative,
                "fixture_state": asdict(state),
                "host_frame": encode_state(state),
                "private_source": source,
            }
        )

    original_binding = binding()
    event = source["history"][3]
    record = relative["history"][3]
    if case == "array_shape":
        record["tof_m"] = record["tof_m"].reshape(8, 64)
    elif case == "reference_rebind":
        source["reference_pose_m_rad"][0] = 1.984375
        relative = diagnostics.prepare_synthetic_c1_relative_input(
            [entry["capture"] for entry in source["history"]],
            reference_tick=23,
            reference_pose_m_rad=source["reference_pose_m_rad"],
            fixture_goal_m=source["fixture_goal_m"],
            synthetic_test_only=True,
        )
        state = replace(state, goal_m=(3.015625, 1, 0))
        source["fixture_state"] = asdict(state)
        source["host_frame"] = encode_state(state)
    elif case in ("changed_payload", "mask", "held_tamper"):
        index = tuple(np.argwhere(record["tof_valid"])[0])
        if case == "mask":
            record["tof_valid"][index] = False
            record["tof_m"][index] = 0
        else:
            record["tof_m"][index] *= 0.9
        if case == "held_tamper":
            event["capture"]["tof_m"] = record["tof_m"].copy()
    elif case == "endian":
        record["tof_m"] = record["tof_m"].astype(">f4")
    elif case == "boolean_tick":
        relative["reference_tick"] = True
    elif case == "missing_identity":
        del source["producer_identity"]
    elif case == "changed_identity":
        source["producer_identity"] = "changed-lineage"
    elif case == "calibration":
        source["calibration_identity"] = "changed-profile"
        source["config"]["wall_height"] = 2.0
    elif case == "epoch":
        source["reference_epoch"] = "different-reference-epoch"
    elif case == "missing_delivery":
        del event["delivery_tick"]
    elif case == "capture_epoch":
        event["clock_epoch"] = "different-epoch"
    elif case == "reused_capture_id":
        event["capture_id"] = source["history"][0]["capture_id"]
    elif case == "late_delivery":
        event["delivery_tick"] += 1
    elif case == "view_clock":
        event["capture"]["capture_ticks"][1] += 1
    elif case == "reversed_capture_time":
        event["capture"]["capture_ticks"][:] = 14
        event["delivery_tick"] = 16
    elif case == "changed_reference":
        source["reference_pose_m_rad"][0] = 2.01
    elif case == "inverse_transform":
        record["capture_poses_body_m_rad"][:, 0] *= -1
    elif case == "arena":
        relative["fixture_arena_yaw_rad"] = 0.1
    elif case == "scale":
        relative["numerical_source_scale"] = 1.0
    elif case in ("velocity_round_trip", "goal_round_trip"):
        state = replace(
            state,
            **(
                {"velocity_m_s": (0.6, 0, 0)}
                if case == "velocity_round_trip"
                else {"goal_m": (3 + 1e-12, 1, 0)}
            ),
        )
        source["fixture_state"] = asdict(state)
    elif case == "goal_binding":
        relative["fixture_goal_body_m"][0] = 2.0
    elif case == "motion_binding":
        source["host_frame"] = encode_state(replace(state, velocity_m_s=(0.25, 0, 0)))
    elif case == "outside_domain":
        source["scenario"] = asdict(
            Scenario(start=(2, 2, 0), goal=(5, 2), obstacles=((2.4, 2, 0.005),))
        )
    elif case == "body_contact":
        source["scenario"] = asdict(
            Scenario(start=(1, 1, 0), goal=(5, 2), obstacles=((2.4, 2, 0.30),))
        )
    elif case == "private_payload_leak":
        relative["scenario"] = deepcopy(source["scenario"])

    def forbidden(*args, **kwargs):
        pytest.fail("a private source audit must not run a producer or decision query")

    for name in (
        "prepare_synthetic_c1_relative_input",
        "capture_synthetic_c1_views",
        "inspect_synthetic_c1_history",
        "probe_synthetic_c1_questions",
        "probe_synthetic_c1_relative_questions",
        "probe_synthetic_c1_enclosure",
        "probe_synthetic_c1_occupied_witness",
        "write_episode",
    ):
        monkeypatch.setattr(diagnostics, name, forbidden)
    frozen = binding()
    expected = (
        None
        if case == "missing_binding"
        else original_binding
        if case in ("changed_identity", "endian")
        else frozen
    )
    if case == "opt_in":
        with pytest.raises(ValueError, match="synthetic_test_only"):
            diagnostics._audit_synthetic_c1_source_binding(
                relative,
                fixture_state=state,
                private_source=source,
                expected_binding=expected,
            )
        return
    result = diagnostics._audit_synthetic_c1_source_binding(
        relative,
        fixture_state=state,
        private_source=source,
        expected_binding=expected,
        synthetic_test_only=True,
    )
    assert binding() == frozen
    assert result["status"] == (
        "consistent_under_fixture_assumptions"
        if case in ("consistent", "reference_rebind")
        else "inconsistent_source_record"
        if case
        in (
            "changed_identity",
            "endian",
            "changed_payload",
            "mask",
            "capture_epoch",
            "reused_capture_id",
            "late_delivery",
            "view_clock",
            "reversed_capture_time",
            "held_tamper",
            "arena",
            "scale",
            "goal_binding",
            "motion_binding",
        )
        else "unresolved_source_evidence"
    )
    assert set(result) == {
        "allowed_use",
        "training_approved",
        "real_input_qualified",
        "free_space_qualified",
        "numerically_certified",
        "status",
        "reason",
        "binding_sha256",
        "host_changed_fields",
    }
    assert result["allowed_use"] == "private_synthetic_source_audit_only"
    assert all(
        result[key] is False
        for key in (
            "training_approved",
            "real_input_qualified",
            "free_space_qualified",
            "numerically_certified",
        )
    )
    if case in ("velocity_round_trip", "goal_round_trip"):
        assert result["reason"] == "host_round_trip_changed"
        assert result["host_changed_fields"] == (
            ("velocity_m_s",) if case == "velocity_round_trip" else ("goal_m",)
        )
    elif case == "held_tamper":
        assert result["reason"] == "held_capture_changed"
    elif case == "calibration":
        assert result["reason"] == "unsupported_candidate_scope_or_profile"
    elif case == "epoch":
        assert result["reason"] == "reference_clock_epoch_mismatch"
    elif case == "motion_binding":
        assert result["reason"] == "private_host_frame_mismatch"
    elif case == "outside_domain":
        assert result["reason"] == "private_domain_not_established"
    elif case == "body_contact":
        assert result["reason"] == "private_body_clearance_not_established"


@pytest.fixture
def c1_relative(c1_history):
    from interface.protocol import State
    from sim.diagnostics import prepare_synthetic_c1_relative_input

    relative = prepare_synthetic_c1_relative_input(
        c1_history,
        reference_tick=23,
        reference_pose_m_rad=[2, 2, 0],
        fixture_goal_m=[5, 2],
        synthetic_test_only=True,
    )
    return relative, {
        "fixture_state": State(
            timestamp_us=1150000, velocity_m_s=(0.6, 0, 0), goal_m=(3, 0, 0)
        ),
        "fixture_current_body_clear": True,
        "fixture_controlled_envelope": True,
        "synthetic_test_only": True,
    }


@pytest.mark.parametrize(
    "case",
    [
        "momentum",
        "rest",
        "near_tie",
        "body_conflict",
        "rotated",
        "held",
        "large",
        "lost_scale",
    ],
)
def test_synthetic_c1_relative_special_comparisons(case):
    from interface.protocol import State
    from sim.diagnostics import (
        capture_synthetic_c1_views,
        prepare_synthetic_c1_relative_input,
        probe_synthetic_c1_questions,
        probe_synthetic_c1_relative_questions,
    )

    speed = 0.2 if case == "momentum" else 0 if case == "rest" else 0.6
    yaw = 0.37 if case == "rotated" else 0
    goal = (0.5, 2 + 1e-12) if case == "near_tie" else (5, 2)
    obstacles = (
        ((2.7, 2, 0.30),)
        if case == "momentum"
        else ((2.4, 2, 0.30),)
        if case == "body_conflict"
        else ()
    )
    if case == "rotated":
        obstacles = ((2 + 0.6 * math.cos(yaw), 2 + 0.6 * math.sin(yaw), 0.30),)
    scene = Scenario(
        start=(1, 1, 0) if case == "body_conflict" else (2, 2, yaw),
        goal=goal,
        obstacles=obstacles,
        obstacle_heights=(1.0,) if case == "rotated" else (),
    )
    forward = np.array([math.cos(yaw), math.sin(yaw)])
    record = capture_synthetic_c1_views(
        scene,
        pose_m_rad=[
            *(
                np.array([2, 2]) - speed * 0.15 * forward
                if case == "momentum"
                else np.array([2, 2]) - 0.09 * forward
            ),
            yaw,
        ],
        capture_tick=20,
        synthetic_test_only=True,
    )
    reference = np.array([2.0, 2.0, yaw])
    world_goal = np.array(goal, dtype=float)
    if case in ("large", "lost_scale"):
        offset = 1e12 if case == "large" else 1e16
        reference[:2] += offset
        world_goal += offset
        record["capture_poses_m_rad"][:, :2] += offset
    history = [deepcopy(record), record] if case == "held" else [record]
    old = probe_synthetic_c1_questions(
        history,
        reference_tick=23,
        reference_pose_m_rad=reference,
        fixture_goal_m=world_goal,
        speed=speed,
        turn_rate=0,
        current_body_clear=True,
        controlled_envelope=True,
        synthetic_test_only=True,
    )
    relative = prepare_synthetic_c1_relative_input(
        history,
        reference_tick=23,
        reference_pose_m_rad=reference,
        fixture_goal_m=world_goal,
        synthetic_test_only=True,
    )
    result = probe_synthetic_c1_relative_questions(
        relative,
        fixture_state=State(
            timestamp_us=1150000,
            velocity_m_s=(speed, 0, 0),
            goal_m=(*(relative["fixture_goal_body_m"] or [3, 0]), 0),
        ),
        fixture_current_body_clear=True,
        fixture_controlled_envelope=True,
        synthetic_test_only=True,
    )
    if case in ("large", "lost_scale"):
        assert all(value is None for value in result["candidate_values"].values())
        assert result["reason"] == "unsupported_numerical_scale"
    else:
        assert result["candidate_values"] == old["candidate_values"]
        assert result["status"] == old["status"]
    if case == "momentum":
        assert result["candidate_values"]["speed_tier"] == "2"
    elif case in ("rest", "near_tie"):
        assert result["candidate_values"]["clear_sector"] is None
    elif case == "body_conflict":
        assert result["status"] == "inconsistent_fixture_evidence"


@pytest.mark.parametrize(
    "case",
    [
        "missing_goal",
        "aged_goal",
        "aged_velocity",
        "aged_angular",
        "clock_offset",
        "clock_reset",
        "lateral_speed",
        "roll_rate",
        "nonplanar_goal",
        "goal_binding",
        "task",
        "opt_in",
        "body_flag",
        "domain_flag",
        "missing_scale",
        "low_scale",
        "infinite_scale",
        "huge_scale",
        "boolean_arena",
        "arena_range",
        "profile",
        "schema",
        "scope",
        "held_change",
        "view_clock",
        "translation_error",
        "heading_error",
        "clock_error",
        "work_boolean",
    ],
)
def test_synthetic_c1_relative_rejects_unsupported_evidence(c1_relative, case):
    from dataclasses import replace

    from sim.diagnostics import probe_synthetic_c1_relative_questions

    relative, settings = c1_relative
    state = settings["fixture_state"]
    rejected = case in (
        "task",
        "opt_in",
        "infinite_scale",
        "boolean_arena",
        "work_boolean",
    )
    if case == "missing_goal":
        settings["fixture_state"] = replace(
            state,
            validity=3,
            ages_us=(0, 0, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF),
            goal_m=(0, 0, 0),
        )
    elif case.startswith("aged_"):
        index = {"aged_velocity": 0, "aged_angular": 1, "aged_goal": 2}[case]
        ages = list(state.ages_us)
        ages[index] = 1
        settings["fixture_state"] = replace(state, ages_us=tuple(ages))
    elif case in ("clock_offset", "clock_reset"):
        settings["fixture_state"] = replace(
            state, timestamp_us=1150001 if case == "clock_offset" else 0
        )
    elif case == "lateral_speed":
        settings["fixture_state"] = replace(state, velocity_m_s=(0.6, 0.01, 0))
    elif case == "roll_rate":
        settings["fixture_state"] = replace(state, angular_velocity_rad_s=(0.01, 0, 0))
    elif case in ("nonplanar_goal", "goal_binding"):
        settings["fixture_state"] = replace(
            state, goal_m=(3, 0, 0.01) if case == "nonplanar_goal" else (2, 0, 0)
        )
    elif case == "task":
        settings["fixture_state"] = replace(state, task_id=2)
    elif case == "opt_in":
        settings["synthetic_test_only"] = False
    elif case in ("body_flag", "domain_flag"):
        settings[
            "fixture_current_body_clear"
            if case == "body_flag"
            else "fixture_controlled_envelope"
        ] = 1
    elif case == "missing_scale":
        del relative["numerical_source_scale"]
    elif case in ("low_scale", "infinite_scale", "huge_scale"):
        relative["numerical_source_scale"] = {
            "low_scale": 1,
            "infinite_scale": np.inf,
            "huge_scale": 1e308,
        }[case]
    elif case in ("boolean_arena", "arena_range"):
        relative["fixture_arena_yaw_rad"] = True if case == "boolean_arena" else 4
    elif case == "profile":
        relative["config"]["wall_height"] = 2
    elif case == "schema":
        relative["schema"] = "unqualified"
    elif case == "scope":
        relative["training_approved"] = True
    elif case == "held_change":
        relative["history"] = [
            deepcopy(relative["history"][-1]),
            relative["history"][-1],
        ]
        changed = tuple(np.argwhere(relative["history"][0]["tof_valid"])[0])
        relative["history"][0]["tof_m"][changed] *= 0.9
    elif case == "view_clock":
        relative["history"][-1]["capture_ticks"][0] -= 1
    elif case in ("translation_error", "heading_error", "clock_error"):
        settings[
            {
                "translation_error": "fixture_transform_error_m",
                "heading_error": "fixture_heading_error_rad",
                "clock_error": "fixture_clock_error_s",
            }[case]
        ] = 0.001
    else:
        settings["max_cells"] = True
    if rejected:
        with pytest.raises(ValueError):
            probe_synthetic_c1_relative_questions(relative, **settings)
    else:
        result = probe_synthetic_c1_relative_questions(relative, **settings)
        assert result["status"] == "unknown"
        assert all(value is None for value in result["candidate_values"].values())
        assert result["queries"] == {}


@pytest.mark.parametrize("side", [-1, 1])
def test_full_synthetic_history_can_hide_a_normal_cylinder_from_a_turning_sweep(side):
    from sim.navigation import evaluate_synthetic
    from teacher.label_pipeline import prepare_request

    config = Config(noise_std=0, dropout=0)
    speed, turn = 0.6, side * 1.5
    current_tick = 23
    scenes = [
        Scenario(start=(2, 2, 0), goal=(5, 2)),
        Scenario(
            start=(2, 2, 0), goal=(5, 2), obstacles=((2.3, 2 + side * 0.47, 0.3),)
        ),
    ]
    captures = (0, 2, 3, 4, 6, 7, 8, 10, 11, 12, 14, 15, 16, 18, 19, 20, 22, 23)
    rendered, references = [], []
    for scene in scenes:
        scene.validate(config)
        ego_history, tof_history, valid_history = [], [], []
        for tick in range(current_tick - config.history_ticks + 1, current_tick + 1):
            position, yaw = integrate(
                [2, 2], 0, speed, turn, (tick - current_tick) * config.dt
            )
            assert not swept_collision(
                position, position, config.radius, scene.obstacles, scene.bounds
            )
            delta = np.asarray(scene.goal) - position
            cosine, sine = math.cos(yaw), math.sin(yaw)
            ego_history.append(
                [
                    speed,
                    turn,
                    cosine * delta[0] + sine * delta[1],
                    -sine * delta[0] + cosine * delta[1],
                ]
            )
            sample_tick = max(
                capture
                for capture in captures
                if capture <= tick - config.latency_ticks
            )
            capture_position, capture_yaw = integrate(
                [2, 2], 0, speed, turn, (sample_tick - current_tick) * config.dt
            )
            ranges = tof_ranges(capture_position, capture_yaw, scene, config)
            valid = np.isfinite(ranges) & (ranges < config.max_range)
            tof_history.append(np.where(valid, ranges, 0).astype(np.float32))
            valid_history.append(valid)
        ego_history = np.asarray(ego_history, dtype=np.float32)
        tof_history = np.asarray(tof_history)
        valid_history = np.asarray(valid_history)
        observation = {
            "schema": "micro-classifier/sim-observation/1",
            "tick": current_tick,
            "time_s": current_tick * config.dt,
            "ego": ego_history[-1],
            "goal_body_m": ego_history[-1, 2:],
            "tof_m": tof_history[-1],
            "tof_valid": valid_history[-1],
            "tof_age_s": (current_tick - sample_tick) * config.dt,
            "tof_sample_tick": sample_tick,
            "history_ego": ego_history,
            "history_tof_m": tof_history,
            "history_tof_valid": valid_history,
            "history_valid": np.ones(config.history_ticks, dtype=bool),
        }
        rendered.append(prepare_request(observation, config=config)["state"])
        references.append(
            evaluate_synthetic(
                scene,
                speed=speed,
                turn_rate=turn,
                tof_age_s=observation["tof_age_s"],
                config=config,
                synthetic_test_only=True,
            )["answers"]["path_blocked"]
        )
    assert rendered[0] == rendered[1]
    assert references == ["false", "true"]


@pytest.mark.parametrize("side", [-1, 1])
def test_synthetic_c1_capture_distinguishes_normal_history_aliases(side):
    from sim.diagnostics import capture_synthetic_c1_views

    scene = Scenario(
        start=(2, 2, 0), goal=(5, 2), obstacles=((2.3, 2 + side * 0.47, 0.3),)
    )
    empty = Scenario(start=scene.start, goal=scene.goal)
    differences = 0
    for capture_tick in (14, 15, 16, 16, 18, 19, 20, 20):
        position, yaw = integrate(
            [2, 2], 0, 0.6, side * 1.5, (capture_tick - 23) * 0.05
        )
        settings = {
            "pose_m_rad": [*position, yaw],
            "capture_tick": capture_tick,
            "synthetic_test_only": True,
        }
        first = capture_synthetic_c1_views(empty, **settings)
        second = capture_synthetic_c1_views(scene, **settings)
        assert second["tof_m"].shape == (8, 8, 8)
        assert second["tof_m"].dtype == np.float32
        assert second["free_space_qualified"] is False
        assert second["training_approved"] is False
        assert "scenario" not in second
        differences += np.count_nonzero(
            (first["tof_m"] != second["tof_m"])
            | (first["tof_valid"] != second["tof_valid"])
        )
    assert differences == 317


@pytest.fixture
def c1_history():
    from sim.diagnostics import capture_synthetic_c1_views

    records = []
    for tick in (14, 15, 16, 16, 18, 19, 20, 20):
        position, yaw = integrate([2, 2], 0, 0.6, 0, (tick - 23) * 0.05)
        records.append(
            capture_synthetic_c1_views(
                Scenario(start=(2, 2, 0)),
                pose_m_rad=[*position, yaw],
                capture_tick=tick,
                synthetic_test_only=True,
            )
        )
    return records


def test_synthetic_c1_history_registers_without_qualifying_free_space(c1_history):
    from sim.diagnostics import inspect_synthetic_c1_history

    result = inspect_synthetic_c1_history(
        c1_history,
        reference_tick=23,
        reference_pose_m_rad=[2, 2, 0],
        synthetic_test_only=True,
    )
    assert result["status"] == "registered_fixture"
    assert result["unique_capture_count"] == 6
    assert result["latest_age_ticks"] == 3
    assert result["free_space_qualified"] is False
    assert result["real_input_qualified"] is False
    valid = result["point_valid"].copy()
    assert result["points_body_m"].shape == (8, 8, 8, 3)
    assert np.all(result["points_body_m"][~valid] == 0)
    result["point_valid"][:] = False
    assert np.any(c1_history[-1]["tof_valid"])
    shifted = inspect_synthetic_c1_history(
        c1_history,
        reference_tick=23,
        reference_pose_m_rad=[3, 2, 0],
        synthetic_test_only=True,
    )
    assert shifted["points_body_m"][valid, 0] == pytest.approx(
        result["points_body_m"][valid, 0] - 1
    )
    rotated = inspect_synthetic_c1_history(
        c1_history,
        reference_tick=23,
        reference_pose_m_rad=[2, 2, math.pi / 2],
        synthetic_test_only=True,
    )
    assert rotated["points_body_m"][valid, 0] == pytest.approx(
        result["points_body_m"][valid, 1]
    )
    assert rotated["points_body_m"][valid, 1] == pytest.approx(
        -result["points_body_m"][valid, 0]
    )


def test_synthetic_c1_preserves_the_complete_slender_alias(c1_history):
    from sim.diagnostics import capture_synthetic_c1_views
    from sim.navigation import evaluate_synthetic

    scene = Scenario(start=(2, 2, 0), goal=(5, 2), obstacles=((2.4, 2, 0.005),))
    for record in c1_history:
        other = capture_synthetic_c1_views(
            scene,
            pose_m_rad=record["capture_poses_m_rad"][0],
            capture_tick=int(record["capture_ticks"][0]),
            synthetic_test_only=True,
        )
        assert np.array_equal(record["tof_m"], other["tof_m"])
        assert np.array_equal(record["tof_valid"], other["tof_valid"])
    answers = [
        evaluate_synthetic(
            world,
            speed=0.6,
            turn_rate=0,
            tof_age_s=0.15,
            synthetic_test_only=True,
        )["answers"]["path_blocked"]
        for world in (Scenario(start=scene.start), scene)
    ]
    assert answers == ["false", "true"]


def test_synthetic_c1_downward_views_reveal_the_near_low_fixture():
    from sim.diagnostics import capture_synthetic_c1_views

    empty = Scenario(start=(2, 2, 0))
    scene = Scenario(
        start=empty.start, obstacles=((2.21, 2, 0.02),), obstacle_heights=(0.05,)
    )
    settings = {"pose_m_rad": [2, 2, 0], "capture_tick": 0, "synthetic_test_only": True}
    first = capture_synthetic_c1_views(empty, **settings)
    second = capture_synthetic_c1_views(scene, **settings)
    assert np.count_nonzero(first["tof_m"] != second["tof_m"]) == 4
    for index in range(8):
        assert np.array_equal(
            tof_ranges([2, 2], index * math.pi / 4, empty, Config()),
            tof_ranges([2, 2], index * math.pi / 4, scene, Config()),
        )


def test_synthetic_c1_masks_ranges_rounding_to_the_ceiling(monkeypatch):
    from sim.diagnostics import capture_synthetic_c1_views

    monkeypatch.setattr(
        "sim.diagnostics.tof_ranges",
        lambda *args: np.full((8, 8), np.nextafter(4.0, 0)),
    )
    record = capture_synthetic_c1_views(
        Scenario(),
        pose_m_rad=[2, 2, 0],
        capture_tick=0,
        synthetic_test_only=True,
    )
    assert not np.any(record["tof_valid"])
    assert np.all(record["tof_m"] == 0)


@pytest.mark.parametrize(
    "field,value",
    [
        ("noise_std", 0.02),
        ("dropout", 0.02),
        ("odometry_position_error", 0.02),
        ("odometry_heading_error", 0.01),
        ("odometry_latency_ticks", 1),
        ("tof_mount_height", None),
        ("field_of_view", math.pi / 3),
        ("tof_rate_hz", None),
        ("latency_ticks", 1),
        ("dt", 0.1),
        ("history_ticks", 4),
    ],
)
def test_synthetic_c1_rejects_unqualified_profiles(field, value):
    from sim.diagnostics import capture_synthetic_c1_views

    config = Config(**{"noise_std": 0, "dropout": 0, field: value})
    with pytest.raises(ValueError, match="profile"):
        capture_synthetic_c1_views(
            Scenario(),
            pose_m_rad=[2, 2, 0],
            capture_tick=0,
            config=config,
            synthetic_test_only=True,
        )


@pytest.mark.parametrize(
    "pose,tick",
    [
        ([2, 2, np.nan], 0),
        ([2, 2, np.inf], 0),
        ([2, 2], 0),
        ([True, False, True], 0),
        ([2, 2, 10**400], 0),
        ([True, 2, 0], 0),
        ([2, 2, 0], True),
        ([2, 2, 0], -1),
        ([2, 2, 0], 2**32),
        ([2, 2, 0], 1),
    ],
)
def test_synthetic_c1_capture_rejects_malformed_pose_or_tick(pose, tick):
    from sim.diagnostics import capture_synthetic_c1_views

    with pytest.raises(ValueError):
        capture_synthetic_c1_views(
            Scenario(),
            pose_m_rad=pose,
            capture_tick=tick,
            synthetic_test_only=True,
        )


@pytest.mark.parametrize(
    "fault",
    [
        "schema",
        "scope",
        "extra_truth",
        "config",
        "view_tick",
        "view_pose",
        "range_nan",
        "range_ceiling",
        "mask_type",
        "shape",
        "held_changed",
        "empty",
        "too_many",
        "old",
        "future",
        "off_cadence",
        "no_support",
    ],
)
def test_synthetic_c1_history_rejects_unsupported_evidence(c1_history, fault):
    from sim.diagnostics import inspect_synthetic_c1_history

    record = c1_history[-1]
    if fault == "schema":
        record["schema"] = "micro-classifier/sim-observation/1"
    elif fault == "scope":
        record["free_space_qualified"] = 0
    elif fault == "extra_truth":
        record["scenario"] = {}
    elif fault == "config":
        record["config"]["noise_std"] = 0.02
    elif fault == "view_tick":
        record["capture_ticks"][0] += 1
    elif fault == "view_pose":
        record["capture_poses_m_rad"][0, 0] += 0.1
    elif fault == "range_nan":
        record["tof_m"][0, 0, 0] = np.nan
    elif fault == "range_ceiling":
        record["tof_valid"][0, 0, 0] = True
        record["tof_m"][0, 0, 0] = 4
    elif fault == "mask_type":
        record["tof_valid"] = record["tof_valid"].astype(np.uint8)
    elif fault == "shape":
        record["tof_m"] = record["tof_m"][0]
    elif fault == "held_changed":
        row, column = np.argwhere(record["tof_valid"][0])[0]
        record["tof_m"][0, row, column] += np.float32(0.001)
    elif fault == "empty":
        c1_history.clear()
    elif fault == "too_many":
        c1_history.append(record)
    elif fault == "old":
        c1_history = [c1_history[0]]
    elif fault == "future":
        c1_history = [record]
        record["capture_ticks"][:] = 23
    elif fault == "off_cadence":
        c1_history = [record]
        record["capture_ticks"][:] = 21
    elif fault == "no_support":
        c1_history = [record]
        record["tof_valid"][:] = False
        record["tof_m"][:] = 0
    result = inspect_synthetic_c1_history(
        c1_history,
        reference_tick=23,
        reference_pose_m_rad=[2, 2, 0],
        synthetic_test_only=True,
    )
    assert result["status"] == "unknown"
    assert result["points_body_m"] is None
    assert result["free_space_qualified"] is False


@pytest.mark.parametrize("opt_in", [False, None, 1, "true"])
def test_synthetic_c1_requires_explicit_opt_in(opt_in):
    from sim.diagnostics import capture_synthetic_c1_views, inspect_synthetic_c1_history

    with pytest.raises(ValueError, match="synthetic_test_only"):
        capture_synthetic_c1_views(
            object(), pose_m_rad=None, capture_tick=None, synthetic_test_only=opt_in
        )
    with pytest.raises(ValueError, match="synthetic_test_only"):
        inspect_synthetic_c1_history(
            object(),
            reference_tick=None,
            reference_pose_m_rad=None,
            synthetic_test_only=opt_in,
        )


@pytest.mark.parametrize("config", [False, 0, {}, "ideal"])
def test_synthetic_c1_rejects_non_config_arguments(config):
    from sim.diagnostics import capture_synthetic_c1_views

    with pytest.raises(ValueError, match="Config instance"):
        capture_synthetic_c1_views(
            Scenario(),
            pose_m_rad=[2, 2, 0],
            capture_tick=0,
            config=config,
            synthetic_test_only=True,
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("reference_tick", True),
        ("reference_tick", -1),
        ("reference_tick", 2**32),
        ("max_age_ticks", True),
        ("max_age_ticks", -1),
        ("max_age_ticks", 9),
        ("reference_pose_m_rad", [2, 2, np.nan]),
        ("reference_pose_m_rad", [True, 2, 0]),
    ],
)
def test_synthetic_c1_rejects_malformed_reference(c1_history, field, value):
    from sim.diagnostics import inspect_synthetic_c1_history

    settings = {
        "reference_tick": 23,
        "reference_pose_m_rad": [2, 2, 0],
        "synthetic_test_only": True,
        field: value,
    }
    with pytest.raises(ValueError):
        inspect_synthetic_c1_history(c1_history, **settings)


def test_synthetic_c1_is_not_a_normal_input(c1_history):
    from teacher.label_pipeline import prepare_request

    assert Config().tof_mount_pitch == 0
    assert Config().noise_std == 0.02
    assert Config().history_ticks == 8
    with pytest.raises(ValueError):
        prepare_request(c1_history[-1], config=Config())


def test_synthetic_c1_low_segments_stop_before_surfaces(c1_history):
    from sim.diagnostics import _c1_low_free_segments, inspect_synthetic_c1_history

    result = inspect_synthetic_c1_history(
        c1_history,
        reference_tick=23,
        reference_pose_m_rad=[2, 2, 0],
        synthetic_test_only=True,
    )
    config = Config(**c1_history[-1]["config"])
    segments, guard = _c1_low_free_segments(
        c1_history[-1],
        result,
        [2, 2, 0],
        config,
    )
    assert len(segments) > 0
    assert segments.shape[1:] == (2, 3)
    assert np.all(segments[..., 2] > 0)
    assert np.all(segments[..., 2] < 0.05)
    assert np.all(segments[:, 0, 2] > segments[:, 1, 2])
    assert guard > 0
    shifted = inspect_synthetic_c1_history(
        c1_history,
        reference_tick=23,
        reference_pose_m_rad=[3, 2, 0],
        synthetic_test_only=True,
    )
    other, _ = _c1_low_free_segments(c1_history[-1], shifted, [3, 2, 0], config)
    assert other[..., 0] == pytest.approx(segments[..., 0] - 1)
    assert other[..., 1:] == pytest.approx(segments[..., 1:])


@pytest.mark.parametrize("background_height", [0.05, 1.0])
def test_synthetic_c1_geometric_occlusion_stops_free_prefixes(
    c1_history, background_height
):
    from sim.diagnostics import (
        _c1_low_free_segments,
        capture_synthetic_c1_views,
        inspect_synthetic_c1_history,
        probe_synthetic_c1_enclosure,
    )

    foreground, background = (2.5, 2, 0.30), (3.2, 2, 0.30)
    scenes = (
        Scenario(start=(2, 2, 0), obstacles=(foreground,), obstacle_heights=(0.5,)),
        Scenario(
            start=(2, 2, 0),
            obstacles=(foreground, background),
            obstacle_heights=(0.5, background_height),
        ),
        Scenario(
            start=(2, 2, 0),
            obstacles=(background,),
            obstacle_heights=(background_height,),
        ),
    )
    records, visible_without_foreground = [], 0
    for empty in c1_history:
        captures = [
            capture_synthetic_c1_views(
                scene,
                pose_m_rad=empty["capture_poses_m_rad"][0],
                capture_tick=int(empty["capture_ticks"][0]),
                synthetic_test_only=True,
            )
            for scene in scenes
        ]
        assert np.array_equal(captures[0]["tof_m"], captures[1]["tof_m"])
        assert np.array_equal(captures[0]["tof_valid"], captures[1]["tof_valid"])
        visible_without_foreground += np.count_nonzero(
            (captures[2]["tof_m"] != empty["tof_m"])
            | (captures[2]["tof_valid"] != empty["tof_valid"])
        )
        records.append(captures[1])
    assert visible_without_foreground > 0
    config = Config(**records[-1]["config"])
    ray = tof_directions(0, config)[1, 3]
    horizontal_speed = math.hypot(*ray[:2])
    direction = ray[:2] / horizontal_speed
    offset = np.asarray(foreground[:2]) - records[-1]["capture_poses_m_rad"][0, :2]
    along = float(offset @ direction)
    lateral = float(offset[0] * direction[1] - offset[1] * direction[0])
    expected = (along - math.sqrt(foreground[2] ** 2 - lateral**2)) / horizontal_speed
    assert 0 < config.tof_mount_height + expected * ray[2] < 0.5
    assert records[-1]["tof_valid"][0, 1, 3]
    assert records[-1]["tof_m"][0, 1, 3] == np.float32(expected)
    settings = {
        "reference_tick": 23,
        "reference_pose_m_rad": [2, 2, 0],
        "synthetic_test_only": True,
    }
    inspected = inspect_synthetic_c1_history(records, **settings)
    assert inspected["status"] == "registered_fixture"
    segments, _ = _c1_low_free_segments(records[-1], inspected, [2, 2, 0], config)
    assert len(segments) > 0
    for obstacle in (foreground, background):
        center = np.asarray(obstacle[:2]) - [2, 2]
        for start, end in segments[..., :2]:
            step = end - start
            fraction = np.clip(np.dot(center - start, step) / np.dot(step, step), 0, 1)
            assert np.linalg.norm(center - start - fraction * step) > obstacle[2]
    result = probe_synthetic_c1_enclosure(
        records,
        speed=0.6,
        current_body_clear=True,
        controlled_envelope=True,
        **settings,
    )
    assert result["status"] == "unknown"
    assert result["fixture_enclosure_excluded"] is False


def test_synthetic_c1_low_foreground_does_not_hide_tall_background(c1_history):
    from sim.diagnostics import capture_synthetic_c1_views

    foreground, background = (2.5, 2, 0.30), (3.2, 2, 0.30)
    scenes = (
        Scenario(start=(2, 2, 0), obstacles=(foreground,), obstacle_heights=(0.05,)),
        Scenario(
            start=(2, 2, 0),
            obstacles=(foreground, background),
            obstacle_heights=(0.05, 1.0),
        ),
        Scenario(start=(2, 2, 0), obstacles=(background,), obstacle_heights=(1.0,)),
    )
    for empty in c1_history:
        captures = [
            capture_synthetic_c1_views(
                scene,
                pose_m_rad=empty["capture_poses_m_rad"][0],
                capture_tick=int(empty["capture_ticks"][0]),
                synthetic_test_only=True,
            )
            for scene in scenes
        ]
        assert captures[1]["tof_valid"][0, 0, 3]
        assert captures[1]["tof_m"][0, 0, 3] == captures[2]["tof_m"][0, 0, 3]
        assert captures[0]["tof_m"][0, 0, 3] == empty["tof_m"][0, 0, 3]
        assert captures[1]["tof_m"][0, 0, 3] != captures[0]["tof_m"][0, 0, 3]


@pytest.mark.parametrize("speed", [0, 0.2, 0.6])
@pytest.mark.parametrize("turn", [-1.5, 0, 1.5])
@pytest.mark.parametrize("pieces", [4, 16])
@pytest.mark.parametrize("braking_turn", [-1.5, 0, 1.5])
def test_synthetic_c1_curved_centerline_encloses_independent_path(
    speed, turn, pieces, braking_turn
):
    from sim.diagnostics import _c1_curved_centerline

    config, age = Config(), 0.15
    points, error = _c1_curved_centerline(
        speed, turn, age, config, pieces, braking_turn
    )
    assert points.shape[1:] == (2,)
    assert 2 <= len(points) <= 2 * pieces + 1
    assert np.all(points[0] == 0)
    assert 0 < error < 0.01
    starts, steps = points[:-1], np.diff(points, axis=0)
    squared = np.sum(steps * steps, axis=1)
    nodes, weights = np.polynomial.legendre.leggauss(32)
    reaction, braking = age + config.dt, speed / config.acceleration
    for elapsed in np.linspace(0, reaction + braking, 129):
        reference = np.zeros(2)
        for duration, deceleration, angular_rate, initial_yaw in (
            (min(elapsed, reaction), 0, turn, 0),
            (
                max(0, elapsed - reaction),
                config.acceleration,
                braking_turn,
                turn * reaction,
            ),
        ):
            times = (nodes + 1) * duration / 2
            speeds = speed - deceleration * times
            headings = initial_yaw + angular_rate * times
            reference += (
                duration
                / 2
                * np.array(
                    [
                        np.dot(weights, speeds * np.cos(headings)),
                        np.dot(weights, speeds * np.sin(headings)),
                    ]
                )
            )
        relative = reference - starts
        fractions = np.divide(
            np.sum(relative * steps, axis=1),
            squared,
            out=np.zeros_like(squared),
            where=squared > 0,
        )
        residual = relative - np.clip(fractions, 0, 1)[:, None] * steps
        assert np.linalg.norm(residual, axis=1).min() <= error
        if elapsed == reaction + braking:
            assert np.linalg.norm(reference - points[-1]) <= error


@pytest.mark.parametrize("turn", [-1.5, 1.5])
@pytest.mark.parametrize("yaw", [0, 0.37, math.pi / 2, math.pi, -math.pi / 2])
@pytest.mark.parametrize("braking_turn", [-1.5, 0, 1.5])
def test_synthetic_c1_curved_tube_excludes_with_obstacle_behind(
    turn, yaw, braking_turn
):
    from sim.diagnostics import capture_synthetic_c1_views, probe_synthetic_c1_enclosure
    from sim.navigation import evaluate_synthetic

    center = np.array([2, 2]) - 0.6 * np.array([math.cos(yaw), math.sin(yaw)])
    scene = Scenario(start=(2, 2, yaw), goal=(5, 2), obstacles=((*center, 0.30),))
    acquired, acquired_yaw = integrate([2, 2], yaw, 0.6, turn, -0.15)
    assert not swept_collision(acquired, [2, 2], 0.18, scene.obstacles, scene.bounds)
    record = capture_synthetic_c1_views(
        scene,
        pose_m_rad=[*acquired, acquired_yaw],
        capture_tick=20,
        synthetic_test_only=True,
    )
    settings = {
        "reference_tick": 23,
        "reference_pose_m_rad": scene.start,
        "speed": 0.6,
        "current_body_clear": True,
        "controlled_envelope": True,
        "synthetic_test_only": True,
    }
    reference = evaluate_synthetic(
        scene, speed=0.6, turn_rate=turn, tof_age_s=0.15, synthetic_test_only=True
    )
    maneuver = reference["maneuvers"][
        {-1.5: "right", 0: "centre", 1.5: "left"}[braking_turn]
    ]
    assert maneuver["status"] == "clear"
    assert probe_synthetic_c1_enclosure([record], **settings)["status"] == "unknown"
    result = probe_synthetic_c1_enclosure(
        [record],
        turn_rate=turn,
        curved_segments=16,
        braking_turn_rate=braking_turn,
        **settings,
    )
    assert result["status"] == "excluded_under_fixture_assumptions", result
    assert result["schema"] == "micro-classifier/synthetic-c1-curved-enclosure/1"
    assert "sweep_enclosure_radius_m" not in result
    assert "straight_centerline_length_m" not in result
    assert result["centerline_error_allowance_m"] > 0
    assert result["curved_tube_radius_m"] > 0.18
    assert result["numerically_certified"] is False
    assert result["assumed_turn_rate_rad_s"] == turn
    assert result["assumed_braking_turn_rate_rad_s"] == braking_turn
    endpoint = np.array(result["curved_centerline_body_m"][-1]) @ np.array(
        [[math.cos(yaw), math.sin(yaw)], [-math.sin(yaw), math.cos(yaw)]]
    ) + np.array(scene.start[:2])
    assert math.dist(endpoint, maneuver["endpoint_m"]) <= (
        result["centerline_error_allowance_m"] + maneuver["endpoint_error_bound_m"]
    )
    if braking_turn == 0:
        assert result == probe_synthetic_c1_enclosure(
            [record], turn_rate=turn, curved_segments=16, **settings
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("curved_segments", True),
        ("curved_segments", -1),
        ("curved_segments", 129),
        ("curved_segments", 16.0),
        ("curved_segments", "16"),
        ("curved_segments", np.inf),
        ("curved_segments", 10**400),
        ("curved_segments", 0),
        ("turn_rate", None),
        ("braking_turn_rate", True),
        ("braking_turn_rate", np.nan),
        ("braking_turn_rate", np.inf),
        ("braking_turn_rate", 1.50001),
        ("braking_turn_rate", -1.50001),
        ("braking_turn_rate", "0"),
        ("braking_turn_rate", 10**400),
    ],
)
def test_synthetic_c1_curved_tube_rejects_malformed_controls(c1_history, field, value):
    from sim.diagnostics import probe_synthetic_c1_enclosure

    settings = {
        "reference_tick": 23,
        "reference_pose_m_rad": [2, 2, 0],
        "speed": 0.6,
        "turn_rate": 1.5,
        "curved_segments": 16,
        "braking_turn_rate": 0.0,
        "synthetic_test_only": True,
        field: value,
    }
    with pytest.raises(ValueError):
        probe_synthetic_c1_enclosure(c1_history, **settings)


@pytest.mark.parametrize("pieces", [1, 128])
def test_synthetic_c1_curved_tube_keeps_exhausted_budget_unknown(c1_history, pieces):
    from sim.diagnostics import probe_synthetic_c1_enclosure

    result = probe_synthetic_c1_enclosure(
        c1_history,
        reference_tick=23,
        reference_pose_m_rad=[2, 2, 0],
        speed=0.6,
        turn_rate=1.5,
        curved_segments=pieces,
        current_body_clear=True,
        controlled_envelope=True,
        max_cells=0,
        synthetic_test_only=True,
    )
    assert result["status"] == "unknown"
    assert result["reason"] == "cell_budget_exhausted"
    assert result["fixture_enclosure_excluded"] is False


@pytest.mark.parametrize("turn", [-1.5, 0, 1.5])
@pytest.mark.parametrize("braking_turn", [-1.5, 0, 1.5])
@pytest.mark.parametrize("yaw", [0, 0.37])
def test_synthetic_c1_occupied_witness_supports_visible_blockage(
    turn, braking_turn, yaw
):
    from sim.diagnostics import (
        capture_synthetic_c1_views,
        probe_synthetic_c1_occupied_witness,
    )
    from sim.navigation import evaluate_synthetic

    forward = np.array([math.cos(yaw), math.sin(yaw)])
    center = np.array([2, 2]) + 0.6 * forward
    scene = Scenario(
        start=(2, 2, yaw),
        goal=(5, 2),
        obstacles=((*center, 0.30),),
        obstacle_heights=(0.05 if braking_turn == 0 else 1.0,),
    )
    record = capture_synthetic_c1_views(
        scene,
        pose_m_rad=[*(np.array([2, 2]) - 0.09 * forward), yaw],
        capture_tick=20,
        synthetic_test_only=True,
    )
    reference = evaluate_synthetic(
        scene, speed=0.6, turn_rate=turn, tof_age_s=0.15, synthetic_test_only=True
    )
    assert (
        reference["maneuvers"][{-1.5: "right", 0: "centre", 1.5: "left"}[braking_turn]][
            "status"
        ]
        == "blocked"
    )
    result = probe_synthetic_c1_occupied_witness(
        [record],
        reference_tick=23,
        reference_pose_m_rad=scene.start,
        speed=0.6,
        turn_rate=turn,
        braking_turn_rate=braking_turn,
        controlled_envelope=True,
        synthetic_test_only=True,
    )
    assert result["status"] == "blocked_under_fixture_assumptions", result
    assert result["fixture_blocked_witness"] is True
    assert result["fixture_current_body_witness"] is False
    assert result["witness_indices"]
    assert result["occupied_point_error_upper_m"] > 0
    for field in (
        "training_approved",
        "real_input_qualified",
        "free_space_qualified",
        "numerically_certified",
    ):
        assert result[field] is False


@pytest.mark.parametrize("keep_floor", [False, True])
def test_synthetic_c1_occupied_witness_rejects_rounded_floor_and_missing(keep_floor):
    from sim.diagnostics import (
        capture_synthetic_c1_views,
        inspect_synthetic_c1_history,
        probe_synthetic_c1_occupied_witness,
    )

    scene = Scenario(start=(2, 2, 0), goal=(5, 2))
    record = capture_synthetic_c1_views(
        scene, pose_m_rad=[1.91, 2, 0], capture_tick=20, synthetic_test_only=True
    )
    settings = {
        "reference_tick": 23,
        "reference_pose_m_rad": scene.start,
        "synthetic_test_only": True,
    }
    inspection = inspect_synthetic_c1_history([record], **settings)
    points = inspection["points_body_m"]
    floor = (
        record["tof_valid"]
        & (points[..., 2] > 0)
        & (points[..., 2] < 1e-6)
        & (np.linalg.norm(points[..., :2], axis=-1) < 0.17)
    )
    assert np.any(floor)
    record["tof_valid"] = floor if keep_floor else np.zeros_like(floor)
    record["tof_m"][~record["tof_valid"]] = 0
    result = probe_synthetic_c1_occupied_witness(
        [record], speed=0.6, turn_rate=0, controlled_envelope=True, **settings
    )
    assert result["status"] == "unknown"
    assert result["fixture_blocked_witness"] is False
    assert not result["witness_indices"]
    assert result.get("occupied_return_count", 0) == 0
    if keep_floor:
        assert result["reason"] == "no_qualified_occupied_returns"


@pytest.mark.parametrize(
    "field,value,reason",
    [
        ("controlled_envelope", False, "controlled_envelope_not_established"),
        ("controlled_envelope", 1, "controlled_envelope_not_established"),
        ("reference_tick", 24, "stale_capture"),
        ("reference_pose_m_rad", [3, 2, 0], "unsupported_capture_to_reference_motion"),
        ("history", [], "unsupported_history"),
        ("synthetic_test_only", False, None),
        ("reference_tick", True, None),
        ("curved_segments", 0, None),
        ("curved_segments", True, None),
        ("curved_segments", 129, None),
        ("speed", -0.01, None),
        ("speed", 0.61, None),
        ("turn_rate", True, None),
        ("turn_rate", np.inf, None),
        ("turn_rate", 1.50001, None),
        ("braking_turn_rate", None, None),
        ("braking_turn_rate", 10**400, None),
    ],
)
def test_synthetic_c1_occupied_witness_rejects_unsupported_evidence(
    field, value, reason
):
    from sim.diagnostics import (
        capture_synthetic_c1_views,
        probe_synthetic_c1_occupied_witness,
    )

    scene = Scenario(start=(2, 2, 0), goal=(5, 2), obstacles=((2.6, 2, 0.30),))
    record = capture_synthetic_c1_views(
        scene, pose_m_rad=[1.91, 2, 0], capture_tick=20, synthetic_test_only=True
    )
    settings = {
        "history": [record],
        "reference_tick": 23,
        "reference_pose_m_rad": scene.start,
        "speed": 0.6,
        "turn_rate": 0,
        "controlled_envelope": True,
        "synthetic_test_only": True,
        field: value,
    }
    if reason is None:
        with pytest.raises(ValueError):
            probe_synthetic_c1_occupied_witness(**settings)
    else:
        result = probe_synthetic_c1_occupied_witness(**settings)
        assert result["status"] == "unknown"
        assert result["reason"] == reason
        assert result["fixture_blocked_witness"] is False


@pytest.mark.parametrize("blocked", [False, True])
@pytest.mark.parametrize("goal", [(5, 2), (2, 5), (2, 0.5), (0.5, 2)])
def test_synthetic_c1_question_feasibility_matches_resolved_fixture(blocked, goal):
    from sim.diagnostics import capture_synthetic_c1_views, probe_synthetic_c1_questions
    from sim.navigation import evaluate_synthetic

    scene = Scenario(
        start=(2, 2, 0), goal=goal, obstacles=((2.6, 2, 0.30),) if blocked else ()
    )
    record = capture_synthetic_c1_views(
        scene, pose_m_rad=[1.91, 2, 0], capture_tick=20, synthetic_test_only=True
    )
    result = probe_synthetic_c1_questions(
        [record],
        reference_tick=23,
        reference_pose_m_rad=scene.start,
        speed=0.6,
        turn_rate=0,
        fixture_goal_m=scene.goal,
        current_body_clear=True,
        controlled_envelope=True,
        synthetic_test_only=True,
    )
    expected = evaluate_synthetic(
        scene, speed=0.6, tof_age_s=0.15, synthetic_test_only=True
    )["answers"]
    assert result["status"] == "resolved_under_fixture_assumptions", result
    assert result["candidate_values"] == {
        name: expected[name] for name in ("path_blocked", "clear_sector", "speed_tier")
    }
    assert len(result["queries"]) == 6
    assert result["unique_motion_queries"] == 3
    assert "mode" not in result["candidate_values"]
    assert result["training_approved"] is False
    result["queries"]["centre"]["witness"]["witness_indices"].append([7, 7, 7])
    assert [7, 7, 7] not in result["queries"]["tier_3"]["witness"]["witness_indices"]


def test_synthetic_c1_question_feasibility_keeps_momentum_capacity():
    from sim.diagnostics import capture_synthetic_c1_views, probe_synthetic_c1_questions
    from sim.navigation import evaluate_synthetic

    scene = Scenario(start=(2, 2, 0), goal=(5, 2), obstacles=((2.7, 2, 0.30),))
    record = capture_synthetic_c1_views(
        scene, pose_m_rad=[1.97, 2, 0], capture_tick=20, synthetic_test_only=True
    )
    result = probe_synthetic_c1_questions(
        [record],
        reference_tick=23,
        reference_pose_m_rad=scene.start,
        speed=0.2,
        turn_rate=0,
        fixture_goal_m=scene.goal,
        current_body_clear=True,
        controlled_envelope=True,
        synthetic_test_only=True,
    )
    reference = evaluate_synthetic(
        scene, speed=0.2, tof_age_s=0.15, synthetic_test_only=True
    )["answers"]
    assert reference["speed_tier"] == "2"
    assert result["candidate_values"] == {
        name: reference[name] for name in ("path_blocked", "clear_sector", "speed_tier")
    }
    assert result["unique_motion_queries"] == 5
    assert [
        result["queries"][f"tier_{tier}"]["speed_m_s"] for tier in (1, 2, 3)
    ] == pytest.approx([0.2, 0.4, 0.6])


@pytest.mark.parametrize(
    "case", ["rest", "zero_cells", "missing_domain", "missing_body", "stale"]
)
def test_synthetic_c1_question_feasibility_preserves_abstention(c1_history, case):
    from sim.diagnostics import probe_synthetic_c1_questions

    settings = {
        "reference_tick": 23,
        "reference_pose_m_rad": [2, 2, 0],
        "speed": 0.6,
        "turn_rate": 0,
        "fixture_goal_m": [5, 2],
        "current_body_clear": True,
        "controlled_envelope": True,
        "synthetic_test_only": True,
    }
    if case == "rest":
        settings["speed"] = 0
    elif case == "zero_cells":
        settings["max_cells"] = 0
    elif case == "missing_domain":
        settings["controlled_envelope"] = False
    elif case == "missing_body":
        settings["current_body_clear"] = 1
    else:
        settings["reference_tick"] = 24
    result = probe_synthetic_c1_questions(c1_history, **settings)
    if case == "rest":
        assert result["candidate_values"] == {
            "path_blocked": "false",
            "clear_sector": None,
            "speed_tier": "3",
        }
    else:
        assert all(value is None for value in result["candidate_values"].values())
        assert result["status"] == "unknown"


@pytest.mark.parametrize("unknown", ["sector", "tier"])
def test_synthetic_c1_question_feasibility_does_not_rank_unknowns(
    c1_history, monkeypatch, unknown
):
    from sim import diagnostics

    def state(settings):
        if unknown == "sector":
            return "unknown" if settings["braking_turn_rate"] > 0 else "blocked"
        if 0.3 < settings["speed"] < 0.5:
            return "unknown"
        return "blocked" if settings["speed"] > 0.5 else "clear"

    monkeypatch.setattr(
        diagnostics,
        "probe_synthetic_c1_enclosure",
        lambda history, **settings: {
            "fixture_enclosure_excluded": state(settings) == "clear"
        },
    )
    monkeypatch.setattr(
        diagnostics,
        "probe_synthetic_c1_occupied_witness",
        lambda history, **settings: {
            "fixture_blocked_witness": state(settings) == "blocked",
            "fixture_current_body_witness": False,
        },
    )
    result = diagnostics.probe_synthetic_c1_questions(
        c1_history,
        reference_tick=23,
        reference_pose_m_rad=[2, 2, 0],
        speed=0.2,
        turn_rate=0,
        fixture_goal_m=[5, 2],
        current_body_clear=True,
        controlled_envelope=True,
        synthetic_test_only=True,
    )
    if unknown == "sector":
        assert result["candidate_values"] == {
            "path_blocked": "true",
            "clear_sector": None,
            "speed_tier": "0",
        }
    else:
        assert result["candidate_values"] == {
            "path_blocked": "false",
            "clear_sector": "centre",
            "speed_tier": None,
        }


@pytest.mark.parametrize("current_body", [False, True])
def test_synthetic_c1_question_feasibility_rejects_conflicts(
    c1_history, monkeypatch, current_body
):
    from sim import diagnostics

    monkeypatch.setattr(
        diagnostics,
        "probe_synthetic_c1_enclosure",
        lambda *args, **kwargs: {"fixture_enclosure_excluded": not current_body},
    )
    monkeypatch.setattr(
        diagnostics,
        "probe_synthetic_c1_occupied_witness",
        lambda *args, **kwargs: {
            "fixture_blocked_witness": True,
            "fixture_current_body_witness": current_body,
        },
    )
    result = diagnostics.probe_synthetic_c1_questions(
        c1_history,
        reference_tick=23,
        reference_pose_m_rad=[2, 2, 0],
        speed=0.6,
        turn_rate=0,
        fixture_goal_m=[5, 2],
        current_body_clear=True,
        controlled_envelope=True,
        synthetic_test_only=True,
    )
    assert result["status"] == "inconsistent_fixture_evidence"
    assert all(value is None for value in result["candidate_values"].values())


def test_synthetic_c1_question_feasibility_keeps_near_tie_unknown(c1_history):
    from sim.diagnostics import probe_synthetic_c1_questions
    from sim.navigation import evaluate_synthetic

    goal = (0.5, 2 + 1e-12)
    scene = Scenario(start=(2, 2, 0), goal=goal)
    assert (
        evaluate_synthetic(scene, speed=0.6, tof_age_s=0.15, synthetic_test_only=True)[
            "answers"
        ]["clear_sector"]
        is None
    )
    result = probe_synthetic_c1_questions(
        c1_history,
        reference_tick=23,
        reference_pose_m_rad=scene.start,
        speed=0.6,
        turn_rate=0,
        fixture_goal_m=goal,
        current_body_clear=True,
        controlled_envelope=True,
        synthetic_test_only=True,
    )
    assert result["candidate_values"] == {
        "path_blocked": "false",
        "clear_sector": None,
        "speed_tier": "3",
    }


def test_synthetic_c1_question_feasibility_detects_current_body_conflict():
    from sim.diagnostics import capture_synthetic_c1_views, probe_synthetic_c1_questions

    scene = Scenario(start=(1, 1, 0), goal=(5, 2), obstacles=((2.4, 2, 0.30),))
    record = capture_synthetic_c1_views(
        scene, pose_m_rad=[1.91, 2, 0], capture_tick=20, synthetic_test_only=True
    )
    result = probe_synthetic_c1_questions(
        [record],
        reference_tick=23,
        reference_pose_m_rad=[2, 2, 0],
        speed=0.6,
        turn_rate=0,
        fixture_goal_m=scene.goal,
        current_body_clear=True,
        controlled_envelope=True,
        synthetic_test_only=True,
    )
    assert (
        result["queries"]["centre"]["witness"]["fixture_current_body_witness"] is True
    )
    assert result["status"] == "inconsistent_fixture_evidence"
    assert all(value is None for value in result["candidate_values"].values())


@pytest.mark.parametrize(
    "field,value",
    [
        ("fixture_goal_m", [True, 2]),
        ("fixture_goal_m", [np.inf, 2]),
        ("fixture_goal_m", [2]),
        ("curved_segments", True),
        ("curved_segments", 0),
        ("max_cells", 65537),
        ("radius_bands", 0),
        ("speed", True),
        ("turn_rate", np.inf),
        ("synthetic_test_only", False),
    ],
)
def test_synthetic_c1_question_feasibility_rejects_malformed_controls(
    c1_history, field, value
):
    from sim.diagnostics import probe_synthetic_c1_questions

    settings = {
        "reference_tick": 23,
        "reference_pose_m_rad": [2, 2, 0],
        "speed": 0.6,
        "turn_rate": 0,
        "fixture_goal_m": [5, 2],
        "current_body_clear": True,
        "controlled_envelope": True,
        "synthetic_test_only": True,
        field: value,
    }
    with pytest.raises(ValueError):
        probe_synthetic_c1_questions(c1_history, **settings)


@pytest.mark.parametrize(
    "case", ["stale", "future", "reversal", "profile", "reset", "early_delivery"]
)
def test_synthetic_c1_relative_temporal_compatibility(c1_history, case):
    from interface.protocol import State
    from sim.diagnostics import (
        prepare_synthetic_c1_relative_input,
        probe_synthetic_c1_questions,
        probe_synthetic_c1_relative_questions,
    )

    history = deepcopy(c1_history)
    tick = 24 if case == "stale" else 19 if case == "reset" else 23
    if case == "future":
        history[-1]["capture_ticks"][:] = 24
    elif case == "reversal":
        history = [deepcopy(history[-1]), history[-1]]
        history[-1]["capture_ticks"][:] = 19
    elif case == "profile":
        history[-1]["config"]["tof_mount_pitch"] = 0
    elif case == "early_delivery":
        history = [deepcopy(history[-1]), deepcopy(history[-1]), history[-1]]
    old = probe_synthetic_c1_questions(
        history,
        reference_tick=tick,
        reference_pose_m_rad=[2, 2, 0],
        fixture_goal_m=[5, 2],
        speed=0.6,
        turn_rate=0,
        current_body_clear=True,
        controlled_envelope=True,
        synthetic_test_only=True,
    )
    relative = prepare_synthetic_c1_relative_input(
        history,
        reference_tick=tick,
        reference_pose_m_rad=[2, 2, 0],
        fixture_goal_m=[5, 2],
        synthetic_test_only=True,
    )
    result = probe_synthetic_c1_relative_questions(
        relative,
        fixture_state=State(
            timestamp_us=tick * 50000, velocity_m_s=(0.6, 0, 0), goal_m=(3, 0, 0)
        ),
        fixture_current_body_clear=True,
        fixture_controlled_envelope=True,
        synthetic_test_only=True,
    )
    assert result["candidate_values"] == old["candidate_values"]
    assert result["status"] == old["status"] == "unknown"
    assert result["reason"] == old["reason"]
    assert result["queries"] == {}


@pytest.mark.parametrize(
    "field,value",
    [
        ("synthetic_test_only", False),
        ("fixture_goal_m", [True, 2]),
        ("fixture_goal_m", [np.inf, 2]),
        ("reference_tick", True),
    ],
)
def test_synthetic_c1_relative_input_rejects_malformed(c1_history, field, value):
    from sim.diagnostics import prepare_synthetic_c1_relative_input

    settings = {
        "reference_tick": 23,
        "reference_pose_m_rad": [2, 2, 0],
        "fixture_goal_m": [5, 2],
        "synthetic_test_only": True,
        field: value,
    }
    with pytest.raises(ValueError):
        prepare_synthetic_c1_relative_input(c1_history, **settings)


@pytest.fixture(scope="module")
def c1_wire_fixtures(request):
    from dataclasses import asdict

    from interface.protocol import State
    from sim import diagnostics

    fixtures = {
        "inputs": {},
        "scene_records": set(),
        "cases": 0,
        "adapter_attempts": 0,
        "relative_attempts": 0,
        "coordinator_attempts": 0,
        "capture_attempts": 0,
        "source_state": State(
            sequence=23,
            timestamp_us=1150000,
            velocity_m_s=(0.5, 0, 0),
            goal_m=(3, 0, 0),
        ),
    }
    for blocked in (False, True):
        scene = Scenario(
            start=(2, 2, 0),
            goal=(5, 2),
            obstacles=((2.6, 2, 0.30),) if blocked else (),
        )
        fixtures["scene_records"].add(json.dumps(asdict(scene), sort_keys=True))
        assert len(fixtures["scene_records"]) <= 8
        fixtures["capture_attempts"] += 1
        record = diagnostics.capture_synthetic_c1_views(
            scene,
            pose_m_rad=[1.91, 2, 0],
            capture_tick=20,
            synthetic_test_only=True,
        )
        fixtures["inputs"][blocked] = diagnostics.prepare_synthetic_c1_relative_input(
            [record],
            reference_tick=23,
            reference_pose_m_rad=scene.start,
            fixture_goal_m=scene.goal,
            synthetic_test_only=True,
        )
    yield fixtures
    assert fixtures["adapter_attempts"] == 2 * fixtures["cases"] <= 48
    assert fixtures["coordinator_attempts"] <= 48
    assert fixtures["capture_attempts"] == len(fixtures["scene_records"]) == 2
    message = (
        "C1 wire ledger: "
        f"cases={fixtures['cases']} "
        f"adapter={fixtures['adapter_attempts']} "
        f"relative={fixtures['relative_attempts']} "
        f"coordinator={fixtures['coordinator_attempts']} "
        f"captures={fixtures['capture_attempts']} "
        f"scenes={len(fixtures['scene_records'])}"
    )
    capture = request.config.pluginmanager.getplugin("capturemanager")
    if capture is None:
        print(message)
    else:
        with capture.global_and_fixture_disabled():
            print(message)


@pytest.mark.parametrize(
    "case",
    range(24),
    ids=(
        "rounding-before-query",
        "exact-clear",
        "exact-blocked",
        "rest-is-partial",
        "stale-host",
        "missing-host-group",
        "frame-binding",
        "bad-crc",
        "bad-profile",
        "non-bytes",
        "strict-opt-in",
        "body-unknown",
        "domain-unknown",
        "transform-unknown",
        "goal-binding",
        "stale-capture",
        "missing-returns",
        "work-exhaustion",
        "conflict-summary",
        "partial-summary",
        "invalid-summary",
        "computation-fault",
        "false-qualification",
        "held-owned-output",
    ),
)
def test_synthetic_c1_wire_rejection(c1_wire_fixtures, monkeypatch, case):
    import zlib
    from dataclasses import replace

    from interface.protocol import (
        CRC,
        RULES_QUESTIONS,
        FrameDecoder,
        Status,
        decode_decision,
        decode_state,
        encode_state,
    )
    from sim import diagnostics
    from sim.rules import host_action

    fixtures = c1_wire_fixtures
    fixtures["cases"] += 1
    assert fixtures["cases"] <= 24
    relative = deepcopy(fixtures["inputs"][case == 2])
    source = fixtures["source_state"]
    settings = {"fixture_current_body_clear": True, "fixture_controlled_envelope": True}
    expected_status = Status.REJECT_OUT_OF_DOMAIN
    expected_candidates = None
    expected_reason = "unqualified_fixture_evidence"
    expected_queries = case in (1, 2, 3, 17, 23)
    if case == 0:
        source = replace(source, velocity_m_s=(0.6, 0, 0))
        expected_reason = "decoded_fixture_state_changed"
    elif case == 1 or case == 23:
        expected_candidates = ("false", "centre", "3")
    elif case == 2:
        expected_candidates = ("true", "none", "0")
    elif case == 3:
        source = replace(source, velocity_m_s=(0, 0, 0))
    elif case == 4:
        source = replace(source, ages_us=(50000, *source.ages_us[1:]))
        expected_status = Status.REJECT_STALE_INPUT
        expected_reason = "stale_fixture_host_state"
    elif case == 5:
        source = replace(
            source,
            validity=6,
            velocity_m_s=(0, 0, 0),
            ages_us=(0xFFFFFFFF, *source.ages_us[1:]),
        )
        expected_reason = "unsupported_fixture_host_validity"
    elif case in (7, 8, 9):
        expected_status = Status.REJECT_UNSUPPORTED_SCHEMA
        expected_reason = (
            "unsupported_fixture_state_frame"
            if case == 9
            else "invalid_fixture_state_frame"
        )
    elif case == 11:
        settings["fixture_current_body_clear"] = False
    elif case == 12:
        settings["fixture_controlled_envelope"] = False
    elif case == 13:
        settings["fixture_transform_error_m"] = 0.001
    elif case == 14:
        relative["fixture_goal_body_m"] = [3.25, 0]
    elif case == 15:
        relative["reference_tick"] = 24
        source = replace(source, timestamp_us=1200000)
        expected_status = Status.REJECT_STALE_INPUT
        expected_reason = "stale_fixture_capture"
    elif case == 16:
        relative["history"][0]["tof_valid"][:] = False
        relative["history"][0]["tof_m"][:] = 0
    elif case == 17:
        settings["max_cells"] = 0
    elif case == 18:
        expected_reason = "inconsistent_fixture_evidence"
    elif case == 19:
        expected_candidates = ("false", None, "2")
    elif case in (20, 22):
        expected_status = Status.FAULT
        expected_reason = "unsupported_fixture_question_result"
    elif case == 21:
        expected_status = Status.FAULT
        expected_reason = "fixture_question_computation_failed"

    frame = encode_state(source)
    if case == 0:
        assert decode_state(frame).velocity_m_s[0] > source.velocity_m_s[0]
    if case == 6:
        frame = encode_state(replace(source, sequence=24))
        expected_reason = "fixture_state_frame_binding_mismatch"
    elif case == 7:
        frame = frame[:25] + bytes([frame[25] ^ 1]) + frame[26:]
    elif case == 8:
        payload = bytearray(frame[:-4])
        payload[8] ^= 1
        frame = bytes(payload) + CRC.pack(zlib.crc32(payload))
    elif case == 9:
        frame = bytearray(frame)
    elif case == 23:
        relative["history"].append(deepcopy(relative["history"][0]))

    original_relative = diagnostics.probe_synthetic_c1_relative_questions
    original_coordinator = diagnostics.probe_synthetic_c1_questions
    before_queries = fixtures["coordinator_attempts"]

    def coordinator(*args, **kwargs):
        fixtures["coordinator_attempts"] += 1
        assert fixtures["coordinator_attempts"] <= 48
        return original_coordinator(*args, **kwargs)

    def relative_questions(*args, **kwargs):
        fixtures["relative_attempts"] += 1
        assert kwargs["fixture_state"] == decode_state(frame)
        if case == 21:
            raise RuntimeError("injected fixture computation failure")
        if 18 <= case <= 22:
            report = {
                "schema": "micro-classifier/synthetic-c1-relative-questions/1",
                "allowed_use": "controlled_synthetic_qualification_only",
                "training_approved": False,
                "real_input_qualified": False,
                "free_space_qualified": False,
                "numerically_certified": False,
                "status": "resolved_under_fixture_assumptions",
                "reason": "fake_fixture_summary_only",
                "candidate_values": {
                    "path_blocked": "false",
                    "clear_sector": "centre",
                    "speed_tier": "3",
                },
                "queries": {},
                "unique_motion_queries": 0,
            }
            if case == 18:
                report["status"] = "inconsistent_fixture_evidence"
            elif case == 19:
                report["status"] = "partial_fixture_evidence"
                report["candidate_values"] = {
                    "path_blocked": "false",
                    "clear_sector": None,
                    "speed_tier": "2",
                }
            elif case == 20:
                report["candidate_values"]["path_blocked"] = 0
            elif case == 22:
                report["real_input_qualified"] = 0
            return report
        return original_relative(*args, **kwargs)

    monkeypatch.setattr(diagnostics, "probe_synthetic_c1_questions", coordinator)
    monkeypatch.setattr(
        diagnostics, "probe_synthetic_c1_relative_questions", relative_questions
    )
    outputs = []
    for request in range(2):
        fixtures["adapter_attempts"] += 1
        assert fixtures["adapter_attempts"] <= 48
        if case == 10:
            with pytest.raises(ValueError, match="synthetic_test_only"):
                diagnostics._probe_synthetic_c1_wire_rejection(
                    relative,
                    fixture_state_frame=frame,
                    fixture_source_state=source,
                    synthetic_test_only=False if request == 0 else 1,
                    **settings,
                )
            continue
        result = diagnostics._probe_synthetic_c1_wire_rejection(
            relative,
            fixture_state_frame=frame,
            fixture_source_state=source,
            synthetic_test_only=True,
            **settings,
        )
        decision = decode_decision(result["decision_frame"])
        assert result["status"] == "rejection_diagnostics_only"
        assert result["reason"] == expected_reason
        assert decision.status == expected_status != Status.OK
        assert (decision.catalogue_version, decision.model_version) == (1, 0)
        for flag in (
            "training_approved",
            "real_input_qualified",
            "free_space_qualified",
            "numerically_certified",
            "source_input_qualified",
            "host_command_admitted",
        ):
            assert result[flag] is False
        if expected_candidates is not None:
            assert tuple(result["candidate_values"].values()) == expected_candidates
        if case == 3:
            assert result["candidate_values"]["clear_sector"] is None
        if case in (0, 4, 5, 6, 7, 8, 9, 18, 20, 21, 22):
            assert decision.answers == ()
        names = {
            question.name.lower(): (question, options)
            for question, (_, options) in RULES_QUESTIONS.items()
        }
        for name, value in result["candidate_values"].items():
            question, options = names[name]
            answers = [
                answer for answer in decision.answers if answer.question_id == question
            ]
            if value is None:
                assert not answers
            else:
                assert len(answers) == 1
                assert answers[0].selected == options.index(value)
                assert answers[0].probabilities == tuple(
                    float(option == value) for option in options
                )
        decoder = FrameDecoder()
        split = len(result["decision_frame"]) // 2
        assert decoder.feed(result["decision_frame"][:split]) == []
        assert decoder.feed(result["decision_frame"][split:]) == [decision]
        assert np.array_equal(
            host_action(encode_state(source), result["decision_frame"]), np.zeros(2)
        )
        assert np.array_equal(host_action(encode_state(source), None), np.zeros(2))
        if result["evidence"] is not None:
            assert result["evidence"]["unique_motion_queries"] <= 6
        outputs.append(result)
        if case == 23 and request == 0:
            result["candidate_values"]["path_blocked"] = "true"
            result["evidence"]["candidate_values"]["path_blocked"] = "true"
    assert fixtures["coordinator_attempts"] - before_queries == (
        2 if expected_queries else 0
    )
    if outputs and case != 23:
        assert outputs[0] == outputs[1]
    if case == 23:
        assert outputs[1]["candidate_values"]["path_blocked"] == "false"
        assert decode_decision(outputs[0]["decision_frame"]) == decode_decision(
            outputs[1]["decision_frame"]
        )


def test_synthetic_c1_relative_input_preserves_boundary(c1_history):
    from sim.diagnostics import prepare_synthetic_c1_relative_input

    relative = prepare_synthetic_c1_relative_input(
        c1_history,
        reference_tick=23,
        reference_pose_m_rad=[2, 2, 0],
        fixture_goal_m=[5, 2],
        synthetic_test_only=True,
    )
    assert relative["status"] == "relative_fixture"
    assert relative["fixture_goal_body_m"] == [3, 0]
    assert relative["numerical_source_scale"] == 5
    assert relative["fixture_arena_yaw_rad"] == 0
    assert "reference_pose_m_rad" not in relative
    for original, converted in zip(c1_history, relative["history"], strict=True):
        assert np.array_equal(converted["tof_m"], original["tof_m"])
        assert not np.shares_memory(converted["tof_valid"], original["tof_valid"])
        assert "capture_poses_m_rad" not in converted
        assert converted["capture_poses_body_m_rad"][0, :2] == pytest.approx(
            original["capture_poses_m_rad"][0, :2] - [2, 2]
        )


@pytest.mark.parametrize("blocked", [False, True])
@pytest.mark.parametrize("goal", [(5, 2), (2, 5), (2, 0.5), (0.5, 2)])
@pytest.mark.parametrize("frame", [0, math.pi / 2])
def test_synthetic_c1_relative_questions_match_existing_input(blocked, goal, frame):
    from interface.protocol import State
    from sim.diagnostics import (
        capture_synthetic_c1_views,
        prepare_synthetic_c1_relative_input,
        probe_synthetic_c1_questions,
        probe_synthetic_c1_relative_questions,
    )

    scene = Scenario(
        start=(2, 2, 0), goal=goal, obstacles=((2.6, 2, 0.30),) if blocked else ()
    )
    record = capture_synthetic_c1_views(
        scene,
        pose_m_rad=[1.91, 2, 0],
        capture_tick=20,
        synthetic_test_only=True,
    )
    rotation = np.array(
        [[math.cos(frame), math.sin(frame)], [-math.sin(frame), math.cos(frame)]]
    )
    shift = np.array([8, -4]) if frame else np.zeros(2)
    reference = [*(np.array(scene.start[:2]) @ rotation + shift), frame]
    world_goal = np.array(goal) @ rotation + shift
    record["capture_poses_m_rad"][:, :2] = (
        record["capture_poses_m_rad"][:, :2] @ rotation + shift
    )
    record["capture_poses_m_rad"][:, 2] += frame
    history = [record]
    relative = prepare_synthetic_c1_relative_input(
        history,
        reference_tick=23,
        reference_pose_m_rad=reference,
        fixture_goal_m=world_goal,
        synthetic_test_only=True,
    )
    old = probe_synthetic_c1_questions(
        history,
        reference_tick=23,
        reference_pose_m_rad=reference,
        fixture_goal_m=world_goal,
        speed=0.6,
        turn_rate=0,
        current_body_clear=True,
        controlled_envelope=True,
        synthetic_test_only=True,
    )
    result = probe_synthetic_c1_relative_questions(
        relative,
        fixture_state=State(
            timestamp_us=1150000,
            velocity_m_s=(0.6, 0, 0),
            goal_m=(*relative["fixture_goal_body_m"], 0),
        ),
        fixture_current_body_clear=True,
        fixture_controlled_envelope=True,
        synthetic_test_only=True,
    )
    assert result["candidate_values"] == old["candidate_values"]
    assert result["status"] == old["status"]
    if frame == 0:
        assert result["status"] == "resolved_under_fixture_assumptions"
    assert result["canonical_guard_scale"] >= 4 * result["numerical_source_scale"]
    assert result["unique_motion_queries"] == old["unique_motion_queries"] == 3


@pytest.mark.parametrize("side", [-1, 1])
@pytest.mark.parametrize("radius", [0.05, 0.30])
def test_synthetic_c1_coarse_curve_preserves_off_polyline_collision(side, radius):
    from sim.diagnostics import (
        _c1_curved_centerline,
        capture_synthetic_c1_views,
        probe_synthetic_c1_enclosure,
    )
    from sim.navigation import evaluate_synthetic

    config, speed, age, pieces = Config(), 0.6, 0.15, 1
    turn = side * config.max_turn_rate
    points, error = _c1_curved_centerline(speed, turn, age, config, pieces, turn)
    nodes, weights = np.polynomial.legendre.leggauss(32)
    times = (nodes + 1) * speed / (2 * config.acceleration)
    speeds = speed - config.acceleration * times
    headings = turn * (age + config.dt + times)
    reaction_end, _ = integrate([0, 0], 0, speed, turn, age + config.dt)
    endpoint = reaction_end + speed / (2 * config.acceleration) * np.array(
        [
            np.dot(weights, speeds * np.cos(headings)),
            np.dot(weights, speeds * np.sin(headings)),
        ]
    )
    starts, steps = points[:-1], np.diff(points, axis=0)
    squared = np.sum(steps * steps, axis=1)
    fractions = np.clip(np.sum((endpoint - starts) * steps, axis=1) / squared, 0, 1)
    closest = starts + fractions[:, None] * steps
    nearest = closest[np.linalg.norm(endpoint - closest, axis=1).argmin()]
    outward = (endpoint - nearest) / np.linalg.norm(endpoint - nearest)
    center = endpoint + outward * (config.radius + radius - 0.001)
    fractions = np.clip(np.sum((center - starts) * steps, axis=1) / squared, 0, 1)
    separation = np.linalg.norm(
        center - starts - fractions[:, None] * steps, axis=1
    ).min()
    assert separation > config.radius + radius
    assert separation < config.radius + radius + error
    assert np.linalg.norm(center) > config.radius + radius
    scene = Scenario(
        start=(2, 2, 0),
        goal=(5, 2),
        obstacles=((*(center + [2, 2]), radius),),
        obstacle_heights=(0.05,),
    )
    reference = evaluate_synthetic(
        scene, speed=speed, turn_rate=turn, tof_age_s=age, synthetic_test_only=True
    )
    assert (
        reference["maneuvers"]["left" if side > 0 else "right"]["status"] == "blocked"
    )
    acquired, acquired_yaw = integrate([2, 2], 0, speed, turn, -age)
    record = capture_synthetic_c1_views(
        scene,
        pose_m_rad=[*acquired, acquired_yaw],
        capture_tick=20,
        synthetic_test_only=True,
    )
    result = probe_synthetic_c1_enclosure(
        [record],
        reference_tick=23,
        reference_pose_m_rad=scene.start,
        speed=speed,
        turn_rate=turn,
        braking_turn_rate=turn,
        curved_segments=pieces,
        current_body_clear=True,
        controlled_envelope=True,
        synthetic_test_only=True,
    )
    assert result["status"] == "unknown"
    assert result["fixture_enclosure_excluded"] is False
    assert result["cells_checked"] > 0
    assert result["curved_tube_radius_m"] >= config.radius + error


@pytest.mark.parametrize("side", [-1, 1])
@pytest.mark.parametrize("radius", [0.05, 0.30])
def test_synthetic_c1_outer_curve_tube_is_not_a_blocked_witness(side, radius):
    from sim.diagnostics import (
        _c1_curved_centerline,
        capture_synthetic_c1_views,
        probe_synthetic_c1_enclosure,
        probe_synthetic_c1_occupied_witness,
    )
    from sim.navigation import evaluate_synthetic

    config, speed, age = Config(), 0.6, 0.15
    turn = side * config.max_turn_rate
    points, error = _c1_curved_centerline(speed, turn, age, config, 1, turn)
    surface = points[-1] + np.array([config.radius + error / 2, 0])
    center = surface + np.array([radius, 0])
    assert np.linalg.norm(surface - points[-1]) < config.radius + error
    assert np.linalg.norm(center) > config.radius + radius
    scene = Scenario(
        start=(2, 2, 0),
        goal=(5, 2),
        obstacles=((*(center + [2, 2]), radius),),
        obstacle_heights=(0.05,),
    )
    reference = evaluate_synthetic(
        scene, speed=speed, turn_rate=turn, tof_age_s=age, synthetic_test_only=True
    )
    assert reference["maneuvers"]["left" if side > 0 else "right"]["status"] == "clear"
    acquired, acquired_yaw = integrate([2, 2], 0, speed, turn, -age)
    record = capture_synthetic_c1_views(
        scene,
        pose_m_rad=[*acquired, acquired_yaw],
        capture_tick=20,
        synthetic_test_only=True,
    )
    result = probe_synthetic_c1_enclosure(
        [record],
        reference_tick=23,
        reference_pose_m_rad=scene.start,
        speed=speed,
        turn_rate=turn,
        braking_turn_rate=turn,
        curved_segments=1,
        current_body_clear=True,
        controlled_envelope=True,
        synthetic_test_only=True,
    )
    assert result["status"] == "unknown"
    assert result["fixture_enclosure_excluded"] is False
    assert result["cells_checked"] > 0

    witness = probe_synthetic_c1_occupied_witness(
        [record],
        reference_tick=23,
        reference_pose_m_rad=scene.start,
        speed=speed,
        turn_rate=turn,
        braking_turn_rate=turn,
        curved_segments=1,
        controlled_envelope=True,
        synthetic_test_only=True,
    )
    assert witness["status"] == "unknown"
    assert witness["fixture_blocked_witness"] is False


@pytest.mark.parametrize("side", [-1, 1])
@pytest.mark.parametrize("radius", [0.05, 0.30])
def test_synthetic_c1_curved_tube_does_not_inherit_straight_clearance(side, radius):
    from sim.diagnostics import capture_synthetic_c1_views, probe_synthetic_c1_enclosure
    from sim.navigation import evaluate_synthetic

    scene = Scenario(
        start=(2, 2, 0),
        goal=(5, 2),
        obstacles=((2.28, 2 + side * (radius + 0.22), radius),),
        obstacle_heights=(0.05,),
    )
    turn = side * 1.5
    acquired, acquired_yaw = integrate([2, 2], 0, 0.6, turn, -0.15)
    record = capture_synthetic_c1_views(
        scene,
        pose_m_rad=[*acquired, acquired_yaw],
        capture_tick=20,
        synthetic_test_only=True,
    )
    for candidate, expected in ((0, "false"), (turn, "true")):
        assert (
            evaluate_synthetic(
                scene,
                speed=0.6,
                turn_rate=candidate,
                tof_age_s=0.15,
                synthetic_test_only=True,
            )["answers"]["path_blocked"]
            == expected
        )
    result = probe_synthetic_c1_enclosure(
        [record],
        reference_tick=23,
        reference_pose_m_rad=scene.start,
        speed=0.6,
        turn_rate=turn,
        curved_segments=16,
        current_body_clear=True,
        controlled_envelope=True,
        synthetic_test_only=True,
    )
    assert result["status"] == "unknown"
    assert result["fixture_enclosure_excluded"] is False


@pytest.mark.parametrize("side", [-1, 1])
@pytest.mark.parametrize("yaw", [0, math.pi / 2])
def test_synthetic_c1_curved_tube_cannot_exclude_a_side_wall(side, yaw):
    from sim.diagnostics import capture_synthetic_c1_views, probe_synthetic_c1_enclosure
    from sim.navigation import evaluate_synthetic

    position = np.array([3, 3]) + side * 2.77 * np.array(
        [-math.sin(yaw), math.cos(yaw)]
    )
    scene = Scenario(start=(*position, yaw), goal=(3, 3))
    turn = side * 1.5
    acquired, acquired_yaw = integrate(position, yaw, 0.6, turn, -0.15)
    record = capture_synthetic_c1_views(
        scene,
        pose_m_rad=[*acquired, acquired_yaw],
        capture_tick=20,
        synthetic_test_only=True,
    )
    for candidate, expected in ((0, "false"), (turn, "true")):
        assert (
            evaluate_synthetic(
                scene,
                speed=0.6,
                turn_rate=candidate,
                tof_age_s=0.15,
                synthetic_test_only=True,
            )["answers"]["path_blocked"]
            == expected
        )
    result = probe_synthetic_c1_enclosure(
        [record],
        reference_tick=23,
        reference_pose_m_rad=scene.start,
        speed=0.6,
        turn_rate=turn,
        curved_segments=16,
        current_body_clear=True,
        controlled_envelope=True,
        synthetic_test_only=True,
    )
    assert result["status"] == "unknown"
    assert result["reason"] == "axis_aligned_wall_support_incomplete"
    assert result["fixture_enclosure_excluded"] is False


@pytest.mark.parametrize("yaw", [0, 0.37, math.pi / 2, math.pi, -math.pi / 2])
def test_synthetic_c1_straight_capsule_excludes_with_obstacle_behind(yaw):
    from sim.diagnostics import capture_synthetic_c1_views, probe_synthetic_c1_enclosure
    from sim.navigation import evaluate_synthetic

    forward = np.array([math.cos(yaw), math.sin(yaw)])
    acquired = np.array([2, 2]) - 0.09 * forward
    center = np.array([2, 2]) - 0.6 * forward
    scene = Scenario(start=(2, 2, yaw), goal=(5, 2), obstacles=((*center, 0.30),))
    assert not swept_collision(acquired, [2, 2], 0.18, scene.obstacles, scene.bounds)
    record = capture_synthetic_c1_views(
        scene,
        pose_m_rad=[*acquired, yaw],
        capture_tick=20,
        synthetic_test_only=True,
    )
    settings = {
        "reference_tick": 23,
        "reference_pose_m_rad": scene.start,
        "speed": 0.6,
        "current_body_clear": True,
        "controlled_envelope": True,
        "synthetic_test_only": True,
    }
    assert (
        evaluate_synthetic(
            scene, speed=0.6, turn_rate=0, tof_age_s=0.15, synthetic_test_only=True
        )["answers"]["path_blocked"]
        == "false"
    )
    default = probe_synthetic_c1_enclosure([record], **settings)
    assert default["status"] == "unknown"
    result = probe_synthetic_c1_enclosure([record], turn_rate=0, **settings)
    assert result["status"] == "excluded_under_fixture_assumptions", result
    assert result["schema"] == "micro-classifier/synthetic-c1-straight-enclosure/1"
    assert result["straight_centerline_length_m"] == pytest.approx(0.30)
    assert result["capsule_radius_m"] == pytest.approx(0.18)
    assert "sweep_enclosure_radius_m" not in result
    assert result["free_space_qualified"] is False
    assert result["numerically_certified"] is False


@pytest.mark.parametrize("turn", [-1.5, -1e-15, 1e-15, 1.5])
def test_synthetic_c1_straight_capsule_rejects_nonzero_turns(c1_history, turn):
    from sim.diagnostics import probe_synthetic_c1_enclosure

    result = probe_synthetic_c1_enclosure(
        c1_history,
        reference_tick=23,
        reference_pose_m_rad=[2, 2, 0],
        speed=0.6,
        turn_rate=turn,
        current_body_clear=True,
        controlled_envelope=True,
        synthetic_test_only=True,
    )
    assert result["status"] == "unknown"
    assert result["reason"] == "unsupported_straight_maneuver"
    assert result["fixture_enclosure_excluded"] is False
    assert "straight_centerline_length_m" not in result


@pytest.mark.parametrize("turn", [True, "0", np.nan, np.inf, -np.inf, 2, -2, 10**400])
def test_synthetic_c1_straight_capsule_rejects_malformed_turns(c1_history, turn):
    from sim.diagnostics import probe_synthetic_c1_enclosure

    with pytest.raises(ValueError):
        probe_synthetic_c1_enclosure(
            c1_history,
            reference_tick=23,
            reference_pose_m_rad=[2, 2, 0],
            speed=0.6,
            turn_rate=turn,
            synthetic_test_only=True,
        )


@pytest.mark.parametrize(
    "pose",
    [(5.7, 2, 0), (2, 5.7, math.pi / 2), (0.3, 2, math.pi), (2, 0.3, -math.pi / 2)],
)
def test_synthetic_c1_straight_capsule_cannot_exclude_a_forward_wall(pose):
    from sim.diagnostics import capture_synthetic_c1_views, probe_synthetic_c1_enclosure
    from sim.navigation import evaluate_synthetic

    scene = Scenario(start=pose, goal=(3, 3))
    acquired = np.asarray(pose[:2]) - 0.09 * np.array(
        [math.cos(pose[2]), math.sin(pose[2])]
    )
    record = capture_synthetic_c1_views(
        scene,
        pose_m_rad=[*acquired, pose[2]],
        capture_tick=20,
        synthetic_test_only=True,
    )
    assert (
        evaluate_synthetic(
            scene, speed=0.6, turn_rate=0, tof_age_s=0.15, synthetic_test_only=True
        )["answers"]["path_blocked"]
        == "true"
    )
    result = probe_synthetic_c1_enclosure(
        [record],
        reference_tick=23,
        reference_pose_m_rad=pose,
        speed=0.6,
        turn_rate=0,
        current_body_clear=True,
        controlled_envelope=True,
        synthetic_test_only=True,
    )
    assert result["status"] == "unknown"
    assert result["reason"] == "axis_aligned_wall_support_incomplete"
    assert result["fixture_enclosure_excluded"] is False


@pytest.mark.parametrize(
    "offset",
    [
        (0.15, 0.229999),
        (0.15, -0.229999),
        (0.529999, 0),
        (0.3 + 0.229999 / math.sqrt(2), 0.229999 / math.sqrt(2)),
    ],
)
def test_synthetic_c1_straight_capsule_keeps_near_contact_unknown(offset):
    from sim.diagnostics import capture_synthetic_c1_views, probe_synthetic_c1_enclosure
    from sim.navigation import evaluate_synthetic

    scene = Scenario(
        start=(2, 2, 0),
        goal=(5, 2),
        obstacles=((2 + offset[0], 2 + offset[1], 0.05),),
        obstacle_heights=(0.05,),
    )
    record = capture_synthetic_c1_views(
        scene, pose_m_rad=[1.91, 2, 0], capture_tick=20, synthetic_test_only=True
    )
    assert (
        evaluate_synthetic(
            scene, speed=0.6, turn_rate=0, tof_age_s=0.15, synthetic_test_only=True
        )["answers"]["path_blocked"]
        == "true"
    )
    result = probe_synthetic_c1_enclosure(
        [record],
        reference_tick=23,
        reference_pose_m_rad=[2, 2, 0],
        speed=0.6,
        turn_rate=0,
        current_body_clear=True,
        controlled_envelope=True,
        synthetic_test_only=True,
    )
    assert result["status"] == "unknown"
    assert result["fixture_enclosure_excluded"] is False


def test_synthetic_c1_enclosure_excludes_empty_straight_fixture(c1_history):
    from sim.diagnostics import probe_synthetic_c1_enclosure

    result = probe_synthetic_c1_enclosure(
        c1_history,
        reference_tick=23,
        reference_pose_m_rad=[2, 2, 0],
        speed=0.6,
        current_body_clear=True,
        controlled_envelope=True,
        synthetic_test_only=True,
    )
    assert result["status"] == "excluded_under_fixture_assumptions", result
    assert result["fixture_enclosure_excluded"] is True
    assert result["sweep_enclosure_radius_m"] == pytest.approx(0.48)
    assert result["cells_checked"] <= 32768
    assert result["free_space_qualified"] is False
    assert result["numerically_certified"] is False


@pytest.mark.parametrize("yaw", [0, 0.37, math.pi / 2, math.pi - 0.01, -math.pi + 0.01])
@pytest.mark.parametrize("turn", [-1.5, 0, 1.5])
def test_synthetic_c1_enclosure_preserves_clear_turning_frames(c1_history, yaw, turn):
    from sim.diagnostics import capture_synthetic_c1_views, probe_synthetic_c1_enclosure

    scene = Scenario(start=(2, 2, yaw))
    records = []
    for original in c1_history:
        tick = int(original["capture_ticks"][0])
        position, acquired_yaw = integrate([2, 2], yaw, 0.6, turn, (tick - 23) * 0.05)
        records.append(
            capture_synthetic_c1_views(
                scene,
                pose_m_rad=[*position, acquired_yaw],
                capture_tick=tick,
                synthetic_test_only=True,
            )
        )
    result = probe_synthetic_c1_enclosure(
        records,
        reference_tick=23,
        reference_pose_m_rad=scene.start,
        speed=0.6,
        current_body_clear=True,
        controlled_envelope=True,
        synthetic_test_only=True,
    )
    assert result["status"] == "excluded_under_fixture_assumptions", result
    assert result["fixture_enclosure_excluded"] is True
    assert result["sweep_enclosure_radius_m"] == pytest.approx(0.48)
    assert result["cells_checked"] <= 32768


@pytest.mark.parametrize("radius", [0.05, 0.30])
@pytest.mark.parametrize("height", [0.05, 1.0])
@pytest.mark.parametrize("turn", [-1.5, 0, 1.5])
@pytest.mark.parametrize("enclosure_turn", [None, 0, -1.5, 1.5])
def test_synthetic_c1_enclosure_never_clears_blocked_envelope_fixtures(
    radius, height, turn, enclosure_turn
):
    from sim.diagnostics import capture_synthetic_c1_views, probe_synthetic_c1_enclosure
    from sim.navigation import evaluate_synthetic

    scene = Scenario(
        start=(2, 2, 0),
        goal=(5, 2),
        obstacles=((2.2 + radius, 2, radius),),
        obstacle_heights=(height,),
    )
    records = []
    for tick in (14, 15, 16, 16, 18, 19, 20, 20):
        position, yaw = integrate([2, 2], 0, 0.6, turn, (tick - 23) * 0.05)
        records.append(
            capture_synthetic_c1_views(
                scene,
                pose_m_rad=[*position, yaw],
                capture_tick=tick,
                synthetic_test_only=True,
            )
        )
    reference = evaluate_synthetic(
        scene,
        speed=0.6,
        turn_rate=turn if enclosure_turn is None else enclosure_turn,
        tof_age_s=0.15,
        synthetic_test_only=True,
    )
    assert reference["answers"]["path_blocked"] == "true"
    result = probe_synthetic_c1_enclosure(
        records,
        reference_tick=23,
        reference_pose_m_rad=[2, 2, 0],
        speed=0.6,
        turn_rate=enclosure_turn,
        curved_segments=16 if enclosure_turn not in (None, 0) else 0,
        current_body_clear=True,
        controlled_envelope=True,
        synthetic_test_only=True,
    )
    assert result["status"] == "unknown"
    assert result["fixture_enclosure_excluded"] is False
    assert result["cells_checked"] <= 32768
    from sim.diagnostics import _c1_low_free_segments, inspect_synthetic_c1_history

    inspected = inspect_synthetic_c1_history(
        records,
        reference_tick=23,
        reference_pose_m_rad=[2, 2, 0],
        synthetic_test_only=True,
    )
    segments, _ = _c1_low_free_segments(
        records[-1],
        inspected,
        [2, 2, 0],
        Config(**records[-1]["config"]),
    )
    center = np.array([0.2 + radius, 0])
    for start, end in segments[..., :2]:
        step = end - start
        fraction = np.clip(np.dot(center - start, step) / np.dot(step, step), 0, 1)
        assert np.linalg.norm(center - start - fraction * step) > radius


@pytest.mark.parametrize("radius", [0.05, 0.30])
@pytest.mark.parametrize("height", [0.05, 1.0])
@pytest.mark.parametrize("enclosure_turn", [None, 0, -1.5, 1.5])
def test_synthetic_c1_enclosure_keeps_masked_world_aliases_unknown(
    c1_history, radius, height, enclosure_turn
):
    from sim.diagnostics import capture_synthetic_c1_views, probe_synthetic_c1_enclosure
    from sim.navigation import evaluate_synthetic

    scene = Scenario(
        start=(2, 2, 0),
        goal=(5, 2),
        obstacles=((2.2 + radius, 2, radius),),
        obstacle_heights=(height,),
    )
    masked_histories = [[], []]
    removed = 0
    for empty in c1_history:
        blocked = capture_synthetic_c1_views(
            scene,
            pose_m_rad=empty["capture_poses_m_rad"][0],
            capture_tick=int(empty["capture_ticks"][0]),
            synthetic_test_only=True,
        )
        shared = (
            empty["tof_valid"]
            & blocked["tof_valid"]
            & (empty["tof_m"] == blocked["tof_m"])
        )
        removed += int((empty["tof_valid"] & ~shared).sum())
        assert shared.any()
        for history, record in zip(masked_histories, (empty, blocked), strict=True):
            history.append(
                dict(
                    record,
                    tof_m=np.where(shared, record["tof_m"], np.float32(0)),
                    tof_valid=shared.copy(),
                )
            )
        assert np.array_equal(
            masked_histories[0][-1]["tof_m"], masked_histories[1][-1]["tof_m"]
        )
        assert np.array_equal(
            masked_histories[0][-1]["tof_valid"],
            masked_histories[1][-1]["tof_valid"],
        )
    assert removed > 0
    for turn in (-1.5, 0, 1.5):
        reference = evaluate_synthetic(
            scene,
            speed=0.6,
            turn_rate=turn,
            tof_age_s=0.15,
            synthetic_test_only=True,
        )
        assert reference["answers"]["path_blocked"] == "true"
    results = [
        probe_synthetic_c1_enclosure(
            history,
            reference_tick=23,
            reference_pose_m_rad=[2, 2, 0],
            speed=0.6,
            turn_rate=enclosure_turn,
            curved_segments=16 if enclosure_turn not in (None, 0) else 0,
            current_body_clear=True,
            controlled_envelope=True,
            synthetic_test_only=True,
        )
        for history in masked_histories
    ]
    assert results[0] == results[1]
    assert results[0]["status"] == "unknown"
    assert results[0]["fixture_enclosure_excluded"] is False


@pytest.mark.parametrize(
    "field,value,reason",
    [
        ("max_cells", 0, "cell_budget_exhausted"),
        ("max_depth", 0, "unexcluded_center_cell"),
        ("current_body_clear", False, "current_body_clear_not_established"),
        ("current_body_clear", 1, "current_body_clear_not_established"),
        ("current_body_clear", "true", "current_body_clear_not_established"),
        ("controlled_envelope", False, "controlled_envelope_not_established"),
        ("controlled_envelope", 1, "controlled_envelope_not_established"),
        ("controlled_envelope", "true", "controlled_envelope_not_established"),
        ("reference_pose_m_rad", [3, 2, 0], "unsupported_capture_to_reference_motion"),
    ],
)
@pytest.mark.parametrize("enclosure_turn", [None, 0, -1.5, 1.5])
def test_synthetic_c1_enclosure_preserves_unknown_on_missing_support(
    c1_history, field, value, reason, enclosure_turn
):
    from sim.diagnostics import probe_synthetic_c1_enclosure

    settings = {
        "reference_tick": 23,
        "reference_pose_m_rad": [2, 2, 0],
        "speed": 0.6,
        "turn_rate": enclosure_turn,
        "curved_segments": 16 if enclosure_turn not in (None, 0) else 0,
        "current_body_clear": True,
        "controlled_envelope": True,
        "synthetic_test_only": True,
        field: value,
    }
    result = probe_synthetic_c1_enclosure(c1_history, **settings)
    assert result["status"] == "unknown"
    assert result["reason"] == reason
    assert result["fixture_enclosure_excluded"] is False


@pytest.mark.parametrize(
    "field,value",
    [
        ("speed", True),
        ("speed", np.nan),
        ("speed", np.inf),
        ("speed", -0.1),
        ("speed", 0.7),
        ("max_cells", True),
        ("max_cells", -1),
        ("max_cells", 65537),
        ("max_depth", True),
        ("max_depth", -1),
        ("max_depth", 13),
        ("radius_bands", True),
        ("radius_bands", 0),
        ("radius_bands", 17),
        ("synthetic_test_only", 1),
        ("synthetic_test_only", False),
    ],
)
def test_synthetic_c1_enclosure_rejects_malformed_controls(c1_history, field, value):
    from sim.diagnostics import probe_synthetic_c1_enclosure

    settings = {
        "reference_tick": 23,
        "reference_pose_m_rad": [2, 2, 0],
        "speed": 0.6,
        "current_body_clear": True,
        "controlled_envelope": True,
        "synthetic_test_only": True,
        field: value,
    }
    with pytest.raises(ValueError):
        probe_synthetic_c1_enclosure(c1_history, **settings)


def test_synthetic_c1_enclosure_does_not_attest_the_object_domain(c1_history):
    from sim.diagnostics import capture_synthetic_c1_views, probe_synthetic_c1_enclosure

    outside_domain = Scenario(start=(2, 2, 0), obstacles=((2.4, 2, 0.005),))
    records = [
        capture_synthetic_c1_views(
            outside_domain,
            pose_m_rad=record["capture_poses_m_rad"][0],
            capture_tick=int(record["capture_ticks"][0]),
            synthetic_test_only=True,
        )
        for record in c1_history
    ]
    for original, other in zip(c1_history, records, strict=True):
        assert np.array_equal(original["tof_m"], other["tof_m"])
    result = probe_synthetic_c1_enclosure(
        records,
        reference_tick=23,
        reference_pose_m_rad=[2, 2, 0],
        speed=0.6,
        current_body_clear=True,
        controlled_envelope=True,
        synthetic_test_only=True,
    )
    assert result["fixture_enclosure_excluded"] is True
    assert result["radius_interval_m"] == [0.05, 0.30]
    assert (
        result["assumptions"]["envelope_membership_independently_established"] is True
    )
    assert result["real_input_qualified"] is False
    assert result["free_space_qualified"] is False


def test_synthetic_c1_enclosure_keeps_stale_or_malformed_history_unknown(c1_history):
    from sim.diagnostics import probe_synthetic_c1_enclosure

    settings = {
        "reference_tick": 23,
        "reference_pose_m_rad": [2, 2, 0],
        "speed": 0.6,
        "current_body_clear": True,
        "controlled_envelope": True,
        "synthetic_test_only": True,
    }
    for records in ([], [c1_history[0]], c1_history * 2):
        result = probe_synthetic_c1_enclosure(records, **settings)
        assert result["status"] == "unknown"
        assert result["fixture_enclosure_excluded"] is False


def test_synthetic_c1_enclosure_cannot_clear_a_near_wall():
    from sim.diagnostics import capture_synthetic_c1_views, probe_synthetic_c1_enclosure
    from sim.navigation import evaluate_synthetic

    scene = Scenario(start=(5.7, 2, 0), goal=(4, 2))
    records = []
    for tick in (14, 15, 16, 16, 18, 19, 20, 20):
        position, yaw = integrate([5.7, 2], 0, 0.6, 0, (tick - 23) * 0.05)
        records.append(
            capture_synthetic_c1_views(
                scene,
                pose_m_rad=[*position, yaw],
                capture_tick=tick,
                synthetic_test_only=True,
            )
        )
    result = probe_synthetic_c1_enclosure(
        records,
        reference_tick=23,
        reference_pose_m_rad=scene.start,
        speed=0.6,
        current_body_clear=True,
        controlled_envelope=True,
        synthetic_test_only=True,
    )
    assert result["reason"] == "axis_aligned_wall_support_incomplete"
    assert result["fixture_enclosure_excluded"] is False
    assert (
        evaluate_synthetic(
            scene,
            speed=0.6,
            turn_rate=0,
            tof_age_s=0.15,
            synthetic_test_only=True,
        )["answers"]["path_blocked"]
        == "true"
    )


def test_synthetic_c1_enclosure_has_independent_sampled_center_support(c1_history):
    from sim.diagnostics import _c1_low_free_segments, inspect_synthetic_c1_history

    result = inspect_synthetic_c1_history(
        c1_history,
        reference_tick=23,
        reference_pose_m_rad=[2, 2, 0],
        synthetic_test_only=True,
    )
    segments, _ = _c1_low_free_segments(
        c1_history[-1],
        result,
        [2, 2, 0],
        Config(**c1_history[-1]["config"]),
    )
    checked = 0
    for radius in (0.05, 0.133, 0.30):
        for horizontal in np.linspace(-0.78, 0.78, 19):
            for vertical in np.linspace(-0.78, 0.78, 19):
                center = np.array([horizontal, vertical])
                distance = np.linalg.norm(center)
                if not 0.18 + radius < distance <= 0.48 + radius:
                    continue
                separations = []
                for start, end in segments[..., :2]:
                    step = end - start
                    fraction = np.clip(
                        np.dot(center - start, step) / np.dot(step, step), 0, 1
                    )
                    separations.append(np.linalg.norm(center - start - fraction * step))
                assert min(separations) < radius
                checked += 1
    assert checked > 100


def test_floor_rules_ignore_floor_without_claiming_calibrated_probabilities():
    from interface.protocol import QuestionId, Status, decode_decision, encode_decision
    from sim.rules import decide

    config = Config(noise_std=0, dropout=0, latency_ticks=0)
    observation, _ = RoverEnv(config).reset()
    decision = decide(observation, config=config)
    assert decision.status == Status.OK
    assert decision.catalogue_version == 1 and decision.model_version == 0
    assert [answer.question_id for answer in decision.answers] == list(QuestionId)[:3]
    assert [answer.selected for answer in decision.answers] == [0, 1, 3]
    assert len(encode_decision(decision)) == 100
    assert decode_decision(encode_decision(decision)) == decision


@pytest.fixture
def motion_rule_observation():
    config = Config(noise_std=0, dropout=0, latency_ticks=2)
    observation, _ = RoverEnv(Config(noise_std=0, dropout=0, latency_ticks=0)).reset()
    observation.update(tick=3, time_s=0.15, tof_sample_tick=0, tof_age_s=0.15)
    observation["ego"] = np.array([0.6, 0, 4, 0], dtype=np.float32)
    observation["goal_body_m"] = observation["ego"][2:].copy()
    observation["history_valid"][-4:] = True
    observation["history_ego"][-4:] = observation["ego"]
    observation["tof_valid"][3, 3] = True
    observation["tof_m"][3, 3] = 0.53
    return config, observation


def test_motion_registered_rules_shift_old_hits_before_stopping_check(
    motion_rule_observation,
):
    from sim.rules import RuleSettings, decide

    config, observation = motion_rule_observation
    original = decide(observation, config=config)
    registered = decide(
        observation, config=config, settings=RuleSettings(register_motion=True)
    )
    assert original.status == registered.status == 0
    assert original.answers[0].selected == 0
    assert registered.answers[0].selected == 1
    assert registered.answers[2].selected == 0


@pytest.mark.parametrize("turn", [0.0, -0.1, 0.1])
def test_motion_registered_rules_match_independent_interval_composition(
    motion_rule_observation, turn
):
    from sim.rules import _registered_columns

    config, observation = motion_rule_observation
    observation["ego"][1] = turn
    observation["history_ego"][-4:] = observation["ego"]
    ranges = observation["tof_m"]
    rays = tof_directions(0, config)
    supported = observation["tof_valid"] & (ranges > 0) & (ranges < config.max_range)
    obstacles = supported & (config.tof_mount_height + ranges * rays[..., 2] > 0.03)
    columns = _registered_columns(observation, config, rays, supported, obstacles)
    angle = float(observation["ego"][1]) * 3 * config.dt
    speed = float(observation["ego"][0])
    translation = (
        np.array([speed * 3 * config.dt, 0])
        if not angle
        else speed
        / float(observation["ego"][1])
        * np.array([math.sin(angle), 1 - math.cos(angle)])
    )
    hit = float(ranges[3, 3]) * rays[3, 3, :2] - translation
    expected_distance = math.hypot(*hit)
    expected_bearing = math.atan2(hit[1], hit[0]) - angle
    column = round(
        (config.field_of_view / 2 - expected_bearing) * 7 / config.field_of_view
    )
    assert columns[column] == pytest.approx(expected_distance, abs=1e-12)
    assert np.count_nonzero(columns < config.max_range) == 1


@pytest.mark.parametrize(
    "defect",
    [
        "missing_history",
        "shape",
        "dtype",
        "mask_dtype",
        "gap",
        "current_mismatch",
        "nan",
        "speed",
        "negative_speed",
        "turn",
        "short_window",
        "clock",
        "delayed_config",
        "delayed_metadata",
    ],
)
def test_motion_registered_rules_reject_unsupported_motion(
    motion_rule_observation, defect
):
    from dataclasses import replace

    from interface.protocol import Status
    from sim.rules import RuleSettings, decide

    config, observation = motion_rule_observation
    if defect == "missing_history":
        del observation["history_ego"]
    elif defect == "shape":
        observation["history_ego"] = np.zeros((8, 3))
    elif defect == "dtype":
        observation["history_ego"] = observation["history_ego"].astype(str)
    elif defect == "mask_dtype":
        observation["history_valid"] = observation["history_valid"].astype(int)
    elif defect == "gap":
        observation["history_valid"][-2] = False
    elif defect == "current_mismatch":
        observation["history_ego"][-1, 0] = 0
    elif defect in ("nan", "speed", "negative_speed", "turn"):
        value = {"nan": float("nan"), "speed": 2, "negative_speed": -1, "turn": 2}[
            defect
        ]
        observation["history_ego"][-2, int(defect == "turn")] = value
    elif defect == "short_window":
        config = replace(config, history_ticks=2)
    elif defect == "clock":
        observation["time_s"] = 0.16
    elif defect == "delayed_config":
        config = replace(config, odometry_latency_ticks=1)
    else:
        observation.update(ego_sample_tick=2, ego_age_s=0.05)
    decision = decide(
        observation, config=config, settings=RuleSettings(register_motion=True)
    )
    assert decision.status == Status.REJECT_OUT_OF_DOMAIN and not decision.answers


def test_motion_registered_rules_reject_turns_without_current_column_support(
    motion_rule_observation,
):
    from interface.protocol import Status
    from sim.rules import RuleSettings, decide, wire_step

    config, observation = motion_rule_observation
    observation["ego"][:2] = [0, 1.5]
    observation["history_ego"][-4:] = observation["ego"]
    settings = RuleSettings(register_motion=True)
    assert decide(observation, config=config).status == Status.OK
    assert (
        decide(observation, config=config, settings=settings).status
        == Status.REJECT_OUT_OF_DOMAIN
    )
    action, *_ = wire_step(observation, config=config, settings=settings)
    np.testing.assert_array_equal(action, [0, 0])


def test_motion_registered_rules_are_detached_and_ignore_privileged_fields(
    motion_rule_observation,
):
    from sim.rules import RuleSettings, decide

    config, observation = motion_rule_observation
    before = json.dumps(observation, default=json_value, sort_keys=True)
    settings = RuleSettings(register_motion=True)
    expected = decide(observation, config=config, settings=settings)
    assert json.dumps(observation, default=json_value, sort_keys=True) == before
    observation.update(
        ground_truth={"position_m": [99, 99]},
        action=[99, 99],
        labels={"path_blocked": False},
    )
    assert decide(observation, config=config, settings=settings) == expected


@pytest.mark.parametrize("value", [None, 0, 1, "true", np.bool_(True)])
def test_motion_registered_rules_require_an_explicit_boolean(value):
    from sim.rules import RuleSettings

    with pytest.raises(ValueError):
        RuleSettings(register_motion=value)


def test_motion_registered_rules_zero_age_preserves_original_decision():
    from sim.rules import RuleSettings, decide

    config = Config(noise_std=0, dropout=0, latency_ticks=0)
    observation, _ = RoverEnv(config).reset()
    before = json.dumps(observation, default=json_value, sort_keys=True)
    assert decide(
        observation, config=config, settings=RuleSettings(register_motion=True)
    ) == decide(observation, config=config)
    assert json.dumps(observation, default=json_value, sort_keys=True) == before


@pytest.mark.parametrize(
    "defect,status",
    [
        ("missing", 2),
        ("stale", 2),
        ("column", 3),
        ("zero", 3),
        ("masked_nonzero", 3),
        ("below_floor", 3),
        ("legacy", 3),
        ("bad_age", 3),
    ],
)
def test_floor_rules_reject_unsupported_evidence(defect, status):
    from dataclasses import replace

    from sim.rules import decide

    config = Config(noise_std=0, dropout=0, latency_ticks=0)
    observation, _ = RoverEnv(config).reset()
    if defect == "missing":
        observation["tof_sample_tick"] = None
        observation["tof_valid"][:] = False
        observation["tof_m"][:] = 0
    elif defect == "stale":
        observation.update(tick=2, time_s=0.1, tof_age_s=0.1)
    elif defect == "column":
        observation["tof_valid"][:, 3] = False
        observation["tof_m"][:, 3] = 0
    elif defect == "zero":
        observation["tof_m"][:] = 0
    elif defect == "masked_nonzero":
        observation["tof_m"][0, 0] = 1
    elif defect == "below_floor":
        observation["tof_m"][-1, 0] = 1
    elif defect == "legacy":
        config = replace(config, tof_mount_height=None)
    else:
        observation["tof_age_s"] = float("nan")
    packet = decide(observation, config=config)
    assert packet.status == status and not packet.answers


def test_floor_rules_obstacle_momentum_and_privileged_fields_are_independent():
    from sim.rules import decide

    config = Config(noise_std=0, dropout=0, latency_ticks=0)
    observation, _ = RoverEnv(config).reset()
    observation["ego"][0] = 0.6
    observation["tof_valid"][3, 3] = True
    observation["tof_m"][3, 3] = 0.35
    first = decide(observation, config=config)
    assert [answer.selected for answer in first.answers][::2] == [1, 0]
    observation.update(
        ground_truth={"position_m": [99, 99]},
        action=[99, 99],
        labels={"path_blocked": False},
    )
    assert decide(observation, config=config) == first


@pytest.mark.parametrize(
    "defect", ["absent", "crc", "sequence", "timestamp", "rejected"]
)
def test_floor_rules_host_brakes_on_missing_or_invalid_decisions(defect):
    from dataclasses import replace

    from interface.protocol import Status, decode_decision, encode_decision
    from sim.rules import host_action, wire_step

    config = Config(noise_std=0, dropout=0, latency_ticks=0)
    observation, _ = RoverEnv(config).reset()
    action, state_frame, frame = wire_step(observation, config=config)
    assert action[0] > 0
    packet = decode_decision(frame)
    if defect == "absent":
        frame = None
    elif defect == "crc":
        frame = frame[:-1] + bytes([frame[-1] ^ 1])
    elif defect == "sequence":
        frame = encode_decision(replace(packet, sequence=1))
    elif defect == "timestamp":
        frame = encode_decision(replace(packet, timestamp_us=1))
    else:
        frame = encode_decision(
            replace(packet, status=Status.REJECT_STALE_INPUT, answers=())
        )
    np.testing.assert_array_equal(
        host_action(state_frame, frame, config=config), [0, 0]
    )


@pytest.fixture(scope="module")
def c1_normal_command_ledger(request):
    counts = {"mapper": 0, "state_decode": 0, "decision_decode": 0, "forbidden": 0}
    yield counts
    assert all(
        counts[key] <= 32 for key in ("mapper", "state_decode", "decision_decode")
    )
    assert counts["forbidden"] == 0
    capture = request.config.pluginmanager.getplugin("capturemanager")
    if capture is None:
        print("C1 normal-command ledger:", json.dumps(counts, sort_keys=True))
    else:
        with capture.global_and_fixture_disabled():
            print("C1 normal-command ledger:", json.dumps(counts, sort_keys=True))


@pytest.mark.parametrize("case", range(24))
def test_synthetic_c1_normal_command_maps_complete_wire_selections(
    c1_normal_command_ledger, monkeypatch, case
):
    from dataclasses import replace

    from interface.protocol import (
        QUESTIONS,
        RULES_QUESTIONS,
        Answer,
        Decision,
        State,
        Status,
        encode_decision,
        encode_state,
    )
    from sim import rules

    ledger = c1_normal_command_ledger
    sector, tier = (case // 3, case % 3 + 1) if case < 9 else (0, 3)
    selected = (int(case == 9), 3 if case == 10 else sector, 0 if case == 11 else tier)
    answers = tuple(
        Answer(
            question,
            tuple(0.25 for _ in options)
            if case == 4 and len(options) == 4
            else tuple(float(index == choice) for index in range(len(options))),
            choice,
        )
        for (question, (_, options)), choice in zip(
            RULES_QUESTIONS.items(), selected, strict=True
        )
    )
    state = State(
        sequence=22,
        timestamp_us=1100000,
        goal_m=(0.01, 0.02, 0.0) if case == 4 else (3.0, 1.0, 0.0),
    )
    decision = Decision(
        sequence=22, timestamp_us=1100000, status=Status.OK, answers=answers
    )
    if case == 13:
        decision = replace(
            decision, status=Status.REJECT_OUT_OF_DOMAIN, answers=answers[:1]
        )
    elif case == 14:
        legacy_answers = tuple(
            Answer(
                question, tuple(float(index == 0) for index in range(len(options))), 0
            )
            for question, (_, options) in QUESTIONS.items()
        )
        decision = replace(
            decision, catalogue_version=0, model_version=1, answers=legacy_answers
        )
    elif case == 16:
        decision = replace(decision, sequence=23)
    elif case == 17:
        decision = replace(decision, timestamp_us=1100001)
    elif case == 19:
        state = replace(state, ages_us=(160000, *state.ages_us[1:]))
    elif case == 20:
        state = replace(
            state,
            validity=3,
            goal_m=(0.0, 0.0, 0.0),
            ages_us=(0, 0, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF),
        )
    elif case == 21:
        state = replace(state, validity=23, faults=1, ages_us=(0, 0, 0, 0xFFFFFFFF, 0))
    state_frame, decision_frame = encode_state(state), encode_decision(decision)
    if case == 12:
        decision_frame = None
    elif case == 15:
        decision_frame = decision_frame[:-1] + bytes([decision_frame[-1] ^ 1])
    elif case == 22:
        state_frame = bytearray(state_frame)
    settings = {
        "reference_tick": 23 if case == 18 else 22,
        "synthetic_test_only": case != 23,
    }
    saved_state, saved_decision, saved_settings = (
        deepcopy(state_frame),
        deepcopy(decision_frame),
        deepcopy(settings),
    )
    for key, name in (
        ("state_decode", "decode_state"),
        ("decision_decode", "decode_decision"),
    ):
        original = getattr(rules, name)

        def counted(*args, _key=key, _original=original, **kwargs):
            ledger[_key] += 1
            assert ledger[_key] <= 32
            return _original(*args, **kwargs)

        monkeypatch.setattr(rules, name, counted)

    def forbidden(*args, **kwargs):
        ledger["forbidden"] += 1
        raise AssertionError(
            "normal mapper must not choose heuristic answers, steer by goals or actuate"
        )

    for name in (
        "host_action",
        "wire_step",
        "decide",
        "_diagnostic_episode",
        "run_diagnostics",
        "write_episode",
    ):
        monkeypatch.setattr(rules, name, forbidden)
    monkeypatch.setattr(RoverEnv, "reset", forbidden)
    monkeypatch.setattr(RoverEnv, "step", forbidden)
    monkeypatch.setattr(rules.math, "atan2", forbidden)
    monkeypatch.setattr(rules.math, "hypot", forbidden)

    def check(**changes):
        ledger["mapper"] += 1
        assert ledger["mapper"] <= 32
        return rules._map_synthetic_c1_normal_command(
            state_frame, decision_frame, **{**settings, **changes}
        )

    if case == 23:
        with pytest.raises(ValueError, match="synthetic_test_only"):
            check()
        return
    before = dict(ledger)
    result = check()
    mapped = case < 9
    assert result["fixture_command_mapped"] is mapped
    assert ledger["state_decode"] - before["state_decode"] == int(case not in (12, 22))
    assert ledger["decision_decode"] - before["decision_decode"] == int(
        case not in (12, 22)
    )
    for flag in (
        "training_approved",
        "real_input_qualified",
        "free_space_qualified",
        "numerically_certified",
        "source_qualified",
        "native_execution_qualified",
        "command_admission_qualified",
    ):
        assert result[flag] is False
    if mapped:
        assert result["status"] == "mapped_conditional_normal_fixture"
        assert result["requested_command"] == {
            "target_speed_m_s": Config().max_speed * tier / 3,
            "turn_rate_rad_s": (1.5, 0.0, -1.5)[sector],
        }
        assert (
            result["state_frame_hex"] == state_frame.hex()
            and result["decision_frame_hex"] == decision_frame.hex()
        )
        if case == 4:
            assert result["requested_command"]["turn_rate_rad_s"] == 0.0
            assert decision.answers[1].selected != max(
                range(4), key=decision.answers[1].probabilities.__getitem__
            )
            assert decision.answers[2].confidence == 0.0
        if case == 0:
            saved = deepcopy(result)
            result["requested_command"]["target_speed_m_s"] = 10.0
            result["work"]["state_decode_entries"] = 100
            assert check() == saved
    else:
        assert result["status"] == "fallback"
        assert result["requested_command"] == {
            "target_speed_m_s": 0.0,
            "turn_rate_rad_s": 0.0,
        }
        assert "state_frame_hex" not in result and "decision_frame_hex" not in result
        assert (
            result["reason"]
            == {
                9: "normal_selection_requests_braking",
                10: "normal_selection_requests_braking",
                11: "normal_selection_requests_braking",
                12: "unsupported_normal_frames",
                13: "complete_active_ok_missing",
                14: "complete_active_ok_missing",
                15: "invalid_normal_frames",
                16: "normal_decision_binding_mismatch",
                17: "normal_decision_binding_mismatch",
                18: "current_state_binding_mismatch",
                19: "stale_host_groups",
                20: "unsupported_host_groups",
                21: "unsupported_host_task_or_faults",
                22: "unsupported_normal_frames",
            }[case]
        )
    assert (
        state_frame == saved_state
        and decision_frame == saved_decision
        and settings == saved_settings
    )


@pytest.mark.parametrize(
    "settings",
    [
        {"floor_band_m": -1},
        {"floor_band_m": None},
        {"max_age_s": True},
        {"max_age_s": float("nan")},
        {"floor_band_m": 10**400},
    ],
)
def test_floor_rule_settings_reject_invalid_values(settings):
    from sim.rules import RuleSettings

    with pytest.raises(ValueError):
        RuleSettings(**settings)


def test_floor_rules_diagnostics_are_bounded_private_and_exclusive(tmp_path):
    from interface.protocol import decode_decision, decode_state
    from sim.rules import run_diagnostics

    output, report = tmp_path / "episodes", tmp_path / "report.json"
    result = run_diagnostics(output, report, config=Config(max_ticks=2))
    assert result["totals"]["episodes"] == 8
    assert result["totals"]["ticks"] == 16
    assert not result["training_approved"] and not result["task_labels"]
    assert not result["rule_quality_qualified"] and not result["calibrated"]
    for path in output.glob("*.jsonl"):
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        assert rows[0]["policy"] == "observation_only_wire_rules"
        for row in rows[1:-1]:
            state = decode_state(bytes.fromhex(row["state_frame_hex"]))
            decision = decode_decision(bytes.fromhex(row["decision_frame_hex"]))
            assert state.sequence == decision.sequence
            assert "ground_truth" not in row["observation"]
            assert "reference_comparisons" not in row
    with pytest.raises(ValueError, match="fresh"):
        run_diagnostics(output, report)


@pytest.mark.parametrize("direction", ["equal", "report_parent", "output_parent"])
def test_floor_rules_diagnostic_paths_reject_before_collection(
    tmp_path, monkeypatch, direction
):
    from sim import rules

    def unexpected(*args):
        raise AssertionError("must reject before collection")

    monkeypatch.setattr(rules, "_diagnostic_episode", unexpected)
    output, report = tmp_path / "output", tmp_path / "output"
    if direction == "report_parent":
        output = report / "nested"
    elif direction == "output_parent":
        report = output / "nested.json"
    with pytest.raises(ValueError, match="nonoverlapping"):
        rules.run_diagnostics(output, report)
    assert not (tmp_path / "output").exists()


@pytest.mark.parametrize("top", [0.05, 0.5, 1.0])
def test_tof_capped_cylinder_first_hit_satisfies_analytic_surface(top):
    config = Config(noise_std=0, dropout=0, latency_ticks=0)
    scene = Scenario(obstacles=((3.0, 3.0, 0.5),), obstacle_heights=(top,))
    ranges = tof_ranges(np.array(scene.start[:2]), 0, scene, config)
    rays = tof_directions(0, config)
    row, column = (4, 3) if top == 0.05 else (3, 3)
    point = np.array([1, 3, 0.15]) + ranges[row, column] * rays[row, column]
    if top == 0.05:
        assert point[2] == pytest.approx(top)
        assert np.linalg.norm(point[:2] - [3, 3]) < 0.5
    else:
        assert np.linalg.norm(point[:2] - [3, 3]) == pytest.approx(0.5)
        assert 0 < point[2] < top
    assert ranges[row, column] < config.max_range


def test_tof_low_obstacles_and_tall_obstacles_have_different_row_visibility():
    config = Config(noise_std=0, dropout=0, latency_ticks=0)
    scenes = [
        Scenario(obstacles=((3, 3, 0.5),), obstacle_heights=(top,))
        for top in (0.05, 1.0)
    ]
    observations = [RoverEnv(config, scene).reset()[0] for scene in scenes]
    assert not observations[0]["tof_valid"][0, 3]
    assert observations[1]["tof_valid"][0, 3]
    assert observations[0]["tof_m"][4, 3] > observations[1]["tof_m"][4, 3]


def test_tof_geometry_rotates_with_yaw_without_changing_returns():
    config = Config()
    scenes = [
        Scenario(start=(3, 3, 0), obstacles=((4, 3, 0.3),)),
        Scenario(start=(3, 3, math.pi / 2), obstacles=((3, 4, 0.3),)),
    ]
    ranges = [
        tof_ranges(np.array(scene.start[:2]), scene.start[2], scene, config)
        for scene in scenes
    ]
    np.testing.assert_allclose(*ranges, rtol=1e-13, atol=1e-13)


def test_tof_finite_wall_does_not_continue_beyond_its_arena_edge():
    config = Config(tof_mount_pitch=-math.pi / 4, wall_height=0.1)
    scene = Scenario()
    ranges = tof_ranges(np.array(scene.start[:2]), 0, scene, config)
    assert np.isinf(ranges).all()


def test_tof_legacy_planar_sampling_preserves_values_masks_and_rng():
    config = Config(tof_mount_height=None, tof_rate_hz=None, latency_ticks=0)
    env = RoverEnv(config)
    observation, _ = env.reset(seed=42)
    rng = np.random.default_rng(42)
    for _ in range(4):
        angles = np.linspace(config.field_of_view / 2, -config.field_of_view / 2, 8)
        ranges = ray_ranges(
            env.position,
            angles,
            env.scenario.obstacles,
            env.scenario.bounds,
            config.max_range,
        )
        grid = np.broadcast_to(ranges, (8, 8)).copy()
        grid += rng.normal(0, config.noise_std, grid.shape)
        valid = rng.random((8, 8)) >= config.dropout
        expected = np.where(valid, np.clip(grid, 0, config.max_range), 0).astype(
            np.float32
        )
        np.testing.assert_array_equal(observation["tof_m"], expected)
        np.testing.assert_array_equal(observation["tof_valid"], valid)
        assert rng.bit_generator.state == env.rng.bit_generator.state
        observation, *_ = env.step((0, 0))


def test_odometry_delay_holds_an_old_estimate_and_exports_its_age():
    from interface.protocol import decode_state, encode_state

    config = Config(odometry_latency_ticks=1, latency_ticks=0)
    env = RoverEnv(config)
    initial, _ = env.reset(seed=4)
    first, *_ = env.step((0.6, 0.4))
    np.testing.assert_array_equal(first["ego"], initial["ego"])
    assert first["ego_sample_tick"] == 0
    assert first["ego_age_s"] == pytest.approx(config.dt)
    second, *_ = env.step((0.6, 0.4))
    assert second["ego"][0] == pytest.approx(config.acceleration * config.dt)
    assert second["ego_sample_tick"] == 1
    np.testing.assert_array_equal(second["history_ego"][-1], second["ego"])
    state = decode_state(encode_state(state_from_observation(second)))
    assert state.ages_us[:3] == (50_000, 50_000, 50_000)
    assert state.velocity_m_s[0] == pytest.approx(second["ego"][0])


@pytest.mark.parametrize(
    "position_error,heading_error", [(0.02, 0), (0, math.radians(2))]
)
def test_odometry_synthetic_errors_are_bounded_and_do_not_change_physics_or_tof(
    position_error, heading_error
):
    from dataclasses import replace

    config = Config(
        odometry_position_error=position_error, odometry_heading_error=heading_error
    )
    noisy, ideal = (
        RoverEnv(config),
        RoverEnv(replace(config, odometry_position_error=0, odometry_heading_error=0)),
    )
    observation, _ = noisy.reset(seed=42)
    reference, _ = ideal.reset(seed=42)
    assert not np.array_equal(observation["ego"], reference["ego"])
    for _ in range(12):
        np.testing.assert_array_equal(observation["tof_m"], reference["tof_m"])
        np.testing.assert_array_equal(observation["tof_valid"], reference["tof_valid"])
        if position_error:
            assert (
                np.linalg.norm(observation["goal_body_m"] - reference["goal_body_m"])
                <= position_error + 1e-6
            )
        else:
            assert np.linalg.norm(observation["goal_body_m"]) == pytest.approx(
                np.linalg.norm(reference["goal_body_m"]), abs=1e-6
            )
            difference = math.atan2(*observation["goal_body_m"][::-1]) - math.atan2(
                *reference["goal_body_m"][::-1]
            )
            assert abs(difference) <= heading_error + 1e-6
        observation, *outcome, info = noisy.step((0.3, 0.2))
        reference, *expected, reference_info = ideal.step((0.3, 0.2))
        assert outcome == expected
        np.testing.assert_array_equal(
            info["ground_truth"]["position_m"],
            reference_info["ground_truth"]["position_m"],
        )
        assert noisy.rng.bit_generator.state == ideal.rng.bit_generator.state


def test_odometry_combined_errors_reset_and_read_without_extra_rng():
    config = Config(
        odometry_position_error=0.02,
        odometry_heading_error=math.radians(2),
        odometry_latency_ticks=1,
    )
    env = RoverEnv(config)
    snapshots = []
    for _ in range(2):
        observation, _ = env.reset(seed=42)
        sequence = []
        for _ in range(10):
            before = deepcopy(env.odometry_rng.bit_generator.state)
            np.testing.assert_array_equal(env._observation()["ego"], observation["ego"])
            assert env.odometry_rng.bit_generator.state == before
            sequence.append(json.dumps(observation, default=json_value, sort_keys=True))
            observation, *_ = env.step((0.3, 0.4))
        snapshots.append(sequence)
    assert snapshots[0] == snapshots[1]
    assert "position_m" not in observation and "yaw_rad" not in observation


@pytest.mark.parametrize(
    "settings",
    [
        {"odometry_position_error": -0.01},
        {"odometry_position_error": float("inf")},
        {"odometry_heading_error": -0.01},
        {"odometry_heading_error": math.pi + 0.01},
        {"odometry_heading_error": float("nan")},
        {"odometry_latency_ticks": -1},
        {"odometry_latency_ticks": 0.5},
        {"odometry_position_error": 10**400},
    ],
)
def test_odometry_rejects_invalid_configuration(settings):
    with pytest.raises(ValueError):
        Config(**settings)


@pytest.mark.parametrize(
    "changes",
    [
        {"ego_sample_tick": 0},
        {"ego_age_s": 0.05},
        {"ego_sample_tick": False, "ego_age_s": 0},
        {"ego_sample_tick": 1.0, "ego_age_s": 0},
        {"ego_sample_tick": -1, "ego_age_s": 0.1},
        {"ego_sample_tick": 2, "ego_age_s": 0},
        {"ego_sample_tick": 0, "ego_age_s": True},
        {"ego_sample_tick": 0, "ego_age_s": float("nan")},
        {"ego_sample_tick": 0, "ego_age_s": 10**400},
        {"ego_sample_tick": 0, "ego_age_s": 0},
        {"ego_sample_tick": 0, "ego_age_s": -0.05},
        {"ego_sample_tick": 0, "ego_age_s": 1e308, "time_s": 1e308},
    ],
)
def test_odometry_wire_export_rejects_malformed_age(changes):
    env = RoverEnv()
    observation, *_ = env.step((0, 0))
    observation.update(changes)
    with pytest.raises(ValueError):
        state_from_observation(observation)


@pytest.mark.parametrize(
    "settings",
    [
        {"tof_mount_height": 0},
        {"tof_mount_height": -0.1},
        {"tof_mount_height": float("inf")},
        {"tof_mount_pitch": math.pi / 2},
        {"tof_mount_pitch": -math.pi / 2},
        {"wall_height": 0},
        {"obstacle_height": -1},
    ],
)
def test_tof_geometry_rejects_invalid_configuration(settings):
    with pytest.raises(ValueError):
        Config(**settings)


@pytest.mark.parametrize(
    "heights", [(0,), (-1,), (True,), (float("nan"),), (float("inf"),), (0.1, 0.2)]
)
def test_tof_geometry_rejects_invalid_obstacle_heights(heights):
    with pytest.raises(ValueError):
        RoverEnv(scenario=Scenario(obstacles=((3, 3, 0.2),), obstacle_heights=heights))


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


@pytest.mark.parametrize(
    "point", [(0.125, 2.0), (5.875, 2.0), (2.0, 0.125), (2.0, 5.875)]
)
def test_synthetic_navigation_reference_and_simulator_include_wall_contact(point):
    from sim.navigation import _touches

    radius, bounds = 0.125, (6.0, 6.0)
    assert swept_collision(point, point, radius, (), bounds)
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


@pytest.mark.parametrize("yaw", [1e16, -1e16])
def test_synthetic_navigation_reference_large_heading_preserves_small_turns(yaw):
    from sim.navigation import evaluate_synthetic

    bounded_yaw = math.atan2(math.sin(yaw), math.cos(yaw))
    settings = {
        "speed": 0.6,
        "turn_rate": 0.7,
        "tof_age_s": 0.1,
        "synthetic_test_only": True,
    }
    large = evaluate_synthetic(Scenario(start=(1.0, 3.0, yaw)), **settings)
    bounded = evaluate_synthetic(Scenario(start=(1.0, 3.0, bounded_yaw)), **settings)
    for name, reference in bounded["maneuvers"].items():
        actual = large["maneuvers"][name]
        assert actual["status"] == reference["status"] == "clear"
        assert math.dist(actual["endpoint_m"], reference["endpoint_m"]) <= (
            actual["endpoint_error_bound_m"]
            + reference["endpoint_error_bound_m"]
            + 1e-12
        )
    assert large["answers"] == bounded["answers"]


@pytest.mark.parametrize("field", ["speed", "turn_rate", "tof_age_s"])
@pytest.mark.parametrize("value", [10**400, -(10**400)])
def test_synthetic_navigation_rejects_unrepresentable_motion(field, value):
    from sim.navigation import evaluate_synthetic, probe_synthetic_ray_witness

    settings = {"speed": 0.6, "synthetic_test_only": True, field: value}
    with pytest.raises(ValueError, match="finite"):
        evaluate_synthetic(Scenario(), **settings)
    with pytest.raises(ValueError, match="finite"):
        probe_synthetic_ray_witness(np.full(8, 0.3), np.ones(8, dtype=bool), **settings)


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


@pytest.mark.parametrize(
    "distance,status", [(0.3, "blocked_witness"), (0.8, "unknown"), (4.0, "unknown")]
)
def test_synthetic_ray_probe_has_positive_witness_but_never_infers_clear(
    distance, status
):
    from sim.navigation import probe_synthetic_ray_witness

    ranges, valid = np.full(8, 4.0), np.ones(8, dtype=bool)
    ranges[3] = distance
    original = ranges.copy()
    result = probe_synthetic_ray_witness(
        ranges,
        valid,
        speed=0.6,
        config=Config(noise_std=0, latency_ticks=0),
        synthetic_test_only=True,
    )
    assert result["status"] == status
    assert result["synthetic"] and not result["training_approved"]
    assert not result["real_input_qualified"] and not result["physical_safety_claim"]
    assert result["witness_columns"] == ([3] if status == "blocked_witness" else [])
    np.testing.assert_array_equal(ranges, original)


def test_synthetic_ray_probe_normal_defaults_abstain():
    from sim.navigation import probe_synthetic_ray_witness

    result = probe_synthetic_ray_witness(
        np.full(8, 0.3), np.ones(8, dtype=bool), speed=0.6, synthetic_test_only=True
    )
    assert (
        result["status"] == "unknown" and result["reason"] == "noise_model_unqualified"
    )


@pytest.mark.parametrize(
    "obstacle,oracle_answer,probe_status",
    [
        ((1.35, 3.0, 0.04), "true", "blocked_witness"),
        ((1.6, 3.0, 0.04), "false", "unknown"),
        ((1.25, 3.195, 0.02), "true", "unknown"),
    ],
)
def test_synthetic_ray_probe_corresponds_to_geometry_without_proving_clear(
    obstacle, oracle_answer, probe_status
):
    from sim.navigation import evaluate_synthetic, probe_synthetic_ray_witness

    config = Config(noise_std=0, latency_ticks=0)
    scene = Scenario(obstacles=(obstacle,))
    angles = np.linspace(config.field_of_view / 2, -config.field_of_view / 2, 8)
    ranges = ray_ranges(
        scene.start[:2], angles, scene.obstacles, scene.bounds, config.max_range
    )
    probe = probe_synthetic_ray_witness(
        ranges,
        np.ones(8, dtype=bool),
        speed=0.6,
        config=config,
        synthetic_test_only=True,
    )
    reference = evaluate_synthetic(
        scene, speed=0.6, config=config, synthetic_test_only=True
    )
    assert probe["status"] == probe_status
    assert reference["answers"]["path_blocked"] == oracle_answer


@pytest.mark.parametrize(
    "offset,status", [(-1e-6, "blocked_witness"), (0, "unknown"), (1e-6, "unknown")]
)
def test_synthetic_ray_probe_boundary_requires_strict_interior(offset, status):
    from sim.navigation import probe_synthetic_ray_witness

    config = Config(noise_std=0, latency_ticks=0)
    angle = np.linspace(config.field_of_view / 2, -config.field_of_view / 2, 8)[3]
    distance = 0.6 * config.dt + 0.6**2 / (2 * config.acceleration)
    contact = distance * math.cos(angle) + math.sqrt(
        config.radius**2 - distance**2 * math.sin(angle) ** 2
    )
    ranges, valid = np.zeros(8), np.zeros(8, dtype=bool)
    ranges[3], valid[3] = contact + offset, True
    result = probe_synthetic_ray_witness(
        ranges, valid, speed=0.6, config=config, synthetic_test_only=True
    )
    assert result["status"] == status


def test_synthetic_ray_probe_missing_mask_cannot_create_origin_witness():
    from sim.navigation import probe_synthetic_ray_witness

    result = probe_synthetic_ray_witness(
        np.zeros(8),
        np.zeros(8, dtype=bool),
        speed=0.6,
        config=Config(noise_std=0, latency_ticks=0),
        synthetic_test_only=True,
    )
    assert result["status"] == "unknown" and result["witness_columns"] == []


@pytest.mark.parametrize(
    "settings,reason",
    [
        ({"config": Config(noise_std=0)}, "registration_unqualified"),
        ({"tof_age_s": 0.1}, "registration_unqualified"),
        ({"turn_rate": 0.1}, "curved_reference_not_supported"),
    ],
)
def test_synthetic_ray_probe_unqualified_assumptions_abstain(settings, reason):
    from sim.navigation import probe_synthetic_ray_witness

    arguments = {
        "speed": 0.6,
        "config": Config(noise_std=0, latency_ticks=0),
        "synthetic_test_only": True,
        **settings,
    }
    result = probe_synthetic_ray_witness(
        np.full(8, 0.3), np.ones(8, dtype=bool), **arguments
    )
    assert result["status"] == "unknown" and result["reason"] == reason


@pytest.mark.parametrize("opt_in", [False, None, 1])
def test_synthetic_ray_probe_requires_explicit_scope_before_reading_inputs(opt_in):
    from sim.navigation import probe_synthetic_ray_witness

    with pytest.raises(ValueError, match="synthetic-test-only"):
        probe_synthetic_ray_witness(
            object(), object(), speed=0.6, synthetic_test_only=opt_in
        )


@pytest.mark.parametrize(
    "defect",
    [
        "speed",
        "bool_speed",
        "age",
        "turn",
        "shape",
        "bool_ranges",
        "nonfinite",
        "range",
        "mask",
        "invalid_padding",
    ],
)
def test_synthetic_ray_probe_rejects_malformed_artificial_input(defect):
    from sim.navigation import probe_synthetic_ray_witness

    ranges, valid = np.full(8, 0.3), np.ones(8, dtype=bool)
    settings = {
        "speed": 0.6,
        "config": Config(noise_std=0, latency_ticks=0),
        "synthetic_test_only": True,
    }
    if defect == "speed":
        settings["speed"] = 1
    elif defect == "bool_speed":
        settings["speed"] = True
    elif defect == "age":
        settings["tof_age_s"] = -1
    elif defect == "turn":
        settings["turn_rate"] = float("nan")
    elif defect == "shape":
        ranges = np.full((8, 8), 0.3)
    elif defect == "bool_ranges":
        ranges = np.ones(8, dtype=bool)
    elif defect == "nonfinite":
        ranges[0] = float("inf")
    elif defect == "range":
        ranges[0] = 5
    elif defect == "mask":
        valid = np.ones(8)
    else:
        valid[0] = False
    with pytest.raises(ValueError):
        probe_synthetic_ray_witness(ranges, valid, **settings)


def test_synthetic_ray_probe_saturation_inside_footprint_is_not_a_surface_hit():
    from sim.navigation import probe_synthetic_ray_witness

    config = Config(noise_std=0, latency_ticks=0, max_range=0.3)
    result = probe_synthetic_ray_witness(
        np.full(8, config.max_range),
        np.ones(8, dtype=bool),
        speed=0.6,
        config=config,
        synthetic_test_only=True,
    )
    assert result["status"] == "unknown" and result["witness_columns"] == []


def test_synthetic_ray_probe_unresolved_numerical_scale_abstains():
    from sim.navigation import probe_synthetic_ray_witness

    config = Config(noise_std=0, latency_ticks=0, radius=1e-16)
    result = probe_synthetic_ray_witness(
        np.full(8, 0.3),
        np.ones(8, dtype=bool),
        speed=0.6,
        config=config,
        synthetic_test_only=True,
    )
    assert result["status"] == "unknown" and result["reason"] == "numerical_unknown"


@pytest.mark.parametrize(
    "error,status",
    [(0.0, "blocked_witness"), (0.01, "blocked_witness"), (0.2, "unknown")],
)
def test_bounded_ray_probe_uncertainty_can_remove_but_not_create_witnesses(
    error, status
):
    from sim.navigation import probe_synthetic_bounded_ray_witness

    ranges, valid = np.zeros(8), np.zeros(8, dtype=bool)
    ranges[3], valid[3] = 0.3, True
    result = probe_synthetic_bounded_ray_witness(
        ranges,
        valid,
        speed=0.6,
        range_error_m=error,
        translation_error_m=error,
        heading_error_rad=error,
        config=Config(noise_std=0, latency_ticks=0),
        synthetic_test_only=True,
    )
    assert result["status"] == status
    assert result["witness_columns"] == ([3] if status == "blocked_witness" else [])
    assert result["synthetic"] and not result["training_approved"]
    assert not result["real_input_qualified"] and not result["physical_safety_claim"]
    json.dumps(result, allow_nan=False)


def test_bounded_ray_probe_does_not_qualify_normal_defaults():
    from sim.navigation import probe_synthetic_bounded_ray_witness

    result = probe_synthetic_bounded_ray_witness(
        np.full(8, 0.3),
        np.ones(8, dtype=bool),
        speed=0.6,
        range_error_m=0.01,
        translation_error_m=0.01,
        heading_error_rad=0.01,
        synthetic_test_only=True,
    )
    assert (
        result["status"] == "unknown" and result["reason"] == "noise_model_unqualified"
    )


@pytest.fixture
def bounded_ray_fixture():
    ranges, valid = np.zeros(8), np.zeros(8, dtype=bool)
    ranges[3], valid[3] = 0.3, True
    return (
        ranges,
        valid,
        {
            "speed": 0.6,
            "range_error_m": 0.01,
            "translation_error_m": 0.01,
            "heading_error_rad": 0.01,
            "config": Config(noise_std=0, latency_ticks=0),
            "synthetic_test_only": True,
        },
    )


def test_bounded_ray_probe_sampled_perturbations_respect_error_ball_and_footprint(
    bounded_ray_fixture,
):
    from sim.navigation import probe_synthetic_bounded_ray_witness

    ranges, valid, settings = bounded_ray_fixture
    original = deepcopy((ranges, valid, settings))
    result = probe_synthetic_bounded_ray_witness(ranges, valid, **settings)
    assert result["status"] == "blocked_witness"
    angle = np.linspace(
        settings["config"].field_of_view / 2, -settings["config"].field_of_view / 2, 8
    )[3]
    nominal = ranges[3] * np.array([math.cos(angle), math.sin(angle)])
    distance = settings["speed"] * settings["config"].dt + settings["speed"] ** 2 / (
        2 * settings["config"].acceleration
    )
    for radial in (-settings["range_error_m"], 0, settings["range_error_m"]):
        for heading in (
            -settings["heading_error_rad"],
            0,
            settings["heading_error_rad"],
        ):
            for direction in np.linspace(0, 2 * math.pi, 8, endpoint=False):
                translation = settings["translation_error_m"] * np.array(
                    [math.cos(direction), math.sin(direction)]
                )
                point = (ranges[3] + radial) * np.array(
                    [math.cos(angle + heading), math.sin(angle + heading)]
                ) + translation
                assert (
                    np.linalg.norm(point - nominal)
                    <= result["point_error_bound_m"][3] + 1e-12
                )
                assert (
                    math.hypot(point[0] - np.clip(point[0], 0, distance), point[1])
                    < settings["config"].radius
                )
    np.testing.assert_array_equal(ranges, original[0])
    np.testing.assert_array_equal(valid, original[1])
    assert settings == original[2]
    result["assumed_error_bounds"]["range_error_m"] = 1
    assert settings == original[2]


@pytest.mark.parametrize(
    "field,value",
    [("range_error_m", 0.2), ("translation_error_m", 0.2), ("heading_error_rad", 1.0)],
)
def test_bounded_ray_probe_each_error_component_can_remove_a_witness(
    bounded_ray_fixture, field, value
):
    from sim.navigation import probe_synthetic_bounded_ray_witness

    ranges, valid, settings = bounded_ray_fixture
    result = probe_synthetic_bounded_ray_witness(
        ranges, valid, **{**settings, field: value}
    )
    assert result["status"] == "unknown" and result["witness_columns"] == []


@pytest.mark.parametrize(
    "offset,status", [(-1e-6, "blocked_witness"), (0, "unknown"), (1e-6, "unknown")]
)
def test_bounded_ray_probe_error_ball_contact_abstains(
    bounded_ray_fixture, offset, status
):
    from sim.navigation import probe_synthetic_bounded_ray_witness

    ranges, valid, settings = bounded_ray_fixture
    angle = np.linspace(
        settings["config"].field_of_view / 2, -settings["config"].field_of_view / 2, 8
    )[3]
    distance = settings["speed"] * settings["config"].dt + settings["speed"] ** 2 / (
        2 * settings["config"].acceleration
    )
    separation = math.hypot(
        ranges[3] * math.cos(angle) - distance, ranges[3] * math.sin(angle)
    )
    result = probe_synthetic_bounded_ray_witness(
        ranges,
        valid,
        **{
            **settings,
            "range_error_m": 0,
            "heading_error_rad": 0,
            "translation_error_m": settings["config"].radius - separation + offset,
        },
    )
    assert result["status"] == status


@pytest.mark.parametrize("radial_error", [0.05, 0.3])
def test_bounded_ray_probe_unsupported_range_interval_stays_unknown(
    bounded_ray_fixture, radial_error
):
    from sim.navigation import probe_synthetic_bounded_ray_witness

    ranges, valid, settings = bounded_ray_fixture
    result = probe_synthetic_bounded_ray_witness(
        ranges,
        valid,
        **{
            **settings,
            "range_error_m": radial_error,
            "config": Config(noise_std=0, latency_ticks=0, max_range=0.35),
        },
    )
    assert result["status"] == "unknown" and result["witness_columns"] == []


@pytest.mark.parametrize(
    "field,value",
    [
        ("range_error_m", -0.1),
        ("range_error_m", True),
        ("range_error_m", float("nan")),
        ("range_error_m", 10**400),
        ("range_error_m", -(10**400)),
        ("translation_error_m", None),
        ("translation_error_m", -0.1),
        ("translation_error_m", float("inf")),
        ("translation_error_m", 10**400),
        ("translation_error_m", -(10**400)),
        ("heading_error_rad", math.pi + 1e-6),
        ("heading_error_rad", -0.1),
        ("heading_error_rad", False),
        ("heading_error_rad", 10**400),
        ("heading_error_rad", -(10**400)),
    ],
)
def test_bounded_ray_probe_rejects_invalid_assumed_bounds(
    bounded_ray_fixture, field, value
):
    from sim.navigation import probe_synthetic_bounded_ray_witness

    ranges, valid, settings = bounded_ray_fixture
    with pytest.raises(ValueError):
        probe_synthetic_bounded_ray_witness(ranges, valid, **{**settings, field: value})


def test_bounded_ray_probe_scope_checked_before_inputs(bounded_ray_fixture):
    from sim.navigation import probe_synthetic_bounded_ray_witness

    _, _, settings = bounded_ray_fixture
    with pytest.raises(ValueError, match="synthetic-test-only"):
        probe_synthetic_bounded_ray_witness(
            object(), object(), **{**settings, "synthetic_test_only": 1}
        )


@pytest.mark.parametrize(
    "override,reason",
    [
        ({"config": Config(noise_std=0)}, "registration_unqualified"),
        ({"tof_age_s": 0.1}, "registration_unqualified"),
        ({"turn_rate": 0.1}, "curved_reference_not_supported"),
    ],
)
def test_bounded_ray_probe_cannot_override_unqualified_assumptions(
    bounded_ray_fixture, override, reason
):
    from sim.navigation import probe_synthetic_bounded_ray_witness

    ranges, valid, settings = bounded_ray_fixture
    result = probe_synthetic_bounded_ray_witness(
        ranges, valid, **{**settings, **override}
    )
    assert result["status"] == "unknown" and result["reason"] == reason


@pytest.fixture
def registration_fixture():
    return {
        "points": [[1.0, 0.0], [0.0, 1.0]],
        "sensor_pose": [0.0, 0.0, 0.0],
        "acquisition_pose": [0.0, 0.0, 0.0],
        "reference_pose": [0.0, 0.0, 0.0],
        "acquisition_time_s": 1.0,
        "reference_time_s": 1.1,
        "synthetic_test_only": True,
    }


@pytest.mark.parametrize(
    "poses,expected",
    [
        ({}, [[1, 0], [0, 1]]),
        ({"sensor_pose": [0.25, -0.5, 0]}, [[1.25, -0.5], [0.25, 0.5]]),
        ({"reference_pose": [1, 0, 0]}, [[0, 0], [-1, 1]]),
        ({"reference_pose": [0, 0, math.pi / 2]}, [[0, -1], [1, 0]]),
        ({"acquisition_pose": [0, 0, math.pi / 2]}, [[0, 1], [-1, 0]]),
        (
            {
                "sensor_pose": [0.5, 0, math.pi / 2],
                "acquisition_pose": [2, 4, 0],
                "reference_pose": [2, 3, math.pi / 2],
            },
            [[2, -0.5], [1, 0.5]],
        ),
    ],
)
def test_registration_reference_analytic_fixtures(
    registration_fixture, poses, expected
):
    from sim.navigation import register_synthetic_points

    result = register_synthetic_points(**{**registration_fixture, **poses})
    assert result["status"] == "registered_fixture"
    np.testing.assert_allclose(result["reference_points_m"], expected, atol=1e-14)
    assert result["elapsed_s"] == pytest.approx(0.1)
    assert result["synthetic"] and not result["training_approved"]
    assert not result["real_input_qualified"] and not result["physical_safety_claim"]
    assert all(result["assumptions"].values())
    assert "labels" not in result and "witness_columns" not in result
    json.dumps(result, allow_nan=False)


def test_registration_reference_composition_and_inverse(registration_fixture):
    from sim.navigation import register_synthetic_points

    first, middle, last = [1, 2, 0.3], [-1, 3, -0.4], [2, -2, 0.8]
    first_to_middle = register_synthetic_points(
        **{**registration_fixture, "acquisition_pose": first, "reference_pose": middle}
    )
    composed = register_synthetic_points(
        **{
            **registration_fixture,
            "points": first_to_middle["reference_points_m"],
            "acquisition_pose": middle,
            "reference_pose": last,
        }
    )
    direct = register_synthetic_points(
        **{**registration_fixture, "acquisition_pose": first, "reference_pose": last}
    )
    np.testing.assert_allclose(
        composed["reference_points_m"], direct["reference_points_m"], atol=1e-14
    )
    inverse = register_synthetic_points(
        **{
            **registration_fixture,
            "points": first_to_middle["reference_points_m"],
            "acquisition_pose": middle,
            "reference_pose": first,
        }
    )
    np.testing.assert_allclose(
        inverse["reference_points_m"], registration_fixture["points"], atol=1e-14
    )


def test_registration_reference_common_large_offset_preserves_local_points(
    registration_fixture,
):
    from sim.navigation import register_synthetic_points

    result = register_synthetic_points(
        **{
            **registration_fixture,
            "points": [[0.125, -0.25]],
            "sensor_pose": [0.25, 0.5, 0],
            "acquisition_pose": [1e16, -1e16, 0],
            "reference_pose": [1e16, -1e16, 0],
        }
    )
    np.testing.assert_array_equal(result["reference_points_m"], [[0.375, 0.25]])


@pytest.mark.parametrize("heading", [1e16, -1e16])
def test_registration_reference_large_heading_matches_bounded_orientation(
    registration_fixture, heading
):
    from sim.navigation import register_synthetic_points

    poses = {
        "sensor_pose": [0.5, -0.25, heading],
        "acquisition_pose": [1, 2, -heading],
        "reference_pose": [2, 3, heading],
    }
    actual = register_synthetic_points(**{**registration_fixture, **poses})
    bounded = {
        name: [*pose[:2], math.atan2(math.sin(pose[2]), math.cos(pose[2]))]
        for name, pose in poses.items()
    }
    expected = register_synthetic_points(**{**registration_fixture, **bounded})
    np.testing.assert_allclose(
        actual["reference_points_m"], expected["reference_points_m"], atol=1e-14
    )


@pytest.mark.parametrize(
    "field,reason",
    [
        ("acquisition_time_s", "missing_timing"),
        ("reference_time_s", "missing_timing"),
        ("sensor_pose", "missing_pose"),
        ("acquisition_pose", "missing_pose"),
        ("reference_pose", "missing_pose"),
    ],
)
def test_registration_reference_missing_evidence_stays_unknown(
    registration_fixture, field, reason
):
    from sim.navigation import register_synthetic_points

    result = register_synthetic_points(**{**registration_fixture, field: None})
    assert result["status"] == "unknown" and result["reason"] == reason
    assert result["reference_points_m"] is None
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize(
    "field,value",
    [
        ("points", [[True, 0]]),
        ("points", [[1, float("nan")]]),
        ("points", [[1, 2, 3]]),
        ("points", [1, 2]),
        ("points", []),
        ("sensor_pose", [0, 0]),
        ("sensor_pose", [0, 0, float("inf")]),
        ("acquisition_pose", [0, True, 0]),
        ("reference_pose", [0, 0, "0"]),
        ("acquisition_time_s", True),
        ("acquisition_time_s", -1),
        ("reference_time_s", float("nan")),
        ("reference_time_s", float("inf")),
        ("reference_time_s", "1.1"),
        ("reference_time_s", 0.5),
        ("points", [[10**400, 0]]),
        ("points", [[-(10**400), 0]]),
        ("sensor_pose", [0, 0, 10**400]),
        ("acquisition_pose", [10**400, 0, 0]),
        ("reference_pose", [-(10**400), 0, 0]),
        ("acquisition_time_s", 10**400),
        ("reference_time_s", 10**400),
    ],
)
def test_registration_reference_rejects_invalid_evidence(
    registration_fixture, field, value
):
    from sim.navigation import register_synthetic_points

    with pytest.raises(ValueError):
        register_synthetic_points(**{**registration_fixture, field: value})


@pytest.mark.parametrize("opt_in", [False, None, 1, "yes"])
def test_registration_reference_requires_scope_before_inputs(
    registration_fixture, opt_in
):
    from sim.navigation import register_synthetic_points

    with pytest.raises(ValueError, match="synthetic-test-only"):
        register_synthetic_points(
            **{
                **registration_fixture,
                "points": object(),
                "synthetic_test_only": opt_in,
            }
        )


def test_registration_reference_numerical_overflow_stays_unknown(registration_fixture):
    from sim.navigation import register_synthetic_points

    result = register_synthetic_points(
        **{
            **registration_fixture,
            "acquisition_pose": [1e308, 0, 0],
            "reference_pose": [-1e308, 0, 0],
        }
    )
    assert result["status"] == "unknown" and result["reason"] == "numerical_unknown"
    assert result["reference_points_m"] is None
    json.dumps(result, allow_nan=False)


def test_registration_reference_is_detached_and_does_not_qualify_witnesses(
    registration_fixture, bounded_ray_fixture
):
    from sim.navigation import (
        probe_synthetic_bounded_ray_witness,
        register_synthetic_points,
    )

    original = deepcopy(registration_fixture)
    result = register_synthetic_points(**registration_fixture)
    result["reference_points_m"][0][0] = 100
    result["assumptions"]["static_world"] = False
    assert registration_fixture == original
    ranges, valid, settings = bounded_ray_fixture
    for override, reason in (
        ({"config": Config()}, "noise_model_unqualified"),
        ({"config": Config(noise_std=0)}, "registration_unqualified"),
        ({"tof_age_s": 0.1}, "registration_unqualified"),
        ({"turn_rate": 0.1}, "curved_reference_not_supported"),
    ):
        probe = probe_synthetic_bounded_ray_witness(
            ranges, valid, **{**settings, **override}
        )
        assert probe["status"] == "unknown" and probe["reason"] == reason


@pytest.fixture
def bounded_registration_fixture(registration_fixture):
    return {
        **registration_fixture,
        "point_error_m": 0.0,
        "pose_error_bounds": {
            name: {"translation_m": 0.0, "heading_rad": 0.0}
            for name in ("sensor_pose", "acquisition_pose", "reference_pose")
        },
    }


def test_bounded_registration_zero_errors_match_exact_reference(
    bounded_registration_fixture,
):
    from sim.navigation import register_synthetic_bounded_points

    result = register_synthetic_bounded_points(**bounded_registration_fixture)
    assert result["status"] == "bounded_fixture"
    assert result["reference_points_m"] == bounded_registration_fixture["points"]
    assert result["point_error_bound_m"] == [0.0, 0.0]
    assert not result["floating_point_certified"]
    assert result["bound_semantics"] == "assumed_model_exact_arithmetic"
    assert result["synthetic"] and not result["training_approved"]
    assert not result["real_input_qualified"] and not result["physical_safety_claim"]
    assert "labels" not in result and "witness_columns" not in result
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize(
    "pose,field",
    [(None, "point_error_m")]
    + [
        (name, field)
        for name in ("sensor_pose", "acquisition_pose", "reference_pose")
        for field in ("translation_m", "heading_rad")
    ],
)
def test_bounded_registration_each_component_has_analytic_effect(
    bounded_registration_fixture, pose, field
):
    from sim.navigation import register_synthetic_bounded_points

    settings = deepcopy(bounded_registration_fixture)
    if pose is None:
        settings[field] = 0.1
    else:
        settings["pose_error_bounds"][pose][field] = 0.1
    result = register_synthetic_bounded_points(**settings)
    expected = 2 * math.sin(0.05) if field == "heading_rad" else 0.1
    np.testing.assert_allclose(result["point_error_bound_m"], [expected, expected])


def test_bounded_registration_heading_errors_use_distinct_lever_arms(
    bounded_registration_fixture,
):
    from sim.navigation import register_synthetic_bounded_points

    settings = deepcopy(bounded_registration_fixture)
    settings.update(
        points=[[1, 0]],
        sensor_pose=[0.5, 0, 0],
        acquisition_pose=[1, 0, 0],
        point_error_m=0.01,
    )
    for name, translation, heading in (
        ("sensor_pose", 0.02, 0.01),
        ("acquisition_pose", 0.03, 0.02),
        ("reference_pose", 0.04, 0.03),
    ):
        settings["pose_error_bounds"][name] = {
            "translation_m": translation,
            "heading_rad": heading,
        }
    result = register_synthetic_bounded_points(**settings)
    expected = 0.1 + 2 * math.sin(0.005) + 3 * math.sin(0.01) + 5 * math.sin(0.015)
    assert result["reference_points_m"] == [[2.5, 0.0]]
    assert result["point_error_bound_m"] == pytest.approx([expected])
    assert "exact_fixture_poses" not in result["assumptions"]
    assert result["assumptions"]["bounded_point_and_pose_errors"]


def test_bounded_registration_sampled_perturbations_fit_declared_enclosure(
    bounded_registration_fixture,
):
    from itertools import product

    from sim.navigation import register_synthetic_bounded_points

    settings = deepcopy(bounded_registration_fixture)
    settings.update(
        points=[[1, 0.5], [-0.4, 0.2]],
        sensor_pose=[0.3, -0.2, 0.4],
        acquisition_pose=[1, 2, -0.3],
        reference_pose=[-2, 0.5, 0.6],
        point_error_m=0.01,
    )
    names = ("sensor_pose", "acquisition_pose", "reference_pose")
    for index, name in enumerate(names):
        settings["pose_error_bounds"][name] = {
            "translation_m": 0.02 + 0.01 * index,
            "heading_rad": 0.01 + 0.01 * index,
        }
    original = deepcopy(settings)
    result = register_synthetic_bounded_points(**settings)

    def transform(point, pose):
        cosine, sine = math.cos(pose[2]), math.sin(pose[2])
        return np.array(
            [
                cosine * point[0] - sine * point[1] + pose[0],
                sine * point[0] + cosine * point[1] + pose[1],
            ]
        )

    checked = 0
    for heading_signs in product((-1, 0, 1), repeat=3):
        for direction, point_direction in product(range(4), repeat=2):
            perturbed = {}
            for index, name in enumerate(names):
                pose, errors = settings[name], settings["pose_error_bounds"][name]
                angle = (direction + index) * math.pi / 2
                perturbed[name] = [
                    pose[0] + errors["translation_m"] * math.cos(angle),
                    pose[1] + errors["translation_m"] * math.sin(angle),
                    pose[2] + heading_signs[index] * errors["heading_rad"],
                ]
            angle = point_direction * math.pi / 2
            for index, point in enumerate(settings["points"]):
                displaced = np.asarray(point) + settings["point_error_m"] * np.array(
                    [math.cos(angle), math.sin(angle)]
                )
                body = transform(displaced, perturbed["sensor_pose"])
                world = transform(body, perturbed["acquisition_pose"])
                reference = perturbed["reference_pose"]
                relative = world - reference[:2]
                actual = transform(relative, [0, 0, -reference[2]])
                separation = np.linalg.norm(
                    actual - result["reference_points_m"][index]
                )
                assert separation <= result["point_error_bound_m"][index] + 1e-12
                checked += 1
    assert checked == 864
    assert settings == original
    result["assumed_error_bounds"]["point_error_m"] = 100
    result["reference_points_m"][0][0] = 100
    assert settings == original


@pytest.mark.parametrize(
    "defect",
    [
        "missing_pose",
        "extra_pose",
        "missing_component",
        "extra_component",
        "wrong_container",
        "wrong_row",
        "negative_point",
        "boolean_point",
        "overflow_point",
        "nan_translation",
        "overflow_translation",
        "boolean_translation",
        "infinite_heading",
        "negative_heading",
        "large_heading",
    ],
)
def test_bounded_registration_rejects_malformed_bounds(
    bounded_registration_fixture, defect
):
    from sim.navigation import register_synthetic_bounded_points

    settings = deepcopy(bounded_registration_fixture)
    rows = settings["pose_error_bounds"]
    if defect == "missing_pose":
        del rows["reference_pose"]
    elif defect == "extra_pose":
        rows["extra"] = rows["reference_pose"].copy()
    elif defect == "missing_component":
        del rows["sensor_pose"]["heading_rad"]
    elif defect == "extra_component":
        rows["sensor_pose"]["extra"] = 0
    elif defect == "wrong_container":
        settings["pose_error_bounds"] = []
    elif defect == "wrong_row":
        rows["sensor_pose"] = []
    elif defect.endswith("point"):
        settings["point_error_m"] = {
            "negative_point": -0.1,
            "boolean_point": True,
            "overflow_point": 10**400,
        }[defect]
    elif defect.endswith("translation"):
        rows["sensor_pose"]["translation_m"] = {
            "nan_translation": float("nan"),
            "overflow_translation": 10**400,
            "boolean_translation": False,
        }[defect]
    else:
        rows["reference_pose"]["heading_rad"] = {
            "infinite_heading": float("inf"),
            "negative_heading": -0.1,
            "large_heading": math.pi + 1e-6,
        }[defect]
    with pytest.raises(ValueError):
        register_synthetic_bounded_points(**settings)


@pytest.mark.parametrize("field", ["acquisition_time_s", "reference_pose"])
def test_bounded_registration_missing_nominal_evidence_stays_unknown(
    bounded_registration_fixture, field
):
    from sim.navigation import register_synthetic_bounded_points

    result = register_synthetic_bounded_points(
        **{**bounded_registration_fixture, field: None}
    )
    assert result["status"] == "unknown"
    assert (
        result["reference_points_m"] is None and result["point_error_bound_m"] is None
    )
    json.dumps(result, allow_nan=False)


def test_bounded_registration_nonfinite_enclosure_stays_unknown(
    bounded_registration_fixture,
):
    from sim.navigation import register_synthetic_bounded_points

    settings = deepcopy(bounded_registration_fixture)
    for row in settings["pose_error_bounds"].values():
        row["translation_m"] = 1e308
    result = register_synthetic_bounded_points(**settings)
    assert result["status"] == "unknown" and result["reason"] == "numerical_unknown"
    assert (
        result["reference_points_m"] is None and result["point_error_bound_m"] is None
    )
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("opt_in", [False, 1])
def test_bounded_registration_checks_scope_before_inputs(
    bounded_registration_fixture, opt_in
):
    from sim.navigation import register_synthetic_bounded_points

    with pytest.raises(ValueError, match="synthetic-test-only"):
        register_synthetic_bounded_points(
            **{
                **bounded_registration_fixture,
                "points": object(),
                "synthetic_test_only": opt_in,
            }
        )


@pytest.fixture
def registered_witness_fixture(bounded_registration_fixture):
    return {
        **deepcopy(bounded_registration_fixture),
        "points": [[0.3, 0.0]],
        "point_error_m": 0.01,
        "speed": 0.6,
        "assume_obstacle_points": True,
        "config": Config(noise_std=0, latency_ticks=0),
    }


@pytest.mark.parametrize(
    "point,error,status",
    [
        ([0.3, 0], 0.01, "blocked_witness"),
        ([0.3, 0], 0.1, "unknown"),
        ([1, 1], 0.01, "unknown"),
    ],
)
def test_registered_witness_requires_entire_error_ball_inside(
    registered_witness_fixture, point, error, status
):
    from sim.navigation import probe_synthetic_registered_witness

    result = probe_synthetic_registered_witness(
        **{**registered_witness_fixture, "points": [point], "point_error_m": error}
    )
    assert result["status"] == status
    assert result["witness_indices"] == ([0] if status == "blocked_witness" else [])
    assert result["braking_distance_m"] == pytest.approx(0.21)
    assert result["synthetic"] and not result["training_approved"]
    assert not result["real_input_qualified"] and not result["physical_safety_claim"]
    assert not result["floating_point_certified"]
    assert "labels" not in result and "path_blocked" not in result
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize(
    "offset,status", [(-1e-6, "blocked_witness"), (0, "unknown"), (1e-6, "unknown")]
)
def test_registered_witness_error_ball_contact_abstains(
    registered_witness_fixture, offset, status
):
    from sim.navigation import probe_synthetic_registered_witness

    result = probe_synthetic_registered_witness(
        **{**registered_witness_fixture, "points": [[0.1, 0.17 + offset]]}
    )
    assert result["status"] == status


@pytest.mark.parametrize(
    "override,reason",
    [
        ({"assume_obstacle_points": False}, "obstacle_membership_unqualified"),
        ({"config": None}, "noise_model_unqualified"),
        ({"config": Config(noise_std=0)}, "registration_unqualified"),
        ({"turn_rate": 0.1}, "curved_reference_not_supported"),
        ({"reference_pose": None}, "missing_pose"),
        ({"acquisition_time_s": None}, "missing_timing"),
    ],
)
def test_registered_witness_unsupported_evidence_stays_unknown(
    registered_witness_fixture, override, reason
):
    from sim.navigation import probe_synthetic_registered_witness

    result = probe_synthetic_registered_witness(
        **{**registered_witness_fixture, **override}
    )
    assert result["status"] == "unknown" and result["reason"] == reason
    assert result["witness_indices"] == []
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize(
    "field,value,exception",
    [
        ("speed", -0.1, ValueError),
        ("speed", 0.7, ValueError),
        ("speed", True, TypeError),
        ("speed", float("nan"), ValueError),
        ("speed", 10**400, ValueError),
        ("turn_rate", 2.0, ValueError),
        ("turn_rate", float("inf"), ValueError),
        ("turn_rate", False, TypeError),
        ("assume_obstacle_points", 1, TypeError),
        ("assume_obstacle_points", None, TypeError),
        ("assume_obstacle_points", "yes", TypeError),
    ],
)
def test_registered_witness_rejects_malformed_motion_or_membership(
    registered_witness_fixture, field, value, exception
):
    from sim.navigation import probe_synthetic_registered_witness

    with pytest.raises(exception):
        probe_synthetic_registered_witness(
            **{**registered_witness_fixture, field: value}
        )


@pytest.mark.parametrize("opt_in", [False, 1])
def test_registered_witness_scope_precedes_inputs(registered_witness_fixture, opt_in):
    from sim.navigation import probe_synthetic_registered_witness

    with pytest.raises(ValueError, match="synthetic-test-only"):
        probe_synthetic_registered_witness(
            **{
                **registered_witness_fixture,
                "points": object(),
                "synthetic_test_only": opt_in,
            }
        )


def test_registered_witness_one_positive_survives_other_unknown_points(
    registered_witness_fixture,
):
    from sim.navigation import probe_synthetic_registered_witness

    result = probe_synthetic_registered_witness(
        **{**registered_witness_fixture, "points": [[1e16, 0], [0.3, 0]]}
    )
    assert result["status"] == "blocked_witness" and result["witness_indices"] == [1]
    unknown = probe_synthetic_registered_witness(
        **{**registered_witness_fixture, "points": [[1e16, 0]]}
    )
    assert unknown["status"] == "unknown" and unknown["reason"] == "numerical_unknown"


@pytest.mark.parametrize(
    "point,obstacles,collision,status",
    [
        ([0.4, 0], ((3.4, 3, 0.001),), True, "blocked_witness"),
        ([1.1, 1], ((4.1, 4, 0.001),), False, "unknown"),
        ([1.1, 1], ((4.1, 4, 0.001), (3.4, 3, 0.001)), True, "unknown"),
    ],
)
def test_registered_witness_independent_world_geometry(
    registered_witness_fixture, point, obstacles, collision, status
):
    from sim.navigation import probe_synthetic_registered_witness

    settings = {
        **registered_witness_fixture,
        "points": [point],
        "acquisition_pose": [3, 3, 0],
        "reference_pose": [3.1, 3, 0],
    }
    result = probe_synthetic_registered_witness(**settings)
    config = settings["config"]
    distance = settings["speed"] * config.dt + settings["speed"] ** 2 / (
        2 * config.acceleration
    )
    assert (
        swept_collision((3.1, 3), (3.1 + distance, 3), config.radius, obstacles, (6, 6))
        is collision
    )
    assert result["status"] == status
    assert result["acquisition_time_s"] < result["reference_time_s"]
    np.testing.assert_allclose(
        result["reference_points_m"], [[point[0] - 0.1, point[1]]]
    )


@pytest.mark.parametrize("heading", [-math.pi / 3, 0, math.pi / 3])
def test_registered_witness_perturbed_world_points_all_collide(
    registered_witness_fixture, heading
):
    from itertools import product

    from sim.navigation import probe_synthetic_registered_witness

    settings = deepcopy(registered_witness_fixture)
    settings.update(
        points=[[0.35, 0]],
        point_error_m=0.003,
        sensor_pose=[0.05, 0, 0.1],
        acquisition_pose=[3, 3, heading],
        reference_pose=[
            3 + 0.1 * math.cos(heading),
            3 + 0.1 * math.sin(heading),
            heading,
        ],
    )
    names = ("sensor_pose", "acquisition_pose", "reference_pose")
    for name in names:
        settings["pose_error_bounds"][name] = {
            "translation_m": 0.002,
            "heading_rad": 0.003,
        }
    result = probe_synthetic_registered_witness(**settings)
    assert result["status"] == "blocked_witness" and result["witness_indices"] == [0]
    config = settings["config"]
    distance = settings["speed"] * config.dt + settings["speed"] ** 2 / (
        2 * config.acceleration
    )

    def transform(point, pose):
        cosine, sine = math.cos(pose[2]), math.sin(pose[2])
        return np.array(
            [
                point[0] * cosine - point[1] * sine + pose[0],
                point[0] * sine + point[1] * cosine + pose[1],
            ]
        )

    checked = 0
    for signs in product((-1, 0, 1), repeat=3):
        for direction, point_direction in product(range(8), range(4)):
            poses = {}
            for index, name in enumerate(names):
                pose = settings[name]
                angle = (direction + index) * math.pi / 4
                poses[name] = [
                    pose[0] + 0.002 * math.cos(angle),
                    pose[1] + 0.002 * math.sin(angle),
                    pose[2] + 0.003 * signs[index],
                ]
            angle = point_direction * math.pi / 2
            point = np.asarray(settings["points"][0]) + 0.003 * np.array(
                [math.cos(angle), math.sin(angle)]
            )
            body = transform(point, poses["sensor_pose"])
            world = transform(body, poses["acquisition_pose"])
            reference = poses["reference_pose"]
            actual = transform(world - reference[:2], [0, 0, -reference[2]])
            error = np.linalg.norm(actual - result["reference_points_m"][0])
            assert error <= result["point_error_bound_m"][0] + 1e-12
            start = np.asarray(reference[:2])
            end = start + distance * np.array(
                [math.cos(reference[2]), math.sin(reference[2])]
            )
            assert swept_collision(start, end, config.radius, ((*world, 1e-6),), (6, 6))
            checked += 1
    assert checked == 864


def test_registered_witness_association_is_required_by_default(
    registered_witness_fixture,
):
    from sim.navigation import probe_synthetic_registered_witness

    settings = dict(registered_witness_fixture)
    del settings["assume_obstacle_points"]
    result = probe_synthetic_registered_witness(**settings)
    assert (
        result["status"] == "unknown"
        and result["reason"] == "obstacle_membership_unqualified"
    )


def test_registered_witness_inputs_and_results_are_detached(registered_witness_fixture):
    from sim.navigation import probe_synthetic_registered_witness

    original = deepcopy(registered_witness_fixture)
    result = probe_synthetic_registered_witness(**registered_witness_fixture)
    result["reference_points_m"][0][0] = 100
    result["assumed_error_bounds"]["point_error_m"] = 100
    result["assumptions"]["obstacle_membership"] = False
    result["witness_indices"].clear()
    assert registered_witness_fixture == original
    assert probe_synthetic_registered_witness(**registered_witness_fixture)[
        "witness_indices"
    ] == [0]


def test_registered_witness_nonfinite_braking_distance_abstains(
    registered_witness_fixture,
):
    from sim.navigation import probe_synthetic_registered_witness

    result = probe_synthetic_registered_witness(
        **{
            **registered_witness_fixture,
            "speed": 1e308,
            "config": Config(max_speed=1e308, noise_std=0, latency_ticks=0),
        }
    )
    assert result["status"] == "unknown" and result["reason"] == "numerical_unknown"
    assert result["braking_distance_m"] is None
    json.dumps(result, allow_nan=False)


def test_registered_witness_invalid_config_is_rejected(registered_witness_fixture):
    from sim.navigation import probe_synthetic_registered_witness

    with pytest.raises(TypeError, match="Config"):
        probe_synthetic_registered_witness(
            **{**registered_witness_fixture, "config": object()}
        )


def test_registered_witness_cannot_bypass_registration_bound_validation(
    registered_witness_fixture,
):
    from sim.navigation import probe_synthetic_registered_witness

    settings = deepcopy(registered_witness_fixture)
    settings["pose_error_bounds"]["reference_pose"]["heading_rad"] = float("nan")
    with pytest.raises(ValueError):
        probe_synthetic_registered_witness(**settings)


@pytest.mark.parametrize("axis", [0, 1])
def test_registered_witness_source_cancellation_cannot_create_positive(
    registered_witness_fixture, axis
):
    from fractions import Fraction

    from sim.navigation import probe_synthetic_registered_witness

    point, mounting, reference = [0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]
    point[axis], mounting[axis], reference[axis] = 1e16, 1.0, 1e16
    exact = Fraction(point[axis]) + Fraction(mounting[axis]) - Fraction(reference[axis])
    assert exact == 1
    obstacle = [3.0, 3.0, 1e-6]
    obstacle[axis] += float(exact)
    assert not swept_collision((3, 3), (3.21, 3), 0.18, (obstacle,), (6, 6))
    result = probe_synthetic_registered_witness(
        **{
            **registered_witness_fixture,
            "points": [point],
            "sensor_pose": mounting,
            "reference_pose": reference,
            "point_error_m": 0.0,
        }
    )
    assert result["reference_points_m"] == [[0.0, 0.0]]
    assert result["status"] == "unknown" and result["reason"] == "numerical_unknown"
    assert result["witness_indices"] == []


@pytest.mark.parametrize(
    "point,status", [([0.1, 0], "blocked_witness"), ([0.3, 0], "unknown")]
)
def test_registered_witness_at_rest_uses_current_footprint_only(
    registered_witness_fixture, point, status
):
    from sim.navigation import probe_synthetic_registered_witness

    result = probe_synthetic_registered_witness(
        **{**registered_witness_fixture, "speed": 0.0, "points": [point]}
    )
    assert result["braking_distance_m"] == 0.0
    assert result["status"] == status


@pytest.fixture
def gaussian_draft_half_width():
    from statistics import NormalDist

    def half_width(failure_budget, maximum_draws):
        return -Config().noise_std * NormalDist().inv_cdf(
            failure_budget / (2 * maximum_draws)
        )

    return half_width


@pytest.mark.parametrize("failure_budget", [0.1, 0.01, 0.001])
@pytest.mark.parametrize("maximum_draws", [64, 512, 25664, 205312])
def test_gaussian_coverage_draft_union_bound_arithmetic(
    gaussian_draft_half_width, failure_budget, maximum_draws
):
    half_width = gaussian_draft_half_width(failure_budget, maximum_draws)
    marginal_failure = math.erfc(half_width / (Config().noise_std * math.sqrt(2)))
    assert marginal_failure > 0
    assert maximum_draws * marginal_failure == pytest.approx(failure_budget, rel=1e-12)


def test_gaussian_coverage_draft_budget_counts_and_monotonicity(
    gaussian_draft_half_width,
):
    from itertools import pairwise

    config = Config()
    budgets = [
        64,
        64 * config.history_ticks,
        64 * (config.max_ticks + 1),
        8 * 64 * (config.max_ticks + 1),
    ]
    assert budgets == [64, 512, 25664, 205312]
    widths = [gaussian_draft_half_width(0.01, count) for count in budgets]
    assert all(earlier < later for earlier, later in pairwise(widths))
    assert gaussian_draft_half_width(0.001, budgets[-1]) > widths[-1]


@pytest.mark.parametrize("failure_budget", [0.1, 0.01, 0.001])
def test_gaussian_coverage_draft_clipping_and_float32_surface_filter(
    gaussian_draft_half_width, failure_budget
):
    config = Config()
    error = gaussian_draft_half_width(failure_budget, 512)
    quantization = float(np.spacing(np.float32(config.max_range))) / 2
    for reference in (0.0, 0.001, 0.1, 2.0, 3.99, config.max_range):
        for fraction in (-1, -0.75, -0.25, 0, 0.25, 0.75, 1):
            observed = float(
                np.float32(np.clip(reference + fraction * error, 0, config.max_range))
            )
            assert abs(observed - reference) <= error + quantization + 1e-14
            if (
                observed - error - quantization > 0
                and observed + error + quantization < config.max_range
            ):
                assert 0 < reference < config.max_range


def test_gaussian_coverage_draft_masked_zero_has_no_surface_information():
    config = Config()
    observed = [
        float(np.where(False, reference, 0)) for reference in (0, 1, config.max_range)
    ]
    assert observed == [0, 0, 0]


def test_gaussian_coverage_draft_finite_interval_can_fail_outside_event(
    gaussian_draft_half_width,
):
    config = Config()
    error = gaussian_draft_half_width(0.01, 64)
    observed = float(np.float32(config.max_range - 2 * error))
    assert 0 < observed - error < observed + error < config.max_range
    assert abs(observed - config.max_range) > error
    assert math.erfc(2 * error / (config.noise_std * math.sqrt(2))) > 0


def test_gaussian_coverage_draft_rare_errors_do_not_bound_selected_precision(
    gaussian_draft_half_width,
):
    config = Config()
    error = gaussian_draft_half_width(0.01, 1)
    false_positive_probability = (
        math.erfc(error / (config.noise_std * math.sqrt(2))) / 2
    )
    selected_probability = false_positive_probability
    assert 0 < false_positive_probability < 0.01
    assert false_positive_probability / selected_probability == 1


def test_gaussian_coverage_draft_pointwise_budget_fails_after_selection(
    gaussian_draft_half_width,
):
    config = Config()
    maximum_draws = 64
    pointwise_width = gaussian_draft_half_width(0.01, 1)
    pointwise_failure = math.erfc(pointwise_width / (config.noise_std * math.sqrt(2)))
    joint_failure = -math.expm1(maximum_draws * math.log1p(-pointwise_failure))
    assert joint_failure > 0.4
    assert gaussian_draft_half_width(0.01, maximum_draws) > pointwise_width


@pytest.mark.parametrize(
    "config",
    [
        Config(),
        Config(latency_ticks=0),
        Config(noise_std=0, dropout=0, latency_ticks=1),
    ],
)
def test_sensor_diagnostic_trace_preserves_observations_and_rng(config):
    from sim.diagnostics import DiagnosticRoverEnv, diagnostic_sample

    plain, traced = RoverEnv(config), DiagnosticRoverEnv(config)
    plain_observation, plain_info = plain.reset(seed=20261019)
    observation, info = traced.reset(seed=20261019)
    actions = [(0.6, 0), (0.6, 0.4), (0.2, -0.3), (0, 0)]
    for action in actions:
        assert json.dumps(
            observation, default=json_value, sort_keys=True
        ) == json.dumps(plain_observation, default=json_value, sort_keys=True)
        assert json.dumps(info, default=json_value, sort_keys=True) == json.dumps(
            plain_info, default=json_value, sort_keys=True
        )
        assert traced.rng.bit_generator.state == plain.rng.bit_generator.state
        sample = diagnostic_sample(traced, observation)
        assert "diagnostic" not in observation and sample["diagnostic"]["privileged"]
        assert not sample["diagnostic"]["training_approved"]
        assert not sample["diagnostic"]["real_input_qualified"]
        assert not sample["diagnostic"]["physical_safety_claim"]
        if traced.tick < traced.config.latency_ticks:
            assert sample["diagnostic"]["status"] == "no_delivery"
        else:
            capture = sample["diagnostic"]["delivered_capture"]
            assert capture["tick"] == observation["tof_sample_tick"]
            assert capture["tick"] <= traced.tick - traced.config.latency_ticks
            assert sample["diagnostic"]["age_consistency_error_s"] == pytest.approx(0)
        plain_observation, plain_reward, plain_done, plain_timeout, plain_info = (
            plain.step(action)
        )
        observation, reward, done, timeout, info = traced.step(action)
        assert (reward, done, timeout) == (plain_reward, plain_done, plain_timeout)
    assert list(traced.capture_trace) == [0, 2, 3, 4]
    traced.reset(seed=20261019)
    assert list(traced.capture_trace) == [0]


def test_sensor_diagnostic_trace_noiseless_residual_and_detached_capture():
    from sim.diagnostics import DiagnosticRoverEnv, diagnostic_sample

    env = DiagnosticRoverEnv(
        Config(noise_std=0, dropout=0), make_scenario("obstacle", seed=1)
    )
    env.reset(seed=1)
    for _ in range(3):
        observation, *_ = env.step((0.6, 0))
    sample = diagnostic_sample(env, observation)
    diagnostic = sample["diagnostic"]
    residuals = [
        value
        for row in diagnostic["range_residual_m"]
        for value in row
        if value is not None
    ]
    assert residuals
    assert max(map(abs, residuals)) < 1e-6
    assert (
        max(
            value
            for value in diagnostic["unregistered_surface_displacement_m"]
            if value is not None
        )
        > 0
    )
    assert (
        max(
            value
            for value in diagnostic["noiseless_registration_roundtrip_error_m"]
            if value is not None
        )
        < 1e-12
    )
    diagnostic["delivered_capture"]["pose_m_rad"][0] = 100
    diagnostic["delivered_capture"]["noiseless_ranges_m"][0][0] = 100
    assert env.capture_trace[env.sensor_tick]["pose_m_rad"][0] != 100
    assert env.capture_trace[env.sensor_tick]["noiseless_ranges_m"][0][0] != 100
    json.dumps(sample, default=json_value, allow_nan=False)


def test_sensor_diagnostic_trace_rejects_mismatched_owner_or_tick():
    from sim.diagnostics import DiagnosticRoverEnv, diagnostic_sample

    env = DiagnosticRoverEnv()
    observation, _ = env.reset(seed=1)
    with pytest.raises(TypeError):
        diagnostic_sample(RoverEnv(), observation)
    with pytest.raises(ValueError):
        diagnostic_sample(env, {**observation, "tick": 1})


def test_sensor_diagnostic_collection_is_bounded_and_censored():
    from dataclasses import asdict

    from sim.diagnostics import collect_diagnostic_episode, summarize_diagnostics

    records, summary = collect_diagnostic_episode("obstacle", seed=20261019, ticks=3)
    assert records[0]["config"] == asdict(Config())
    assert (
        records[0]["reference_independence"]
        == "shared_simulator_geometry_and_ray_model"
    )
    assert not records[0]["task_labels"] and not records[0]["physical_metrology"]
    assert summary["ticks"] == 3 and summary["observations"] == 4
    assert summary["censored"] and not summary["environment_timeout"]
    assert not summary["success"] and not summary["collision"]
    statistics = summarize_diagnostics(records)
    assert (
        statistics["observations"] == 4 and statistics["no_delivery_observations"] == 2
    )
    assert statistics["range_residual_m"]["count"] > 0
    assert statistics["age_consistency_error_s"]["observed_max_abs_s"] < 1e-12
    assert all(
        "diagnostic" not in record["observation"]
        for record in records
        if record["kind"] == "sample"
    )


@pytest.mark.parametrize(
    "settings",
    [
        {"ticks": 0},
        {"ticks": 33},
        {"ticks": True},
        {"seed": -1},
        {"seed": True},
        {"scenes": []},
        {"scenes": ["clear"] * 5},
        {"scenes": ["clear", "clear"]},
        {"scenes": ["unknown"]},
    ],
)
def test_sensor_diagnostic_study_rejects_out_of_scope_before_writing(
    tmp_path, settings
):
    from sim.diagnostics import run_diagnostic_study

    output, report = tmp_path / "episodes", tmp_path / "report.json"
    with pytest.raises(ValueError):
        run_diagnostic_study(output, report, **{"seed": 1, "ticks": 1, **settings})
    assert not output.exists() and not report.exists()


def test_sensor_diagnostic_study_fresh_outputs_hashes_and_empty_statistics(tmp_path):
    import hashlib
    from dataclasses import asdict

    from sim.diagnostics import run_diagnostic_study

    output, destination = tmp_path / "episodes", tmp_path / "report.json"
    report = run_diagnostic_study(
        output, destination, seed=1, ticks=1, scenes=["clear"]
    )
    assert json.loads(destination.read_text()) == report
    assert not report["accepted_bounds"] and not report["locked_splits"]
    assert report["task_labels"] == report["accepted_family_assignments"] == 0
    assert report["diagnostics"]["range_residual_m"]["count"] == 0
    assert report["diagnostics"]["range_residual_m"]["observed_max_abs_m"] is None
    episode = report["episodes"][0]
    data = Path(episode["path"]).read_bytes()
    assert hashlib.sha256(data).hexdigest() == episode["sha256"]
    assert len(data) == episode["bytes"]
    rows = [json.loads(line) for line in data.splitlines()]
    assert rows[0]["config"] == asdict(Config())
    observations = b"".join(
        (
            json.dumps(row["observation"], sort_keys=True, separators=(",", ":")) + "\n"
        ).encode()
        for row in rows
        if row["kind"] == "sample"
    )
    assert hashlib.sha256(observations).hexdigest() == episode["observation_sha256"]
    with pytest.raises(FileExistsError):
        run_diagnostic_study(output, tmp_path / "other-report.json", seed=1)
    with pytest.raises(FileExistsError):
        run_diagnostic_study(tmp_path / "other-episodes", destination, seed=1)
    with pytest.raises(ValueError):
        run_diagnostic_study(
            tmp_path / "nested", tmp_path / "nested" / "report.json", seed=1
        )


@pytest.mark.parametrize("layout", ["same", "report_inside", "report_ancestor"])
def test_sensor_diagnostic_study_rejects_overlapping_outputs_before_collection(
    tmp_path, monkeypatch, layout
):
    from sim.diagnostics import run_diagnostic_study

    root = tmp_path / "study"
    output, report = {
        "same": (root, root),
        "report_inside": (root, root / "report.json"),
        "report_ancestor": (root / "episodes", root),
    }[layout]
    monkeypatch.setattr(
        "sim.diagnostics.collect_diagnostic_episode",
        lambda *args, **kwargs: pytest.fail(
            "collection started before path validation"
        ),
    )
    with pytest.raises(ValueError):
        run_diagnostic_study(output, report, seed=1)
    assert not root.exists()


def test_sensor_diagnostic_trace_all_dropout_is_not_zero_residual_evidence():
    from sim.diagnostics import DiagnosticRoverEnv, diagnostic_sample

    env = DiagnosticRoverEnv(Config(dropout=1), make_scenario("obstacle", seed=1))
    for _ in range(2):
        observation, *_ = env.step((0, 0))
    sample = diagnostic_sample(env, observation)["diagnostic"]
    assert sample["status"] == "delivered" and sample["invalid_zones"] == 64
    assert sample["valid_surface_zones"] == 0
    assert all(value is None for row in sample["range_residual_m"] for value in row)


def test_sensor_diagnostic_collection_preserves_real_termination(monkeypatch):
    from sim.diagnostics import collect_diagnostic_episode

    monkeypatch.setattr(
        "sim.diagnostics.make_scenario",
        lambda *args: Scenario(goal=(1.05, 3.0)),
    )
    _, summary = collect_diagnostic_episode("clear", seed=1, ticks=32)
    assert summary["ticks"] == 1 and summary["observations"] == 2
    assert summary["success"] and not summary["collision"]
    assert not summary["censored"] and not summary["environment_timeout"]
    assert summary["stop_reason"] == "environment_end"


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
    [
        (-1, 0),
        (1, 0),
        (0, -1),
        (float("nan"), 0),
        (0, float("inf")),
        (True, 0),
        (10**400, 0),
        (0, 10**400),
    ],
)
def test_draft_envelope_rejects_invalid_values(speed, age):
    with pytest.raises((TypeError, ValueError)):
        stopping_envelope(speed, age, Config())


@pytest.fixture
def draft_observation():
    config = Config(noise_std=0, dropout=0, latency_ticks=0)
    observation, _ = RoverEnv(config).reset(seed=5)
    observation["tof_m"] = np.full((8, 8), 2.0)
    observation["tof_valid"] = np.ones((8, 8), dtype=bool)
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


def test_observation_validation_does_not_read_catalogue_or_source(
    draft_observation, monkeypatch
):
    from sim import labels

    def unexpected_catalogue():
        raise AssertionError("input validation must not compute proxy labels")

    monkeypatch.setattr(labels, "draft_catalogue", unexpected_catalogue)
    config, observation = draft_observation
    ego, ranges, valid, envelope = validate_observation(observation, config)
    np.testing.assert_equal(ego, observation["ego"])
    np.testing.assert_equal(ranges, observation["tof_m"])
    np.testing.assert_equal(valid, observation["tof_valid"])
    assert envelope == config.radius


def test_draft_file_cache_preserves_ownership_and_invalidates_edits(
    draft_observation, tmp_path, monkeypatch
):
    from sim import labels

    source = tmp_path / "labels.py"
    catalogue_path = tmp_path / "catalogue.json"
    catalogue = draft_catalogue()
    source.write_bytes(b"fixture labeler source\n")
    catalogue_path.write_text(json.dumps(catalogue))
    monkeypatch.setattr(labels, "__file__", str(source))
    original_read = Path.read_bytes
    reads = []

    def read_bytes(path):
        reads.append(path)
        return original_read(path)

    monkeypatch.setattr(Path, "read_bytes", read_bytes)
    config, observation = draft_observation
    first = draft_labels(observation, config)
    assert draft_labels(observation, config) == first
    assert reads.count(source) == reads.count(catalogue_path) == 1
    draft_catalogue()["questions"][0]["options"][0] = "modified"
    assert draft_catalogue() == catalogue
    replacement = b"replacement fixture source\n"
    source.write_bytes(replacement)
    updated = draft_labels(observation, config)
    assert updated["labeler_sha256"] == hashlib.sha256(replacement).hexdigest()
    assert updated["labeler_sha256"] != first["labeler_sha256"]
    assert reads.count(source) == 2
    catalogue["policy_id"] += "-fixture"
    catalogue_path.write_text(json.dumps(catalogue))
    assert draft_labels(observation, config)["policy_id"] == catalogue["policy_id"]
    assert reads.count(catalogue_path) == 2


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


def test_observation_reads_do_not_advance_or_expose_history():
    env = RoverEnv()
    observation, _ = env.reset(seed=4)
    for tick in range(env.config.history_ticks + 2):
        rng_state = deepcopy(env.rng.bit_generator.state)
        repeated = env._observation()
        assert len(env.history) == min(tick + 1, env.config.history_ticks)
        assert env.rng.bit_generator.state == rng_state
        for name, value in observation.items():
            np.testing.assert_equal(repeated[name], value)
        for value in repeated.values():
            if isinstance(value, np.ndarray):
                value[:] = 0
        detached = env._observation()
        for name, value in observation.items():
            np.testing.assert_equal(detached[name], value)
        observation, *_ = env.step((0.1, 0.1))


def test_latency_dropout_and_sensor_timestamp_are_explicit():
    env = RoverEnv(Config(noise_std=0, dropout=0, latency_ticks=2))
    observation, _ = env.reset()
    assert not observation["tof_valid"].any()
    assert observation["tof_sample_tick"] is None
    observation, *_ = env.step([0, 0])
    assert not observation["tof_valid"].any()
    observation, *_ = env.step([0, 0])
    assert observation["tof_valid"].any()
    assert not observation["tof_valid"][0].any()
    assert observation["tof_sample_tick"] == 0
    assert observation["tof_age_s"] == pytest.approx(0.1)
    dropped, _ = RoverEnv(Config(dropout=1, latency_ticks=0)).reset()
    assert not dropped["tof_valid"].any()
    assert np.isfinite(dropped["tof_m"]).all()


def test_tof_rate_delivers_pending_frames_without_a_new_capture():
    env = RoverEnv(Config(noise_std=0, dropout=0))
    observation, _ = env.reset()
    delivered = [observation["tof_sample_tick"]]
    ages = [observation["tof_age_s"]]
    for _ in range(8):
        observation, *_ = env.step((0, 0))
        delivered.append(observation["tof_sample_tick"])
        ages.append(observation["tof_age_s"])
    assert delivered == [None, None, 0, 0, 2, 3, 4, 4, 6]
    assert ages[2:] == pytest.approx([0.1, 0.15, 0.1, 0.1, 0.1, 0.15, 0.1])


def test_tof_rate_holds_measurements_without_consuming_rng():
    env = RoverEnv(Config(latency_ticks=0))
    observation, _ = env.reset(seed=42)
    before = deepcopy(env.rng.bit_generator.state)
    held, *_ = env.step((0, 0))
    assert env.rng.bit_generator.state == before
    np.testing.assert_array_equal(held["tof_m"], observation["tof_m"])
    np.testing.assert_array_equal(held["tof_valid"], observation["tof_valid"])
    assert held["tof_sample_tick"] == 0
    assert held["tof_age_s"] == pytest.approx(env.config.dt)


@pytest.mark.parametrize(
    "dt,rate,captures",
    [
        (0.05, 15, [0, 2, 3, 4, 6, 7, 8]),
        (0.05, 10, [0, 2, 4, 6, 8]),
        (0.1, 10, list(range(9))),
        (0.3, 2, [0, 2, 4, 5, 7]),
        (1.0, 15, list(range(9))),
    ],
)
def test_tof_rate_phase_and_reset_are_deterministic(dt, rate, captures):
    from sim.diagnostics import DiagnosticRoverEnv

    env = DiagnosticRoverEnv(Config(dt=dt, tof_rate_hz=rate, latency_ticks=0))
    sequences = []
    for _ in range(2):
        observation, _ = env.reset(seed=42)
        sequence = [json.dumps(observation, default=json_value, sort_keys=True)]
        for _ in range(8):
            observation, *_ = env.step((0, 0))
            sequence.append(json.dumps(observation, default=json_value, sort_keys=True))
        assert list(env.capture_trace) == captures
        sequences.append(sequence)
    assert sequences[0] == sequences[1]


def test_tof_rate_legacy_config_loading_keeps_per_tick_sampling():
    from dataclasses import asdict

    record = asdict(Config())
    assert record.pop("tof_rate_hz") == 15
    legacy = Config.from_record(record)
    assert legacy.tof_rate_hz is None
    env = RoverEnv(legacy)
    env.reset(seed=42)
    for tick in range(1, 9):
        observation, *_ = env.step((0, 0))
        expected = tick - legacy.latency_ticks
        assert observation["tof_sample_tick"] == (expected if expected >= 0 else None)
    assert Config.from_record(asdict(Config())) == Config()


@pytest.mark.parametrize("rate", [0, -1, 15.1, 20, float("inf"), float("nan"), True])
def test_tof_rate_rejects_unsupported_configuration(rate):
    with pytest.raises(ValueError):
        Config(tof_rate_hz=rate)


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
        {"dt": 10**400},
        {"max_speed": -(10**400)},
        {"noise_std": 10**400},
    ],
)
def test_invalid_simulation_configuration_is_rejected(kwargs):
    with pytest.raises(ValueError):
        Config(**kwargs)


@pytest.mark.parametrize("field", Config.__dataclass_fields__)
@pytest.mark.parametrize("value", [False, True])
def test_boolean_simulation_configuration_is_rejected(field, value):
    with pytest.raises(ValueError, match="finite"):
        Config(**{field: value})


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
