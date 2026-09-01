---
program_id: PGM-ATT-CLOSE-001
revision: 2
validity: CURRENT
change_type: MODIFY
---
# PGM-ATT-CLOSE-001 Attendance Close

## Artifact
- `AttendanceCloseService.java`
- `AttendanceCloseMapper.java`
- `AttendanceCloseMapper.xml`

## AS-IS
Service가 계획분을 30분 단위로 절삭하고 `TB_ATT_DAILY`을 갱신한다. 월마감 후 수정요청 정책은 구현되지 않았다.

## TO-BE
- 10분 단위 절삭.
- `isMonthClosed` 조회 추가.
- `hasApprovedCorrection` 조회 추가.
- FORCE_CLOSE 월마감 후 재집계 금지.

## Data
READ: TB_WORK_PLAN, TB_ATT_CLOSE, TB_ATT_CORRECTION_REQ.
WRITE: TB_ATT_DAILY, TB_ATT_CLOSE.

## Transaction / Error
검증과 Write를 동일 Spring Transaction에서 수행. 허용조건 불충족은 Write 전 예외.

## Applicable Standard
- Java Service에서 Transaction Boundary 유지.
- Mapper Interface/XML ID 일치.
- Oracle MERGE 사용 시 Key 조건 고정.
- 관련 없는 Refactoring 금지.

## Test Mapping
AC-01~05 전부 필수.
