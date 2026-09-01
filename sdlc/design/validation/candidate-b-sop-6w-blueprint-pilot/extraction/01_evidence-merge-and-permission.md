# Evidence Merge + Action Permission

## 1. 6W Evidence Envelope

| 6W | Value | Truth | Evidence |
|---|---|---|---|
| Who | ESS_PROFILE_FLEX 탄력근로제 근무자 | OBSERVED_FOR_PILOT | PPT Slide1 + Source FLEX check |
| When | 매일 / 근무일자별 | GIVEN_FOR_PILOT | PPT Slide1; XLSX does not specify |
| Where | ESS 탄력근로제 근무계획 | OBSERVED_FOR_PILOT | PPT Slide2 + JSP path |
| What | 날짜/유형/시작/종료/예상시간/상태 | OBSERVED_FOR_PILOT | PPT + XLSX + Source |
| How | 10분 검증 → Create/Update, Confirmed 수정차단 | MIXED | XLSX/PPT + Source AS-IS partial |
| Why | 근태집계/마감 기준 제공 | GIVEN_FOR_PILOT | PPT Slide1/5 + downstream candidate |

## 2. Evidence Gaps

| Concern | Status | Execution Impact |
|---|---|---|
| 실제 ESS 권한/Profile ID | OPEN | Auth 관련 Source 변경 DENY |
| 실제 CONFIRMED 상태 Code | OPEN | 상태 비교 하드코딩 DENY |
| 10분 UI/Service Target | CURRENT_FOR_FIXTURE | Patch Proposal ALLOW |
| WORK_TYPE/FLEX | OBSERVED | Reuse Candidate ALLOW |
| DB Index/Lock | BLIND_SPOT | Query write/merge 전 검토 필요 |
| Mail Schedule | OPEN | Mail integration implementation DENY |
| Runtime downstream | NOT_VERIFIED | Integration CONFIRMED 금지 |

## 3. Target Proof for Fixture

```yaml
target_write_proof:
  result: PASS_FOR_FIXTURE_ONLY
  program: PGM-FLEX-PLAN-001
  evidence:
    - CURRENT_SOURCE_SYMBOL: FlexWorkPlanService.savePlan
    - CURRENT_SOURCE_PATH: flexWorkPlan.jsp
    - MAPPER_RELATION: FlexWorkPlanMapper.xml
    - DATA_RELATION: TB_FLEX_WORK_PLAN
  ambiguity:
    actual_customer_repo: UNRESOLVED
```

## 4. Action Permissions

| Action | Permission | Reason |
|---|---|---|
| 6W/RQ/FR/BR Candidate | ALLOW | Evidence sufficient for draft |
| Customer Review View | ALLOW | OPEN items visible |
| Development Blueprint | ALLOW | Fixture source identified |
| Patch Proposal against Fixture | ALLOW | Target proof PASS_FOR_FIXTURE |
| Actual Customer Source Write | DENY | Real current source/evidence absent |
| Hardcode CONFIRMED code | DENY | Code value OPEN |
| Mail integration write | DENY | Schedule/target OPEN |
| Merge/Release | DENY | No real tests / no customer repo |
| Verify PASS | DENY | Runtime tests not executed |

## 5. Workflow Continuation

`workflow_exit=OPEN`

분석/설계/고객검토/Fixture Patch Proposal은 계속 진행할 수 있으나 실제 고객 Source Write 권한은 별도다.