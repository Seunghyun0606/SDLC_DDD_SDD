# 10 TEST — 테스트시나리오

> Test Source/Evidence는 `SIMULATED_SOURCE_FIXTURE`다.

## 문서 목적
AC와 Test Case를 연결하고 실제 실행 여부를 분리한다.

## 30초 요약
3개 AC에 5개 TC Candidate를 만들었다. Application Test는 실행하지 않는다.

## Workflow
`AC → TC → executable evidence → result`

## 입력/Evidence
- TO-BE Service Hash: sha256:6e370964640c92b0001da72f40e15b92b9a07d423619086d77be9e53dfd570a0
- Test intent Hash: sha256:43fa42c7aa6ad83976ce1a123261ce33e869623e338cf5204bcf07beef603766
- Evidence Type: SIMULATED_SOURCE_FIXTURE

## 본문
| TC | AC | Scenario | Execution |
|---|---|---|---|
| TC-PILOT-001 | AC-01 | 수동 저장 | FIXTURE_STRUCTURE_ONLY |
| TC-PILOT-002 | AC-02 | 저장 계획 조회 | FIXTURE_STRUCTURE_ONLY |
| TC-PILOT-003 | AC-03 | 기존 계획 없음 + default 있음 | FIXTURE_STRUCTURE_ONLY |
| TC-PILOT-004 | AC-03 | 기존 계획 있음 | ASSUMPTION_TEST_ONLY |
| TC-PILOT-005 | AC-03 | default 없음 | NOT_EXECUTABLE_POLICY_REQUIRED |

## 미확정/Alert/Assumption
TC-004/005는 Business Policy 확정 전 Release Acceptance로 사용할 수 없다.

## 관련 ID/Traceability
`AC-01→TC-001, AC-02→TC-002, AC-03→TC-003~005`

## 다음 작업
VERIFY에서 검증 범위를 판정한다.
