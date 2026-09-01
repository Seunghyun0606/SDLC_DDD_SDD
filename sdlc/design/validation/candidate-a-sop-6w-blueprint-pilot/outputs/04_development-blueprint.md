# Development Blueprint — RQ-FLEX-PLAN-001

> Purpose: 개발자가 별도 추측 없이 UI/CRUD/Logic/Integration/Query/Data/Code/Source/Test를 이해하도록 하는 상세설계.

## 1. Business Scenario

`ESS_PROFILE_FLEX` 탄력근로제 근무자가 매일 ESS 근무계획 화면에서 근무일자/유형/시작/종료시간을 선택하여 10분 단위로 계획을 저장/수정한다. 저장된 계획은 근태집계/마감 기준으로 사용된다.

## 2. UI Specification

### Screen
- Logical ID: `SCR-FLEX-WORK-PLAN`
- Brownfield JSP: `src/main/webapp/WEB-INF/jsp/attendance/flexWorkPlan.jsp`

### Layout
1. 월 선택 + 조회
2. 월 Calendar
3. 선택일 상세 Panel
4. 저장/수정/기본값 Button

### Fields

| Field | UI Type | Required | Editable | Source/Code | Validation |
|---|---|---:|---:|---|---|
| workDate | Date | Y | Y | Calendar | 대상 월 내부 |
| workTypeCode | Select | Y | 조건부 | `CM_CODE_DETAIL/WORK_TYPE` | FLEX 대상자 기본값 |
| startTime | Time Select | Y | Y | UI generated | 10분 단위 |
| endTime | Time Select | Y | Y | UI generated | 10분 단위, start<end |
| expectedMinutes | Text | - | N | 계산값 | 계산 Rule 필요 |
| statusCode | Text/Badge | - | N | `TB_FLEX_WORK_PLAN.STATUS_CD` | CONFIRMED 시 수정불가 |

## 3. CRUD Matrix

| Use Case | Service | Mapper | Table | CRUD |
|---|---|---|---|---|
| 월 Calendar 조회 | findMonthlyPlans | selectMonthlyWorkPlans | TB_FLEX_WORK_PLAN | R |
| 일 계획 조회 | findPlan | selectWorkPlan | TB_FLEX_WORK_PLAN | R |
| 최초 저장 | savePlan | insertWorkPlan | TB_FLEX_WORK_PLAN | C |
| 기존 수정 | savePlan | updateWorkPlan | TB_FLEX_WORK_PLAN | U |
| 기본값 조회 | findDefault | selectDefaultPlan | TB_WORK_PLAN_DEFAULT | R |
| 기본값 등록 | saveDefault | insertDefaultPlan | TB_WORK_PLAN_DEFAULT | C |
| 기본값 수정 | saveDefault | updateDefaultPlan | TB_WORK_PLAN_DEFAULT | U |
| 삭제 | - | - | - | OUT_OF_SCOPE |

## 4. Core Business Logic

```text
savePlan(employeeId, command)
1. Work Profile 조회
2. FLEX 대상 여부 검증
3. 입력 Field 검증
4. 시작/종료가 10분 단위인지 검증
5. start < end 검증
6. 기존 계획 조회
7. 기존 상태가 CONFIRMED면 수정 차단
8. 예상근무시간 계산
9. 기존 없음 → INSERT
10. 기존 있음 → UPDATE
11. 결과 반환
```

### Decision Table

| Existing | Status | Time Valid | Action |
|---|---|---|---|
| N | - | Y | INSERT |
| Y | DRAFT | Y | UPDATE |
| Y | CONFIRMED | Y | ERROR |
| ANY | ANY | N | ERROR |

## 5. Integration

| Integration | Direction | Contract | Pilot Status |
|---|---|---|---|
| 근태집계/마감 | Work Plan → Downstream | `TB_FLEX_WORK_PLAN` 조회 | Source Candidate Observed |
| 알람메일 | Plan/No-plan → Mail Batch | 미입력 대상 추출 | Contract Detail OPEN |
| 전자결재 | - | 본 Scope 없음 | NONE_CONFIRMED_BY_PPT |

