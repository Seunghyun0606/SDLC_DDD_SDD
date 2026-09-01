# TASK-P017-DEV-01 / PGM-ATT-CLOSE-001 — Development Blueprint

> 상태: `PILOT_FIXTURE / SOURCE-READY CONTRACT SAMPLE`
> 실제 고객 Repository가 아니므로 화면명/Code 등 Fixture에 없는 값은 `OPEN` 또는 `PILOT_ASSUMPTION`으로 표시한다.

## 1. 6W Business Scenario

| 6W | 내용 | Truth |
|---|---|---|
| Who | 근태마감 권한을 가진 업무담당자 또는 마감 Batch Actor | OPEN — 실제 권한 Profile 확인 필요 |
| When | 일근태 마감 시; 월마감 이후 승인 수정요청 재집계 시 | GIVEN/CR |
| Where | 근태마감 기능. 실제 Menu/Batch Entry는 Repository/화면목록으로 확인 필요 | OPEN |
| What | 대상 사원/근무일자의 근무계획 분과 근태 일집계 결과 | OBSERVED_FROM_FIXTURE |
| How | 마감상태/수정승인/FORCE_CLOSE 검증 → 계획분 조회 → 10분 단위 계산 → 일집계 UPSERT | DESIGN |
| Why | 10분 단위 근무계획과 근태마감 결과를 일치시키고, 월마감 후 변경을 통제 | RQ/CR |

## 2. Screen / Channel Spec

### UI Change
`NO_UI_CHANGE_ASSUMED`

Pilot Source에는 UI Fixture가 없으므로 신규 Field/Button을 임의 설계하지 않는다.

개발 전 확인:
- 실제 근태마감 메뉴/화면 ID
- `closeType` 입력 위치
- 수정요청 선택/참조 방식
- 월마감 후 재집계 Action의 노출 권한

확인 전에는 Service/Mapper 변경만 Source-ready Candidate다.

## 3. Field / Input Contract

| Field | 의미 | Source | Required | Validation |
|---|---|---|---|---|
| employeeId | 대상 사원 | closeDaily parameter | Y | 존재/권한은 기존 Pattern 유지 |
| workDate | 근무일자 | closeDaily parameter | Y | 월마감 상태 조회 Key |
| closeType | 마감유형 | closeDaily parameter | Y | 실제 Code Master 확인 필요 |
| plannedMinutes | 계획근무분 | TB_WORK_PLAN query | Y | null/default 정책 확인 필요 |
| reflectedMinutes | 반영근무분 | calculated | Y | 10분 단위 절삭 |
| approvalStatus | 수정요청 승인상태 | TB_ATT_CORRECTION_REQ | 조건부 | `APPROVED` 실제 Code 확인 필요 |

`FORCE_CLOSE`, `APPROVED` 문자열은 Pilot Fixture 값이며 실제 프로젝트에서는 Common Code Evidence 확인 전 하드코딩 금지.

## 4. CRUD Matrix

| Action | Service | Mapper Statement | Target | CRUD | 조건 |
|---|---|---|---|---|---|
| 계획분 조회 | closeDaily | selectPlannedMinutes | TB_WORK_PLAN | R | employeeId + workDate |
| 월마감 조회 | closeDaily | isMonthClosed | TB_ATT_CLOSE | R | employeeId/workDate 또는 월 Key — 실제 Schema 확인 |
| 승인 수정요청 조회 | closeDaily | hasApprovedCorrection | TB_ATT_CORRECTION_REQ | R | employeeId + workDate + approval status |
| 일집계 반영 | closeDaily | upsertDailyAttendance | TB_ATT_DAILY | C/U | validation 통과 후 |
| 마감상태 반영 | closeDaily | 기존 close statement | TB_ATT_CLOSE | U | 기존 Flow 유지 |

Delete는 본 Scope에 없다: `DELETE = NONE_CONFIRMED_FOR_FIXTURE`.

## 5. Core Business Logic

### Decision Table

| monthClosed | closeType | approvedCorrection | 결과 |
|---|---|---|---|
| N | ANY | N/A | 10분 단위 집계 후 마감 |
| Y | FORCE_CLOSE | ANY | Reject |
| Y | NORMAL | Y | 10분 단위 재집계 허용 |
| Y | NORMAL | N | Reject |

### Calculation

```text
reflectedMinutes = floor(plannedMinutes / 10) * 10
```

10분 미만 잔여분 절삭 정책은 고객 확인 필요.

### Validation Order

