#!/usr/bin/env python3
"""Detect source evidence drift and create a non-destructive reverse review plan."""
from __future__ import annotations

import argparse
import json
from collections import deque
from pathlib import Path
from typing import Any

IMPACT_PRIORITY = {
    "CHECK_REQUIRED_REVERSE": 1,
    "STALE_PROPAGATED": 2,
    "STALE_SOURCE_EVIDENCE": 3,
}


def _evidence_key(item: dict[str, Any]) -> str:
    path = str(item.get("path", "")).strip()
    symbol = str(item.get("symbol", "")).strip()
    if not path:
        raise ValueError("source evidence path is required")
    return f"{path}::{symbol}"


def _index_source_manifest(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if data.get("schema_version") != 1:
        raise ValueError("unsupported source manifest schema")
    if not data.get("source_ref"):
        raise ValueError("source_ref is required")
    result: dict[str, dict[str, Any]] = {}
    for item in data.get("evidence", []):
        key = _evidence_key(item)
        if key in result:
            raise ValueError(f"duplicate source evidence key: {key}")
        if not item.get("hash"):
            raise ValueError(f"source hash is required: {key}")
        result[key] = dict(item)
    return result


def _source_drift(baseline: dict[str, Any], observed: dict[str, Any]) -> list[dict[str, Any]]:
    before = _index_source_manifest(baseline)
    after = _index_source_manifest(observed)
    rows: list[dict[str, Any]] = []
    for key in sorted(set(before) | set(after)):
        old = before.get(key)
        new = after.get(key)
        if old is None:
            state = "ADDED"
        elif new is None:
            state = "DELETED"
        elif old["hash"] != new["hash"]:
            state = "MODIFIED"
        else:
            state = "UNCHANGED"
        rows.append({
            "evidence_key": key,
            "path": (new or old).get("path"),
            "symbol": (new or old).get("symbol", ""),
            "state": state,
            "before_hash": old.get("hash") if old else None,
            "after_hash": new.get("hash") if new else None,
        })
    return rows


def _validate_artifact_index(data: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    if data.get("schema_version") != 1:
        raise ValueError("unsupported artifact evidence index schema")
    artifacts: dict[str, dict[str, Any]] = {}
    for artifact in data.get("artifacts", []):
        artifact_id = str(artifact.get("artifact_id", "")).strip()
        if not artifact_id:
            raise ValueError("artifact_id is required")
        if artifact_id in artifacts:
            raise ValueError(f"duplicate artifact_id: {artifact_id}")
        if not artifact.get("artifact_type"):
            raise ValueError(f"artifact_type is required: {artifact_id}")
        if not artifact.get("status"):
            raise ValueError(f"artifact status is required: {artifact_id}")
        for evidence in artifact.get("source_evidence", []):
            _evidence_key(evidence)
            if not evidence.get("source_hash"):
                raise ValueError(f"artifact source_hash is required: {artifact_id}")
        artifacts[artifact_id] = dict(artifact)

    edges: list[dict[str, Any]] = []
    for edge in data.get("propagation_edges", []):
        source = str(edge.get("from_artifact", "")).strip()
        target = str(edge.get("to_artifact", "")).strip()
        policy = edge.get("on_source_drift")
        if source not in artifacts or target not in artifacts:
            raise ValueError(f"propagation edge endpoint missing: {source}->{target}")
        if policy not in {"STALE", "CHECK_REQUIRED", "NONE"}:
            raise ValueError(f"unsupported propagation policy: {policy}")
        edges.append(dict(edge))
    return artifacts, edges


def _set_impact(impacts: dict[str, dict[str, Any]], artifact_id: str, status: str, reason: dict[str, Any]) -> bool:
    current = impacts.get(artifact_id)
    if current is None or IMPACT_PRIORITY[status] > IMPACT_PRIORITY[current["impact_status"]]:
        impacts[artifact_id] = {
            "artifact_id": artifact_id,
            "impact_status": status,
            "reasons": [reason],
        }
        return True
    if IMPACT_PRIORITY[status] == IMPACT_PRIORITY[current["impact_status"]]:
        if reason not in current["reasons"]:
            current["reasons"].append(reason)
    return False


def analyze(baseline: dict[str, Any], observed: dict[str, Any], artifact_index: dict[str, Any]) -> dict[str, Any]:
    before = _index_source_manifest(baseline)
    after = _index_source_manifest(observed)
    drift = _source_drift(baseline, observed)
    drift_by_key = {row["evidence_key"]: row for row in drift}
    artifacts, edges = _validate_artifact_index(artifact_index)

    impacts: dict[str, dict[str, Any]] = {}
    stale_queue: deque[str] = deque()

    for artifact_id, artifact in artifacts.items():
        for evidence in artifact.get("source_evidence", []):
            key = _evidence_key(evidence)
            observed_evidence = after.get(key)
            recorded_hash = evidence.get("source_hash")
            reason: dict[str, Any] | None = None
            if observed_evidence is None:
                reason = {"kind": "SOURCE_EVIDENCE_DELETED", "evidence_key": key, "recorded_hash": recorded_hash}
            elif recorded_hash != observed_evidence.get("hash"):
                reason = {
                    "kind": "RECORDED_HASH_MISMATCH",
                    "evidence_key": key,
                    "recorded_hash": recorded_hash,
                    "observed_hash": observed_evidence.get("hash"),
                    "drift_state": drift_by_key.get(key, {}).get("state"),
                }
            elif key in drift_by_key and drift_by_key[key]["state"] == "DELETED":
                reason = {"kind": "SOURCE_EVIDENCE_DELETED", "evidence_key": key, "recorded_hash": recorded_hash}

            if reason is not None:
                if _set_impact(impacts, artifact_id, "STALE_SOURCE_EVIDENCE", reason):
                    stale_queue.append(artifact_id)

    outgoing: dict[str, list[dict[str, Any]]] = {}
    for edge in edges:
        outgoing.setdefault(edge["from_artifact"], []).append(edge)

    expanded: set[str] = set()
    while stale_queue:
        source_artifact = stale_queue.popleft()
        if source_artifact in expanded:
            continue
        expanded.add(source_artifact)
        for edge in outgoing.get(source_artifact, []):
            policy = edge["on_source_drift"]
            if policy == "NONE":
                continue
            target = edge["to_artifact"]
            status = "STALE_PROPAGATED" if policy == "STALE" else "CHECK_REQUIRED_REVERSE"
            reason = {
                "kind": "PROPAGATED_FROM_ARTIFACT",
                "from_artifact": source_artifact,
                "edge_kind": edge.get("kind", "UNSPECIFIED"),
                "policy": policy,
                "note": edge.get("note"),
            }
            became_stronger = _set_impact(impacts, target, status, reason)
            if policy == "STALE" and became_stronger:
                stale_queue.append(target)

    artifact_impacts = []
    for artifact_id in sorted(impacts):
        item = impacts[artifact_id]
        item["artifact_type"] = artifacts[artifact_id]["artifact_type"]
        item["previous_status"] = artifacts[artifact_id]["status"]
        artifact_impacts.append(item)

    reverse_candidates = []
    for item in artifact_impacts:
        stale = item["impact_status"].startswith("STALE")
        reverse_candidates.append({
            "artifact_id": item["artifact_id"],
            "artifact_type": item["artifact_type"],
            "candidate_action": "REGENERATE_FROM_CURRENT_EVIDENCE" if stale else "HUMAN_REVIEW_REQUIRED",
            "auto_apply": False,
            "business_truth_auto_update": False,
        })

    return {
        "schema_version": 1,
        "baseline_ref": baseline["source_ref"],
        "observed_ref": observed["source_ref"],
        "source_drift": drift,
        "artifact_impacts": artifact_impacts,
        "reverse_candidates": reverse_candidates,
        "summary": {
            "source_added": sum(1 for x in drift if x["state"] == "ADDED"),
            "source_modified": sum(1 for x in drift if x["state"] == "MODIFIED"),
            "source_deleted": sum(1 for x in drift if x["state"] == "DELETED"),
            "source_unchanged": sum(1 for x in drift if x["state"] == "UNCHANGED"),
            "direct_stale_artifacts": sum(1 for x in artifact_impacts if x["impact_status"] == "STALE_SOURCE_EVIDENCE"),
            "propagated_stale_artifacts": sum(1 for x in artifact_impacts if x["impact_status"] == "STALE_PROPAGATED"),
            "check_required_artifacts": sum(1 for x in artifact_impacts if x["impact_status"] == "CHECK_REQUIRED_REVERSE"),
        },
        "safety": {
            "artifact_files_modified": False,
            "business_truth_modified": False,
            "reverse_result_is_candidate_only": True,
        },
    }


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--observed", required=True)
    parser.add_argument("--artifact-index", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        result = analyze(
            _read_json(Path(args.baseline)),
            _read_json(Path(args.observed)),
            _read_json(Path(args.artifact_index)),
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
