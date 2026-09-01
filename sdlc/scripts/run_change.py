#!/usr/bin/env python3
"""Executable /change orchestration using the same Provider/Stage Result/Canonical guard as /work."""
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


APPLY = _load("change_apply", SCRIPT_DIR / "apply_canonical_delta.py")
CONFIG = _load("change_config", SCRIPT_DIR / "runtime_config.py")
WORK = _load("change_work", SCRIPT_DIR / "run_work.py")


def build_change_plan(
    root: Path, *, target_id: str, change_text: str, store_path: Path,
    artifact: str | None = None, allow_business_truth_change: bool = False,
    project_profile: dict[str, Any] | None = None, source_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    store = APPLY.load_store(store_path)
    policy = CONFIG.delivery_policy(project_profile or {}) if project_profile else None
    hops = int(policy.get("graph_hops", 4) if policy else 4)
    distances = WORK._related_entity_ids(store, target_id, hops)
    allowed_existing = set(distances)
    if target_id in store.get("entities", {}):
        allowed_existing.add(target_id)
    safe_target = WORK.SAFE_TARGET_RE.sub("_", target_id).strip("_") or "TARGET"
    artifact_rel = artifact or f"sdlc/runtime/change/{safe_target}/CHANGE_change-analysis.md"
    artifact_path, artifact_rel = WORK.safe_repo_path(root, artifact_rel)
    if artifact_path.is_file():
        allowed_existing.update(WORK._artifact_referenced_entities(artifact_path, store))
    git = WORK.git_metadata(root)
    return {
        "schema_version": 2,
        "planned_at": WORK.now(),
        "target": {
            "id": target_id,
            "canonical_found": target_id in store.get("entities", {}),
            "entity": store.get("entities", {}).get(target_id),
            "graph_max_hops": hops,
            "related_entities": [
                {"id": eid, "distance": distance, "entity_type": store["entities"][eid].get("entity_type"), "truth_status": store["entities"][eid].get("truth_status"), "fields": store["entities"][eid].get("fields", {})}
                for eid, distance in sorted(distances.items(), key=lambda x: (x[1], x[0]))
            ],
        },
        "change_request": {
            "original_text": change_text,
            "classification_required": ["CLARIFICATION", "BEHAVIOR_CHANGE", "TECHNICAL_CHANGE", "NEW_REQUIREMENT"],
            "business_truth_auto_confirmation_forbidden": True,
        },
        "selection": {
            "stage": "CHANGE",
            "stage_reason": "USER_CHANGE_REQUEST",
            "stage_override": True,
            "artifact_path": artifact_rel,
            "artifact_reason": "CHANGE_ANALYSIS_ARTIFACT",
            "artifact_override": bool(artifact),
            "artifact_existed_at_plan_time": artifact_path.is_file(),
            "reference_path": ".cursor/skills/change/SKILL.md",
            "template_path": None,
        },
        "delivery": {
            "profile": policy.get("profile") if policy else "LEGACY",
            "mode": policy.get("mode") if policy else None,
            "enabled_stages": policy.get("enabled_stages") if policy else list(WORK.STAGES),
            "optional_stages": policy.get("optional_stages") if policy else [],
            "program_readiness": policy.get("program_readiness") if policy else "FULL",
            "explicit_stage_outside_profile": False,
        },
        "canonical": {"store_path": str(store_path), "base_revision": store["revision"], "allowed_existing_entity_ids": sorted(allowed_existing)},
        "version_baseline": {"git_available": git.get("available", False), "git_commit": git.get("head"), "git_branch": git.get("branch"), "dirty_paths": sorted(WORK.git_changed_paths(root)), "canonical_revision": store["revision"]},
        "source_policy": {"allowed_write_roots": CONFIG.source_roots(source_profile or {})},
        "guards": {
            "outside_target_graph_mutation_forbidden": True,
            "confirmed_business_mutation_requires_explicit_user_authorization": True,
            "allow_business_truth_change": allow_business_truth_change,
            "source_or_stage_override_does_not_authorize_upstream_business_truth_change": True,
            "artifact_only_change_may_use_empty_operations_with_no_change_reason": True,
            "protected_branch_write_forbidden": True,
            "stale_git_head_forbidden": True,
            "dirty_workspace_forbidden_by_default": True,
        },
        "next_stage_candidate": None,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Execute a natural-language change request through the common guarded runtime.")
    ap.add_argument("--root", default=".")
    ap.add_argument("--target", required=True)
    ap.add_argument("--change", required=True, help="Natural-language before/after or requested change")
    ap.add_argument("--artifact")
    ap.add_argument("--store", default="sdlc/canonical/store.json")
    ap.add_argument("--project-profile", default="sdlc/config/project-profile.yaml")
    ap.add_argument("--source-profile", default="sdlc/config/source-profile.yaml")
    ap.add_argument("--provider-config", default="sdlc/config/agent-provider.json")
    ap.add_argument("--run-dir")
    ap.add_argument("--plan-only", action="store_true")
    ap.add_argument("--allow-business-truth-change", action="store_true")
    ap.add_argument("--result-out")
    args = ap.parse_args(argv)

    root = Path(args.root).resolve()
    store = Path(args.store) if Path(args.store).is_absolute() else root / args.store
    project = CONFIG.load_config(Path(args.project_profile) if Path(args.project_profile).is_absolute() else root / args.project_profile)
    source = CONFIG.load_config(Path(args.source_profile) if Path(args.source_profile).is_absolute() else root / args.source_profile)
    try:
        plan = build_change_plan(
            root, target_id=args.target, change_text=args.change, store_path=store, artifact=args.artifact,
            allow_business_truth_change=args.allow_business_truth_change, project_profile=project, source_profile=source,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "PLAN_FAILED", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2
    if args.plan_only:
        print(json.dumps({"status": "PLAN_READY", "plan": plan}, ensure_ascii=False, indent=2))
        return 0

    provider_path = Path(args.provider_config) if Path(args.provider_config).is_absolute() else root / args.provider_config
    if not provider_path.is_file():
        print(json.dumps({"status": "NOT_EXECUTED_PROVIDER_CONFIG_MISSING", "provider_config": str(provider_path)}, ensure_ascii=False, indent=2))
        return 4
    provider = WORK.load_json(provider_path)
    run_dir = Path(args.run_dir) if args.run_dir else root / "sdlc/runtime/change-runs" / WORK.SAFE_TARGET_RE.sub("_", args.target)
    if not run_dir.is_absolute():
        run_dir = root / run_dir
    result = WORK.execute_plan(root, plan, provider_config=provider, run_dir=run_dir, store_path=store, source_profile=source)
    if args.result_out:
        WORK.save_json(Path(args.result_out), result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") in {"APPLIED", "IDEMPOTENT", "NO_CHANGE", "DRY_RUN_VALIDATED"} else 3


if __name__ == "__main__":
    raise SystemExit(main())
