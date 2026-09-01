# 02 DECOMPOSE — 요구분석

## 문서 목적
RQ 원문을 테스트 가능한 기능 행동으로 분해한다.

## 30초 요약
외부 요구사항 3건을 3개 FR Candidate로 1:1 보존하고, 요구 문구에서 직접 도출 가능한 최소 AC 후보만 만든다.

## Workflow
`RQ → Business Goal → FR → AC Candidate`

## 입력/Evidence
- `REQ_TM_FL001~003` — GIVEN
- Source는 이 단계에서 필수가 아님

## 본문
### Business Goal Candidate
최초 근무계획 수립 시 기본 근무스케줄을 활용해 근무계획을 만들고, 저장한 계획을 조회할 수 있게 한다.

### FR
| FR | External ID | 행동 | 상태 |
|---|---|---|---|
| FR-CAND-0001-01 | REQ_TM_FL001 | 탄력근로제 근무계획을 저장한다 | CANDIDATE |
| FR-CAND-0001-02 | REQ_TM_FL002 | 탄력근로제 근무계획을 조회한다 | CANDIDATE |
| FR-CAND-0001-03 | REQ_TM_FL003 | 기본 근무스케줄을 바탕으로 근무계획을 생성하고 자동 저장한다 | CANDIDATE |

### AC Candidate
- `AC-CAND-0001-01`: 입력된 탄력근로제 근무계획이 저장된다.
- `AC-CAND-0001-02`: 저장된 탄력근로제 근무계획을 조회할 수 있다.
- `AC-CAND-0001-03`: 기본 근무스케줄을 이용해 근무계획이 생성되고 저장된다.

## 미확정/Alert/Assumption
- 자동 생성 시점/Trigger는 원문에 없음 → `ALT-PILOT-001 OPEN`
- 기존 계획 존재 시 overwrite/skip 정책은 원문에 없음 → `ALT-PILOT-002 OPEN`

## 관련 ID/Traceability
`RQ-CAND-0001 → FR-CAND-0001-01~03 → AC-CAND-0001-01~03`

## 다음 작업
CLARIFY에서 결과를 바꿀 수 있는 업무 질문을 최소화해 제시한다.
