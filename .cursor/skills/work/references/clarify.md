# Clarify Reference

## Purpose
결과를 바꿀 수 있는 질문만 생성하고 답이 없어도 다음 단계 진행이 가능한 상태를 만든다.

## Required Input
- Stage: `CLARIFY`
- RQ/FR + OPEN/불확실 항목

## Optional Input
- 기존 Knowledge / Project Overlay / Domain Overlay / PM 정보

## Retrieval Strategy
1. Canonical direct relation
2. 기존 Program/Process/BR summary
3. Trace/Static Analysis candidate
4. Relevant symbol/source snippet
5. 필요한 경우에만 full file

## 실행 계약(Agent Execution Contract)
| 항목 | 실행 규칙 |
|---|---|
| 입력 필드 | RQ/FR, OPEN 항목, 현재 가정, 관련 Evidence를 입력으로 사용한다. |
| 근거 분류 | 사용자/정책 답변은 CONFIRMED 또는 GIVEN, Source 관찰은 OBSERVED, 질문 필요성 판단은 INFERRED로 둔다. |
| 실행 순서 | OPEN 목록화 → 결과를 바꾸는지 평가 → 중복 질문 제거 → 우선순위 지정 → 답변이 없을 때 사용할 ALT/ASM 정의 순서로 수행한다. |
| 계속/중단 조건 | 질문 답변이 없어도 일반 Workflow는 계속한다. 실행 안전성·법적/보안 위험 등 Hard Guard 조건만 해당 실행을 중단한다. |
| 출력 필드 매핑 | INT/질문, 우선순위, 영향 대상, 답변 상태, ALT/ASM, 관련 RQ/FR/BR을 기록한다. |
| 품질 게이트 | 모든 질문은 답변에 따라 설계/범위/검증 결과가 달라지는 이유를 설명할 수 있어야 한다. |
| 미확정/실패 처리 | 답변 없음은 OPEN, 상충 답변은 CONFLICT, Source와 정책이 다르면 Business Truth를 자동 선택하지 않고 CHECK_REQUIRED로 남긴다. |

## Steps
1. 입력과 Evidence provenance를 분리한다.
2. 중요 질문을 우선순위화한다.
3. 미확정은 ALT/ASM으로 남긴다.
4. Canonical relation과 Artifact를 동기화한다.

## Output
- INT/ALT/ASM
- Template: `sdlc/templates/core/interview-questions.md`

## Quality Check
- 질문이 실제 결과를 바꾸는가
- Human Truth와 OBSERVED/INFERRED가 구분되는가

## Alert Conditions
- Business Truth 미확정
- Evidence 충돌
- 정책 확인 필요

## Token Strategy
관련 RQ/FR/BR 후보만 사용한다.

## Do Not
- 답변이 없다는 이유로 Workflow 전체를 막지 않는다.
- Source 구현을 정책 답변으로 대신하지 않는다.
