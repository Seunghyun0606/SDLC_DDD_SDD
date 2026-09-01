#!/usr/bin/env python3
"""Raw customer-document -> Evidence Chunk adapter.

Supported without third-party dependencies: TXT/MD/CSV, DOCX, PPTX, XLSX (OOXML XML).
PDF uses pypdf or PyPDF2 when installed; otherwise it fails closed as TOOL_REQUIRED rather
than pretending that an unread PDF contains no business rule. Image OCR is intentionally
not implemented here.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

NS_A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
NS_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
NS_S = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
NS_R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def _chunk(document_id: str, source_hash: str, locator: str, raw_text: str, *,
           kind: str, method: str, status: str = "EXTRACTED", structured: Any = None,
           format_context: Any = None, parent_locator: str | None = None, sequence: int | None = None,
           confidence: str = "HIGH") -> dict[str, Any]:
    row = {
        "document_id": document_id,
        "locator": locator,
        "raw_text": raw_text,
        "source_hash": source_hash,
        "extraction_status": status,
        "extraction_method": method,
        "content_kind": kind,
        "confidence": confidence,
    }
    if structured is not None:
        row["structured_content"] = structured
    if format_context is not None:
        row["format_context"] = format_context
    if parent_locator:
        row["parent_locator"] = parent_locator
    if sequence is not None:
        row["sequence"] = sequence
    return row


def extract_text(path: Path, document_id: str, source_hash: str) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    chunks = []
    for idx, paragraph in enumerate(re.split(r"\n\s*\n", text), start=1):
        raw = paragraph.strip()
        if raw:
            kind = "HEADING" if raw.startswith("#") else "PARAGRAPH"
            chunks.append(_chunk(document_id, source_hash, f"paragraph {idx}", raw, kind=kind, method="UTF8_TEXT", sequence=idx))
    return chunks


def extract_csv(path: Path, document_id: str, source_hash: str) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    rows = list(csv.reader(io.StringIO(text)))
    chunks = []
    if rows:
        chunks.append(_chunk(
            document_id, source_hash, "table 1", "\n".join(" | ".join(row) for row in rows),
            kind="TABLE", method="CSV_READER", structured={"headers": rows[0], "rows": rows[1:]},
            format_context={"delimiter": ","}, sequence=1,
        ))
    return chunks


def _xml_text(node: ET.Element, tag_suffix: str = "t") -> str:
    return "".join((el.text or "") for el in node.iter() if el.tag.endswith("}" + tag_suffix) or el.tag == tag_suffix).strip()


def extract_docx(path: Path, document_id: str, source_hash: str) -> list[dict[str, Any]]:
    chunks = []
    with zipfile.ZipFile(path) as zf:
        root = ET.fromstring(zf.read("word/document.xml"))
        body = root.find(f"{NS_W}body")
        if body is None:
            return chunks
        seq = 0
        table_index = 0
        for child in list(body):
            if child.tag == f"{NS_W}p":
                text = _xml_text(child)
                if text:
                    seq += 1
                    chunks.append(_chunk(document_id, source_hash, f"paragraph {seq}", text, kind="PARAGRAPH", method="DOCX_OOXML", sequence=seq))
            elif child.tag == f"{NS_W}tbl":
                table_index += 1
                rows = []
                for tr in child.findall(f"{NS_W}tr"):
                    rows.append([_xml_text(tc) for tc in tr.findall(f"{NS_W}tc")])
                seq += 1
                raw = "\n".join(" | ".join(row) for row in rows)
                chunks.append(_chunk(document_id, source_hash, f"table {table_index}", raw, kind="TABLE", method="DOCX_OOXML", structured={"rows": rows}, format_context={"table_index": table_index}, sequence=seq))
    return chunks


def _pptx_slide_number(name: str) -> int:
    m = re.search(r"slide(\d+)\.xml$", name)
    return int(m.group(1)) if m else 0


def extract_pptx(path: Path, document_id: str, source_hash: str) -> list[dict[str, Any]]:
    chunks = []
    with zipfile.ZipFile(path) as zf:
        slide_names = sorted((n for n in zf.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n)), key=_pptx_slide_number)
        for seq, name in enumerate(slide_names, start=1):
            slide = _pptx_slide_number(name)
            root = ET.fromstring(zf.read(name))
            texts = [(el.text or "").strip() for el in root.iter(f"{NS_A}t") if (el.text or "").strip()]
            raw = "\n".join(texts)
            if not raw:
                continue
            chunks.append(_chunk(
                document_id, source_hash, f"slide {slide}", raw, kind="SLIDE", method="PPTX_OOXML",
                structured={"slide": slide, "text_runs": texts}, format_context={"slide": slide}, sequence=seq,
            ))
    return chunks


def _xlsx_shared_strings(zf: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []
    root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    return [_xml_text(si) for si in root.findall(f"{NS_S}si")]


def _xlsx_sheet_names(zf: zipfile.ZipFile) -> dict[str, str]:
    workbook = ET.fromstring(zf.read("xl/workbook.xml"))
    rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    relmap = {r.attrib.get("Id"): r.attrib.get("Target") for r in rels}
    result = {}
    for sheet in workbook.findall(f".//{NS_S}sheet"):
        name = sheet.attrib.get("name", "Sheet")
        rid = sheet.attrib.get(f"{NS_R}id")
        target = relmap.get(rid)
        if target:
            target = target.lstrip("/")
            result[name] = target if target.startswith("xl/") else "xl/" + target
    return result


def extract_xlsx(path: Path, document_id: str, source_hash: str) -> list[dict[str, Any]]:
    chunks = []
    with zipfile.ZipFile(path) as zf:
        shared = _xlsx_shared_strings(zf)
        sheets = _xlsx_sheet_names(zf)
        seq = 0
        for sheet_name, xml_name in sheets.items():
            if xml_name not in zf.namelist():
                continue
            root = ET.fromstring(zf.read(xml_name))
            rows = []
            min_cell = None
            max_cell = None
            for row in root.findall(f".//{NS_S}row"):
                values = []
                for cell in row.findall(f"{NS_S}c"):
                    ref = cell.attrib.get("r")
                    min_cell = min_cell or ref
                    max_cell = ref or max_cell
                    value_node = cell.find(f"{NS_S}v")
                    inline = cell.find(f"{NS_S}is")
                    raw = value_node.text if value_node is not None else _xml_text(inline) if inline is not None else ""
                    if cell.attrib.get("t") == "s" and raw:
                        try:
                            raw = shared[int(raw)]
                        except (ValueError, IndexError):
                            pass
                    values.append(raw or "")
                if values:
                    rows.append(values)
            if rows:
                seq += 1
                locator = f"{sheet_name}!{min_cell or 'A1'}:{max_cell or 'A1'}"
                chunks.append(_chunk(
                    document_id, source_hash, locator, "\n".join(" | ".join(row) for row in rows),
                    kind="CELL_RANGE", method="XLSX_OOXML",
                    structured={"sheet": sheet_name, "range": locator.split("!", 1)[1], "headers": rows[0], "rows": rows[1:]},
                    format_context={"sheet": sheet_name}, sequence=seq,
                ))
    return chunks


def extract_pdf(path: Path, document_id: str, source_hash: str) -> tuple[list[dict[str, Any]], str, list[str]]:
    reader_cls = None
    method = None
    try:
        from pypdf import PdfReader  # type: ignore
        reader_cls, method = PdfReader, "PYPDF"
    except Exception:
        try:
            from PyPDF2 import PdfReader  # type: ignore
            reader_cls, method = PdfReader, "PYPDF2"
        except Exception:
            return [], "EXTRACTION_REQUIRED", ["PDF text parser dependency(pypdf/PyPDF2) 또는 외부 Document Tool이 필요함"]
    chunks = []
    reader = reader_cls(str(path))
    for index, page in enumerate(reader.pages, start=1):
        try:
            text = (page.extract_text() or "").strip()
        except Exception:
            text = ""
        if text:
            chunks.append(_chunk(document_id, source_hash, f"page {index}", text, kind="PARAGRAPH", method=method, sequence=index, confidence="MEDIUM"))
    status = "EXTRACTED" if chunks else "EXTRACTION_REQUIRED"
    notes = [] if chunks else ["PDF에 추출 가능한 text layer가 없거나 parser가 내용을 읽지 못함; OCR/Document AI 필요"]
    return chunks, status, notes


def extract(path: Path, document_id: str | None = None) -> dict[str, Any]:
    path = path.resolve()
    if not path.is_file():
        raise ValueError(f"file not found: {path}")
    document_id = document_id or path.stem
    source_hash = sha256(path)
    suffix = path.suffix.lower()
    notes: list[str] = []
    if suffix in {".txt", ".md"}:
        chunks, status = extract_text(path, document_id, source_hash), "EXTRACTED"
    elif suffix == ".csv":
        chunks, status = extract_csv(path, document_id, source_hash), "EXTRACTED"
    elif suffix == ".docx":
        chunks, status = extract_docx(path, document_id, source_hash), "EXTRACTED"
    elif suffix == ".pptx":
        chunks, status = extract_pptx(path, document_id, source_hash), "EXTRACTED"
    elif suffix == ".xlsx":
        chunks, status = extract_xlsx(path, document_id, source_hash), "EXTRACTED"
    elif suffix == ".pdf":
        chunks, status, notes = extract_pdf(path, document_id, source_hash)
    else:
        chunks, status = [], "UNSUPPORTED"
        notes.append(f"unsupported format: {suffix or '<none>'}")
    if not chunks and status == "EXTRACTED":
        status = "PARTIAL"
        notes.append("파일은 열었지만 의미 있는 Evidence Chunk를 만들지 못함")
    return {
        "schema_version": 1,
        "document_id": document_id,
        "source_file": str(path),
        "source_hash": source_hash,
        "format": suffix.lstrip(".").upper(),
        "extraction_status": status,
        "chunk_count": len(chunks),
        "evidence_chunks": chunks,
        "notes": notes,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Extract raw customer documents into br-document Evidence Chunks.")
    ap.add_argument("--input", required=True)
    ap.add_argument("--document-id")
    ap.add_argument("--output", required=True)
    args = ap.parse_args(argv)
    try:
        result = extract(Path(args.input), args.document_id)
    except (OSError, ValueError, zipfile.BadZipFile, ET.ParseError) as exc:
        result = {"schema_version": 1, "extraction_status": "FAILED", "error": str(exc), "evidence_chunks": []}
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result.get("extraction_status"), "chunk_count": len(result.get("evidence_chunks", [])), "output": str(out)}, ensure_ascii=False))
    return 0 if result.get("extraction_status") in {"EXTRACTED", "PARTIAL"} else 4


if __name__ == "__main__":
    raise SystemExit(main())
