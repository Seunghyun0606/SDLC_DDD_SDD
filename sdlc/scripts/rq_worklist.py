#!/usr/bin/env python3
"""Project RQ assignment + derived progress worklist.

Business meaning remains in the Canonical store. PM-owned planning data lives separately under
.sdlc/management, while progress/status is derived from the existing human check/delivery/projection
runtimes. The Markdown file is a generated stakeholder view, not another source of truth.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PLANNING_PATH = ".sdlc/management/rq-planning.json"
VIEW_PATH = "docs/00_관리/RQ_작업목록.md"
RUNTIME_PATH = "sdlc/runtime/management/rq-worklist.json"
PLANNING_FIELDS = [
    "priority", "pm_owner", "business_owner", "engineering_owner", "test_owner",
    "customer_decision_owner", "milestone", "planned_start", "planned_end", "note",
]


def _load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


CHECK = _load_module("rq_worklist_human_check", "tailored_check.py")
TAILOR = CHECK.TAILOR


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _load_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.is_file():
        return default
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON object required: {path}")
    return data


def _planning(root: Path) -> dict[str, Any]:
    data = _load_json(root / PLANNING_PATH, {"schema_version": 1, "requirements": {}})
    if int(data.get("schema_version") or 0) != 1:
        raise ValueError("unsupported rq planning schema_version")
    rows = data.setdefault("requirements", {})
    if not isinstance(rows, dict):
        raise ValueError("rq planning requirements must be a mapping")
    return data


def _save(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _external_ids(entity: dict[str, Any]) -> list[str]:
    fields = entity.get("fields") or {}
    raw = fields.get("external_requirement_ids")
    if isinstance(raw, list):
        return [str(x) for x in raw if str(x).strip()]
    if raw not in (None, ""):
        return [str(raw)]
    one = fields.get("external_requirement_id")
    return [str(one)] if one not in (None, "") else []


def _projection_state(view: dict[str, Any]) -> str:
    stale = int(view.get("stale_count") or 0)
    pending = int(view.get("pending_review_count") or 0)
    current = int(view.get("current_count") or 0)
    if stale:
        return f"현행화 필요 {stale}"
    if pending:
        return f"검토 대기 {pending}"
    if current:
        return f"현재 {current}"
    return "아직 생성 안 됨"


def build_rows(root: Path) -> tuple[list[dict[str, Any]], int]:
    root = root.resolve()
    store = TAILOR.load_store(root)
    planning = _planning(root).get("requirements") or {}
    project = CHECK.check(root, target=None, setup_only=False, debug_stage=False)
    control_rows = {
        str(row.get("rq_id")): row
        for row in ((project.get("project_view") or {}).get("requirements") or [])
    }
    rows: list[dict[str, Any]] = []
    for rq_id, entity in sorted((store.get("entities") or {}).items()):
        if str(entity.get("entity_type") or "").upper() != "RQ":
            continue
        control = control_rows.get(rq_id, {})
        plan = planning.get(rq_id) if isinstance(planning.get(rq_id), dict) else {}
        change = control.get("change_level") or {}
        blockers = control.get("what_blocks_release") or {}
        views = control.get("views") or {}
        row = {
            "rq_id": rq_id,
            "title": control.get("title") or (entity.get("fields") or {}).get("name") or "",
            "external_requirement_ids": _external_ids(entity),
            **{key: str(plan.get(key) or "") for key in PLANNING_FIELDS},
            "working_state": control.get("working_state") or "작업 준비",
            "change_level": change.get("effective") or change.get("provisional") or "미분류",
            "human_decision_count": int(blockers.get("human_decisions") or 0),
            "evidence_passed": list(control.get("evidence_passed") or []),
            "projection_state": _projection_state(views),
            "next_action": control.get("next") or "",
            "planning_updated_at": str(plan.get("updated_at") or ""),
        }
        rows.append(row)
    return rows, int(store.get("revision") or 0)


def _esc(value: Any) -> str:
    if isinstance(value, list):
        value = ", ".join(str(x) for x in value)
    return str(value if value is not None else "").replace("|", "\\|").replace("\n", "<br>")


def render(rows: list[dict[str, Any]], revision: int) -> str:
    columns = [
        ("rq_id", "RQ"), ("title", "요구사항명"), ("external_requirement_ids", "외부 요구ID"),
        ("priority", "우선순위"), ("pm_owner", "PM"), ("business_owner", "업무/BA"),
        ("engineering_owner", "설계·개발"), ("test_owner", "테스트"),
        ("customer_decision_owner", "고객 결정자"), ("milestone", "마일스톤"),
        ("planned_start", "계획시작"), ("planned_end", "계획종료"),
        ("working_state", "현재 상태"), ("change_level", "Change Level"),
        ("human_decision_count", "사람 결정 필요"), ("evidence_passed", "확보된 검증근거"),
        ("projection_state", "산출물 View"), ("next_action", "다음 작업"), ("note", "비고"),
    ]
    lines = [
        "# RQ 작업 목록", "",
        "> Canonical RQ + PM 계획정보 + Runtime 상태를 합성한 Generated View다. 요구사항 의미와 현재 상태를 이 표에서 수동 확정하지 않는다.",
        "", f"- Canonical Revision: `{revision}`", f"- RQ 수: **{len(rows)}**", f"- 생성시각: `{now()}`", "",
        "## 관리 원칙", "",
        "- PM이 직접 관리: 우선순위, 담당자, 마일스톤, 계획일, 비고",
        "- Runtime이 자동 계산: 현재 상태, Change Level, 사람 결정 필요, 검증근거, 산출물 View 상태, 다음 작업",
        "- 새 요구사항은 재-Intake 후 이 목록을 새로고침하면 RQ ID 기준으로 추가된다.",
        "- 요구사항 의미 변경은 `/change`로 처리한다.", "",
        "| " + " | ".join(label for _, label in columns) + " |",
        "|" + "|".join("---" for _ in columns) + "|",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_esc(row.get(key, "")) for key, _ in columns) + " |")
    if not rows:
        lines.append("| " + " | ".join(["인입된 RQ 없음"] + [""] * (len(columns) - 1)) + " |")
    lines += ["", "## 사용 명령", "", "```bash",
              "python sdlc/scripts/harness.py rq-list refresh",
              "python sdlc/scripts/harness.py rq-list assign --target RQ-001 --engineering-owner \"홍길동\" --test-owner \"김테스트\" --priority HIGH",
              "python sdlc/scripts/harness.py check RQ-001", "```", ""]
    return "\n".join(lines)


def refresh(root: Path, *, view_path: str = VIEW_PATH, runtime_path: str = RUNTIME_PATH) -> dict[str, Any]:
    root = root.resolve()
    rows, revision = build_rows(root)
    view = root / view_path
    view.parent.mkdir(parents=True, exist_ok=True)
    view.write_text(render(rows, revision), encoding="utf-8")
    machine = root / runtime_path
    payload = {
        "schema_version": 1,
        "generated_at": now(),
        "canonical_revision": revision,
        "rq_count": len(rows),
        "rows": rows,
        "business_truth_authority": False,
        "planning_source": PLANNING_PATH,
        "human_view": view_path,
    }
    _save(machine, payload)
    return {
        "status": "RQ_WORKLIST_REFRESHED",
        "rq_count": len(rows),
        "canonical_revision": revision,
        "human_view": view_path,
        "planning_store": PLANNING_PATH,
        "runtime_view": runtime_path,
    }


def assign(root: Path, target: str, values: dict[str, Any]) -> dict[str, Any]:
    root = root.resolve()
    store = TAILOR.load_store(root)
    entity = (store.get("entities") or {}).get(target)
    if not isinstance(entity, dict) or str(entity.get("entity_type") or "").upper() != "RQ":
        raise ValueError(f"RQ target not found: {target}")
    planning = _planning(root)
    rows = planning["requirements"]
    current = rows.get(target) if isinstance(rows.get(target), dict) else {}
    changed: dict[str, str] = {}
    for key in PLANNING_FIELDS:
        if key not in values or values[key] is None:
            continue
        value = str(values[key]).strip()
        current[key] = value
        changed[key] = value
    if not changed:
        raise ValueError("at least one planning field is required")
    current["updated_at"] = now()
    rows[target] = current
    planning["updated_at"] = now()
    _save(root / PLANNING_PATH, planning)
    result = refresh(root)
    return {**result, "status": "RQ_ASSIGNMENT_UPDATED", "target": target, "changed": changed}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Manage PM-owned RQ assignments and render derived project progress list.")
    sub = ap.add_subparsers(dest="command")
    refresh_p = sub.add_parser("refresh")
    refresh_p.add_argument("--root", default=".")
    refresh_p.add_argument("--out", default=VIEW_PATH)
    assign_p = sub.add_parser("assign")
    assign_p.add_argument("--root", default=".")
    assign_p.add_argument("--target", required=True)
    for option in PLANNING_FIELDS:
        assign_p.add_argument("--" + option.replace("_", "-"), dest=option)
    args = ap.parse_args(argv)
    command = args.command or "refresh"
    try:
        if command == "refresh":
            result = refresh(Path(getattr(args, "root", ".")), view_path=getattr(args, "out", VIEW_PATH))
        else:
            values = {key: getattr(args, key) for key in PLANNING_FIELDS}
            result = assign(Path(args.root), args.target, values)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "RQ_WORKLIST_FAILED", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
