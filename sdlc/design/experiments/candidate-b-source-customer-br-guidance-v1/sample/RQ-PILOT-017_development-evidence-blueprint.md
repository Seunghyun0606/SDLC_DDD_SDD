# TASK-P017-DEV-01 / PGM-ATT-CLOSE-001 — Development Evidence Blueprint

> `PILOT_FIXTURE`. 실제 고객 Source/Schema가 아니므로 미확인 값은 권한을 제한한다.

## 1. 6W Scenario Evidence

| 6W | Value | Truth | Evidence |
|---|---|---|---|
| Who | 근태마감 권한 사용자 또는 마감 Batch | INFERRED/OPEN_PROFILE | RQ/Fixture, 실제 Auth 없음 |
| When | 일마감 또는 월마감 후 승인 수정요청 재집계 | GIVEN | RQ + CR-PILOT-001 |
| Where | 근태마감 업무기능 | INFERRED/OPEN_ENTRY | Fixture Service, 실제 Menu/Batch 미확인 |
| What | 사원/근무일자의 계획근무분 → 일집계 | OBSERVED | Mapper/Table Fixture |
| How | 상태/승인/FORCE 검증 → 계획 조회 → 10분 계산 → UPSERT | DESIGN | functional/PGM design |
| Why | 계획과 마감결과 단위 일치 + 월마감 후 변경통제 | GIVEN/INFERRED | RQ + CR |

6W coverage: `PARTIAL_WITH_CRITICAL_OPEN_WHO_WHERE`.

## 2. UI / Channel

- UI change: `NO_UI_CHANGE_ASSUMED`
- actual menu/screen: `OPEN`
- actual batch entry: `OPEN`
- closeType input source: `OPEN`
- correction request selection/reference: `OPEN`

따라서 UI 변경 Source Write 권한은 `DENY`; Service/Mapper Fixture proposal만 평가한다.

## 3. Field/Input

| Field | Meaning | Evidence | Status |
|---|---|---|---|
| employeeId | 대상 사원 | Service parameter | OBSERVED |
| workDate | 근무일 | Service parameter | OBSERVED |
| closeType | 마감유형 | Fixture parameter | OBSERVED_BUT_CODE_OPEN |
| plannedMinutes | 계획근무분 | TB_WORK_PLAN | OBSERVED |
| approvalStatus | 승인상태 | TB_ATT_CORRECTION_REQ | DESIGN_TARGET / CODE_OPEN |

## 4. CRUD

| Action | Mapper | Target | CRUD | Evidence |
|---|---|---|---|---|
| 계획 조회 | selectPlannedMinutes | TB_WORK_PLAN | R | Fixture source |
| 월마감 확인 | isMonthClosed | TB_ATT_CLOSE | R | Design + Fixture target |
| 승인 수정 조회 | hasApprovedCorrection | TB_ATT_CORRECTION_REQ | R | Design + Fixture target |
| 일집계 반영 | upsertDailyAttendance | TB_ATT_DAILY | C/U | Fixture source |
| 마감상태 갱신 | existing close statement | TB_ATT_CLOSE | U | Existing flow candidate |

Delete: `NONE_CONFIRMED_FOR_FIXTURE`.

## 5. Core Logic

| monthClosed | closeType | approved | result |
|---|---|---|---|
| N | ANY | N/A | calculate by 10m + write |
| Y | FORCE_CLOSE | ANY | reject before write |
| Y | NORMAL | Y | recalculate + write |
| Y | NORMAL | N | reject before write |

Calculation: `floor(plannedMinutes / 10) * 10`.

잔여분 절삭은 고객확인 미완료 → merge/release denial reason.

## 6. Integration

Direct interface change: `NONE_ASSUMED_FROM_FIXTURE`.

Upstream approval dependency blind spots:
- 누가 TB_ATT_CORRECTION_REQ를 갱신하는지
- 승인취소/반려
- 비동기 반영 지연
- duplicate/race

이 Evidence가 실제 프로젝트에서 중요하면 Impact Escalation.

## 7. Query/Data

### selectPlannedMinutes
- key: employeeId + workDate candidate
- table: TB_WORK_PLAN
- actual PK/index/cardinality: OPEN

### isMonthClosed
- target: TB_ATT_CLOSE
- month key/scope: OPEN
- lock/index: OPEN

### hasApprovedCorrection
- target: TB_ATT_CORRECTION_REQ
- filter: employeeId + workDate + approved code
- actual approval code: OPEN

### Write
- existing Oracle MERGE 유지
- MERGE Key 변경 금지
- actual Null/Lock semantics: OPEN_RUNTIME

## 8. Common Code

| Candidate | Truth | Authority | Permission Impact |
|---|---|---|---|
| FORCE_CLOSE | OBSERVED_FIXTURE | SOURCE_LITERAL_ONLY | merge DENY until Code Master verify |
| APPROVED | DESIGN_FIXTURE | NONE | merge DENY until Code Master verify |

## 9. Transaction/Auth/Audit

- transaction owner: AttendanceCloseService.closeDaily — OBSERVED_FIXTURE
- auth profile: OPEN — CRITICAL
- logging: existing pattern 유지 — OBSERVED
- PII log review: OPEN

## 10. Current Source Mapping

| File | Symbol | Evidence State | Change |
|---|---|---|---|
| AttendanceCloseService.java | closeDaily | CURRENT_FIXTURE_HASH | MODIFY |
| AttendanceCloseMapper.java | isMonthClosed/hasApprovedCorrection | TARGET_DESIGN | ADD |
| AttendanceCloseMapper.xml | statements | TARGET_DESIGN | ADD |

## 11. Tests

- AC-01 485→480
- AC-03 month closed + approved → success
- AC-04 month closed + unapproved → no write
- AC-05 approved + FORCE_CLOSE → no write
- regression normal daily close

Runtime evidence: `NOT_EXECUTED`.

## 12. Blind Spots

- actual authorization profile
- actual menu/batch entry
- month close scope/key
- code master values
- real correction request schema/index
- runtime lock/performance

## 13. Target Write Proof

Fixture result: `PASS_FOR_FIXTURE_SERVICE_MAPPER_ONLY`.

Real customer source result: `NOT_READY`.

Evidence families needed:
- current source symbol/path
- canonical TASK↔PGM
- mapper relation
- real code master/schema
- current branch revision

## 14. Action Permissions

```yaml
proposal: ALLOW
fixture_draft_source_write: ALLOW
real_customer_source_write: DENY
ui_source_write: DENY
merge: DENY
release: DENY
verify_pass: DENY
```
