# Requirement Reference

## Purpose
Requirement 원문과 External ID를 보존하고 FR을 테스트 가능한 행동으로 분해하되, INTAKE와 DECOMPOSE 산출물을 별도 문서로 중복 생성하지 않는다.

## Required Input
- Stage: `DECOMPOSE`
- Requirement 원문 또는 RQ + Source Record/External ID

## Optional Input
- 기존 Knowledge / Project Overlay / Domain Overlay / PM 정보
- 기존 시스템/Source Evidence

## Retrieval Strategy
1. Requirement 원문/External ID/Source Record
2. Canonical direct relation
3. 기존 Program/Process/BR summary
4. Trace/Static Analysis candidate
5. Relevant symbol/source snippet
6. 필요한 경우에만 full file

## 실행 계약(Agent Execution Contract)
| 항목 | 실행 규칙 |
|---|---|
| 입력 필드 | Requirement 원문, External ID, Source Record 위치를 먼저 확보한다. 없으면 없는 필드를 명시한다. |
| 근거 분류 | 고객/사용자 원문은 GIVEN, Source에서 확인한 사실은 OBSERVED, 분해·그룹화 판단은 INFERRED, 근거 없는 보완은 ASSUMED로 구분한다. |
| 실행 순서 | 원문/External ID 보존 → 요청/업무 목표 정리 → 테스트 가능한 FR 분해 → BR 후보 분리 → AC 생성 → 미확정 이월 순서로 수행한다. |
| 계속/중단 조건 | Optional 정보 부족은 계속한다. Required 원문 자체가 없으면 내용을 발명하지 말고 CHECK_REQUIRED를 남긴 뒤 가능한 기존 Canonical만 정리한다. |
| 출력 필드 매핑 | 원문/External ID/정규화 문장/목표/범위/FR/BR 후보/AC/OPEN을 하나의 `requirement.md` Artifact와 Canonical relation에 반영한다. 별도 requirement-analysis 문서를 새로 만들지 않는다. |
| 품질 게이트 | External ID와 원문이 보존되고, 각 FR이 단일 테스트 가능 행동이며, Source 관찰과 Business Truth가 구분되어야 한다. 원문과 분석결과가 서로 다른 문서에서 중복 관리되지 않아야 한다. |
| 미확정/실패 처리 | 중복 ID는 ALERT, near-duplicate는 GROUPING_REVIEW, Business Rule 미확정은 OPEN/CHECK_REQUIRED로 유지한다. |

## Steps
1. 원문/외부 ID/출처를 변경하지 않고 보존한다.
2. 현재 문제, 업무 목표, 기대 결과, Scope/Constraint를 정리한다.
3. 요구를 하나 이상의 테스트 가능한 FR로 분해한다.
4. 명시적 또는 후보 Business Rule을 FR 설명과 분리한다.
5. 각 FR에 연결 가능한 AC를 만든다.
6. 부족한 6W/정책/권한/상세설계 정보는 이 단계에서 발명하지 않고 CLARIFY/PROCESS OPEN으로 넘긴다.
7. 같은 내용을 별도 Requirement Analysis Artifact에 복사하지 않는다.

## Output
- Canonical RQ/FR/BR Candidate/AC
- Single Artifact Template: `sdlc/templates/core/requirement.md`
- `sdlc/templates/core/requirement-analysis.md`는 기존 링크 호환용 Legacy View이며 신규 Workflow에서는 생성하지 않는다.

## Quality Check
- 요구 원문과 External ID가 보존되었는가
- FR이 테스트 가능한 단일 행동인가
- BR 후보가 단순 기능 설명과 구분되는가
- AC가 FR 결과를 검증할 수 있는가
- Source 관찰과 Business Truth가 섞이지 않았는가
- 동일 요구정보가 두 개의 활성 문서에 중복 작성되지 않았는가

## Alert Conditions
- Evidence 없음 또는 충돌
- Target ambiguity
- Business Truth 미확정
- Scope expansion
- 원문/External ID 손실

## Token Strategy
Requirement 원문과 직접 연결된 기존 정보만 우선하고 관련 Symbol만 확장한다.

## Do Not
- Source 구현을 Business Rule로 자동 확정하지 않는다.
- 존재하지 않는 Program/Table/API를 사실처럼 만들지 않는다.
- 정보 부족만으로 전체 Workflow를 중단하지 않는다.
- Requirement와 Requirement Analysis를 별도 활성 Artifact로 중복 생성하지 않는다.
