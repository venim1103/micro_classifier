"""Validate pinned d3 teachers against streamed BF16 weights, without a full GPU copy.

python -m teacher.validate_d3_int8 --output teacher/reports/name.json
Use --repo-id vllm-sr/d3-mini to validate the unquantized host-embedding adapter.
The synthetic fixtures measure parity and resources, not task accuracy.
"""

from __future__ import annotations

import argparse
import contextlib
import functools
import hashlib
import json
import platform
import resource
import statistics
import time
from pathlib import Path
from unittest.mock import patch

import torch
from PIL import Image, ImageDraw
from safetensors import safe_open
from torch.nn import functional

from teacher import d3_int8
from teacher.vela_int8 import QUANTIZED_LINEARS, stored_bf16_weights


def diagnostic_requests():
    """Fixed text, synthetic state JSON, and local 64x64 image fixtures."""
    questions = [
        {"type": "noul", "instructions": "Does the state mention an obstruction?"},
        {
            "type": "choice",
            "instructions": "What does the state primarily describe?",
            "criteria": {"navigation": None, "battery": None, "delivery": None},
        },
        {
            "type": "score",
            "instructions": "How urgent does the state sound?",
            "criteria": ["Routine", "Needs attention", "Immediate attention"],
        },
    ]
    texts = [
        "The path ahead is clear. The rover is stationary.",
        "An obstruction is visible ahead on the left.",
        "The battery sensor reports smoke; request immediate review.",
        "No obstruction was detected. The destination is ahead.",
        "The parcel arrived on schedule yesterday.",
        "The battery is fully charged; the next inspection is next month.",
        "The delivery is late, but there is no urgent deadline.",
        "The quoted word 'obstruction' is not a sensor observation.",
        "The navigation sensor has stopped reporting valid readings.",
        "The rover has reached its destination and is stopped.",
    ]
    rows = []
    for index, text in enumerate(texts):
        bundle = {"q": questions[index % 3]}
        if index == 0:
            bundle = {
                f"q{number}": question for number, question in enumerate(questions)
            }
        rows.append({"id": f"text-{index:02}", "state": text, "questions": bundle})
    for index in range(11):
        ranges = [round(0.25 + ((index + column) % 8) * 0.45, 2) for column in range(8)]
        rows.append(
            {
                "id": f"rover-{index:02}",
                "state": {
                    "fixture": "synthetic diagnostic, not an operational policy",
                    "axes": "FLU",
                    "speed_m_s": round(index * 0.1, 1),
                    "goal_body_m": [2.0, round((index - 5) * 0.2, 1)],
                    "tof_m": [ranges] * 8,
                    "valid_tof_rows": [index % 4 != 0] * 8,
                    "history_speed_m_s": [round(index * 0.1, 1)] * 8,
                    "fault": "sensor stale" if index == 10 else None,
                    "obstruction_ahead": index % 2 == 0,
                },
                "questions": {"q": questions[index % 3]},
            }
        )
    for index, color in enumerate(("red", "green", "blue", "white")):
        image = Image.new("RGB", (64, 64), color)
        ImageDraw.Draw(image).rectangle((20, 20, 43, 43), fill="black")
        rows.append(
            {
                "id": f"image-{index:02}",
                "state": "A synthetic image.",
                "images": [image],
                "questions": {
                    "color": {
                        "type": "choice",
                        "instructions": "What color is the background?",
                        "criteria": {
                            key: None for key in ("red", "green", "blue", "white")
                        },
                    },
                    "square": {
                        "type": "noul",
                        "instructions": "Is a black square visible?",
                    },
                },
            }
        )
    return rows


