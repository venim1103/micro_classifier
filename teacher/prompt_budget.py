"""Offline text-only d3 token counts; no model weights or inference."""

import argparse
import hashlib
import json
import runpy
import tempfile
from copy import deepcopy
from importlib.metadata import version
from pathlib import Path
from types import SimpleNamespace

from teacher.label_pipeline import (
    compact_request_draft,
    episode_requests,
    expand_compact_state,
    validate_request,
)

ASSET_NAMES = (
    "d3_format.py",
    "d3_runtime.py",
    "decision_config.json",
    "config.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "chat_template.jinja",
    "vocab.json",
    "merges.txt",
)
OPTIONAL_NAMES = ("added_tokens.json", "special_tokens_map.json", "tokenizer.model")


def verify_prompt_assets(root, *, expected_manifest_sha256):
    root = Path(root)
    raw_manifest = (root / "MODEL_MANIFEST.json").read_bytes()
    checksum = hashlib.sha256(raw_manifest).hexdigest()
    if checksum != expected_manifest_sha256:
        raise ValueError("manifest identity differs from the approved revision")
    manifest = json.loads(raw_manifest)
    if manifest.get("schema") != "d3-package-manifest/1":
        raise ValueError("unsupported d3 package manifest")
    hashes = manifest.get("files_sha256", {})
    names = [*ASSET_NAMES, *(name for name in OPTIONAL_NAMES if (root / name).exists())]
    names.extend(
        path.relative_to(root).as_posix()
        for path in (root / "chat_templates").glob("*.jinja")
    )
    verified = {}
    formatter_source = None
    for name in names:
        if name not in hashes:
            raise ValueError(f"prompt asset not covered by manifest: {name}")
        raw = (root / name).read_bytes()
        actual = hashlib.sha256(raw).hexdigest()
        if actual != hashes[name]:
            raise ValueError(f"prompt asset SHA-256 mismatch: {name}")
        verified[name] = actual
        if name == "d3_format.py":
            formatter_source = raw
    return verified, formatter_source


def load_prompt_assets(*, repo_id="vllm-sr/d3-flash", snapshot=None):
    from huggingface_hub import constants
    from transformers import AutoTokenizer

    from teacher.d3_int8 import APPROVED_MANIFESTS, APPROVED_REVISIONS

    if repo_id not in APPROVED_REVISIONS:
        raise ValueError("unapproved d3 repository")
    revision = APPROVED_REVISIONS[repo_id]
    root = (
        Path(snapshot)
        if snapshot is not None
        else Path(constants.HF_HUB_CACHE)
        / ("models--" + repo_id.replace("/", "--"))
        / "snapshots"
        / revision
    )
    files, formatter_source = verify_prompt_assets(
        root, expected_manifest_sha256=APPROVED_MANIFESTS[repo_id]
    )
    with tempfile.TemporaryDirectory(prefix="micro-d3-prompt-") as temporary:
        source_path = Path(temporary) / "d3_format.py"
        source_path.write_bytes(formatter_source)
        formatter = SimpleNamespace(**runpy.run_path(str(source_path)))
    config = json.loads((root / "decision_config.json").read_text())
    if config.get("prompt") != "d3" or config.get("format_id") != formatter.FORMAT_ID:
        raise ValueError("unsupported prompt contract")
    tokenizer = AutoTokenizer.from_pretrained(
        str(root), local_files_only=True, trust_remote_code=False, use_fast=True
    )
    tokenizer.padding_side = "left"
    if not tokenizer.is_fast or tokenizer.pad_token_id is None:
        raise ValueError("a local fast tokenizer with a pad token is required")
    codes, token_ids = formatter.answer_codes(tokenizer)
    if config.get("codes") != codes or config.get("token_ids") != token_ids:
        raise ValueError("tokenizer answer codes differ from the pinned config")
    probe = "State:\nA"
    if (
        tokenizer(probe)["input_ids"]
        != tokenizer(probe, add_special_tokens=False)["input_ids"]
    ):
        raise ValueError("tokenizer adds unexpected special tokens")
    return SimpleNamespace(
        tokenizer=tokenizer,
        formatter=formatter,
        codes=codes,
        provenance={
            "repo_id": repo_id,
            "revision": revision,
            "manifest_sha256": APPROVED_MANIFESTS[repo_id],
            "files_sha256": files,
            "verification_scope": "prompt_and_tokenizer_assets_only_not_model_package",
            "model_weights_loaded": False,
            "tokenizer_class": type(tokenizer).__name__,
            "transformers_version": version("transformers"),
            "tokenizers_version": version("tokenizers"),
        },
    )


