#!/usr/bin/env python3
"""Collect language-neutral bounded source evidence from explicit target paths and analyzer outputs."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Any
import yaml


def load(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_path(root: Path, rel: str) -> Path:
    path = (root / rel).resolve()
    resolved_root = root.resolve()
    if path != resolved_root and resolved_root not in path.parents:
        raise ValueError(f"path escapes source root: {rel}")
    return path


def collect(source_root: Path, source_revision: str, target_doc: dict[str, Any], analyzer_docs: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    target = (target_doc or {}).get("source_target") or {}
    if not target.get("target_id") or not target.get("target_type"):
        raise ValueError("source_target requires target_id and target_type")

    artifacts = []
    evidence = []
    open_items = []
    seq = 1
    for rel in target.get("direct_paths") or []:
        path = safe_path(source_root, str(rel))
        if not path.is_file():
            open_items.append({
                "open_id": f"OPEN-SOURCE-PATH-{seq:03d}",
                "type": "SOURCE_PATH_MISSING",
                "question": f"명시된 Source path가 존재하는가: {rel}",
                "blocks_reasoning": False,
                "blocks_action": False,
                "action_scopes": [],
                "escalation": "ENGINEERING_OWNER",
            })
            seq += 1
            continue
        file_hash = sha256(path)
        artifacts.append({"path": str(rel), "file_hash": file_hash, "truth": "OBSERVED"})
        evidence.append({
            "evidence_id": f"EV-SRC-{seq:03d}",
            "truth": "OBSERVED",
            "locator": str(rel),
            "source_revision": source_revision,
            "file_hash": file_hash,
            "analyzer_id": "core-bounded-path",
        })
        seq += 1

    analyzer_evidence = []
    for doc in analyzer_docs or []:
        root = (doc or {}).get("analyzer_evidence") or {}
        analyzer_id = root.get("analyzer_id") or "UNASSIGNED_ANALYZER"
        for item in root.get("evidence") or []:
            copied = dict(item)
            copied.setdefault("truth", "INFERRED")
            copied["analyzer_id"] = analyzer_id
            copied.setdefault("source_revision", source_revision)
            analyzer_evidence.append(copied)
        for item in root.get("open_items") or []:
            open_items.append(item)

    explicit_relations = []
    for relation in target.get("explicit_relations") or []:
        copied = dict(relation)
        copied.setdefault("truth_state", "OPEN")
        copied.setdefault("status", "OPEN")
        explicit_relations.append(copied)

    return {
        "schema_version": 1,
        "artifact_type": "SOURCE_DISCOVERY_RESULT",
        "source_discovery_result": {
            "metadata": {
                "source_root": str(source_root),
                "source_revision": source_revision,
                "collector": "core-bounded-source-evidence-v1",
                "language_specific_parsing": False,
            },
            "target": {
                "target_id": target.get("target_id"),
                "target_type": target.get("target_type"),
            },
            "artifacts": artifacts,
            "explicit_relations": explicit_relations,
            "evidence": evidence + analyzer_evidence,
            "open_items": open_items,
            "constraints": {
                "name_similarity_confirms_relation": False,
                "analyzer_evidence_auto_confirms_business_truth": False,
                "source_behavior_is_not_business_truth": True,
                "bounded_scope_only": True,
            },
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_root", type=Path)
    parser.add_argument("source_revision")
    parser.add_argument("target_context", type=Path)
    parser.add_argument("--analyzer-evidence", type=Path, nargs="*", default=[])
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()
    result = collect(args.source_root, args.source_revision, load(args.target_context), [load(p) for p in args.analyzer_evidence])
    text = yaml.safe_dump(result, allow_unicode=True, sort_keys=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
