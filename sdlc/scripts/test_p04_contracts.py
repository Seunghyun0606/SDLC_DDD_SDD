#!/usr/bin/env python3
"""Self-contained P0.4 TEST -> VERIFY contract tests."""

from copy import deepcopy
from validate_p04_contracts import validate_contract, validate_execution, validate_verification

H = "a" * 64


def assert_code(errors, code):
    assert any(e.startswith(code + ":") for e in errors), (code, errors)


def contract_case():
    return {
        "artifact_type": "TEST_CONTRACT", "contract_id": "TCN-1",
        "subject": {"rq_group_candidate_id": "RQG-CAND-X"},
        "source_binding": {"fixture_evidence": False, "production_source": True, "source_evidence_set_id": H},
        "acceptance_criteria": [{"id": "AC-1"}, {"id": "AC-2"}],
        "test_cases": [
            {"id": "TC-1", "ac_ids": ["AC-1"], "required": True},
            {"id": "TC-2", "ac_ids": ["AC-2"], "required": True},
        ],
        "coverage": {"required_ac_ids": ["AC-1", "AC-2"], "uncovered_ac_ids": [], "coverage_percent": 100},
        "execution_requirements": {"required_test_case_ids": ["TC-1", "TC-2"]},
        "review": {"business_rule_candidate_reviewed": True},
    }


def execution_case():
    return {
        "artifact_type": "TEST_EXECUTION_RESULT", "execution_result_id": "TEX-1",
        "subject": {"test_contract_id": "TCN-1"},
        "source_binding": {"source_evidence_set_id": H},
        "runtime_environment": {"actual_runtime": True},
        "execution": {"cases": [
            {"id": "TC-1", "state": "PASSED", "actual_result": "ok", "evidence": ["log-1"]},
            {"id": "TC-2", "state": "PASSED", "actual_result": "ok", "evidence": ["log-2"]},
        ]},
        "summary": {"required": 2, "passed": 2, "failed": 0, "blocked": 0, "not_executed": 0, "skipped": 0},
        "open_blockers": [],
    }


def verification_case():
    return {
        "artifact_type": "VERIFICATION_RESULT",
        "source_binding": {"source_evidence_set_id": H},
        "verification": {"state": "VERIFIED_PASS"},
        "claims": {"runtime_pass": True, "production_verified": True},
    }


def main():
    c, e, v = contract_case(), execution_case(), verification_case()
    assert validate_contract(c) == []
    assert validate_execution(c, e) == []
    assert validate_verification(c, e, v) == []

    bad = deepcopy(c); bad["test_cases"][1]["ac_ids"] = ["AC-X"]
    errs = validate_contract(bad); assert_code(errs, "TV-003"); assert_code(errs, "TV-004")

    bad = deepcopy(e); bad["execution"]["cases"][0]["evidence"] = []
    assert_code(validate_execution(c, bad), "TV-005")

    bad = deepcopy(e); bad["execution"]["cases"][0] = {"id": "TC-1", "state": "NOT_EXECUTED", "actual_result": "ok", "evidence": ["fake"]}
    bad["summary"] = {"required": 2, "passed": 1, "failed": 0, "blocked": 0, "not_executed": 1, "skipped": 0}
    assert_code(validate_execution(c, bad), "TV-006")

    badv = deepcopy(v); bade = deepcopy(e); bade["runtime_environment"]["actual_runtime"] = False
    assert_code(validate_verification(c, bade, badv), "TV-010")

    badc = deepcopy(c); badc["source_binding"]["production_source"] = False; badc["source_binding"]["fixture_evidence"] = True
    assert_code(validate_verification(badc, e, v), "TV-013")

    badc = deepcopy(c); badc["review"]["business_rule_candidate_reviewed"] = False
    assert_code(validate_verification(badc, e, v), "TV-012")

    print("OK: P0.4 TEST/VERIFY contract tests passed")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
