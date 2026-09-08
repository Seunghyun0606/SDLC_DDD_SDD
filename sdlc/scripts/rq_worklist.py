#!/usr/bin/env python3
"""Project RQ planning + derived progress worklist.

Canonical Business Truth is never written by this module. PM planning is an independent,
flexible schema managed through CSV/XLSX or the legacy single-RQ CLI. Runtime status is always
derived from existing check/delivery/projection evidence.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
PLANNING_PATH = ".sdlc/management/rq-planning.json"
VIEW_PATH = "docs/00_관리/RQ_작업목록.md"
RUNTIME_PATH = "sdlc/runtime/management/rq-worklist.json"
DEFAULT_EDITABLE_XLSX = "docs/00_관리/RQ_작업관리.xlsx"

# Backward-compatible convenience fields for CLI users. Spreadsheet users may define any
# non-system PM column; these keys are not a closed planning schema.
PLANNING_FIELDS = [
    "priority", "pm_owner", "business_owner", "engineering_owner", "test_owner",
    "customer_decision_owner", "milestone", "planned_start", "planned_end", "note",
]
LEGACY_LABELS = {
    "priority": "우선순위", "pm_owner": "PM", "business_owner": "업무/BA",
    "engineering_owner": "설계·개발", "test_owner": "테스트",
    "customer_decision_owner": "고객 결정자", "milestone": "마일스톤",
    "planned_start": "계획시작", "planned_end": "계획종료", "note": "비고",
}
LABEL_TO_LEGACY = {v: k for k, v in LEGACY_LABELS.items()}
RQ_ALIASES = {"RQ", "RQ ID", "RQ_ID", "rq_id", "요구사항ID", "요구사항 ID"}
READ_ONLY_CONTEXT = {"요구사항명", "외부 요구ID", "title", "external_requirement_ids"}
DERIVED_LABELS = {
    "현재 상태", "Change Level", "사람 결정 필요", "확보된 검증근거", "산출물 View", "다음 작업",
}
SYSTEM_KEYS = {
    "rq_id", "title", "external_requirement_ids", "working_state", "change_level",
    "human_decision_count", "evidence_passed", "projection_state", "next_action",
    "planning_updated_at", "updated_at",
}
CUSTOM_PREFIX = "custom::"


def _load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


CHECK = _load_module("rq_worklist_human_check", "tailored_check.py")
TAILOR = CHECK.TAILOR
IMPORT = _load_module("rq_worklist_requirement_import", "import_requirements.py")


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
    data = _load_json(root / PLANNING_PATH, {"schema_version": 2, "requirements": {}, "column_order": [], "column_labels": {}})
    version = int(data.get("schema_version") or 0)
    if version not in {1, 2}:
        raise ValueError("unsupported rq planning schema_version")
    rows = data.setdefault("requirements", {})
    if not isinstance(rows, dict):
        raise ValueError("rq planning requirements must be a mapping")
    # Non-destructive in-memory migration from the fixed v1 planning shape.
    if version == 1:
        order = []
        for key in PLANNING_FIELDS:
            if any(isinstance(row, dict) and str(row.get(key) or "") for row in rows.values()):
                order.append(key)
        data["schema_version"] = 2
        data["column_order"] = order
        data["column_labels"] = {key: LEGACY_LABELS[key] for key in order}
    data.setdefault("column_order", [])
    data.setdefault("column_labels", {})
    if not isinstance(data["column_order"], list) or not isinstance(data["column_labels"], dict):
        raise ValueError("rq planning column metadata is invalid")
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


def _pm_value_keys(plan: dict[str, Any]) -> list[str]:
    return [k for k in plan if k not in SYSTEM_KEYS and k != "updated_at"]


def _label_for_key(key: str, planning: dict[str, Any] | None = None, *, view: bool = False) -> str:
    labels = (planning or {}).get("column_labels") or {}
    label = str(labels.get(key) or LEGACY_LABELS.get(key) or (key[len(CUSTOM_PREFIX):] if key.startswith(CUSTOM_PREFIX) else key))
    if view and label in DERIVED_LABELS:
        return f"PM:{label}"
    return label


def _key_for_header(header: str) -> str | None:
    raw = str(header or "").strip()
    if not raw or raw in READ_ONLY_CONTEXT or raw in RQ_ALIASES:
        return None
    if raw in LABEL_TO_LEGACY:
        return LABEL_TO_LEGACY[raw]
    if raw in PLANNING_FIELDS:
        return raw
    return CUSTOM_PREFIX + raw


def build_rows(root: Path) -> tuple[list[dict[str, Any]], int]:
    root = root.resolve()
    store = TAILOR.load_store(root)
    planning_doc = _planning(root)
    planning = planning_doc.get("requirements") or {}
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
        pm_fields = {key: str(plan.get(key) or "") for key in _pm_value_keys(plan)}
        row = {
            "rq_id": rq_id,
            "title": control.get("title") or (entity.get("fields") or {}).get("name") or "",
            "external_requirement_ids": _external_ids(entity),
            **{key: str(plan.get(key) or "") for key in PLANNING_FIELDS},
            **pm_fields,
            "pm_fields": pm_fields,
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


def _pm_columns_from_rows(rows: list[dict[str, Any]]) -> list[str]:
    seen: list[str] = []
    for row in rows:
        for key in (row.get("pm_fields") or {}):
            if key not in seen:
                seen.append(key)
    return seen


def render(rows: list[dict[str, Any]], revision: int, planning: dict[str, Any] | None = None) -> str:
    planning = planning or {"column_order": _pm_columns_from_rows(rows), "column_labels": {}}
    available = set(_pm_columns_from_rows(rows))
    ordered = [str(k) for k in planning.get("column_order", []) if str(k) in available]
    ordered += [k for k in available if k not in ordered]
    columns: list[tuple[str, str]] = [
        ("rq_id", "RQ"), ("title", "요구사항명"), ("external_requirement_ids", "외부 요구ID"),
    ]
    columns += [(key, _label_for_key(key, planning, view=True)) for key in ordered]
    columns += [
        ("working_state", "현재 상태"), ("change_level", "Change Level"),
        ("human_decision_count", "사람 결정 필요"), ("evidence_passed", "확보된 검증근거"),
        ("projection_state", "산출물 View"), ("next_action", "다음 작업"),
    ]
    lines = [
        "# RQ 작업 목록", "",
        "> Canonical RQ + PM 계획정보 + Runtime 상태를 합성한 Generated View다. PM 컬럼은 자유롭게 구성할 수 있지만 요구사항 의미와 Runtime 상태는 이 표에서 수동 확정하지 않는다.",
        "", f"- Canonical Revision: `{revision}`", f"- RQ 수: **{len(rows)}**", f"- 생성시각: `{now()}`", "",
        "## 관리 원칙", "",
        "- PM 편집 권장: `RQ_작업관리.xlsx` 또는 CSV를 Export → 컬럼/값 편집 → Import",
        "- PM 컬럼: RQ 외에는 프로젝트가 자유롭게 추가/삭제 가능하며 Canonical에 반영되지 않는다.",
        "- Runtime 자동 계산: 현재 상태, Change Level, 사람 결정 필요, 검증근거, 산출물 View 상태, 다음 작업",
        "- 요구사항 의미 변경은 `/change`로 처리한다.", "",
        "| " + " | ".join(label for _, label in columns) + " |",
        "|" + "|".join("---" for _ in columns) + "|",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_esc(row.get(key, "")) for key, _ in columns) + " |")
    if not rows:
        lines.append("| " + " | ".join(["인입된 RQ 없음"] + [""] * (len(columns) - 1)) + " |")
    lines += ["", "## PM 편집 파일", "", "```bash",
              "python sdlc/scripts/harness.py rq-list export --format xlsx --output docs/00_관리/RQ_작업관리.xlsx",
              "python sdlc/scripts/harness.py rq-list import docs/00_관리/RQ_작업관리.xlsx",
              "python sdlc/scripts/harness.py check RQ-001", "```", ""]
    return "\n".join(lines)


def refresh(root: Path, *, view_path: str = VIEW_PATH, runtime_path: str = RUNTIME_PATH) -> dict[str, Any]:
    root = root.resolve()
    rows, revision = build_rows(root)
    planning = _planning(root)
    view = root / view_path
    view.parent.mkdir(parents=True, exist_ok=True)
    view.write_text(render(rows, revision, planning), encoding="utf-8")
    machine = root / runtime_path
    payload = {
        "schema_version": 2,
        "generated_at": now(),
        "canonical_revision": revision,
        "rq_count": len(rows),
        "pm_column_order": list(planning.get("column_order") or []),
        "rows": rows,
        "business_truth_authority": False,
        "planning_source": PLANNING_PATH,
        "human_view": view_path,
    }
    _save(machine, payload)
    return {
        "status": "RQ_WORKLIST_REFRESHED", "rq_count": len(rows), "canonical_revision": revision,
        "human_view": view_path, "planning_store": PLANNING_PATH, "runtime_view": runtime_path,
    }


def _assert_rq(store: dict[str, Any], target: str) -> None:
    entity = (store.get("entities") or {}).get(target)
    if not isinstance(entity, dict) or str(entity.get("entity_type") or "").upper() != "RQ":
        raise ValueError(f"RQ target not found: {target}")


def assign(root: Path, target: str, values: dict[str, Any]) -> dict[str, Any]:
    """Backward-compatible one-RQ convenience command."""
    root = root.resolve()
    store = TAILOR.load_store(root)
    _assert_rq(store, target)
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
        if key not in planning["column_order"]:
            planning["column_order"].append(key)
        planning["column_labels"][key] = LEGACY_LABELS[key]
    if not changed:
        raise ValueError("at least one planning field is required")
    current["updated_at"] = now()
    rows[target] = current
    planning["updated_at"] = now()
    _save(root / PLANNING_PATH, planning)
    result = refresh(root)
    return {**result, "status": "RQ_ASSIGNMENT_UPDATED", "target": target, "changed": changed}


def _read_table(path: Path) -> tuple[list[str], list[list[Any]]]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as fh:
            matrix = list(csv.reader(fh))
        if not matrix:
            return [], []
        return [str(x).strip() for x in matrix[0]], matrix[1:]
    if suffix == ".xlsx":
        _sheet, matrix = IMPORT.read_xlsx_matrix(path)
        if not matrix:
            return [], []
        return [str(x).strip() for x in matrix[0]], matrix[1:]
    raise ValueError("PM worklist import supports .csv or .xlsx")


def _rq_column(headers: list[str]) -> int:
    matches = [i for i, h in enumerate(headers) if h in RQ_ALIASES]
    if len(matches) != 1:
        raise ValueError("exactly one RQ identifier column is required (recommended header: RQ)")
    return matches[0]


def import_planning(root: Path, input_path: Path, *, replace_columns: bool = True) -> dict[str, Any]:
    """Import PM spreadsheet atomically. No Canonical write is performed."""
    root = root.resolve()
    headers, raw_rows = _read_table(input_path)
    if not headers:
        raise ValueError("empty PM worklist")
    rq_index = _rq_column(headers)
    store = TAILOR.load_store(root)

    input_columns: list[tuple[int, str, str]] = []
    seen_labels: set[str] = set()
    for i, header in enumerate(headers):
        if i == rq_index or header in READ_ONLY_CONTEXT or not header:
            continue
        if header in seen_labels:
            raise ValueError(f"duplicate PM column: {header}")
        seen_labels.add(header)
        key = _key_for_header(header)
        if key:
            input_columns.append((i, key, header))

    prepared: list[tuple[str, dict[str, str]]] = []
    seen_rq: set[str] = set()
    for row_no, raw in enumerate(raw_rows, 2):
        if not any(str(x).strip() for x in raw):
            continue
        rq_id = str(raw[rq_index] if rq_index < len(raw) else "").strip()
        if not rq_id:
            raise ValueError(f"row {row_no}: RQ is required")
        if rq_id in seen_rq:
            raise ValueError(f"duplicate RQ in PM file: {rq_id}")
        seen_rq.add(rq_id)
        _assert_rq(store, rq_id)
        updates = {key: str(raw[i] if i < len(raw) and raw[i] is not None else "").strip() for i, key, _ in input_columns}
        prepared.append((rq_id, updates))

    planning = _planning(root)
    requirements = planning["requirements"]
    new_keys = [key for _, key, _ in input_columns]
    labels = {key: label for _, key, label in input_columns}

    if replace_columns:
        old_keys = list(planning.get("column_order") or [])
        removed = [key for key in old_keys if key not in new_keys]
        for plan in requirements.values():
            if isinstance(plan, dict):
                for key in removed:
                    plan.pop(key, None)
        planning["column_order"] = list(new_keys)
        planning["column_labels"] = dict(labels)
    else:
        for key in new_keys:
            if key not in planning["column_order"]:
                planning["column_order"].append(key)
            planning["column_labels"][key] = labels[key]

    for rq_id, updates in prepared:
        current = requirements.get(rq_id) if isinstance(requirements.get(rq_id), dict) else {}
        for key, value in updates.items():
            current[key] = value
        current["updated_at"] = now()
        requirements[rq_id] = current
    planning["schema_version"] = 2
    planning["updated_at"] = now()
    _save(root / PLANNING_PATH, planning)
    result = refresh(root)
    return {
        **result, "status": "RQ_PLANNING_IMPORTED", "input": str(input_path),
        "imported_rq_count": len(prepared), "pm_column_count": len(planning["column_order"]),
        "column_mode": "REPLACE" if replace_columns else "MERGE", "canonical_mutated": False,
    }


def _editable_headers_rows(root: Path) -> tuple[list[str], list[list[Any]]]:
    planning = _planning(root)
    rows, _revision = build_rows(root)
    pm_keys = list(planning.get("column_order") or [])
    headers = ["RQ", "요구사항명", "외부 요구ID"] + [_label_for_key(k, planning) for k in pm_keys]
    matrix = []
    for row in rows:
        matrix.append([
            row["rq_id"], row["title"], ", ".join(row.get("external_requirement_ids") or []),
            *[str((row.get("pm_fields") or {}).get(k) or "") for k in pm_keys],
        ])
    return headers, matrix


def _xlsx_col(n: int) -> str:
    out = ""
    while n:
        n, r = divmod(n - 1, 26)
        out = chr(65 + r) + out
    return out


def _xlsx_cell(ref: str, value: Any, header: bool = False) -> str:
    style = ' s="1"' if header else ""
    text = escape(str(value if value is not None else ""))
    return f'<c r="{ref}"{style} t="inlineStr"><is><t>{text}</t></is></c>'


def _write_xlsx(path: Path, headers: list[str], rows: list[list[Any]]) -> None:
    main = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    rel = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    sheet_name = "RQ 작업관리"
    cols = "".join(f'<col min="{i}" max="{i}" width="{min(max(len(h) * 2 + 4, 14), 32)}" customWidth="1"/>' for i, h in enumerate(headers, 1))
    xml_rows = ['<row r="1" ht="24" customHeight="1">' + "".join(_xlsx_cell(f"{_xlsx_col(i)}1", h, True) for i, h in enumerate(headers, 1)) + "</row>"]
    for rno, row in enumerate(rows, 2):
        xml_rows.append(f'<row r="{rno}">' + "".join(_xlsx_cell(f"{_xlsx_col(i)}{rno}", row[i - 1] if i - 1 < len(row) else "") for i in range(1, len(headers) + 1)) + "</row>")
    sheet = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="{main}"><sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews><cols>{cols}</cols><sheetData>{''.join(xml_rows)}</sheetData><autoFilter ref="A1:{_xlsx_col(len(headers))}{max(1, len(rows)+1)}"/></worksheet>'''
    content = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/></Types>'''
    rootrel = '''<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>'''
    workbook = f'''<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="{main}" xmlns:r="{rel}"><sheets><sheet name="{sheet_name}" sheetId="1" r:id="rId1"/></sheets></workbook>'''
    wbrels = '''<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>'''
    styles = f'''<?xml version="1.0" encoding="UTF-8"?><styleSheet xmlns="{main}"><fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="11"/><name val="Calibri"/></font></fonts><fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills><borders count="1"><border/></borders><cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs><cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/><xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"><alignment horizontal="center" vertical="center" wrapText="1"/></xf></cellXfs></styleSheet>'''
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, value in {"[Content_Types].xml": content, "_rels/.rels": rootrel, "xl/workbook.xml": workbook, "xl/_rels/workbook.xml.rels": wbrels, "xl/styles.xml": styles, "xl/worksheets/sheet1.xml": sheet}.items():
            zf.writestr(name, value)


def export_planning(root: Path, output: Path, fmt: str | None = None) -> dict[str, Any]:
    root = root.resolve()
    output = output if output.is_absolute() else root / output
    fmt = str(fmt or output.suffix.lstrip(".") or "xlsx").lower()
    if fmt not in {"xlsx", "csv"}:
        raise ValueError("export format must be xlsx or csv")
    headers, rows = _editable_headers_rows(root)
    output.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "csv":
        with output.open("w", encoding="utf-8-sig", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(headers)
            writer.writerows(rows)
    else:
        _write_xlsx(output, headers, rows)
    return {
        "status": "RQ_PLANNING_EXPORTED", "output": str(output.relative_to(root) if output.is_relative_to(root) else output),
        "format": fmt.upper(), "rq_count": len(rows), "pm_column_count": max(0, len(headers) - 3),
        "editable_columns": headers, "canonical_mutated": False,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Manage PM-owned RQ planning and render derived project progress list.")
    sub = ap.add_subparsers(dest="command")
    refresh_p = sub.add_parser("refresh")
    refresh_p.add_argument("--root", default=".")
    refresh_p.add_argument("--out", default=VIEW_PATH)
    assign_p = sub.add_parser("assign")
    assign_p.add_argument("--root", default=".")
    assign_p.add_argument("--target", required=True)
    for option in PLANNING_FIELDS:
        assign_p.add_argument("--" + option.replace("_", "-"), dest=option)
    import_p = sub.add_parser("import")
    import_p.add_argument("input")
    import_p.add_argument("--root", default=".")
    import_p.add_argument("--merge-columns", action="store_true", help="Preserve PM columns not present in the imported file")
    export_p = sub.add_parser("export")
    export_p.add_argument("--root", default=".")
    export_p.add_argument("--format", choices=["xlsx", "csv"], default="xlsx")
    export_p.add_argument("--output", default=DEFAULT_EDITABLE_XLSX)
    args = ap.parse_args(argv)
    command = args.command or "refresh"
    try:
        if command == "refresh":
            result = refresh(Path(getattr(args, "root", ".")), view_path=getattr(args, "out", VIEW_PATH))
        elif command == "assign":
            values = {key: getattr(args, key) for key in PLANNING_FIELDS}
            result = assign(Path(args.root), args.target, values)
        elif command == "import":
            result = import_planning(Path(args.root), Path(args.input), replace_columns=not args.merge_columns)
        else:
            result = export_planning(Path(args.root), Path(args.output), args.format)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
        print(json.dumps({"status": "RQ_WORKLIST_FAILED", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())