"""Offline host/Arm reference build evidence, not linked firmware or fit proof."""

import argparse
import csv
import io
import json
import os
import struct
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from interface import native_verify

ROOT = native_verify.ROOT
OPTIMIZATIONS = ("-O0", "-O2", "-Os")
TOOLS = {
    "host_cc": "cc",
    "host_size": "size",
    "host_nm": "nm",
    "host_readelf": "readelf",
    "arm_cc": "arm-none-eabi-gcc",
    "arm_size": "arm-none-eabi-size",
    "arm_nm": "arm-none-eabi-nm",
    "arm_readelf": "arm-none-eabi-readelf",
}


def audit_sources():
    return {
        **native_verify.source_records(),
        "interface/build_audit.py": native_verify.file_record(Path(__file__)),
    }


def write_json(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")


def diagnostic_text(value):
    return value.decode(errors="replace") if isinstance(value, bytes) else value or ""


def run_logged(command, output):
    record = {"argv": command, "cwd": str(ROOT), "locale": "C"}
    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
            env={**os.environ, "LC_ALL": "C"},
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
    except subprocess.TimeoutExpired as error:
        write_json(
            output,
            {
                **record,
                "timed_out": True,
                "stdout": diagnostic_text(error.stdout),
                "stderr": diagnostic_text(error.stderr),
            },
        )
        raise
    except OSError as error:
        write_json(output, {**record, "launch_error": str(error)})
        raise
    write_json(
        output,
        {
            **record,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        },
    )
    result.check_returncode()
    return result.stdout


def parse_sections(text):
    lines = [line.split() for line in text.splitlines() if line.strip()]
    if (
        len(lines) < 4
        or lines[0][-1] != ":"
        or lines[1] != ["section", "size", "addr"]
        or len(lines[-1]) != 2
        or lines[-1][0] != "Total"
        or not lines[-1][1].isdecimal()
    ):
        raise ValueError("unsupported GNU size SysV output")
    sections = []
    for row in lines[2:-1]:
        if len(row) != 3 or not all(value.isdecimal() for value in row[1:]):
            raise ValueError("invalid GNU size section row")
        sections.append({"name": row[0], "bytes": int(row[1]), "address": int(row[2])})
    if len({row["name"] for row in sections}) != len(sections) or sum(
        row["bytes"] for row in sections
    ) != int(lines[-1][1]):
        raise ValueError("GNU size duplicate section or inconsistent total")
    return sections


def parse_undefined(text):
    symbols = []
    for line in text.splitlines():
        if not line.strip():
            continue
        row = line.split()
        if len(row) != 2 or row[1] not in ("U", "w", "v"):
            raise ValueError("unsupported GNU nm undefined-symbol output")
        symbols.append({"name": row[0], "type": row[1]})
    if len({row["name"] for row in symbols}) != len(symbols):
        raise ValueError("duplicate undefined symbol")
    return symbols


def parse_stack(text):
    rows = []
    for fields in csv.reader(io.StringIO(text), delimiter="\t", strict=True):
        if not fields:
            continue
        if (
            len(fields) != 3
            or not fields[1].isdecimal()
            or fields[2] not in ("static", "dynamic", "dynamic,bounded")
        ):
            raise ValueError("unsupported GCC stack-usage row")
        location = fields[0].rsplit(":", 3)
        if (
            len(location) != 4
            or not location[0]
            or not location[3]
            or not all(value.isdecimal() and int(value) > 0 for value in location[1:3])
        ):
            raise ValueError("invalid GCC stack source location")
        source, line, column, function = location
        rows.append(
            {
                "source": source,
                "line": int(line),
                "column": int(column),
                "function": function,
                "bytes": int(fields[1]),
                "qualifier": fields[2],
            }
        )
    identities = {(row["source"], row["function"]) for row in rows}
    if not rows or len(identities) != len(rows):
        raise ValueError("empty or duplicate GCC stack evidence")
    return rows


def elf_identity(path, target):
    data = path.read_bytes()
    if len(data) < 20 or data[:4] != b"\x7fELF" or data[4] not in (1, 2):
        raise ValueError("object is not ELF32/ELF64")
    if len(data) < (52 if data[4] == 1 else 64):
        raise ValueError("truncated ELF header")
    if data[5:7] != b"\x01\x01":
        raise ValueError("only current little-endian ELF is supported")
    file_type, machine = struct.unpack_from("<HH", data, 16)
    if file_type != 1 or (target == "arm" and (machine != 40 or data[4] != 1)):
        raise ValueError("expected relocatable object for selected target")
    return {"class_bits": 32 if data[4] == 1 else 64, "machine": machine, "type": "REL"}


def inspect_object(directory, source, target, optimization, tools):
    directory.mkdir()
    object_path = directory / "reference.o"
    command = [
        tools[f"{target}_cc"]["path"],
        "-std=c11",
        optimization,
        "-Wall",
        "-Wextra",
        "-Werror",
        "-pedantic",
        "-fstack-usage",
        *(["-mcpu=cortex-m55", "-mthumb"] if target == "arm" else []),
        "-I",
        str(ROOT / "firmware/include"),
        "-c",
        str(source.relative_to(ROOT)),
        "-o",
        str(object_path),
    ]
    run_logged(command, directory / "compile.json")
    identity = elf_identity(object_path, target)
    sections = parse_sections(
        run_logged(
            [
                tools[f"{target}_size"]["path"],
                "--format=sysv",
                "--radix=10",
                str(object_path),
            ],
            directory / "sections.json",
        )
    )
    symbols = parse_undefined(
        run_logged(
            [
                tools[f"{target}_nm"]["path"],
                "--format=posix",
                "--undefined-only",
                str(object_path),
            ],
            directory / "undefined.json",
        )
    )
    run_logged(
        [
            tools[f"{target}_readelf"]["path"],
            "--file-header",
            "--section-headers",
            "--arch-specific",
            "--wide",
            str(object_path),
        ],
        directory / "elf.json",
    )
    stack = parse_stack((directory / "reference.su").read_text())
    return {
        "source": str(source.relative_to(ROOT)),
        "target": target,
        "optimization": optimization,
        "elf": identity,
        "sections": sections,
        "undefined_symbols": symbols,
        "stack_usage": stack,
        "max_reported_function_stack_bytes": max(row["bytes"] for row in stack),
        "unbounded_dynamic_functions": [
            row["function"] for row in stack if row["qualifier"] == "dynamic"
        ],
        "artifact_directory": str(directory),
    }


def run_audit(output, work_dir, *, cases=128, seed=20261019):
    native_verify.validate_configuration(cases, seed)
    output, work_dir = Path(output).expanduser(), Path(work_dir).expanduser()
    if output.is_symlink() or work_dir.is_symlink():
        raise ValueError("audit outputs must not be symlinks")
    output, work_dir = output.resolve(), work_dir.resolve()
    if output.exists() or work_dir.exists():
        raise FileExistsError("audit report and work directory must be fresh")
    if (
        output == work_dir
        or output.is_relative_to(work_dir)
        or work_dir.is_relative_to(output)
    ):
        raise ValueError("audit report and work directory must not contain each other")
    sources = audit_sources()
    tools = {
        role: native_verify.compiler_identity(name) for role, name in TOOLS.items()
    }
    work_dir.mkdir(parents=True)
    objects, host_runs = [], []
    for optimization in OPTIMIZATIONS:
        matrix_dir = work_dir / optimization[1:]
        matrix_dir.mkdir()
        host_dir = matrix_dir / "host-verification"
        host_dir.mkdir()
        try:
            codec, build = native_verify.build_native(
                host_dir, compiler=tools["host_cc"]["path"], optimization=optimization
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
            write_json(
                host_dir / "failure.json",
                {
                    "argv": error.cmd,
                    "error": str(error),
                    "stdout": diagnostic_text(error.stdout),
                    "stderr": diagnostic_text(error.stderr),
                },
            )
            raise
        write_json(host_dir / "build.json", build)
        evidence = native_verify.verification_evidence(codec, cases=cases, seed=seed)
        write_json(host_dir / "evidence.json", evidence)
        host_runs.append(
            {"optimization": optimization, "build": build, "evidence": evidence}
        )
        for target in ("host", "arm"):
            for source in native_verify.SOURCES:
                objects.append(
                    inspect_object(
                        matrix_dir / f"{target}-{source.stem}",
                        source,
                        target,
                        optimization,
                        tools,
                    )
                )
    native_verify.require(
        len({row["evidence"]["result_sha256"] for row in host_runs}) == 1,
        "optimization-level synthetic parity",
    )
    native_verify.require(audit_sources() == sources, "audit source stability")
    for record in tools.values():
        native_verify.require(
            native_verify.file_record(record["path"])
            == {key: record[key] for key in ("bytes", "sha256")},
            "audit tool stability",
        )
    artifacts = {}
    for path in sorted(work_dir.rglob("*")):
        if path.is_symlink():
            raise ValueError("audit artifacts must not be symlinks")
        if path.is_file():
            artifacts[str(path.relative_to(work_dir))] = native_verify.file_record(path)
    report = {
        "schema": "micro-classifier/reference-build-audit/1",
        "created_at": datetime.now(UTC).isoformat(),
        "status": "reference_build_checks_passed",
        "scope": {
            "synthetic_only": True,
            "task_data": False,
            "training_enabled": False,
            "model_loaded": False,
            "arm_compile_only": True,
            "board_executed": False,
            "linked_firmware": False,
            "memory_fit_qualified": False,
            "full_stack_bound": False,
            "safety_qualified": False,
        },
        "sources": sources,
        "tools": tools,
        "work_dir": str(work_dir),
        "host_runs": host_runs,
        "objects": objects,
        "artifacts": artifacts,
        "limits": [
            "host fixtures only; no Arm execution, target linking or libm qualification",
            "per-function GCC stack reports are not call-chain or full-program bounds",
            "inlining, external callees, interrupts and runtime overhead remain unqualified",
            "object section listings include metadata and are not linked ROM/RAM footprints",
            "undefined symbols are per-object requirements, not a linked dependency closure",
            "compiler/tool hashes do not attest complete toolchains or libraries",
            "no adopted size/stack/latency threshold, safety policy or architecture",
            "fresh paths prevent accidental reuse, not concurrent adversarial filesystem races",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    write_json(output, report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--work-dir", required=True, type=Path)
    parser.add_argument("--cases", type=int, default=128)
    parser.add_argument("--seed", type=int, default=20261019)
    arguments = parser.parse_args(argv)
    try:
        report = run_audit(
            arguments.output,
            arguments.work_dir,
            cases=arguments.cases,
            seed=arguments.seed,
        )
    except (OSError, ValueError, subprocess.SubprocessError, csv.Error) as error:
        parser.exit(1, f"reference build audit failed: {error}\n")
    print(
        json.dumps(
            {
                "status": report["status"],
                "objects": len(report["objects"]),
                "host_runs": len(report["host_runs"]),
            }
        )
    )


if __name__ == "__main__":
    main()