def count_requests(requests, *, assets, budget=2048):
    if type(budget) is not int or not 1 <= budget <= 2048:
        raise ValueError("budget must be between 1 and 2048 tokens")
    results = []
    for index, request in enumerate(requests):
        validate_request(request)
        names = list(request["questions"])
        texts = [
            assets.formatter.render(
                assets.tokenizer,
                request["state"],
                request["questions"][name],
                assets.codes,
            )
            for name in names
        ]
        sequences = assets.tokenizer(
            texts, add_special_tokens=False, truncation=False, padding=False
        )["input_ids"]
        if len(sequences) != len(names) or any(not sequence for sequence in sequences):
            raise ValueError("tokenizer returned missing or empty sequences")
        canonical = json.dumps(
            request, sort_keys=True, separators=(",", ":"), allow_nan=False
        )
        results.append(
            {
                "request_index": index,
                "request_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
                "source": deepcopy(request.get("source")),
                "tokens": {
                    name: len(sequence)
                    for name, sequence in zip(names, sequences, strict=True)
                },
                "fits_budget": all(len(sequence) <= budget for sequence in sequences),
            }
        )
    if not results:
        raise ValueError("preflight needs at least one request")
    return {
        "schema": "micro-classifier/offline-prompt-budget/1",
        "allowed_use": "offline_tokenizer_preflight_only",
        "training_approved": False,
        "live_labeling_approved": False,
        "model_weights_loaded": False,
        "inference_calls": 0,
        "budget": budget,
        "token_counts_verified": True,
        "all_fit": all(row["fits_budget"] for row in results),
        "request_count": len(results),
        "over_budget_count": sum(not row["fits_budget"] for row in results),
        "max_tokens": max(count for row in results for count in row["tokens"].values()),
        "assets": deepcopy(assets.provenance),
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "results": results,
    }


def compare_compact_requests(requests, *, assets, budget=2048, float32_rows=False):
    requests = list(requests)
    compact = [
        compact_request_draft(request, float32_rows=float32_rows)
        for request in requests
    ]
    original_report = count_requests(requests, assets=assets, budget=budget)
    compact_report = count_requests(compact, assets=assets, budget=budget)
    comparisons = []
    for request, draft, original_row, compact_row in zip(
        requests,
        compact,
        original_report["results"],
        compact_report["results"],
        strict=True,
    ):
        if expand_compact_state(draft["state"]) != request["state"]:
            raise ValueError("comparison requires exact reconstruction")
        comparisons.append(
            {
                "request_index": original_row["request_index"],
                "source": deepcopy(original_row["source"]),
                "original_request_sha256": original_row["request_sha256"],
                "compact_request_sha256": compact_row["request_sha256"],
                "original_state_sha256": draft["representation"][
                    "original_state_sha256"
                ],
                "original_tokens": original_row["tokens"],
                "compact_tokens": compact_row["tokens"],
                "original_fits_budget": original_row["fits_budget"],
                "compact_fits_budget": compact_row["fits_budget"],
                "exact_roundtrip": True,
            }
        )
    return {
        "schema": (
            "micro-classifier/lossless-float32-prompt-comparison-draft/1"
            if float32_rows
            else "micro-classifier/lossless-prompt-comparison-draft/1"
        ),
        "representation_schema": compact[0]["representation"]["schema"],
        "allowed_use": "lossless_draft_tests_and_offline_comparison_only",
        "review_status": "unreviewed_draft",
        "live_labeling_approved": False,
        "training_approved": False,
        "model_weights_loaded": False,
        "inference_calls": 0,
        "token_counts_verified": True,
        "budget": budget,
        "request_count": len(comparisons),
        "exact_roundtrip_count": len(comparisons),
        "all_fit": compact_report["all_fit"],
        "over_budget_count": compact_report["over_budget_count"],
        "max_tokens": compact_report["max_tokens"],
        "original_all_fit": original_report["all_fit"],
        "original_over_budget_count": original_report["over_budget_count"],
        "original_max_tokens": original_report["max_tokens"],
        "assets": deepcopy(assets.provenance),
        "codec_source_sha256": compact[0]["representation"]["codec_source_sha256"],
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "results": comparisons,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episode", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=8, help="observations per episode")
    parser.add_argument("--budget", type=int, default=2048)
    parser.add_argument(
        "--repo-id",
        choices=("vllm-sr/d3-flash", "vllm-sr/d3-mini"),
        default="vllm-sr/d3-flash",
    )
    parser.add_argument(
        "--snapshot", type=Path, help="already-cached pinned snapshot only"
    )
    comparison = parser.add_mutually_exclusive_group()
    comparison.add_argument(
        "--compare-compact-draft",
        action="store_true",
        help="compare full state with the unreviewed lossless row-table draft",
    )
    comparison.add_argument(
        "--compare-float32-draft",
        action="store_true",
        help="compare the unreviewed exact float32 row-string draft",
    )
    args = parser.parse_args()
    if args.limit < 1 or not 1 <= args.budget <= 2048:
        parser.error("limit must be positive and budget between 1 and 2048")
    if args.output.exists():
        raise FileExistsError(args.output)
    requests = [
        request
        for path in args.episode
        for request in episode_requests(path, limit=args.limit)
    ]
    assets = load_prompt_assets(repo_id=args.repo_id, snapshot=args.snapshot)
    report = (
        compare_compact_requests(
            requests,
            assets=assets,
            budget=args.budget,
            float32_rows=args.compare_float32_draft,
        )
        if args.compare_compact_draft or args.compare_float32_draft
        else count_requests(requests, assets=assets, budget=args.budget)
    )
    report["episode_limit"] = args.limit
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        json.dump(report, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
    print(
        json.dumps(
            {
                name: report[name]
                for name in (
                    "request_count",
                    "budget",
                    "max_tokens",
                    "over_budget_count",
                    "all_fit",
                    "model_weights_loaded",
                    "inference_calls",
                )
            },
            sort_keys=True,
        )
    )
    return 0 if report["all_fit"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
