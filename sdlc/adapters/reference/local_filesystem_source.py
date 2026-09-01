#!/usr/bin/env python3
"""Stack-neutral local filesystem SOURCE reference adapter for P0.7."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Iterable

ADAPTER_VERSION = "P0.7-1"
PROVIDER_ID = "reference-local-filesystem-source"
PROVIDER_TYPE = "SOURCE"
CAPABILITIES = [
    "source.snapshot.read",
    "source.object.read",
    "source.search",
    "source.diff",
]


def describe() -> dict[str, Any]:
    return {
        "provider_id": PROVIDER_ID,
        "provider_type": PROVIDER_TYPE,
        "provider_state": "AVAILABLE",
        "mode": "READ_ONLY",
        "capabilities": list(CAPABILITIES),
        "adapter_version": ADAPTER_VERSION,
    }


def _blocked(req: dict[str, Any], code: str, message: str, retryable: bool = False) -> dict[str, Any]:
    return _response(req, "BLOCKED", "UNAVAILABLE", [], [], [{"code": code, "message": message}], [], retryable)


def _response(req: dict[str, Any], status: str, revision: str, outputs: list[Any], evidence: list[dict[str, Any]],
              open_items: list[dict[str, Any]], warnings: list[str], retryable: bool = False,
              extensions: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "provider_response": {
            "request_id": req.get("request_id"),
            "provider_id": PROVIDER_ID,
            "provider_type": PROVIDER_TYPE,
            "operation": req.get("operation"),
            "status": status,
            "provider_revision": revision,
            "outputs": outputs,
            "evidence": evidence,
            "open_items": open_items,
            "warnings": warnings,
            "retryable": retryable,
            "extensions": extensions or {},
        },
    }


def _root(req: dict[str, Any], config: dict[str, Any]) -> Path | None:
    ext = req.get("extensions") or {}
    raw = ext.get("root") or config.get("root")
    if not raw:
        return None
    root = Path(raw).expanduser().resolve()
    return root if root.exists() and root.is_dir() else None


def _safe(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    candidate.relative_to(root)
    return candidate


def _text_files(root: Path, max_files: int, max_bytes: int) -> tuple[list[Path], bool, list[str]]:
    files: list[Path] = []
    total = 0
    limited = False
    warnings: list[str] = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        try:
            size = path.stat().st_size
        except OSError as exc:
            warnings.append(f"stat failed: {path.relative_to(root)}: {exc}")
            continue
        if len(files) >= max_files or total + size > max_bytes:
            limited = True
            break
        files.append(path)
        total += size
    return files, limited, warnings


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _snapshot(root: Path, files: Iterable[Path]) -> tuple[str, list[dict[str, Any]]]:
    items = []
    manifest = hashlib.sha256()
    for path in files:
        rel = path.relative_to(root).as_posix()
        digest = _hash_file(path)
        size = path.stat().st_size
        items.append({"path": rel, "sha256": digest, "size": size})
        manifest.update(rel.encode("utf-8")); manifest.update(b"\0"); manifest.update(digest.encode("ascii")); manifest.update(b"\n")
    return manifest.hexdigest(), items


def _read_text(path: Path, max_output_chars: int) -> tuple[str | None, str | None]:
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError) as exc:
        return None, str(exc)
    return text[:max_output_chars], None


def invoke(request_doc: dict[str, Any], adapter_config: dict[str, Any] | None = None) -> dict[str, Any]:
    config = adapter_config or {}
    req = (request_doc or {}).get("provider_request") or request_doc
    operation = req.get("operation")
    if operation not in CAPABILITIES:
        return _blocked(req, "UNSUPPORTED_OPERATION", f"unsupported capability: {operation}")
    root = _root(req, config)
    if root is None:
        return _blocked(req, "SOURCE_ROOT_UNAVAILABLE", "configured source root is missing or not a directory")

    max_files = int(config.get("max_files", 500))
    max_bytes = int(config.get("max_bytes", 5_000_000))
    max_output_chars = int(config.get("max_output_chars", 20_000))

    if operation == "source.object.read":
        relative = str((req.get("extensions") or {}).get("path") or "")
        if not relative:
            return _blocked(req, "SOURCE_PATH_REQUIRED", "extensions.path is required")
        try:
            path = _safe(root, relative)
        except (ValueError, OSError):
            return _blocked(req, "SOURCE_SCOPE_VIOLATION", "requested path is outside source root")
        if not path.is_file():
            return _blocked(req, "SOURCE_OBJECT_NOT_FOUND", f"source object not found: {relative}")
        digest = _hash_file(path)
        text, error = _read_text(path, max_output_chars)
        if error:
            return _response(req, "PARTIAL", digest, [{"path": relative, "sha256": digest}], [], [], [error])
        evidence = [{"evidence_id": "EV-SOURCE-READ-001", "truth": "OBSERVED", "locator": relative,
                     "revision": digest, "observed_value": {"sha256": digest, "content": text}}]
        return _response(req, "OK", digest, [{"path": relative, "sha256": digest, "content": text}], evidence, [], [])

    if operation == "source.diff":
        ext = req.get("extensions") or {}
        before_raw, after_raw = ext.get("before_root"), ext.get("after_root")
        if not before_raw or not after_raw:
            return _blocked(req, "SOURCE_DIFF_ROOT_REQUIRED", "extensions.before_root and extensions.after_root are required")
        before, after = Path(before_raw).expanduser().resolve(), Path(after_raw).expanduser().resolve()
        if not before.is_dir() or not after.is_dir():
            return _blocked(req, "SOURCE_DIFF_ROOT_UNAVAILABLE", "before/after source roots must exist")
        bf, bl, bw = _text_files(before, max_files, max_bytes)
        af, al, aw = _text_files(after, max_files, max_bytes)
        brev, bitems = _snapshot(before, bf); arev, aitems = _snapshot(after, af)
        bmap = {x["path"]: x["sha256"] for x in bitems}; amap = {x["path"]: x["sha256"] for x in aitems}
        changed = sorted({p for p in set(bmap) | set(amap) if bmap.get(p) != amap.get(p)})
        evidence = [{"evidence_id": "EV-SOURCE-DIFF-001", "truth": "OBSERVED", "locator": "filesystem-diff",
                     "revision": f"{brev}..{arev}", "observed_value": {"changed_paths": changed}}]
        status = "PARTIAL" if bl or al else "OK"
        warnings = bw + aw + (["bounded scan limit reached"] if bl or al else [])
        return _response(req, status, arev, [{"before_revision": brev, "after_revision": arev, "changed_paths": changed}], evidence, [], warnings)

    files, limited, warnings = _text_files(root, max_files, max_bytes)
    revision, items = _snapshot(root, files)
    if operation == "source.snapshot.read":
        evidence = [{"evidence_id": "EV-SOURCE-SNAPSHOT-001", "truth": "OBSERVED", "locator": str(root),
                     "revision": revision, "observed_value": {"file_count": len(items)}}]
        status = "PARTIAL" if limited else "OK"
        if limited: warnings.append("bounded scan limit reached")
        return _response(req, status, revision, [{"files": items}], evidence, [], warnings)

    query = str((req.get("extensions") or {}).get("query") or "")
    if not query:
        return _blocked(req, "SOURCE_QUERY_REQUIRED", "extensions.query is required")
    matches = []
    for path in files:
        text, error = _read_text(path, max_output_chars)
        if error or text is None:
            if error: warnings.append(f"read failed: {path.relative_to(root)}: {error}")
            continue
        for line_no, line in enumerate(text.splitlines(), 1):
            if query in line:
                matches.append({"path": path.relative_to(root).as_posix(), "line": line_no, "text": line[:500]})
    evidence = [{"evidence_id": "EV-SOURCE-SEARCH-001", "truth": "OBSERVED", "locator": str(root),
                 "revision": revision, "observed_value": {"query": query, "match_count": len(matches)}}]
    status = "PARTIAL" if limited else "OK"
    if limited: warnings.append("bounded scan limit reached")
    return _response(req, status, revision, [{"query": query, "matches": matches}], evidence, [], warnings)
