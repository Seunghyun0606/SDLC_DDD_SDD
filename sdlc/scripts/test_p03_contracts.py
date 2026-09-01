#!/usr/bin/env python3
"""Self-contained P0.3 validator tests."""

from copy import deepcopy

from validate_p03_contracts import validate_discovery, validate_reverse

H1 = "a" * 64
H2 = "b" * 64


def assert_code(errors, code):
    assert any(e.startswith(code + ":") for e in errors), (code, errors)


def discovery_case():
    return {
        "source_discovery_result": {
            "metadata": {"discovery_id": "DISC-1", "source_root": "fixture", "source_revision": "rev-1", "provider_state": "AVAILABLE"},
            "target": {"source_group_id": "RQG-CAND-X", "program_ids": ["PGM-1"]},
            "artifacts": [{"path": "A.java", "file_hash": H1, "direct_program_ids": ["PGM-1"]}],
            "evidence": [{"evidence_id": "EV-1", "truth": "OBSERVED", "locator": "A.java", "value": "x"}],
        }
    }


def reverse_case():
    return {
        "source_diff_evidence": {
            "metadata": {"source_revision_before": "rev-1", "source_revision_after": "rev-2"},
            "changed_files": [{"path": "A.java", "before_hash": H1, "after_hash": H2, "direct_program_ids": ["PGM-1"]}],
            "direct_program_ids": ["PGM-1"],
        },
        "reverse_sync_candidate": {
            "source_revision_before": "rev-1",
            "source_revision_after": "rev-2",
            "direct_program_ids": ["PGM-1"],
            "semantic_change_class": "BUSINESS_RULE_CANDIDATE",
            "protected_human_truth": True,
            "required_review": "L2_OR_HUMAN",
            "status": "REVIEW_REQUIRED",
            "stale_candidates": [{"artifact": "impact.md", "relation": "impact_analysis", "state": "STALE_CANDIDATE"}],
            "review_candidates": [{"artifact": "requirement.md", "relation": "requirement", "state": "REVIEW_CANDIDATE"}],
        },
    }


def main():
    d = discovery_case()
    assert validate_discovery(d) == []
    bad = deepcopy(d); bad["source_discovery_result"]["artifacts"][0]["file_hash"] = "bad"
    assert_code(validate_discovery(bad), "DISC-007")
    bad = deepcopy(d); bad["source_discovery_result"]["evidence"][0]["truth"] = "CONFIRMED"
    assert_code(validate_discovery(bad), "DISC-009")

    r = reverse_case()
    assert validate_reverse(r) == []
    bad = deepcopy(r); bad["reverse_sync_candidate"]["protected_human_truth"] = False
    assert_code(validate_reverse(bad), "RS-011")
    bad = deepcopy(r); bad["reverse_sync_candidate"]["stale_candidates"][0]["relation"] = "requirement"
    assert_code(validate_reverse(bad), "RS-015")
    bad = deepcopy(r); bad["source_diff_evidence"]["changed_files"][0]["after_hash"] = H1
    assert_code(validate_reverse(bad), "RS-005")

    print("OK: P0.3 source discovery/reverse sync contract tests passed")
    return 0

if __name__ == "__main__": raise SystemExit(main())
