#!/usr/bin/env python3
"""Generate Customer Views from the project-selected Tailoring Profile and template.

The renderer keeps one Canonical/Internal evidence projection path, but the final Markdown layout
comes from ``documents.customer.profile``. Customer views remain GENERATED_VIEW, become
PENDING_REVIEW/STALE_VIEW through the normal lifecycle, and never directly mutate Business Truth.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
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


RENDER = _load("customer_projection_renderer", "render_customer_document.py")
LIFE = _load("customer_projection_lifecycle", "projection_lifecycle_runtime.py")
CONFIG = _load("customer_projection_config", "runtime_config_v19.py")
TAILOR = _load("customer_projection_tailoring", "tailoring_runtime.py")

DEFAULT_CONTRACT = "sdlc/design/contracts/customer-document-contract.json"
DEFAULT_PROJECTION_CONFIG = "sdlc/config/customer-document-profile.example.json"
DEFAULT_CUSTOMER_PROFILE = "CUSTOMER_STANDARD_3"
DEFAULT_INTERNAL_PROFILE = "STANDARD_5"

TYPE_TO_ID = {
    "solution_agreement": "A01",
    "delivery_scope": "A02",
    "acceptance_handover": "A03",
    "A01": "A01",
    "A02": "A02",
    "A03": "A03",
}


def _repo_file(root: Path, raw: str) -> tuple[Path, str]:
    path = Path(raw)
    path = path if path.is_absolute() else root / path
    path = path.resolve()
    try:
        rel = path.relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError(f"customer projection path escapes project root: {raw}") from exc
    if not path.is_file():
        raise ValueError(f"customer projection file not found: {rel}")
    return path, rel


def _project_settings(
    root: Path,
    *,
    contract_path: str | None,
    projection_config_path: str | None,
    tailoring_profile_id: str | None,
) -> dict[str, Any]:
    resolved = CONFIG.resolve_runtime_config(root)
    project = resolved.get("project") or {}
    customer_profile_id = tailoring_profile_id or str(
        CONFIG.nested(project, "documents", "customer", "profile", default=DEFAULT_CUSTOMER_PROFILE)
        or DEFAULT_CUSTOMER_PROFILE
    )
    internal_profile_id = str(
        CONFIG.nested(project, "documents", "internal", "profile", default=DEFAULT_INTERNAL_PROFILE)
        or DEFAULT_INTERNAL_PROFILE
    )
    contract_raw = contract_path or str(
        CONFIG.nested(project, "documents", "customer", "projection_contract", default=DEFAULT_CONTRACT)
        or DEFAULT_CONTRACT
    )
    projection_raw = projection_config_path or str(
        CONFIG.nested(project, "documents", "customer", "projection_config", default=DEFAULT_PROJECTION_CONFIG)
        or DEFAULT_PROJECTION_CONFIG
    )
    contract_file, contract_rel = _repo_file(root, contract_raw)
    projection_file, projection_rel = _repo_file(root, projection_raw)
    customer_profile, customer_profile_path = TAILOR.load_profile(root, customer_profile_id)
    internal_profile, internal_profile_path = TAILOR.load_profile(root, internal_profile_id)
    return {
        "project": project,
        "customer_profile_id": customer_profile_id,
        "customer_profile": customer_profile,
        "customer_profile_path": customer_profile_path.relative_to(root).as_posix(),
        "internal_profile_id": internal_profile_id,
        "internal_profile": internal_profile,
        "internal_profile_path": internal_profile_path.relative_to(root).as_posix(),
        "contract": RENDER.load(contract_file),
        "contract_path": contract_rel,
        "projection_config": RENDER.load(projection_file),
        "projection_config_path": projection_rel,
    }


def _render_output_path(row: dict[str, Any], target: str) -> str:
    raw = str(row.get("output_path") or "").strip()
    if not raw:
        raise ValueError(f"customer artifact {row.get('id') or '<unknown>'} output_path is required")
    safe_target = TAILOR._safe_target(target)
    return raw.replace("{target}", safe_target).replace("{artifact_id}", str(row.get("id") or "artifact"))


def _internal_expected_paths(root: Path, target: str, profile: dict[str, Any]) -> dict[Path, dict[str, Any]]:
    rows: dict[Path, dict[str, Any]] = {}
    for artifact_id, value in (profile.get("artifacts") or {}).items():
        if not isinstance(value, dict):
            continue
        row = dict(value)
        row["id"] = str(artifact_id)
        raw = str(row.get("output_path") or "").strip()
        if not raw:
            continue
        rel = raw.replace("{target}", TAILOR._safe_target(target)).replace("{artifact_id}", str(artifact_id))
        rows[(root / rel).resolve()] = row
    return rows


def _annotate_profile_stages(
    root: Path,
    *,
    target: str,
    document_type: str,
    contract: dict[str, Any],
    internal_profile: dict[str, Any],
    artifacts: list[dict[str, Any]],
) -> None:
    """Annotate Tailored Internal documents without forcing Stage names into human filenames.

    The selected Internal Profile already knows which compatibility stages feed each human document.
    For a requested Customer View we choose the latest stage that is valid for both profiles. This
    keeps customer projection profile-neutral and avoids making users rename documents with Stage IDs.
    """
    resolved = RENDER.resolve_document_type(document_type, contract)
    allowed = set(str(x).upper() for x in contract["document_types"][resolved].get("stages", []))
    expected = _internal_expected_paths(root, target, internal_profile)
    for artifact in artifacts:
        if artifact.get("stage"):
            continue
        source = str(artifact.get("source") or "").split("#", 1)[0]
        if not source:
            continue
        row = expected.get(Path(source).resolve())
        if not row:
            continue
        stages = [str(x).upper() for x in (row.get("sources") or {}).get("stages", [])]
        matches = [stage for stage in stages if stage in allowed]
        if matches:
            artifact["stage"] = max(matches, key=lambda stage: RENDER.STAGE_ORDER.get(stage, -1))
            artifact["tailoring_artifact_id"] = row["id"]


def _placeholder_name(section: str) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣]+", "_", section).strip("_")


def _optional_appendix(document_type: str, contract: dict, profile: dict, projection: dict[str, Any]) -> str:
    rows: list[str] = []
    for section_id in RENDER.enabled_optional(document_type, contract, profile):
        heading = section_id.replace("_", " ")
        content = str(projection.get(heading) or "").strip()
        if content:
            rows.extend([f"### {heading}", content, ""])
    return "\n".join(rows).strip()


def _render_selected_template(
    template_text: str,
    *,
    document_type: str,
    contract: dict,
    profile: dict,
    projection: dict[str, Any],
) -> str:
    replacements = {
        "short_name": str(projection.get("_short_name") or "프로젝트 변경"),
        "customer_purpose": str(projection.get("문서 목적") or ""),
        "customer_summary": str(projection.get("한눈에 보기") or ""),
        "customer_questions": str(projection.get("고객과 함께 확인할 내용") or ""),
        "agreed_items": str(projection.get("합의된 내용") or ""),
        "open_items": str(projection.get("미확정 사항") or ""),
        "next_steps": str(projection.get("다음 단계") or ""),
        "optional_appendix": _optional_appendix(document_type, contract, profile, projection),
    }
    for section, value in projection.items():
        if section.startswith("_"):
            continue
        replacements[f"section_{_placeholder_name(section)}"] = str(value)
    text = template_text
    for key, value in replacements.items():
        text = text.replace("{{" + key + "}}", value)
    unresolved = sorted(set(re.findall(r"\{\{[^{}]+\}\}", text)))
    if unresolved:
        raise ValueError("unresolved customer template placeholder(s): " + ", ".join(unresolved))
    return text.rstrip() + "\n"


def generate(
    root: Path,
    *,
    target: str,
    document_type: str,
    inputs: list[str],
    out: str,
    short_name: str | None = None,
    contract_path: str | None = None,
    profile_path: str | None = None,
    tailoring_profile_id: str | None = None,
) -> dict:
    root = root.resolve()
    settings = _project_settings(
        root,
        contract_path=contract_path,
        projection_config_path=profile_path,
        tailoring_profile_id=tailoring_profile_id,
    )
    contract = settings["contract"]
    profile = settings["projection_config"]
    resolved_type = RENDER.resolve_document_type(document_type, contract)
    customer_rows = settings["customer_profile"].get("artifacts") or {}
    selected = customer_rows.get(resolved_type)
    if not isinstance(selected, dict):
        raise ValueError(
            f"customer tailoring profile {settings['customer_profile_id']} has no artifact for {resolved_type}"
        )
    if str(selected.get("audience") or "").upper() != "CUSTOMER":
        raise ValueError(f"customer artifact {resolved_type} audience must be CUSTOMER")
    if str(selected.get("authoring") or "").upper() != "GENERATED_VIEW":
        raise ValueError(f"customer artifact {resolved_type} authoring must be GENERATED_VIEW")
    template_file, template_rel = _repo_file(root, str(selected.get("template") or ""))

    artifacts: list[dict[str, Any]] = []
    for raw in inputs:
        path = Path(raw)
        path = path if path.is_absolute() else root / path
        artifacts.extend(RENDER.load_artifact_input(path, contract))
    _annotate_profile_stages(
        root,
        target=target,
        document_type=resolved_type,
        contract=contract,
        internal_profile=settings["internal_profile"],
        artifacts=artifacts,
    )
    projection = RENDER.project(resolved_type, contract, profile, artifacts, short_name)
    text = _render_selected_template(
        template_file.read_text(encoding="utf-8"),
        document_type=resolved_type,
        contract=contract,
        profile=profile,
        projection=projection,
    )

    output = Path(out)
    output = output if output.is_absolute() else root / output
    output = output.resolve()
    try:
        output_rel = output.relative_to(root).as_posix()
    except ValueError as exc:
        raise ValueError("customer output path escapes project root") from exc
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")

    artifact_id = TYPE_TO_ID.get(document_type, TYPE_TO_ID.get(resolved_type, resolved_type))
    metadata = LIFE.register_generated(
        root,
        target=target,
        artifact_id=artifact_id,
        artifact_path=output_rel,
        audience="CUSTOMER",
        profile_id=settings["customer_profile_id"],
    )
    return {
        "status": "CUSTOMER_VIEW_GENERATED",
        "target_id": target,
        "document_type": resolved_type,
        "artifact_id": artifact_id,
        "artifact_path": output_rel,
        "template_path": template_rel,
        "customer_tailoring_profile": settings["customer_profile_id"],
        "customer_tailoring_profile_path": settings["customer_profile_path"],
        "internal_tailoring_profile": settings["internal_profile_id"],
        "projection_contract": settings["contract_path"],
        "projection_config": settings["projection_config_path"],
        "source_count": projection.get("_source_count", 0),
        "source_stages": projection.get("_source_stages", []),
        "lifecycle": metadata["lifecycle"],
        "generated_from_revision": metadata["generated_from_revision"],
        "business_truth_authority": False,
        "customer_edit_auto_updates_canonical": False,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Generate a customer view using the selected Tailoring Profile template.")
    ap.add_argument("--root", default=".")
    ap.add_argument("--target", required=True)
    ap.add_argument("--type", required=True)
    ap.add_argument("--input", action="append", default=[])
    ap.add_argument("--out", required=True)
    ap.add_argument("--short-name")
    ap.add_argument("--contract", help="Override documents.customer.projection_contract")
    ap.add_argument("--profile", help="Override documents.customer.projection_config")
    ap.add_argument("--tailoring-profile", help="Override documents.customer.profile for one run")
    args = ap.parse_args(argv)
    try:
        result = generate(
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
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAILED", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
