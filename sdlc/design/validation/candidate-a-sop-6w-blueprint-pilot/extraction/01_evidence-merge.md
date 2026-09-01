# Extraction Result — XLSX + PPT SoP + Brownfield Source

## 1. 6W Merge

| 6W | XLSX | PPT SoP | Source | Merged Result |
|---|---|---|---|---|
| Who | OPEN | ESS_PROFILE_FLEX 탄력근로제 근무자 | FLEX Work Profile 검증 OBSERVED | ESS_PROFILE_FLEX 탄력근로제 근무자 |
| When | OPEN | 매일 예정 근무일 입력 | 날짜 Key 기반 구현 OBSERVED | 매일 / 근무일자별 |
| Where | OPEN | ESS > 근태/휴가 > 탄력근로제 근무계획 | `flexWorkPlan.jsp` OBSERVED | ESS 탄력근로제 근무계획 화면 |
| What | 등록/수정/조회, Calendar, 예상시간 | 근무일자/근무유형/시작/종료/예상시간/상태 | Physical Field/Table OBSERVED | 일자별 근무계획 |
| How | 등록/수정/조회/기본값/메일 | 10분 선택, 1일1계획, 확정 수정금지 | AS-IS Insert/Update + 30분 Validation | 조회→검증→Create/Update, TO-BE 10분 |
| Why | OPEN | 근태집계/마감 기준 제공 | Downstream read Candidate | 계획과 근태처리 기준 일치 |

## 2. UI / CRUD Merge

| Item | Evidence | Result |
|---|---|---|
| 월 Calendar | XLSX TE004 + PPT Slide2/4 + JSP | REQUIRED |
| 근무일자 | PPT + Table Key | REQUIRED |
| 근무유형 | PPT + `WORK_TYPE` Code | REQUIRED |
| 시작/종료시간 | PPT + JSP | REQUIRED |
| 예상근무시간 | XLSX TE005 + PPT + JSP | READ_ONLY |
| 상태 | PPT + Table Field | READ_ONLY |
| 조회 | XLSX | READ |
| 저장 | FL001/TE001 | CREATE when absent |
| 수정 | TE002 | UPDATE when existing and editable |
| 삭제 | Evidence 없음 / Mapper 없음 | OUT_OF_SCOPE / NOT ASSUMED |
| 기본값 | TE006~008 + PPT | R/C/U |
| 알람메일 | TE009 + PPT | INTEGRATION CANDIDATE |

## 3. Business Rule Candidate

| BR | Statement | Evidence |
|---|---|---|
| BR-FLEX-01 | FLEX 권한/근무유형 대상자만 계획 입력 가능 | PPT + Source Profile Check |
| BR-FLEX-02 | 시작/종료시간은 10분 단위 | PPT + XLSX 10분 요구 / Source AS-IS 30분 |
| BR-FLEX-03 | 시작시간 < 종료시간 | PPT |
| BR-FLEX-04 | 사원+근무일자 기준 1개 계획 | PPT + Physical Key |
| BR-FLEX-05 | CONFIRMED 계획은 화면에서 직접 수정 금지 | PPT; Source implementation missing |
| BR-FLEX-06 | 예상근무시간은 입력시간 기준 계산 | XLSX TE005 + PPT |
| BR-FLEX-07 | 미입력자는 알람메일 후보 | XLSX TE009 + PPT |

## 4. Source Change Candidates

- JSP time option generation: 30분 → 10분
- Service time-unit validation: `% 30` → `% 10`
- Service: `STATUS_CD=CONFIRMED` 수정차단 추가 필요
- Existing Insert/Update pattern 유지
- Existing `WORK_TYPE/FLEX` Common Code 재사용
- `TB_FLEX_WORK_PLAN`, `TB_EMP_WORK_PROFILE`, `TB_WORK_PLAN_DEFAULT`, `CM_CODE_DETAIL` 재사용

## 5. Still OPEN

- 실제 고객의 ESS Profile ID/권한 체계
- 실제 Menu ID/URL
- CONFIRMED 상태의 실제 Code 값
- 점심/휴게시간을 예상근무시간에서 어떻게 차감하는지
- 알람메일 발송 시각/대상선정 Batch
- DB Index/Lock/동시수정 정책

## Pilot Decision

XLSX 단독보다 PPT SoP + Source Evidence를 합쳤을 때 개발 가능한 수준으로 크게 개선되지만, OPEN 항목을 명시적으로 유지해야 한다.