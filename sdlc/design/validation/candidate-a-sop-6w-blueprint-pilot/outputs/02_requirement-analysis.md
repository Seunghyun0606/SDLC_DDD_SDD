# RQ-FLEX-PLAN-001 — 탄력근로제 일일 근무계획 관리

> Status: `RQ CANDIDATE / NOT PUBLISHED`
> Business Definition: `outputs/01_business-definition-6w.md`

## Purpose

탄력근로제 근무자가 일자별 예정 근무시간을 10분 단위로 등록·조회·수정하고, 해당 계획을 근태집계/마감의 기준으로 사용할 수 있게 한다.

## FR

| FR | 기능 | Source |
|---|---|---|
| FR-FLEX-01 | 월 Calendar 및 일자별 계획 조회 | REQ_TM_TE003~005 + PPT |
| FR-FLEX-02 | 일별 근무계획 신규 저장 | REQ_TM_FL001 / TE001 |
| FR-FLEX-03 | 기존 근무계획 수정 | REQ_TM_TE002 |
| FR-FLEX-04 | 예상근무시간 계산/표시 | REQ_TM_TE005 + PPT |
| FR-FLEX-05 | 개인 입력 기본값 조회/등록/수정 | REQ_TM_TE006~008 |
| FR-FLEX-06 | 기본 근무스케줄 기반 초기 계획 제안/자동생성 Candidate | REQ_TM_FL003 |
| FR-FLEX-07 | 미입력자 알람메일 연계 Candidate | REQ_TM_TE009 + PPT |

## BR

| BR | Business Rule | Status |
|---|---|---|
| BR-FLEX-01 | FLEX 대상자만 근무계획 입력 가능 | CANDIDATE |
| BR-FLEX-02 | 시간 입력은 10분 단위 | CANDIDATE |
| BR-FLEX-03 | 시작시간은 종료시간보다 이전 | CANDIDATE |
| BR-FLEX-04 | 사원+근무일자 기준 1개 근무계획 유지 | CANDIDATE |
| BR-FLEX-05 | CONFIRMED 상태는 화면에서 직접 수정 금지 | CUSTOMER_CONFIRM_REQUIRED |
| BR-FLEX-06 | 예상근무시간은 입력시간을 기준으로 계산 | CANDIDATE |
| BR-FLEX-07 | 미입력자는 알람메일 대상 후보 | CANDIDATE |

## AC

| AC | 완료조건 |
|---|---|
| AC-FLEX-01 | FLEX 대상자가 09:00~18:10 계획을 저장할 수 있다 |
| AC-FLEX-02 | 09:05와 같이 10분 단위가 아닌 시간은 저장되지 않는다 |
| AC-FLEX-03 | 시작시간 >= 종료시간이면 저장되지 않는다 |
| AC-FLEX-04 | 동일 사원/일자 계획이 존재하면 Insert가 아닌 Update 흐름을 사용한다 |
| AC-FLEX-05 | CONFIRMED 계획 수정 시 차단된다 |
| AC-FLEX-06 | 월 조회 시 Calendar와 일자별 상태를 볼 수 있다 |
| AC-FLEX-07 | 기본값이 존재하면 신규 계획 입력 시 초기값으로 제안된다 |
| AC-FLEX-08 | 미입력자 알람 연계 대상이 식별된다 |

## Scope

### In
- ESS 화면 조회/저장/수정
- 10분 단위 변경
- Calendar/예상시간
- 기본값
- 미입력 알람 연계 Candidate

### Out / Separate Program
- 근태집계/마감 자체 계산로직 변경
- 전자결재
- 관리자 대량등록
- 확정 이후 예외승인 Process 상세

## Clarification Priority

P0 — Source 생성 전 필요:
- 실제 `CONFIRMED` Code
- 휴게시간/예상근무시간 계산 Rule
- 실제 권한/Profile ID

P1 — 통합 Test 전 필요:
- 알람메일 Schedule/수신자
- 근태집계/마감의 정확한 소비 Program

## Next

Customer Review → Functional/Development Blueprint → Brownfield Source Validation.