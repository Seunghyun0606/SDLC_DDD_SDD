#!/usr/bin/env python3
"""Generate Customer Projection independently from Engineering document topology.

Customer assembly is driven by the selected Customer Profile plus semantic artifact metadata.
It never resolves an Engineering/Internal profile, expected Engineering filename, artifact order, or
Engineering document count. Legacy Stage inference remains available inside the renderer only as a
compatibility fallback for old inputs that do not yet carry semantic metadata.

Business Truth authority remains Canonical. Source/Engineering/Test evidence may enrich a Customer
view but can never overwrite Confirmed Business Truth through this runtime.
"""
from __future__ import annotations

import argparse
import copy
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
CONFIG = _load("customer_projection_config", "project_config.py")
TAILOR = _load("customer_projection_tailoring", "tailoring_runtime.py")

DEFAULT_CONTRACT = "sdlc/design/contracts/customer-document-contract.json"
DEFAULT_PROJECTION_CONFIG = "sdlc/config/customer-document-profile.json"
DEFAULT_CUSTOMER_PROFILE = "CUSTOMER_STANDARD_3"


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
    return {
        "project": project,
        "customer_profile_id": customer_profile_id,
        "customer_profile": customer_profile,
        "customer_profile_path": customer_profile_path.relative_to(root).as_posix(),
        "contract": RENDER.load(contract_file),
        "contract_path": contract_rel,
        "projection_config": RENDER.load(projection_file),
        "projection_config_path": projection_rel,
    }


def _profile_artifact(
    profile: dict[str, Any], requested: str, contract: dict[str, Any]
) -> tuple[str, dict[str, Any], str]:
    """Resolve a Customer-profile-local artifact and its semantic projection type.

    ``projection_type`` lets one semantic Customer contract be split into multiple submission
    artifacts without introducing any dependency on Engineering topology.
    """
    rows = profile.get("artifacts") or {}
    if not isinstance(rows, dict):
        raise ValueError("customer tailoring artifacts must be a mapping")

    direct = rows.get(requested)
    if isinstance(direct, dict):
        semantic = str(direct.get("projection_type") or requested)
        return requested, dict(direct), RENDER.resolve_document_type(semantic, contract)

    resolved_request = RENDER.resolve_document_type(requested, contract)
    candidates: list[tuple[str, dict[str, Any], str]] = []
    for artifact_id, value in rows.items():
        if not isinstance(value, dict):
            continue
        semantic_raw = str(value.get("projection_type") or artifact_id)
        try:
            semantic = RENDER.resolve_document_type(semantic_raw, contract)
        except KeyError:
            continue
        if semantic == resolved_request:
            candidates.append((str(artifact_id), dict(value), semantic))
    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) > 1:
        choices = ", ".join(x[0] for x in candidates)
        raise ValueError(
            f"customer profile splits semantic type {resolved_request}; choose an artifact id: {choices}"
        )
    raise ValueError(
        f"customer tailoring profile {profile.get('profile_id')} has no artifact for {requested}"
    )


def _render_output_path(row: dict[str, Any], target: str, artifact_id: str) -> str:
    raw = str(row.get("output_path") or "").strip()
    if not raw:
        raise ValueError(f"customer artifact {artifact_id} output_path is required")
    safe_target = TAILOR._safe_target(target)
    return raw.replace("{target}", safe_target).replace("{artifact_id}", artifact_id)


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


def _contract_for_artifact(
    contract: dict[str, Any], semantic_type: str, row: dict[str, Any]
) -> dict[str, Any]:
    """Apply only this Customer artifact's semantic source selector to a contract copy."""
    local = copy.deepcopy(contract)
    sources = row.get("sources") or {}
    profile_stages = [str(x).upper() for x in sources.get("stages", [])] if isinstance(sources, dict) else []
    if profile_stages:
        local["document_types"][semantic_type]["stages"] = profile_stages
    return local


def _annotate_unclassified_inputs(row: dict[str, Any], artifacts: list[dict[str, Any]]) -> None:
    """Give legacy/unclassified inputs a semantic stage using the Customer artifact itself.

    This fallback is intentionally local to the selected Customer artifact. It never looks up an
    Engineering profile, expected filename, artifact order, or document count. Explicit input stage
    metadata always wins; only unclassified legacy inputs receive the latest allowed Customer stage.
    """
    sources = row.get("sources") or {}
    stages = [str(x).upper() for x in sources.get("stages", [])] if isinstance(sources, dict) else []
    if not stages:
        return
    fallback_stage = stages[-1]
    for artifact in artifacts:
        if not artifact.get("stage"):
            artifact["stage"] = fallback_stage
            artifact["stage_inference"] = "CUSTOMER_PROFILE_SEMANTIC_FALLBACK"


