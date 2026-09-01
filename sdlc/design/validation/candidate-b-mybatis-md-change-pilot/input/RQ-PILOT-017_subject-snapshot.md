# External Intake Subject Snapshot

> producer: `EXTERNAL_INTAKE_FOR_PILOT`
> Candidate B가 생성한 RQ가 아님.

```yaml
subject:
  type: RQ
  id: RQ-PILOT-017
  revision: 2
  title: 근태마감에 10분 단위 근무계획 반영
  legacy_source_ids: REQ_TM_TE016..REQ_TM_TE054
  business_goal: 10분 단위 근무계획을 근태마감 결과에 반영
  change:
    id: CR-PILOT-001
    statement: 월마감 이후 승인된 수정요청은 재집계 허용, FORCE_CLOSE는 제외
    truth: GIVEN
```

Candidate B는 이 입력의 Boundary 정합성을 재결정하지 않고 Stage Evidence/Execution Safety를 적용한다.
