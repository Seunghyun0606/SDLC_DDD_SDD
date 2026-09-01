# ESS-FLEX-PLAN — 6W Business Definition with Evidence

> Status: `DRAFT_COMPLETE / BUSINESS_REVIEW_REQUIRED`

## Primary Scenario

`ESS_PROFILE_FLEX 권한의 탄력근로제 근무자가 매일 ESS 탄력근로제 근무계획 메뉴에서 근무일자/유형/시작/종료시간을 선택하여 10분 단위 검증 후 계획을 저장/수정하고, 해당 계획을 근태집계/마감 기준으로 제공한다.`

## 6W Evidence

### Who
- value: ESS_PROFILE_FLEX 탄력근로제 근무자
- truth: `OBSERVED_FOR_PILOT`
- evidence: PPT Slide1 + Source FLEX profile check
- open: 실제 고객 Profile ID

### When
- value: 매일 / 예정 근무일 계획 입력 시
- truth: `GIVEN_FOR_PILOT`
- evidence: PPT Slide1
- xlsx: 해당 정보 없음

### Where
- value: ESS > 근태/휴가 > 탄력근로제 근무계획
- truth: `OBSERVED_FOR_PILOT`
- evidence: PPT Slide2 + `flexWorkPlan.jsp`
- open: 실제 Menu ID/URL

### What
- value: 근무일자, 근무유형, 시작시간, 종료시간, 예상근무시간, 상태
- truth: `OBSERVED_FOR_PILOT`
- evidence: PPT Slide2 + XLSX TE001~005 + Source Table/UI

### How
- value: 조회 → 10분/시간범위/상태 검증 → Insert/Update
- truth: `MIXED`
- evidence:
  - XLSX: 등록/수정/조회
  - PPT: 10분/Confirmed rule
  - Source: Insert/Update + AS-IS 30분
- gap: CONFIRMED source rule not observed

### Why
- value: 예정근무시간을 근태집계/마감의 기준으로 제공하고 미입력을 예방
- truth: `GIVEN_FOR_PILOT`
- evidence: PPT Slide1/5 + XLSX alarm mail

## Business Rule State

| BR | Rule | Evidence State | Publish |
|---|---|---|---|
| BR-FLEX-01 | FLEX 대상자만 입력 | PPT + Source | CANDIDATE |
| BR-FLEX-02 | 10분 단위 | XLSX + PPT + AS-IS gap | CANDIDATE |
| BR-FLEX-03 | start < end | PPT only | REVIEW_REQUIRED |
| BR-FLEX-04 | 사원/일자 1계획 | PPT + Source key | CANDIDATE |
| BR-FLEX-05 | CONFIRMED 수정금지 | PPT only, source missing | REVIEW_REQUIRED |
| BR-FLEX-06 | 예상근무시간 계산 | XLSX + PPT | CANDIDATE |
| BR-FLEX-07 | 미입력 알람 후보 | XLSX + PPT | CANDIDATE |

## Action Impact

6W 문서 자체는 Complete로 작성 가능하지만 `BR-FLEX-05`, 실제 Profile ID, actual Code가 OPEN이므로 실제 고객 Source Write는 별도 제한한다.