## 6. Query / Data Contract

### Plan Query

```sql
SELECT EMP_ID, WORK_DATE, START_TIME, END_TIME, WORK_TYPE_CD, STATUS_CD
FROM TB_FLEX_WORK_PLAN
WHERE EMP_ID = #{employeeId}
  AND WORK_DATE = #{workDate}
```

### Monthly Query

```sql
SELECT WORK_DATE, START_TIME, END_TIME, WORK_TYPE_CD, STATUS_CD
FROM TB_FLEX_WORK_PLAN
WHERE EMP_ID = #{employeeId}
  AND WORK_DATE BETWEEN #{monthStart} AND #{monthEnd}
ORDER BY WORK_DATE
```

### Common Code

```sql
SELECT CODE, CODE_NAME
FROM CM_CODE_DETAIL
WHERE CODE_GROUP = 'WORK_TYPE'
  AND USE_YN = 'Y'
```

### Data Objects

| Table | Key | Purpose | Write |
|---|---|---|---|
| TB_FLEX_WORK_PLAN | EMP_ID + WORK_DATE | 일자별 근무계획 | C/U |
| TB_EMP_WORK_PROFILE | EMP_ID + Effective Period | FLEX 대상 확인 | N |
| TB_WORK_PLAN_DEFAULT | EMP_ID | 개인 기본값 | C/U |
| CM_CODE_DETAIL | CODE_GROUP + CODE | 근무유형 Code | N |

## 7. Common Code

- `WORK_TYPE/FLEX`: Source Fixture에서 관찰됨
- `STATUS_CD/CONFIRMED`: PPT 업무값은 존재하지만 실제 Code 값은 `OPEN`
- 10분 단위는 Common Code가 아니라 Validation Rule

실제 고객 Source에서 `CONFIRMED` Code를 확인하기 전 하드코딩 금지.

## 8. Brownfield Source Mapping

| Design Concern | Current Target |
|---|---|
| 30→10분 UI Option | `flexWorkPlan.jsp` |
| 30→10분 validation | `FlexWorkPlanService.savePlan` |
| 확정 수정 차단 | `FlexWorkPlanService.savePlan` + status query |
| 월/일 조회 | `FlexWorkPlanMapper.xml` |
| Work Type Code | `CM_CODE_DETAIL` query |

### Preserve
- Service Transaction boundary
- Existing insert-vs-update Pattern
- Mapper Interface ↔ XML statement ID
- Existing Error Handling Pattern
- 관련 없는 Refactoring 금지

## 9. Transaction / Authorization / Error

- Transaction owner: Service save method
- Authorization: ESS Profile/WorkProfile check; 실제 Security annotation/interceptor는 OPEN
- Validation Error는 Write 이전 발생
- 동시 수정/Optimistic Lock은 현재 Evidence 없음 → OPEN

## 10. Test Mapping

| Test | Expected |
|---|---|
| FLEX user, 09:00~18:10 신규 | INSERT 성공 |
| 기존 DRAFT 09:10~18:20 | UPDATE 성공 |
| 09:05 입력 | INVALID_TIME_UNIT |
| start>=end | INVALID_TIME_RANGE |
| non-FLEX user | NOT_FLEX_WORKER |
| CONFIRMED 수정 | PLAN_CONFIRMED |
| 월 조회 | 일자별 Calendar 데이터 반환 |
| 기본값 존재 | 신규 입력 초기값 제안 |

## 11. Source-ready Gate

### Sufficient for Pilot Fixture
- Screen/Field: PASS
- CRUD: PASS
- Core Logic: PASS
- Query/Table: PASS_FOR_FIXTURE
- Common Code WORK_TYPE: PASS_FOR_FIXTURE
- Integration: PARTIAL
- Auth Profile actual ID: OPEN
- CONFIRMED actual Code: OPEN
- Expected time break deduction: OPEN
- Lock/Concurrency: OPEN

따라서 이 문서로 `Patch Proposal`은 충분하지만 실제 고객 Source Write 전 OPEN 항목의 영향도를 확인해야 한다.