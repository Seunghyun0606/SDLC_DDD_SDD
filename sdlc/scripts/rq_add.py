#!/usr/bin/env python3
"""Add one new RQ from a direct user request without re-running spreadsheet intake.

This is an incremental SINGLE_WRITER project entrypoint, not a replacement for bulk Requirement
Intake. RQ sequence is derived from the current Canonical JSON file, matching the existing intake
ID style. Canonical write is locked/atomic, but sequence allocation is not a multi-writer service.
The original request is preserved, the new RQ starts as CANDIDATE, and missing details stay OPEN.
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


def _clean(value: str | None) -> str | None:
    text = str(value or "").strip()
    return text or None


def _normalize(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", str(value or "")).split()).casefold()


def _prompt_key(request: str) -> str:
    return "prompt:" + hashlib.sha256(_normalize(request).encode("utf-8")).hexdigest()


def _source_hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _next_rq_id(store: dict[str, Any]) -> str:
    pattern = re.compile(r"^RQ-(\d+)$")
    numbers = [
        int(match.group(1))
        for entity_id, entity in (store.get("entities") or {}).items()
        if str((entity or {}).get("entity_type") or "").upper() == "RQ"
        and (match := pattern.match(str(entity_id)))
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


def _same_title_candidates(store: dict[str, Any], title: str) -> list[str]:
    wanted_title = _normalize(title)
    if not wanted_title:
        return []
    rows: list[str] = []
    for entity_id, entity in _rq_entities(store):
        fields = entity.get("fields") or {}
        existing_title = _normalize(fields.get("name") or fields.get("title") or "")
        if existing_title == wanted_title:
            rows.append(entity_id)
    return sorted(set(rows))


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
                 background: str | None, desired_result: str | None, scope: str | None,
                 external_id: str | None, prompt_key: str) -> dict[str, Any]:
    payload = {
        "title": title,
        "request": request,
        "background": background,
        "desired_result": desired_result,
        "scope": scope,
        "external_id": external_id,
    }
    source_hash = _source_hash(payload)
    external_ids = [external_id] if external_id else []
    fields: dict[str, Any] = {
        "name": title,
        "title": title,
        "original_requirement": request,
        "external_requirement_ids": external_ids,
        "direct_requirement_key": prompt_key,
        "source_kind": "DIRECT_USER_REQUEST",
        "creation_method": "PROMPT_RQ_ADD",
        "current_problem": background or "OPEN",
        "desired_result": desired_result or "OPEN",
        "scope": scope or "OPEN",
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
        "locator": "prompt:rq-add",
        "source_hash": source_hash,
        "note": "Direct user requirement seed. Missing business details remain OPEN; this does not confirm Business Truth.",
    }
    token = json.dumps(
        {"target": target, "payload": payload, "base_revision": int(store.get("revision") or 0)},
        ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    return {
        "schema_version": 1,
        "delta_id": "RQADD-" + hashlib.sha256(token).hexdigest()[:24],
        "base_revision": int(store.get("revision") or 0),
        "stage": "INTAKE",
        "source_artifact": "PROMPT_RQ_ADD",
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
    except Exception as exc:  # Derived-view failure must not roll back a successful RQ write.
        return {
            "status": "RQ_WORKLIST_REFRESH_FAILED",
            "error": str(exc),
            "canonical_rollback": False,
        }


def add_requirement(root: Path, *, request: str, title: str | None = None,
                    background: str | None = None, desired_result: str | None = None,
                    scope: str | None = None, external_id: str | None = None,
                    allow_duplicate: bool = False, store_path: str = DEFAULT_STORE,
                    refresh_worklist: bool = True) -> dict[str, Any]:
    root = root.resolve()
    request = _clean(request) or ""
    if not request:
        raise ValueError("요청 내용(--request)은 필수입니다.")
    title = _clean(title) or _default_title(request)
    if not title:
        raise ValueError("요구사항명을 만들 수 없습니다. --title을 지정하세요.")
    background = _clean(background)
    desired_result = _clean(desired_result)
    scope = _clean(scope)
    external_id = _clean(external_id)
    prompt_key = _prompt_key(request)
    store_file = Path(store_path)
    store_file = store_file if store_file.is_absolute() else root / store_file

    store = APPLY.load_store(store_file)

    # Exact same direct prompt is idempotent even if a later caller supplies a different display title.
    # Return the existing target without mutating Canonical or consuming a new RQ sequence number.
    existing = _existing_by_prompt(store, prompt_key)
    if existing:
        result = {
            "status": "RQ_ALREADY_EXISTS",
            "created": False,
            "target": existing,
            "canonical_mutated": False,
            "original_request_preserved": True,
            "sequence_policy": "SINGLE_WRITER_FILE_DERIVED",
            "message": "같은 요청 원문으로 이미 생성된 RQ가 있어 기존 RQ를 사용합니다.",
            "next_command": f"python sdlc/scripts/harness.py work --target {existing}",
            "change_existing_requirement": f"python sdlc/scripts/harness.py change --target {existing}",
        }
        if refresh_worklist:
            result["worklist"] = _refresh_worklist(root)
        return result

    # Same display title with a different original request may be a real duplicate or a separate request.
    # Do not guess: require review unless the caller explicitly confirmed that a separate RQ is intended.
    title_duplicates = _same_title_candidates(store, title)
    if title_duplicates and not allow_duplicate:
        return {
            "status": "RQ_ADD_DUPLICATE_REVIEW_REQUIRED",
            "created": False,
            "possible_duplicates": title_duplicates,
            "message": "같은 요구사항명의 RQ가 이미 있습니다. 기존 RQ 변경인지 별도 신규 RQ인지 확인하세요.",
            "canonical_mutated": False,
            "sequence_policy": "SINGLE_WRITER_FILE_DERIVED",
        }

    _assert_external_id_available(store, external_id)
    target = _next_rq_id(store)
    delta = _build_delta(
        store,
        target=target,
        title=title,
        request=request,
        background=background,
        desired_result=desired_result,
        scope=scope,
        external_id=external_id,
        prompt_key=prompt_key,
    )
    apply_result, resulting = APPLY.apply_delta_to_store(store_file, delta)
    if _is_stale_revision(apply_result):
        return {
            "status": "RQ_ADD_CONFLICT_RETRY_REQUIRED",
            "created": False,
            "planned_target": target,
            "canonical_mutated": False,
            "sequence_policy": "SINGLE_WRITER_FILE_DERIVED",
            "message": "다른 RQ 생성/기준 정보 변경과 충돌했습니다. 현재는 RQ 생성 담당자 한 명이 앞 작업 완료 후 다시 실행해야 합니다.",
        }
    if apply_result.get("status") not in {"APPLIED", "IDEMPOTENT"}:
        raise ValueError(f"Canonical RQ add failed: {apply_result}")

    result = {
        "status": "RQ_ADDED" if apply_result.get("status") == "APPLIED" else "RQ_ALREADY_EXISTS",
        "created": apply_result.get("status") == "APPLIED",
        "target": target,
        "title": title,
        "truth_status": "CANDIDATE",
        "canonical_revision": int(resulting.get("revision") or 0),
        "canonical_mutated": apply_result.get("status") == "APPLIED",
        "original_request_preserved": True,
        "external_requirement_id": external_id,
        "open_fields": [
            label for label, value in {
                "현재 문제/배경": background,
                "기대 결과": desired_result,
                "적용 범위": scope,
            }.items() if not value
        ],
        "next_command": f"python sdlc/scripts/harness.py work --target {target}",
        "change_existing_requirement": f"python sdlc/scripts/harness.py change --target {target}",
        "sequence_policy": "SINGLE_WRITER_FILE_DERIVED",
    }
    if refresh_worklist:
        result["worklist"] = _refresh_worklist(root)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="자연어로 추가 RQ 하나를 생성합니다. 대량 요구사항은 XLSX Intake를 사용합니다."
    )
    parser.add_argument("request_text", nargs="?", help="요청 원문")
    parser.add_argument("--request", dest="request_option", help="요청 원문")
    parser.add_argument("--title", help="짧은 요구사항명; 생략 시 원문에서 중립적으로 생성")
    parser.add_argument("--background", help="현재 문제 또는 요청 배경")
    parser.add_argument("--desired-result", help="완료 후 기대하는 업무 결과")
    parser.add_argument("--scope", help="알고 있는 적용 범위")
    parser.add_argument("--external-id", help="고객/외부 요구사항 ID가 있으면 기록")
    parser.add_argument("--allow-duplicate", action="store_true", help="중복 후보를 확인한 뒤 의도적으로 별도 RQ를 만들 때만 사용")
    parser.add_argument("--root", default=".")
    parser.add_argument("--store", default=DEFAULT_STORE)
    parser.add_argument("--no-worklist-refresh", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    if args.request_text and args.request_option and args.request_text.strip() != args.request_option.strip():
        print(json.dumps({
            "status": "RQ_ADD_FAILED",
            "error": "요청 원문은 위치 인자 또는 --request 중 하나로만 전달하세요.",
        }, ensure_ascii=False, indent=2))
        return 2
    request = args.request_option or args.request_text or ""
    try:
        result = add_requirement(
            Path(args.root),
            request=request,
            title=args.title,
            background=args.background,
            desired_result=args.desired_result,
            scope=args.scope,
            external_id=args.external_id,
            allow_duplicate=args.allow_duplicate,
            store_path=args.store,
            refresh_worklist=not args.no_worklist_refresh,
        )
    except (OSError, ValueError, json.JSONDecodeError, TimeoutError) as exc:
        print(json.dumps({"status": "RQ_ADD_FAILED", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") in {"RQ_ADDED", "RQ_ALREADY_EXISTS"} else 3


if __name__ == "__main__":
    raise SystemExit(main())
