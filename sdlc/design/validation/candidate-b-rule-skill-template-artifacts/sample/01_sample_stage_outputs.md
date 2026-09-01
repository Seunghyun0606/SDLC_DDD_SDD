# Candidate B Sample Stage Outputs

> 입력: `요구사항목록.xlsx`
> 대표 Stress Group: `REQ_TM_TE077~REQ_TM_TE099`, 근무집계 Batch 반영 23건
> 현재 입력에는 실제 Source Repository/Test Result가 없으므로 Source-bound Stage는 Evidence 부족 상태를 그대로 보여준다.

# 1. INTAKE

```yaml
stage: INTAKE
progress: COMPLETE
quality: WARNING
workflow_exit: OPEN
missing_evidence:
  - current_problem
  - desired_outcome_detail
action_permissions:
  next_stage_draft: ALLOW
  source_write: DENY
```

해석: Intake 산출물 작성은 완료됐지만 개발 가능하다는 뜻이 아니다.

# 2. DECOMPOSE

```yaml
stage: DECOMPOSE
progress: COMPLETE
quality: WARNING
workflow_exit: OPEN
outputs:
  requirement_candidates: PRESENT
  functional_candidates: PRESENT
action_permissions:
  canonical_publish: REQUIRES_DECISION
  next_stage_draft: ALLOW
```

# 3. CLARIFY

Batch 특성 때문에 다음 질문을 생성한다.

- 실행 Schedule/Trigger는 무엇인가?
- 재처리 정책은 무엇인가?
- 중복 실행 시 Idempotency가 보장되는가?
- 실패 후 Compensation은 무엇인가?
- Downstream Consumer는 누구인가?
- 실행 권한/운영 권한은 누구에게 있는가?

```yaml
stage: CLARIFY
progress: COMPLETE
quality: WARNING
business_truth_confirmation: DENY
next_stage_draft: ALLOW
```

# 4. PROCESS

```yaml
stage: PROCESS
progress: COMPLETE
quality: WARNING
outputs:
  process_draft: PRESENT
blind_spots:
  - batch_trigger
  - retry_and_duplicate
  - downstream_consumer
```

# 5. DISCOVERY

```yaml
stage: DISCOVERY
progress: COMPLETE
quality: CRITICAL
workflow_exit: OPEN
missing_evidence:
  - source_repository
  - static_index
outputs:
  discovery_queries: PRESENT
action_permissions:
  discovery_complete_claim: DENY
  source_write: DENY
```

B2 Option A이므로 `progress=COMPLETE`가 가능하지만 Discovery가 증거상 완료됐다고 주장하지 않는다.

# 6. IMPACT

```yaml
stage: IMPACT
progress: COMPLETE
quality: CRITICAL
coverage_basis: legacy_requirement_only
coverage_scope: requirement_text
blind_spots:
  - scheduler
  - shared_procedure
  - dynamic_sql
  - trigger
  - file_or_db_polling
  - downstream_consumer
runtime_evidence_used: false
action_permissions:
  impact_confirmed: DENY
```

# 7. DESIGN

```yaml
stage: DESIGN
progress: COMPLETE
quality: WARNING
outputs:
  functional_design_skeleton: PRESENT
open:
  - transaction_boundary
  - retry_policy
  - authorization
  - interface_contract
```

# 8. PROGRAM

```yaml
stage: PROGRAM
progress: COMPLETE
quality: CRITICAL
confirmed_programs: []
program_candidates: []
action_permissions:
  program_confirmed: DENY
  development_target: DENY
```

# 9. DEVELOPMENT — 현재 Sample Evidence 기준

Source target이 없으므로 B1의 Draft Write 허용조건도 충족하지 못한다.

```yaml
stage: DEVELOPMENT
progress: COMPLETE
quality: CRITICAL
target_write_proof: FAIL
action_permissions:
  draft_source_write: DENY
  source_write: DENY
  merge: DENY
  release: DENY
allowed:
  - patch_plan
  - source_discovery_plan
```

