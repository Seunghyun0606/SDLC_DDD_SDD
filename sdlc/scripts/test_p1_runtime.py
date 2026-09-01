#!/usr/bin/env python3
import importlib.util
import tempfile
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]


def load_module(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    lint = load_module("p1lint", "sdlc/scripts/lint_p1_knowledge.py")

    knowledge = {
        "knowledge_candidate": {
            "knowledge_id": "K-DEMO-001",
            "project_id": "DEMO",
            "type": "PROGRAM_RESPONSIBILITY",
            "title": "generic responsibility",
            "statement": "generic observed responsibility",
            "truth_state": "OBSERVED",
            "promotion_state": "CANDIDATE",
            "revision": 1,
            "provenance": {"evidence_ids": ["E-1"], "source_refs": ["src/a"]},
            "review": {"required": True, "reviewed_by": "", "decision_basis": ""},
        }
    }
    assert lint.lint_knowledge(knowledge) == []

    promoted_without_review = yaml.safe_load(yaml.safe_dump(knowledge))
    promoted_without_review["knowledge_candidate"]["promotion_state"] = "PROMOTED"
    assert any(x.startswith("P1K-006") for x in lint.lint_knowledge(promoted_without_review))

    term1 = {
        "glossary_entry": {
            "term_id": "TERM-1", "project_id": "DEMO", "term": "Order", "normalized_term": "order",
            "truth_state": "GIVEN", "status": "CONFIRMED",
            "provenance": {"source_refs": ["doc://official"]},
        }
    }
    term2 = yaml.safe_load(yaml.safe_dump(term1))
    term2["glossary_entry"]["term_id"] = "TERM-2"
    assert any(x.startswith("P1G-006") for x in lint.lint_glossary([term1, term2]))

    forbidden = ["REQ_TM_TE", "RQG-CAND-6BB6D66548", "AttendanceClose", "TB_ATT_", "10분"]
    core_files = [
        "sdlc/config/p1-foundation.yaml",
        "sdlc/design/contracts/p1-foundation-late-customization.md",
        "sdlc/scripts/lint_p1_knowledge.py",
        "sdlc/scripts/evaluate_open_items.py",
        "sdlc/scripts/build_baseline_cache.py",
        "sdlc/scripts/assess_p1_scale_out.py",
    ]
    text = "\n".join((ROOT / x).read_text(encoding="utf-8") for x in core_files)
    for token in forbidden:
        assert token not in text, token

    print("OK: P1 knowledge/runtime tests passed")


if __name__ == "__main__":
    main()
