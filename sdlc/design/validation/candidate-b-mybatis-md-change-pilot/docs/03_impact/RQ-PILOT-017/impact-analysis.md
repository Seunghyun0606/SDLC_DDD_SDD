---
stage: IMPACT
progress: COMPLETE
quality: WARNING
validity: CURRENT
---
# Impact Analysis

## Coverage Basis
Fixture Source + Mapper XML 정적 Inspection.

## Confirmed in Fixture
- AttendanceCloseService.closeDaily
- AttendanceCloseMapper
- AttendanceCloseMapper.xml
- TB_WORK_PLAN READ
- TB_ATT_DAILY WRITE
- TB_ATT_CLOSE READ/WRITE
- TB_ATT_CORRECTION_REQ NEW READ

## Blind Spots
실제 Batch/Scheduler, Procedure/Trigger, 다른 Consumer는 Fixture에 없으므로 실제 프로젝트에서는 확인 필요.

## Target Write Proof
```yaml
program_id: PGM-ATT-CLOSE-001
resolver_confidence: HIGH
proof: PASS_FOR_FIXTURE
independent_evidence:
  - current_source_symbol
  - mapper_xml_table_relation
source_revision: fixture-as-is-v1
```

## Permissions
```yaml
draft_source_write: ALLOW
merge: DENY
release: DENY
reason: runtime test 미실행 + pilot only
```
