# Clarify Reference

## Purpose
결과를 바꿀 수 있는 미확정 사항을 구조화하고, 질문만 생성하는 것이 아니라 인터뷰·현행/Source/Data 분석·프로젝트 표준·설계/개발 제안 중 실제 해소 경로를 선택한다.

## Required Input
- Stage: `CLARIFY`
- RQ/FR + 현재 미확정/불확실 항목

## Optional Input
- SOP/정책/매뉴얼
- 기존 Knowledge / Project Overlay / Domain Overlay / PM 정보
- 기존 시스템/Source/Data Evidence
- Project Standard / `open-resolution-profile.yaml`

## Retrieval Strategy
1. Canonical direct relation과 현재 미확정 항목
2. 기존 답변/Decision Log/Open Resolution Workbook
3. 기존 Program/Process/BR summary
4. 프로젝트 표준
5. Trace/Static Analysis candidate
6. Relevant symbol/source/data snippet
7. 필요한 경우에만 full file 또는 인터뷰 질문 생성

## 실행 계약(Agent Execution Contract)
| 항목 | 실행 규칙 |
|---|---|
| 입력 필드 | RQ/FR, 확인/결정할 내용, 현재 값, 관련 Evidence, 필요한 경우 Project Authority Profile을 사용한다. |
| 근거 분류 | 사용자/정책 답변은 CONFIRMED/GIVEN, Source/현행 분석은 OBSERVED, Project Standard는 PROJECT_STANDARD, 설계/개발 제안은 PROPOSAL 계열로 내부 기록한다. |
| 실행 순서 | 미확정 목록화 → 결과 영향 확인 → 확인 방법 선택 → 인터뷰 질문/분석 Task/제안 작성 → 근거와 대안 기록 → 확인·결정 담당 지정 → 산출물 반영 순서로 수행한다. 내부 Category/Decision Domain/Resolution Method/Basis는 필요한 경우 Agent가 계산한다. |
| 계속/중단 조건 | SOP나 답변이 없어도 현행분석/제안으로 가능한 설계는 계속한다. 업무 Truth가 필요한 항목은 제안까지만 진행한다. Hard Guard만 해당 실행을 중단한다. |
| 출력 필드 매핑 | 사람 View에는 OPEN ID, 관련 항목, 확인/결정할 내용, 확인 방법, 현재 확인값/제안, 확인·결정 담당, 진행상태를 `open-resolution-workbook.md`에 기록한다. 고객 질문 View가 필요하면 `interview-questions.md`를 파생한다. |
| 품질 게이트 | 모든 미확정 항목은 최소 하나의 실제 해소 경로와 담당 역할이 있어야 한다. 현행 관찰과 TO-BE 업무정책, 제안과 확정을 혼동하지 않는다. |
| 미확정/실패 처리 | 사람 상태는 `미확정 / 확인중 / 제안 / 확정 / 보류`만 사용한다. 내부 Machine 상태는 Contract mapping에 따라 유지한다. |

## Steps
1. 현재 결과를 바꾸는 미확정 항목만 남긴다. 문서 정밀도에만 영향을 주는 항목은 P2 또는 후속으로 내린다.
2. 고객에게 확인해야 하는 것, 시스템에서 확인할 것, 설계/개발자가 제안할 것을 분리한다.
3. 현행/Source/Data로 확인 가능한 항목은 고객 질문으로 전가하지 않는다.
4. Greenfield에서 자료가 없는 UI/기술 항목은 Project Standard와 전문경험을 근거로 후보안을 제시할 수 있다.
5. 확인/결정 담당과 진행상태를 갱신하고 Functional Design/Program Spec의 관련 OPEN을 동기화한다.
6. 세부 `Category / Decision Domain / Resolution Method / Basis Class / Internal Status / downstream impact`는 기본 사용자 입력이 아니라 Machine metadata로 관리한다.

## Output
- 미확정 사항 해소표(Open Resolution Workbook)
- 필요 시 고객용 Interview/Clarification View
- Template: `sdlc/templates/core/open-resolution-workbook.md`
- Customer/Interview View: `sdlc/templates/core/interview-questions.md`

## Quality Check
- 실제 결과에 영향이 없는 사소한 OPEN까지 과도하게 만들지 않았는가
- SOP가 없다는 이유로 모든 OPEN이 미해결로 남아 있지 않은가
- 분석 가능한 것을 고객에게 불필요하게 묻지 않았는가
- 경험 기반 제안과 Business Truth가 구분되는가
- 기술 결정이 불필요하게 고객 승인 대기로 남지 않는가
- 사용자가 내부 Machine taxonomy를 이해해야만 작성할 수 있게 만들지 않았는가

## Alert Conditions
- Business Truth 미확정
- Evidence 충돌
- 정책 확인 필요
- 결정권자 불명확
- 제안안이 프로젝트 표준과 충돌

## Token Strategy
관련 RQ/FR/BR/SCN/PGM, 현재 미확정, 직접 Evidence와 Project Standard만 우선 사용한다.

## Do Not
- 답변이 없다는 이유로 Workflow 전체를 막지 않는다.
- 모든 OPEN을 인터뷰 질문으로만 바꾸지 않는다.
- Source 구현을 정책 답변으로 대신하지 않는다.
- 설계/개발 경험을 CONFIRMED Business Rule로 기록하지 않는다.
- 일반 사용자에게 Decision Domain/Resolution Method/Basis Class를 필수 입력으로 요구하지 않는다.