def _canonical_artifact(root: Path, target: str, row: dict[str, Any]) -> list[dict[str, Any]]:
    """Expose direct Canonical meaning as a semantic input without changing the Canonical store."""
    store = TAILOR.load_store(root)
    entities = store.get("entities") or {}
    entity = entities.get(target)
    if not isinstance(entity, dict):
        return []
    sources = row.get("sources") or {}
    stages = [str(x).upper() for x in sources.get("stages", [])] if isinstance(sources, dict) else []
    stage = stages[-1] if stages else None
    fields: dict[str, str] = {}
    for key, value in entity.items():
        text = RENDER._to_text(value)
        if text:
            fields[str(key)] = text
    related: list[str] = []
    for rel in store.get("relations") or []:
        if not isinstance(rel, dict):
            continue
        source = str(rel.get("source") or rel.get("from") or "")
        destination = str(rel.get("target") or rel.get("to") or "")
        if target in {source, destination}:
            other = destination if source == target else source
            relation_type = str(rel.get("type") or rel.get("relation") or "RELATED")
            related.append(f"{target} -[{relation_type}]- {other}")
    if related:
        fields["관련 ID 및 추적성"] = "\n".join(f"- {x}" for x in sorted(set(related)))
    return [{
        "source": "sdlc/canonical/store.json#" + target,
        "artifact_type": "CANONICAL_JSON_BUNDLE",
        "stage": stage,
        "title": str(entity.get("title") or entity.get("name") or target),
        "sections": {},
        "fields": fields,
        "semantic_source": "CANONICAL",
    }]


def generate(
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
    settings = _project_settings(
        root,
        contract_path=contract_path,
        projection_config_path=profile_path,
        tailoring_profile_id=tailoring_profile_id,
    )
    artifact_id, selected, semantic_type = _profile_artifact(
        settings["customer_profile"], document_type, settings["contract"]
    )
    if str(selected.get("audience") or "").upper() != "CUSTOMER":
        raise ValueError(f"customer artifact {artifact_id} audience must be CUSTOMER")
    if str(selected.get("authoring") or "").upper() != "GENERATED_VIEW":
        raise ValueError(f"customer artifact {artifact_id} authoring must be GENERATED_VIEW")

    template_file, template_rel = _repo_file(root, str(selected.get("template") or ""))
    local_contract = _contract_for_artifact(settings["contract"], semantic_type, selected)

    artifacts: list[dict[str, Any]] = []
    artifacts.extend(_canonical_artifact(root, target, selected))
    external_artifacts: list[dict[str, Any]] = []
    for raw in inputs:
        path = Path(raw)
        path = path if path.is_absolute() else root / path
        external_artifacts.extend(RENDER.load_artifact_input(path, local_contract))
    _annotate_unclassified_inputs(selected, external_artifacts)
    artifacts.extend(external_artifacts)

    projection = RENDER.project(
        semantic_type,
        local_contract,
        settings["projection_config"],
        artifacts,
        short_name,
    )
    text = _render_selected_template(
        template_file.read_text(encoding="utf-8"),
        document_type=semantic_type,
        contract=local_contract,
        profile=settings["projection_config"],
        projection=projection,
    )

    output_raw = out or _render_output_path(selected, target, artifact_id)
    output = Path(output_raw)
    output = output if output.is_absolute() else root / output
    output = output.resolve()
    try:
        output_rel = output.relative_to(root).as_posix()
    except ValueError as exc:
        raise ValueError("customer output path escapes project root") from exc
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")

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
        "document_type": semantic_type,
        "artifact_id": artifact_id,
        "customer_artifact_id": artifact_id,
        "artifact_path": output_rel,
        "template_path": template_rel,
        "customer_tailoring_profile": settings["customer_profile_id"],
        "customer_tailoring_profile_path": settings["customer_profile_path"],
        "projection_contract": settings["contract_path"],
        "projection_config": settings["projection_config_path"],
        "source_count": projection.get("_source_count", 0),
        "source_stages": projection.get("_source_stages", []),
        "semantic_input_priority": [
            "CANONICAL_SPEC",
            "CANONICAL_RELATION",
            "SEMANTIC_TAGGED_ENGINEERING",
            "VERIFIED_SOURCE_EVIDENCE",
            "TEST_VERIFICATION",
            "OPERATIONS_KNOWLEDGE",
        ],
        "engineering_profile_dependency": False,
        "customer_topology_source": "CUSTOMER_PROFILE_ONLY",
        "lifecycle": metadata["lifecycle"],
        "generated_from_revision": metadata["generated_from_revision"],
        "business_truth_authority": False,
        "customer_edit_auto_updates_canonical": False,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Generate a Customer view from Canonical/semantic evidence and a Customer-only profile.")
    ap.add_argument("--root", default=".")
    ap.add_argument("--target", required=True)
    ap.add_argument("--type", required=True, help="Customer artifact id or semantic document type")
    ap.add_argument("--input", action="append", default=[])
    ap.add_argument("--out", help="Override the selected Customer artifact output_path")
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