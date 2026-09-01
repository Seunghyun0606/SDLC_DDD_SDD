#!/usr/bin/env python3
"""Self-contained P0.2 tests for review queue and canonical publish guards."""

from build_requirement_review_queue import build
from validate_p02_contracts import validate_publish_request, validate_review_queue


def assert_code(errors, code):
    assert any(e.startswith(code + ":") for e in errors), (code, errors)


def synthetic_inputs():
    groups = {
        "source": {"file": "sample.xlsx"},
        "candidate_groups": [
            {
                "candidate_group_id": "RQG-CAND-001",
                "level1": "근태관리",
                "level2": "근태마감",
                "requirement_name": "근태마감 개선",
                "source_count": 2,
                "source_ids": ["LEG-001", "LEG-002"],
            }
        ],
    }
    crosswalk = {
        "crosswalk": [
            {
                "legacy_pilot_group_id": "RQG-CAND-001",
                "stable_group_id": "RQG-CAND-ABCDEF1234",
            }
        ]
    }
    return groups, crosswalk


def valid_publish():
    return {
        "canonical_publish_request": {
            "review_snapshot": {
                "review_id": "RQR-ABCDEF1234",
                "source_group_id": "RQG-CAND-ABCDEF1234",
                "source_requirement_ids": ["LEG-001", "LEG-002"],
                "source_count": 2,
                "decision": "KEEP_AS_RQ",
                "boundary_status": "CONFIRMED",
                "decision_basis": "업무 담당자 확인",
                "evidence_ids": ["EV-DEC-001"],
                "decided_by": "human-reviewer",
                "decided_at": "2026-09-02T00:00:00+09:00",
                "decision_revision": 1,
                "source_revision": "rev-1",
            },
            "id_allocation": {
                "status": "PREALLOCATED",
                "canonical_rq_ids": ["RQ-0001"],
                "canonical_fr_ids": [],
            },
            "publish": {
                "canonical_rq_ids": ["RQ-0001"],
                "canonical_fr_ids": [],
            },
            "trace": {
                "review_id": "RQR-ABCDEF1234",
                "decision_revision": 1,
                "evidence_ids": ["EV-DEC-001"],
            },
        }
    }


def main():
    groups, crosswalk = synthetic_inputs()
    queue = build(groups, crosswalk)
    errors = validate_review_queue(queue)
    assert errors == [], errors
    item = queue["requirement_review_queue"]["items"][0]
    assert item["review_id"] == "RQR-ABCDEF1234"
    assert item["decision"] == "UNRESOLVED"
    assert item["publish_allowed"] is False

    bad_queue = build(groups, crosswalk)
    bad_queue["requirement_review_queue"]["items"][0]["publish_allowed"] = True
    errors = validate_review_queue(bad_queue)
    assert_code(errors, "RQR-012")
    assert_code(errors, "RQR-015")

    duplicate_groups, crosswalk = synthetic_inputs()
    duplicate_groups["candidate_groups"].append(
        {
            "candidate_group_id": "RQG-CAND-002",
            "level1": "근태관리",
            "level2": "다른영역",
            "requirement_name": "다른요구",
            "source_count": 1,
            "source_ids": ["LEG-001"],
        }
    )
    crosswalk["crosswalk"].append(
        {"legacy_pilot_group_id": "RQG-CAND-002", "stable_group_id": "RQG-CAND-FFFF000001"}
    )
    try:
        build(duplicate_groups, crosswalk)
        raise AssertionError("duplicate source ID must fail")
    except ValueError as exc:
        assert "multiple groups" in str(exc)

    publish = valid_publish()
    errors = validate_publish_request(publish)
    assert errors == [], errors

    open_publish = valid_publish()
    open_publish["canonical_publish_request"]["review_snapshot"]["boundary_status"] = "OPEN"
    errors = validate_publish_request(open_publish)
    assert_code(errors, "PUB-005")

    unallocated = valid_publish()
    unallocated["canonical_publish_request"]["id_allocation"]["status"] = "OPEN"
    errors = validate_publish_request(unallocated)
    assert_code(errors, "PUB-008")

    candidate_id_reuse = valid_publish()
    root = candidate_id_reuse["canonical_publish_request"]
    root["id_allocation"]["canonical_rq_ids"] = ["RQG-CAND-ABCDEF1234"]
    root["publish"]["canonical_rq_ids"] = ["RQG-CAND-ABCDEF1234"]
    errors = validate_publish_request(candidate_id_reuse)
    assert_code(errors, "PUB-010")

    split_bad = valid_publish()
    root = split_bad["canonical_publish_request"]
    root["review_snapshot"]["decision"] = "SPLIT_TO_MULTIPLE_RQ"
    errors = validate_publish_request(split_bad)
    assert_code(errors, "PUB-015")

    trace_mismatch = valid_publish()
    trace_mismatch["canonical_publish_request"]["trace"]["decision_revision"] = 2
    errors = validate_publish_request(trace_mismatch)
    assert_code(errors, "PUB-018")

    print("OK: P0.2 review/publish contract tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
