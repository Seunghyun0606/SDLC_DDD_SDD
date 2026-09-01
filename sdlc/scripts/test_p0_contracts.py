#!/usr/bin/env python3
"""Self-contained contract tests for P0 deterministic validators."""

from validate_p0_contracts import validate_boundary, validate_stage_pack


def valid_stage_pack():
    return {
        "stage_input_pack": {
            "metadata": {
                "pack_id": "SIP-TEST-001",
                "project_id": "P-001",
                "stage": "DECOMPOSE",
                "source_revision": "rev-1",
                "profile": "STANDARD",
            },
            "target": {
                "primary_id": "RQ-CANDIDATE-001",
                "target_type": "RQ_CANDIDATE",
                "boundary_status": "OPEN",
                "source_requirement_ids": ["LEGACY-001"],
                "related_ids": {k: [] for k in ("rq", "fr", "br", "ac", "proc", "pgm", "task", "tc")},
            },
            "resolved_facts": [
                {
                    "fact_id": "FACT-001",
                    "value": "원문 값",
                    "truth": "GIVEN",
                    "evidence_ids": ["EV-001"],
                }
            ],
            "evidence": [{"evidence_id": "EV-001"}],
            "open_items": [
                {
                    "open_id": "OPEN-001",
                    "type": "BOUNDARY_AMBIGUOUS",
                    "question": "RQ 경계를 확인해야 하는가?",
                    "blocks_reasoning": True,
                    "blocks_action": False,
                    "required_evidence": ["업무 Outcome 기준"],
                    "escalation": "L2_OR_HUMAN",
                }
            ],
            "constraints": {
                "do_not_invent_missing_business_fact": True,
                "source_behavior_is_not_business_truth": True,
                "ambiguous_write_must_not_be_auto_selected": True,
            },
        }
    }


def valid_boundary():
    return {
        "boundary_records": [
            {
                "source_requirement_id": "LEGACY-001",
                "decision": "UNRESOLVED",
                "status": "OPEN",
                "canonical_rq_ids": [],
                "canonical_fr_ids": [],
                "escalation": "L2_OR_HUMAN",
            }
        ]
    }


def assert_contains(errors, code):
    assert any(e.startswith(code + ":") for e in errors), (code, errors)


def main():
    errors = validate_stage_pack(valid_stage_pack())
    assert errors == [], errors

    bad_stage = valid_stage_pack()
    bad_stage["stage_input_pack"]["target"]["target_type"] = "RQ"
    bad_stage["stage_input_pack"]["target"]["boundary_status"] = "CONFIRMED"
    errors = validate_stage_pack(bad_stage)
    assert_contains(errors, "SIP-018")
    assert_contains(errors, "SIP-019")

    errors = validate_boundary(valid_boundary())
    assert errors == [], errors

    bad_boundary = {
        "boundary_records": [
            {
                "source_requirement_id": "LEGACY-002",
                "decision": "SPLIT_TO_MULTIPLE_RQ",
                "status": "CONFIRMED",
                "canonical_rq_ids": ["RQ-0001"],
                "canonical_fr_ids": [],
                "evidence_ids": [],
                "decided_by": None,
            }
        ]
    }
    errors = validate_boundary(bad_boundary)
    assert_contains(errors, "RQB-010")
    assert_contains(errors, "RQB-011")

    duplicate = valid_boundary()
    duplicate["boundary_records"].append(dict(duplicate["boundary_records"][0]))
    errors = validate_boundary(duplicate)
    assert_contains(errors, "RQB-012")

    print("OK: P0 contract tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
