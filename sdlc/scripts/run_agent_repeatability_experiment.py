#!/usr/bin/env python3
"""Execute the same external Agent command repeatedly and measure semantic repeatability.

This runner does not provide an LLM. A real provider/Agent command must be supplied by the
project environment. Each run must write a Stage Result JSON and its referenced artifact
inside the run directory. Results are validated with validate_agent_stage_result.py and
compared using the same semantic fingerprint rules.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
VALIDATOR_PATH = SCRIPT_DIR / "validate_agent_stage_result.py"
SPEC = importlib.util.spec_from_file_location("stage_result_validator_repeatability", VALIDATOR_PATH)
VALIDATOR = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(VALIDATOR)


def _read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("config must be a JSON object")
    return data


def _validate_config(config: dict[str, Any]) -> None:
    if config.get("schema_version") != 1:
        raise ValueError("unsupported repeatability config schema")
    if not str(config.get("provider_id") or "").strip():
        raise ValueError("provider_id is required")
    run_count = config.get("run_count")
    if not isinstance(run_count, int) or run_count < 2 or run_count > 20:
        raise ValueError("run_count must be an integer between 2 and 20")
    command = config.get("command")
    enabled = bool(config.get("enabled", False))
    if enabled and (not isinstance(command, list) or not command or not all(isinstance(x, str) and x for x in command)):
        raise ValueError("enabled experiment requires a non-empty command array")
    result_filename = str(config.get("result_filename") or "stage-result.json")
    if Path(result_filename).is_absolute() or ".." in Path(result_filename).parts:
        raise ValueError("result_filename must be run-directory relative")


def _format_command(command: list[str], *, run_dir: Path, run_index: int, result_path: Path) -> list[str]:
    values = {
        "run_dir": str(run_dir),
        "run_index": str(run_index),
        "result_path": str(result_path),
    }
    return [part.format(**values) for part in command]


def run_experiment(config: dict[str, Any], output_root: Path) -> dict[str, Any]:
    _validate_config(config)
    provider_id = str(config["provider_id"])
    run_count = int(config["run_count"])
    result_filename = str(config.get("result_filename") or "stage-result.json")

    if not config.get("enabled", False):
        return {
            "schema_version": 1,
            "provider_id": provider_id,
            "run_count_requested": run_count,
            "run_count_executed": 0,
            "verdict": "NOT_EXECUTED_PROVIDER_UNAVAILABLE_OR_DISABLED",
            "runs": [],
            "semantic_match_count": 0,
            "semantic_match_rate": None,
            "actual_provider_executed": False,
            "llm_determinism_proven": False,
        }

    output_root.mkdir(parents=True, exist_ok=True)
    runs = []
    fingerprints: list[str | None] = []
    command_template = list(config["command"])

    for index in range(1, run_count + 1):
        run_dir = output_root / f"run-{index:02d}"
        run_dir.mkdir(parents=True, exist_ok=True)
        result_path = run_dir / result_filename
        command = _format_command(command_template, run_dir=run_dir, run_index=index, result_path=result_path)
        completed = subprocess.run(
            command,
            cwd=str(run_dir),
            text=True,
            capture_output=True,
            timeout=int(config.get("timeout_seconds", 120)),
            check=False,
        )
        run_record: dict[str, Any] = {
            "run_index": index,
            "command_exit_code": completed.returncode,
            "stdout": completed.stdout[-4000:],
            "stderr": completed.stderr[-4000:],
            "result_path": str(result_path),
        }
        if completed.returncode != 0 or not result_path.is_file():
            run_record["validation"] = None
            run_record["semantic_fingerprint"] = None
            runs.append(run_record)
            fingerprints.append(None)
            continue

        try:
            stage_result = VALIDATOR.load_json(result_path)
            validation = VALIDATOR.validate_stage_result(stage_result, run_dir)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            run_record["validation"] = {"status": "FAIL", "errors": [{"code": "RESULT_LOAD_FAILED", "message": str(exc)}]}
            run_record["semantic_fingerprint"] = None
            runs.append(run_record)
            fingerprints.append(None)
            continue
        run_record["validation"] = validation
        run_record["semantic_fingerprint"] = validation.get("semantic_fingerprint")
        runs.append(run_record)
        fingerprints.append(validation.get("semantic_fingerprint"))

    valid_fingerprints = [fp for fp in fingerprints if fp]
    first = valid_fingerprints[0] if valid_fingerprints else None
    match_count = sum(1 for fp in valid_fingerprints if fp == first) if first else 0
    all_commands_ok = all(row["command_exit_code"] == 0 for row in runs)
    all_valid = len(runs) == run_count and all(row.get("validation", {}).get("status") == "PASS" for row in runs)
    all_match = bool(first) and len(valid_fingerprints) == run_count and match_count == run_count

    if not all_commands_ok:
        verdict = "FAIL_PROVIDER_COMMAND"
    elif not all_valid:
        verdict = "FAIL_STAGE_RESULT_VALIDATION"
    elif not all_match:
        verdict = "FAIL_SEMANTIC_REPEATABILITY_MISMATCH"
    else:
        verdict = "PASS_REPEATED_PROVIDER_OUTPUT_SEMANTIC_MATCH"

    return {
        "schema_version": 1,
        "provider_id": provider_id,
        "run_count_requested": run_count,
        "run_count_executed": len(runs),
        "verdict": verdict,
        "runs": runs,
        "semantic_match_count": match_count,
        "semantic_match_rate": (match_count / run_count) if run_count else None,
        "actual_provider_executed": True,
        "llm_determinism_proven": False,
        "interpretation": "동일 Provider 명령의 관측된 Stage Result 의미 일치율이며 LLM의 이론적 결정론을 증명하지 않는다.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        result = run_experiment(_read_json(Path(args.config)), Path(args.run_root))
    except (OSError, json.JSONDecodeError, ValueError, subprocess.SubprocessError) as exc:
        print(f"ERROR: {exc}")
        return 2
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "provider_id": result["provider_id"],
        "verdict": result["verdict"],
        "run_count_executed": result["run_count_executed"],
        "semantic_match_rate": result["semantic_match_rate"],
    }, ensure_ascii=False))
    return 0 if result["verdict"] in {
        "PASS_REPEATED_PROVIDER_OUTPUT_SEMANTIC_MATCH",
        "NOT_EXECUTED_PROVIDER_UNAVAILABLE_OR_DISABLED",
    } else 1


if __name__ == "__main__":
    raise SystemExit(main())