def fixture_digest(rows):
    digest = hashlib.sha256()
    for row in rows:
        digest.update(
            json.dumps(
                {key: value for key, value in row.items() if key != "images"},
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode()
        )
        for image in row.get("images", []):
            digest.update(json.dumps([image.mode, image.size]).encode())
            digest.update(image.tobytes())
    return digest.hexdigest()


def distribution(answer):
    if "error" in answer:
        raise ValueError(f"teacher rejected a diagnostic question: {answer}")
    if answer["type"] == "noul":
        values = {"false": 1 - answer["noul"], "true": answer["noul"]}
    else:
        values = answer["probabilities"]
    if not values or any(not 0 <= value <= 1 for value in values.values()):
        raise ValueError("invalid probability distribution")
    if abs(sum(values.values()) - 1) > 1e-5:
        raise ValueError("probabilities do not sum to one")
    return values


def compare(candidate, reference):
    if candidate.keys() != reference.keys():
        raise ValueError("request IDs differ")
    groups = {
        kind: {"deltas": [], "questions": 0, "decision_flips": 0}
        for kind in ("choice", "noul", "score")
    }
    for request_id, expected in reference.items():
        actual = candidate[request_id]
        if (
            actual["answers"].keys() != expected["answers"].keys()
            or actual["usage"] != expected["usage"]
        ):
            raise ValueError("question IDs or input tokens differ")
        for question_id, answer in expected["answers"].items():
            observed = actual["answers"][question_id]
            if observed["type"] != answer["type"]:
                raise ValueError("answer types differ")
            left, right = distribution(observed), distribution(answer)
            if list(left) != list(right):
                raise ValueError("option identities or order differ")
            group = groups[answer["type"]]
            group["questions"] += 1
            group["deltas"].extend(abs(left[key] - right[key]) for key in right)
            if answer["type"] == "noul":
                flip = (left["true"] >= 0.5) != (right["true"] >= 0.5)
            else:
                flip = max(left, key=left.get) != max(right, key=right.get)
            group["decision_flips"] += int(flip)
    combined = [delta for group in groups.values() for delta in group["deltas"]]
    if not combined:
        raise ValueError("no probability values compared")
    result = {
        "compared_values": len(combined),
        "max_abs_delta": max(combined),
        "mean_abs_delta": statistics.fmean(combined),
        "decision_flips": sum(group["decision_flips"] for group in groups.values()),
    }
    result["by_type"] = {}
    for kind, group in groups.items():
        values = group.pop("deltas")
        result["by_type"][kind] = {
            **group,
            "compared_values": len(values),
            "max_abs_delta": max(values, default=0),
            "mean_abs_delta": statistics.fmean(values) if values else 0,
        }
    return result


@contextlib.contextmanager
def stored_reference(teacher, path):
    """Stream BF16 projections; look up the exact used embedding rows on GPU."""
    model = teacher.engine.backbone
    embedding = model.language_model.embed_tokens

    def gpu_lookup(ids):
        unique, inverse = torch.unique(ids.cpu(), return_inverse=True)
        table = embedding.weight_host[unique].to(ids.device)
        return functional.embedding(inverse.to(ids.device), table)

    with contextlib.ExitStack() as stack:
        stack.enter_context(patch.object(embedding, "forward", gpu_lookup))
        if teacher.quantized:
            stack.enter_context(stored_bf16_weights(model, path, cache_size=1))
        else:
            weight_map = json.loads(
                (Path(path) / "model.safetensors.index.json").read_text()
            )["weight_map"]
            handles = {
                shard: stack.enter_context(
                    safe_open(str(Path(path) / shard), framework="pt")
                )
                for shard in set(weight_map.values())
            }

            @functools.lru_cache(maxsize=1)
            def fetch(key, device):
                return handles[weight_map[key]].get_tensor(key).to(device)

            stack.callback(fetch.cache_clear)

            def forward(module, key, inputs):
                return functional.linear(inputs, fetch(key, inputs.device), module.bias)

            for name, module in model.named_modules():
                parts = name.split(".", 3)
                if (
                    parts[:2] == ["language_model", "layers"]
                    and len(parts) == 4
                    and parts[3] in QUANTIZED_LINEARS
                ):
                    stack.enter_context(
                        patch.object(
                            module,
                            "forward",
                            functools.partial(forward, module, f"{name}.weight"),
                        )
                    )
        yield


def run_requests(teacher, rows):
    responses, timings = {}, {}
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    for row in rows:
        started = time.perf_counter()
        response = teacher.system_one(
            **{key: value for key, value in row.items() if key != "id"}
        )
        torch.cuda.synchronize()
        for answer in response["answers"].values():
            distribution(answer)
        responses[row["id"]] = response
        timings[row["id"]] = time.perf_counter() - started
        print(f"{row['id']}: {timings[row['id']]:.3f}s", flush=True)
    seconds = sum(timings.values())
    return {
        "responses": responses,
        "request_seconds": timings,
        "seconds": seconds,
        "requests_per_second": len(rows) / seconds,
        "questions_per_second": sum(len(row["questions"]) for row in rows) / seconds,
        "median_request_seconds": statistics.median(timings.values()),
        "peak_allocated_gib": torch.cuda.max_memory_allocated() / 2**30,
        "peak_reserved_gib": torch.cuda.max_memory_reserved() / 2**30,
        "host_peak_rss_gib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2**20,
    }


@contextlib.contextmanager
def mini_experiment_memory_limit(device="cuda:0"):
    if not torch.cuda.is_available() or torch.cuda.get_device_capability(device)[0] < 8:
        raise ValueError("experiment requires native BF16-capable CUDA")
    total = torch.cuda.get_device_properties(device).total_memory
    free, _ = torch.cuda.mem_get_info(device)
    previous = torch.cuda.get_per_process_memory_fraction(device)
    fraction = min(previous, 10 * 2**30 / total)
    limit = int(fraction * total)
    if free < limit or torch.cuda.memory_reserved(device) > limit:
        raise ValueError("insufficient free memory for the capped experiment")
    torch.cuda.set_per_process_memory_fraction(fraction, device)
    torch.cuda.reset_peak_memory_stats(device)
    try:
        if torch.cuda.get_per_process_memory_fraction(device) * total > limit + 1:
            raise RuntimeError("PyTorch allocator cap configuration failed")
        yield {
            "requested_cap_gib": 10,
            "enforced_cap_bytes": limit,
            "allocator_fraction": fraction,
            "device_total_bytes": total,
            "device_free_before_bytes": free,
            "scope": "PyTorch caching allocator, not all driver allocations",
        }
    finally:
        torch.cuda.set_per_process_memory_fraction(previous, device)


def validate_mini_int8_experiment(path):
    report = {
        "schema": "micro-classifier/d3-mini-int8-experiment/1",
        "repo_id": d3_int8.MINI_REPO_ID,
        "revision": d3_int8.APPROVED_REVISIONS[d3_int8.MINI_REPO_ID],
        "manifest_sha256": d3_int8.APPROVED_MANIFESTS[d3_int8.MINI_REPO_ID],
        "status": "running",
        "token_budget": 2048,
        "training_approved": False,
        "live_labeling_approved": False,
        "task_quality_claim": False,
        "context_probe_approved_by_parity": False,
        "adapter_source_sha256": hashlib.sha256(
            Path(d3_int8.__file__).read_bytes()
        ).hexdigest(),
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "limitations": [
            "Synthetic parity/resource experiment, not task quality or training labels.",
            "Normal adapter ceilings remain 2048; no larger-context inference in this phase.",
            "Allocator cap excludes driver/native allocations; OOM aborts without retry.",
            "Full manifest verification precedes approved cached release imports.",
        ],
    }
    try:
        with mini_experiment_memory_limit() as limit:
            report["memory_limit"] = limit
            started = time.perf_counter()
            teacher = d3_int8.load_engine(
                path=path,
                device="cuda:0",
                repo_id=d3_int8.MINI_REPO_ID,
                experimental_mini_int8=True,
            )
            report["load"] = {
                "seconds": time.perf_counter() - started,
                "allocated_gib": torch.cuda.memory_allocated() / 2**30,
                "peak_reserved_gib": torch.cuda.max_memory_reserved() / 2**30,
            }
            report["provenance"] = teacher.provenance()
            report["environment"] = {
                **teacher.engine.runtime_info(),
                "python": platform.python_version(),
            }
            if teacher.engine.image_unavailable is not None:
                raise RuntimeError(
                    f"image validation unavailable: {teacher.engine.image_unavailable}"
                )
            rows = diagnostic_requests()
            report["fixtures"] = {
                "sha256": fixture_digest(rows),
                "requests": len(rows),
                "reviewed_labels": False,
            }
            print("Capped mini INT8 candidate pass", flush=True)
            report["candidate"] = run_requests(teacher, rows)
            print("Capped stored BF16 reference pass", flush=True)
            with stored_reference(teacher, path):
                report["reference"] = run_requests(teacher, rows)
            report["parity"] = compare(
                report["candidate"]["responses"], report["reference"]["responses"]
            )
            report["status"] = "complete_requires_parity_review"
    except (RuntimeError, ValueError, OSError) as error:
        report.update(
            status="aborted", error_type=type(error).__name__, error=str(error)
        )
        if torch.cuda.is_initialized():
            report["abort_peak_reserved_gib"] = torch.cuda.max_memory_reserved() / 2**30
    return report


def context_probe_inputs():
    from teacher.label_pipeline import episode_requests

    root = Path(__file__).resolve().parents[1]
    result = []
    for name, relative, tick in (
        ("startup-clear", "sim/episodes/wire-v0-smoke/clear-20261015.jsonl", 0),
        ("warm-clear", "sim/episodes/wire-v0-smoke/clear-20261015.jsonl", 15),
        ("warm-slalom", "sim/episodes/label-smoke-20261016/slalom.jsonl", 15),
    ):
        requests = list(episode_requests(root / relative, limit=tick + 1))
        if len(requests) != tick + 1:
            raise ValueError(f"missing existing probe observation: {name}")
        result.append((name, requests[tick]))
    return result


def validate_mini_context_probe(path, parity_path):
    from teacher.label_pipeline import digest

    report = {
        "schema": "micro-classifier/d3-mini-context-resource-probe/1",
        "repo_id": d3_int8.MINI_REPO_ID,
        "revision": d3_int8.APPROVED_REVISIONS[d3_int8.MINI_REPO_ID],
        "manifest_sha256": d3_int8.APPROVED_MANIFESTS[d3_int8.MINI_REPO_ID],
        "status": "running",
        "budgets": [4096, 8192, 12288],
        "cases": [],
        "review_acknowledged_by_explicit_cli": True,
        "training_approved": False,
        "live_labeling_approved": False,
        "task_quality_claim": False,
        "mode_labels_written": 0,
        "responses_discarded": True,
        "truncation_enabled": False,
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "adapter_source_sha256": hashlib.sha256(
            Path(d3_int8.__file__).read_bytes()
        ).hexdigest(),
        "limitations": [
            "Three selected existing full states, not representative task coverage.",
            "Original mode question is only a resource workload; answer values are discarded.",
            "No BF16 parity or task-quality measurement at larger contexts.",
            "Normal defaults, full input/history and draft representations unchanged.",
            "Abort the whole probe on OOM/cap failure, without retry or larger allocation.",
        ],
    }
    try:
        raw = Path(parity_path).read_bytes()
        parity = json.loads(raw)
        if (
            parity.get("schema") != "micro-classifier/d3-mini-int8-experiment/1"
            or parity.get("repo_id") != report["repo_id"]
            or parity.get("revision") != report["revision"]
            or parity.get("manifest_sha256") != report["manifest_sha256"]
            or parity.get("status") != "complete_requires_parity_review"
            or parity.get("token_budget") != 2048
            or parity.get("fixtures", {}).get("sha256")
            != fixture_digest(diagnostic_requests())
            or parity.get("parity")
            != compare(
                parity["candidate"]["responses"], parity["reference"]["responses"]
            )
        ):
            raise ValueError(
                "reviewed parity report does not match the pinned completed experiment"
            )
        report["reviewed_parity_sha256"] = hashlib.sha256(raw).hexdigest()
        inputs = context_probe_inputs()
        with mini_experiment_memory_limit() as limit:
            report["memory_limit"] = limit
            started = time.perf_counter()
            teacher = d3_int8.load_engine(
                path=path,
                device="cuda:0",
                repo_id=d3_int8.MINI_REPO_ID,
                token_budget=12288,
                experimental_mini_int8=True,
            )
            report["load"] = {
                "seconds": time.perf_counter() - started,
                "allocated_gib": torch.cuda.memory_allocated() / 2**30,
                "peak_reserved_gib": torch.cuda.max_memory_reserved() / 2**30,
            }
            report["provenance"] = teacher.provenance()
            report["environment"] = teacher.engine.runtime_info()
            plans = []
            for name, request in inputs:
                prepared = teacher.engine.prepare(
                    request["state"], request["questions"]
                )
                if prepared.errors or set(prepared.sequences) != set(
                    request["questions"]
                ):
                    raise ValueError(f"complete prompt preparation failed: {name}")
                observation = json.loads(request["state"])["module_observation"]
                plans.append(
                    (
                        request,
                        {
                            "id": name,
                            "source": request["source"],
                            "request_sha256": digest(request),
                            "input_provenance": request["provenance"],
                            "state_sha256": hashlib.sha256(
                                request["state"].encode()
                            ).hexdigest(),
                            "token_ids_sha256": digest(prepared.sequences),
                            "tokens": max(map(len, prepared.sequences.values())),
                            "history_ticks": sum(observation["history_valid"]),
                            "truncated": False,
                        },
                    )
                )
            report["inputs"] = [metadata for _, metadata in plans]
            for budget in report["budgets"]:
                teacher.token_budget = budget
                teacher.engine.max_length = budget
                for request, metadata in plans:
                    case = {
                        "id": metadata["id"],
                        "budget": budget,
                        "tokens": metadata["tokens"],
                        "status": "budget_rejected"
                        if metadata["tokens"] > budget
                        else "running",
                    }
                    report["cases"].append(case)
                    if case["status"] == "budget_rejected":
                        continue
                    torch.cuda.empty_cache()
                    torch.cuda.reset_peak_memory_stats()
                    torch.cuda.synchronize()
                    started = time.perf_counter()
                    response = teacher.system_one(
                        state=request["state"], questions=request["questions"]
                    )
                    torch.cuda.synchronize()
                    case["seconds"] = time.perf_counter() - started
                    if set(response["answers"]) != set(request["questions"]):
                        raise ValueError("resource response question mismatch")
                    for answer in response["answers"].values():
                        distribution(answer)
                    del response
                    case.update(
                        peak_allocated_gib=torch.cuda.max_memory_allocated() / 2**30,
                        peak_reserved_gib=torch.cuda.max_memory_reserved() / 2**30,
                    )
                    if (
                        case["peak_allocated_gib"] * 2**30 > limit["enforced_cap_bytes"]
                        or case["peak_reserved_gib"] > 11
                    ):
                        raise RuntimeError("measured memory cap exceeded")
                    case["status"] = "complete_answers_discarded"
                    print(
                        f"{case['id']} budget={budget} tokens={case['tokens']}: {case['seconds']:.3f}s",
                        flush=True,
                    )
            report["status"] = "complete_resource_only"
    except (RuntimeError, ValueError, OSError, KeyError, TypeError) as error:
        report.update(
            status="aborted", error_type=type(error).__name__, error=str(error)
        )
        if report["cases"] and report["cases"][-1]["status"] == "running":
            report["cases"][-1]["status"] = "aborted"
        if torch.cuda.is_initialized():
            report["abort_peak_allocated_gib"] = (
                torch.cuda.max_memory_allocated() / 2**30
            )
            report["abort_peak_reserved_gib"] = torch.cuda.max_memory_reserved() / 2**30
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-id", choices=d3_int8.APPROVED_REVISIONS, default=d3_int8.REPO_ID
    )
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    experiment = parser.add_mutually_exclusive_group()
    experiment.add_argument("--mini-int8-experiment", action="store_true")
    experiment.add_argument("--mini-int8-context-probe", action="store_true")
    parser.add_argument("--reviewed-parity-report", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    if args.reviewed_parity_report is not None and not args.mini_int8_context_probe:
        parser.error(
            "--reviewed-parity-report is only valid with --mini-int8-context-probe"
        )
    if args.mini_int8_experiment or args.mini_int8_context_probe:
        if args.repo_id != d3_int8.MINI_REPO_ID or args.snapshot is None:
            parser.error(
                "mini INT8 experiment requires d3-mini and an already-cached --snapshot"
            )
        if args.mini_int8_context_probe and args.reviewed_parity_report is None:
            parser.error(
                "context probe requires --reviewed-parity-report after result review"
            )
        torch.set_num_threads(4)
        report = (
            validate_mini_context_probe(args.snapshot, args.reviewed_parity_report)
            if args.mini_int8_context_probe
            else validate_mini_int8_experiment(args.snapshot)
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x") as stream:
            json.dump(report, stream, indent=2, allow_nan=False)
            stream.write("\n")
        print(
            json.dumps(
                {
                    "status": report["status"],
                    "parity": report.get("parity"),
                    "error": report.get("error"),
                }
            ),
            flush=True,
        )
        if report["status"] == "aborted":
            raise SystemExit(1)
        return
    if not torch.cuda.is_available() or torch.cuda.get_device_capability()[0] < 8:
        parser.error(
            "a native BF16-capable CUDA GPU is required; never use the GTX 1080 Ti"
        )
    torch.set_num_threads(4)
    path = args.snapshot or d3_int8.download(args.repo_id)
    started = time.perf_counter()
    teacher = d3_int8.load_engine(path=path, device="cuda:0", repo_id=args.repo_id)
    load_seconds = time.perf_counter() - started
    if teacher.engine.image_unavailable is not None:
        raise RuntimeError(
            f"image validation unavailable: {teacher.engine.image_unavailable}"
        )
    rows = diagnostic_requests()
    report = {
        "schema": "micro-classifier/d3-validation/1",
        "provenance": teacher.provenance(),
        "environment": {
            **teacher.engine.runtime_info(),
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "fixtures": {
            "sha256": fixture_digest(rows),
            "requests": len(rows),
            "reviewed_labels": False,
        },
        "load": {
            "seconds": load_seconds,
            "allocated_gib": torch.cuda.memory_allocated() / 2**30,
        },
        "limitations": [
            "Synthetic parity fixtures, not task accuracy or commercial provenance clearance.",
            "Reference streams stored BF16 text projections and used embedding rows.",
            "Reference speed includes disk and transfer overhead, not resident BF16 speed.",
            "One question per forward pass, 2048-token ceiling, no video or remote media.",
        ],
    }
    print("Candidate pass", flush=True)
    report["candidate"] = run_requests(teacher, rows)
    print("Stored BF16 reference pass", flush=True)
    with stored_reference(teacher, path):
        report["reference"] = run_requests(teacher, rows)
    report["parity"] = compare(
        report["candidate"]["responses"], report["reference"]["responses"]
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps(report["parity"], indent=2), flush=True)
    print(f"Report: {args.output}", flush=True)


if __name__ == "__main__":
    main()
