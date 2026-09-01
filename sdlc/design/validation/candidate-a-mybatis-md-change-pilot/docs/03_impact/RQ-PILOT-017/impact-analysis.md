---
revision: 2
validity: CURRENT
fixture_evidence: true
---
# Impact Analysis

## Source Evidence
| Type | Target | Evidence | Change |
|---|---|---|---|
| Java | AttendanceCloseService.closeDaily | 30분 절삭 | MODIFY |
| Mapper | AttendanceCloseMapper | 계획분/마감상태 갱신 | MODIFY |
| XML | AttendanceCloseMapper.xml | TB_WORK_PLAN/TB_ATT_DAILY/TB_ATT_CLOSE | MODIFY |
| Data | TB_ATT_CORRECTION_REQ | AS-IS 미참조 | NEW READ |

## CR 전/후 Impact 차이
- rev1: `AttendanceCloseService`, `selectPlannedMinutes`, `upsertDailyAttendance` 중심.
- rev2: `TB_ATT_CLOSE` 월마감 조회와 `TB_ATT_CORRECTION_REQ` 승인 조회가 새 영향으로 추가됨.

## Target
`PGM-ATT-CLOSE-001` Candidate를 Confirmed로 승격하는 것은 이 Fixture 안에서만 유효하다.

## Blind Spots
실제 프로젝트라면 Batch, 다른 Service 호출자, Procedure/Trigger, 외부 Consumer를 Static Analysis로 추가 확인해야 한다.
