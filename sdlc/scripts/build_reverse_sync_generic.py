#!/usr/bin/env python3
"""Build conservative reverse-sync candidates from stack-neutral source diff evidence and confirmed trace graph edges."""
from __future__ import annotations
import argparse
import sys
from collections import deque
from pathlib import Path
import yaml

TECHNICAL_TYPES = {"PGM", "ART", "SYMBOL", "DATA", "INT", "SOURCE"}
BUSINESS_TYPES = {"RQ", "FR", "BR", "PROC", "FTR", "AC", "TC"}
SEMANTIC_CLASSES = {
    "TECHNICAL_ONLY", "FUNCTIONAL_BEHAVIOR", "BUSINESS_RULE_CANDIDATE", "DATA_CONTRACT",
    "INTERFACE_CONTRACT", "SECURITY_BEHAVIOR", "UNKNOWN",
}
REVIEW_CLASSES = {
    "FUNCTIONAL_BEHAVIOR", "BUSINESS_RULE_CANDIDATE", "DATA_CONTRACT",
    "INTERFACE_CONTRACT", "SECURITY_BEHAVIOR", "UNKNOWN",
}


def load(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def changed_refs(diff_root):
    refs = set()
    for item in diff_root.get("changed_items") or []:
        if item.get("path"):
            refs.add(str(item["path"]))
        for key in ("changed_symbols", "data_refs", "interface_refs"):
            refs.update(str(value) for value in (item.get(key) or []) if value)
    return refs


def direct_nodes(graph_root, refs):
    result = set()
    for node in graph_root.get("nodes") or []:
        node_refs = {str(x) for x in (node.get("source_refs") or []) if x}
        if node.get("node_id") in refs or node_refs & refs:
            result.add(node.get("node_id"))
    return {x for x in result if x}


def confirmed_incoming(graph_root):
    incoming = {}
    open_edges = []
    for edge in graph_root.get("edges") or []:
        to_id, from_id = edge.get("to_id"), edge.get("from_id")
        if not to_id or not from_id:
            continue
        if edge.get("status") == "CONFIRMED":
            incoming.setdefault(to_id, []).append(from_id)
        else:
            open_edges.append(edge.get("edge_id"))
    return incoming, [x for x in open_edges if x]


def confirmed_ancestors(graph_root, starts, max_hops=8):
    incoming, open_edges = confirmed_incoming(graph_root)
    distance = {node_id: 0 for node_id in starts}
    queue = deque(starts)
    while queue:
        current = queue.popleft()
        depth = distance[current]
        if depth >= max_hops:
            continue
        for parent in incoming.get(current, []):
            if parent in distance:
                continue
            distance[parent] = depth + 1
            queue.append(parent)
    return distance, open_edges


def build(diff_doc, graph_doc):
    diff = (diff_doc or {}).get("source_diff_evidence") or {}
    metadata = diff.get("metadata") or {}
    graph = (graph_doc or {}).get("reference_graph") or {}
    semantic_class = diff.get("semantic_change_class") or "UNKNOWN"
    if semantic_class not in SEMANTIC_CLASSES:
        return None, [f"RS-GEN-001: invalid semantic_change_class: {semantic_class}"]
    if not metadata.get("source_revision_before") or not metadata.get("source_revision_after"):
        return None, ["RS-GEN-002: source revisions before/after are required or must be explicit OPEN"]

    refs = changed_refs(diff)
    if not refs:
        return None, ["RS-GEN-003: changed_items must contain at least one path/symbol/data/interface reference"]

    nodes = {node.get("node_id"): node for node in graph.get("nodes") or [] if node.get("node_id")}
    starts = direct_nodes(graph, refs)
    distances, open_edges = confirmed_ancestors(graph, starts)

    stale_candidates = []
    review_candidates = []
    for node_id, distance in sorted(distances.items(), key=lambda item: (item[1], item[0])):
        node = nodes.get(node_id) or {}
        node_type = node.get("node_type")
        candidate = {
            "node_id": node_id,
            "node_type": node_type,
            "distance_from_changed_source": distance,
            "state": "STALE_CANDIDATE" if node_type in TECHNICAL_TYPES else "REVIEW_CANDIDATE",
        }
        if node_type in TECHNICAL_TYPES:
            stale_candidates.append(candidate)
        elif node_type in BUSINESS_TYPES and semantic_class in REVIEW_CLASSES:
            review_candidates.append(candidate)

    unresolved = []
    if not starts:
        unresolved.append({
            "code": "DIRECT_TRACE_NOT_FOUND",
            "changed_refs": sorted(refs),
            "required_action": "L2_TRACE_REVIEW",
        })
    if open_edges:
        unresolved.append({
            "code": "NON_CONFIRMED_TRACE_EDGES_NOT_TRAVERSED",
            "edge_ids": sorted(open_edges),
            "required_action": "REVIEW_TRACE_PROVENANCE",
        })

    review_required = semantic_class in {"BUSINESS_RULE_CANDIDATE", "SECURITY_BEHAVIOR", "UNKNOWN"} or bool(review_candidates)
    result = {
        "version": 1,
        "reverse_sync_candidate": {
            "change_id": metadata.get("change_id"),
            "project_id": metadata.get("project_id"),
            "source_revision_before": metadata.get("source_revision_before"),
            "source_revision_after": metadata.get("source_revision_after"),
            "changed_refs": sorted(refs),
            "semantic_change_class": semantic_class,
            "secondary_classes": diff.get("secondary_classes") or [],
            "direct_trace_node_ids": sorted(starts),
            "stale_candidates": stale_candidates,
            "review_candidates": review_candidates,
            "protected_human_truth": True,
            "required_review": "L2_OR_HUMAN" if review_required else "L2",
            "unresolved": unresolved,
            "status": "REVIEW_REQUIRED" if review_required or unresolved else "CANDIDATE_READY",
            "constraints": {
                "source_diff_is_observed": True,
                "business_truth_auto_overwrite": False,
                "non_confirmed_edges_are_not_silently_traversed": True,
                "semantic_class_is_consumed_not_inferred_by_core": True,
            },
        },
    }
    return result, []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source_diff", type=Path)
    parser.add_argument("reference_graph", type=Path)
    parser.add_argument("-o", "--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result, errors = build(load(args.source_diff), load(args.reference_graph))
    except Exception as exc:
        print(f"RS-GEN-LOAD: {exc}", file=sys.stderr)
        return 2
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    args.output.write_text(yaml.safe_dump(result, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"OK: generic reverse-sync candidate built: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