1. 대상/입력 기본 검증
2. 월마감 여부
3. FORCE_CLOSE 여부
4. 승인 수정요청 존재 여부
5. 계획분 조회
6. 10분 단위 계산
7. TB_ATT_DAILY write
8. 기존 마감상태 처리

Write 이전에 Validation 실패 시 종료한다.

## 6. State / Error

상태 후보:

```text
OPEN/DAILY_CLOSE
→ CLOSED
→ MONTH_CLOSED
→ APPROVED_CORRECTION
→ RECALCULATED
```

실제 State Code는 Source/Code Master 확인 필요.

오류 Candidate:
- MONTH_CLOSED_WITHOUT_APPROVED_CORRECTION
- FORCE_CLOSE_RECALCULATION_DENIED

실제 Error Code/Message Convention은 Brownfield Source Profile에서 가져온다.

## 7. Integration Contract

직접 외부 Interface 변경: `NONE_CONFIRMED_FOR_FIXTURE`.

다만 `TB_ATT_CORRECTION_REQ`의 승인상태가 전자결재/승인 프로세스에서 생성된다면 Upstream Dependency가 존재한다.

확인 필요:
- 승인상태 생성 Program
- 승인취소/반려 시 상태변화
- Async 반영 지연 여부
- 중복 승인/취소 race condition

## 8. Query / Data Contract

### Q1 selectPlannedMinutes

목적: 대상 일자의 계획근무분 조회.

```sql
SELECT planned_minutes
FROM TB_WORK_PLAN
WHERE emp_id = :employeeId
  AND work_date = :workDate
```

실제 Column/PK/복수 계획 Row 정책은 real schema에서 확인.

### Q2 isMonthClosed

목적: 해당 일자의 월마감 상태 확인.

필수 확인:
- 월 Key 계산 방식
- 사원별/조직별/전사별 마감 Scope
- Index/Lock

### Q3 hasApprovedCorrection

목적: 월마감 이후 허용 가능한 수정요청 존재 확인.

```sql
SELECT COUNT(*)
FROM TB_ATT_CORRECTION_REQ
WHERE emp_id = :employeeId
  AND work_date = :workDate
  AND approval_status = :approvedCode
```

`approval_status='APPROVED'` 하드코딩 여부는 실제 Code Master 확인 전 결정하지 않는다.

### Write

`TB_ATT_DAILY` 기존 Oracle MERGE Key/Null semantics를 유지한다. Key를 재설계하지 않는다.

## 9. Common Code

| Group | Value | 상태 | 조치 |
|---|---|---|---|
| ATT_CLOSE_TYPE 후보 | FORCE_CLOSE | PILOT_ASSUMPTION | 실제 Code Master 확인 |
| APPROVAL_STATUS 후보 | APPROVED | PILOT_ASSUMPTION | 실제 Code Master 확인 |

## 10. Transaction / Authorization / Audit

- Transaction owner: `AttendanceCloseService.closeDaily`
- Spring `@Transactional` 기존 Pattern 유지
- 검증과 Write는 동일 Transaction Boundary
- 실제 Authorization Profile은 OPEN
- 기존 마감 Audit/Logging Pattern 유지
- PII가 Log에 직접 노출되는지 Source Review 필요

## 11. Brownfield Source Mapping

| Layer | File | Symbol | Change |
|---|---|---|---|
| Service | AttendanceCloseService.java | closeDaily | 30→10분 계산 + 월마감 정책 |
| Mapper Interface | AttendanceCloseMapper.java | isMonthClosed/hasApprovedCorrection | ADD |
| Mapper XML | AttendanceCloseMapper.xml | 동일 statement | ADD |
| Existing SQL | Mapper XML | upsertDailyAttendance | 기존 Key 유지 |

## 12. Test Mapping

- AC-01: 485분 → 480분
- AC-03: 월마감 + 승인 수정요청 → 성공
- AC-04: 월마감 + 미승인 → write 없이 실패
- AC-05: 월마감 + 승인 + FORCE_CLOSE → write 없이 실패
- Regression: 미월마감 기존 정상마감
- Data: 실패 Case에서 TB_ATT_DAILY 미변경

## 13. Source-ready Open Items

`CRITICAL OPEN`:
- 실제 근태마감 권한/Profile
- 실제 메뉴/Entry point
- 월마감 Scope/Key
- 실제 승인/마감 Common Code
- TB_ATT_CORRECTION_REQ 실제 Schema/Index

따라서 Fixture Patch는 가능하지만 실제 고객 Source Write는 이 항목 Evidence 확보 후에 수행한다.
