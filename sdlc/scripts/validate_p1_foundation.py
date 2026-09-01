#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path
import yaml

MODES = {"AUTO", "BROWNFIELD", "GREENFIELD", "HYBRID"}
PROVIDER_STATES = {"AVAILABLE", "DEGRADED", "UNAVAILABLE", "UNCONFIGURED", "DISABLED"}
OVERLAY_STATES = {"PROPOSED", "ACTIVE", "SUPERSEDED", "REJECTED"}
TRUTH_STATES = {"GIVEN", "OBSERVED", "INFERRED", "CONFIRMED", "OPEN"}
VALID_TRIGGERS = {
    "CORE_DEFAULT_CONFLICTS_WITH_OBSERVED_PROJECT_FACT",
    "REQUIRED_PROJECT_TERM_DIFFERS",
    "REQUIRED_ARTIFACT_OR_STAGE_DIFFERS",
    "PROVIDER_OR_PATH_REQUIRES_PROJECT_BINDING",
    "PROJECT_STANDARD_REQUIRES_OVERRIDE",
}


def load_yaml(path):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}


def validate_config(doc):
    errors = []
    if doc.get("principles", {}).get("require_upfront_project_customization") is not False:
        errors.append("P1-001 upfront customization must not be required")
    if doc.get("principles", {}).get("sample_or_pilot_required") is not False:
        errors.append("P1-002 sample/pilot must not be required by core")
    if doc.get("customization", {}).get("strategy") != "LATE_BOUND_OVERLAY":
        errors.append("P1-003 customization strategy must be LATE_BOUND_OVERLAY")
    if doc.get("baseline_index", {}).get("duplicate_truth") != "DENY":
        errors.append("P1-004 baseline index must not duplicate truth")
    return errors


def validate_bootstrap(doc):
    errors = []
    root = doc.get("project_bootstrap", {})
    if not root.get("project_id"):
        errors.append("P1-101 project_id required")
    if root.get("mode") not in MODES:
        errors.append("P1-102 invalid project mode")
    state = root.get("providers", {}).get("source_provider_state")
    if state not in PROVIDER_STATES:
        errors.append("P1-103 source_provider_state required and must be known")
    if root.get("customization", {}).get("upfront_customization_complete_required") is not False:
        errors.append("P1-104 bootstrap must not require customization completion")
    return errors


def validate_overlay(doc):
    errors = []
    root = doc.get("overlay", {})
    state = root.get("state")
    if state not in OVERLAY_STATES:
        errors.append("P1-201 invalid overlay state")
        return errors
    trigger = root.get("trigger", {})
    basis = root.get("basis", {})
    scope = root.get("scope", {})
    safety = root.get("safety", {})
    if trigger.get("type") not in VALID_TRIGGERS:
        errors.append("P1-202 overlay requires a valid observed-project trigger")
    if not trigger.get("reason"):
        errors.append("P1-203 overlay reason required")
    if basis.get("truth_state") not in TRUTH_STATES:
        errors.append("P1-204 invalid overlay truth state")
    if not scope.get("project_id"):
        errors.append("P1-205 overlay project scope required")
    if root.get("revision", 0) < 1:
        errors.append("P1-206 overlay revision must be >= 1")
    if safety.get("copies_core_truth"):
        errors.append("P1-207 overlay must not copy core truth")
    if safety.get("sample_specific_only"):
        errors.append("P1-208 sample-only customization is not allowed")
    if state == "ACTIVE" and basis.get("truth_state") in {"OBSERVED", "CONFIRMED"}:
        if not (basis.get("evidence_ids") or basis.get("source_refs")):
            errors.append("P1-209 active observed overlay requires evidence/source ref")
    if state == "ACTIVE" and basis.get("truth_state") == "GIVEN" and not basis.get("source_refs"):
        errors.append("P1-210 active GIVEN overlay requires source ref")
    change = root.get("change", {})
    if not change.get("target_key"):
        errors.append("P1-211 overlay target_key required")
    return errors


def validate_graph(doc):
    errors = []
    root = doc.get("reference_graph", {})
    nodes = root.get("nodes", [])
    edges = root.get("edges", [])
    node_ids = [x.get("node_id") for x in nodes]
    if any(not x for x in node_ids) or len(set(node_ids)) != len(node_ids):
        errors.append("P1-301 node ids must be non-empty and unique")
    node_set = set(node_ids)
    edge_ids = [x.get("edge_id") for x in edges]
    if any(not x for x in edge_ids) or len(set(edge_ids)) != len(edge_ids):
        errors.append("P1-302 edge ids must be non-empty and unique")
    unresolved = set(root.get("unresolved_references", []))
    for edge in edges:
        missing = [x for x in (edge.get("from_id"), edge.get("to_id")) if x not in node_set]
        for ref in missing:
            if ref not in unresolved:
                errors.append(f"P1-303 dangling reference not preserved as OPEN: {ref}")
        if not (edge.get("evidence_ids") or edge.get("source_refs")):
            errors.append(f"P1-304 edge provenance required: {edge.get('edge_id')}")
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=["config", "bootstrap", "overlay", "graph"])
    parser.add_argument("path")
    args = parser.parse_args()
    doc = load_yaml(args.path)
    funcs = {
        "config": validate_config,
        "bootstrap": validate_bootstrap,
        "overlay": validate_overlay,
        "graph": validate_graph,
    }
    errors = funcs[args.kind](doc)
    if errors:
        print("\n".join(errors))
        return 1
    print(f"OK: P1 {args.kind} contract valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
