#!/usr/bin/env python3
"""Minimal executable Canonical JSON store + concurrency-safe delta applier.

The semantic behavior stays intentionally small: JSON file store, optimistic revision,
semantic idempotency, all-or-nothing entity/relation/provenance operations, no delete,
and no Source-derived overwrite of CONFIRMED_BUSINESS truth.

P0 runtime hardening adds a filesystem lock plus atomic replace at the *write* boundary.
`apply_delta()` remains a pure in-memory function for tests/reuse. Production callers
should use `apply_delta_to_store()` so two Agent processes cannot both commit a delta
based on the same on-disk revision.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

EVIDENCE_CLASSES = {"GIVEN", "OBSERVED", "INFERRED", "ASSUMED", "CONFIRMED"}
NON_CONFIRMED_EVIDENCE = EVIDENCE_CLASSES - {"CONFIRMED"}
ALLOWED_OPS = {"UPSERT_ENTITY", "UPSERT_RELATION", "ADD_PROVENANCE"}


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def empty_store() -> dict:
    return {
        "schema_version": 1,
        "revision": 0,
        "updated_at": None,
        "entities": {},
        "relations": [],
        "applied_deltas": [],
    }


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON object required: {path}")
    return data


def validate_store(store: dict) -> None:
    if store.get("schema_version") != 1:
        raise ValueError("canonical store schema_version must be 1")
    if not isinstance(store.get("revision"), int) or store["revision"] < 0:
        raise ValueError("canonical store revision must be a non-negative integer")
    if not isinstance(store.get("entities"), dict):
        raise ValueError("canonical store entities must be an object")
    if not isinstance(store.get("relations"), list):
        raise ValueError("canonical store relations must be an array")
    if not isinstance(store.get("applied_deltas"), list):
        raise ValueError("canonical store applied_deltas must be an array")


def load_store(path: Path) -> dict:
    if not path.exists():
        return empty_store()
    data = load_json(path)
    validate_store(data)
    return data


def _atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
    try:
        with temp.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink(missing_ok=True)


def save_store(path: Path, store: dict) -> None:
    """Atomically replace the store file.

    This function intentionally does not acquire a lock because a few tests/builders use
    it for isolated snapshots. Concurrent production mutation should go through
    `apply_delta_to_store()`.
    """
    validate_store(store)
    _atomic_write_json(path, store)


@contextmanager
def store_lock(path: Path, timeout_seconds: float = 10.0, poll_seconds: float = 0.05):
    """Cross-process lock using O_EXCL; no third-party dependency required."""
    lock_path = path.with_suffix(path.suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + max(timeout_seconds, 0.1)
    fd = None
    while True:
        try:
            fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.write(fd, f"pid={os.getpid()} acquired_at={now()}\n".encode("utf-8"))
            os.fsync(fd)
            break
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise TimeoutError(f"canonical store lock timeout: {lock_path}")
            time.sleep(poll_seconds)
    try:
        yield lock_path
    finally:
        if fd is not None:
            os.close(fd)
        lock_path.unlink(missing_ok=True)


def _error(code: str, message: str, **extra) -> dict:
    return {"code": code, "message": message, **extra}


def _semantic_delta_payload(delta: dict) -> dict:
    volatile = {"generated_at", "updated_at", "created_at", "checked_at", "observed_at"}

    def clean(value):
        if isinstance(value, dict):
            return {k: clean(v) for k, v in sorted(value.items()) if k not in volatile and k != "base_revision"}
        if isinstance(value, list):
            return [clean(v) for v in value]
        return value

    return clean(delta)


def delta_payload_hash(delta: dict) -> str:
    raw = json.dumps(_semantic_delta_payload(delta), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


def validate_delta(delta: dict) -> list[dict]:
    errors = []
    if delta.get("schema_version") != 1:
        errors.append(_error("INVALID_SCHEMA_VERSION", "delta schema_version must be 1"))
    if not str(delta.get("delta_id") or "").strip():
        errors.append(_error("MISSING_DELTA_ID", "delta_id is required"))
    if not isinstance(delta.get("base_revision"), int) or delta.get("base_revision", -1) < 0:
        errors.append(_error("INVALID_BASE_REVISION", "base_revision must be a non-negative integer"))
    if not str(delta.get("stage") or "").strip():
        errors.append(_error("MISSING_STAGE", "stage is required"))
    if not str(delta.get("source_artifact") or "").strip():
        errors.append(_error("MISSING_SOURCE_ARTIFACT", "source_artifact is required"))

    operations = delta.get("operations")
    if not isinstance(operations, list):
        errors.append(_error("INVALID_OPERATIONS", "operations must be an array"))
        return errors
    if not operations:
        if not str(delta.get("no_change_reason") or "").strip():
            errors.append(_error(
                "EMPTY_OPERATIONS_REQUIRE_REASON",
                "empty operations require no_change_reason for explicit document-only/no-canonical-change work",
            ))
        return errors

    for index, op in enumerate(operations):
        if not isinstance(op, dict):
            errors.append(_error("INVALID_OPERATION", "operation must be an object", operation_index=index))
            continue
        kind = op.get("op")
        if kind not in ALLOWED_OPS:
            errors.append(_error("UNSUPPORTED_OPERATION", f"unsupported operation: {kind}", operation_index=index))
            continue
        evidence = op.get("evidence_class")
        if evidence not in EVIDENCE_CLASSES:
            errors.append(_error("INVALID_EVIDENCE_CLASS", f"invalid evidence_class: {evidence}", operation_index=index))
        if kind == "UPSERT_ENTITY":
            if not str(op.get("id") or "").strip():
                errors.append(_error("MISSING_ENTITY_ID", "UPSERT_ENTITY requires id", operation_index=index))
            if not str(op.get("entity_type") or "").strip():
                errors.append(_error("MISSING_ENTITY_TYPE", "UPSERT_ENTITY requires entity_type", operation_index=index))
            if not isinstance(op.get("fields", {}), dict):
                errors.append(_error("INVALID_ENTITY_FIELDS", "UPSERT_ENTITY fields must be an object", operation_index=index))
            if op.get("truth_status") == "CONFIRMED_BUSINESS" and evidence != "CONFIRMED":
                errors.append(_error(
                    "BUSINESS_CONFIRMATION_REQUIRES_CONFIRMED_EVIDENCE",
                    "CONFIRMED_BUSINESS requires evidence_class CONFIRMED",
                    operation_index=index,
                ))
        elif kind == "UPSERT_RELATION":
            for field in ["from", "kind", "to"]:
                if not str(op.get(field) or "").strip():
                    errors.append(_error("MISSING_RELATION_FIELD", f"UPSERT_RELATION requires {field}", operation_index=index, field=field))
        elif kind == "ADD_PROVENANCE" and not str(op.get("id") or "").strip():
            errors.append(_error("MISSING_ENTITY_ID", "ADD_PROVENANCE requires id", operation_index=index))
    return errors


def _provenance(delta: dict, op: dict, operation_index: int) -> dict:
    row = {
        "delta_id": delta["delta_id"],
        "stage": delta["stage"],
        "source_artifact": delta["source_artifact"],
        "evidence_class": op["evidence_class"],
        "operation_index": operation_index,
    }
    for key in ["locator", "source_hash", "note", "git_commit", "canonical_revision"]:
        if op.get(key) not in (None, ""):
            row[key] = op[key]
    return row


def _append_provenance(entity: dict, row: dict) -> None:
    rows = entity.setdefault("provenance", [])
    key = (row.get("delta_id"), row.get("operation_index"), row.get("locator"), row.get("source_hash"))
    for existing in rows:
        existing_key = (existing.get("delta_id"), existing.get("operation_index"), existing.get("locator"), existing.get("source_hash"))
        if existing_key == key:
            return
    rows.append(row)


def _relation_key(row: dict) -> tuple[str, str, str]:
    return str(row.get("from")), str(row.get("kind")), str(row.get("to"))


def _changed_fields(existing: dict, incoming: dict) -> list[str]:
    current = existing.get("fields", {})
    return sorted(key for key, value in incoming.items() if current.get(key) != value)


def _existing_delta(store: dict, delta_id: str) -> dict | None:
    return next((row for row in store.get("applied_deltas", []) if row.get("delta_id") == delta_id), None)


def apply_delta(store: dict, delta: dict) -> tuple[dict, dict]:
    """Pure semantic apply. Conflict/invalid deltas never mutate the input store."""
    validate_store(store)
    original = copy.deepcopy(store)
    errors = validate_delta(delta)
    if errors:
        return ({"status": "INVALID_DELTA", "delta_id": delta.get("delta_id"), "store_revision": store["revision"], "errors": errors}, original)

    delta_id = delta["delta_id"]
    payload_hash = delta_payload_hash(delta)
    existing_delta = _existing_delta(store, delta_id)
    if existing_delta is not None:
        existing_hash = existing_delta.get("payload_hash")
        if not existing_hash:
            return ({
                "status": "CONFLICT", "delta_id": delta_id, "store_revision": store["revision"],
                "conflicts": [_error("DELTA_ID_LEGACY_HASH_MISSING", "delta_id was applied without payload_hash; semantic identity cannot be proven")],
            }, original)
        if existing_hash != payload_hash:
            return ({
                "status": "CONFLICT", "delta_id": delta_id, "store_revision": store["revision"],
                "conflicts": [_error("DELTA_ID_CONTENT_CONFLICT", "delta_id was already applied with different semantic content", existing_payload_hash=existing_hash, incoming_payload_hash=payload_hash)],
            }, original)
        return ({
            "status": "IDEMPOTENT", "delta_id": delta_id, "store_revision": store["revision"], "payload_hash": payload_hash,
            "message": "same delta_id and semantic payload already applied; no mutation performed",
        }, original)

    if delta["base_revision"] != store["revision"]:
        return ({
            "status": "CONFLICT", "delta_id": delta_id, "store_revision": store["revision"],
            "conflicts": [_error("STALE_BASE_REVISION", "delta base_revision does not match canonical store revision", expected_revision=store["revision"], actual_revision=delta["base_revision"])],
        }, original)

    if not delta["operations"]:
        return ({
            "status": "NO_CHANGE", "delta_id": delta_id, "store_revision": store["revision"], "payload_hash": payload_hash,
            "no_change_reason": delta["no_change_reason"], "message": "artifact may change but Canonical mutation was not requested",
        }, original)

    working = copy.deepcopy(store)
    entity_ops = [(i, op) for i, op in enumerate(delta["operations"]) if op["op"] == "UPSERT_ENTITY"]
    provenance_ops = [(i, op) for i, op in enumerate(delta["operations"]) if op["op"] == "ADD_PROVENANCE"]
    relation_ops = [(i, op) for i, op in enumerate(delta["operations"]) if op["op"] == "UPSERT_RELATION"]

    for index, op in entity_ops:
        entity_id = op["id"]
        existing = working["entities"].get(entity_id)
        if existing is not None and existing.get("entity_type") != op["entity_type"]:
            return ({
                "status": "CONFLICT", "delta_id": delta_id, "store_revision": store["revision"],
                "conflicts": [_error("ENTITY_TYPE_MISMATCH", "existing entity_type differs from incoming entity_type", entity_id=entity_id, existing_type=existing.get("entity_type"), incoming_type=op["entity_type"])],
            }, original)
        if existing is None:
            entity = {
                "id": entity_id,
                "entity_type": op["entity_type"],
                "fields": copy.deepcopy(op.get("fields", {})),
                "truth_status": op.get("truth_status", "CANDIDATE"),
                "provenance": [],
            }
            _append_provenance(entity, _provenance(delta, op, index))
            working["entities"][entity_id] = entity
            continue

        changed = _changed_fields(existing, op.get("fields", {}))
        incoming_truth = op.get("truth_status")
        if existing.get("truth_status") == "CONFIRMED_BUSINESS" and op["evidence_class"] in NON_CONFIRMED_EVIDENCE:
            if changed:
                return ({
                    "status": "CONFLICT", "delta_id": delta_id, "store_revision": store["revision"],
                    "conflicts": [_error("BUSINESS_TRUTH_OVERWRITE_BLOCKED", "non-confirmed evidence cannot overwrite CONFIRMED_BUSINESS fields", entity_id=entity_id, changed_fields=changed, evidence_class=op["evidence_class"])],
                }, original)
            if incoming_truth and incoming_truth != "CONFIRMED_BUSINESS":
                return ({
                    "status": "CONFLICT", "delta_id": delta_id, "store_revision": store["revision"],
                    "conflicts": [_error("BUSINESS_TRUTH_STATUS_DOWNGRADE_BLOCKED", "non-confirmed evidence cannot downgrade CONFIRMED_BUSINESS truth_status", entity_id=entity_id, existing_truth_status="CONFIRMED_BUSINESS", incoming_truth_status=incoming_truth, evidence_class=op["evidence_class"])],
                }, original)
        existing.setdefault("fields", {}).update(copy.deepcopy(op.get("fields", {})))
        if incoming_truth:
            existing["truth_status"] = incoming_truth
        _append_provenance(existing, _provenance(delta, op, index))

    for index, op in provenance_ops:
        entity = working["entities"].get(op["id"])
        if entity is None:
            return ({
                "status": "CONFLICT", "delta_id": delta_id, "store_revision": store["revision"],
                "conflicts": [_error("MISSING_PROVENANCE_TARGET", "ADD_PROVENANCE target does not exist", entity_id=op["id"])],
            }, original)
        _append_provenance(entity, _provenance(delta, op, index))

    existing_relations = {_relation_key(row): row for row in working["relations"]}
    for index, op in relation_ops:
        missing = [entity_id for entity_id in [op["from"], op["to"]] if entity_id not in working["entities"]]
        if missing:
            return ({
                "status": "CONFLICT", "delta_id": delta_id, "store_revision": store["revision"],
                "conflicts": [_error("MISSING_RELATION_ENDPOINT", "relation endpoint does not exist", missing_entities=missing, relation={"from": op["from"], "kind": op["kind"], "to": op["to"]})],
            }, original)
        key = (op["from"], op["kind"], op["to"])
        provenance = _provenance(delta, op, index)
        relation = existing_relations.get(key)
        if relation is None:
            relation = {"from": op["from"], "kind": op["kind"], "to": op["to"], "provenance": [provenance]}
            working["relations"].append(relation)
            existing_relations[key] = relation
        elif provenance not in relation.setdefault("provenance", []):
            relation["provenance"].append(provenance)

    applied_at = now()
    working["revision"] = store["revision"] + 1
    working["updated_at"] = applied_at
    working["applied_deltas"].append({
        "delta_id": delta_id,
        "payload_hash": payload_hash,
        "revision": working["revision"],
        "stage": delta["stage"],
        "source_artifact": delta["source_artifact"],
        "operation_count": len(delta["operations"]),
        "applied_at": applied_at,
    })
    return ({
        "status": "APPLIED", "delta_id": delta_id, "payload_hash": payload_hash,
        "previous_revision": store["revision"], "store_revision": working["revision"],
        "operation_count": len(delta["operations"]), "entity_count": len(working["entities"]), "relation_count": len(working["relations"]),
    }, working)


def apply_delta_to_store(path: Path, delta: dict, *, dry_run: bool = False, lock_timeout_seconds: float = 10.0) -> tuple[dict, dict]:
    """Reload-under-lock, apply, and atomically persist.

    This closes the TOCTOU gap between validation and file replacement. The incoming
    `base_revision` is checked against the store *after the lock is acquired*.
    """
    if dry_run:
        store = load_store(path)
        return apply_delta(store, delta)
    with store_lock(path, timeout_seconds=lock_timeout_seconds):
        current = load_store(path)
        result, resulting = apply_delta(current, delta)
        if result["status"] == "APPLIED":
            save_store(path, resulting)
        return result, resulting


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Apply a minimal stage delta to the Canonical JSON store.")
    parser.add_argument("--store", default="sdlc/canonical/store.json")
    parser.add_argument("--delta", required=True)
    parser.add_argument("--result-out")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--lock-timeout-seconds", type=float, default=10.0)
    args = parser.parse_args(argv)

    store_path = Path(args.store)
    delta = load_json(Path(args.delta))
    if args.dry_run:
        store = load_store(store_path)
        result, _ = apply_delta(store, delta)
    else:
        try:
            result, _ = apply_delta_to_store(store_path, delta, lock_timeout_seconds=args.lock_timeout_seconds)
        except TimeoutError as exc:
            result = {"status": "CONFLICT", "delta_id": delta.get("delta_id"), "conflicts": [_error("STORE_LOCK_TIMEOUT", str(exc))]}

    if args.dry_run:
        result = {**result, "dry_run": True, "store_written": False}
    elif result["status"] == "APPLIED":
        result = {**result, "store_written": True, "write_mode": "LOCKED_ATOMIC_REPLACE"}
    else:
        result = {**result, "store_written": False}

    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.result_out:
        result_path = Path(args.result_out)
        result_path.parent.mkdir(parents=True, exist_ok=True)
        result_path.write_text(text, encoding="utf-8")
    print(text, end="")
    if result["status"] in {"APPLIED", "IDEMPOTENT", "NO_CHANGE"}:
        return 0
    if result["status"] == "CONFLICT":
        return 2
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
