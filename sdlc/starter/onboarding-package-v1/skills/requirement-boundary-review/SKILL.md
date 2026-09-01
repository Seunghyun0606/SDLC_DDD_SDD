# Skill — Requirement Boundary Review

## Purpose
Candidate Group을 Canonical RQ/FR로 자동 승격하지 않고, Human/L2가 Business Outcome 경계를 확인할 수 있도록 Evidence와 선택지를 정리한다.

## Required Input
- Requirement Review Queue Item
- Source Group membership
- Source revision

## Optional Input
- 업무 담당자 확인
- Release/Owner/Acceptance Criteria 정보
- Process/Policy 문서

## Precondition
- `source_group_id`가 존재한다.
- `source_requirement_ids`와 `source_count`가 일치한다.
- Candidate는 아직 Canonical ID로 발행되지 않았다.

## Atomic Steps
1. Source Group의 원본 ID 범위를 확인한다.
2. 후보명이 독립 Business Outcome을 의미하는지 Evidence를 찾는다.
3. Owner/Release/Acceptance Criteria 경계를 확인한다.
4. 다음 Decision 중 하나를 선택한다.
   - KEEP_AS_RQ
   - MAP_TO_EXISTING_RQ_AS_FR
   - MERGE_INTO_NEW_RQ
   - SPLIT_TO_MULTIPLE_RQ
   - REJECT_AS_REQUIREMENT
   - UNRESOLVED
5. 근거가 부족하면 `UNRESOLVED / OPEN`으로 유지한다.
6. CONFIRMED이면 decided_by/decided_at/evidence/decision_revision을 기록한다.
7. Publish 가능 여부를 Validator로 확인한다.

## Decision Rules
- 이름이 같다는 이유만으로 같은 RQ라고 확정하지 않는다.
- CRUD/조회/송신 이름만으로 Split하지 않는다.
- Split/Merge가 Owner/Release/AC 경계를 바꾸면 L2 이상 또는 Human 결정이 필요하다.
- Source 구현은 Business Boundary의 단독 확정 근거가 아니다.

## Output Schema
- `sdlc/templates/requirement-review-decision.yaml`

## Quality Check
- Source ID 집합이 Review 전후 동일한가?
- Decision Basis와 Evidence가 존재하는가?
- CONFIRMED가 아닌데 publish_allowed=true가 되지 않았는가?
- Candidate ID가 Canonical ID처럼 표시되지 않았는가?

## Stop Conditions
- CONFIRMED 결정과 Evidence가 모두 기록됨
- 또는 필요한 Business Evidence가 없어 OPEN으로 종료함

## Escalation Conditions
- Split/Merge → L2_OR_HUMAN
- Cross-domain boundary → L3_OR_HUMAN
- Business owner disagreement → HUMAN

## Do Not
- Candidate를 자동 Canonical RQ로 승격
- Source Count가 크다는 이유만으로 Split
- Source Count가 작다는 이유만으로 KEEP_AS_RQ
- OPEN 상태에서 Canonical ID 발행

## Example
`RQG-CAND-6BB6D66548` 근태마감 39건은 Excel만으로 하나의 RQ인지 여러 RQ인지 확정하지 않는다. 필요한 Owner/Release/AC 경계를 요청하고 `UNRESOLVED / OPEN`을 유지한다.
