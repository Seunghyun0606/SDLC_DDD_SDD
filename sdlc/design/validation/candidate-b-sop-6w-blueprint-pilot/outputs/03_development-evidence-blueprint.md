# Development Evidence Blueprint — RQ-FLEX-PLAN-001

> progress: `DRAFT_COMPLETE_FOR_FIXTURE`
> actual_source_write: `DENY_REAL_REPO`

## 1. Business / 6W Reference

- Who: ESS_PROFILE_FLEX worker — Evidence: PPT + Source candidate
- When: daily — Evidence: PPT
- Where: ESS flex work-plan menu — Evidence: PPT + JSP
- What: date/type/start/end/expected/status — Evidence: PPT + XLSX + Source
- How: validate → insert/update — Evidence: XLSX/PPT/Source
- Why: attendance aggregation/closing basis — Evidence: PPT + downstream candidate

## 2. UI Evidence

| UI | Expected | Evidence | Truth |
|---|---|---|---|
| 월 Calendar | required | XLSX TE004 + PPT + JSP | OBSERVED_FOR_PILOT |
| workDate | required/editable | PPT + Table key | OBSERVED |
| workTypeCode | required | PPT + WORK_TYPE source query | OBSERVED |
| start/end | required | PPT + JSP | OBSERVED |
| expectedMinutes | read only | XLSX TE005 + JSP | OBSERVED |
| status | read only | PPT + table field | OBSERVED |
| delete button | none | no evidence | NONE_OBSERVED |

## 3. CRUD / Data

| Action | Mapper | Table | Evidence |
|---|---|---|---|
| 월조회 | selectMonthlyWorkPlans | TB_FLEX_WORK_PLAN | Source Fixture |
| 일조회 | selectWorkPlan | TB_FLEX_WORK_PLAN | Source Fixture |
| 신규 | insertWorkPlan | TB_FLEX_WORK_PLAN | Source Fixture |
| 수정 | updateWorkPlan | TB_FLEX_WORK_PLAN | Source Fixture |
| 기본값 조회 | selectDefaultPlan | TB_WORK_PLAN_DEFAULT | Source Fixture |
| 기본값 등록/수정 | insert/updateDefaultPlan | TB_WORK_PLAN_DEFAULT | Source Fixture |

## 4. Core Logic / Evidence

```text
profile check          OBSERVED
30-minute current rule OBSERVED AS-IS
10-minute desired rule GIVEN/OBSERVED
insert-vs-update       OBSERVED
confirmed edit block   PPT GIVEN, SOURCE NOT_OBSERVED
start<end              PPT GIVEN, SOURCE NOT_OBSERVED
```

### TO-BE Proposal

1. Current 30분 UI option → 10분 option
2. `%30` validation → `%10`
3. start<end validation 추가/확인
4. actual status code 확인 후 Confirmed edit guard
5. Existing Insert/Update/Transaction pattern 유지

## 5. Query Evidence

```sql
SELECT EMP_ID, WORK_DATE, START_TIME, END_TIME, WORK_TYPE_CD, STATUS_CD
FROM TB_FLEX_WORK_PLAN
WHERE EMP_ID = #{employeeId}
  AND WORK_DATE = #{workDate}
```

`EMP_ID + WORK_DATE` key: OBSERVED_FOR_FIXTURE.
Actual index/unique constraint: `NOT_VERIFIED`.

## 6. Common Code

| Concept | Value | Evidence | Permission |
|---|---|---|---|
| Work Type | WORK_TYPE/FLEX | Source query + Service | REUSE_ALLOWED_FOR_FIXTURE |
| Confirmed State | CONFIRMED business label | PPT only | HARDCODE_DENY |
| Time Unit | 10 minutes | requirement/rule | validation, not code |

## 7. Integration

- Attendance aggregation/closing reader: `CANDIDATE / NOT_RUNTIME_VERIFIED`
- Missing-plan mail: `REQUIREMENT_CANDIDATE / TARGET_OPEN`
- e-Approval: `NONE_BY_SCOPE`

## 8. Source Target Proof

```yaml
proof:
  jsp: flexWorkPlan.jsp
  service: FlexWorkPlanService.savePlan
  mapper_xml: FlexWorkPlanMapper.xml
  table: TB_FLEX_WORK_PLAN
  result: PASS_FOR_FIXTURE_ONLY
```

## 9. Action Permissions

```yaml
action_permissions:
  analysis_draft: ALLOW
  customer_review: ALLOW
  development_blueprint: ALLOW
  patch_proposal_fixture: ALLOW
  actual_customer_source_write: DENY
  merge: DENY
  release: DENY
  verify_pass: DENY
```

## 10. Required before Real Write

1. 실제 repo commit/source hashes
2. 실제 Security Profile mapping
3. 실제 CONFIRMED 상태 Code
4. 실제 unique/index/lock
5. 실제 downstream caller/consumer
6. 실제 build/test command 및 테스트 실행환경