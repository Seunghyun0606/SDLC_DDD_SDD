# Clarify Reference

## Purpose
결과를 바꿀 수 있는 OPEN을 구조화하고, 질문만 생성하는 것이 아니라 인터뷰·현행/Source/Data 분석·프로젝트 표준·설계/개발 제안 중 가장 적절한 해소 경로를 선택한다.

## Required Input
- Stage: `CLARIFY`
- RQ/FR + OPEN/불확실 항목

## Optional Input
- SOP/정책/매뉴얼
- 기존 Knowledge / Project Overlay / Domain Overlay / PM 정보
- 기존 시스템/Source/Data Evidence
- Project Standard / `open-resolution-profile.yaml`

## Retrieval Strategy
1. Canonical direct relation과 현재 OPEN
2. 기존 답변/Decision Log/Open Resolution Workbook
3. 기존 Program/Process/BR summary
4. 프로젝트 표준
5. Trace/Static Analysis candidate
6. Relevant symbol/source/data snippet
7. 필요한 경우에만 full file 또는 인터뷰 질문 생성

## 실행 계약(Agent Execution Contract)
| 항목 | 실행 규칙 |
|---|---|
| 입력 필드 | RQ/FR, OPEN 항목, 현재 가정, 관련 Evidence, Project Authority Profile을 사용한다. |
| 근거 분류 | 사용자/정책 답변은 CONFIRMED/GIVEN, Source/현행 분석은 OBSERVED, Project Standard는 PROJECT_STANDARD, 설계자/개발자 제안은 DESIGN_PROPOSAL/TECHNICAL_PROPOSAL로 둔다. |
| 실행 순서 | OPEN 목록화 → Category/Decision Domain 분류 → 결과 영향 평가 → 해소 경로 선택 → 인터뷰 질문/분석 Task/제안안 작성 → 근거와 대안 기록 → 결정권자 판정 → 산출물 반영 순서로 수행한다. |
| 계속/중단 조건 | SOP나 답변이 없어도 현행분석/제안으로 가능한 설계는 계속한다. 업무 Truth가 필요한 항목은 PROPOSED까지만 진행한다. Hard Guard만 해당 실행을 중단한다. |
| 출력 필드 매핑 | OPEN ID, Category, Decision Domain, 질문/분석 Task/제안안, Resolution Method, Basis, 결정권자, 상태, downstream impact를 `open-resolution-workbook.md`에 기록한다. 고객 질문 View가 필요하면 `interview-questions.md`를 파생한다. |
| 품질 게이트 | 모든 OPEN은 최소 하나의 해소 경로를 가져야 하며, 제안값은 이유/대안/결정권자가 있어야 한다. 현행 관찰과 TO-BE 업무정책을 혼동하지 않는다. |
| 미확정/실패 처리 | 답변 없음은 OPEN/PROPOSED, 현행 확인은 OBSERVED_AS_IS, 상충은 CONFLICT, 기술 권한자가 채택한 안은 ACCEPTED_DESIGN, 업무 권한자가 확인한 정책만 CONFIRMED_BUSINESS로 둔다. |

## Steps
1. OPEN을 `open-resolution-contract.json`의 Category/Decision Domain으로 분류한다.
2. 고객에게 물어야 하는 것, 시스템에서 확인할 것, 설계자/개발자가 제안할 것을 분리한다.
3. 인터뷰 질문에는 현재 정보·추천 선택지·답변 영향·결정권자를 함께 제시한다.
4. Brownfield에서 현행/Source/Data로 확인 가능한 항목은 고객 질문으로 전가하지 않는다.
5. Greenfield에서 자료가 없는 UI/기술 항목은 Project Standard와 전문경험을 근거로 후보안을 제시한다.
6. 결정 상태를 갱신하고 Functional Design/Program Spec의 OPEN을 동기화한다.

## Output
- OPEN Resolution Workbook
- 필요 시 고객용 Interview/Clarification View
- Template: `sdlc/templates/core/open-resolution-workbook.md`
- Customer/Interview View: `sdlc/templates/core/interview-questions.md`

## Quality Check
- SOP가 없다는 이유만으로 모든 OPEN이 미해결로 남아 있지 않은가
- 실제로 분석 가능한 것을 고객에게 불필요하게 묻지 않았는가
- 질문에 답변 선택지/설계 영향이 포함되어 있는가
- 경험 기반 제안과 Business Truth가 구분되는가
- 기술 결정이 불필요하게 고객 승인 대기로 남지 않는가

## Alert Conditions
- Business Truth 미확정
- Evidence 충돌
- 정책 확인 필요
- 결정권자 불명확
- 제안안이 프로젝트 표준과 충돌

## Token Strategy
관련 RQ/FR/BR/SCN/PGM, 현재 OPEN, 직접 Evidence와 Project Standard만 우선 사용한다.

## Do Not
- 답변이 없다는 이유로 Workflow 전체를 막지 않는다.
- 모든 OPEN을 인터뷰 질문으로만 바꾸지 않는다.
- Source 구현을 정책 답변으로 대신하지 않는다.
- 설계자/개발자 경험을 CONFIRMED Business Rule로 기록하지 않는다.
