#!/usr/bin/env python3
"""Execute one AI-SDLC /work stage with explicit target/stage/artifact re-entry support.

The executor is deliberately small. It does not implement an LLM; a project-configured
Agent/LLM command receives a deterministic work-context JSON and must materialize the
selected artifact plus Stage Result envelope. The executor then validates target scope,
Stage Result, Canonical delta and applies the delta atomically.

Key usability rule: target identity and stage/document selection are independent.
Examples:
  --target RQ-001                         # continue from the target's current state
  --target PGM-001 --stage PROGRAM       # revise Program stage for a PGM
  --target RQ-001 --stage DESIGN --artifact docs/design/RQ-001.md
  --target ANA-001 --stage DESIGN --artifact docs/analysis/ANA-001.md

An arbitrary target ID may be used even when it is not yet in Canonical, but then an
explicit stage or an artifact with stage metadata is required. Existing unrelated
Canonical entities may never be mutated just because a provider can see the repository.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


APPLY = _load_module("work_apply_canonical", SCRIPT_DIR / "apply_canonical_delta.py")
VALIDATOR = _load_module("work_stage_validator", SCRIPT_DIR / "validate_agent_stage_result.py")

STAGES = [
    "INTAKE", "DECOMPOSE", "CLARIFY", "PROCESS", "DISCOVERY", "IMPACT",
    "DESIGN", "PROGRAM", "DEVELOPMENT", "TEST", "VERIFY", "KNOWLEDGE_PROMOTION",
]
STAGE_INDEX = {stage: i for i, stage in enumerate(STAGES)}
TYPE_DEFAULT_STAGE = {
    "RQ": "DECOMPOSE",
    "FR": "DESIGN",
    "BR": "CLARIFY",
    "SCN": "PROCESS",
    "PROC": "PROCESS",
    "PGM": "PROGRAM",
    "TASK": "DEVELOPMENT",
    "AC": "TEST",
    "TC": "TEST",
}
STAGE_ARTIFACT_NAMES = {
    "INTAKE": "requirement.md",
    "DECOMPOSE": "requirement.md",
    "CLARIFY": "interview-questions.md",
    "PROCESS": "process-analysis.md",
    "DISCOVERY": "impact-analysis.md",
    "IMPACT": "impact-analysis.md",
    "DESIGN": "functional-design.md",
    "PROGRAM": "program-spec.md",
    "DEVELOPMENT": "implementation-result.md",
    "TEST": "test-scenario.md",
    "VERIFY": "verification-result.md",
    "KNOWLEDGE_PROMOTION": "operations-knowledge.md",
}
FRONTMATTER_STAGE_RE = re.compile(r"^stage:\s*[\"']?([A-Z_]+)", re.M)
GENERATED_BY_STAGE_RE = re.compile(r"^\s*stage:\s*([A-Z_]+)\s*$", re.M)
SAFE_TARGET_RE = re.compile(r"[^A-Za-z0-9_.-]+")


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON object required: {path}")
    return data


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def safe_repo_path(root: Path, raw: str) -> tuple[Path, str]:
    rel = Path(raw)
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError(f"repository-relative safe path required: {raw}")
    root_resolved = root.resolve()
    resolved = (root_resolved / rel).resolve()
    resolved.relative_to(root_resolved)
    return resolved, rel.as_posix()


def infer_artifact_stage(path: Path) -> str | None:
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    frontmatter = text
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end >= 0:
            frontmatter = text[4:end]
    match = FRONTMATTER_STAGE_RE.search(frontmatter) or GENERATED_BY_STAGE_RE.search(frontmatter)
    stage = match.group(1) if match else None
    if stage == "KNOWLEDGE":
        stage = "KNOWLEDGE_PROMOTION"
    return stage if stage in STAGE_INDEX else None


def _next_stage(stage: str) -> str | None:
    index = STAGE_INDEX[stage]
    return STAGES[index + 1] if index + 1 < len(STAGES) else None


def _related_entity_ids(store: dict[str, Any], target_id: str, max_hops: int) -> dict[str, int]:
    if target_id not in store.get("entities", {}):
        return {}
    adjacency: dict[str, set[str]] = {}
    for row in store.get("relations", []):
        left, right = str(row.get("from", "")), str(row.get("to", ""))
        if left and right:
            adjacency.setdefault(left, set()).add(right)
            adjacency.setdefault(right, set()).add(left)
    distances = {target_id: 0}
    queue: deque[tuple[str, int]] = deque([(target_id, 0)])
    while queue:
        node, distance = queue.popleft()
        if distance >= max_hops:
            continue
        for neighbor in sorted(adjacency.get(node, set())):
            if neighbor in distances:
                continue
            distances[neighbor] = distance + 1
            queue.append((neighbor, distance + 1))
    return distances


def _artifact_referenced_entities(path: Path, store: dict[str, Any]) -> set[str]:
    if not path.is_file():
        return set()
    text = path.read_text(encoding="utf-8")
    return {entity_id for entity_id in store.get("entities", {}) if entity_id and entity_id in text}


def _latest_target_stage(entity: dict[str, Any] | None) -> str | None:
    if not entity:
        return None
    stages = []
    for row in entity.get("provenance", []):
        stage = row.get("stage")
        if stage == "KNOWLEDGE":
            stage = "KNOWLEDGE_PROMOTION"
        if stage in STAGE_INDEX:
            stages.append(stage)
    return max(stages, key=lambda x: STAGE_INDEX[x]) if stages else None


def choose_stage(
    store: dict[str, Any],
    target_id: str,
    *,
    explicit_stage: str | None,
    artifact_stage: str | None,
) -> tuple[str, str]:
    if explicit_stage:
        stage = explicit_stage.upper()
        if stage not in STAGE_INDEX:
            raise ValueError(f"unsupported work stage: {explicit_stage}")
        return stage, "USER_STAGE_OVERRIDE"
    if artifact_stage:
        return artifact_stage, "EXPLICIT_ARTIFACT_STAGE"
    entity = store.get("entities", {}).get(target_id)
    latest = _latest_target_stage(entity)
    if latest:
        next_stage = _next_stage(latest)
        return (next_stage or latest), "TARGET_PROVENANCE_NEXT_STAGE"
    if entity:
        default = TYPE_DEFAULT_STAGE.get(str(entity.get("entity_type") or "").upper())
        if default:
            return default, "TARGET_TYPE_DEFAULT"
    raise ValueError(
        f"target {target_id!r} has no resolvable stage; specify --stage or an existing --artifact with stage metadata"
    )


def _artifact_from_provenance(root: Path, store: dict[str, Any], entity_ids: set[str], stage: str) -> str | None:
    candidates: list[str] = []
    for entity_id in entity_ids:
        entity = store.get("entities", {}).get(entity_id, {})
        for row in entity.get("provenance", []):
            if row.get("stage") != stage:
                continue
            raw = str(row.get("source_artifact") or "").strip()
            if not raw:
                continue
            try:
                path, rel = safe_repo_path(root, raw)
            except ValueError:
                continue
            if path.is_file() and rel not in candidates:
                candidates.append(rel)
    return sorted(candidates)[-1] if candidates else None


def build_plan(
    root: Path,
    *,
    target_id: str,
    store_path: Path,
    stage: str | None = None,
    artifact: str | None = None,
    max_hops: int = 4,
    allow_business_truth_change: bool = False,
) -> dict[str, Any]:
    root = root.resolve()
    store = APPLY.load_store(store_path)
    explicit_artifact_stage = None
    explicit_artifact_rel = None
    if artifact:
        artifact_path, explicit_artifact_rel = safe_repo_path(root, artifact)
        explicit_artifact_stage = infer_artifact_stage(artifact_path)
    selected_stage, stage_reason = choose_stage(
        store, target_id, explicit_stage=stage, artifact_stage=explicit_artifact_stage
    )
    if explicit_artifact_stage and explicit_artifact_stage != selected_stage:
        raise ValueError(
            f"artifact stage {explicit_artifact_stage} conflicts with selected stage {selected_stage}; choose the matching stage/document explicitly"
        )

    distances = _related_entity_ids(store, target_id, max_hops)
    allowed_existing = set(distances)
    if artifact:
        artifact_path, _ = safe_repo_path(root, artifact)
        allowed_existing.update(_artifact_referenced_entities(artifact_path, store))

    if explicit_artifact_rel:
        artifact_rel = explicit_artifact_rel
        artifact_reason = "USER_ARTIFACT_OVERRIDE"
    else:
        existing = _artifact_from_provenance(root, store, allowed_existing or {target_id}, selected_stage)
        if existing:
            artifact_rel = existing
            artifact_reason = "TARGET_GRAPH_EXISTING_ARTIFACT"
        else:
            safe_target = SAFE_TARGET_RE.sub("_", target_id).strip("_") or "TARGET"
            artifact_rel = f"sdlc/runtime/work/{safe_target}/{selected_stage}_{STAGE_ARTIFACT_NAMES[selected_stage]}"
            artifact_reason = "NEW_STAGE_ARTIFACT"

    harness_path = root / "sdlc/design/contracts/harness-package-contract.json"
    stage_contract = None
    reference = None
    template = None
    if harness_path.is_file():
        harness = load_json(harness_path)
        stage_contract = harness.get("stage_contracts", {}).get(selected_stage)
        if stage_contract:
            ref_name = stage_contract.get("reference")
            template_name = stage_contract.get("template")
            if ref_name:
                reference = f".cursor/skills/work/references/{ref_name}"
            if template_name:
                template = f"sdlc/templates/core/{template_name}"
    if not template:
        template = f"sdlc/templates/core/{STAGE_ARTIFACT_NAMES[selected_stage]}"

    related = []
    for entity_id, distance in sorted(distances.items(), key=lambda item: (item[1], item[0])):
        entity = store["entities"][entity_id]
        related.append({
            "id": entity_id,
            "distance": distance,
            "entity_type": entity.get("entity_type"),
            "truth_status": entity.get("truth_status"),
            "fields": entity.get("fields", {}),
        })

    return {
        "schema_version": 1,
        "planned_at": now(),
        "target": {
            "id": target_id,
            "canonical_found": target_id in store.get("entities", {}),
            "entity": store.get("entities", {}).get(target_id),
            "graph_max_hops": max_hops,
            "related_entities": related,
        },
        "selection": {
            "stage": selected_stage,
            "stage_reason": stage_reason,
            "stage_override": bool(stage),
            "artifact_path": artifact_rel,
            "artifact_reason": artifact_reason,
            "artifact_override": bool(artifact),
            "artifact_existed_at_plan_time": (root / artifact_rel).is_file(),
            "reference_path": reference,
            "template_path": template,
        },
        "canonical": {
            "store_path": str(store_path),
            "base_revision": store["revision"],
            "allowed_existing_entity_ids": sorted(allowed_existing),
        },
        "guards": {
            "outside_target_graph_mutation_forbidden": True,
            "confirmed_business_mutation_requires_explicit_user_authorization": True,
            "allow_business_truth_change": allow_business_truth_change,
            "source_or_stage_override_does_not_authorize_upstream_business_truth_change": True,
            "artifact_only_change_may_use_empty_operations_with_no_change_reason": True,
        },
        "next_stage_candidate": _next_stage(selected_stage),
    }


def validate_target_scope(
    plan: dict[str, Any], delta: dict[str, Any], store: dict[str, Any]
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    allowed = set(plan["canonical"]["allowed_existing_entity_ids"])
    allow_business = bool(plan["guards"].get("allow_business_truth_change"))
    entities = store.get("entities", {})

    touched: set[str] = set()
    for op in delta.get("operations", []):
        kind = op.get("op")
        if kind in {"UPSERT_ENTITY", "ADD_PROVENANCE"}:
            touched.add(str(op.get("id") or ""))
        elif kind == "UPSERT_RELATION":
            touched.update([str(op.get("from") or ""), str(op.get("to") or "")])
    outside = sorted(entity_id for entity_id in touched if entity_id in entities and entity_id not in allowed)
    if outside:
        errors.append({
            "code": "OUTSIDE_TARGET_GRAPH_MUTATION",
            "message": "existing Canonical entities outside the selected target/document graph cannot be changed by this /work execution",
            "entity_ids": outside,
        })

    if not allow_business:
        for op in delta.get("operations", []):
            if op.get("op") != "UPSERT_ENTITY":
                continue
            entity_id = str(op.get("id") or "")
            existing = entities.get(entity_id)
            incoming_truth = op.get("truth_status")
            if existing and existing.get("truth_status") == "CONFIRMED_BUSINESS":
                changed = APPLY._changed_fields(existing, op.get("fields", {}))
                status_changed = bool(incoming_truth and incoming_truth != "CONFIRMED_BUSINESS")
                if changed or status_changed:
                    errors.append({
                        "code": "EXPLICIT_BUSINESS_TRUTH_CHANGE_REQUIRED",
                        "message": "selecting a stage/document does not authorize changing confirmed Business Truth; use /change or --allow-business-truth-change after explicit confirmation",
                        "entity_id": entity_id,
                        "changed_fields": changed,
                    })
            elif not existing and incoming_truth == "CONFIRMED_BUSINESS":
                errors.append({
                    "code": "EXPLICIT_BUSINESS_TRUTH_CHANGE_REQUIRED",
                    "message": "creating confirmed Business Truth requires explicit /work authorization or /change",
                    "entity_id": entity_id,
                })
    return errors


def _format_command(command: list[str], values: dict[str, str]) -> list[str]:
    return [part.format(**values) for part in command]


def execute_plan(
    root: Path,
    plan: dict[str, Any],
    *,
    provider_config: dict[str, Any],
    run_dir: Path,
    store_path: Path,
    dry_run: bool = False,
) -> dict[str, Any]:
    if provider_config.get("schema_version") != 1:
        raise ValueError("provider config schema_version must be 1")
    if not provider_config.get("enabled", False):
        return {
            "status": "NOT_EXECUTED_PROVIDER_UNAVAILABLE_OR_DISABLED",
            "provider_id": provider_config.get("provider_id"),
            "plan": plan,
            "canonical_applied": False,
        }
    command = provider_config.get("command")
    if not isinstance(command, list) or not command or not all(isinstance(x, str) and x for x in command):
        raise ValueError("enabled provider config requires non-empty command array")

    root = root.resolve()
    run_dir = run_dir.resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    context_path = run_dir / "work-context.json"
    result_path = run_dir / str(provider_config.get("result_filename") or "stage-result.json")
    save_json(context_path, plan)

    artifact_abs, artifact_rel = safe_repo_path(root, plan["selection"]["artifact_path"])
    artifact_abs.parent.mkdir(parents=True, exist_ok=True)
    values = {
        "root": str(root),
        "run_dir": str(run_dir),
        "context_path": str(context_path),
        "result_path": str(result_path),
        "artifact_path": str(artifact_abs),
        "artifact_rel": artifact_rel,
        "target_id": str(plan["target"]["id"]),
        "stage": str(plan["selection"]["stage"]),
    }
    completed = subprocess.run(
        _format_command(command, values),
        cwd=str(root),
        text=True,
        capture_output=True,
        timeout=int(provider_config.get("timeout_seconds", 120)),
        check=False,
    )
    execution: dict[str, Any] = {
        "status": "PROVIDER_COMPLETED" if completed.returncode == 0 else "PROVIDER_FAILED",
        "provider_id": provider_config.get("provider_id"),
        "command_exit_code": completed.returncode,
        "stdout": completed.stdout[-4000:],
        "stderr": completed.stderr[-4000:],
        "context_path": str(context_path),
        "result_path": str(result_path),
        "canonical_applied": False,
    }
    if completed.returncode != 0 or not result_path.is_file():
        execution["status"] = "FAIL_PROVIDER_COMMAND_OR_RESULT_MISSING"
        return execution

    stage_result = load_json(result_path)
    selected_stage = plan["selection"]["stage"]
    if stage_result.get("stage") != selected_stage:
        execution["status"] = "FAIL_SELECTED_STAGE_MISMATCH"
        execution["selected_stage"] = selected_stage
        execution["actual_stage"] = stage_result.get("stage")
        return execution
    if stage_result.get("artifact_path") != plan["selection"]["artifact_path"]:
        execution["status"] = "FAIL_SELECTED_ARTIFACT_MISMATCH"
        execution["selected_artifact"] = plan["selection"]["artifact_path"]
        execution["actual_artifact"] = stage_result.get("artifact_path")
        return execution

    store = APPLY.load_store(store_path)
    if store["revision"] != plan["canonical"]["base_revision"]:
        execution["status"] = "FAIL_PLAN_STALE_CANONICAL_REVISION"
        execution["planned_revision"] = plan["canonical"]["base_revision"]
        execution["current_revision"] = store["revision"]
        return execution

    delta = stage_result.get("canonical_delta") if isinstance(stage_result.get("canonical_delta"), dict) else {}
    scope_errors = validate_target_scope(plan, delta, store)
    if scope_errors:
        execution["status"] = "FAIL_TARGET_SCOPE_GUARD"
        execution["scope_errors"] = scope_errors
        return execution

    validation = VALIDATOR.validate_stage_result(stage_result, root, store_path=store_path)
    execution["validation"] = validation
    if validation["status"] != "PASS" or not validation["executable"]:
        execution["status"] = "FAIL_STAGE_RESULT_VALIDATION"
        return execution

    canonical_check = validation.get("canonical_check") or {}
    if dry_run:
        execution["status"] = "DRY_RUN_VALIDATED"
        execution["canonical_status"] = canonical_check.get("status")
        return execution

    apply_result, resulting_store = APPLY.apply_delta(store, delta)
    execution["canonical_result"] = apply_result
    if apply_result["status"] == "APPLIED":
        APPLY.save_store(store_path, resulting_store)
        execution["canonical_applied"] = True
        execution["status"] = "APPLIED"
    elif apply_result["status"] in {"IDEMPOTENT", "NO_CHANGE"}:
        execution["status"] = apply_result["status"]
    else:
        execution["status"] = "FAIL_CANONICAL_APPLY"
    execution["next_stage_candidate"] = plan.get("next_stage_candidate")
    return execution


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Execute one /work stage for any Canonical or explicit target ID.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--target", required=True, help="RQ/FR/BR/PGM/TASK/AC/TC or any project target ID such as ANA-001")
    parser.add_argument("--stage", help="Explicit stage re-entry/override, e.g. DESIGN or PROGRAM")
    parser.add_argument("--artifact", help="Explicit repository-relative document to create/revise")
    parser.add_argument("--store", default="sdlc/canonical/store.json")
    parser.add_argument("--provider-config", default="sdlc/config/agent-repeatability-profile.example.json")
    parser.add_argument("--run-dir")
    parser.add_argument("--plan-out")
    parser.add_argument("--result-out")
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-hops", type=int, default=4)
    parser.add_argument("--allow-business-truth-change", action="store_true")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    store_path = (root / args.store).resolve() if not Path(args.store).is_absolute() else Path(args.store)
    try:
        plan = build_plan(
            root,
            target_id=args.target,
            store_path=store_path,
            stage=args.stage,
            artifact=args.artifact,
            max_hops=args.max_hops,
            allow_business_truth_change=args.allow_business_truth_change,
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"status": "PLAN_FAILED", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2

    if args.plan_out:
        save_json(Path(args.plan_out), plan)
    if args.plan_only:
        print(json.dumps({"status": "PLAN_READY", "plan": plan}, ensure_ascii=False, indent=2))
        return 0

    provider_path = Path(args.provider_config)
    if not provider_path.is_absolute():
        provider_path = root / provider_path
    provider = load_json(provider_path)
    if args.run_dir:
        run_dir = Path(args.run_dir)
        if not run_dir.is_absolute():
            run_dir = root / run_dir
    else:
        safe_target = SAFE_TARGET_RE.sub("_", args.target).strip("_") or "TARGET"
        run_dir = root / "sdlc/runtime/work-runs" / f"{safe_target}-{plan['selection']['stage']}"
    try:
        result = execute_plan(root, plan, provider_config=provider, run_dir=run_dir, store_path=store_path, dry_run=args.dry_run)
    except (OSError, json.JSONDecodeError, ValueError, subprocess.SubprocessError) as exc:
        result = {"status": "EXECUTION_FAILED", "error": str(exc), "canonical_applied": False}
    if args.result_out:
        save_json(Path(args.result_out), result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") in {
        "APPLIED", "IDEMPOTENT", "NO_CHANGE", "DRY_RUN_VALIDATED",
        "NOT_EXECUTED_PROVIDER_UNAVAILABLE_OR_DISABLED",
    } else 3


if __name__ == "__main__":
    raise SystemExit(main())
