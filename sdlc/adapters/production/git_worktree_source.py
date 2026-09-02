#!/usr/bin/env python3
"""Git worktree SOURCE adapter with revision, branch, scope and atomic-write guards.

This adapter is a production-candidate implementation. It is intentionally conservative:
- every write is serialized with a repository-local file lock,
- HEAD is re-read immediately before write,
- optional expected object hash protects against concurrent uncommitted edits,
- path traversal and symlink escapes are denied,
- writes never auto-commit or promote source behavior to business truth.
"""
from __future__ import annotations

import hashlib
import os
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows is explicitly unsupported for write lock today.
    fcntl = None

ADAPTER_VERSION = "P0-PROD-1"
PROVIDER_ID = "git-worktree-source"
PROVIDER_TYPE = "SOURCE"
CAPABILITIES = [
    "source.snapshot.read",
    "source.object.read",
    "source.search",
    "source.diff",
    "source.write",
]


def describe() -> dict[str, Any]:
    return {
        "provider_id": PROVIDER_ID,
        "provider_type": PROVIDER_TYPE,
        "provider_state": "AVAILABLE",
        "mode": "READ_WRITE",
        "capabilities": list(CAPABILITIES),
        "adapter_version": ADAPTER_VERSION,
        "production_candidate": True,
    }


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
            "provider_revision": revision or "UNAVAILABLE",
            "outputs": outputs,
            "evidence": evidence,
            "open_items": open_items,
            "warnings": warnings,
            "retryable": retryable,
            "extensions": extensions or {},
        },
    }


def _blocked(req: dict[str, Any], code: str, message: str, revision: str = "UNAVAILABLE", retryable: bool = False):
    return _response(req, "BLOCKED", revision, [], [], [{"code": code, "message": message}], [], retryable)


def _git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args], shell=False, capture_output=True, text=True, check=check
    )


def _root(req: dict[str, Any], config: dict[str, Any]) -> Path | None:
    raw = (req.get("extensions") or {}).get("root") or config.get("root")
    if not raw:
        return None
    root = Path(raw).expanduser().resolve()
    if not root.is_dir() or not (root / ".git").exists():
        return None
    return root


def _head(root: Path) -> str:
    return _git(root, "rev-parse", "HEAD").stdout.strip()


