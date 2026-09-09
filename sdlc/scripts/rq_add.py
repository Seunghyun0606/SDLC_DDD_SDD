#!/usr/bin/env python3
"""Add one new RQ from a direct user request without re-running spreadsheet intake.

This is an incremental project entrypoint, not a replacement for bulk Requirement Intake.
The original request is preserved, the new RQ starts as CANDIDATE, and existing RQs are
never silently modified. PM worklist refresh is best-effort after the Canonical write.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
DEFAULT_STORE = "sdlc/canonical/store.json"


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


APPLY = _load("rq_add_canonical", "apply_canonical_delta.py")


def _normalize(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", str(value or "")).split()).casefold()


def _prompt_key(request: str) -> str:
    return "prompt:" + hashlib.sha256(_normalize(request).encode("utf-8")).hexdigest()


def _source_hash(request: str) -> str:
    return "sha256:" + hashlib.sha256(request.encode("utf-8")).hexdigest()


def _next_rq_id(store: dict[str, Any]) -> str:
    pattern = re.compile(r"^RQ-(\d+)$")
    numbers = [
        int(match.group(1))
        for entity_id in (store.get("entities") or {})
        if (match := pattern.match(str(entity_id)))
    ]
    return f"RQ-{max(numbers or [0]) + 1:03d}"


def _default_title(request: str) -> str:
    one_line = " ".join(request.split())
    if len(one_line) <= 60:
        return one_line
    return one_line[:57].rstrip() + "..."


def _rq_entities(store: dict[str, Any]):
    for entity_id, entity in (store.get("entities") or {}).items():
        if str((entity or {}).get("entity_type") or "").upper() == "RQ":
            yield str(entity_id), entity


def _existing_by_prompt(store: dict[str, Any], prompt_key: str) -> str | None:
    for entity_id, entity in _rq_entities(store):
        fields = entity.get("fields") or {}
        if str(fields.get("direct_requirement_key") or "") == prompt_key:
            return entity_id
    return None


def _external_ids(entity: dict[str, Any]) -> set[str]:
    fields = entity.get("fields") or {}
    values: set[str] = set()
    raw = fields.get("external_requirement_ids")
    if isinstance(raw, list):
        values.update(str(value).strip() for value in raw if str(value).strip())
    elif raw not in (None, ""):
        values.add(str(raw).strip())
    one = fields.get("external_requirement_id")
    if one not in (None, ""):
        values.add(str(one).strip())
    return values


def _assert_external_id_available(store: dict[str, Any], external_id: str | None) -> None:
    if not external_id:
        return
    wanted = external_id.strip()
    for entity_id, entity in _rq_entities(store):
        if wanted in _external_ids(entity):
            raise ValueError(f"external requirement id already belongs to {entity_id}: {wanted}")


def _build_delta(store: dict[str, Any], *, target: str, title: str, request: str,
                 external_id: str | None, prompt_key: str) -> dict[str, Any]:
    source_hash = _source_hash(request)
    external_ids = [external_id.strip()] if external_id and external_id.strip() else []
    fields: dict[str, Any] = {
        "name": title,
        "title": title,
        "original_requirement": request,
        "external_requirement_ids": external_ids,
        "direct_requirement_key": prompt_key,
        "source_kind": "DIRECT_USER_REQUEST",
        "current_problem": "OPEN",
        "desired_result": "OPEN",
        "business_rules": "OPEN",
        "review_status": "AGENT_DRAFT_THEN_HUMAN_CONFIRM",
    }
    op = {
        "op": "UPSERT_ENTITY",
        "id": target,
        "entity_type": "RQ",
        "fields": fields,
        "truth_status": "CANDIDATE",
        "evidence_class": "GIVEN",
        "locator": "direct-user-request",
        "source_hash": source_hash,
        "note": "Direct user requirement request preserved as a Candidate; not Business Truth confirmation.",
    }
    token = f"{prompt_key}\x1f{external_id or ''}".encode("utf-8")
    return {
        "schema_version": 1,
        "delta_id": "RQADD-" + hashlib.sha256(token).hexdigest()[:24],
        "base_revision": int(store.get("revision") or 0),
        "stage": "INTAKE",
        "source_artifact": "DIRECT_USER_REQUEST",
        "operations": [op],
    }


def _is_stale_revision(result: dict[str, Any]) -> bool:
    return result.get("status") == "CONFLICT" and any(
        row.get("code") == "STALE_BASE_REVISION" for row in result.get("conflicts", [])
    )


def _refresh_worklist(root: Path) -> dict[str, Any]:
    try:
        worklist = _load("rq_add_worklist", "rq_worklist.py")
        return worklist.refresh(root)
    except Exception as exc:  # Canonical add must not be rolled back by a derived-view failure.
        return {
            "status": "RQ_WORKLIST_REFRESH_FAILED",
            "error": str(exc),
            "canonical_rollback": False,
        }


def add_requirement(root: Path, *, request: str, title: str | None = None,
                    external_id: str | None = None, store_path: str = DEFAULT_STORE,
                    refresh_worklist: bool = True) -> dict[str, Any]:
    root = root.resolve()
    request = str(request or "").strip()
    if not request:
        raise ValueError("request text is required")
    title = str(title or "").strip() or _default_title(request)
    if not title:
        raise ValueError("title could not be derived from request")
    external_id = str(external_id or "").strip() or None
    prompt_key = _prompt_key(request)
    store_file = Path(store_path)
    store_file = store_file if store_file.is_absolute() else root / store_file

    # Retry only optimistic-revision races. Other conflicts are returned fail-closed.
    for attempt in range(3):
        store = APPLY.load_store(store_file)
        existing = _existing_by_prompt(store, prompt_key)
        if existing:
            result = {
                "status": "RQ_ALREADY_EXISTS",
                "target": existing,
                "canonical_mutated": False,
                "original_request_preserved": True,
                "next_command": f"python sdlc/scripts/harness.py work --target {existing}",
            }
            if refresh_worklist:
                result["worklist"] = _refresh_worklist(root)
            return result

        _assert_external_id_available(store, external_id)
        target = _next_rq_id(store)
        delta = _build_delta(
            store,
            target=target,
            title=title,
            request=request,
            external_id=external_id,
            prompt_key=prompt_key,
        )
        apply_result, resulting = APPLY.apply_delta_to_store(store_file, delta)
        if apply_result.get("status") in {"APPLIED", "IDEMPOTENT"}:
            result = {
                "status": "RQ_ADDED" if apply_result.get("status") == "APPLIED" else "RQ_ALREADY_EXISTS",
                "target": target,
                "title": title,
                "truth_status": "CANDIDATE",
                "canonical_revision": int(resulting.get("revision") or 0),
                "canonical_mutated": apply_result.get("status") == "APPLIED",
                "original_request_preserved": True,
                "external_requirement_id": external_id,
                "next_command": f"python sdlc/scripts/harness.py work --target {target}",
                "change_existing_requirement": f"python sdlc/scripts/harness.py change --target {target}",
            }
            if refresh_worklist:
                result["worklist"] = _refresh_worklist(root)
            return result
        if _is_stale_revision(apply_result) and attempt < 2:
            continue
        raise ValueError(f"Canonical RQ add failed: {apply_result}")

    raise ValueError("Canonical RQ add failed after revision retries")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Add one new RQ from a direct prompt without re-running spreadsheet intake."
    )
    parser.add_argument("request_text", nargs="?", help="Original requirement text")
    parser.add_argument("--request", dest="request_option", help="Original requirement text")
    parser.add_argument("--title", help="Short display title; original request is preserved separately")
    parser.add_argument("--external-id", help="Optional customer/external requirement identifier")
    parser.add_argument("--root", default=".")
    parser.add_argument("--store", default=DEFAULT_STORE)
    parser.add_argument("--no-worklist-refresh", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    if args.request_text and args.request_option and args.request_text.strip() != args.request_option.strip():
        print(json.dumps({
            "status": "RQ_ADD_FAILED",
            "error": "provide requirement text either positionally or with --request, not two different values",
        }, ensure_ascii=False, indent=2))
        return 2
    request = args.request_option or args.request_text or ""
    try:
        result = add_requirement(
            Path(args.root),
            request=request,
            title=args.title,
            external_id=args.external_id,
            store_path=args.store,
            refresh_worklist=not args.no_worklist_refresh,
        )
    except (OSError, ValueError, json.JSONDecodeError, TimeoutError) as exc:
        print(json.dumps({"status": "RQ_ADD_FAILED", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
