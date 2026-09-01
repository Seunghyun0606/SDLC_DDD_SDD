# /work — Candidate B Realization

## Purpose

각 Stage에서 산출물 작성상태와 실제 실행가능 권한을 분리하고, 위험한 코드변경은 Target Proof + Work Unit + 중앙 Recovery 계약을 통해 수행한다.

## Required Input

- Target(RQ/FR/PGM/TASK)
- current stage
- canonical revision
- stage evidence envelope
- current action permissions

코드 변경 단계 추가 필수:

- target write proof
- central recovery store reachable
- program write lane acquisition result

## Optional Input

- Assumption/Alert
- Source/Trace/Runtime evidence
- 담당자/일정/공수
- Excel PM import diff

## Common Steps

1. Target resolve
2. Evidence revision 확인
3. Required/Optional input 평가
4. Stage 산출물 생성/갱신
5. `progress`, `quality`, `validity` 계산
6. 각 action별 permission 계산
7. 다음 안전한 작업 제안

## Stage behavior

### INTAKE / DECOMPOSE / CLARIFY / PROCESS

- 정보 부족이어도 Draft/Candidate 계속 생성
- 업무 불확실성은 Alert/Assumption으로 유지
- Business truth 자동 확정 금지

### DISCOVERY / IMPACT

반드시 기록:

- coverage_basis
- coverage_scope
- blind_spots
- runtime_evidence_used
- unresolved_dynamic_edges

`HIGH confidence`는 `complete coverage`가 아니다.

### DESIGN / PROGRAM

- Transaction/Auth/Security/Interface gap 표시
- PGM Candidate와 Confirmed Program 분리

### DEVELOPMENT

순서:

```text
Target Resolve
→ Target Write Proof
→ Central Work Unit PREPARED
→ PGM Write Lane Acquire
→ Draft/Normal Write
→ APPLIED fingerprint
→ Test/Verification
→ VERIFIED
→ Canonical/Artifact sync
→ COMMITTED
→ Lane Release
```

중요 업무 가정이 남아 있어도 B1에 따라 Draft Branch Write 가능.

단:

```yaml
merge: DENY
release: DENY
verify_pass: DENY_or_REQUIRES_EVIDENCE
```

### TEST / VERIFY

- Test Scenario 작성과 실제 Test PASS를 분리
- 실행결과가 없으면 PASS 금지
- Verify는 AC coverage, implementation result, environment/provenance, critical gap을 확인

### KNOWLEDGE

High-blast K1:

```text
Candidate Extract
→ Evidence Check
→ Human Scope/Temporal Confirmation
→ K1 Promotion
```

## Task Assignment behavior

Task 생성 후 Agent는 `Developer Work Group`을 제안한다.

- 같은 RQ/Outcome
- 같은 PGM
- 같은 Transaction/State/Interface
- Artifact/Data/Test dependency

동일 PGM의 actual write Task는 같은 PGM Lane에 넣고 동시에 하나만 `READY_TO_WRITE`다.

## PM / Excel behavior

`/work` 중 Task/Assignment/Schedule 변경이 발생하면 Harness Canonical revision을 먼저 갱신한다.

Excel import 요청은:

```text
Stable Task ID
→ Base Revision
→ Field Diff
→ Conflict Check
→ Canonical Commit
→ View Regenerate
```

## Output

```yaml
work_result:
  target: TASK-0042-DEV-002
  stage: DEVELOPMENT
  progress: COMPLETE
  quality: WARNING
  validity: CURRENT
  evidence_revision:
    canonical: 17
    source: abc123
  action_permissions:
    draft_source_write: ALLOW
    merge: DENY
    release: DENY
    verify_pass: DENY
  work_unit:
    id: WU-0042-002-17
    state: APPLIED
  program_lane:
    program_id: PGM-ATT-0016
    state: OWNED
  alerts:
    - DRAFT_ASSUMPTION_WRITE
```

## Quality Check

- progress만 보고 실행한 Action이 없는가?
- Target Proof와 Resolver confidence를 혼동하지 않았는가?
- Same PGM lane 중복 owner가 없는가?
- APPLIED 작업을 중복 적용하지 않았는가?
- Excel import가 canonical revision을 검증했는가?
- K1 high-blast가 Human 확인 없이 승격되지 않았는가?

## Alert Conditions

- TARGET_PROOF_FAILED
- PGM_LANE_BUSY
- WORK_UNIT_RECOVERY_REQUIRED
- CENTRAL_STORE_UNAVAILABLE
- DRAFT_ASSUMPTION_WRITE
- MERGE_RELEASE_DENIED
- PM_SYNC_CONFLICT
- KNOWLEDGE_SCOPE_CONFIRM_REQUIRED

## Do Not

- `COMPLETE`를 Release Ready로 해석하지 않는다.
- Lease 만료만 보고 같은 Patch를 다시 적용하지 않는다.
- Resolver HIGH만으로 코드변경하지 않는다.
- 동일 PGM을 두 Runner가 동시에 변경하지 않는다.
- Excel을 Canonical Task SoT로 취급하지 않는다.
