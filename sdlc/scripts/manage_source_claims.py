#!/usr/bin/env python3
"""Atomic file/program claim manager for multi-agent source changes.

Claims are persisted under the project runtime directory and mutated while holding an OS file lock.
This is the enforcement primitive used before source.write; it is not a distributed lock service.
For multi-host agents, replace this adapter with a shared transactional claim provider.
"""
from __future__ import annotations

import argparse
import fnmatch
import os
import subprocess
import tempfile
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
import yaml

try:
    import fcntl
except ImportError:  # pragma: no cover
    fcntl = None


def now() -> datetime:
    return datetime.now(timezone.utc)


def iso(value: datetime) -> str:
    return value.isoformat()


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def git_head(project_root: Path) -> str:
    cp = subprocess.run(["git", "-C", str(project_root), "rev-parse", "HEAD"], shell=False, capture_output=True, text=True, check=True)
    return cp.stdout.strip()


def git_branch(project_root: Path) -> str:
    cp = subprocess.run(["git", "-C", str(project_root), "rev-parse", "--abbrev-ref", "HEAD"], shell=False, capture_output=True, text=True, check=True)
    return cp.stdout.strip()


def load_store(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema_version": 1, "artifact_type": "SOURCE_CLAIM_STORE", "claims": []}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {"schema_version": 1, "artifact_type": "SOURCE_CLAIM_STORE", "claims": []}


def atomic_write(path: Path, doc: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".claims-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            yaml.safe_dump(doc, fh, allow_unicode=True, sort_keys=False)
            fh.flush(); os.fsync(fh.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


@contextmanager
def locked(path: Path):
    if fcntl is None:
        raise RuntimeError("atomic claims require fcntl-compatible platform")
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = path.with_suffix(path.suffix + ".lock")
    with lock.open("a+", encoding="utf-8") as fh:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


def overlap(a: str, b: str) -> bool:
    if a == b or fnmatch.fnmatch(a, b) or fnmatch.fnmatch(b, a):
        return True
    # Fail safe for common glob prefixes. We prefer a false conflict over silent double ownership.
    prefix_a = a.split("*")[0].split("?")[0]
    prefix_b = b.split("*")[0].split("?")[0]
    return bool(prefix_a and prefix_b and (prefix_a.startswith(prefix_b) or prefix_b.startswith(prefix_a)))


def active_claims(store: dict[str, Any], at: datetime | None = None) -> list[dict[str, Any]]:
    at = at or now()
    out = []
    for claim in store.get("claims") or []:
        if claim.get("status") != "ACTIVE":
            continue
        expires = parse_time(claim.get("expires_at"))
        if expires and expires <= at:
            claim["status"] = "EXPIRED"
            claim["expired_at"] = iso(at)
            continue
        out.append(claim)
    return out


def acquire(project_root: Path, store_path: Path, claim_id: str, agent_id: str, paths: list[str], programs: list[str],
            expected_revision: str, expected_branch: str | None, ttl_minutes: int) -> tuple[int, dict[str, Any]]:
    if not paths and not programs:
        return 1, {"decision": "DENY", "blockers": [{"code": "CLAIM_SCOPE_REQUIRED"}]}
    try:
        current_revision = git_head(project_root)
        current_branch = git_branch(project_root)
    except (subprocess.CalledProcessError, OSError) as exc:
        return 1, {"decision": "DENY", "blockers": [{"code": "GIT_CONTEXT_UNAVAILABLE", "message": str(exc)}]}
    if expected_revision != current_revision:
        return 1, {"decision": "DENY", "blockers": [{"code": "REVISION_MISMATCH", "expected_revision": expected_revision, "current_revision": current_revision}]}
    if expected_branch and expected_branch != current_branch:
        return 1, {"decision": "DENY", "blockers": [{"code": "BRANCH_MISMATCH", "expected_branch": expected_branch, "current_branch": current_branch}]}

    with locked(store_path):
        store = load_store(store_path)
        active = active_claims(store)
        blockers = []
        for claim in active:
            if claim.get("agent_id") == agent_id and claim.get("claim_id") == claim_id:
                if sorted(claim.get("paths") or []) == sorted(paths) and sorted(claim.get("program_ids") or []) == sorted(programs):
                    atomic_write(store_path, store)
                    return 0, {"decision": "ALLOW", "claim": claim, "idempotent": True}
                blockers.append({"code": "CLAIM_ID_REUSE_WITH_DIFFERENT_SCOPE", "claim_id": claim_id})
                continue
            if claim.get("agent_id") == agent_id:
                continue
            for requested in paths:
                for owned in claim.get("paths") or []:
                    if overlap(requested, owned):
                        blockers.append({"code": "ACTIVE_PATH_CLAIM_CONFLICT", "path": requested, "conflicting_claim_id": claim.get("claim_id"), "conflicting_agent_id": claim.get("agent_id")})
            if set(programs).intersection(set(claim.get("program_ids") or [])):
                blockers.append({"code": "ACTIVE_PROGRAM_CLAIM_CONFLICT", "program_ids": sorted(set(programs).intersection(set(claim.get("program_ids") or []))),
                                 "conflicting_claim_id": claim.get("claim_id"), "conflicting_agent_id": claim.get("agent_id")})
        if blockers:
            atomic_write(store_path, store)
            return 1, {"decision": "DENY", "blockers": blockers, "current_revision": current_revision, "current_branch": current_branch}
        acquired = now()
        claim = {
            "claim_id": claim_id,
            "agent_id": agent_id,
            "paths": paths,
            "program_ids": programs,
            "expected_revision": expected_revision,
            "branch": current_branch,
            "status": "ACTIVE",
            "acquired_at": iso(acquired),
            "expires_at": iso(acquired + timedelta(minutes=ttl_minutes)),
        }
        store.setdefault("claims", []).append(claim)
        atomic_write(store_path, store)
        return 0, {"decision": "ALLOW", "claim": claim, "idempotent": False}


def release(store_path: Path, claim_id: str, agent_id: str) -> tuple[int, dict[str, Any]]:
    with locked(store_path):
        store = load_store(store_path)
        active_claims(store)
        for claim in store.get("claims") or []:
            if claim.get("claim_id") != claim_id:
                continue
            if claim.get("agent_id") != agent_id:
                return 1, {"decision": "DENY", "blockers": [{"code": "CLAIM_OWNER_MISMATCH", "claim_id": claim_id}]}
            if claim.get("status") != "ACTIVE":
                atomic_write(store_path, store)
                return 0, {"decision": "ALLOW", "released": claim_id, "idempotent": True, "previous_status": claim.get("status")}
            claim["status"] = "RELEASED"; claim["released_at"] = iso(now())
            atomic_write(store_path, store)
            return 0, {"decision": "ALLOW", "released": claim_id, "idempotent": False}
        return 1, {"decision": "DENY", "blockers": [{"code": "CLAIM_NOT_FOUND", "claim_id": claim_id}]}


def verify(store_path: Path, claim_id: str, agent_id: str, paths: list[str]) -> tuple[int, dict[str, Any]]:
    with locked(store_path):
        store = load_store(store_path)
        active = active_claims(store)
        atomic_write(store_path, store)
        for claim in active:
            if claim.get("claim_id") == claim_id and claim.get("agent_id") == agent_id:
                uncovered = [path for path in paths if not any(fnmatch.fnmatch(path, pattern) for pattern in claim.get("paths") or [])]
                if uncovered:
                    return 1, {"decision": "DENY", "blockers": [{"code": "CLAIM_DOES_NOT_COVER_PATH", "paths": uncovered}]}
                return 0, {"decision": "ALLOW", "claim": claim}
        return 1, {"decision": "DENY", "blockers": [{"code": "ACTIVE_CLAIM_REQUIRED", "claim_id": claim_id, "agent_id": agent_id}]}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["acquire", "release", "verify", "list"])
    p.add_argument("--project-root", type=Path, default=Path("."))
    p.add_argument("--store", type=Path)
    p.add_argument("--claim-id")
    p.add_argument("--agent-id")
    p.add_argument("--path", action="append", default=[])
    p.add_argument("--program-id", action="append", default=[])
    p.add_argument("--expected-revision")
    p.add_argument("--expected-branch")
    p.add_argument("--ttl-minutes", type=int, default=120)
    p.add_argument("-o", "--output", type=Path)
    a = p.parse_args()
    root = a.project_root.resolve()
    store = (a.store or (root / ".ai-sdlc" / "claims" / "source-claims.yaml")).resolve()
    if a.action == "acquire":
        if not a.claim_id or not a.agent_id or not a.expected_revision:
            p.error("acquire requires --claim-id --agent-id --expected-revision")
        code, result = acquire(root, store, a.claim_id, a.agent_id, a.path, a.program_id, a.expected_revision, a.expected_branch, a.ttl_minutes)
    elif a.action == "release":
        if not a.claim_id or not a.agent_id:
            p.error("release requires --claim-id --agent-id")
        code, result = release(store, a.claim_id, a.agent_id)
    elif a.action == "verify":
        if not a.claim_id or not a.agent_id:
            p.error("verify requires --claim-id --agent-id")
        code, result = verify(store, a.claim_id, a.agent_id, a.path)
    else:
        with locked(store):
            doc = load_store(store); active = active_claims(doc); atomic_write(store, doc)
        code, result = 0, {"decision": "ALLOW", "active_claims": active, "store": str(store)}
    out = {"schema_version": 1, "artifact_type": "SOURCE_CLAIM_RESULT", "source_claim_result": result}
    text = yaml.safe_dump(out, allow_unicode=True, sort_keys=False)
    if a.output:
        a.output.parent.mkdir(parents=True, exist_ok=True); a.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
