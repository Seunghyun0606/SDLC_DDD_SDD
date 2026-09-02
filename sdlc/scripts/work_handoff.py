#!/usr/bin/env python3
"""User-facing /work adapter around the guarded ``run_work.py`` executor."""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
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


WORK = _load("wp4_guarded_work", "run_work.py")
HUMAN_DECISION_CATEGORIES = {
    "BUSINESS_POLICY", "SCOPE", "APPROVAL", "TECHNICAL_CHOICE", "ACCEPTANCE",
}
STAGE_LABELS = {
    "INTAKE": "요구사항정의", "DECOMPOSE": "요구사항정의", "CLARIFY": "확인질문",
    "PROCESS": "업무프로세스", "DISCOVERY": "현행근거", "IMPACT": "영향분석",
    "DESIGN": "기능설계", "PROGRAM": "프로그램명세", "DEVELOPMENT": "구현결과",
    "TEST": "테스트시나리오", "VERIFY": "검증결과", "KNOWLEDGE_PROMOTION": "운영지식",
}
SUCCESS = {"APPLIED", "IDEMPOTENT", "NO_CHANGE", "DRY_RUN_VALIDATED"}
SAFE_NAME_RE = re.compile(r"[^0-9A-Za-z가-힣_.-]+")


def _safe_name(value: str, fallback: str) -> str:
    text = SAFE_NAME_RE.sub("_", str(value or "")).strip("_.-")
    return text[:80] or fallback


def _target_name(plan: dict[str, Any]) -> str:
    fields = ((((plan.get("target") or {}).get("entity") or {}).get("fields")) or {})
    for key in ("name", "requirement_name", "title", "normalized_text"):
        if str(fields.get(key) or "").strip():
            return str(fields[key]).strip()
    return str((plan.get("target") or {}).get("id") or "작업")


def default_document_path(plan: dict[str, Any]) -> str:
    target = _safe_name(str((plan.get("target") or {}).get("id") or "TARGET"), "TARGET")
    name = _safe_name(_target_name(plan), "작업")
    stage = str((plan.get("selection") or {}).get("stage") or "WORK")
    return f"docs/10_산출물/{target}_{name}_{STAGE_LABELS.get(stage, stage)}.md"


def partition_uncertainty(stage_result: dict[str, Any] | None) -> tuple[list[dict[str, Any]], list[Any]]:
    review_items: list[dict[str, Any]] = []
    agent_open: list[Any] = []
    for item in (stage_result or {}).get("uncertainty", []) or []:
        if isinstance(item, dict):
            category = str(item.get("category") or "").upper()
            if item.get("requires_human_decision") is True and category in HUMAN_DECISION_CATEGORIES:
                review_items.append({
                    "state": item.get("state"),
                    "category": category,
                    "question": item.get("question") or item.get("message") or item.get("detail") or "확인이 필요합니다.",
                    "evidence": item.get("evidence") or item.get("locator"),
                })
                continue
        agent_open.append(item)
    return review_items, agent_open


def _load_stage_result(root: Path, execution: dict[str, Any]) -> dict[str, Any] | None:
    raw = execution.get("result_path")
    if not raw:
        return None
    path = Path(str(raw))
    if not path.is_absolute():
        path = root / path
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return None
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def build_user_handoff(target: str, plan: dict[str, Any], execution: dict[str, Any] | None = None) -> dict[str, Any]:
    execution = execution or {}
    stage_result = _load_stage_result(Path(plan.get("_root") or "."), execution) if execution else None
    review_items, agent_open = partition_uncertainty(stage_result)
    success = execution.get("status") in SUCCESS
    if success and review_items:
        next_command = f"python sdlc/scripts/harness.py review --target {target} --by <확인자> --answer <결정내용>"
        message = "Agent 초안이 완료되었습니다. 아래 판단권한 항목만 확인하면 됩니다."
    elif success:
        next_command = f"python sdlc/scripts/harness.py work --target {target}"
        message = "Agent 초안/검증이 완료되었습니다. 사람 판단이 필요한 항목이 없어 다음 단계로 진행할 수 있습니다."
    else:
        next_command = None
        message = "실행이 완료되지 않았습니다. Runtime 상태를 먼저 확인해야 합니다."
    return {
        "document": (plan.get("selection") or {}).get("artifact_path"),
        "review_required": bool(review_items),
        "review_items": review_items,
        "agent_open_items": agent_open,
        "next_stage_candidate": plan.get("next_stage_candidate"),
        "next_command": next_command,
        "message": message,
    }


def _handoff_path(root: Path, target: str) -> Path:
    return root / "sdlc/runtime/work-handoff" / f"{_safe_name(target, 'TARGET')}.json"


def _write_handoff(root: Path, target: str, plan: dict[str, Any], execution: dict[str, Any], handoff: dict[str, Any]) -> Path:
    path = _handoff_path(root, target)
    WORK.save_json(path, {
        "schema_version": 1,
        "target": target,
        "stage": (plan.get("selection") or {}).get("stage"),
        "document": handoff.get("document"),
        "execution_status": execution.get("status"),
        "review_required": handoff.get("review_required"),
        "review_items": handoff.get("review_items"),
        "agent_open_items": handoff.get("agent_open_items"),
        "next_stage_candidate": handoff.get("next_stage_candidate"),
        "next_command": handoff.get("next_command"),
        "stage_result_path": execution.get("result_path"),
    })
    return path


