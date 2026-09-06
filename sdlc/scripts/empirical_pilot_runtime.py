#!/usr/bin/env python3
"""Prepare, validate and summarize observed empirical pilot evidence.

This runtime intentionally does not execute an External Agent or impersonate a Human pilot.
It only makes the evidence lifecycle executable and fail-closed:

  init      copy a NOT_RUN template into the project runtime area
  validate  validate one evidence JSON with the empirical evidence contract
  status    validate all known pilot evidence files and summarize their current state

Examples:
  python sdlc/scripts/empirical_pilot_runtime.py init --pilot external-agent-tailoring
  python sdlc/scripts/empirical_pilot_runtime.py validate --input sdlc/runtime/pilots/external-agent-tailoring.json
  python sdlc/scripts/empirical_pilot_runtime.py status
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
VALIDATOR_PATH = SCRIPT_DIR / "validate_empirical_pilot_evidence.py"

SPEC = importlib.util.spec_from_file_location("empirical_pilot_validator_runtime", VALIDATOR_PATH)
VALIDATOR = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(VALIDATOR)

PILOT_SPECS: dict[str, dict[str, str]] = {
    "external-agent-tailoring": {
        "pilot_type": "EXTERNAL_AGENT_TAILORING_SEMANTIC_EQUIVALENCE",
        "template": "sdlc/validation/pilots/external-agent-tailoring-pilot.example.json",
        "default_evidence": "sdlc/runtime/pilots/external-agent-tailoring.json",
    },
    "human-first-use": {
        "pilot_type": "HUMAN_FIRST_USE",
        "template": "sdlc/validation/pilots/human-first-use-pilot.example.json",
        "default_evidence": "sdlc/runtime/pilots/human-first-use.json",
    },
    "brownfield-reconciliation": {
        "pilot_type": "BROWNFIELD_RECONCILIATION",
        "template": "sdlc/validation/pilots/brownfield-reconciliation-pilot.example.json",
        "default_evidence": "sdlc/runtime/pilots/brownfield-reconciliation.json",
    },
}


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON object required: {path}")
    return data


def _root(value: str | None) -> Path:
    return Path(value or REPO_ROOT).resolve()


def _resolve_under_root(root: Path, value: str | None, default_rel: str) -> Path:
    candidate = Path(value) if value else Path(default_rel)
    if not candidate.is_absolute():
        candidate = root / candidate
    resolved = candidate.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"path must remain under --root: {resolved}") from exc
    return resolved


def init_pilot(*, root: Path, pilot: str, output: str | None = None) -> dict[str, Any]:
    spec = PILOT_SPECS[pilot]
    template = root / spec["template"]
    if not template.is_file():
        raise FileNotFoundError(f"pilot template missing: {template}")
    destination = _resolve_under_root(root, output, spec["default_evidence"])
    if destination.exists():
        raise FileExistsError(f"pilot evidence already exists: {destination}")

    data = _load_json(template)
    if data.get("pilot_type") != spec["pilot_type"]:
        raise ValueError(f"template pilot_type mismatch: {template}")
    if data.get("execution_status") != "NOT_RUN":
        raise ValueError(f"pilot template must start as NOT_RUN: {template}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "schema_version": 1,
        "status": "PILOT_INITIALIZED",
        "pilot": pilot,
        "pilot_type": spec["pilot_type"],
        "execution_status": "NOT_RUN",
        "empirical_pass": False,
        "evidence_file": str(destination.relative_to(root)),
        "template": spec["template"],
        "next_command": f"python sdlc/scripts/empirical_pilot_runtime.py validate --input {destination.relative_to(root)}",
        "boundary": "init only prepares evidence; it does not execute or observe an Agent/Human/Brownfield pilot",
    }


def validate_file(path: Path) -> dict[str, Any]:
    data = _load_json(path)
    result = VALIDATOR.validate(data)
    result["evidence_file"] = str(path)
    return result


def status(*, root: Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    verdict_counts: dict[str, int] = {}
    empirical_pass_count = 0

    for pilot, spec in PILOT_SPECS.items():
        evidence = root / spec["default_evidence"]
        if evidence.is_file():
            try:
                result = validate_file(evidence)
            except (OSError, json.JSONDecodeError, ValueError) as exc:
                result = {
                    "pilot_type": spec["pilot_type"],
                    "execution_status": "UNKNOWN",
                    "verdict": "FAIL_INSUFFICIENT_EVIDENCE",
                    "empirical_pass": False,
                    "errors": [f"EVIDENCE_LOAD_FAILED: {exc}"],
                }
            source = "RUNTIME_EVIDENCE"
        else:
            result = {
                "pilot_type": spec["pilot_type"],
                "execution_status": "NOT_RUN",
                "verdict": "NOT_RUN",
                "empirical_pass": False,
                "errors": [],
            }
            source = "EVIDENCE_FILE_MISSING"

        verdict = str(result.get("verdict") or "UNKNOWN")
        verdict_counts[verdict] = verdict_counts.get(verdict, 0) + 1
        empirical = bool(result.get("empirical_pass", False))
        empirical_pass_count += int(empirical)
        rows.append({
            "pilot": pilot,
            "pilot_type": spec["pilot_type"],
            "evidence_file": spec["default_evidence"],
            "source": source,
            "execution_status": result.get("execution_status"),
            "verdict": verdict,
            "empirical_pass": empirical,
            "errors": result.get("errors", []),
        })

    return {
        "schema_version": 1,
        "status": "EMPIRICAL_PILOT_STATUS",
        "pilot_count": len(rows),
        "empirical_pass_count": empirical_pass_count,
        "all_empirical_pass": empirical_pass_count == len(rows),
        "verdict_counts": verdict_counts,
        "pilots": rows,
        "production_ready_claimed": False,
        "interpretation": "Missing or NOT_RUN evidence remains NOT_RUN. CI/fixture success is not substituted for observed empirical evidence.",
    }


def _write_optional(path: str | None, payload: dict[str, Any], *, root: Path) -> None:
    if not path:
        return
    output = _resolve_under_root(root, path, path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Empirical pilot evidence runtime")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="create one NOT_RUN pilot evidence file")
    p_init.add_argument("--pilot", choices=sorted(PILOT_SPECS), required=True)
    p_init.add_argument("--root")
    p_init.add_argument("--output")

    p_validate = sub.add_parser("validate", help="validate one pilot evidence file")
    p_validate.add_argument("--input", required=True)
    p_validate.add_argument("--root")
    p_validate.add_argument("--output")

    p_status = sub.add_parser("status", help="summarize all pilot evidence states")
    p_status.add_argument("--root")
    p_status.add_argument("--output")

    args = parser.parse_args(argv)
    root = _root(getattr(args, "root", None))

    try:
        if args.command == "init":
            result = init_pilot(root=root, pilot=args.pilot, output=args.output)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0

        if args.command == "validate":
            input_path = _resolve_under_root(root, args.input, args.input)
            result = validate_file(input_path)
            _write_optional(args.output, result, root=root)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if result["verdict"] in {
                "NOT_RUN",
                "PASS_OBSERVED_EMPIRICAL_PILOT",
                "FAIL_OBSERVED_EMPIRICAL_PILOT",
            } else 1

        result = status(root=root)
        _write_optional(args.output, result, root=root)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({
            "status": "EMPIRICAL_PILOT_RUNTIME_FAILED",
            "error": str(exc),
            "production_ready_claimed": False,
        }, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
