# Candidate A Sample Stage Outputs

> 입력: `요구사항목록.xlsx`
> Stress Group: `REQ_TM_TE016~REQ_TM_TE054`, 요구사항명 `10분단위 근무계획 개선 근태마감 반영을 구현`, 39 Raw Items
> 목적: Candidate A 계약을 실제 Stage 순서로 적용했을 때 사용자가 보게 될 산출물 형태를 예시한다.

# 1. INTAKE

```yaml
raw_inventory:
  source: 요구사항목록.xlsx
  raw_count: 142
  legacy_id_preserved: 142
selected_topic_group:
  id: TG-ATT-CLOSE-10MIN
  title: 10분단위 근무계획 개선 근태마감 반영을 구현
  item_count: 39
  legacy_ids: REQ_TM_TE016..REQ_TM_TE054
  publish_state: RAW_ONLY
alerts:
  - BOUNDARY_INCOMPLETE
```

사용자 View:

| 항목 | 값 |
|---|---|
| 원본 행 | 39 |
| 자동 RQ 생성 | 아니오 |
| 다음 작업 | RQ 경계 후보 생성 |

# 2. DECOMPOSE

```yaml
rq_candidate:
  id: RQC-ATT-001
  business_goal:
    value: 10분 단위 근무계획을 근태마감에 반영
    truth: INFERRED
  observable_outcome:
    value: 근태마감 결과에 10분 단위 계획이 반영됨
    truth: INFERRED
  actor_trigger:
    truth: OPEN
  policy_state_scope:
    truth: OPEN
  acceptance_release_scope:
    truth: OPEN
fr_candidates: 39
split_review:
  required: true
  reason: "FR Candidate 39개 + Boundary 핵심항목 미확정"
publish_permission: DENY
```

# 3. CLARIFY

Agent가 사용자에게 전달하는 질문 예:

1. 39개 항목은 모두 동일한 `근태마감` 결과를 만들기 위한 세부 기능인가?
2. 마감 실행 Actor/Trigger는 동일한가, 자동 Batch와 수동 마감이 섞여 있는가?
3. 일부 항목만 별도로 적용/배포할 수 있는가?
4. 마감 전/후 또는 확정/재오픈 등 서로 다른 State 정책이 섞여 있는가?
5. 법인/근무제/고용형태별로 서로 다른 정책 범위가 존재하는가?

산출물:

```yaml
clarification:
  target: RQC-ATT-001
  questions: 5
  answered: 0
  scope_revision: 1
  next_stage_allowed: PROCESS_DRAFT
```

# 4. PROCESS

현재 답변이 없으므로 Process는 Draft다.

```text
[INFERRED] 근무계획 생성/변경
        ↓
[OPEN] 마감 Trigger
        ↓
[INFERRED] 10분 단위 근무계획 반영
        ↓
[OPEN] 마감 상태 전환/재오픈/예외
```

- `process-analysis.md`: DRAFT
- RQ Split: 아직 결정하지 않음
- State Machine 차이가 확인되면 `SCOPE_CHANGE_CANDIDATE`

# 5. DISCOVERY

현재 Sample에는 Source Repository가 없으므로:

```yaml
discovery:
  status: PREPARED
  confirmed_programs: 0
  planned_queries:
    - "근태마감 처리 entry point 탐색"
    - "10분 단위 계획 참조 table/procedure 탐색"
    - "마감 Batch/manual trigger 분리 탐색"
  completion_claim: DENY
```

# 6. IMPACT

```yaml
impact:
  technical_candidates: []
  functional_candidate:
    - "근태마감 결과 계산"
  business_candidate:
    - "마감 시 근무계획 반영 규칙"
  confirmed: false
```

기술 Boundary가 이후 여러 PGM으로 발견되더라도 그것만으로 RQ를 자동 Split하지 않는다.

# 7. DESIGN

```yaml
functional_design:
  scope_revision: 1
  status: DRAFT
  target_outcome: "근태마감 결과에 10분 단위 근무계획 반영"
  open:
    - actor_trigger
    - close_state_transition
    - exception_policy
    - independent_release_scope
```

# 8. PROGRAM

Source Evidence 부재 상태:

```yaml
program_list:
  confirmed: []
  candidates: []
  discovery_required: true
```

FR 39개를 개발자에게 그대로 39개 RQ로 배정하지 않는다.

# 9. DEVELOPMENT

```yaml
development:
  source_write: DENY
  reason: "PGM/ART target evidence 없음"
  allowed:
    - task_candidate_design
    - source_discovery_plan
```

# 10. TEST

```yaml
test:
  candidate_scenarios:
    - 정상 마감 시 10분 단위 근무계획 반영
    - 마감 상태별 반영 여부
    - 예외 근무제/정책 범위
  executed_results: 0
  pass_claim: DENY
```

# 11. VERIFY

```yaml
verification:
  status: NOT_READY
  rq_boundary_verified: false
  implementation_verified: false
  test_verified: false
```

# 12. Candidate A에서 사용자가 실제 Review하는 지점

이 Sample에서 가장 중요한 Review는 INTAKE와 DECOMPOSE 사이의 숫자 개수가 아니라 다음 질문이다.

```text
39 Raw Items
→ 같은 업무 Outcome인가?
→ Actor/Trigger가 같은가?
→ 같은 State/Policy Scope인가?
→ 독립 Acceptance/Release가 필요한 부분이 있는가?
```

답에 따라 예를 들어 39개가 `마감 계산`, `마감 상태 전환`, `재오픈 후 재계산`의 서로 독립된 Outcome으로 확인되면 3개 RQ Candidate Split Proposal을 만들 수 있다. 반대로 동일 Outcome의 세부 계산 규칙이면 1 RQ + 다수 FR로 유지할 수 있다.

즉, **Agent가 숫자로 RQ 크기를 결정하지 않고 사용자가 업무 경계를 확인할 수 있는 근거를 제공하는 것**이 Candidate A의 제안이다.