def _branch(root: Path) -> str:
    return _git(root, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()


def _safe(root: Path, relative: str) -> Path:
    if not relative or Path(relative).is_absolute():
        raise ValueError("relative path required")
    raw_candidate = root / relative
    if raw_candidate.is_symlink():
        raise ValueError("symlink target is not writable through this adapter")
    candidate = raw_candidate.resolve()
    candidate.relative_to(root)
    return candidate


def _hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _hash_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    return _hash_bytes(path.read_bytes())


def _bounded_files(root: Path, max_files: int, max_bytes: int, excludes: Iterable[str]) -> tuple[list[Path], bool]:
    files: list[Path] = []
    total = 0
    excluded = tuple(excludes)
    limited = False
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix()
        if rel.startswith(".git/") or rel.startswith(".ai-sdlc/") or any(rel.startswith(x.rstrip("/") + "/") or rel == x.rstrip("/") for x in excluded):
            continue
        size = path.stat().st_size
        if len(files) >= max_files or total + size > max_bytes:
            limited = True
            break
        files.append(path)
        total += size
    return files, limited


def _snapshot(root: Path, files: Iterable[Path]) -> list[dict[str, Any]]:
    out = []
    for path in files:
        out.append({
            "path": path.relative_to(root).as_posix(),
            "sha256": _hash_file(path),
            "size": path.stat().st_size,
        })
    return out


@contextmanager
def _write_lock(root: Path):
    if fcntl is None:
        raise RuntimeError("atomic source.write lock requires fcntl-compatible platform")
    lock_dir = root / ".ai-sdlc" / "locks"
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock_path = lock_dir / "source-write.lock"
    with lock_path.open("a+", encoding="utf-8") as fh:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


def _read_text(path: Path, max_chars: int) -> tuple[str | None, str | None]:
    try:
        return path.read_text(encoding="utf-8")[:max_chars], None
    except (UnicodeDecodeError, OSError) as exc:
        return None, str(exc)


def invoke(request_doc: dict[str, Any], adapter_config: dict[str, Any] | None = None) -> dict[str, Any]:
    config = adapter_config or {}
    req = (request_doc or {}).get("provider_request") or request_doc
    operation = req.get("operation")
    if operation not in CAPABILITIES:
        return _blocked(req, "UNSUPPORTED_OPERATION", f"unsupported capability: {operation}")
    root = _root(req, config)
    if root is None:
        return _blocked(req, "GIT_SOURCE_ROOT_UNAVAILABLE", "configured root must be an existing Git worktree")
    try:
        head = _head(root)
    except (subprocess.CalledProcessError, OSError) as exc:
        return _blocked(req, "GIT_REVISION_UNAVAILABLE", str(exc))

    ext = req.get("extensions") or {}
    max_files = int(config.get("max_files", 1000))
    max_bytes = int(config.get("max_bytes", 20_000_000))
    max_chars = int(config.get("max_output_chars", 40_000))
    excludes = list(config.get("exclude_paths") or [])

    if operation == "source.object.read":
        try:
            path = _safe(root, str(ext.get("path") or ""))
        except ValueError as exc:
            return _blocked(req, "SOURCE_SCOPE_VIOLATION", str(exc), head)
        if not path.is_file():
            return _blocked(req, "SOURCE_OBJECT_NOT_FOUND", str(ext.get("path")), head)
        content, error = _read_text(path, max_chars)
        digest = _hash_file(path) or "MISSING"
        if error:
            return _response(req, "PARTIAL", head, [{"path": ext.get("path"), "sha256": digest}], [], [], [error])
        evidence = [{"evidence_id": "EV-GIT-READ-001", "truth": "OBSERVED", "locator": str(ext.get("path")), "revision": head,
                     "observed_value": {"sha256": digest, "content": content}}]
        return _response(req, "OK", head, [{"path": ext.get("path"), "sha256": digest, "content": content}], evidence, [], [])

    if operation == "source.snapshot.read":
        files, limited = _bounded_files(root, max_files, max_bytes, excludes)
        items = _snapshot(root, files)
        evidence = [{"evidence_id": "EV-GIT-SNAPSHOT-001", "truth": "OBSERVED", "locator": str(root), "revision": head,
                     "observed_value": {"file_count": len(items), "branch": _branch(root)}}]
        warnings = ["bounded scan limit reached"] if limited else []
        return _response(req, "PARTIAL" if limited else "OK", head, [{"files": items, "branch": _branch(root)}], evidence, [], warnings)

    if operation == "source.search":
        query = str(ext.get("query") or "")
        if not query:
            return _blocked(req, "SOURCE_QUERY_REQUIRED", "extensions.query is required", head)
        files, limited = _bounded_files(root, max_files, max_bytes, excludes)
        matches: list[dict[str, Any]] = []
        for path in files:
            text, _ = _read_text(path, max_chars)
            if text is None:
                continue
            for line_no, line in enumerate(text.splitlines(), 1):
                if query in line:
                    matches.append({"path": path.relative_to(root).as_posix(), "line": line_no, "text": line[:500]})
        evidence = [{"evidence_id": "EV-GIT-SEARCH-001", "truth": "OBSERVED", "locator": str(root), "revision": head,
                     "observed_value": {"query": query, "match_count": len(matches)}}]
        return _response(req, "PARTIAL" if limited else "OK", head, [{"query": query, "matches": matches}], evidence, [], ["bounded scan limit reached"] if limited else [])

    if operation == "source.diff":
        base = str(ext.get("base_revision") or req.get("expected_revision") or "")
        target = str(ext.get("target_revision") or head)
        if not base:
            return _blocked(req, "SOURCE_DIFF_BASE_REQUIRED", "base_revision or expected_revision is required", head)
        try:
            cp = _git(root, "diff", "--name-status", base, target)
        except subprocess.CalledProcessError as exc:
            return _blocked(req, "SOURCE_DIFF_FAILED", exc.stderr.strip() or str(exc), head)
        changed = []
        for line in cp.stdout.splitlines():
            parts = line.split("\t")
            if len(parts) >= 2:
                changed.append({"status": parts[0], "path": parts[-1]})
        evidence = [{"evidence_id": "EV-GIT-DIFF-001", "truth": "OBSERVED", "locator": f"git:{base}..{target}", "revision": head,
                     "observed_value": {"changed": changed}}]
        return _response(req, "OK", head, [{"base_revision": base, "target_revision": target, "changed": changed}], evidence, [], [])

    # source.write
    if req.get("write_intent") is not True:
        return _blocked(req, "WRITE_INTENT_REQUIRED", "source.write requires write_intent=true", head)
    relative = str(ext.get("path") or "")
    content = ext.get("content")
    if not isinstance(content, str):
        return _blocked(req, "SOURCE_CONTENT_REQUIRED", "extensions.content must be a UTF-8 string", head)
    expected = str(req.get("expected_revision") or "")
    expected_branch = ext.get("expected_agent_branch") or config.get("expected_agent_branch")
    expected_object_hash = ext.get("expected_object_sha256")
    try:
        target_path = _safe(root, relative)
    except ValueError as exc:
        return _blocked(req, "SOURCE_SCOPE_VIOLATION", str(exc), head)

    try:
        with _write_lock(root):
            current_head = _head(root)
            if expected != current_head:
                return _blocked(req, "REVISION_MISMATCH", f"expected {expected}, current {current_head}", current_head)
            current_branch = _branch(root)
            if expected_branch and current_branch != expected_branch:
                return _blocked(req, "AGENT_BRANCH_MISMATCH", f"expected branch {expected_branch}, current {current_branch}", current_head)
            before_hash = _hash_file(target_path)
            if expected_object_hash is not None and expected_object_hash != before_hash:
                return _blocked(req, "OBJECT_REVISION_MISMATCH", f"expected object {expected_object_hash}, current {before_hash}", current_head)
            new_bytes = content.encode("utf-8")
            after_hash = _hash_bytes(new_bytes)
            if before_hash == after_hash:
                evidence = [{"evidence_id": "EV-GIT-WRITE-IDEMPOTENT-001", "truth": "OBSERVED", "locator": relative, "revision": current_head,
                             "observed_value": {"before_sha256": before_hash, "after_sha256": after_hash, "idempotent": True}}]
                return _response(req, "OK", current_head, [{"path": relative, "changed": False, "sha256": after_hash}], evidence, [], [])
            target_path.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp_name = tempfile.mkstemp(prefix=".ai-sdlc-write-", dir=str(target_path.parent))
            try:
                with os.fdopen(fd, "wb") as fh:
                    fh.write(new_bytes)
                    fh.flush()
                    os.fsync(fh.fileno())
                os.replace(tmp_name, target_path)
            finally:
                if os.path.exists(tmp_name):
                    os.unlink(tmp_name)
            actual_hash = _hash_file(target_path)
            if actual_hash != after_hash:
                return _response(req, "ERROR", current_head, [], [], [{"code": "POST_WRITE_HASH_MISMATCH", "message": relative}], [], False)
            evidence = [{"evidence_id": "EV-GIT-WRITE-001", "truth": "OBSERVED", "locator": relative, "revision": current_head,
                         "observed_value": {"before_sha256": before_hash, "after_sha256": actual_hash, "branch": current_branch, "committed": False}}]
            return _response(req, "OK", current_head, [{"path": relative, "changed": True, "before_sha256": before_hash, "after_sha256": actual_hash,
                                                        "branch": current_branch, "committed": False}], evidence, [], [], extensions={"post_write_verification": "HASH_MATCH"})
    except RuntimeError as exc:
        return _blocked(req, "WRITE_LOCK_UNAVAILABLE", str(exc), head)
    except OSError as exc:
        # At this point the runtime wrapper must classify an adapter exception as UNKNOWN_AFTER_WRITE.
        raise RuntimeError(f"source.write I/O failure for {relative}: {exc}") from exc
