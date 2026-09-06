#!/usr/bin/env python3
"""v1.9 /work adapter: keep the Stage executor, replace Stage->document coupling with Tailoring.

INTERACTIVE prepare delegates to the existing guarded runtime, then rewrites only the planned
Human Artifact/template according to the selected Project Tailoring Profile. Finalize reuses the
unchanged v1.8 semantic guards. HEADLESS builds the same plan and executes it through run_work.

Compatibility rule: a legacy/minimum deployment that does not contain the v1.9 profile package
must keep the v1.8 Core Stage Artifact instead of failing before the existing guarded runtime can
run. An explicitly configured profile that exists but is invalid still fails closed.
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
WORK = _load("tailored_work_core", "run_work.py")
INTERACTIVE = _load("tailored_work_interactive", "interactive_work.py")
HANDOFF = _load("tailored_work_handoff", "work_handoff.py")
SUCCESS = {"APPLIED", "IDEMPOTENT", "NO_CHANGE", "DRY_RUN_VALIDATED"}


def _value(args: list[str], option: str, default: str | None = None) -> str | None:
    for i, value in enumerate(args):
        if value == option and i + 1 < len(args):
            return args[i + 1]
        if value.startswith(option + "="):
            return value.split("=", 1)[1]
    return default


def _flag(args: list[str], option: str) -> bool:
    return option in args


def _capture_main(fn, args: list[str]) -> tuple[int, dict[str, Any]]:
    captured = StringIO()
    with redirect_stdout(captured):
        code = fn(args)
    raw = captured.getvalue().strip()
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {"status": "DELEGATE_OUTPUT_INVALID", "raw": raw}
    return code, result


def _safe_path(root: Path, raw: str) -> tuple[Path, str]:
    return WORK.safe_repo_path(root, raw)


def _legacy_tailoring_fallback(project: dict[str, Any], target: str, stage: str, effective: str, error: str) -> dict[str, Any]:
    """Represent a missing optional v1.9 profile package without changing v1.8 Stage semantics."""
    return {
        "schema_version": 1,
        "target_id": target,
        "stage": stage,
        "change_level": effective,
        "profiles": TAILOR.project_profile_ids(project),
        "profile_paths": {},
        "primary_work_artifact": None,
        "affected_artifacts": {"internal": [], "customer": [], "pm": []},
        "machine_evidence_visibility": str(CONFIG.nested(project, "documents", "machine", "visibility", default="HIDDEN") or "HIDDEN").upper(),
        "stage_preserved": True,
        "projection_creates_business_truth": False,
        "compatibility_fallback": "PROFILE_PACKAGE_MISSING_KEEP_CORE_STAGE_ARTIFACT",
        "fallback_reason": error,
    }


def _profile_plan(root: Path, target: str, stage: str) -> tuple[dict[str, Any], dict[str, Any]]:
    resolved = CONFIG.resolve_runtime_config(root)
    project = resolved.get("project") or {}
    store = TAILOR.load_store(root)
    change = TAILOR.resolve_change_level(root, target, stage, store, project)
    effective = str(change.get("effective_change_level") or change.get("provisional_change_level") or "L3")
    try:
        tailoring = TAILOR.resolve_artifacts(
            root,
            project=project,
            target=target,
            stage=stage,
            change_level=effective,
            store=store,
        )
    except ValueError as exc:
        # Standard v1.9 deployments carry sdlc/tailoring/standard. Legacy/minimum executable
        # deployments may only carry Core Stage templates. Preserve that valid v1.8 behavior.
        if "tailoring profile not found:" not in str(exc):
            raise
        tailoring = _legacy_tailoring_fallback(project, target, stage, effective, str(exc))
    return change, tailoring


def _apply_plan_tailoring(root: Path, plan: dict[str, Any], *, explicit_artifact: bool) -> dict[str, Any]:
    target = str((plan.get("target") or {}).get("id") or "")
    stage = str((plan.get("selection") or {}).get("stage") or "")
    change, tailoring = _profile_plan(root, target, stage)
    plan["change_level"] = change
    plan["tailoring"] = tailoring
    plan["human_control_plane"] = {
        "runtime_stage_hidden_by_default": True,
        "primary_artifact_is_human_review_surface": True,
        "machine_evidence_visibility": tailoring.get("machine_evidence_visibility", "HIDDEN"),
        "customer_projection_creates_business_truth": False,
    }
    if explicit_artifact:
        plan["tailoring"]["explicit_artifact_override_preserved"] = True
        return plan

    primary = tailoring.get("primary_work_artifact")
    if not isinstance(primary, dict):
        plan["tailoring"].setdefault("fallback", "NO_PRIMARY_MAPPING_KEEP_CORE_STAGE_ARTIFACT")
        return plan
    artifact_raw = str(primary.get("output_path") or "")
    template_raw = str(primary.get("template") or "")
    artifact_abs, artifact_rel = _safe_path(root, artifact_raw)
    template_abs, template_rel = _safe_path(root, template_raw)
    if not template_abs.is_file():
        raise ValueError(f"tailoring template not found: {template_rel}")
    artifact_abs.parent.mkdir(parents=True, exist_ok=True)
    plan["selection"].update({
        "artifact_path": artifact_rel,
        "artifact_reason": "TAILORING_PROFILE_PRIMARY",
        "artifact_override": False,
        "artifact_existed_at_plan_time": artifact_abs.is_file(),
        "artifact_hash_at_plan_time": WORK._hash_file(artifact_abs),
        "template_path": template_rel,
        "tailoring_artifact_id": primary.get("id"),
        "tailoring_profile_id": primary.get("profile_id"),
        "audience": primary.get("audience"),
    })
    return plan


def _projection_metadata_path(root: Path, target: str, artifact_id: str) -> Path:
    safe_target = TAILOR._safe_target(target)
    safe_artifact = TAILOR._safe_target(artifact_id)
    return root / TAILOR.PROJECTION_RUNTIME_ROOT / f"{safe_target}-{safe_artifact}.json"


def _record_projection(root: Path, plan: dict[str, Any]) -> str | None:
    primary = (plan.get("tailoring") or {}).get("primary_work_artifact")
    if not isinstance(primary, dict):
        return None
    artifact_path = str((plan.get("selection") or {}).get("artifact_path") or "")
    if not artifact_path or not (root / artifact_path).is_file():
        return None
    store = TAILOR.load_store(root)
    target = str((plan.get("target") or {}).get("id") or "")
    path = _projection_metadata_path(root, target, str(primary.get("id") or "artifact"))
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "target_id": target,
        "artifact_id": primary.get("id"),
        "artifact_path": artifact_path,
        "audience": primary.get("audience"),
        "profile_id": primary.get("profile_id"),
        "canonical_revision": int(store.get("revision") or 0),
        "generated_from_revision": int(store.get("revision") or 0),
        "generated_at": TAILOR.now(),
        "ownership": "HUMAN_REVIEWED" if primary.get("audience") == "INTERNAL_IT" else "GENERATED_VIEW",
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path.relative_to(root).as_posix()


def _interactive(args: list[str], root: Path) -> int:
    explicit_artifact = _value(args, "--artifact") is not None
    if _flag(args, "--finalize"):
        code, result = _capture_main(INTERACTIVE.main, args)
        if result.get("status") in SUCCESS:
            context_raw = result.get("context_path")
            if context_raw:
                context_path = Path(str(context_raw))
                if not context_path.is_absolute():
                    context_path = root / context_path
                if context_path.is_file():
                    context = WORK.load_json(context_path)
                    plan = {k: v for k, v in context.items() if k not in {"interactive_baseline", "interactive_output"}}
                    metadata = _record_projection(root, plan)
                    if metadata:
                        result["projection_metadata"] = metadata
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return code

    code, result = _capture_main(INTERACTIVE.main, args)
    if result.get("status") not in {"INTERACTIVE_HANDOFF_READY", "PLAN_READY"}:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return code
    context_raw = result.get("context_path")
    if not context_raw:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return code
    context_path = Path(str(context_raw))
    if not context_path.is_absolute():
        context_path = root / context_path
    context = WORK.load_json(context_path)
    plan = {k: v for k, v in context.items() if k not in {"interactive_baseline", "interactive_output"}}
    plan = _apply_plan_tailoring(root, plan, explicit_artifact=explicit_artifact)
    context.update(plan)
    artifact_abs, artifact_rel = _safe_path(root, str(plan["selection"]["artifact_path"]))
    context.setdefault("interactive_output", {})["artifact_path"] = artifact_rel
    context.setdefault("interactive_baseline", {})["artifact_hash"] = WORK._hash_file(artifact_abs)
    WORK.save_json(context_path, context)

    result["plan"] = plan
    result["artifact_path"] = artifact_rel
    result["template_path"] = plan["selection"].get("template_path")
    result["change_level"] = plan.get("change_level")
    result["tailoring"] = plan.get("tailoring")
    result["instruction"] = "현재 Agent는 Runtime Stage를 직접 고르지 않고 Tailoring이 선택한 Primary Artifact를 검토/작성한 뒤 finalize한다."
    plan_out = _value(args, "--plan-out")
    if plan_out:
        plan_path = Path(str(plan_out))
        if not plan_path.is_absolute():
            plan_path = root / plan_path
        WORK.save_json(plan_path, plan)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return code


def _headless(args: list[str], root: Path) -> int:
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--root", default=".")
    ap.add_argument("--target", required=True)
    ap.add_argument("--stage")
    ap.add_argument("--artifact")
    ap.add_argument("--store", default="sdlc/canonical/store.json")
    ap.add_argument("--project-profile", required=True)
    ap.add_argument("--source-profile", required=True)
    ap.add_argument("--provider-config", required=True)
    ap.add_argument("--run-dir")
    ap.add_argument("--plan-out")
    ap.add_argument("--result-out")
    ap.add_argument("--plan-only", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--max-hops", type=int)
    ap.add_argument("--allow-business-truth-change", action="store_true")
    ns, _ = ap.parse_known_args(args)

    store_path = Path(ns.store) if Path(ns.store).is_absolute() else root / ns.store
    project_path = Path(ns.project_profile) if Path(ns.project_profile).is_absolute() else root / ns.project_profile
    source_path = Path(ns.source_profile) if Path(ns.source_profile).is_absolute() else root / ns.source_profile
    provider_path = Path(ns.provider_config) if Path(ns.provider_config).is_absolute() else root / ns.provider_config
    project_profile = WORK.CONFIG.load_config(project_path)
    source_profile = WORK.CONFIG.load_config(source_path)
    policy = WORK.CONFIG.delivery_policy(project_profile) if project_profile else None
    hops = ns.max_hops if ns.max_hops is not None else int(policy.get("graph_hops", 4) if policy else 4)
    try:
        plan = WORK.build_plan(
            root,
            target_id=ns.target,
            store_path=store_path,
            stage=ns.stage,
            artifact=ns.artifact,
            max_hops=hops,
            allow_business_truth_change=ns.allow_business_truth_change,
            project_profile=project_profile,
            source_profile=source_profile,
        )
        # Handoff and Stage Result loading must stay anchored to the actual project root.
        # Without this marker HEADLESS execution can succeed but lose human-decision uncertainty.
        plan["_root"] = str(root)
        plan = _apply_plan_tailoring(root, plan, explicit_artifact=bool(ns.artifact))
        if ns.plan_out:
            out = Path(ns.plan_out)
            if not out.is_absolute():
                out = root / out
            WORK.save_json(out, plan)
        if ns.plan_only:
            result = {"status": "PLAN_READY", "plan": plan}
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        if not provider_path.is_file():
            result = {"status": "NOT_EXECUTED_PROVIDER_CONFIG_MISSING", "provider_config": str(provider_path), "canonical_applied": False}
        else:
            provider = WORK.load_json(provider_path)
            if ns.run_dir:
                run_dir = Path(ns.run_dir)
                if not run_dir.is_absolute():
                    run_dir = root / run_dir
            else:
                run_dir = root / "sdlc/runtime/work-runs" / f"{TAILOR._safe_target(ns.target)}-{plan['selection']['stage']}"
            result = WORK.execute_plan(
                root,
                plan,
                provider_config=provider,
                run_dir=run_dir,
                store_path=store_path,
                dry_run=ns.dry_run,
                source_profile=source_profile,
            )
            if result.get("status") in SUCCESS:
                metadata = _record_projection(root, plan)
                if metadata:
                    result["projection_metadata"] = metadata
                try:
                    handoff = HANDOFF.build_user_handoff(ns.target, plan, result)
                    handoff_path = HANDOFF._write_handoff(root, ns.target, plan, result, handoff)
                    result["user_handoff"] = handoff
                    result["handoff_path"] = handoff_path.relative_to(root).as_posix()
                except Exception as exc:  # Handoff is a view; execution result stays authoritative.
                    result["handoff_warning"] = str(exc)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {"status": "TAILORED_WORK_FAILED", "error": str(exc), "canonical_applied": False}
    if ns.result_out:
        out = Path(ns.result_out)
        if not out.is_absolute():
            out = root / out
        WORK.save_json(out, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") in SUCCESS | {"PLAN_READY"} else 3


def main(argv: list[str] | None = None) -> int:
    args = list(argv or [])
    root = Path(_value(args, "--root", ".") or ".").resolve()
    try:
        resolved = CONFIG.resolve_runtime_config(root)
        legacy_path = root / CONFIG.DEFAULT_PROVIDER_CONFIG_PATH
        legacy = CONFIG.load_config(legacy_path) if legacy_path.is_file() else {}
        runtime = CONFIG.resolve_agent_runtime(resolved.get("project") or {}, legacy_provider=legacy)
        if runtime.get("execution_mode") == "INTERACTIVE":
            return _interactive(args, root)
        return _headless(args, root)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "TAILORED_WORK_FAILED", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
