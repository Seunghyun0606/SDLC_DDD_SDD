#!/usr/bin/env python3
"""Compatibility lint for knowledge/glossary artifacts aligned with P1 promotion authority."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
import yaml

TRUTH = {"GIVEN", "OBSERVED", "INFERRED", "CONFIRMED", "OPEN"}
PROMOTION = {"CANDIDATE", "REVIEW_REQUIRED", "PROMOTED", "REJECTED", "SUPERSEDED"}
GLOSSARY_STATUS = {"CANDIDATE", "CONFIRMED", "SUPERSEDED", "REJECTED"}
BUSINESS_SEMANTIC_TYPES = {"BUSINESS_RULE", "PROCESS", "DATA_MEANING", "INTERFACE_MEANING", "OPERATIONAL_CONSTRAINT"}


def load(path): return yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}


def lint_knowledge(doc):
    errors = []; root = doc.get("knowledge_candidate", {})
    if not root.get("knowledge_id"): errors.append("P1K-001 knowledge_id required")
    if not root.get("project_id"): errors.append("P1K-002 project_id required")
    if root.get("truth_state") not in TRUTH: errors.append("P1K-003 invalid truth_state")
    if root.get("promotion_state") not in PROMOTION: errors.append("P1K-004 invalid promotion_state")
    prov = root.get("provenance", {})
    if not (prov.get("evidence_ids") or prov.get("source_refs")): errors.append("P1K-005 provenance required")
    if root.get("promotion_state") == "PROMOTED":
        review = root.get("review", {})
        if review.get("decision") != "CONFIRM" or not review.get("reviewed_by") or not review.get("reviewed_at") or not review.get("decision_basis"):
            errors.append("P1K-006 promoted knowledge requires explicit CONFIRM review")
        if root.get("type") in BUSINESS_SEMANTIC_TYPES and root.get("truth_state") not in {"GIVEN", "CONFIRMED"}:
            errors.append("P1K-007 promoted business-semantic knowledge must be GIVEN/CONFIRMED")
    return errors


def lint_glossary(entries):
    errors=[]; seen_ids=set(); normalized={}
    for doc in entries:
        root=doc.get("glossary_entry", {}); tid=root.get("term_id"); norm=(root.get("normalized_term") or root.get("term") or "").strip().casefold()
        if not tid or tid in seen_ids: errors.append("P1G-001 term_id must be non-empty and unique")
        seen_ids.add(tid)
        if not root.get("project_id"): errors.append(f"P1G-002 project_id required: {tid}")
        if root.get("truth_state") not in TRUTH: errors.append(f"P1G-003 invalid truth_state: {tid}")
        if root.get("status") not in GLOSSARY_STATUS: errors.append(f"P1G-004 invalid status: {tid}")
        prov=root.get("provenance", {})
        if root.get("status") == "CONFIRMED" and not (prov.get("evidence_ids") or prov.get("source_refs")): errors.append(f"P1G-005 confirmed term requires provenance: {tid}")
        if norm: normalized.setdefault(norm, []).append(tid)
    for norm,ids in normalized.items():
        if len(ids)>1: errors.append(f"P1G-006 duplicate normalized term {norm}: {','.join(ids)}")
    return errors


def main():
    p=argparse.ArgumentParser(); p.add_argument("kind", choices=["knowledge", "glossary"]); p.add_argument("paths", nargs="+"); a=p.parse_args(); docs=[load(x) for x in a.paths]
    errors=lint_knowledge(docs[0]) if a.kind=="knowledge" else lint_glossary(docs)
    if errors: print("\n".join(errors)); return 1
    print(f"OK: P1 {a.kind} lint passed"); return 0

if __name__=="__main__": sys.exit(main())
