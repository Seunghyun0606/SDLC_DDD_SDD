#!/usr/bin/env python3
"""PM/RQ Human Control Plane focused on working software, decisions, risk and stale views.

Internal Stage is hidden unless ``--debug-stage`` is requested. Technical verification never
implies customer acceptance; delivery states come from explicit evidence-backed events.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename); mod = importlib.util.module_from_spec(spec); assert spec and spec.loader; sys.modules[name] = mod; spec.loader.exec_module(mod); return mod

CONFIG = _load("human_check_config", "runtime_config_v19.py")
TAILOR = _load("human_check_tailoring", "tailoring_runtime.py")
WORK = _load("human_check_work", "run_work.py")
BASE_CHECK = _load("human_check_base_helpers", "run_check.py")
DELIVERY = _load("human_check_delivery", "delivery_status_runtime.py")


def _field(entity: dict[str, Any], *names: str) -> Any:
    fields = entity.get("fields") or {}
    for name in names:
        if name in fields and fields[name] not in (None, ""): return fields[name]
    return None


def _stage(entity: dict[str, Any]) -> str | None: return WORK._latest_target_stage(entity)
def _open_items(entity: dict[str, Any]) -> list[dict[str, str]]: return BASE_CHECK._open_values(entity)
def _provenance_artifacts(entity: dict[str, Any]) -> list[str]: return sorted({str(x.get("source_artifact")) for x in entity.get("provenance", []) if str(x.get("source_artifact") or "").strip()})


def _profile_ids(project: dict[str, Any]) -> dict[str, str]:
    """Expose v1.10 Engineering naming while preserving the legacy internal alias."""
    profiles = dict(TAILOR.project_profile_ids(project))
    engineering = str(
        CONFIG.nested(
            project,
            "documents",
            "engineering",
            "profile",
            default=CONFIG.nested(
                project,
                "documents",
                "internal",
                "profile",
                default=CONFIG.DEFAULT_ENGINEERING_PROFILE,
            ),
        )
        or CONFIG.DEFAULT_ENGINEERING_PROFILE
    )
    profiles["engineering"] = engineering
    profiles["internal"] = engineering
    return profiles


def _change_state(root: Path, rq_id: str) -> dict[str, Any]:
    state = TAILOR.load_change_state(root, rq_id)
    return {
        "provisional": state.get("provisional_change_level"), "effective": state.get("effective_change_level"),
        "reason": state.get("classification_reason", []), "uncertainty": state.get("uncertainty", []),
        "typed_facts": state.get("typed_facts", {}), "candidate_hints": state.get("candidate_hints", []),
        "escalations": len(state.get("escalation_history", [])), "status": state.get("status") or ("CLASSIFIED" if state else "NOT_CLASSIFIED"),
    }


def _target_freshness(root: Path, rq_id: str, canonical_revision: int) -> dict[str, Any]:
    all_views = TAILOR.projection_freshness(root, canonical_revision)
    rows = [x for x in all_views.get("views", []) if not x.get("target_id") or str(x.get("target_id")) == rq_id]
    return {
        "stale": [x for x in rows if x.get("freshness") == "STALE_VIEW"],
        "pending_review": [x for x in rows if x.get("freshness") == "PENDING_REVIEW"],
        "current": [x for x in rows if x.get("freshness") == "CURRENT"],
    }


def _working_state(delivery: dict[str, Any], opens: list[dict[str, str]], freshness: dict[str, Any]) -> str:
    if delivery.get("as_built_reconciled"): return "완료·현행화"
    if delivery.get("deployment_completed"): return "배포완료·AS-BUILT 대기"
    if delivery.get("customer_acceptance") == "ACCEPTED": return "배포 대기"
    if delivery.get("technical_verification_passed"): return "고객 인수 대기"
    if delivery.get("development_started"): return "개발·검증 진행"
    if opens: return "사람 결정 대기"
    if freshness.get("stale"): return "View 현행화 필요"
    return "작업 준비"


def _next_action(delivery: dict[str, Any], opens: list[dict[str, str]], freshness: dict[str, Any]) -> str:
    if opens: return "업무 의미/권위가 필요한 미확정 항목을 결정한다."
    if freshness.get("stale"): return "STALE_VIEW를 재생성하고 필요한 Human/Customer Review를 수행한다."
    if not delivery.get("development_started"): return "Change Level의 최소 Semantic Work Plan으로 개발을 시작한다."
    if not delivery.get("build_passed"): return "Source 변경과 Build Evidence를 확인한다."
    if not delivery.get("test_passed"): return "Test Evidence를 확보한다."
    if not delivery.get("regression_passed"): return "Regression 범위를 실행하고 결과를 기록한다."
    if not delivery.get("technical_verification_passed"): return "기술 검증을 완료한다."
    if delivery.get("customer_acceptance") != "ACCEPTED": return "Customer Acceptance 결정을 받는다."
    if not delivery.get("deployment_completed"): return "배포 Evidence를 기록한다."
    if not delivery.get("as_built_reconciled"): return "Accepted Delta를 AS-BUILT에 Reconcile한다."
    return "다음 변경에서 Historical Impact Evidence를 재사용한다."


def _rq_row(root: Path, rq_id: str, entity: dict[str, Any], canonical_revision: int, *, debug_stage: bool) -> dict[str, Any]:
    opens = _open_items(entity); delivery = DELIVERY.snapshot(root, rq_id); freshness = _target_freshness(root, rq_id, canonical_revision); change = _change_state(root, rq_id)
    uncertain = list(change.get("uncertainty") or []) + [x.get("value", "") for x in opens]
    passed = [name for name, ok in [
        ("BUILD", delivery.get("build_passed")), ("TEST", delivery.get("test_passed")), ("REGRESSION", delivery.get("regression_passed")), ("TECHNICAL_VERIFY", delivery.get("technical_verification_passed")), ("CUSTOMER_ACCEPTANCE", delivery.get("customer_acceptance") == "ACCEPTED"), ("DEPLOYMENT", delivery.get("deployment_completed")), ("AS_BUILT", delivery.get("as_built_reconciled"))
    ] if ok]
    row: dict[str, Any] = {
        "rq_id": rq_id,
        "what_changed": _field(entity, "current_conclusion", "to_be", "desired_outcome", "title", "name", "summary"),
        "title": _field(entity, "title", "name", "requirement_name", "summary"),
        "working_state": _working_state(delivery, opens, freshness),
        "change_level": change,
        "what_is_uncertain": uncertain,
        "what_blocks_release": {
            "human_decisions": len(opens), "delivery_gate_blocked": bool(delivery.get("release_blocked")), "stale_views": len(freshness["stale"]), "pending_view_reviews": len(freshness["pending_review"]),
        },
        "who_must_decide": _field(entity, "decision_owner", "owner", "assignee", "requirement_owner"),
        "evidence_passed": passed,
        "delivery": delivery,
        "views": {"stale_count": len(freshness["stale"]), "pending_review_count": len(freshness["pending_review"]), "current_count": len(freshness["current"])},
        "next": _next_action(delivery, opens, freshness),
        "major_artifacts": _provenance_artifacts(entity)[-5:],
    }
    if debug_stage: row["internal_stage_debug"] = _stage(entity)
    return row


def _project_view(root: Path, store: dict[str, Any], *, debug_stage: bool) -> dict[str, Any]:
    revision = int(store.get("revision") or 0)
    rows = [_rq_row(root, eid, entity, revision, debug_stage=debug_stage) for eid, entity in sorted((store.get("entities") or {}).items()) if str(entity.get("entity_type") or "").upper() == "RQ"]
    freshness = TAILOR.projection_freshness(root, revision)
    return {
        "view": "PROJECT_HUMAN_CONTROL_PLANE",
        "questions": ["What changed?", "What is uncertain?", "What blocks release?", "Who must decide?", "What evidence passed?", "What remains stale?", "What is next?"],
        "rq_count": len(rows),
        "release_blocked_count": sum(1 for x in rows if x["what_blocks_release"]["delivery_gate_blocked"] or x["what_blocks_release"]["human_decisions"] or x["what_blocks_release"]["stale_views"]),
        "human_decision_required_total": sum(int(x["what_blocks_release"]["human_decisions"]) for x in rows),
        "stale_human_view_count": freshness.get("stale_count", 0),
        "pending_view_review_count": freshness.get("pending_review_count", 0),
        "requirements": rows,
        "internal_stage_hidden": not debug_stage,
        "stage_completion_dashboard": False,
    }


def _rq_view(root: Path, rq_id: str, entity: dict[str, Any], store: dict[str, Any], *, debug_stage: bool) -> dict[str, Any]:
    row = _rq_row(root, rq_id, entity, int(store.get("revision") or 0), debug_stage=debug_stage); opens = _open_items(entity)
    source_rows = [{"source_artifact": p.get("source_artifact"), "evidence": p.get("evidence"), "source_hash": p.get("source_hash"), **({"stage": p.get("stage")} if debug_stage else {})} for p in entity.get("provenance", [])[-10:]]
    return {
        "view": "RQ_REVIEW",
        "summary": row,
        "human_decisions_required": opens,
        "agent_or_technical_investigation": [x for x in opens if any(k in x.get("value", "").upper() for k in ["CHECK_REQUIRED", "CANDIDATE", "OBSERVED"])],
        "evidence": source_rows,
        "internal_stage_hidden": not debug_stage,
    }


def check(root: Path, *, target: str | None, setup_only: bool, debug_stage: bool) -> dict[str, Any]:
    root = root.resolve(); resolved = CONFIG.resolve_runtime_config(root); project = resolved.get("project") or {}; legacy_path = root / CONFIG.DEFAULT_PROVIDER_CONFIG_PATH; legacy = CONFIG.load_config(legacy_path) if legacy_path.is_file() else {}; runtime = CONFIG.resolve_agent_runtime(project, legacy_provider=legacy) if project else {"ready": False, "execution_mode": "INTERACTIVE"}
    ready = resolved.get("source_kind") != "UNCONFIGURED" and runtime.get("ready")
    profiles = _profile_ids(project) if project else {}
    if setup_only:
        return {"schema_version": 5, "status": "READY" if ready else "SETUP_OR_AGENT_EXECUTION_REQUIRED", "setup": {"project_config": (root / CONFIG.PROJECT_ENTRY_PATH).is_file(), "config_source": resolved.get("source_kind"), "agent_execution": {k: runtime.get(k) for k in ["execution_mode", "ready", "provider_required", "provider_id", "config_source"]}, "config_usage": resolved.get("usage"), "tailoring_profiles": profiles, "engineering_profile": profiles.get("engineering"), "change_level_policy": CONFIG.nested(project, "change", "level_policy", default="AUTO") if project else None}}
    store = TAILOR.load_store(root)
    base: dict[str, Any] = {"schema_version": 5, "status": "READY" if ready else "SETUP_OR_AGENT_EXECUTION_REQUIRED", "project": {"name": CONFIG.nested(project, "project", "name", default=None), "mode": CONFIG.project_mode(project), "delivery_profile": CONFIG.delivery_profile(project), "change_level_policy": CONFIG.nested(project, "change", "level_policy", default="AUTO"), "artifact_profiles": profiles, "engineering_profile": profiles.get("engineering")}, "canonical_revision": int(store.get("revision") or 0)}
    if target and target.lower() not in {"project", "all"}:
        entity = (store.get("entities") or {}).get(target); base["rq_review"] = _rq_view(root, target, entity, store, debug_stage=debug_stage) if entity else {"rq_id": target, "found": False}
    else: base["project_view"] = _project_view(root, store, debug_stage=debug_stage)
    reverse = BASE_CHECK._latest_reverse(root)
    if reverse:
        data = reverse["data"]; base["brownfield_reconciliation"] = {"latest_reverse_path": reverse["path"], "review_required": bool(data.get("review_required") or data.get("reverse_candidates") or data.get("candidate_updates")), "coverage_gaps": data.get("coverage_gaps", []), "authority_rule": "Source observation never auto-rewrites confirmed Business Truth."}
    return base


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Show PM/RQ control plane without Stage completion inference."); ap.add_argument("target_positional", nargs="?"); ap.add_argument("--root", default="."); ap.add_argument("--target"); ap.add_argument("--setup", action="store_true"); ap.add_argument("--debug-stage", action="store_true"); ap.add_argument("--out"); args = ap.parse_args(argv); target = args.target or args.target_positional
    try: result = check(Path(args.root), target=target, setup_only=args.setup, debug_stage=args.debug_stage)
    except (OSError, ValueError, json.JSONDecodeError) as exc: result = {"status": "CHECK_FAILED", "error": str(exc)}
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        path = Path(args.out); path = path if path.is_absolute() else Path(args.root).resolve() / path; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(text, encoding="utf-8")
    print(text, end=""); return 0 if result.get("status") == "READY" else 4 if result.get("status") == "SETUP_OR_AGENT_EXECUTION_REQUIRED" else 2


if __name__ == "__main__": raise SystemExit(main())
