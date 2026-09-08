#!/usr/bin/env python3
"""Build an RQ <-> supporting-document review draft immediately after Requirement Intake.

The runtime performs deterministic, evidence-preserving preparation only:
- register supporting files in br-input/manifest.yaml,
- extract PPTX/XLSX/DOCX/PDF/CSV/MD/TXT evidence chunks,
- prefilter likely RQ-document pairs from observable text overlap,
- write a review draft for the interactive Agent/human reviewer.

It never confirms Business Truth and never mutates Canonical entities/relations.
Semantic confirmation belongs to the interactive Agent and human review workflow.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
SUPPORTED = {".pptx", ".xlsx", ".docx", ".pdf", ".csv", ".md", ".txt"}
EVIDENCE_DIR = "sdlc/runtime/intake/reference-evidence"
AGENT_CONTEXT_PATH = "sdlc/runtime/intake/rq-reference-agent-review.json"
REVIEW_MD_PATH = "docs/00_관리/RQ_참고문서_초안검토.md"
STOPWORDS = {
    "요구사항", "요청", "기능", "개선", "시스템", "업무", "관련", "처리", "화면", "자료",
    "the", "and", "for", "with", "from", "this", "that", "requirement", "system", "function",
}


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


EXTRACT = _load("intake_reference_extract", "extract_document_evidence.py")
REGISTRY = _load("intake_reference_registry", "rq_reference_registry.py")
TAILOR = REGISTRY.TAILOR


def _save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def collect_reference_paths(
    root: Path,
    references: list[str] | None = None,
    reference_dirs: list[str] | None = None,
    primary_requirement: Path | None = None,
) -> list[Path]:
    root = root.resolve()
    primary = primary_requirement.resolve() if primary_requirement else None
    found: list[Path] = []
    for raw in references or []:
        path = Path(raw)
        path = path if path.is_absolute() else root / path
        if not path.is_file():
            raise ValueError(f"reference file not found: {path}")
        if path.suffix.lower() not in SUPPORTED:
            raise ValueError(f"unsupported reference format: {path.suffix or '<none>'}: {path}")
        found.append(path.resolve())
    for raw in reference_dirs or []:
        directory = Path(raw)
        directory = directory if directory.is_absolute() else root / directory
        if not directory.is_dir():
            raise ValueError(f"reference directory not found: {directory}")
        for path in sorted(directory.rglob("*")):
            if path.is_file() and path.suffix.lower() in SUPPORTED:
                found.append(path.resolve())
    unique: list[Path] = []
    seen: set[str] = set()
    for path in found:
        if primary and path == primary:
            continue
        key = str(path)
        if key not in seen:
            unique.append(path)
            seen.add(key)
    return unique


def _ensure_project_copy(root: Path, source: Path) -> Path:
    try:
        source.resolve().relative_to(root.resolve())
        return source.resolve()
    except ValueError:
        digest = EXTRACT.sha256(source).split(":", 1)[-1][:8]
        target_dir = root / "br-input/originals"
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / source.name
        if target.exists() and EXTRACT.sha256(target) != EXTRACT.sha256(source):
            target = target_dir / f"{source.stem}-{digest}{source.suffix}"
        if not target.exists():
            shutil.copy2(source, target)
        return target.resolve()


def _yaml(value: Any) -> str:
    return json.dumps(str(value), ensure_ascii=False)


def _ensure_manifest(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.is_file():
        path.write_text(
            "schema_version: 1\npackage:\n  note: Intake supporting documents auto-registered; metadata can be enriched later.\ndocuments:\n",
            encoding="utf-8",
        )
        return
    text = path.read_text(encoding="utf-8")
    if not re.search(r"(?m)^documents:\s*$", text):
        path.write_text(text.rstrip() + "\n\ndocuments:\n", encoding="utf-8")


def _existing_documents(path: Path) -> dict[str, dict[str, str]]:
    if not path.is_file():
        return {}
    try:
        return REGISTRY._manifest_documents(path)
    except ValueError:
        return {}


def _register_document(root: Path, source: Path) -> tuple[str, Path, dict[str, Any]]:
    source = _ensure_project_copy(root, source)
    extracted = EXTRACT.extract(source)
    digest = str(extracted.get("source_hash") or "sha256:unknown").split(":", 1)[-1]
    manifest_path = root / REGISTRY.MANIFEST_PATH
    _ensure_manifest(manifest_path)
    existing = _existing_documents(manifest_path)
    rel = _rel(root, source)
    for doc_id, row in existing.items():
        if str(row.get("path") or "") == rel or str(row.get("source_hash") or "") == extracted.get("source_hash"):
            extracted["document_id"] = doc_id
            return doc_id, source, extracted

    doc_id = f"CUST-AUTO-{digest[:10].upper()}"
    if doc_id in existing and str(existing[doc_id].get("path") or "") != rel:
        doc_id = f"CUST-AUTO-{digest[:16].upper()}"
    block = [
        f"  - document_id: {doc_id}",
        f"    path: {_yaml(rel)}",
        f"    title: {_yaml(source.stem)}",
        "    document_type: SUPPORTING_MATERIAL",
        "    authority: UNKNOWN",
        "    lifecycle_status: CURRENT",
        f"    source_hash: {_yaml(extracted.get('source_hash') or '')}",
        "    locator_hint: extracted chunk locator",
    ]
    with manifest_path.open("a", encoding="utf-8") as fh:
        if manifest_path.stat().st_size and not manifest_path.read_text(encoding="utf-8").endswith("\n"):
            fh.write("\n")
        fh.write("\n".join(block) + "\n")
    extracted["document_id"] = doc_id
    return doc_id, source, extracted


def _flatten_text(value: Any) -> list[str]:
    if isinstance(value, dict):
        rows: list[str] = []
        for child in value.values():
            rows.extend(_flatten_text(child))
        return rows
    if isinstance(value, list):
        rows: list[str] = []
        for child in value:
            rows.extend(_flatten_text(child))
        return rows
    if value in (None, ""):
        return []
    return [str(value)]


def _tokens(text: str) -> set[str]:
    return {
        token.lower()
        for token in re.findall(r"[A-Za-z0-9가-힣_]{2,}", text)
        if token.lower() not in STOPWORDS
    }


def _rq_summary(entity: dict[str, Any]) -> dict[str, Any]:
    fields = entity.get("fields") or {}
    text = "\n".join(_flatten_text(fields))
    title = str(fields.get("name") or fields.get("title") or fields.get("request_summary") or "")
    external = fields.get("external_requirement_ids") or fields.get("external_requirement_id") or []
    if not isinstance(external, list):
        external = [external]
    return {
        "title": title,
        "text": text,
        "tokens": sorted(_tokens(text + "\n" + title)),
        "external_requirement_ids": [str(x) for x in external if str(x).strip()],
    }


def _document_summary(doc_id: str, source: Path, extracted: dict[str, Any]) -> dict[str, Any]:
    chunks = list(extracted.get("evidence_chunks") or [])
    raw = "\n".join(str(row.get("raw_text") or "") for row in chunks)
    locators = [str(row.get("locator") or "") for row in chunks if row.get("locator")]
    return {
        "document_id": doc_id,
        "title": source.stem,
        "path": str(source),
        "format": extracted.get("format"),
        "source_hash": extracted.get("source_hash"),
        "extraction_status": extracted.get("extraction_status"),
        "chunk_count": extracted.get("chunk_count"),
        "text": raw,
        "tokens": sorted(_tokens(source.stem + "\n" + raw)),
        "locators": locators,
    }


def _score(rq: dict[str, Any], doc: dict[str, Any]) -> tuple[int, list[str], list[str]]:
    rq_tokens = set(rq.get("tokens") or [])
    doc_tokens = set(doc.get("tokens") or [])
    overlap = sorted(rq_tokens & doc_tokens)
    score = len(overlap)
    reasons: list[str] = []
    title = str(rq.get("title") or "").strip().lower()
    text = str(doc.get("text") or "").lower()
    if title and len(title) >= 3 and title in text:
        score += 8
        reasons.append("요구사항명이 문서 내용에서 직접 확인됨")
    matched_external = [x for x in rq.get("external_requirement_ids") or [] if str(x).lower() in text]
    if matched_external:
        score += 5 * len(matched_external)
        reasons.append("외부 요구ID가 문서 내용에서 확인됨")
    if overlap:
        reasons.append("공통 핵심어: " + ", ".join(overlap[:8]))
    matched_locators: list[str] = []
    for chunk in doc.get("locators") or []:
        if len(matched_locators) >= 3:
            break
        matched_locators.append(str(chunk))
    return score, reasons, matched_locators


def _render_review(root: Path, registry: dict[str, Any]) -> str:
    lines = [
        "# RQ 참고문서 초안 검토", "",
        "> Requirement Intake 후 생성된 Review Surface다. `제안`은 Business Truth가 아니며 Agent/사람이 실제 첨부문서를 확인해 `확정` 또는 `제외`로 수정한다.",
        "> 행 추가/삭제 및 셀 수정 후 `python sdlc/scripts/harness.py rq-ref import docs/00_관리/RQ_참고문서_초안검토.md`로 반영할 수 있다.",
        "",
        "| " + " | ".join(REGISTRY.COLUMNS) + " |",
        "|" + "|".join("---" for _ in REGISTRY.COLUMNS) + "|",
    ]
    for link in registry.get("links", []) or []:
        if not isinstance(link, dict):
            continue
        row = [
            link.get("rq_id", ""), link.get("document_id", ""), link.get("purpose", ""),
            link.get("locator_hint", ""), "필수" if link.get("required") else "선택",
            link.get("review_status", "확정"), link.get("proposal_reason", ""), link.get("note", ""),
        ]
        lines.append("| " + " | ".join(REGISTRY._esc(value) for value in row) + " |")
    if not any(isinstance(x, dict) for x in registry.get("links", []) or []):
        lines.append("| " + " | ".join(["연결 초안 없음"] + [""] * (len(REGISTRY.COLUMNS) - 1)) + " |")
    return "\n".join(lines) + "\n"


def draft(root: Path, rq_ids: list[str], reference_paths: list[Path]) -> dict[str, Any]:
    root = root.resolve()
    canonical = TAILOR.load_store(root)
    rqs: dict[str, dict[str, Any]] = {}
    for rq_id in rq_ids:
        entity = REGISTRY._assert_rq(canonical, rq_id)
        rqs[rq_id] = _rq_summary(entity)

    documents: dict[str, dict[str, Any]] = {}
    for source in reference_paths:
        doc_id, project_source, extracted = _register_document(root, source)
        evidence_path = root / EVIDENCE_DIR / f"{doc_id}.json"
        _save_json(evidence_path, extracted)
        documents[doc_id] = _document_summary(doc_id, project_source, extracted)
        documents[doc_id]["evidence_file"] = _rel(root, evidence_path)

    registry = REGISTRY._load_store(root / REGISTRY.STORE_PATH)
    links = registry.setdefault("links", [])
    existing = {
        (str(row.get("rq_id") or ""), str(row.get("document_id") or ""))
        for row in links if isinstance(row, dict)
    }
    proposals: list[dict[str, Any]] = []
    unmatched_rq: list[str] = []
    for rq_id, rq_data in rqs.items():
        ranked = []
        for doc_id, doc in documents.items():
            score, reasons, locators = _score(rq_data, doc)
            ranked.append((score, doc_id, reasons, locators))
        ranked.sort(key=lambda row: (-row[0], row[1]))
        selected = []
        if ranked and ranked[0][0] > 0:
            floor = max(1, int(ranked[0][0] * 0.6))
            selected = [row for row in ranked if row[0] >= floor][:3]
        elif len(ranked) == 1:
            score, doc_id, reasons, locators = ranked[0]
            selected = [(score, doc_id, ["동일 Intake 패키지의 유일한 참고문서이므로 검토 후보로 포함"], locators)]
        if not selected:
            unmatched_rq.append(rq_id)
            continue
        for score, doc_id, reasons, locators in selected:
            if (rq_id, doc_id) in existing:
                continue
            proposal = {
                "rq_id": rq_id,
                "document_id": doc_id,
                "purpose": "요구사항과 함께 전달된 참고자료 검토",
                "locator_hint": ", ".join(locators[:3]),
                "required": False,
                "review_status": "제안",
                "origin": "INTAKE_AUTO_DRAFT",
                "proposal_score": score,
                "proposal_reason": "; ".join(reasons) or "내용 기반 연결 후보; Agent 검토 필요",
                "note": "Intake 자동 초안. Agent/사람 검토 전에는 확정 연결로 간주하지 않음.",
                "updated_at": REGISTRY.now(),
            }
            links.append(proposal)
            proposals.append(proposal)
            existing.add((rq_id, doc_id))

    registry["updated_at"] = REGISTRY.now()
    registry["draft_source"] = "REQUIREMENT_INTAKE_SUPPORTING_DOCUMENTS"
    REGISTRY._save(root / REGISTRY.STORE_PATH, registry)
    registry_refresh = REGISTRY.refresh(root)

    review_path = root / REVIEW_MD_PATH
    review_path.parent.mkdir(parents=True, exist_ok=True)
    review_path.write_text(_render_review(root, registry), encoding="utf-8")
    context = {
        "schema_version": 1,
        "status": "AGENT_REFERENCE_REVIEW_REQUIRED",
        "instruction": [
            "각 RQ의 의미와 후보 문서의 실제 Evidence Chunk를 읽는다.",
            "관련성이 확인되면 review_status를 확정으로 바꾸고 purpose/locator_hint를 보정한다.",
            "관련이 없으면 제외로 바꾸거나 행을 제거한다.",
            "판단 근거가 부족하면 제안 상태를 유지하고 사람에게 확인한다.",
            "Registry 검토만으로 Canonical Business Truth를 변경하지 않는다.",
        ],
        "rq": rqs,
        "documents": documents,
        "proposals": proposals,
        "unmatched_rq": unmatched_rq,
        "review_surface": REVIEW_MD_PATH,
        "registry_store": REGISTRY.STORE_PATH,
        "canonical_mutated": False,
    }
    _save_json(root / AGENT_CONTEXT_PATH, context)
    return {
        "status": "RQ_REFERENCE_DRAFT_CREATED",
        "reference_document_count": len(documents),
        "proposal_count": len(proposals),
        "unmatched_rq": unmatched_rq,
        "agent_review_required": True,
        "agent_review_context": AGENT_CONTEXT_PATH,
        "review_surface": REVIEW_MD_PATH,
        "registry": registry_refresh,
        "canonical_mutated": False,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Create an Intake-time RQ/reference-document review draft.")
    ap.add_argument("--root", default=".")
    ap.add_argument("--rq", action="append", required=True)
    ap.add_argument("--reference", action="append", default=[])
    ap.add_argument("--reference-dir", action="append", default=[])
    args = ap.parse_args(argv)
    root = Path(args.root).resolve()
    try:
        paths = collect_reference_paths(root, args.reference, args.reference_dir)
        result = draft(root, list(args.rq), paths)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "RQ_REFERENCE_DRAFT_FAILED", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
