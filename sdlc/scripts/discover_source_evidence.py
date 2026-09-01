#!/usr/bin/env python3
"""Bounded source discovery using an explicit direct-trace manifest."""

from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

import yaml

JAVA_METHOD = re.compile(r"\b(?:public|protected|private)\s+[\w<>\[\], ?]+\s+(\w+)\s*\(")
MAPPER_ID = re.compile(r"<(?:select|insert|update|delete)\s+id=\"([^\"]+)\"")
TABLE = re.compile(r"\b(TB_[A-Z0-9_]+)\b")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    artifact_type = "JAVA" if suffix == ".java" else "XML" if suffix == ".xml" else "OTHER"
    symbols = sorted(set(JAVA_METHOD.findall(text))) if artifact_type == "JAVA" else []
    mapper_ids = sorted(set(MAPPER_ID.findall(text))) if artifact_type == "XML" else []
    tables = sorted(set(TABLE.findall(text)))
    tx = ["@Transactional"] if "@Transactional" in text else []
    return {
        "artifact_type": artifact_type,
        "file_hash": sha256(path),
        "symbols": symbols,
        "mapper_statement_ids": mapper_ids,
        "table_names": tables,
        "transaction_markers": tx,
    }


def discover(source_root: Path, manifest: dict) -> dict:
    root = (manifest or {}).get("trace_manifest") or {}
    revision = root.get("source_revision_before")
    group_id = root.get("source_group_id")
    programs = root.get("programs") or []
    if not revision or not group_id or not programs:
        raise ValueError("trace_manifest requires source_revision_before, source_group_id and programs")

    artifacts = []
    direct_relations = []
    evidence = []
    evidence_seq = 1
    for program in programs:
        pid = program.get("program_id")
        if not pid:
            raise ValueError("program_id is required")
        for rel in program.get("artifacts") or []:
            path = source_root / rel
            if not path.is_file():
                raise ValueError(f"direct artifact missing: {rel}")
            info = extract(path)
            artifacts.append({"path": rel, "direct_program_ids": [pid], **info})
            direct_relations.append({"program_id": pid, "artifact_path": rel, "relation": "DIRECT_MANIFEST"})
            evidence.append({
                "evidence_id": f"EV-DISC-{evidence_seq:03d}",
                "truth": "OBSERVED",
                "locator": rel,
                "value": {
                    "symbols": info["symbols"],
                    "mapper_statement_ids": info["mapper_statement_ids"],
                    "table_names": info["table_names"],
                    "transaction_markers": info["transaction_markers"],
                },
            })
            evidence_seq += 1

    blind_spots = [
        "runtime callers outside fixture are not proven complete",
        "database trigger/procedure dependencies are not scanned by this fixture-only discovery",
        "batch/external consumers outside direct manifest remain OPEN",
    ]
    return {
        "version": 1,
        "source_discovery_result": {
            "metadata": {
                "discovery_id": "DISC-ATT-CLOSE-FIXTURE-001",
                "source_root": str(source_root),
                "source_revision": revision,
                "provider_state": "AVAILABLE",
                "fixture_evidence": True,
            },
            "target": {
                "source_group_id": group_id,
                "canonical_rq_ids": root.get("requirement_context", {}).get("canonical_rq_ids") or [],
                "program_ids": [p["program_id"] for p in programs],
            },
            "direct_relations": direct_relations,
            "artifacts": artifacts,
            "blind_spots": blind_spots,
            "evidence": evidence,
            "open_items": [
                {
                    "type": "FIXTURE_ONLY_EVIDENCE",
                    "question": "실제 고객 Repository에서 동일 관계가 성립하는가?",
                    "escalation": "ENGINEERING_OWNER",
                }
            ],
            "validation": {
                "source_revision_present": "PASS",
                "file_hash_present": "PASS",
                "direct_relation_check": "PASS",
                "evidence_truth_check": "PASS",
            },
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_root", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()
    manifest = yaml.safe_load(args.manifest.read_text(encoding="utf-8")) or {}
    result = discover(args.source_root, manifest)
    text = yaml.safe_dump(result, allow_unicode=True, sort_keys=False)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
