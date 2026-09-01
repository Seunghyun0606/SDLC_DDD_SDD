#!/usr/bin/env python3
"""Build one deterministic E2E /check status from P0.1~P0.4 artifacts."""

from __future__ import annotations
import argparse
import sys
from pathlib import Path
import yaml


def load(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def add(errors, code, message):
    errors.append(f"{code}: {message}")


def find_group(normalization, group_id):
    root = (normalization or {}).get("legacy_requirement_normalization") or {}
    for group in root.get("candidate_groups") or []:
        if group.get("group_id") == group_id:
            return group
    return None


def build_status(normalization, review_doc, reverse_doc, verification):
    errors = []
    review = (review_doc or {}).get("requirement_review_decision") or {}
    reverse = (reverse_doc or {}).get("reverse_sync_candidate") or {}
    group_id = review.get("source_group_id")
    if not group_id:
        add(errors, "E2E-001", "review source_group_id is required")
        return None, errors

    group = find_group(normalization, group_id)
    if not group:
        add(errors, "E2E-002", f"normalization group not found: {group_id}")
    if reverse.get("source_group_id") != group_id:
        add(errors, "E2E-003", "reverse-sync source_group_id must match review")
    subject = (verification or {}).get("subject") or {}
    if subject.get("rq_group_candidate_id") != group_id:
        add(errors, "E2E-004", "verification rq_group_candidate_id must match review")

    if group:
        norm_ids = set(group.get("source_requirement_ids") or [])
        review_ids = set(review.get("source_requirement_ids") or [])
        if norm_ids != review_ids:
            add(errors, "E2E-005", "normalization/review source_requirement_ids mismatch")
        if group.get("source_count") != len(norm_ids):
            add(errors, "E2E-006", "normalization source_count mismatch")
        if review.get("source_count") != len(review_ids):
            add(errors, "E2E-007", "review source_count mismatch")

    if errors:
        return None, errors

    stages = [{
        "stage": "NORMALIZE",
        "display_name_ko": "레거시 요구사항 정규화",
        "state": "COMPLETE",
        "summary_ko": f"{group.get('source_count')}개 Source Row가 Stable Candidate Group 1개로 보존됨",
        "blocking": False,
    }]

    boundary_open = review.get("boundary_status") != "CONFIRMED"
    stages.append({
        "stage": "BOUNDARY_REVIEW",
        "display_name_ko": "요구사항 경계 검토",
        "state": "ACTION_REQUIRED" if boundary_open else "COMPLETE",
        "summary_ko": "Canonical RQ/FR 경계가 아직 OPEN이며 L2/Human 검토 필요" if boundary_open else "Canonical 경계가 검토 완료됨",
        "blocking": boundary_open,
    })

    publish_allowed = review.get("publish_allowed") is True
    canonical_ids = list(review.get("canonical_rq_ids") or []) + list(review.get("canonical_fr_ids") or [])
    stages.append({
        "stage": "CANONICAL_PUBLISH",
        "display_name_ko": "Canonical 발행",
        "state": "BLOCKED" if not publish_allowed else ("READY" if canonical_ids else "BLOCKED"),
        "summary_ko": "경계 미확정으로 Canonical 발행 금지" if not publish_allowed else ("사전 할당 Canonical ID로 Publish Request 생성 가능" if canonical_ids else "Publish 허용 상태지만 사전 할당 Canonical ID가 없음"),
        "blocking": not (publish_allowed and canonical_ids),
    })

    fixture_only = bool(((reverse_doc or {}).get("source_diff_evidence") or {}).get("metadata", {}).get("fixture_evidence"))
    reverse_review = reverse.get("status") == "REVIEW_REQUIRED"
    stages.append({
        "stage": "SOURCE_DISCOVERY_REVERSE_SYNC",
        "display_name_ko": "소스 탐색·영향·역동기화",
        "state": "REVIEW_REQUIRED" if reverse_review else "COMPLETE",
        "summary_ko": "Synthetic Source에서 Direct PGM/ART 영향은 확인했으나 Business Rule 후보는 검토 필요" if fixture_only else "Source Evidence 기반 영향 및 역동기화 후보 생성 완료",
        "blocking": reverse_review,
    })

    v = (verification or {}).get("verification") or {}
    claims = (verification or {}).get("claims") or {}
    vstate = v.get("state") or (verification or {}).get("status")
    production_verified = claims.get("production_verified") is True
    if vstate == "VERIFIED_PASS" and production_verified:
        test_state, test_blocking = "COMPLETE", False
        test_summary = "실제 Runtime 테스트 및 Production Verification 완료"
    elif vstate == "CONTRACT_PASS_RUNTIME_NOT_EXECUTED":
        test_state, test_blocking = "BLOCKED_RUNTIME", True
        test_summary = "AC/TC 계약은 통과했지만 Runtime 테스트가 실행되지 않음"
    elif vstate == "VERIFIED_FAIL":
        test_state, test_blocking = "FAILED", True
        test_summary = "실행 테스트 또는 Verification 실패"
    else:
        test_state, test_blocking = "ACTION_REQUIRED", True
        test_summary = f"Verification 상태 확인 필요: {vstate or 'UNKNOWN'}"
    stages.append({
        "stage": "TEST_VERIFY",
        "display_name_ko": "테스트·검증",
        "state": test_state,
        "summary_ko": test_summary,
        "blocking": test_blocking,
    })

    blockers = []
    if boundary_open:
        blockers.append({"code": "BOUNDARY_REVIEW_OPEN", "owner": "L2_OR_HUMAN", "action_ko": "근태마감 그룹의 독립 Business Outcome/Owner/Release/AC 경계를 검토한다."})
    if fixture_only:
        blockers.append({"code": "ACTUAL_SOURCE_REQUIRED", "owner": "ENGINEERING_OWNER", "action_ko": "실제 고객 Repository/Snapshot으로 Source Discovery를 재실행한다."})
    if reverse_review:
        blockers.append({"code": "BUSINESS_RULE_REVIEW_REQUIRED", "owner": "L2_OR_HUMAN", "action_ko": "Source Diff의 BUSINESS_RULE_CANDIDATE를 실제 업무규칙과 대조한다."})
    for code in (verification or {}).get("open_blockers") or []:
        if code == "BUSINESS_RULE_REVIEW_OPEN":
            continue
        blockers.append({
            "code": code,
            "owner": "ENGINEERING_OR_TEST_OWNER",
            "action_ko": {
                "TEST_COMMAND_OPEN": "실행 가능한 Test Command를 제공한다.",
                "RUNTIME_ENVIRONMENT_UNAVAILABLE": "실제 Runtime/Test 환경을 연결한다.",
            }.get(code, "해당 Blocker에 필요한 Evidence/권한을 제공한다."),
        })

    overall = "READY_FOR_RELEASE" if not blockers and production_verified else "ACTION_REQUIRED"
    if any(s["state"] == "FAILED" for s in stages):
        overall = "FAILED"

    status = {
        "schema_version": 1,
        "artifact_type": "E2E_CHECK_STATUS",
        "subject": {
            "source_group_id": group_id,
            "source_requirement_count": group.get("source_count"),
            "source_requirement_ids": group.get("source_requirement_ids") or [],
        },
        "overall": {
            "state": overall,
            "release_ready": overall == "READY_FOR_RELEASE",
            "production_verified": production_verified,
            "summary_ko": "진행 가능하지만 Human/실제 Source/Runtime Blocker가 남아 있음" if overall == "ACTION_REQUIRED" else ("Release 준비 완료" if overall == "READY_FOR_RELEASE" else "실패 상태 확인 필요"),
        },
        "stage_status": stages,
        "blockers": blockers,
        "next_actions": [b["action_ko"] for b in blockers[:5]],
        "truth_guards": {
            "candidate_is_not_canonical": boundary_open,
            "fixture_is_not_production_source": fixture_only,
            "contract_coverage_is_not_runtime_pass": vstate == "CONTRACT_PASS_RUNTIME_NOT_EXECUTED",
            "source_behavior_is_not_business_truth": True,
        },
    }
    return status, []


def validate_status(status):
    errors = []
    if not isinstance(status, dict):
        return ["E2E-100: status is required"]
    overall = status.get("overall") or {}
    blockers = status.get("blockers") or []
    if overall.get("state") == "READY_FOR_RELEASE":
        if blockers:
            add(errors, "E2E-101", "READY_FOR_RELEASE cannot have blockers")
        if overall.get("production_verified") is not True:
            add(errors, "E2E-102", "READY_FOR_RELEASE requires production_verified=true")
    guards = status.get("truth_guards") or {}
    if guards.get("source_behavior_is_not_business_truth") is not True:
        add(errors, "E2E-103", "source_behavior_is_not_business_truth must remain true")
    if not status.get("stage_status"):
        add(errors, "E2E-104", "stage_status is required")
    return errors


def main():
    p = argparse.ArgumentParser()
    p.add_argument("normalization", type=Path)
    p.add_argument("review", type=Path)
    p.add_argument("reverse_sync", type=Path)
    p.add_argument("verification", type=Path)
    p.add_argument("-o", "--output", type=Path, required=True)
    a = p.parse_args()
    try:
        status, errors = build_status(load(a.normalization), load(a.review), load(a.reverse_sync), load(a.verification))
    except Exception as exc:
        print(f"E2E-LOAD: {exc}", file=sys.stderr)
        return 2
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    errors = validate_status(status)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    a.output.write_text(yaml.safe_dump(status, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"OK: E2E status built: {a.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
