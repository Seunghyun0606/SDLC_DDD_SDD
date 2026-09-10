#!/usr/bin/env python3
"""Safe official customer-view facade.

The low-level customer projection renderer remains reusable, but the public Harness entrypoint must
not overwrite final-reviewed or manually edited customer wording. One-off ``--out`` previews also
use independent lifecycle metadata so they cannot replace the official artifact's tracking record.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


BASE = _load("customer_view_safe_base", "customer_projection_runtime.py")
LIFE = BASE.LIFE
TAILOR = BASE.TAILOR


def _output_abs(root: Path, raw: str) -> tuple[Path, str]:
    path = Path(raw)
    path = path if path.is_absolute() else root / path
    path = path.resolve()
    try:
        rel = path.relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError("customer output path escapes project root") from exc
    return path, rel


def _load_metadata(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _target_exists(root: Path, target: str) -> bool:
    store = TAILOR.load_store(root)
    return isinstance((store.get("entities") or {}).get(target), dict)


def _resolve_selection(
    root: Path,
    *,
    target: str,
    document_type: str,
    contract_path: str | None,
    profile_path: str | None,
    tailoring_profile_id: str | None,
) -> tuple[dict[str, Any], str, dict[str, Any], str, str]:
    settings = BASE._project_settings(
        root,
        contract_path=contract_path,
        projection_config_path=profile_path,
        tailoring_profile_id=tailoring_profile_id,
    )
    artifact_id, selected, semantic_type = BASE._profile_artifact(
        settings["customer_profile"], document_type, settings["contract"]
    )
    default_output = BASE._render_output_path(selected, target, artifact_id)
    return settings, artifact_id, selected, semantic_type, default_output


def _overwrite_block(root: Path, target: str, artifact_id: str) -> dict[str, Any] | None:
    metadata_path = LIFE.metadata_path(root, target, artifact_id)
    row = _load_metadata(metadata_path)
    if not row:
        return None
    raw_lifecycle = str(row.get("lifecycle") or "").upper()
    current_state = LIFE.state(root, row)
    if raw_lifecycle == "FINAL_REVIEW":
        return {
            "status": "CUSTOMER_VIEW_OVERWRITE_BLOCKED",
            "target_id": target,
            "artifact_id": artifact_id,
            "reason": "고객 최종 검토 문구가 보존되어 있어 정식 문서를 자동 덮어쓸 수 없습니다.",
            "current_state": current_state,
            "artifact_path": row.get("artifact_path"),
            "canonical_mutated": False,
            "next_action": "현재 문서를 검토하고, 비교 초안이 필요하면 --out으로 별도 미리보기를 생성하세요. 업무 의미가 바뀌었다면 /change 또는 /work 경계부터 처리하세요.",
        }
    if current_state == "MANUAL_EDIT_DETECTED":
        return {
            "status": "CUSTOMER_VIEW_OVERWRITE_BLOCKED",
            "target_id": target,
            "artifact_id": artifact_id,
            "reason": "사람이 수정한 고객문서가 감지되어 정식 문서를 자동 덮어쓸 수 없습니다.",
            "current_state": current_state,
            "artifact_path": row.get("artifact_path"),
            "canonical_mutated": False,
            "next_action": "수정 의미를 확인한 뒤 표현 수정이면 문구를 보존하고, 업무 의미 변경이면 /change로 반영하세요. 비교 초안은 --out으로 별도 생성할 수 있습니다.",
        }
    return None


def _preview_artifact_id(artifact_id: str, output_rel: str) -> str:
    suffix = hashlib.sha256(output_rel.encode("utf-8")).hexdigest()[:10]
    return f"{artifact_id}__preview__{suffix}"


def generate_safe(
    root: Path,
    *,
    target: str,
    document_type: str,
    inputs: list[str],
    out: str | None = None,
    short_name: str | None = None,
    contract_path: str | None = None,
    profile_path: str | None = None,
    tailoring_profile_id: str | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    if not _target_exists(root, target):
        return {
            "status": "CUSTOMER_VIEW_TARGET_NOT_FOUND",
            "target_id": target,
            "canonical_mutated": False,
            "next_action": "새 요구사항 한두 건은 rq-add, 대량 요구사항 파일은 intake로 먼저 RQ를 생성하세요.",
        }

    settings, artifact_id, _selected, _semantic_type, default_output = _resolve_selection(
        root,
        target=target,
        document_type=document_type,
        contract_path=contract_path,
        profile_path=profile_path,
        tailoring_profile_id=tailoring_profile_id,
    )
    default_abs, default_rel = _output_abs(root, default_output)
    requested_abs, requested_rel = _output_abs(root, out or default_output)
    is_preview = out is not None and requested_abs != default_abs

    if not is_preview:
        blocked = _overwrite_block(root, target, artifact_id)
        if blocked:
            return blocked
        return BASE.generate(
            root,
            target=target,
            document_type=document_type,
            inputs=inputs,
            out=default_rel,
            short_name=short_name,
            contract_path=contract_path,
            profile_path=profile_path,
            tailoring_profile_id=tailoring_profile_id,
        )

    # BASE.generate registers metadata under the official artifact id. Preserve that record while
    # still reusing the same rendering implementation, then register preview metadata separately.
    official_meta = LIFE.metadata_path(root, target, artifact_id)
    previous_metadata = official_meta.read_bytes() if official_meta.is_file() else None
    try:
        result = BASE.generate(
            root,
            target=target,
            document_type=document_type,
            inputs=inputs,
            out=requested_rel,
            short_name=short_name,
            contract_path=contract_path,
            profile_path=profile_path,
            tailoring_profile_id=tailoring_profile_id,
        )
    finally:
        if previous_metadata is None:
            if official_meta.is_file():
                official_meta.unlink()
        else:
            official_meta.parent.mkdir(parents=True, exist_ok=True)
            official_meta.write_bytes(previous_metadata)

    preview_id = _preview_artifact_id(artifact_id, requested_rel)
    preview_metadata = LIFE.register_generated(
        root,
        target=target,
        artifact_id=preview_id,
        artifact_path=requested_rel,
        audience="CUSTOMER",
        profile_id=settings["customer_profile_id"],
    )
    result.update({
        "status": "CUSTOMER_VIEW_PREVIEW_GENERATED",
        "preview": True,
        "official_artifact_id": artifact_id,
        "artifact_id": preview_id,
        "customer_artifact_id": artifact_id,
        "official_artifact_path": default_rel,
        "lifecycle_artifact_id": preview_id,
        "lifecycle": preview_metadata["lifecycle"],
        "generated_from_revision": preview_metadata["generated_from_revision"],
        "official_lifecycle_preserved": True,
    })
    return result


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Safely generate a Customer view without overwriting reviewed human wording.")
    ap.add_argument("--root", default=".")
    ap.add_argument("--target", required=True)
    ap.add_argument("--type", required=True, help="Customer artifact id or semantic document type")
    ap.add_argument("--input", action="append", default=[])
    ap.add_argument("--out", help="Create a separate preview when this differs from the profile output_path")
    ap.add_argument("--short-name")
    ap.add_argument("--contract", help="Override documents.customer.projection_contract")
    ap.add_argument("--profile", help="Override documents.customer.projection_config")
    ap.add_argument("--tailoring-profile", help="Override documents.customer.profile for one run")
    args = ap.parse_args(argv)
    try:
        result = generate_safe(
            Path(args.root).resolve(),
            target=args.target,
            document_type=args.type,
            inputs=args.input,
            out=args.out,
            short_name=args.short_name,
            contract_path=args.contract,
            profile_path=args.profile,
            tailoring_profile_id=args.tailoring_profile,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("status") in {"CUSTOMER_VIEW_GENERATED", "CUSTOMER_VIEW_PREVIEW_GENERATED"} else 3
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAILED", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
