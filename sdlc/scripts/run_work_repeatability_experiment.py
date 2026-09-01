#!/usr/bin/env python3
"""Repeat the real /work executor against the same Canonical snapshot and input.

This closes the gap between a provider-command loop and the actual Harness execution path.
Each run resets the same scratch Canonical store, reuses the same target/stage/artifact,
executes run_work.py, validates the Stage Result and compares semantic fingerprints.

A validation fixture can prove runner wiring but cannot produce an Agent empirical PASS.
Only provider_class=EXTERNAL_AGENT is reported as actual_agent_provider_executed=true.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


WORK = _load("repeat_work_executor", SCRIPT_DIR / "run_work.py")
APPLY = _load("repeat_apply", SCRIPT_DIR / "apply_canonical_delta.py")


def _read(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON object required: {path}")
    return data


def _write(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_experiment(
    root: Path,
    provider: dict[str, Any],
    *,
    target_id: str,
    stage: str,
    artifact: str,
    baseline_store: dict[str, Any],
    run_root: Path,
    run_count: int,
) -> dict[str, Any]:
    if run_count < 2 or run_count > 20:
        raise ValueError("run_count must be between 2 and 20")
    provider_class = str(provider.get("provider_class") or "UNKNOWN")
    if not provider.get("enabled", False):
        return {
            "schema_version": 1,
            "provider_id": provider.get("provider_id"),
            "provider_class": provider_class,
            "run_count_requested": run_count,
            "run_count_executed": 0,
            "actual_agent_provider_executed": False,
            "verdict": "NOT_EXECUTED_PROVIDER_UNAVAILABLE_OR_DISABLED",
            "runs": [],
            "semantic_match_rate": None,
            "llm_determinism_proven": False,
        }

    root = root.resolve()
    run_root = run_root.resolve()
    run_root.mkdir(parents=True, exist_ok=True)
    scratch_store = run_root / "scratch-store.json"
    artifact_path, artifact_rel = WORK.safe_repo_path(root, artifact)
    runs = []
    fingerprints = []

    for index in range(1, run_count + 1):
        APPLY.save_store(scratch_store, json.loads(json.dumps(baseline_store)))
        if artifact_path.exists():
            artifact_path.unlink()
        plan = WORK.build_plan(
            root,
            target_id=target_id,
            store_path=scratch_store,
            stage=stage,
            artifact=artifact_rel,
        )
        plan["planned_at"] = "REPEATABILITY_FIXED_INPUT"
        result = WORK.execute_plan(
            root,
            plan,
            provider_config=provider,
            run_dir=run_root / f"run-{index:02d}",
            store_path=scratch_store,
        )
        fingerprint = (result.get("validation") or {}).get("semantic_fingerprint")
        runs.append({
            "run_index": index,
            "status": result.get("status"),
            "semantic_fingerprint": fingerprint,
            "validation_status": (result.get("validation") or {}).get("status"),
            "canonical_applied": result.get("canonical_applied", False),
        })
        fingerprints.append(fingerprint)

    first = fingerprints[0] if fingerprints else None
    match_count = sum(1 for value in fingerprints if first and value == first)
    all_success = all(row["status"] in {"APPLIED", "IDEMPOTENT", "NO_CHANGE"} for row in runs)
    all_fingerprints = bool(first) and all(value for value in fingerprints)
    all_match = all_fingerprints and match_count == run_count
    actual_agent = provider_class == "EXTERNAL_AGENT" and all_success

    if not all_success:
        verdict = "FAIL_WORK_EXECUTION"
    elif not all_match:
        verdict = "FAIL_SEMANTIC_REPEATABILITY_MISMATCH"
    elif provider_class == "EXTERNAL_AGENT":
        verdict = "PASS_REPEATED_AGENT_WORK_OUTPUT_SEMANTIC_MATCH"
    elif provider_class == "VALIDATION_FIXTURE":
        verdict = "PASS_WORK_REPEATABILITY_FIXTURE_PROVIDER"
    else:
        verdict = "PASS_WORK_REPEATABILITY_UNCLASSIFIED_PROVIDER"

    return {
        "schema_version": 1,
        "provider_id": provider.get("provider_id"),
        "provider_class": provider_class,
        "target_id": target_id,
        "stage": stage,
        "artifact": artifact_rel,
        "run_count_requested": run_count,
        "run_count_executed": len(runs),
        "actual_agent_provider_executed": actual_agent,
        "verdict": verdict,
        "runs": runs,
        "semantic_match_count": match_count,
        "semantic_match_rate": match_count / run_count,
        "llm_determinism_proven": False,
        "interpretation": "동일 Canonical snapshot/target/stage/document 입력에 대한 실제 /work 실행 결과의 의미 일치율이다. LLM 이론적 결정론을 주장하지 않는다.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Repeat the real /work path against the same input and Canonical snapshot.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--provider-config", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--stage", required=True)
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--baseline-store")
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--run-count", type=int, default=3)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    provider = _read(Path(args.provider_config))
    baseline = APPLY.load_store(Path(args.baseline_store)) if args.baseline_store else APPLY.empty_store()
    try:
        result = run_experiment(
            root,
            provider,
            target_id=args.target,
            stage=args.stage.upper(),
            artifact=args.artifact,
            baseline_store=baseline,
            run_root=Path(args.run_root),
            run_count=args.run_count,
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        result = {"schema_version": 1, "verdict": "ERROR", "error": str(exc), "actual_agent_provider_executed": False}
    _write(Path(args.output), result)
    print(json.dumps({
        "verdict": result.get("verdict"),
        "run_count_executed": result.get("run_count_executed"),
        "semantic_match_rate": result.get("semantic_match_rate"),
        "actual_agent_provider_executed": result.get("actual_agent_provider_executed"),
    }, ensure_ascii=False))
    return 0 if result.get("verdict") in {
        "PASS_REPEATED_AGENT_WORK_OUTPUT_SEMANTIC_MATCH",
        "PASS_WORK_REPEATABILITY_FIXTURE_PROVIDER",
        "PASS_WORK_REPEATABILITY_UNCLASSIFIED_PROVIDER",
        "NOT_EXECUTED_PROVIDER_UNAVAILABLE_OR_DISABLED",
    } else 2


if __name__ == "__main__":
    raise SystemExit(main())
