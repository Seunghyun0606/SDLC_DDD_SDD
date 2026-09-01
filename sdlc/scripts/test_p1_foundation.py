#!/usr/bin/env python3
from pathlib import Path
import importlib.util
import copy
import yaml

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "sdlc/scripts/validate_p1_foundation.py"

spec = importlib.util.spec_from_file_location("p1v", VALIDATOR)
p1v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p1v)


def load(rel):
    return yaml.safe_load((ROOT / rel).read_text(encoding="utf-8")) or {}


def assert_has(errors, code):
    assert any(e.startswith(code) for e in errors), (code, errors)


def main():
    config = load("sdlc/config/p1-foundation.yaml")
    bootstrap = load("sdlc/design/validation/p1-foundation-knowledge-bootstrap-v1/generic-project-bootstrap.yaml")
    overlay = load("sdlc/design/validation/p1-foundation-knowledge-bootstrap-v1/generic-project-overlay.yaml")
    graph = load("sdlc/design/validation/p1-foundation-knowledge-bootstrap-v1/generic-reference-graph.yaml")

    assert p1v.validate_config(config) == []
    assert p1v.validate_bootstrap(bootstrap) == []
    assert p1v.validate_overlay(overlay) == []
    assert p1v.validate_graph(graph) == []

    bad = copy.deepcopy(config)
    bad["principles"]["require_upfront_project_customization"] = True
    assert_has(p1v.validate_config(bad), "P1-001")

    bad = copy.deepcopy(bootstrap)
    bad["project_bootstrap"]["customization"]["upfront_customization_complete_required"] = True
    assert_has(p1v.validate_bootstrap(bad), "P1-104")

    bad = copy.deepcopy(overlay)
    bad["overlay"]["safety"]["sample_specific_only"] = True
    assert_has(p1v.validate_overlay(bad), "P1-208")

    bad = copy.deepcopy(overlay)
    bad["overlay"]["trigger"]["type"] = "JUST_IN_CASE"
    assert_has(p1v.validate_overlay(bad), "P1-202")

    bad = copy.deepcopy(graph)
    bad["reference_graph"]["edges"][0]["evidence_ids"] = []
    bad["reference_graph"]["edges"][0]["source_refs"] = []
    assert_has(p1v.validate_graph(bad), "P1-304")

    bad = copy.deepcopy(graph)
    bad["reference_graph"]["edges"][0]["to_id"] = "MISSING-NODE"
    assert_has(p1v.validate_graph(bad), "P1-303")

    forbidden = ["REQ_TM_TE", "RQG-CAND-6BB6D66548", "AttendanceClose", "TB_ATT_", "10분"]
    core_paths = [
        ROOT / "sdlc/config/p1-foundation.yaml",
        ROOT / "sdlc/design/contracts/p1-foundation-late-customization.md",
        ROOT / "sdlc/scripts/validate_p1_foundation.py",
        ROOT / "sdlc/scripts/resolve_project_overlay.py",
    ]
    core_text = "\n".join(p.read_text(encoding="utf-8") for p in core_paths)
    for token in forbidden:
        assert token not in core_text, f"pilot token leaked into P1 core: {token}"

    print("OK: P1 foundation tests passed")


if __name__ == "__main__":
    main()
