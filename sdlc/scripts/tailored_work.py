#!/usr/bin/env python3
"""Human-first /work adapter with Change-Level semantic execution policy.

Change Level selects execution depth. Stage selects an internal focus. Tailoring Profile owns Human
Artifact topology. PROFILE_PRIMARY_SET therefore exposes and enforces all required Engineering
projections even when one document is the current primary editing surface.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


CONFIG = _load("tailored_work_config", "runtime_config_v19.py")
TAILOR = _load("tailored_work_tailoring", "tailoring_runtime.py")
EXEC = _load("tailored_work_change_execution", "change_execution_runtime.py")
WORK = _load("tailored_work_core", "run_work.py")
INTERACTIVE = _load("tailored_work_interactive", "interactive_work.py")
HANDOFF = _load("tailored_work_handoff", "work_handoff.py")
LIFE = _load("tailored_work_projection_lifecycle", "projection_lifecycle_runtime.py")
SUCCESS = {"APPLIED", "IDEMPOTENT", "NO_CHANGE", "DRY_RUN_VALIDATED"}


def _value(args: list[str], option: str, default: str | None = None) -> str | None:
    for i, value in enumerate(args):
        if value == option and i + 1 < len(args): return args[i + 1]
        if value.startswith(option + "="): return value.split("=", 1)[1]
    return default


def _flag(args: list[str], option: str) -> bool: return option in args


def _capture_main(fn, args: list[str]) -> tuple[int, dict[str, Any]]:
    captured = StringIO()
    with redirect_stdout(captured): code = fn(args)
    raw = captured.getvalue().strip()
    try: result = json.loads(raw)
    except json.JSONDecodeError: result = {"status": "DELEGATE_OUTPUT_INVALID", "raw": raw}
    return code, result


def _safe_path(root: Path, raw: str) -> tuple[Path, str]: return WORK.safe_repo_path(root, raw)


def _semantic_context(root: Path, target: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    resolved = CONFIG.resolve_runtime_config(root)
    project = resolved.get("project") or {}
    store = TAILOR.load_store(root)
    change = EXEC.resolve_change(root, target, store, project, phase="WORK")
    execution = EXEC.resolve_execution_plan(root, change)
    return project, store, change, execution


def _route_default_stage(args: list[str], root: Path) -> tuple[list[str], dict[str, Any] | None, dict[str, Any] | None]:
    if _value(args, "--stage") is not None or _value(args, "--artifact") is not None:
        return list(args), None, None
    target = _value(args, "--target")
    if not target: return list(args), None, None
    _, _, change, execution = _semantic_context(root, target)
    routed = list(args) + ["--stage", str(execution["default_entry_stage"])]
    return routed, change, execution


def _legacy_tailoring_fallback(project: dict[str, Any], target: str, stage: str, effective: str, error: str) -> dict[str, Any]:
    return {
        "schema_version": 3,
        "target_id": target,
        "stage": stage,
        "change_level": effective,
        "profiles": TAILOR.project_profile_ids(project),
        "profile_paths": {},
        "projection_topologies": {"internal": "STAGE_MATCHED", "customer": "STAGE_MATCHED", "pm": "STAGE_MATCHED"},
        "primary_work_artifact": None,
        "required_engineering_artifacts": [],
        "projection_update_set": [],
        "affected_artifacts": {"internal": [], "customer": [], "pm": []},
        "machine_evidence_visibility": str(CONFIG.nested(project, "documents", "machine", "visibility", default="HIDDEN") or "HIDDEN").upper(),
        "stage_preserved": True,
        "projection_creates_business_truth": False,
        "compatibility_fallback": "PROFILE_PACKAGE_MISSING_KEEP_CORE_STAGE_ARTIFACT",
        "fallback_reason": error,
    }


def _profile_plan(root: Path, target: str, stage: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    project, store, change, execution = _semantic_context(root, target)
    effective = str(change.get("effective_change_level") or change.get("provisional_change_level") or "L3")
    try:
        tailoring = TAILOR.resolve_artifacts(root, project=project, target=target, stage=stage, change_level=effective, store=store)
    except ValueError as exc:
        if "tailoring profile not found:" not in str(exc): raise
        tailoring = _legacy_tailoring_fallback(project, target, stage, effective, str(exc))
    execution = dict(execution)
    execution["selected_internal_stage"] = stage
    execution["explicit_stage_outside_normal_allowlist"] = stage not in set(execution.get("stage_allowlist") or [])
    return change, execution, tailoring


def _prepare_required_projection_targets(root: Path, tailoring: dict[str, Any]) -> list[dict[str, Any]]:
    prepared: list[dict[str, Any]] = []
    for row in tailoring.get("required_engineering_artifacts") or []:
        if not isinstance(row, dict): continue
        output_raw = str(row.get("output_path") or "")
        template_raw = str(row.get("template") or "")
        if not output_raw or not template_raw: continue
        output_abs, output_rel = _safe_path(root, output_raw)
        template_abs, template_rel = _safe_path(root, template_raw)
        if not template_abs.is_file(): raise ValueError(f"tailoring template not found: {template_rel}")
        output_abs.parent.mkdir(parents=True, exist_ok=True)
        prepared.append({
            "id": row.get("id"), "output_path": output_rel, "template": template_rel,
            "projection_detail": row.get("projection_detail"), "stage_match": bool(row.get("stage_match")),
            "projection_required": bool(row.get("projection_required")),
            "existed_at_plan_time": output_abs.is_file(), "hash_at_plan_time": WORK._hash_file(output_abs),
        })
    return prepared


def _apply_plan_tailoring(root: Path, plan: dict[str, Any], *, explicit_artifact: bool, explicit_stage: bool) -> dict[str, Any]:
    target = str((plan.get("target") or {}).get("id") or "")
    stage = str((plan.get("selection") or {}).get("stage") or "")
    change, execution, tailoring = _profile_plan(root, target, stage)
    plan["change_level"] = change
    plan["execution_policy"] = execution
    plan["tailoring"] = tailoring
    plan["required_projection_targets"] = _prepare_required_projection_targets(root, tailoring)
    plan["human_control_plane"] = {
        "runtime_stage_hidden_by_default": True,
        "semantic_work_is_primary_execution_contract": True,
        "change_level_does_not_own_projection_topology": True,
        "primary_artifact_is_current_edit_focus_not_only_required_document": True,
        "profile_required_projections_must_be_refreshed": bool(plan["required_projection_targets"]),
        "machine_evidence_visibility": tailoring.get("machine_evidence_visibility", "HIDDEN"),
        "customer_projection_creates_business_truth": False,
        "explicit_stage_override": explicit_stage,
    }
    if explicit_artifact:
        plan["tailoring"]["explicit_artifact_override_preserved"] = True
        return plan

    primary = tailoring.get("primary_work_artifact")
    if not isinstance(primary, dict):
        plan["tailoring"].setdefault("fallback", "NO_PRIMARY_MAPPING_KEEP_CORE_STAGE_ARTIFACT")
        current = str((plan.get("selection") or {}).get("artifact_path") or "")
        reason = str((plan.get("selection") or {}).get("artifact_reason") or "")
        if reason == "NEW_STAGE_ARTIFACT" or current.startswith("sdlc/runtime/work/"):
            artifact_rel = HANDOFF.default_document_path(plan)
            artifact_abs, artifact_rel = _safe_path(root, artifact_rel)
            artifact_abs.parent.mkdir(parents=True, exist_ok=True)
            plan["selection"].update({
                "artifact_path": artifact_rel, "artifact_reason": "USER_DOCUMENT_DEFAULT_COMPATIBILITY_FALLBACK",
                "artifact_override": False, "artifact_existed_at_plan_time": artifact_abs.is_file(),
                "artifact_hash_at_plan_time": WORK._hash_file(artifact_abs),
            })
        return plan

    artifact_raw = str(primary.get("output_path") or "")
    template_raw = str(primary.get("template") or "")
    artifact_abs, artifact_rel = _safe_path(root, artifact_raw)
    template_abs, template_rel = _safe_path(root, template_raw)
    if not template_abs.is_file(): raise ValueError(f"tailoring template not found: {template_rel}")
    artifact_abs.parent.mkdir(parents=True, exist_ok=True)
    plan["selection"].update({
        "artifact_path": artifact_rel, "artifact_reason": "TAILORING_PROFILE_PRIMARY", "artifact_override": False,
        "artifact_existed_at_plan_time": artifact_abs.is_file(), "artifact_hash_at_plan_time": WORK._hash_file(artifact_abs),
        "template_path": template_rel, "tailoring_artifact_id": primary.get("id"),
        "tailoring_profile_id": primary.get("profile_id"), "audience": primary.get("audience"),
        "projection_detail": primary.get("projection_detail"),
    })
    return plan


def _projection_rows(plan: dict[str, Any]) -> list[dict[str, Any]]:
    rows = (plan.get("tailoring") or {}).get("required_engineering_artifacts") or []
    if rows: return [dict(x) for x in rows if isinstance(x, dict)]
    primary = (plan.get("tailoring") or {}).get("primary_work_artifact")
    return [dict(primary)] if isinstance(primary, dict) else []


def _record_projections(root: Path, plan: dict[str, Any]) -> dict[str, Any]:
    target = str((plan.get("target") or {}).get("id") or "")
    resolved = CONFIG.resolve_runtime_config(root)
    project = resolved.get("project") or {}
    configured_policy = CONFIG.nested(project, "documents", "engineering", "manual_edit_policy", default="TYPO_ONLY")
    metadata: list[str] = []
    missing: list[str] = []
    for row in _projection_rows(plan):
        artifact_path = str(row.get("output_path") or "")
        if not artifact_path or not (root / artifact_path).is_file():
            missing.append(artifact_path or str(row.get("id") or "artifact")); continue
        artifact_id = str(row.get("id") or "artifact")
        registered = LIFE.register_generated(
            root, target=target, artifact_id=artifact_id, artifact_path=artifact_path,
            audience=str(row.get("audience") or "INTERNAL_IT"), profile_id=str(row.get("profile_id") or "") or None,
            manual_edit_policy=str(row.get("manual_edit_policy") or configured_policy or "TYPO_ONLY"),
        )
        if not registered.get("generated_content_hash"):
            raise ValueError(f"projection content hash was not recorded: {artifact_path}")
        metadata.append(LIFE.metadata_path(root, target, artifact_id).relative_to(root).as_posix())
    return {"metadata": metadata, "missing_required": missing, "complete": not missing}


def _apply_projection_completion(result: dict[str, Any], registration: dict[str, Any]) -> None:
    result["projection_metadata_set"] = registration["metadata"]
    result["required_projection_missing"] = registration["missing_required"]
    result["required_projection_complete"] = registration["complete"]
    if registration["metadata"]: result["projection_metadata"] = registration["metadata"][0]
    if not registration["complete"]:
        result["semantic_status"] = result.get("status")
        result["status"] = "PROJECTION_REFRESH_REQUIRED"
        result["next_action"] = "update every tailoring.required_engineering_artifacts document from current Canonical/Evidence, then finalize again"


def _interactive(args: list[str], root: Path, *, explicit_stage: bool) -> int:
    explicit_artifact = _value(args, "--artifact") is not None
    if _flag(args, "--finalize"):
        code, result = _capture_main(INTERACTIVE.main, args)
        if result.get("status") in SUCCESS:
            context_raw = result.get("context_path")
            if context_raw:
                context_path = Path(str(context_raw)); context_path = context_path if context_path.is_absolute() else root / context_path
                if context_path.is_file():
                    context = WORK.load_json(context_path)
                    plan = {k: v for k, v in context.items() if k not in {"interactive_baseline", "interactive_output"}}
                    registration = _record_projections(root, plan)
                    _apply_projection_completion(result, registration)
                    if not registration["complete"]: code = 3
        print(json.dumps(result, ensure_ascii=False, indent=2)); return code

    code, result = _capture_main(INTERACTIVE.main, args)
    if result.get("status") not in {"INTERACTIVE_HANDOFF_READY", "PLAN_READY"}:
        print(json.dumps(result, ensure_ascii=False, indent=2)); return code
    context_raw = result.get("context_path")
    if not context_raw:
        print(json.dumps(result, ensure_ascii=False, indent=2)); return code
    context_path = Path(str(context_raw)); context_path = context_path if context_path.is_absolute() else root / context_path
    context = WORK.load_json(context_path)
    plan = {k: v for k, v in context.items() if k not in {"interactive_baseline", "interactive_output"}}
    plan = _apply_plan_tailoring(root, plan, explicit_artifact=explicit_artifact, explicit_stage=explicit_stage)
    context.update(plan)
    artifact_abs, artifact_rel = _safe_path(root, str(plan["selection"]["artifact_path"]))
    context.setdefault("interactive_output", {})["artifact_path"] = artifact_rel
    context.setdefault("interactive_baseline", {})["artifact_hash"] = WORK._hash_file(artifact_abs)
    WORK.save_json(context_path, context)
    result.update({
        "plan": plan,
        "artifact_path": artifact_rel,
        "template_path": plan["selection"].get("template_path"),
        "change_level": plan.get("change_level"),
        "execution_policy": plan.get("execution_policy"),
        "tailoring": plan.get("tailoring"),
        "required_projection_targets": plan.get("required_projection_targets"),
        "instruction": "Change Level은 Semantic/Evidence/Review 깊이만 결정한다. primary_work_artifact를 중심으로 작업하되 tailoring.required_engineering_artifacts를 모두 projection_detail 수준으로 갱신한다. Canonical/Trace/Provenance/Source Hash/Stage Result는 사람이 수동 유지하지 않는다.",
    })
    plan_out = _value(args, "--plan-out")
    if plan_out:
        plan_path = Path(str(plan_out)); plan_path = plan_path if plan_path.is_absolute() else root / plan_path; WORK.save_json(plan_path, plan)
    print(json.dumps(result, ensure_ascii=False, indent=2)); return code


def _headless(args: list[str], root: Path, *, explicit_stage: bool) -> int:
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--root", default="."); ap.add_argument("--target", required=True); ap.add_argument("--stage"); ap.add_argument("--artifact")
    ap.add_argument("--store", default="sdlc/canonical/store.json"); ap.add_argument("--project-profile", required=True); ap.add_argument("--source-profile", required=True); ap.add_argument("--provider-config", required=True)
    ap.add_argument("--run-dir"); ap.add_argument("--plan-out"); ap.add_argument("--result-out"); ap.add_argument("--plan-only", action="store_true"); ap.add_argument("--dry-run", action="store_true"); ap.add_argument("--max-hops", type=int); ap.add_argument("--allow-business-truth-change", action="store_true")
    ns, _ = ap.parse_known_args(args)
    store_path = Path(ns.store) if Path(ns.store).is_absolute() else root / ns.store
    project_path = Path(ns.project_profile) if Path(ns.project_profile).is_absolute() else root / ns.project_profile
    source_path = Path(ns.source_profile) if Path(ns.source_profile).is_absolute() else root / ns.source_profile
    provider_path = Path(ns.provider_config) if Path(ns.provider_config).is_absolute() else root / ns.provider_config
    project_profile = WORK.CONFIG.load_config(project_path); source_profile = WORK.CONFIG.load_config(source_path)
    delivery = WORK.CONFIG.delivery_policy(project_profile) if project_profile else None
    hops = ns.max_hops if ns.max_hops is not None else int(delivery.get("graph_hops", 4) if delivery else 4)
    try:
        plan = WORK.build_plan(root, target_id=ns.target, store_path=store_path, stage=ns.stage, artifact=ns.artifact, max_hops=hops, allow_business_truth_change=ns.allow_business_truth_change, project_profile=project_profile, source_profile=source_profile)
        plan["_root"] = str(root)
        plan = _apply_plan_tailoring(root, plan, explicit_artifact=bool(ns.artifact), explicit_stage=explicit_stage)
        if ns.plan_out:
            out = Path(ns.plan_out); out = out if out.is_absolute() else root / out; WORK.save_json(out, plan)
        if ns.plan_only:
            print(json.dumps({"status": "PLAN_READY", "plan": plan}, ensure_ascii=False, indent=2)); return 0
        if not provider_path.is_file():
            result = {"status": "NOT_EXECUTED_PROVIDER_CONFIG_MISSING", "provider_config": str(provider_path), "canonical_applied": False}
        else:
            provider = WORK.load_json(provider_path)
            run_dir = Path(ns.run_dir) if ns.run_dir else root / "sdlc/runtime/work-runs" / f"{TAILOR._safe_target(ns.target)}-{plan['selection']['stage']}"
            if not run_dir.is_absolute(): run_dir = root / run_dir
            result = WORK.execute_plan(root, plan, provider_config=provider, run_dir=run_dir, store_path=store_path, dry_run=ns.dry_run, source_profile=source_profile)
            if result.get("status") in SUCCESS:
                registration = _record_projections(root, plan); _apply_projection_completion(result, registration)
                if registration["complete"]:
                    try:
                        handoff = HANDOFF.build_user_handoff(ns.target, plan, result); handoff_path = HANDOFF._write_handoff(root, ns.target, plan, result, handoff)
                        result["user_handoff"] = handoff; result["handoff_path"] = handoff_path.relative_to(root).as_posix()
                    except Exception as exc: result["handoff_warning"] = str(exc)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {"status": "TAILORED_WORK_FAILED", "error": str(exc), "canonical_applied": False}
    if ns.result_out:
        out = Path(ns.result_out); out = out if out.is_absolute() else root / out; WORK.save_json(out, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") in SUCCESS | {"PLAN_READY"} else 3


def main(argv: list[str] | None = None) -> int:
    original = list(argv or [])
    root = Path(_value(original, "--root", ".") or ".").resolve()
    explicit_stage = _value(original, "--stage") is not None
    try:
        args, _, _ = _route_default_stage(original, root)
        resolved = CONFIG.resolve_runtime_config(root)
        legacy_path = root / CONFIG.DEFAULT_PROVIDER_CONFIG_PATH
        legacy = CONFIG.load_config(legacy_path) if legacy_path.is_file() else {}
        runtime = CONFIG.resolve_agent_runtime(resolved.get("project") or {}, legacy_provider=legacy)
        if runtime.get("execution_mode") == "INTERACTIVE": return _interactive(args, root, explicit_stage=explicit_stage)
        return _headless(args, root, explicit_stage=explicit_stage)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "TAILORED_WORK_FAILED", "error": str(exc)}, ensure_ascii=False, indent=2)); return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
