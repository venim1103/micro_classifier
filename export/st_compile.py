"""Plan compile-only STM32N6 experiments; ST software is not bundled."""

import argparse
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

PROFILE = "profile-internal-memories-only--default"
ARTIFACT_NAMES = {"float.onnx", "int8.prepared.onnx", "int8.onnx"}


def file_info(path):
    payload = Path(path).read_bytes()
    return {"bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}


def build_plan(manifest_path, output, *, expected_version, executable="stedgeai"):
    manifest_path = Path(manifest_path).resolve()
    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError("compiler output must be a new directory")
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", expected_version):
        raise ValueError("expected ST version must be an exact major.minor.patch")
    if not executable or "\x00" in str(executable):
        raise ValueError("compiler executable must be nonempty")
    executable = str(executable)
    if "/" in executable:
        executable = str(Path(executable).expanduser().resolve())
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("schema") != "micro-classifier/m1a-host/1":
        raise ValueError("unsupported host manifest schema")
    cases = manifest.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("manifest must contain probe cases")
    jobs = []
    seen = set()
    for row in cases:
        name = row.get("case", "")
        if not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", name) or name in seen:
            raise ValueError("case names must be safe and unique")
        seen.add(name)
        if row.get("untrained") is not True:
            raise ValueError("only untrained M1a probes are supported")
        artifacts = row.get("artifacts", {})
        if set(artifacts) != ARTIFACT_NAMES:
            raise ValueError("manifest must describe all three probe artifacts")
        inputs = {}
        for filename, metadata in artifacts.items():
            path = (manifest_path.parent / name / filename).resolve()
            if not path.is_relative_to(manifest_path.parent):
                raise ValueError("artifact path escapes the manifest directory")
            if file_info(path) != metadata:
                raise ValueError(f"artifact hash/size mismatch: {name}/{filename}")
            inputs[filename] = {"path": str(path), **metadata}
        destination = output / name
        jobs.append(
            {
                "case": name,
                "inputs": inputs,
                "numerical_smoke": row["numerical_smoke"],
                "argv": [
                    executable,
                    "generate",
                    "--model",
                    inputs["int8.onnx"]["path"],
                    "--target",
                    "stm32n6",
                    "--st-neural-art",
                    PROFILE,
                    "--workspace",
                    str(destination / "workspace"),
                    "--output",
                    str(destination / "generated"),
                    "--verbosity",
                    "2",
                ],
            }
        )
    return {
        "schema": "micro-classifier/m1a-st-plan/1",
        "status": "planned_not_executed",
        "source_manifest": {"path": str(manifest_path), **file_info(manifest_path)},
        "runner_sha256": file_info(__file__)["sha256"],
        "output": str(output),
        "expected_version": expected_version,
        "executable": executable,
        "profile": PROFILE,
        "jobs": jobs,
        "compiler_executed": False,
        "milestone_passed": False,
        "board_measured": False,
    }


def invoke(argv, log_path, directory, timeout):
    started = time.monotonic()
    result = {"argv": argv, "returncode": None, "process_started": False}
    with log_path.open("xb") as log:
        try:
            process = subprocess.Popen(
                argv,
                cwd=directory,
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        except OSError as error:
            result.update(status="launch_failed", error=str(error))
        else:
            result["process_started"] = True
            try:
                result["returncode"] = process.wait(timeout=timeout)
                result["status"] = "ok" if result["returncode"] == 0 else "failed"
            except (subprocess.TimeoutExpired, KeyboardInterrupt) as error:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                result["returncode"] = process.wait()
                result["status"] = (
                    "timeout"
                    if isinstance(error, subprocess.TimeoutExpired)
                    else "interrupted"
                )
    result["host_wall_seconds"] = time.monotonic() - started
    return result


def execute_plan(plan, *, timeout=600):
    if os.name != "posix":
        raise ValueError("compiler execution currently requires POSIX process groups")
    if isinstance(timeout, bool) or not isinstance(timeout, int) or timeout < 1:
        raise ValueError("timeout must be a positive integer in seconds")
    fresh = build_plan(
        plan["source_manifest"]["path"],
        plan["output"],
        expected_version=plan["expected_version"],
        executable=plan["executable"],
    )
    if fresh != plan:
        raise ValueError("plan or its inputs changed; rebuild the plan")
    executable = shutil.which(plan["executable"])
    if executable is None:
        raise FileNotFoundError("ST executable not found; nothing was executed")
    executable = str(Path(executable).resolve())
    identity = {"path": executable, **file_info(executable)}
    output = Path(plan["output"])
    output.mkdir(parents=True, exist_ok=False)
    (output / "plan.json").write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n")
    report = {
        "schema": "micro-classifier/m1a-st-run/1",
        "created_utc": datetime.now(UTC).isoformat(),
        "status": "version_check_failed",
        "tool_executable": identity,
        "tool_bundle_fully_hashed": False,
        "source_manifest": plan["source_manifest"],
        "runner_sha256": plan["runner_sha256"],
        "timeout_seconds_per_command": timeout,
        "commands": [],
        "cases": [],
        "compiler_executed": False,
        "generate_attempted": False,
        "milestone_passed": False,
        "board_measured": False,
        "metrics_reviewed": False,
    }
    version = invoke(
        [executable, "--version"], output / "version.log", output, min(timeout, 60)
    )
    report["commands"].append(version)
    report["compiler_executed"] = version["process_started"]
    versions = re.findall(
        r"\bST Edge AI Core\s+v?([0-9]+\.[0-9]+\.[0-9]+)(?![\w.-])",
        (output / "version.log").read_text(errors="replace"),
    )
    report["reported_versions"] = versions
    if version["status"] == "ok" and set(versions) == {plan["expected_version"]}:
        tools = invoke(
            [executable, "--tools-version"],
            output / "tools-version.log",
            output,
            min(timeout, 60),
        )
        report["commands"].append(tools)
        report["status"] = "tools_version_failed"
        if tools["status"] == "ok":
            report["status"] = "generated_reports_pending_review"
            for job in plan["jobs"]:
                destination = output / job["case"]
                destination.mkdir()
                argv = [executable, *job["argv"][1:]]
                report["generate_attempted"] = True
                result = invoke(
                    argv, destination / "compiler.log", destination, timeout
                )
                info_paths = [
                    destination / folder / "network_c_info.json"
                    for folder in ("workspace", "generated")
                ]
                required_present = (
                    destination / "generated" / "network_generate_report.txt"
                ).is_file() and any(path.is_file() for path in info_paths)
                if result["status"] == "ok" and not required_present:
                    result["status"] = "missing_reports"
                report["cases"].append(
                    {
                        "case": job["case"],
                        "command": result,
                        "required_reports_present": required_present,
                        "numerical_smoke": job["numerical_smoke"],
                    }
                )
                if result["status"] != "ok":
                    report["status"] = "compile_failures"
                if result["status"] == "interrupted":
                    break
    report["files"] = {}
    for path in sorted(output.rglob("*")):
        if path.is_symlink():
            report["files"][str(path.relative_to(output))] = {
                "symlink_not_hashed": str(path.readlink())
            }
        elif path.is_file():
            report["files"][str(path.relative_to(output))] = file_info(path)
    with (output / "result.json").open("x") as stream:
        json.dump(report, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-version", required=True)
    parser.add_argument("--executable", default="stedgeai")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()
    try:
        plan = build_plan(
            args.manifest,
            args.output,
            expected_version=args.expected_version,
            executable=args.executable,
        )
        report = execute_plan(plan, timeout=args.timeout) if args.execute else plan
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.error(str(error))
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
    if args.execute and report["status"] != "generated_reports_pending_review":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
