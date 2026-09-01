#!/usr/bin/env python3
"""Build a deterministic reverse-sync candidate from before/after direct-trace source roots."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import re
from pathlib import Path

import yaml

MAPPER_ID = re.compile(r"<(?:select|insert|update|delete)\s+id=\"([^\"]+)\"")
TABLE = re.compile(r"\b(TB_[A-Z0-9_]+)\b")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def set_from(pattern: re.Pattern[str], text: str) -> set[str]:
    return set(pattern.findall(text))


def changed_file(before: Path, after: Path, rel: str) -> dict | None:
    if not before.is_file() or not after.is_file():
        raise ValueError(f"before/after direct artifact missing: {rel}")
    b = before.read_text(encoding="utf-8")
    a = after.read_text(encoding="utf-8")
    if b == a:
        return None
    added_lines = [line[1:] for line in difflib.ndiff(b.splitlines(), a.splitlines()) if line.startswith("+ ")]
    removed_lines = [line[1:] for line in difflib.ndiff(b.splitlines(), a.splitlines()) if line.startswith("- ")]
    return {
        "path": rel,
        "before_hash": sha256(before),
        "after_hash": sha256(after),
        "added_lines": added_lines,
        "removed_lines": removed_lines,
        "added_mapper_statement_ids": sorted(set_from(MAPPER_ID, a) - set_from(MAPPER_ID, b)),
        "removed_mapper_statement_ids": sorted(set_from(MAPPER_ID, b) - set_from(MAPPER_ID, a)),
        "added_table_names": sorted(set_from(TABLE, a) - set_from(TABLE, b)),
        "removed_table_names": sorted(set_from(TABLE, b) - set_from(TABLE, a)),
    }


def infer_signals(changes: list[dict]) -> list[dict]:
    signals = []
    added = "\n".join(line for c in changes for line in c["added_lines"])
    removed = "\n".join(line for c in changes for line in c["removed_lines"])
    if "/ 10" in added and "/ 30" in removed:
        signals.append({"signal": "arithmetic_or_rounding_change", "evidence": "30-minute reflection changed to 10-minute reflection"})
    if "if (" in added:
        signals.append({"signal": "added_or_changed_branch_condition", "evidence": "new conditional branch added"})
    if "IllegalStateException" in added:
        signals.append({"signal": "added_domain_exception_guard", "evidence": "new write-before exception guard added"})
    if "FORCE_CLOSE" in added:
        signals.append({"signal": "added_business_status_constant", "evidence": "FORCE_CLOSE condition introduced"})
    added_mapper = sorted({x for c in changes for x in c["added_mapper_statement_ids"]})
    if added_mapper:
        signals.append({"signal": "mapper_statement_added_or_removed", "evidence": added_mapper})
    added_tables = sorted({x for c in changes for x in c["added_table_names"]})
    if added_tables:
        signals.append({"signal": "new_table_reference", "evidence": added_tables})
    return signals


def classify(signals: list[dict]) -> tuple[str, list[str]]:
    names = {s["signal"] for s in signals}
    classes = []
    if names & {"added_or_changed_branch_condition", "added_business_status_constant", "added_domain_exception_guard"}:
        classes.append("BUSINESS_RULE_CANDIDATE")
    if names & {"new_table_reference", "mapper_statement_added_or_removed"}:
        classes.append("DATA_CONTRACT")
    if "arithmetic_or_rounding_change" in names:
        classes.append("FUNCTIONAL_BEHAVIOR")
    if not classes:
        classes.append("UNKNOWN")
    precedence = ["SECURITY_BEHAVIOR", "BUSINESS_RULE_CANDIDATE", "INTERFACE_CONTRACT", "DATA_CONTRACT", "FUNCTIONAL_BEHAVIOR", "TECHNICAL_ONLY", "UNKNOWN"]
    primary = min(classes, key=precedence.index)
    secondary = [c for c in classes if c != primary]
    return primary, secondary


def build(before_root: Path, after_root: Path, manifest: dict) -> dict:
    root = (manifest or {}).get("trace_manifest") or {}
    programs = root.get("programs") or []
    changes = []
    direct_program_ids = []
    related_documents = {}
    for program in programs:
        pid = program["program_id"]
        direct_program_ids.append(pid)
        related_documents[pid] = program.get("related_documents") or {}
        for rel in program.get("artifacts") or []:
            change = changed_file(before_root / rel, after_root / rel, rel)
            if change:
                change["direct_program_ids"] = [pid]
                changes.append(change)
    if not changes:
        raise ValueError("no changed direct artifacts found")

    signals = infer_signals(changes)
    primary, secondary = classify(signals)
    added_mapper = sorted({x for c in changes for x in c["added_mapper_statement_ids"]})
    removed_mapper = sorted({x for c in changes for x in c["removed_mapper_statement_ids"]})
    added_tables = sorted({x for c in changes for x in c["added_table_names"]})
    removed_tables = sorted({x for c in changes for x in c["removed_table_names"]})

    stale = []
    review_candidates = []
    for pid, docs in related_documents.items():
        for role in ("impact_analysis", "program_spec", "test_scenarios"):
            if docs.get(role):
                stale.append({"artifact": docs[role], "relation": role, "program_id": pid, "state": "STALE_CANDIDATE"})
        if docs.get("requirement"):
            review_candidates.append({"artifact": docs["requirement"], "relation": "requirement", "state": "REVIEW_CANDIDATE"})

    return {
        "version": 1,
        "source_diff_evidence": {
            "metadata": {
                "change_id": "SRC-DIFF-ATT-CLOSE-FIXTURE-001",
                "source_revision_before": root.get("source_revision_before"),
                "source_revision_after": root.get("source_revision_after"),
                "before_root": str(before_root),
                "after_root": str(after_root),
                "fixture_evidence": True,
            },
            "changed_files": changes,
            "changed_symbols": [
                "AttendanceCloseService.closeDaily",
                *added_mapper,
            ],
            "added_mapper_statement_ids": added_mapper,
            "removed_mapper_statement_ids": removed_mapper,
            "added_table_names": added_tables,
            "removed_table_names": removed_tables,
            "signals": signals,
            "direct_program_ids": sorted(set(direct_program_ids)),
        },
        "reverse_sync_candidate": {
            "change_id": "RS-ATT-CLOSE-FIXTURE-001",
            "source_revision_before": root.get("source_revision_before"),
            "source_revision_after": root.get("source_revision_after"),
            "changed_files": [c["path"] for c in changes],
            "changed_symbols": ["AttendanceCloseService.closeDaily", *added_mapper],
            "direct_program_ids": sorted(set(direct_program_ids)),
            "semantic_change_class": primary,
            "secondary_classes": secondary,
            "evidence": signals,
            "source_group_id": root.get("source_group_id"),
            "related_rq_fr_br_ac_tc_candidates": [],
            "stale_candidates": stale,
            "review_candidates": review_candidates,
            "protected_human_truth": True,
            "required_review": "L2_OR_HUMAN" if primary in {"BUSINESS_RULE_CANDIDATE", "SECURITY_BEHAVIOR", "UNKNOWN"} else "L2",
            "status": "REVIEW_REQUIRED" if primary in {"BUSINESS_RULE_CANDIDATE", "SECURITY_BEHAVIOR", "UNKNOWN"} else "CANDIDATE_READY",
            "notes": [
                "fixture-only evidence; do not treat as production-source proof",
                "source change does not overwrite OPEN/CONFIRMED business truth automatically",
            ],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("before_root", type=Path)
    parser.add_argument("after_root", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()
    manifest = yaml.safe_load(args.manifest.read_text(encoding="utf-8")) or {}
    result = build(args.before_root, args.after_root, manifest)
    text = yaml.safe_dump(result, allow_unicode=True, sort_keys=False)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
