#!/usr/bin/env python3
"""Provider-driven Greenfield /work E2E runner.

Unlike the previous pilot, this runner contains no domain-specific OPEN questions, stage
answers or pre-rendered documents. It seeds only the user-provided requirement as GIVEN
input, then executes the real run_work.py coordinator for each requested stage.

A deterministic validation fixture provider may be used to test executor plumbing in CI,
but such a run is reported as PASS_EXECUTOR_E2E_FIXTURE_PROVIDER, never as Agent E2E.
Only provider_class=EXTERNAL_AGENT can produce PASS_AGENT_E2E_PROVIDER_EXECUTION.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


APPLY = _load("greenfield_apply", SCRIPT_DIR / "apply_canonical_delta.py")
WORK = _load("greenfield_work", SCRIPT_DIR / "run_work.py")
DEFAULT_STAGES = ["DECOMPOSE", "CLARIFY", "PROCESS", "DESIGN", "PROGRAM"]
SAFE_RE = re.compile(r"[^A-Za-z0-9_.-]+")


def _read(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON object required: {path}")
    return data


def _write(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def canonical_requirement_id(seed: dict[str, Any]) -> str:
    explicit = str(seed.get("canonical_requirement_id") or "").strip()
    if explicit:
        return explicit
    external = SAFE_RE.sub("_", str(seed["external_id"])).strip("_")
    return f"RQ-{external}"


def initialize_requirement(seed: dict[str, Any], store_path: Path, intake_artifact: str) -> dict[str, Any]:
    store = APPLY.load_store(store_path)
    rq_id = canonical_requirement_id(seed)
    if rq_id in store.get("entities", {}):
        return {"status": "EXISTING", "requirement_id": rq_id, "store_revision": store["revision"]}
    delta = {
        "schema_version": 1,
        "delta_id": f"GREENFIELD-INTAKE-{SAFE_RE.sub('_', str(seed['pilot_id']))}",
        "base_revision": store["revision"],
        "stage": "INTAKE",
        "source_artifact": intake_artifact,
        "operations": [{
            "op": "UPSERT_ENTITY",
            "id": rq_id,
            "entity_type": "RQ",
            "fields": {
                "external_id": seed["external_id"],
                "original_text": seed["requirement_text"],
                "source_document": seed.get("source_document"),
                "requirement_group": seed.get("requirement_group"),
            },
            "evidence_class": "GIVEN",
            "truth_status": "CANDIDATE",
            "note": "Greenfield user-provided requirement seed; no additional business fact invented",
        }],
    }
    result, next_store = APPLY.apply_delta(store, delta)
    if result["status"] != "APPLIED":
        raise ValueError(f"failed to initialize Greenfield requirement: {result}")
    APPLY.save_store(store_path, next_store)
    return {"status": "APPLIED", "requirement_id": rq_id, "store_revision": next_store["revision"]}


def run(
    root: Path,
    seed: dict[str, Any],
    provider: dict[str, Any],
    *,
    runtime_root: Path,
    stages: list[str] | None = None,
) -> dict[str, Any]:
    required = ["schema_version", "pilot_id", "mode", "external_id", "requirement_text"]
    missing = [key for key in required if key not in seed]
    if missing:
        raise ValueError(f"seed missing fields: {missing}")
    if seed["schema_version"] != 1 or seed["mode"] != "GREENFIELD":
        raise ValueError("Greenfield pilot requires schema_version=1 and mode=GREENFIELD")
    if not str(seed["requirement_text"]).strip():
        raise ValueError("requirement_text is empty")

    stages = stages or list(DEFAULT_STAGES)
    unknown = [stage for stage in stages if stage not in WORK.STAGE_INDEX]
    if unknown:
        raise ValueError(f"unsupported stages: {unknown}")

    runtime_root = runtime_root.resolve()
    root_resolved = root.resolve()
    runtime_root.relative_to(root_resolved)
    runtime_root.mkdir(parents=True, exist_ok=True)
    store_path = runtime_root / "canonical/store.json"
    intake_rel = runtime_root.relative_to(root_resolved).joinpath("intake-seed.json").as_posix()
    _write(root / intake_rel, {
        "schema_version": 1,
        "external_id": seed["external_id"],
        "requirement_text": seed["requirement_text"],
        "source_document": seed.get("source_document"),
    })
    init = initialize_requirement(seed, store_path, intake_rel)
    rq_id = init["requirement_id"]

    provider_class = str(provider.get("provider_class") or "UNKNOWN")
    if not provider.get("enabled", False):
        return {
            "schema_version": 2,
            "pilot_id": seed["pilot_id"],
            "pilot_kind": "PROVIDER_DRIVEN_GREENFIELD_WORK_E2E",
            "requirement_id": rq_id,
            "input": {"external_id": seed["external_id"], "requirement_text": seed["requirement_text"]},
            "provider_id": provider.get("provider_id"),
            "provider_class": provider_class,
            "actual_agent_provider_executed": False,
            "stage_results": [],
            "verdict": "NOT_EXECUTED_PROVIDER_UNAVAILABLE_OR_DISABLED",
            "limitations": ["Agent/LLM Provider가 연결되지 않아 실제 Stage 생성은 실행하지 않았다."],
        }

    results = []
    artifact_paths = []
    for stage in stages:
        artifact_rel = runtime_root.relative_to(root_resolved).joinpath("artifacts", f"{stage}_{WORK.STAGE_ARTIFACT_NAMES[stage]}").as_posix()
        plan = WORK.build_plan(
            root,
            target_id=rq_id,
            store_path=store_path,
            stage=stage,
            artifact=artifact_rel,
        )
        result = WORK.execute_plan(
            root,
            plan,
            provider_config=provider,
            run_dir=runtime_root / "runs" / stage,
            store_path=store_path,
        )
        results.append({"stage": stage, "execution": result})
        if (root / artifact_rel).is_file():
            artifact_paths.append(artifact_rel)
        if result.get("status") not in {"APPLIED", "IDEMPOTENT", "NO_CHANGE"}:
            break

    all_requested_executed = len(results) == len(stages)
    all_success = all(row["execution"].get("status") in {"APPLIED", "IDEMPOTENT", "NO_CHANGE"} for row in results)
    actual_agent = provider_class == "EXTERNAL_AGENT" and all_requested_executed and all_success
    if all_requested_executed and all_success and provider_class == "VALIDATION_FIXTURE":
        verdict = "PASS_EXECUTOR_E2E_FIXTURE_PROVIDER"
    elif actual_agent:
        verdict = "PASS_AGENT_E2E_PROVIDER_EXECUTION"
    elif all_requested_executed and all_success:
        verdict = "PASS_PROVIDER_E2E_UNCLASSIFIED_PROVIDER"
    else:
        verdict = "FAIL_GREENFIELD_WORK_E2E"

    return {
        "schema_version": 2,
        "pilot_id": seed["pilot_id"],
        "pilot_kind": "PROVIDER_DRIVEN_GREENFIELD_WORK_E2E",
        "requirement_id": rq_id,
        "input": {
            "source_document": seed.get("source_document"),
            "external_id": seed["external_id"],
            "requirement_group": seed.get("requirement_group"),
            "requirement_text": seed["requirement_text"],
            "existing_source_repository": seed.get("existing_source_repository"),
        },
        "requested_stages": stages,
        "provider_id": provider.get("provider_id"),
        "provider_class": provider_class,
        "actual_agent_provider_executed": actual_agent,
        "stage_results": results,
        "materialized_artifacts": artifact_paths,
        "canonical_revision": APPLY.load_store(store_path)["revision"],
        "business_fact_invention_measured_by_runner": False,
        "verdict": verdict,
        "limitations": [
            "Runner는 Stage별 의미 품질을 하드코딩하거나 판정하지 않는다; Agent Stage Result/Quality Gate를 검증한다.",
            "VALIDATION_FIXTURE Provider 성공은 실제 LLM/Agent E2E 성공으로 간주하지 않는다.",
            "사람 사용성 평가는 별도 실증이 필요하다.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run provider-driven Greenfield /work E2E without hardcoded domain outputs.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--seed", required=True)
    parser.add_argument("--provider-config", required=True)
    parser.add_argument("--runtime-root")
    parser.add_argument("--stages", default=",".join(DEFAULT_STAGES))
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    seed = _read(Path(args.seed))
    provider = _read(Path(args.provider_config))
    safe_pilot = SAFE_RE.sub("_", str(seed.get("pilot_id") or "pilot")).strip("_")
    runtime_root = Path(args.runtime_root) if args.runtime_root else root / "sdlc/runtime/validation/greenfield" / safe_pilot
    if not runtime_root.is_absolute():
        runtime_root = root / runtime_root
    try:
        result = run(root, seed, provider, runtime_root=runtime_root, stages=[x.strip().upper() for x in args.stages.split(",") if x.strip()])
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        result = {"schema_version": 2, "verdict": "ERROR", "error": str(exc), "actual_agent_provider_executed": False}
    _write(Path(args.output), result)
    print(json.dumps({
        "verdict": result.get("verdict"),
        "provider_class": result.get("provider_class"),
        "actual_agent_provider_executed": result.get("actual_agent_provider_executed"),
        "artifact_count": len(result.get("materialized_artifacts", [])),
    }, ensure_ascii=False))
    return 0 if result.get("verdict") in {
        "PASS_EXECUTOR_E2E_FIXTURE_PROVIDER",
        "PASS_AGENT_E2E_PROVIDER_EXECUTION",
        "PASS_PROVIDER_E2E_UNCLASSIFIED_PROVIDER",
        "NOT_EXECUTED_PROVIDER_UNAVAILABLE_OR_DISABLED",
    } else 2


if __name__ == "__main__":
    raise SystemExit(main())
