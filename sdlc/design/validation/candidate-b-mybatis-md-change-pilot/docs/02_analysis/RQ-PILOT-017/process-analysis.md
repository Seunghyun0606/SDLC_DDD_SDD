---
stage: PROCESS
progress: COMPLETE
quality: WARNING
validity: CURRENT
---
# Process Analysis

```text
마감 요청
→ 월마감?
  ├ NO → 10분 집계/반영
  └ YES → FORCE_CLOSE?
            ├ YES → DENY
            └ NO → 승인 수정요청?
                      ├ YES → 재집계
                      └ NO → DENY
```

## Missing Evidence
- 실제 승인 Authority.
- Batch/수동 마감이 동일 Service를 사용하는지.

## Permission
다음 Discovery/Impact는 ALLOW, Source Write는 아직 DENY.
