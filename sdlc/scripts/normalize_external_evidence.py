#!/usr/bin/env python3
"""Normalize external Tool/MCP exports into the existing Evidence Chunk shape.

This avoids creating a new Template/Stage/Canonical entity for every Jira/APM/DB/API tool.
Input is provider-owned JSON; output is provider-neutral Evidence Chunks consumed by the
same Stage Context/provenance path as document/source evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def _hash(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


def normalize(data: Any, *, provider: str, default_kind: str = "OTHER") -> dict[str, Any]:
    rows = data if isinstance(data, list) else data.get("items", data.get("results", [data])) if isinstance(data, dict) else []
    if not isinstance(rows, list):
        rows = [rows]
    chunks = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            row = {"value": row}
        external_id = str(row.get("id") or row.get("key") or row.get("name") or index)
        locator = str(row.get("url") or row.get("locator") or row.get("path") or f"{provider}:{external_id}")
        raw_text = row.get("text") or row.get("body") or row.get("summary") or row.get("message")
        if raw_text is None:
            raw_text = json.dumps(row, ensure_ascii=False, sort_keys=True)
        chunks.append({
            "document_id": f"EXT-{provider}",
            "locator": locator,
            "raw_text": str(raw_text),
            "source_hash": _hash(row),
            "extraction_status": "EXTRACTED",
            "extraction_method": f"EXTERNAL_PROVIDER:{provider}",
            "content_kind": str(row.get("content_kind") or default_kind),
            "structured_content": row,
            "format_context": {"provider": provider, "external_id": external_id},
            "sequence": index,
            "confidence": str(row.get("confidence") or "MEDIUM"),
        })
    return {
        "schema_version": 1,
        "provider": provider,
        "chunk_count": len(chunks),
        "evidence_chunks": chunks,
        "boundary": "External Provider -> Evidence Chunk -> Canonical/Stage Context",
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Normalize external Tool/MCP JSON into common Evidence Chunks.")
    ap.add_argument("--input", required=True)
    ap.add_argument("--provider", required=True)
    ap.add_argument("--kind", default="OTHER")
    ap.add_argument("--output", required=True)
    args = ap.parse_args(argv)
    try:
        data = json.loads(Path(args.input).read_text(encoding="utf-8"))
        result = normalize(data, provider=args.provider, default_kind=args.kind)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        result = {"schema_version": 1, "provider": args.provider, "chunk_count": 0, "evidence_chunks": [], "error": str(exc)}
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"provider": args.provider, "chunk_count": result.get("chunk_count", 0), "output": str(out)}, ensure_ascii=False))
    return 0 if result.get("chunk_count", 0) else 4


if __name__ == "__main__":
    raise SystemExit(main())
