# Skill — Canonical Publish

## Purpose
Human/L2가 `CONFIRMED`한 Requirement Boundary Decision을 검증하고, 사전 할당된 Canonical RQ/FR ID를 사용해 Publish Request를 만든다.

## Required Input
- `requirement_review_decision`
- Source revision
- Preallocated Canonical RQ/FR IDs

## Precondition
- `boundary_status = CONFIRMED`
- `decision != UNRESOLVED`
- decided_by / decided_at / decision_basis / evidence_ids 존재
- decision_revision >= 1
- Source Group membership이 Review 당시와 동일
- Canonical ID가 사전 할당되어 있음

## Atomic Steps
1. Review Snapshot의 Source Group/Source IDs/Revision을 확인한다.
2. Decision과 Boundary Status를 확인한다.
3. 결정자/시각/근거/Evidence/Revision을 확인한다.
4. 사전 할당된 Canonical ID를 입력받는다.
5. Candidate Group ID가 Canonical ID로 재사용되지 않았는지 확인한다.
6. Decision별 Cardinality를 검증한다.
7. `canonical_publish_request`를 생성한다.
8. `validate_p02_contracts.py publish-request`를 통과시킨다.
9. 실제 Canonical Registry Write Adapter가 없으면 `PUBLISH_READY`에서 종료한다.

## Decision Cardinality
- KEEP_AS_RQ → RQ 정확히 1개
- MAP_TO_EXISTING_RQ_AS_FR → RQ 1개 + FR 1개 이상
- MERGE_INTO_NEW_RQ → RQ 정확히 1개
- SPLIT_TO_MULTIPLE_RQ → RQ 2개 이상
- REJECT_AS_REQUIREMENT → RQ/FR 0개

## Output Schema
- `sdlc/templates/canonical-publish-request.yaml`

## Quality Check
- Candidate ID와 Canonical ID가 다른가?
- Source Group과 Source ID가 모두 Trace에 남았는가?
- Review Revision이 Publish Trace와 동일한가?
- Evidence가 Publish Trace에 그대로 보존됐는가?
- 같은 Review Revision이 다른 ID 집합으로 재발행되지 않는가?

## Stop Conditions
- Publish Request가 Validator를 통과함
- 또는 Precondition/Revision/ID Conflict로 BLOCK됨

## Escalation Conditions
- ID allocation conflict → Harness Admin
- Review revision conflict → Reviewer
- Source membership/revision drift → L2/Human re-review
- Decision evidence conflict → Human

## Do Not
- Canonical ID 자동 추측/생성
- Candidate Group ID를 Canonical ID로 재사용
- OPEN/PROVISIONAL Review Publish
- Evidence 없는 CONFIRMED Publish
- 같은 Review Revision으로 다른 Canonical 결과 발행

## P0.2 Scope
P0.2는 `PUBLISH_READY` 요청 생성과 검증까지 다룬다. 물리 Canonical Registry write는 실제 Registry 위치와 ID allocator 계약이 확정된 뒤 다음 단계에서 연결한다.