# 10. DEVELOPMENT — Source가 연결된 가상 검증 예

아래는 B1/B3/B6 동작을 보기 위한 계약 예다.

```yaml
target:
  program_id: PGM-ATT-BATCH-001
  resolver_confidence: HIGH
target_write_proof:
  result: PASS
  evidence:
    - canonical_relation
    - current_source_symbol
business_uncertainty:
  severity: CRITICAL
  assumption_id: ASM-ATT-BATCH-01
central_store: AVAILABLE
program_lane:
  key: PROJECT-A:PGM-ATT-BATCH-001
  state: OWNED
work_unit:
  id: WU-ATT-BATCH-001
  state: PREPARED
action_permissions:
  draft_source_write: ALLOW
  merge: DENY
  release: DENY
  verify_pass: DENY
user_badge: "가정 기반 Draft / 병합·배포 불가"
```

코드 변경 후 Crash가 발생했다고 가정한다.

```text
WU PREPARED
→ Source edit
→ WU APPLIED + after_fingerprint 저장
→ Agent crash
```

다른 사용자가 `/work` 재시도:

```yaml
recovery:
  existing_idempotency_key_found: true
  existing_state: APPLIED
  reapply_patch: false
  source_fingerprint_matches: true
  next_action: RESUME_VERIFY
```

# 11. Same PGM Serial Lane

Developer A가 같은 PGM을 수정 중:

```yaml
lane:
  program: PGM-ATT-BATCH-001
  owner: WU-ATT-BATCH-001
  status: OWNED
```

Developer B의 다른 Task가 같은 PGM write를 요청:

```yaml
assignment:
  task: TASK-ATT-BATCH-004
  analysis: ALLOW
  test_preparation: ALLOW
  source_write: DENY
  alert: PGM_LANE_BUSY
```

다른 PGM Task는 병렬 가능하다.

# 12. TEST

```yaml
stage: TEST
progress: COMPLETE
quality: WARNING
candidate_scenarios:
  - 정상 Batch 집계
  - 동일 입력 중복 실행
  - 중간 실패 후 재처리
  - Downstream Consumer 반영
executed_results: 0
action_permissions:
  test_pass: DENY
```

# 13. VERIFY

```yaml
stage: VERIFY
progress: COMPLETE
quality: CRITICAL
validity: CURRENT
action_permissions:
  verify_pass: DENY
reason:
  - no_implementation_result
  - no_executed_test
  - no_ac_coverage
```

UI에서는 내부 `progress=COMPLETE` 대신 `검증 대기`로 보여주는 것이 B2 권장 UX다.

# 14. KNOWLEDGE

```yaml
knowledge_candidate:
  level: K1
  blast_radius: HIGH
  status: CANDIDATE
  human_confirmation_required:
    - authority
    - scope
    - effective_from
    - effective_to
    - exceptions
promotion_permission: DENY
```

# 15. PM / Developer Group

Source가 확인되어 세 Task가 생성됐다고 가정:

```yaml
developer_work_group:
  id: DWG-ATT-BATCH-01
  name: 근무집계 Batch 계산/재처리
  tasks:
    - TASK-ATT-DEV-001
    - TASK-ATT-DEV-002
  lanes:
    PGM-ATT-BATCH-001:
      mode: SERIAL
      tasks: [TASK-ATT-DEV-001, TASK-ATT-DEV-002]
  recommended_owner_continuity: HIGH
```

Consumer 검증은 별도 PGM/VERIFY_ONLY Task라 다른 개발자/테스터가 병렬 수행할 수 있다.

# 16. 사용자가 확인해야 할 핵심 UX

Candidate B에서 같은 Stage에 동시에 다음이 보일 수 있다.

```text
산출물 작성: 완료
품질: 경고
다음 Draft 진행: 가능
코드 초안 작성: 가능 또는 불가
병합: 불가
배포: 불가
최종 검증: 불가
```

이 다층 상태가 안전성을 높이지만 사용자에게 지나치게 복잡한지가 최종 사용성 검증 포인트다.
