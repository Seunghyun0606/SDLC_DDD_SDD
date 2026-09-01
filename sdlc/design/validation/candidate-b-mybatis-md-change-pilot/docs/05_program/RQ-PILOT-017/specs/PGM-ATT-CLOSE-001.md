---
stage: PROGRAM
progress: COMPLETE
quality: OK
validity: CURRENT
program_id: PGM-ATT-CLOSE-001
---
# PGM-ATT-CLOSE-001

## Artifacts
AttendanceCloseService.java / AttendanceCloseMapper.java / AttendanceCloseMapper.xml.

## Change
30→10분 절삭, 월마감 조회, 승인수정요청 조회, FORCE_CLOSE 차단.

## Data
READ TB_WORK_PLAN/TB_ATT_CLOSE/TB_ATT_CORRECTION_REQ. WRITE TB_ATT_DAILY/TB_ATT_CLOSE.

## Execution Contract
Actual Draft Write 전에 Central Store AVAILABLE + `PGM-ATT-CLOSE-001` Lane 소유 + Work Unit PREPARED + Target Write Proof PASS가 모두 필요.
