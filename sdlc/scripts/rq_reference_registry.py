#!/usr/bin/env python3
"""Many-to-many RQ <-> reference-document planning registry.

The registry tells people and Agents which source documents should be consulted for an RQ. It is
not Business Truth. Only evidence actually inspected during /work becomes Canonical Provenance.
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
COLUMNS = ["RQ", "문서ID", "사용목적", "참고위치", "필수여부", "비고"]


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
        rows.append({
            "rq_id": rq_id,
            "rq_title": _title(entity),
            "document_id": doc_id,
            "document_title": doc.get("title", ""),
            "document_path": doc.get("path", ""),
            "purpose": str(link.get("purpose") or ""),
            "locator_hint": str(link.get("locator_hint") or doc.get("locator_hint") or ""),
            "required": bool(link.get("required")),
            "evidence_state": "근거 사용 확인" if _evidence_used(entity, doc_id, doc) else "참고 예정",
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
        ("locator_hint", "참고위치"), ("required", "필수여부"), ("evidence_state", "Evidence 상태"),
        ("note", "비고"),
    ]
    lines = [
        "# RQ 참고문서 연결 목록", "",
        "> RQ가 분석될 때 참고해야 할 원본 문서를 미리 연결한 Management View다. 연결만으로 Business Truth가 되지 않으며, 실제 `/work`에서 조사된 내용만 Evidence/Provenance가 된다.",
        "", f"- Canonical Revision: `{revision}`", f"- 연결 수: **{len(rows)}**", f"- 생성시각: `{now()}`", "",
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
    _save(root / RUNTIME_PATH, {
        "schema_version": 1, "generated_at": now(), "canonical_revision": revision,
        "link_count": len(rows), "rows": rows, "planning_source": STORE_PATH,
        "document_manifest": MANIFEST_PATH, "business_truth_authority": False,
        "actual_evidence_authority": "CANONICAL_PROVENANCE",
    })
    return {"status": "RQ_REFERENCE_REGISTRY_REFRESHED", "link_count": len(rows), "human_view": VIEW_PATH, "planning_store": STORE_PATH, "canonical_mutated": False}


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
    current.update({"purpose": purpose, "locator_hint": locator_hint, "required": bool(required), "note": note, "updated_at": now()})
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


def _read_rows(path: Path) -> list[dict[str, str]]:
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
        str(x.get("locator_hint") or ""), "필수" if x.get("required") else "선택", str(x.get("note") or ""),
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