# Input 03 — Brownfield JSP / Spring / MyBatis Source Fixture

> `SIMULATED SOURCE EVIDENCE`. 실제 고객 Repository가 아니라 개발 Blueprint 충분성을 검증하기 위한 가상 Brownfield 코드 구조다.

## Project Stack

```text
JSP
→ Spring MVC Controller
→ Service (@Transactional)
→ MyBatis Mapper Interface
→ Mapper XML
→ Oracle
```

## Current Artifact Map

| Layer | Path / Symbol | Current Responsibility |
|---|---|---|
| JSP | `src/main/webapp/WEB-INF/jsp/attendance/flexWorkPlan.jsp` | 월 Calendar + 일자별 계획 입력 |
| Controller | `FlexWorkPlanController` | 조회/저장 Request Mapping |
| Service | `FlexWorkPlanService.savePlan` | 권한/시간 검증 후 Insert/Update |
| Mapper | `FlexWorkPlanMapper` | Plan/Profile/Code 조회 및 Plan Write |
| XML | `mapper/FlexWorkPlanMapper.xml` | Oracle SQL |

## JSP AS-IS Snippet

```jsp
<select id="startTime">
  <option value="0900">09:00</option>
  <option value="0930">09:30</option>
  <option value="1000">10:00</option>
</select>
<select id="endTime">...</select>
<input id="expectedMinutes" readonly />
<button id="btnSave">저장</button>
```

Observation: 현재 Fixture UI는 30분 단위 Time Option을 사용한다.

## Service AS-IS Snippet

```java
@Transactional
public void savePlan(String employeeId, WorkPlanCommand cmd) {
    WorkProfile profile = mapper.selectWorkProfile(employeeId, cmd.getWorkDate());
    if (!"FLEX".equals(profile.getWorkTypeCode())) {
        throw new BusinessException("NOT_FLEX_WORKER");
    }
    if (cmd.getStartMinute() % 30 != 0 || cmd.getEndMinute() % 30 != 0) {
        throw new BusinessException("INVALID_TIME_UNIT");
    }
    WorkPlan current = mapper.selectWorkPlan(employeeId, cmd.getWorkDate());
    if (current == null) mapper.insertWorkPlan(employeeId, cmd);
    else mapper.updateWorkPlan(employeeId, cmd);
}
```

## Mapper / SQL AS-IS

```text
selectWorkProfile
selectWorkPlan
selectMonthlyWorkPlans
selectDefaultPlan
insertDefaultPlan
updateDefaultPlan
insertWorkPlan
updateWorkPlan
```

```sql
SELECT EMP_ID, WORK_DATE, START_TIME, END_TIME, WORK_TYPE_CD, STATUS_CD
FROM TB_FLEX_WORK_PLAN
WHERE EMP_ID = #{employeeId}
  AND WORK_DATE = #{workDate}
```

```sql
SELECT CODE, CODE_NAME
FROM CM_CODE_DETAIL
WHERE CODE_GROUP = 'WORK_TYPE'
  AND USE_YN = 'Y'
```

## Physical Data Evidence

| Object | Key / Meaning | Access |
|---|---|---|
| `TB_FLEX_WORK_PLAN` | `EMP_ID + WORK_DATE` | R/C/U |
| `TB_EMP_WORK_PROFILE` | 적용 근무유형/Profile | R |
| `TB_WORK_PLAN_DEFAULT` | 개인별 입력 기본값 | R/C/U |
| `CM_CODE_DETAIL` | `WORK_TYPE` 공통코드 | R |

## Downstream Reference Evidence

가상 Batch Source `AttendanceAggregationMapper.selectFlexPlanForAggregation`이 `TB_FLEX_WORK_PLAN`을 조회한다고 가정한다.

이는 `저장된 계획이 근태집계/마감에서 참조된다`는 PPT 업무연계와 정합성을 보조하지만, 실제 고객 Repository에서는 반드시 Current Source Trace로 재검증해야 한다.

## Brownfield Findings

- AS-IS는 30분 단위 Validation/UI Option
- 이미 `FLEX` Work Type 검증이 존재
- `EMP_ID + WORK_DATE` 단일계획 구조가 존재
- Delete Statement는 없음
- Confirmed 상태 수정차단은 AS-IS Snippet에서 아직 관찰되지 않음

따라서 TO-BE에서 필요한 핵심 변경은 `10분 단위 UI/Validation`과 `CONFIRMED 수정차단`이며, 실제 고객 Source에서는 Transaction/Error/Code/Index/Lock을 다시 확인해야 한다.