def _provider_policy() -> dict[str, Any]:
    return {
        "goal": "Evidence로 가능한 내용을 Agent가 먼저 작성하고 사람에게는 판단권한 항목만 요청한다.",
        "human_decision_categories": sorted(HUMAN_DECISION_CATEGORIES),
        "uncertainty_metadata": {
            "requires_human_decision": "true only when a project authority must decide",
            "category": "one of human_decision_categories",
            "question": "one concrete decision question",
        },
        "agent_owned_unknown_rule": "Evidence 조사나 분석으로 확인 가능한 미확정은 OPEN/CHECK_REQUIRED로 유지하고 requires_human_decision을 붙이지 않는다.",
        "no_invention": True,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run one guarded work stage and return a human-friendly handoff.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--target", required=True)
    parser.add_argument("--stage")
    parser.add_argument("--artifact")
    parser.add_argument("--store", default="sdlc/canonical/store.json")
    parser.add_argument("--project-profile", default="sdlc/config/project-profile.yaml")
    parser.add_argument("--source-profile", default="sdlc/config/source-profile.yaml")
    parser.add_argument("--provider-config", default="sdlc/config/agent-provider.json")
    parser.add_argument("--run-dir")
    parser.add_argument("--plan-out")
    parser.add_argument("--result-out")
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-hops", type=int)
    parser.add_argument("--allow-business-truth-change", action="store_true")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    store_path = Path(args.store) if Path(args.store).is_absolute() else root / args.store
    project_path = Path(args.project_profile) if Path(args.project_profile).is_absolute() else root / args.project_profile
    source_path = Path(args.source_profile) if Path(args.source_profile).is_absolute() else root / args.source_profile
    project_profile = WORK.CONFIG.load_config(project_path)
    source_profile = WORK.CONFIG.load_config(source_path)
    policy = WORK.CONFIG.delivery_policy(project_profile) if project_profile else None
    hops = args.max_hops if args.max_hops is not None else int(policy.get("graph_hops", 4) if policy else 4)

    try:
        plan = WORK.build_plan(
            root, target_id=args.target, store_path=store_path, stage=args.stage, artifact=args.artifact,
            max_hops=hops, allow_business_truth_change=args.allow_business_truth_change,
            project_profile=project_profile, source_profile=source_profile,
        )
        plan["_root"] = str(root)
        if not args.artifact:
            current = str((plan.get("selection") or {}).get("artifact_path") or "")
            if (plan.get("selection") or {}).get("artifact_reason") == "NEW_STAGE_ARTIFACT" or current.startswith("sdlc/runtime/work/"):
                rel = default_document_path(plan)
                artifact_abs, rel = WORK.safe_repo_path(root, rel)
                plan["selection"].update({
                    "artifact_path": rel,
                    "artifact_reason": "USER_DOCUMENT_DEFAULT",
                    "artifact_override": False,
                    "artifact_existed_at_plan_time": artifact_abs.is_file(),
                    "artifact_hash_at_plan_time": WORK._hash_file(artifact_abs),
                })
        plan["human_handoff_policy"] = _provider_policy()
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"status": "PLAN_FAILED", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2

    if args.plan_out:
        out = Path(args.plan_out) if Path(args.plan_out).is_absolute() else root / args.plan_out
        WORK.save_json(out, plan)
    if args.plan_only:
        handoff = {
            "document": plan["selection"]["artifact_path"], "review_required": False,
            "review_items": [], "agent_open_items": [], "next_stage_candidate": plan.get("next_stage_candidate"),
            "next_command": f"python sdlc/scripts/harness.py work --target {args.target}",
            "message": "이 문서는 사람이 빈 Template을 작성하는 대상이 아닙니다. Provider 연결 시 Agent가 Evidence 기반 초안을 작성합니다.",
        }
        print(json.dumps({"status": "PLAN_READY", "plan": plan, "user_handoff": handoff}, ensure_ascii=False, indent=2))
        return 0

    provider_path = Path(args.provider_config) if Path(args.provider_config).is_absolute() else root / args.provider_config
    if not provider_path.is_file():
        result = {"status": "NOT_EXECUTED_PROVIDER_CONFIG_MISSING", "provider_config": str(provider_path), "canonical_applied": False, "executable": False}
        handoff = build_user_handoff(args.target, plan, result)
        output = {**result, "user_handoff": handoff}
        if args.result_out:
            out = Path(args.result_out) if Path(args.result_out).is_absolute() else root / args.result_out
            WORK.save_json(out, output)
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 4

    try:
        provider = WORK.load_json(provider_path)
        run_dir = (Path(args.run_dir) if Path(args.run_dir).is_absolute() else root / args.run_dir) if args.run_dir else root / "sdlc/runtime/work-runs" / f"{_safe_name(args.target, 'TARGET')}-{plan['selection']['stage']}"
        result = WORK.execute_plan(root, plan, provider_config=provider, run_dir=run_dir, store_path=store_path, dry_run=args.dry_run, source_profile=source_profile)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        result = {"status": "EXECUTION_FAILED", "error": str(exc), "canonical_applied": False}

    handoff = build_user_handoff(args.target, plan, result)
    handoff_path = _write_handoff(root, args.target, plan, result, handoff)
    output = {**result, "user_handoff": handoff, "handoff_path": handoff_path.relative_to(root).as_posix()}
    if args.result_out:
        out = Path(args.result_out) if Path(args.result_out).is_absolute() else root / args.result_out
        WORK.save_json(out, output)
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if result.get("status") in SUCCESS else 3


if __name__ == "__main__":
    raise SystemExit(main())
