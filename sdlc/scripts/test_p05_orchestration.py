#!/usr/bin/env python3
from copy import deepcopy
from orchestrate_e2e_status import build_status, validate_status

IDS = ["REQ-1", "REQ-2"]


def inputs():
    n = {"legacy_requirement_normalization": {"candidate_groups": [{
        "group_id": "RQG-CAND-X", "source_requirement_ids": IDS, "source_count": 2
    }]}}
    r = {"requirement_review_decision": {
        "source_group_id": "RQG-CAND-X", "source_requirement_ids": IDS, "source_count": 2,
        "boundary_status": "OPEN", "publish_allowed": False,
        "canonical_rq_ids": [], "canonical_fr_ids": []
    }}
    rs = {
        "source_diff_evidence": {"metadata": {"fixture_evidence": True}},
        "reverse_sync_candidate": {"source_group_id": "RQG-CAND-X", "status": "REVIEW_REQUIRED"}
    }
    v = {
        "subject": {"rq_group_candidate_id": "RQG-CAND-X"},
        "verification": {"state": "CONTRACT_PASS_RUNTIME_NOT_EXECUTED"},
        "claims": {"production_verified": False},
        "open_blockers": ["TEST_COMMAND_OPEN", "RUNTIME_ENVIRONMENT_UNAVAILABLE", "BUSINESS_RULE_REVIEW_OPEN"],
    }
    return n, r, rs, v


def assert_code(errors, code):
    assert any(e.startswith(code + ":") for e in errors), (code, errors)


def main():
    n, r, rs, v = inputs()
    status, errors = build_status(n, r, rs, v)
    assert errors == []
    assert status["overall"]["state"] == "ACTION_REQUIRED"
    assert status["overall"]["release_ready"] is False
    assert status["truth_guards"]["candidate_is_not_canonical"] is True
    assert status["truth_guards"]["fixture_is_not_production_source"] is True
    assert status["truth_guards"]["contract_coverage_is_not_runtime_pass"] is True
    assert len(status["blockers"]) >= 4
    assert validate_status(status) == []

    bad_rs = deepcopy(rs)
    bad_rs["reverse_sync_candidate"]["source_group_id"] = "RQG-CAND-Y"
    _, errors = build_status(n, r, bad_rs, v)
    assert_code(errors, "E2E-003")

    bad_v = deepcopy(v)
    bad_v["subject"]["rq_group_candidate_id"] = "RQG-CAND-Y"
    _, errors = build_status(n, r, rs, bad_v)
    assert_code(errors, "E2E-004")

    bad_r = deepcopy(r)
    bad_r["requirement_review_decision"]["source_requirement_ids"] = ["REQ-1"]
    _, errors = build_status(n, bad_r, rs, v)
    assert_code(errors, "E2E-005")

    ready = deepcopy(status)
    ready["overall"]["state"] = "READY_FOR_RELEASE"
    assert_code(validate_status(ready), "E2E-101")
    assert_code(validate_status(ready), "E2E-102")

    bad_guard = deepcopy(status)
    bad_guard["truth_guards"]["source_behavior_is_not_business_truth"] = False
    assert_code(validate_status(bad_guard), "E2E-103")

    print("OK: P0.5 E2E orchestration tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
