#!/usr/bin/env python3
"""Human Control Plane /check view for v1.9.

Default output hides internal Stage names and exposes project/RQ decisions, risks, Change Level,
artifact freshness and next human action. ``--debug-stage`` restores internal Stage for Harness
administrators without making it a normal user concern.
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
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


CONFIG = _load("human_check_config", "runtime_config_v19.py")
TAILOR = _load("human_check_tailoring", "tailoring_runtime.py")
WORK = _load("human_check_work", "run_work.py")
BASE_CHECK = _load("human_check_base_helpers", "run_check.py")

STAGE_TO_HUMAN = {
    None: "요구사항 등록",
    "INTAKE": "요구사항 등록",
    "DECOMPOSE": "요구사항 이해",
    "CLARIFY": "업무 확인",
    "PROCESS": "업무 분석",
    "DISCOVERY": "기술 조사",
    "IMPACT": "영향 분석",
    "DESIGN": "상세 설계",
    "PROGRAM": "개발 준비",
    "DEVELOPMENT": "개발",
    "TEST": "테스트",
    "VERIFY": "검증·인수",
    "KNOWLEDGE_PROMOTION": "완료·현행화",
}
NEXT_ACTION = {
    "요구사항 등록": "요구사항 원본과 생성 이유를 확인한다.",
    "요구사항 이해": "Agent 초안의 요구 목적·범위와 미확정 사항을 검토한다.",
    "업무 확인": "사람 결정이 필요한 업무정책만 확인한다.",
    "업무 분석": "AS-IS/TO-BE 흐름과 예외를 검토한다.",
    "기술 조사": "Source/DB/Interface Evidence와 Coverage Gap을 확인한다.",
    "영향 분석": "영향 범위와 Change Level을 확정한다.",
    "상세 설계": "기능 동작과 인수조건을 검토한다.",
    "개발 준비": "Program/Task/Source Mapping과 구현 준비도를 확인한다.",
    "개발": "구현 및 예상 외 Legacy 영향 발견 여부를 확인한다.",
    "테스트": "AC/TC Coverage와 실패 원인을 확인한다.",
    "검증·인수": "최종 Acceptance와 현행화 대상을 확인한다.",
    "완료·현행화": "재사용 Knowledge와 stale View가 없는지 확인한다.",
}


def _field(entity: dict[str, Any], *names: str) -> Any:
    fields = entity.get("fields") or {}
    for name in names:
        if name in fields and fields[name] not in (None, ""):
            return fields[name]
    return None


def _stage(entity: dict[str, Any]) -> str | None:
    return WORK._latest_target_stage(entity)


def _human_state(entity: dict[str, Any]) -> str:
    return STAGE_TO_HUMAN.get(_stage(entity), "분석·설계")


def _open_items(entity: dict[str, Any]) -> list[dict[str, str]]:
    return BASE_CHECK._open_values(entity)


def _provenance_artifacts(entity: dict[str, Any]) -> list[str]:
    return sorted({str(row.get("source_artifact")) for row in entity.get("provenance", []) if str(row.get("source_artifact") or "").strip()})


def _stage_seen(entity: dict[str, Any], stage: str) -> bool:
    return any(str(row.get("stage") or "") == stage for row in entity.get("provenance", []))


def _change_state(root: Path, rq_id: str) -> dict[str, Any]:
    state = TAILOR.load_change_state(root, rq_id)
    return {
        "provisional": state.get("provisional_change_level"),
        "effective": state.get("effective_change_level"),
        "reason": state.get("classification_reason", []),
        "escalations": len(state.get("escalation_history", [])),
        "status": state.get("status") or ("CLASSIFIED" if state else "NOT_CLASSIFIED"),
    }


def _rq_row(root: Path, rq_id: str, entity: dict[str, Any], *, debug_stage: bool) -> dict[str, Any]:
    state = _human_state(entity)
    opens = _open_items(entity)
    row: dict[str, Any] = {
        "rq_id": rq_id,
        "title": _field(entity, "title", "name", "requirement_name", "summary"),
        "user_state": state,
        "change_level": _change_state(root, rq_id),
        "human_decision_required_count": len(opens),
        "technical_gap": bool(any(word in json.dumps(opens, ensure_ascii=False).upper() for word in ["CHECK_REQUIRED", "CANDIDATE", "PARTIAL"])),
        "impact_coverage": "CHECK_REQUIRED" if any("COVERAGE" in x.get("value", "").upper() for x in opens) else "NO_EXPLICIT_GAP",
        "development": "DONE" if _stage_seen(entity, "DEVELOPMENT") else "NOT_DONE",
        "verification": "DONE" if _stage_seen(entity, "VERIFY") else ("TESTING" if _stage_seen(entity, "TEST") else "NOT_DONE"),
        "acceptance": "ACCEPTED_OR_VERIFIED" if _stage_seen(entity, "VERIFY") else "PENDING",
        "owner": _field(entity, "owner", "assignee", "requirement_owner"),
        "next_action": NEXT_ACTION.get(state, "현재 산출물과 미확정 사항을 검토한다."),
        "primary_artifacts": _provenance_artifacts(entity)[-5:],
    }
    if debug_stage:
        row["internal_stage"] = _stage(entity)
    return row


def _project_view(root: Path, store: dict[str, Any], *, debug_stage: bool) -> dict[str, Any]:
    rq_rows = [
        _rq_row(root, entity_id, entity, debug_stage=debug_stage)
        for entity_id, entity in sorted((store.get("entities") or {}).items())
        if str(entity.get("entity_type") or "").upper() == "RQ"
    ]
    freshness = TAILOR.projection_freshness(root, int(store.get("revision") or 0))
    return {
        "view": "PROJECT_HUMAN_CONTROL_PLANE",
        "rq_count": len(rq_rows),
        "human_decision_required_total": sum(int(row["human_decision_required_count"]) for row in rq_rows),
        "stale_human_view_count": freshness["stale_count"],
        "requirements": rq_rows,
        "freshness": freshness,
        "internal_stage_hidden": not debug_stage,
    }


def _rq_view(root: Path, rq_id: str, entity: dict[str, Any], store: dict[str, Any], *, debug_stage: bool) -> dict[str, Any]:
    row = _rq_row(root, rq_id, entity, debug_stage=debug_stage)
    fields = entity.get("fields") or {}
    opens = _open_items(entity)
    confirmed = [
        {"path": key, "value": value}
        for key, value in fields.items()
        if value not in (None, "") and not any(word in str(value).upper() for word in BASE_CHECK.OPEN_WORDS)
    ]
    source_rows = [
        {
            "stage": p.get("stage") if debug_stage else None,
            "source_artifact": p.get("source_artifact"),
            "evidence": p.get("evidence"),
            "source_hash": p.get("source_hash"),
        }
        for p in entity.get("provenance", [])[-10:]
    ]
    if not debug_stage:
        for item in source_rows:
            item.pop("stage", None)
    return {
        "view": "RQ_REVIEW",
        "summary": {
            "rq_id": rq_id,
            "title": row.get("title"),
            "original_requirement": _field(entity, "original_requirement", "request", "description", "source_text"),
            "why_created": _field(entity, "grouping_basis", "creation_reason", "source_locator"),
            "current_conclusion": _field(entity, "current_conclusion", "to_be", "desired_outcome", "result"),
            "user_state": row["user_state"],
            "change_level": row["change_level"],
            "risk": _field(entity, "risk", "risks"),
            "owner": row["owner"],
            "next_action": row["next_action"],
        },
        "confirmed": confirmed,
        "human_decisions_required": opens,
        "agent_or_technical_investigation": [x for x in opens if any(k in x.get("value", "").upper() for k in ["CHECK_REQUIRED", "CANDIDATE", "OBSERVED"])],
        "major_artifacts": row["primary_artifacts"],
        "evidence": source_rows,
        "internal_stage_hidden": not debug_stage,
    }


def check(root: Path, *, target: str | None, setup_only: bool, debug_stage: bool) -> dict[str, Any]:
    root = root.resolve()
    resolved = CONFIG.resolve_runtime_config(root)
    project = resolved.get("project") or {}
    legacy_path = root / CONFIG.DEFAULT_PROVIDER_CONFIG_PATH
    legacy = CONFIG.load_config(legacy_path) if legacy_path.is_file() else {}
    runtime = CONFIG.resolve_agent_runtime(project, legacy_provider=legacy) if project else {"ready": False, "execution_mode": "INTERACTIVE"}
    if setup_only:
        return {
            "schema_version": 4,
            "status": "READY" if resolved.get("source_kind") != "UNCONFIGURED" and runtime.get("ready") else "SETUP_OR_AGENT_EXECUTION_REQUIRED",
            "setup": {
                "project_config": (root / CONFIG.PROJECT_ENTRY_PATH).is_file(),
                "config_source": resolved.get("source_kind"),
                "agent_execution": {k: runtime.get(k) for k in ["execution_mode", "ready", "provider_required", "provider_id", "config_source"]},
                "config_usage": resolved.get("usage"),
                "tailoring_profiles": TAILOR.project_profile_ids(project) if project else {},
                "change_level_policy": CONFIG.nested(project, "change", "level_policy", default="AUTO") if project else None,
            },
        }
    store = TAILOR.load_store(root)
    base = {
        "schema_version": 4,
        "status": "READY" if resolved.get("source_kind") != "UNCONFIGURED" and runtime.get("ready") else "SETUP_OR_AGENT_EXECUTION_REQUIRED",
        "project": {
            "name": CONFIG.nested(project, "project", "name", default=None),
            "mode": CONFIG.project_mode(project),
            "delivery_profile": CONFIG.delivery_profile(project),
            "change_level_policy": CONFIG.nested(project, "change", "level_policy", default="AUTO"),
            "artifact_profiles": TAILOR.project_profile_ids(project),
        },
        "canonical_revision": int(store.get("revision") or 0),
    }
    if target and target.lower() not in {"project", "all"}:
        entity = (store.get("entities") or {}).get(target)
        if not entity:
            base["rq_review"] = {"rq_id": target, "found": False}
        else:
            base["rq_review"] = _rq_view(root, target, entity, store, debug_stage=debug_stage)
    else:
        base["project_view"] = _project_view(root, store, debug_stage=debug_stage)
    reverse = BASE_CHECK._latest_reverse(root)
    if reverse:
        data = reverse["data"]
        base["brownfield_reconciliation"] = {
            "latest_reverse_path": reverse["path"],
            "review_required": bool(data.get("review_required") or data.get("reverse_candidates") or data.get("candidate_updates")),
            "coverage_gaps": data.get("coverage_gaps", []),
            "authority_rule": "Source observation never auto-rewrites confirmed Business Truth.",
        }
    return base


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Show PM/RQ Human Control Plane without requiring Stage knowledge.")
    ap.add_argument("target_positional", nargs="?")
    ap.add_argument("--root", default=".")
    ap.add_argument("--target")
    ap.add_argument("--setup", action="store_true")
    ap.add_argument("--debug-stage", action="store_true")
    ap.add_argument("--out")
    args = ap.parse_args(argv)
    target = args.target or args.target_positional
    try:
        result = check(Path(args.root), target=target, setup_only=args.setup, debug_stage=args.debug_stage)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {"status": "CHECK_FAILED", "error": str(exc)}
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        path = Path(args.out)
        if not path.is_absolute():
            path = Path(args.root).resolve() / path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if result.get("status") == "READY" else 4 if result.get("status") == "SETUP_OR_AGENT_EXECUTION_REQUIRED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
