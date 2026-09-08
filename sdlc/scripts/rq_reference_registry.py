#!/usr/bin/env python3
"""Many-to-many RQ <-> reference-document planning registry.

The registry tells people and Agents which source documents should be consulted for an RQ. It is
not Business Truth. Intake-time auto proposals remain review drafts until Agent/human review.
Only evidence actually inspected during /work becomes Canonical Provenance.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
STORE_PATH = ".sdlc/management/rq-references.json"
RUNTIME_PATH = "sdlc/runtime/management/rq-reference-registry.json"
VIEW_PATH = "docs/00_관리/RQ_참고문서_연결목록.md"
MANIFEST_PATH = "br-input/manifest.yaml"
DEFAULT_EDITABLE_XLSX = "docs/00_관리/RQ_참고문서_연결관리.xlsx"
COLUMNS = ["RQ", "문서ID", "사용목적", "참고위치", "필수여부", "검토상태", "제안이유", "비고"]
REVIEW_STATES = {"제안", "확정", "제외"}


def _load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


RQW = _load_module("rq_reference_worklist", "rq_worklist.py")
TAILOR = RQW.TAILOR


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _strip_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _manifest_documents(path: Path) -> dict[str, dict[str, str]]:
    """Parse the standard br-input manifest document list without third-party YAML."""
    if not path.is_file():
        raise ValueError(f"reference manifest not found: {path}")
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        rows = data.get("documents") or []
        if not isinstance(rows, list):
            raise ValueError("manifest documents must be a list")
        result = {}
        for row in rows:
            if isinstance(row, dict) and row.get("document_id"):
                result[str(row["document_id"])] = {str(k): str(v) for k, v in row.items() if v is not None}
        return result

    result: dict[str, dict[str, str]] = {}
    in_documents = False
    current: dict[str, str] | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        text = line.strip()
        if text == "documents:":
            in_documents = True
            continue
        if not in_documents:
            continue
        if indent == 0 and text != "documents:":
            break
        if text.startswith("- "):
            if current and current.get("document_id"):
                result[current["document_id"]] = current
            current = {}
            text = text[2:].strip()
            if text and ":" in text:
                key, value = text.split(":", 1)
                current[key.strip()] = _strip_scalar(value)
            continue
        if current is not None and ":" in text:
            key, value = text.split(":", 1)
            current[key.strip()] = _strip_scalar(value)
    if current and current.get("document_id"):
        result[current["document_id"]] = current
    if not result:
        raise ValueError("manifest has no document_id entries")
    return result


def _load_store(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"schema_version": 1, "links": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or int(data.get("schema_version") or 0) != 1:
        raise ValueError("unsupported rq reference registry schema")
    if not isinstance(data.get("links", []), list):
        raise ValueError("rq reference links must be a list")
    return data


def _save(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _assert_rq(canonical: dict[str, Any], rq_id: str) -> dict[str, Any]:
    entity = (canonical.get("entities") or {}).get(rq_id)
    if not isinstance(entity, dict) or str(entity.get("entity_type") or "").upper() != "RQ":
        raise ValueError(f"RQ target not found: {rq_id}")
    return entity


def _truthy(value: Any) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "필수", "예"}


def _review_state(value: Any, default: str = "확정") -> str:
    raw = str(value or "").strip()
    aliases = {
        "PROPOSED": "제안", "DRAFT": "제안", "제안": "제안",
        "CONFIRMED": "확정", "APPROVED": "확정", "확정": "확정",
        "EXCLUDED": "제외", "REJECTED": "제외", "제외": "제외",
    }
    state = aliases.get(raw.upper(), aliases.get(raw, default))
    if state not in REVIEW_STATES:
        raise ValueError(f"unsupported review status: {raw}")
    return state


def _evidence_used(entity: dict[str, Any], document_id: str, doc: dict[str, str]) -> bool:
    needles = {document_id.lower()}
    for key in ("path", "title"):
        if doc.get(key):
            needles.add(str(doc[key]).lower())
            needles.add(Path(str(doc[key])).name.lower())
    for prov in entity.get("provenance", []) or []:
        text = json.dumps(prov, ensure_ascii=False).lower()
        if any(needle and needle in text for needle in needles):
            return True
    return False


def _title(entity: dict[str, Any]) -> str:
    fields = entity.get("fields") or {}
    return str(fields.get("name") or fields.get("title") or fields.get("request_summary") or "")


def build_rows(root: Path) -> tuple[list[dict[str, Any]], int]:
    root = root.resolve()
    canonical = TAILOR.load_store(root)
    docs = _manifest_documents(root / MANIFEST_PATH)
    registry = _load_store(root / STORE_PATH)
    rows = []
    for link in registry.get("links", []):
        if not isinstance(link, dict):
            continue
        rq_id = str(link.get("rq_id") or "")
        doc_id = str(link.get("document_id") or "")
        entity = (canonical.get("entities") or {}).get(rq_id) or {}
        doc = docs.get(doc_id) or {}
        review_status = _review_state(link.get("review_status"), "확정")
        evidence_state = "연결 제외" if review_status == "제외" else ("근거 사용 확인" if _evidence_used(entity, doc_id, doc) else "참고 예정")
        rows.append({
            "rq_id": rq_id,
            "rq_title": _title(entity),
            "document_id": doc_id,
            "document_title": doc.get("title", ""),
            "document_path": doc.get("path", ""),
            "purpose": str(link.get("purpose") or ""),
            "locator_hint": str(link.get("locator_hint") or doc.get("locator_hint") or ""),
            "required": bool(link.get("required")),
            "review_status": review_status,
            "proposal_reason": str(link.get("proposal_reason") or ""),
            "origin": str(link.get("origin") or ""),
            "evidence_state": evidence_state,
            "note": str(link.get("note") or ""),
            "updated_at": str(link.get("updated_at") or ""),
        })
    rows.sort(key=lambda row: (row["rq_id"], row["document_id"]))
    return rows, int(canonical.get("revision") or 0)


def _esc(value: Any) -> str:
    if isinstance(value, bool):
        value = "필수" if value else "선택"
    return str(value if value is not None else "").replace("|", "\\|").replace("\n", "<br>")


def render(rows: list[dict[str, Any]], revision: int) -> str:
    columns = [
        ("rq_id", "RQ"), ("rq_title", "요구사항명"), ("document_id", "문서ID"),
        ("document_title", "문서명"), ("document_path", "원본경로"), ("purpose", "사용목적"),
        ("locator_hint", "참고위치"), ("required", "필수여부"), ("review_status", "검토상태"),
        ("proposal_reason", "제안이유"), ("evidence_state", "Evidence 상태"), ("note", "비고"),
    ]
    lines = [
        "# RQ 참고문서 연결 목록", "",
        "> RQ 분석 시 참고할 원본 문서의 Management View다. Intake 자동 연결은 `제안` 상태로 시작하며 Agent/사람 검토 전에는 확정 연결이나 Business Truth로 간주하지 않는다.",
        "", f"- Canonical Revision: `{revision}`", f"- 행 수: **{len(rows)}**", f"- 생성시각: `{now()}`", "",
        "| " + " | ".join(label for _, label in columns) + " |",
        "|" + "|".join("---" for _ in columns) + "|",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_esc(row.get(key, "")) for key, _ in columns) + " |")
    if not rows:
        lines.append("| " + " | ".join(["연결 없음"] + [""] * (len(columns) - 1)) + " |")
    return "\n".join(lines) + "\n"


def refresh(root: Path) -> dict[str, Any]:
    root = root.resolve()
    rows, revision = build_rows(root)
    view = root / VIEW_PATH
    view.parent.mkdir(parents=True, exist_ok=True)
    view.write_text(render(rows, revision), encoding="utf-8")
    active = [row for row in rows if row.get("review_status") != "제외"]
    proposed = [row for row in rows if row.get("review_status") == "제안"]
    confirmed = [row for row in rows if row.get("review_status") == "확정"]
    _save(root / RUNTIME_PATH, {
        "schema_version": 2, "generated_at": now(), "canonical_revision": revision,
        "row_count": len(rows), "active_link_count": len(active), "proposed_count": len(proposed),
        "confirmed_count": len(confirmed), "rows": rows, "planning_source": STORE_PATH,
        "document_manifest": MANIFEST_PATH, "business_truth_authority": False,
        "actual_evidence_authority": "CANONICAL_PROVENANCE",
    })
    return {
        "status": "RQ_REFERENCE_REGISTRY_REFRESHED", "link_count": len(active), "proposed_count": len(proposed),
        "confirmed_count": len(confirmed), "human_view": VIEW_PATH, "planning_store": STORE_PATH,
        "canonical_mutated": False,
    }


def link(root: Path, rq_id: str, document_id: str, *, purpose: str = "", locator_hint: str = "", required: bool = False, note: str = "") -> dict[str, Any]:
    root = root.resolve()
    canonical = TAILOR.load_store(root)
    _assert_rq(canonical, rq_id)
    docs = _manifest_documents(root / MANIFEST_PATH)
    if document_id not in docs:
        raise ValueError(f"document_id not found in {MANIFEST_PATH}: {document_id}")
    registry = _load_store(root / STORE_PATH)
    links = registry.setdefault("links", [])
    current = next((x for x in links if isinstance(x, dict) and x.get("rq_id") == rq_id and x.get("document_id") == document_id), None)
    if current is None:
        current = {"rq_id": rq_id, "document_id": document_id}
        links.append(current)
    current.update({
        "purpose": purpose, "locator_hint": locator_hint, "required": bool(required), "note": note,
        "review_status": "확정", "origin": "MANUAL_OR_AGENT_LINK", "updated_at": now(),
    })
    registry["updated_at"] = now()
    _save(root / STORE_PATH, registry)
    result = refresh(root)
    return {**result, "status": "RQ_REFERENCE_LINKED", "rq_id": rq_id, "document_id": document_id}


def unlink(root: Path, rq_id: str, document_id: str) -> dict[str, Any]:
    root = root.resolve()
    registry = _load_store(root / STORE_PATH)
    before = len(registry.get("links", []))
    registry["links"] = [x for x in registry.get("links", []) if not (isinstance(x, dict) and x.get("rq_id") == rq_id and x.get("document_id") == document_id)]
    if len(registry["links"]) == before:
        raise ValueError(f"RQ reference link not found: {rq_id} -> {document_id}")
    registry["updated_at"] = now()
    _save(root / STORE_PATH, registry)
    result = refresh(root)
    return {**result, "status": "RQ_REFERENCE_UNLINKED", "rq_id": rq_id, "document_id": document_id}


def _md_cells(line: str) -> list[str]:
    text = line.strip().strip("|")
    cells: list[str] = []
    buf: list[str] = []
    escaped = False
    for char in text:
        if escaped:
            buf.append(char); escaped = False
        elif char == "\\":
            escaped = True
        elif char == "|":
            cells.append("".join(buf).strip()); buf = []
        else:
            buf.append(char)
    cells.append("".join(buf).strip())
    return [cell.replace("<br>", "\n") for cell in cells]


def _read_markdown_table(path: Path) -> tuple[list[str], list[list[str]]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    header_at = None
    headers: list[str] = []
    for index, line in enumerate(lines[:-1]):
        if not line.lstrip().startswith("|"):
            continue
        candidate = _md_cells(line)
        if "RQ" not in candidate or "문서ID" not in candidate:
            continue
        separators = _md_cells(lines[index + 1]) if lines[index + 1].lstrip().startswith("|") else []
        if separators and all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in separators):
            header_at, headers = index, candidate
            break
    if header_at is None:
        raise ValueError("reference Markdown table not found")
    matrix: list[list[str]] = []
    for line in lines[header_at + 2:]:
        if not line.lstrip().startswith("|"):
            if matrix:
                break
            continue
        row = _md_cells(line)
        if any(cell.strip() for cell in row):
            matrix.append(row)
    return headers, matrix


def _read_rows(path: Path) -> list[dict[str, str]]:
    if path.suffix.lower() == ".md":
        headers, matrix = _read_markdown_table(path)
    else:
        headers, matrix = RQW._read_table(path)
    missing = [h for h in ["RQ", "문서ID"] if h not in headers]
    if missing:
        raise ValueError(f"reference file missing column(s): {', '.join(missing)}")
    unknown = [h for h in headers if h and h not in COLUMNS]
    if unknown:
        raise ValueError(f"unsupported reference column(s): {', '.join(unknown)}")
    result = []
    for row in matrix:
        if not any(str(x).strip() for x in row):
            continue
        first = str(row[0] if row else "").strip()
        if first in {"연결 초안 없음", "연결 없음"}:
            continue
        result.append({h: str(row[i] if i < len(row) else "").strip() for i, h in enumerate(headers) if h})
    return result


def import_registry(root: Path, input_path: Path) -> dict[str, Any]:
    root = root.resolve()
    input_path = input_path if input_path.is_absolute() else root / input_path
    incoming = _read_rows(input_path)
    canonical = TAILOR.load_store(root)
    docs = _manifest_documents(root / MANIFEST_PATH)
    prepared = []
    seen = set()
    for idx, row in enumerate(incoming, 2):
        rq_id, doc_id = row.get("RQ", ""), row.get("문서ID", "")
        if not rq_id or not doc_id:
            raise ValueError(f"row {idx}: RQ and 문서ID are required")
        _assert_rq(canonical, rq_id)
        if doc_id not in docs:
            raise ValueError(f"row {idx}: document_id not found in manifest: {doc_id}")
        key = (rq_id, doc_id)
        if key in seen:
            raise ValueError(f"duplicate reference link: {rq_id} -> {doc_id}")
        seen.add(key)
        prepared.append({
            "rq_id": rq_id, "document_id": doc_id, "purpose": row.get("사용목적", ""),
            "locator_hint": row.get("참고위치", ""), "required": _truthy(row.get("필수여부")),
            "review_status": _review_state(row.get("검토상태"), "확정"),
            "proposal_reason": row.get("제안이유", ""), "origin": "REVIEW_IMPORT",
            "note": row.get("비고", ""), "updated_at": now(),
        })
    _save(root / STORE_PATH, {"schema_version": 1, "updated_at": now(), "links": prepared})
    result = refresh(root)
    return {**result, "status": "RQ_REFERENCE_REGISTRY_IMPORTED", "imported_link_count": len(prepared), "canonical_mutated": False}


def export_registry(root: Path, output: Path, fmt: str = "xlsx") -> dict[str, Any]:
    root = root.resolve()
    output = output if output.is_absolute() else root / output
    registry = _load_store(root / STORE_PATH)
    matrix = [[
        str(x.get("rq_id") or ""), str(x.get("document_id") or ""), str(x.get("purpose") or ""),
        str(x.get("locator_hint") or ""), "필수" if x.get("required") else "선택",
        _review_state(x.get("review_status"), "확정"), str(x.get("proposal_reason") or ""), str(x.get("note") or ""),
    ] for x in registry.get("links", []) if isinstance(x, dict)]
    output.parent.mkdir(parents=True, exist_ok=True)
    fmt = fmt.lower()
    if fmt == "csv":
        with output.open("w", encoding="utf-8-sig", newline="") as fh:
            writer = csv.writer(fh); writer.writerow(COLUMNS); writer.writerows(matrix)
    elif fmt == "xlsx":
        RQW._write_xlsx(output, COLUMNS, matrix)
    else:
        raise ValueError("export format must be xlsx or csv")
    return {"status": "RQ_REFERENCE_REGISTRY_EXPORTED", "output": str(output.relative_to(root) if output.is_relative_to(root) else output), "format": fmt.upper(), "link_count": len(matrix), "canonical_mutated": False}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Manage RQ-to-reference-document planning links.")
    sub = ap.add_subparsers(dest="command")
    p = sub.add_parser("refresh"); p.add_argument("--root", default=".")
    p = sub.add_parser("link"); p.add_argument("--root", default="."); p.add_argument("--target", required=True); p.add_argument("--document-id", required=True); p.add_argument("--purpose", default=""); p.add_argument("--locator-hint", default=""); p.add_argument("--required", action="store_true"); p.add_argument("--note", default="")
    p = sub.add_parser("unlink"); p.add_argument("--root", default="."); p.add_argument("--target", required=True); p.add_argument("--document-id", required=True)
    p = sub.add_parser("import"); p.add_argument("input"); p.add_argument("--root", default=".")
    p = sub.add_parser("export"); p.add_argument("--root", default="."); p.add_argument("--format", choices=["xlsx", "csv"], default="xlsx"); p.add_argument("--output", default=DEFAULT_EDITABLE_XLSX)
    args = ap.parse_args(argv)
    command = args.command or "refresh"
    try:
        if command == "refresh": result = refresh(Path(getattr(args, "root", ".")))
        elif command == "link": result = link(Path(args.root), args.target, args.document_id, purpose=args.purpose, locator_hint=args.locator_hint, required=args.required, note=args.note)
        elif command == "unlink": result = unlink(Path(args.root), args.target, args.document_id)
        elif command == "import": result = import_registry(Path(args.root), Path(args.input))
        else: result = export_registry(Path(args.root), Path(args.output), args.format)
        print(json.dumps(result, ensure_ascii=False, indent=2)); return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "RQ_REFERENCE_REGISTRY_FAILED", "error": str(exc)}, ensure_ascii=False, indent=2)); return 2


if __name__ == "__main__":
    raise SystemExit(main())
