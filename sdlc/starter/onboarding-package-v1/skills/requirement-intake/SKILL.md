# Skill — Generic Requirement Intake

## Purpose

Greenfield/Brownfield/Hybrid 프로젝트의 요구사항 원문을 원래 의미와 Provenance를 보존한 `REQUIREMENT_CANDIDATE`와 Stage Input Pack으로 구조화한다.

특정 고객 Excel Column, 업무 Domain, 기술 Stack, 기존 Pilot Grouping 규칙을 Core Intake 전제로 사용하지 않는다.

## Required Input

- Requirement Source 원문 또는 명시적 Requirement 요청
- Project ID
- Project Mode 또는 AUTO
- Source Locator/Source ID를 만들 수 있는 최소 정보

## Optional Input

- 원본 Requirement ID
- Business Document Manifest
- Glossary
- Project/Domain Hint
- 기존 Canonical RQ/FR Reference
- Project Overlay
- Legacy Requirement Normalizer Adapter 결과

## Precondition

- 원문 또는 사용자가 직접 제공한 Requirement Intent가 존재한다.
- 원본 ID가 있으면 그대로 보존한다.
- 원본 ID가 없으면 Canonical RQ ID를 임의 발행하지 않고 Intake Source ID를 별도로 유지한다.

## Retrieval Strategy

1. 사용자가 직접 제공한 Requirement 원문
2. 명시된 Source Locator/Document Section
3. 원본 Requirement ID/External Ticket ID
4. Glossary/Project Context의 직접 Reference
5. 기존 Canonical Direct Relation
6. 필요한 경우에만 Business Document Provider/Parser 결과

Requirement Intake 단계에서 Source Repository 전체를 탐색하지 않는다.

## Atomic Steps

1. 원문 Source/Locator/Revision을 기록한다.
2. 원본 Requirement ID가 있으면 보존한다.
3. 요구사항명 또는 한 줄 Intent를 원문의 범위를 넘지 않게 작성한다.
4. 현재 문제/요청내용을 원문에서 분리한다.
5. 원하는 결과/Business Outcome을 원문에서 확인한다.
6. Actor/Trigger/Scope/Constraint가 명시돼 있으면 Evidence와 함께 기록한다.
7. 명시되지 않은 Actor/Why/정책/예외는 OPEN으로 남긴다.
8. 기존 RQ와 직접 연결된 근거가 있으면 Related Candidate로 기록한다.
9. Legacy Requirement Inventory의 Grouping이 필요하면 Core에서 규칙을 새로 만들지 않고 Config/Adapter 결과를 입력으로 사용한다.
10. Candidate를 Canonical RQ로 자동 발행하지 않는다.
11. `REQUIREMENT_CANDIDATE`를 생성한다.
12. Stage Input Pack v2에 Source Requirement ID, Evidence, OPEN, Expected Output을 기록한다.
13. 다음 `DECOMPOSE` Stage Handoff를 준비한다.

## Decision Rules

- 사용자 직접 입력은 `GIVEN`이다.
- 문서에서 직접 읽은 내용은 Source Authority에 따라 `GIVEN` 또는 `OBSERVED` Evidence로 보존한다.
- 존재하지 않는 Why/Rule/Exception을 자연스럽게 보이게 만들기 위해 창작하지 않는다.
- 외부 Ticket/Excel Row의 경계가 Canonical Requirement 경계라는 보장은 없다.
- Grouping/Merge/Split은 Configured Normalizer 또는 Boundary Review를 통해서만 수행한다.
- Source 구현은 Intake 단계 Business Truth 근거로 사용하지 않는다.

## Output Schema

- `REQUIREMENT_CANDIDATE`
- 갱신된 `sdlc/templates/stage-input-pack.yaml` v2
- 필요한 OPEN/Question
- 기존 RQ/FR 관련 후보가 있는 경우 Reference Candidate

## Quality Check

- 원문 Locator/Source ID가 보존됐는가?
- 외부 Requirement ID가 있으면 그대로 보존됐는가?
- Requirement Candidate가 원문보다 의미를 확장하지 않았는가?
- 없는 Actor/Why/Rule을 창작하지 않았는가?
- Candidate가 Canonical로 자동 발행되지 않았는가?
- 다음 Agent가 원문과 OPEN을 대화 History 없이 확인할 수 있는가?

## Alert Conditions

- SOURCE_LOCATOR_OPEN
- SOURCE_REVISION_OPEN
- REQUIREMENT_INTENT_AMBIGUOUS
- AUTHORITY_UNKNOWN
- EXISTING_RQ_MATCH_AMBIGUOUS
- LEGACY_NORMALIZER_REQUIRED

## Stop Conditions

- Requirement Candidate와 Stage Input Pack이 값 또는 명시적 OPEN으로 생성됐다.
- 다음 판단이 Requirement Boundary/Merge/Split 결정이다.
- 다음 Evidence가 별도 Business Document Provider나 권한을 요구한다.

## Escalation Conditions

- Requirement Intent 자체가 모호함 → L2_OR_HUMAN
- 기존 RQ와 Merge/Split 판단 필요 → L2_OR_HUMAN
- 상충하는 공식 요구 Source → HUMAN
- Cross-domain Boundary → L3_OR_HUMAN

## Do Not

- Canonical RQ ID 임의 생성
- 고객/Pilot 전용 Column을 Core 필수 입력으로 요구
- 외부 Row/Ticket 하나를 자동 Canonical RQ로 확정
- 이름 유사성으로 기존 RQ 자동 Merge
- 없는 Why/Rule/Exception 창작
- Source 구현을 Business Requirement로 역확정

## Example

입력 Requirement가 "주문 취소 후 재고가 즉시 복원되어야 한다"이고 별도 Actor/예외 규칙이 없다면, 해당 문장을 `GIVEN` Evidence로 보존하고 원하는 결과를 "취소 완료 시 재고 복원" 후보로 구조화한다.

누가 취소할 수 있는지, 부분취소가 가능한지, 외부 결제 취소가 필요한지는 원문에 없으므로 OPEN으로 남긴다. 특정 기술 구현이나 기존 Source 구조는 INTAKE 단계에서 추측하지 않는다.
