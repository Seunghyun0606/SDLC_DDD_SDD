# Requirement Reference

## Purpose
Requirement 원문과 External ID를 보존하고 FR을 테스트 가능한 행동으로 분해한다.

## Required Input
- Stage: `DECOMPOSE`
- RQ + Source Record/External ID

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
| 입력 필드 | RQ 또는 Requirement 원문, External ID, Source Record 위치를 먼저 확보한다. 없으면 없는 필드를 명시한다. |
| 근거 분류 | 고객/사용자 원문은 GIVEN, Source에서 확인한 사실은 OBSERVED, 분해·그룹화 판단은 INFERRED, 근거 없는 보완은 ASSUMED로 구분한다. |
| 실행 순서 | 원문/External ID 보존 → 정규화 문장 생성 → 테스트 가능한 FR 분해 → AC 후보 생성 → 관련 Candidate 연결 순서로 수행한다. |
| 계속/중단 조건 | Optional 정보 부족은 계속한다. Required 원문 자체가 없으면 내용을 발명하지 말고 CHECK_REQUIRED를 남긴 뒤 가능한 기존 Canonical만 정리한다. |
| 출력 필드 매핑 | RQ/FR/AC Candidate, External ID, original_text, normalized_text, provenance, OPEN/Alert를 Artifact와 Canonical relation에 함께 반영한다. |
| 품질 게이트 | External ID와 원문이 보존되고, 각 FR이 단일 테스트 가능 행동이며, Source 관찰과 Business Truth가 구분되어야 한다. |
| 미확정/실패 처리 | 중복 ID는 ALERT, near-duplicate는 GROUPING_REVIEW, Business Rule 미확정은 OPEN/CHECK_REQUIRED로 유지한다. |

## Steps
1. 입력과 Evidence provenance를 분리한다.
2. 현재 Stage에 필요한 최소 결과를 만든다.
3. 미확정은 ALT/ASM 또는 CHECK_REQUIRED로 남긴다.
4. Canonical relation과 Artifact를 동기화한다.

## Output
- Canonical RQ/FR/AC candidate
- Template: `sdlc/templates/core/requirement-analysis.md`

## Quality Check
- RQ/FR/PGM/TASK/AC/TC 연결이 가능한가
- Source 기반 사실은 locator/confidence가 있는가
- Human Truth와 OBSERVED/INFERRED가 섞이지 않았는가

## Alert Conditions
- Evidence 없음 또는 충돌
- Target ambiguity
- Business Truth 미확정
- Scope expansion

## Token Strategy
Summary/Index/Trace를 우선하고 관련 Symbol만 확장한다.

## Do Not
- Source 구현을 Business Rule로 자동 확정하지 않는다.
- 존재하지 않는 Program/Table/API를 사실처럼 만들지 않는다.
- 정보 부족만으로 전체 Workflow를 중단하지 않는다.
