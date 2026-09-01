#!/usr/bin/env python3
"""P0.1 regression tests for Legacy Normalizer, Group Boundary, and Pack Granularity."""

from normalize_legacy_requirements import group_rows, stable_group_id
from validate_p0_contracts import validate_boundary, validate_normalization, validate_stage_pack


def related_ids():
    return {k: [] for k in ("rq", "fr", "br", "ac", "proc", "pgm", "task", "tc")}


def assert_has(errors, code):
    assert any(e.startswith(code + ":") for e in errors), (code, errors)


def main():
    source = {
        "source": {"name": "requirements.xlsx/Sheet1", "revision": "rev-1"},
        "rows": [
            {"source_requirement_id": "REQ-001", "level1": "근태관리", "level2": "근태마감", "requirement_name": "근태마감 개선"},
            {"source_requirement_id": "REQ-002", "level1": "근태관리", "level2": "근태마감", "requirement_name": "근태마감 개선"},
            {"source_requirement_id": "REQ-003", "level1": "근태관리", "level2": "Batch", "requirement_name": "근무집계 개선"},
        ],
    }
    normalized = group_rows(source)
    assert validate_normalization(normalized) == []
    groups = normalized["legacy_requirement_normalization"]["candidate_groups"]
    assert len(groups) == 2
    assert groups[0]["group_id"] == stable_group_id("근태마감", "근태마감 개선")
    assert groups[0]["publish_canonical"] is False

    bad_normalized = group_rows(source)
    bad_normalized["legacy_requirement_normalization"]["source_rows"][1]["requirement_name"] = "다른 요구사항"
    assert_has(validate_normalization(bad_normalized), "LRN-019")

    bad_publish = group_rows(source)
    bad_publish["legacy_requirement_normalization"]["candidate_groups"][0]["publish_canonical"] = True
    assert_has(validate_normalization(bad_publish), "LRN-015")

    group_boundary = {
        "boundary_records": [{
            "scope_type": "GROUP",
            "source_group_id": groups[0]["group_id"],
            "source_requirement_ids": ["REQ-001", "REQ-002"],
            "source_count": 2,
            "decision": "UNRESOLVED",
            "status": "OPEN",
            "canonical_rq_ids": [],
            "canonical_fr_ids": [],
            "escalation": "L2_OR_HUMAN",
        }]
    }
    assert validate_boundary(group_boundary) == []

    bad_boundary = {"boundary_records": [dict(group_boundary["boundary_records"][0])]}
    bad_boundary["boundary_records"][0]["scope_type"] = "ROW"
    assert_has(validate_boundary(bad_boundary), "RQB-015")

    pack = {
        "stage_input_pack": {
            "metadata": {
                "pack_id": "SIP-P01-001",
                "project_id": "P-001",
                "stage": "DECOMPOSE",
                "source_revision": "rev-1",
                "profile": "STANDARD",
                "granularity": "GROUP",
                "source_group_id": groups[0]["group_id"],
            },
            "target": {
                "primary_id": "RQ-CANDIDATE-001",
                "target_type": "RQ_CANDIDATE",
                "boundary_status": "OPEN",
                "source_requirement_ids": ["REQ-001", "REQ-002"],
                "related_ids": related_ids(),
            },
            "evidence": [{"evidence_id": "EV-001"}],
            "resolved_facts": [{"fact_id": "FACT-001", "value": "근태마감 개선", "truth": "GIVEN", "evidence_ids": ["EV-001"]}],
            "open_items": [{
                "open_id": "OPEN-001",
                "type": "BOUNDARY_AMBIGUOUS",
                "question": "하나의 RQ인가?",
                "blocks_reasoning": True,
                "blocks_action": False,
                "required_evidence": ["Business Outcome"],
                "escalation": "L2_OR_HUMAN",
            }],
            "constraints": {
                "do_not_invent_missing_business_fact": True,
                "source_behavior_is_not_business_truth": True,
                "ambiguous_write_must_not_be_auto_selected": True,
            },
        }
    }
    assert validate_stage_pack(pack) == []

    bad_pack = {"stage_input_pack": dict(pack["stage_input_pack"])}
    bad_pack["stage_input_pack"]["metadata"] = dict(pack["stage_input_pack"]["metadata"])
    bad_pack["stage_input_pack"]["metadata"]["granularity"] = "ROW"
    errors = validate_stage_pack(bad_pack)
    assert_has(errors, "SIP-022")
    assert_has(errors, "SIP-026")

    print("OK: P0.1 contract tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
