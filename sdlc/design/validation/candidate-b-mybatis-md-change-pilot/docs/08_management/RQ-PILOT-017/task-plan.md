# Developer Work Group / Task Plan

```yaml
group:
  id: DWG-P017-01
  name: 근태마감 10분 반영 + 월마감 수정정책
  recommended_owner_continuity: HIGH
  tasks:
    - TASK-P017-DEV-01
    - TASK-P017-DEV-02
    - TASK-P017-TST-01
```

| Task | PGM | 내용 | Lane |
|---|---|---|---|
| TASK-P017-DEV-01 | PGM-ATT-CLOSE-001 | Service 정책 변경 | SERIAL |
| TASK-P017-DEV-02 | PGM-ATT-CLOSE-001 | Mapper query 추가 | SERIAL |
| TASK-P017-TST-01 | PGM-ATT-CLOSE-001 | AC test | VERIFY, 병렬 준비 가능 |

DEV-01이 Lane을 소유한 동안 DEV-02의 분석/patch 준비는 가능하지만 실제 Source Write는 DENY한다. 동일 Developer에게 연속 배분하면 context switching을 줄일 수 있다.
