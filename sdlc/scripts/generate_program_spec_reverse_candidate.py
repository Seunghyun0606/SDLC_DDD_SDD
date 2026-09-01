#!/usr/bin/env python3
"""Generate non-destructive Program Spec update candidates from impact-graph deltas.

The generator compares two Brownfield Impact Adapter outputs and maps graph changes to
registered Program Spec bindings. It never rewrites artifacts and never changes
Business/Functional truth. Output is a review candidate only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import deque
from pathlib import Path
from typing import Any

ALLOWED_PROGRAM_SECTIONS = [
    "실제 구현 Target",
    "실제 파일·심볼 근거",
    "구현 매핑과 차이",
    "Query·Table·Source 구현 근거",
    "트랜잭션·실행 제어",
    "연계 구현 계약",
    "기술 제어와 운영 조건",
    "TASK·AC·TC·Source 연결",
    "구현 준비도",
]
FORBIDDEN_SEMANTIC_SECTIONS = [
    "업무 시나리오",
    "업무 규칙",
    "기능 요구사항 의미",
    "업무 예외 의미",
    "Business Truth",
]
EDGE_KEY_FIELDS = ("from", "type", "to")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_impact(payload: dict[str, Any]) -> None:
    required = {"adapter_id", "nodes", "edges", "coverage", "coverage_gaps"}
    missing = sorted(required - set(payload))
    if missing:
        raise ValueError(f"impact output missing fields: {missing}")
    node_ids: set[str] = set()
    for node in payload["nodes"]:
        node_id = str(node.get("id", "")).strip()
        if not node_id:
            raise ValueError("impact node id is required")
        if node_id in node_ids:
            raise ValueError(f"duplicate impact node: {node_id}")
        node_ids.add(node_id)
    edge_keys: set[tuple[str, str, str]] = set()
    for edge in payload["edges"]:
        key = tuple(str(edge.get(field, "")).strip() for field in EDGE_KEY_FIELDS)
        if not all(key):
            raise ValueError("impact edge from/type/to are required")
        if key in edge_keys:
            raise ValueError(f"duplicate impact edge: {key}")
        edge_keys.add(key)


def _validate_bindings(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if payload.get("schema_version") != 1:
        raise ValueError("unsupported program binding schema")
    programs = payload.get("programs")
    if not isinstance(programs, list):
        raise ValueError("programs must be a list")
    seen: set[str] = set()
    for program in programs:
        program_id = str(program.get("program_id", "")).strip()
        artifact_path = str(program.get("artifact_path", "")).strip()
        functional_ref = str(program.get("functional_design_ref", "")).strip()
        roots = program.get("source_node_ids")
        if not program_id or not artifact_path or not functional_ref:
            raise ValueError("program_id/artifact_path/functional_design_ref are required")
        if program_id in seen:
            raise ValueError(f"duplicate program_id: {program_id}")
        seen.add(program_id)
        if not isinstance(roots, list) or not roots or not all(str(x).strip() for x in roots):
            raise ValueError(f"source_node_ids are required: {program_id}")
    return programs


def _node_index(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["id"]: dict(row) for row in payload["nodes"]}


def _edge_index(payload: dict[str, Any]) -> dict[tuple[str, str, str], dict[str, Any]]:
    return {tuple(row[field] for field in EDGE_KEY_FIELDS): dict(row) for row in payload["edges"]}


def _coverage_index(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row.get("dimension", f"#{idx}"): dict(row) for idx, row in enumerate(payload.get("coverage", []))}


def _gap_key(row: dict[str, Any]) -> str:
    return "|".join(str(row.get(key, "")) for key in ("dimension", "code", "pattern", "message"))


def _diff(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    before_nodes, after_nodes = _node_index(before), _node_index(after)
    before_edges, after_edges = _edge_index(before), _edge_index(after)

    added_nodes = [after_nodes[key] for key in sorted(set(after_nodes) - set(before_nodes))]
    removed_nodes = [before_nodes[key] for key in sorted(set(before_nodes) - set(after_nodes))]
    changed_nodes = [
        {"id": key, "before": before_nodes[key], "after": after_nodes[key]}
        for key in sorted(set(before_nodes) & set(after_nodes))
        if before_nodes[key] != after_nodes[key]
    ]

    added_edges = [after_edges[key] for key in sorted(set(after_edges) - set(before_edges))]
    removed_edges = [before_edges[key] for key in sorted(set(before_edges) - set(after_edges))]
    changed_edges = [
        {"key": list(key), "before": before_edges[key], "after": after_edges[key]}
        for key in sorted(set(before_edges) & set(after_edges))
        if before_edges[key] != after_edges[key]
    ]

    before_cov, after_cov = _coverage_index(before), _coverage_index(after)
    coverage_changes = [
        {"dimension": key, "before": before_cov.get(key), "after": after_cov.get(key)}
        for key in sorted(set(before_cov) | set(after_cov))
        if before_cov.get(key) != after_cov.get(key)
    ]

    before_gaps = {_gap_key(row): row for row in before.get("coverage_gaps", [])}
    after_gaps = {_gap_key(row): row for row in after.get("coverage_gaps", [])}
    return {
        "added_nodes": added_nodes,
        "removed_nodes": removed_nodes,
        "changed_nodes": changed_nodes,
        "added_edges": added_edges,
        "removed_edges": removed_edges,
        "changed_edges": changed_edges,
        "coverage_changes": coverage_changes,
        "coverage_gaps_added": [after_gaps[key] for key in sorted(set(after_gaps) - set(before_gaps))],
        "coverage_gaps_resolved": [before_gaps[key] for key in sorted(set(before_gaps) - set(after_gaps))],
    }


def _changed_node_ids(delta: dict[str, Any]) -> set[str]:
    ids = {row["id"] for row in delta["added_nodes"] + delta["removed_nodes"]}
    ids.update(row["id"] for row in delta["changed_nodes"])
    for field in ("added_edges", "removed_edges"):
        for edge in delta[field]:
            ids.add(edge["from"])
            ids.add(edge["to"])
    for edge in delta["changed_edges"]:
        ids.add(edge["key"][0])
        ids.add(edge["key"][2])
    return ids


def _adjacency(before: dict[str, Any], after: dict[str, Any]) -> dict[str, set[str]]:
    graph: dict[str, set[str]] = {}
    for payload in (before, after):
        for edge in payload["edges"]:
            left, right = edge["from"], edge["to"]
            graph.setdefault(left, set()).add(right)
            graph.setdefault(right, set()).add(left)
    return graph


def _distance_from_roots(graph: dict[str, set[str]], roots: list[str], max_hops: int) -> dict[str, int]:
    distances: dict[str, int] = {}
    queue: deque[tuple[str, int]] = deque()
    for root in roots:
        distances[root] = 0
        queue.append((root, 0))
    while queue:
        node, distance = queue.popleft()
        if distance >= max_hops:
            continue
        for neighbor in sorted(graph.get(node, set())):
            if neighbor in distances and distances[neighbor] <= distance + 1:
                continue
            distances[neighbor] = distance + 1
            queue.append((neighbor, distance + 1))
    return distances


def _candidate_id(program_id: str, baseline_id: str, observed_id: str, delta: dict[str, Any]) -> str:
    raw = json.dumps(
        {"program_id": program_id, "baseline": baseline_id, "observed": observed_id, "delta": delta},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return "REV-PGM-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12].upper()


def generate(
    baseline: dict[str, Any],
    observed: dict[str, Any],
    bindings: dict[str, Any],
    max_hops: int = 3,
) -> dict[str, Any]:
    _validate_impact(baseline)
    _validate_impact(observed)
    programs = _validate_bindings(bindings)
    if max_hops < 0:
        raise ValueError("max_hops must be >= 0")

    delta = _diff(baseline, observed)
    changed_ids = _changed_node_ids(delta)
    graph = _adjacency(baseline, observed)
    candidates = []

    for program in programs:
        roots = [str(x) for x in program["source_node_ids"]]
        distances = _distance_from_roots(graph, roots, max_hops)
        related = sorted(node for node in changed_ids if node in distances)
        # Coverage changes are global analysis metadata. They may enrich a related
        # candidate, but must never create a candidate for an unrelated Program.
        if not related:
            continue
        direct = sorted(node for node in changed_ids if node in set(roots))
        candidate_delta = {
            "related_changed_nodes": [{"node_id": node, "distance": distances.get(node)} for node in related],
            "direct_changed_roots": direct,
            "graph_delta": delta,
        }
        candidates.append({
            "candidate_id": _candidate_id(program["program_id"], baseline["adapter_id"], observed["adapter_id"], candidate_delta),
            "program_id": program["program_id"],
            "artifact_path": program["artifact_path"],
            "functional_design_ref": program["functional_design_ref"],
            "impact_kind": "DIRECT_SOURCE_CHANGE" if direct else "RELATED_IMPLEMENTATION_GRAPH_CHANGE",
            "max_hops": max_hops,
            "implementation_delta": candidate_delta,
            "program_spec_patch_scope": {
                "allowed_sections": ALLOWED_PROGRAM_SECTIONS,
                "forbidden_semantic_sections": FORBIDDEN_SEMANTIC_SECTIONS,
            },
            "review_required": True,
            "auto_apply": False,
            "business_truth_auto_update": False,
            "functional_design_auto_update": False,
            "artifact_file_modified": False,
        })

    return {
        "schema_version": 1,
        "capability": "PROGRAM_SPEC_SEMANTIC_REVERSE_CANDIDATE",
        "baseline_adapter_id": baseline["adapter_id"],
        "observed_adapter_id": observed["adapter_id"],
        "graph_delta_summary": {
            key: len(value) for key, value in delta.items()
        },
        "program_candidates": candidates,
        "summary": {
            "binding_count": len(programs),
            "candidate_count": len(candidates),
            "changed_node_or_edge_endpoint_count": len(changed_ids),
        },
        "safety": {
            "candidate_only": True,
            "artifact_files_modified": False,
            "functional_design_modified": False,
            "business_truth_modified": False,
            "automatic_rewrite": False,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-impact", required=True)
    parser.add_argument("--observed-impact", required=True)
    parser.add_argument("--program-bindings", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--max-hops", type=int, default=3)
    args = parser.parse_args(argv)
    try:
        result = generate(
            _load_json(Path(args.baseline_impact)),
            _load_json(Path(args.observed_impact)),
            _load_json(Path(args.program_bindings)),
            args.max_hops,
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 1
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
