# Skill — Config-driven Stage Procedure

## Purpose

`stage-routing.yaml`이 선택한 현재 Stage와 `stage-procedures.yaml`의 Procedure Profile을 이용해, 도구 실행 특성이 특별하지 않은 분석/설계 Stage를 동일한 Low-Agent 실행 계약으로 수행한다.

이 Skill은 Stage별 SKILL 파일을 반복 생성하지 않기 위한 공통 실행기다.

## Required Input

- 현재 Stage Input Pack v2
- `sdlc/config/stage-routing.yaml`
- `sdlc/config/stage-procedures.yaml`
- Stage Route의 `stage`, `required_input_types`, `expected_outputs`, `next_stage`

## Optional Input

- 현재 Requirement/Analysis/Design Artifact
- Project/Profile/Overlay
- Reference Graph
- 관련 Evidence Source

## Precondition

- 현재 Stage가 Stage Routing에 존재한다.
- 현재 Stage에 대응하는 Procedure Profile이 존재한다.
- Required Input은 값 또는 명시적 `OPEN` 상태로 존재한다.
- Stage Input Pack의 Safety Constraint가 유지된다.

## Retrieval Strategy

1. Stage Input Pack의 `target.related_ids`
2. `required_inputs`의 직접 Reference
3. `evidence`의 직접 Locator/Revision
4. 현재 Stage에 필요한 Canonical/Current Artifact
5. Reference Graph의 직접 관계
6. OPEN Item이 요구하는 제한된 추가 Evidence

전체 Repository/전체 문서를 무제한 탐색하지 않는다.

## Atomic Steps

1. 현재 Stage를 `stage-routing.yaml`에서 확인한다.
2. 동일 Stage의 Procedure Profile을 `stage-procedures.yaml`에서 읽는다.
3. Required Input Type이 값 또는 명시적 OPEN으로 존재하는지 확인한다.
4. 기존 `resolved_facts`, `evidence`, `open_items`를 삭제하지 않고 이어받는다.
5. Procedure Profile의 `atomic_steps`를 순서대로 수행한다.
6. 각 새 Fact에 Truth State와 Evidence Reference를 기록한다.
7. 모르는 값은 OPEN Item으로 기록하고 추측하지 않는다.
8. Profile의 `decision_rules`를 적용한다.
9. Stage Routing의 `expected_outputs` 각각을 `COMPLETE / PARTIAL / OPEN` 중 하나로 명시한다.
10. Profile의 `quality_checks`를 수행한다.
11. Alert 조건을 Stage Input Pack에 보존한다.
12. Stop/Escalation 조건을 평가한다.
13. Handoff에 현재 Skill, Agent Level, Next Stage를 기록한다.
14. 다음 Agent가 Conversation History 없이 작업할 수 있는지 확인한다.

## Decision Rules

- Profile에 없는 Business Decision을 임의로 만들지 않는다.
- `OBSERVED` 또는 `INFERRED`를 자동 `CONFIRMED`로 승격하지 않는다.
- Candidate를 자동 Canonical로 승격하지 않는다.
- OPEN은 비위험 Workflow를 기본적으로 막지 않는다.
- Side-effect Action은 이 공통 Skill이 임의 실행하지 않는다.
- Stage Routing과 Procedure Profile이 충돌하면 `CONFIG_CONTRACT_CONFLICT`로 Escalate한다.

## Output Schema

- 갱신된 `sdlc/templates/stage-input-pack.yaml` v2
- Stage Routing의 `expected_outputs`에 선언된 Artifact
- 필요한 OPEN/Alert/Escalation
- Reference Graph 갱신 후보

## Quality Check

- 모든 Required Input이 값 또는 OPEN인가?
- 새로운 Fact가 Truth State를 가지는가?
- CONFIRMED Fact에 Evidence가 있는가?
- OPEN이 조용히 삭제되지 않았는가?
- Expected Output이 COMPLETE/PARTIAL/OPEN으로 명시됐는가?
- Output의 관련 ID가 Stage Pack `related_ids`에 보존됐는가?
- 다음 Stage가 Stage Routing과 일치하는가?
- Side-effect를 임의 실행하지 않았는가?

## Alert Conditions

- CONFIG_CONTRACT_CONFLICT
- MISSING_REQUIRED_INPUT
- EVIDENCE_CONFLICT
- AUTHORITY_UNKNOWN
- OUTPUT_TRACE_MISSING
- NEXT_STAGE_MISMATCH

Procedure Profile에 정의된 Alert도 함께 적용한다.

## Stop Conditions

- Required Output이 값 또는 명시적 OPEN/PARTIAL로 채워졌다.
- Procedure Profile의 Stop Condition이 충족됐다.
- 다음 Evidence가 새로운 권한/Provider/Runtime을 요구한다.
- 다음 판단이 L2/L3/Human Business/Architecture Decision을 요구한다.

## Escalation Conditions

- `CONFIG_CONTRACT_CONFLICT` → HARNESS_OWNER
- `EVIDENCE_CONFLICT` → L2_OR_HUMAN
- Business Truth 확정 필요 → HUMAN
- Architecture Decision 필요 → L3_OR_HUMAN
- Procedure Profile의 Escalation 규칙을 추가 적용

## Do Not

- Procedure Profile에 없는 규칙 창작
- OPEN을 완료값으로 치환
- Source Behavior를 Business Truth로 확정
- Candidate를 Canonical로 자동 발행
- 전체 Repository 무제한 탐색
- Stage를 임의 Skip
- Side-effect Provider 호출

## Example

예: 현재 Stage가 `IMPACT`이면 `stage-procedures.yaml`의 `IMPACT` Profile을 읽는다.

Direct PGM/ART Evidence가 확인되면 Technical Impact Candidate를 만들 수 있다. Downstream Interface Evidence가 없으면 영향이 없다고 결론내리지 않고 `DOWNSTREAM_UNKNOWN / OPEN`으로 보존한다. 모든 결과는 `IMPACT_ANALYSIS`와 갱신된 Stage Input Pack에 기록하고 Stage Routing이 정의한 `DESIGN`으로 Handoff한다.
