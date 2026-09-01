#!/usr/bin/env python3
"""Build language-neutral reverse-sync candidates from analyzer signals and confirmed graph edges."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any
import yaml

TECHNICAL_STALE_TYPES = {"PGM", "ART", "SYMBOL", "DATA", "INT", "TC"}
HUMAN_REVIEW_TYPES = {"RQ", "FR", "BR", "PROC", "FTR", "AC"}


def load(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def signal_names(change: dict[str, Any]) -> set[str]:
    names = set()
    for file_item in change.get("changed_files") or []:
        for signal in file_item.get("signals") or []:
            if isinstance(signal, str):
                names.add(signal)
            elif isinstance(signal, dict) and signal.get("signal"):
                names.add(str(signal.get("signal")))
    return names


def classify(signals: set[str], classification: dict[str, Any]) -> tuple[str, list[str]]:
    matches = []
    for class_name, candidates in (classification.get("candidate_signals") or {}).items():
        if signals.intersection(set(candidates or [])):
            matches.append(class_name)
    if not matches:
        return "UNKNOWN", []
    precedence = classification.get("classification_precedence") or []
    rank = {name: idx for idx, name in enumerate(precedence)}
    matches = sorted(set(matches), key=lambda name: rank.get(name, 999))
    return matches[0], matches[1:]


def confirmed(edge: dict[str, Any]) -> bool:
    return edge.get("status") == "CONFIRMED" or edge.get("truth_state") == "CONFIRMED"


def build(change_doc: dict[str, Any], graph_doc: dict[str, Any], classification: dict[str, Any]) -> dict[str, Any]:
    change = (change_doc or {}).get("source_change_evidence") or {}
    graph = (graph_doc or {}).get("reference_graph") or {}
    nodes = {n.get("node_id"): n for n in (graph.get("nodes") or []) if n.get("node_id")}
    edges = [e for e in (graph.get("edges") or []) if confirmed(e)]
    changed_paths = {x.get("path") for x in (change.get("changed_files") or []) if x.get("path")}
    changed_node_ids = {
        node_id for node_id, node in nodes.items()
        if node.get("source_ref") in changed_paths
    }

    related_ids = set()
    used_edges = []
    for edge in edges:
        if edge.get("from_id") in changed_node_ids:
            related_ids.add(edge.get("to_id")); used_edges.append(edge.get("edge_id"))
        if edge.get("to_id") in changed_node_ids:
            related_ids.add(edge.get("from_id")); used_edges.append(edge.get("edge_id"))

    signals = signal_names(change)
    primary, secondary = classify(signals, classification)
    stale_candidates = []
    review_candidates = []
    for node_id in sorted(x for x in related_ids if x in nodes):
        node = nodes[node_id]
        candidate = {
            "node_id": node_id,
            "node_type": node.get("node_type"),
            "title": node.get("title"),
            "source_ref": node.get("source_ref"),
            "reason": "CONFIRMED_DIRECT_GRAPH_RELATION_TO_CHANGED_SOURCE",
        }
        if node.get("node_type") in TECHNICAL_STALE_TYPES:
            candidate["state"] = "STALE_CANDIDATE"
            stale_candidates.append(candidate)
        elif node.get("node_type") in HUMAN_REVIEW_TYPES:
            candidate["state"] = "REVIEW_CANDIDATE"
            review_candidates.append(candidate)

    required_review = "L2_OR_HUMAN" if primary in {"BUSINESS_RULE_CANDIDATE", "SECURITY_BEHAVIOR", "UNKNOWN"} or review_candidates else "L2"
    return {
        "schema_version": 1,
        "artifact_type": "REVERSE_SYNC_CANDIDATE",
        "reverse_sync_candidate": {
            "change_id": change.get("change_id"),
            "source_revision_before": change.get("source_revision_before"),
            "source_revision_after": change.get("source_revision_after"),
            "changed_files": sorted(changed_paths),
            "changed_source_node_ids": sorted(changed_node_ids),
            "confirmed_graph_edge_ids": sorted(x for x in set(used_edges) if x),
            "semantic_change_class": primary,
            "secondary_classes": secondary,
            "signals": sorted(signals),
            "stale_candidates": stale_candidates,
            "review_candidates": review_candidates,
            "protected_human_truth": True,
            "required_review": required_review,
            "status": "REVIEW_REQUIRED" if required_review == "L2_OR_HUMAN" else "CANDIDATE_READY",
            "open_items": list(change.get("open_items") or []),
            "constraints": {
                "confirmed_trace_only": True,
                "source_does_not_overwrite_human_truth": True,
                "candidate_is_not_canonical": True,
            },
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_change", type=Path)
    parser.add_argument("reference_graph", type=Path)
    parser.add_argument("classification", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()
    result = build(load(args.source_change), load(args.reference_graph), load(args.classification))
    text = yaml.safe_dump(result, allow_unicode=True, sort_keys=False)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
