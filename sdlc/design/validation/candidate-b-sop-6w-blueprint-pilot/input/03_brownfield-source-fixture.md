# Input 03 — Brownfield Source Evidence Fixture

> `SIMULATED SOURCE EVIDENCE`. 실제 고객 Repository가 아니다.

## Current Stack

`JSP → Spring MVC → Service(@Transactional) → MyBatis Mapper/XML → Oracle`

## Current Targets

- `src/main/webapp/WEB-INF/jsp/attendance/flexWorkPlan.jsp`
- `FlexWorkPlanController`
- `FlexWorkPlanService.savePlan`
- `FlexWorkPlanMapper`
- `mapper/FlexWorkPlanMapper.xml`

## Current Observations

### JSP
현재 시작/종료 시간 Option이 30분 간격이다.

### Service

```java
if (!"FLEX".equals(profile.getWorkTypeCode())) throw ...;
if (cmd.getStartMinute() % 30 != 0 || cmd.getEndMinute() % 30 != 0) throw ...;
WorkPlan current = mapper.selectWorkPlan(employeeId, cmd.getWorkDate());
if (current == null) mapper.insertWorkPlan(...);
else mapper.updateWorkPlan(...);
```

### Mapper Statements

- selectWorkProfile
- selectWorkPlan
- selectMonthlyWorkPlans
- selectDefaultPlan
- insertDefaultPlan
- updateDefaultPlan
- insertWorkPlan
- updateWorkPlan

### Data

- `TB_FLEX_WORK_PLAN` — `EMP_ID + WORK_DATE`, R/C/U
- `TB_EMP_WORK_PROFILE` — 대상 근무유형, R
- `TB_WORK_PLAN_DEFAULT` — 개인 기본값, R/C/U
- `CM_CODE_DETAIL` — `WORK_TYPE`, R

### Common Code

Source에서 `WORK_TYPE/FLEX` 사용이 관찰된다.
`STATUS_CD=CONFIRMED`의 실제 Code 값은 이 Fixture에 명시하지 않는다.

### Downstream Candidate

`AttendanceAggregationMapper.selectFlexPlanForAggregation`가 `TB_FLEX_WORK_PLAN`을 읽는 것으로 가정한다.

## Evidence Revision

```yaml
source_commit: FIXTURE-SRC-001
source_scope: FLEX_WORK_PLAN
currentness: CURRENT_FOR_PILOT
runtime_verified: false
```

## Blind Spots

- 실제 Security interceptor/profile mapping
- DB Index/Lock
- 실제 상태 Code Master
- Mail Batch
- 실제 Integration runtime trace