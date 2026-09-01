# Skill — End-to-End Status / Check

## Purpose
동일 Work Unit의 Normalization, Boundary Review, Canonical Publish, Source/Reverse Sync, Test/Verify 상태를 읽어 사용자가 바로 이해할 수 있는 하나의 `/check` 상태로 조합한다. 새로운 Business Truth나 Canonical Entity를 만들지 않는다.

## Required Input
- Legacy Requirement Normalization
- Requirement Review Decision
- Reverse Sync Candidate
- Verification Result

## Optional Input
- Current Stage Input Pack
- 담당자/일정/Release metadata
- 실제 Source Provider 상태

## Precondition
- 모든 입력이 동일 `source_group_id`를 가리켜야 한다.
- Normalization과 Review의 Source Requirement ID 집합이 같아야 한다.
- 입력 Artifact가 없으면 추측하지 않고 OPEN/BLOCKED로 남긴다.

## Retrieval Strategy
1. Stable Candidate Group ID
2. Source Requirement ID 집합
3. Boundary/Publish 상태
4. Source/Reverse Sync 상태
5. Test/Verification 상태
6. Open Blocker와 Owner

## Atomic Steps
1. Work Unit ID를 확인한다.
2. 단계 간 ID/Source Coverage를 교차검증한다.
3. 각 Stage의 상태를 원본 Artifact에서 읽는다.
4. Candidate/Canonical, Fixture/Production, Coverage/Runtime를 분리한다.
5. Blocker를 중복 제거하고 책임 주체를 붙인다.
6. 다음 실행 가능한 Action을 우선순위대로 최대 5개 선택한다.
7. `E2E_CHECK_STATUS`를 생성한다.
8. Release Ready 주장 전에 Production Verification과 Blocker 0건을 확인한다.

## Decision Rules
- Orchestrator는 Read Model이다. 원본 상태를 수정하지 않는다.
- Boundary OPEN이면 Candidate를 Canonical로 표시하지 않는다.
- Fixture Evidence는 Production Source로 표시하지 않는다.
- AC/TC Coverage는 Runtime PASS로 표시하지 않는다.
- `READY_FOR_RELEASE`는 blocker 0 + `production_verified=true`일 때만 가능하다.
- Source Behavior는 항상 Business Truth와 분리한다.

## Output Schema
`sdlc/templates/e2e-check-status.yaml`

## Quality Check
- 모든 Stage가 같은 Group을 가리키는가?
- Source ID Coverage가 동일한가?
- Blocker와 다음 Action이 모순되지 않는가?
- Release Ready와 Production Verified가 일치하는가?
- 사용자 화면에서 내부 P0.x 구현명 없이 현재 상태를 이해할 수 있는가?

## Alert Conditions
- E2E_GROUP_MISMATCH
- E2E_SOURCE_COVERAGE_MISMATCH
- RELEASE_READY_WITH_BLOCKER
- RELEASE_READY_WITHOUT_PRODUCTION_VERIFY
- CANDIDATE_CANONICAL_CONFUSION
- FIXTURE_PRODUCTION_CONFUSION
- CONTRACT_RUNTIME_CONFUSION

## Stop Conditions
- 현재 입력으로 상태/Blocker/다음 Action을 모두 표시함
- 다음 진행이 Human 결정, 실제 Source, Runtime 또는 권한을 요구함
- 추가 조회가 기존 상태를 바꾸지 않음

## Escalation Conditions
- Boundary/Business Rule → L2_OR_HUMAN
- 실제 Source/Runtime 연결 → ENGINEERING_OWNER
- Runtime 복합 실패 → L3
- Release 승인 → Human/Release Owner

## Do Not
- Candidate를 Canonical로 바꾸기
- Blocker를 숨기기
- Synthetic Fixture를 Production으로 표시하기
- NOT_EXECUTED Test를 PASS로 표시하기
- 상태 Dashboard를 이유로 기존 Stage Artifact를 복제하기

## Example
현재 근태마감 Pilot은 `정규화 완료 / 경계검토 필요 / Canonical 발행 차단 / Synthetic Source 검토 필요 / Runtime 테스트 차단`으로 표시한다. 다음 Action은 Human 경계검토, 실제 고객 Source 연결, Business Rule 검토, Test Command와 Runtime 연결이다.
