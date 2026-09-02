#!/usr/bin/env python3
"""Deterministically render customer-reviewable Markdown from a registered template.

Missing fields are rendered as OPEN rather than invented. The sidecar metadata records exactly
which fields were missing and the input evidence/revision used for the render.
"""
from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path
from typing import Any
import yaml

TOKEN = re.compile(r"\{\{\s*([A-Za-z0-9_.-]+)\s*\}\}")


def load(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def flatten(value: Any, prefix: str = "") -> dict[str, Any]:
    out: dict[str, Any] = {}
    if isinstance(value, dict):
        for key, child in value.items():
            name = f"{prefix}.{key}" if prefix else str(key)
            out[name] = child
            out.update(flatten(child, name))
    return out


def display(value: Any) -> str:
    if value is None or value == "":
        return "OPEN"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list)):
        dumped = yaml.safe_dump(value, allow_unicode=True, sort_keys=False).strip()
        return dumped if dumped else "OPEN"
    return str(value)


def resolve_artifact(registry: dict[str, Any], requested: str) -> tuple[str, dict[str, Any]]:
    aliases = registry.get("aliases") or {}
    artifact_id = aliases.get(requested, requested)
    artifact = (registry.get("artifacts") or {}).get(artifact_id)
    if not isinstance(artifact, dict):
        raise ValueError(f"unknown human artifact: {requested}")
    return artifact_id, artifact


def render(repo_root: Path, registry: dict[str, Any], requested: str, context_doc: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    artifact_id, artifact = resolve_artifact(registry, requested)
    template_path = repo_root / str(artifact.get("template"))
    if not template_path.is_file():
        raise FileNotFoundError(f"registered template missing: {template_path}")
    template = template_path.read_text(encoding="utf-8")
    context = (context_doc or {}).get("context") or context_doc
    if not isinstance(context, dict):
        raise ValueError("context must be an object")
    values = flatten(context)
    missing: list[str] = []

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in values or values[key] in (None, ""):
            missing.append(key)
            return "OPEN"
        return display(values[key])

    text = TOKEN.sub(replace, template)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    metadata = {
        "schema_version": 1,
        "artifact_type": "HUMAN_ARTIFACT_RENDER_RESULT",
        "render_result": {
            "artifact_id": artifact_id,
            "display_name_ko": artifact.get("display_name_ko"),
            "stages": artifact.get("stages") or ([artifact.get("stage")] if artifact.get("stage") else []),
            "template": artifact.get("template"),
            "sha256": digest,
            "missing_fields": sorted(set(missing)),
            "open_preserved": bool(missing),
            "source_revision": context.get("source_revision"),
            "evidence_refs": context.get("evidence_refs") or [],
            "truth_guards": {
                "missing_values_are_open": True,
                "render_does_not_promote_source_evidence_to_business_truth": True,
            },
        },
    }
    return text, metadata


def default_filename(registry: dict[str, Any], requested: str, context_doc: dict[str, Any]) -> str:
    _, artifact = resolve_artifact(registry, requested)
    context = (context_doc or {}).get("context") or context_doc
    rid = str(context.get("representative_id") or context.get("requirement_id") or context.get("program_id") or "OPEN")
    short = str(context.get("short_business_name") or context.get("title") or "업무")
    safe = re.sub(r"[\\/:*?\"<>|\s]+", "_", short).strip("_") or "업무"
    return f"{rid}_{safe}_{artifact.get('default_filename_suffix')}.md"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact")
    parser.add_argument("context", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument("--metadata-output", type=Path)
    parser.add_argument("--registry", type=Path, default=Path("sdlc/config/human-artifacts.yaml"))
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    args = parser.parse_args()
    registry = load(args.registry)
    context = load(args.context)
    text, metadata = render(args.repo_root.resolve(), registry, args.artifact, context)
    output = args.output
    if output is None:
        output = Path("docs") / default_filename(registry, args.artifact, context)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")
    meta = args.metadata_output or output.with_suffix(output.suffix + ".meta.yaml")
    meta.write_text(yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"OK: rendered {args.artifact} -> {output}; metadata={meta}; open_fields={len(metadata['render_result']['missing_fields'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
