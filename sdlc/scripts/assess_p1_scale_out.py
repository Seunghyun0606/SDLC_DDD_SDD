#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path
import yaml


def load(path):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("bootstrap")
    p.add_argument("graph")
    p.add_argument("--real-source", action="store_true")
    p.add_argument("--representative-slice-reviewed", action="store_true")
    p.add_argument("--customization-conflicts-recorded", action="store_true")
    args = p.parse_args()

    bootstrap = load(args.bootstrap).get("project_bootstrap", {})
    graph = load(args.graph).get("reference_graph", {})

    blockers = []
    if not bootstrap.get("project_id"):
        blockers.append("FOUNDATION_STATE_INVALID")
    if not graph.get("graph_id") or graph.get("validation", {}).get("dangling_node_refs"):
        blockers.append("REFERENCE_GRAPH_INVALID")
    if not args.customization_conflicts_recorded:
        blockers.append("CUSTOMIZATION_CONFLICT_STATUS_OPEN")
    if not args.real_source:
        blockers.append("REAL_SOURCE_REQUIRED")
    if not args.representative_slice_reviewed:
        blockers.append("REPRESENTATIVE_VERTICAL_SLICE_REQUIRED")

    if not blockers:
        state = "READY_FOR_SCALE_OUT"
    elif set(blockers).issubset({"REAL_SOURCE_REQUIRED", "REPRESENTATIVE_VERTICAL_SLICE_REQUIRED"}):
        state = "FOUNDATION_READY_REAL_SLICE_REQUIRED"
    else:
        state = "ACTION_REQUIRED"

    result = {
        "p1_scale_out_state": state,
        "production_ready": False,
        "real_source_confirmed": args.real_source,
        "representative_slice_reviewed": args.representative_slice_reviewed,
        "customization_conflicts_recorded": args.customization_conflicts_recorded,
        "blockers": blockers,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if state == "READY_FOR_SCALE_OUT" else 2


if __name__ == "__main__":
    sys.exit(main())
