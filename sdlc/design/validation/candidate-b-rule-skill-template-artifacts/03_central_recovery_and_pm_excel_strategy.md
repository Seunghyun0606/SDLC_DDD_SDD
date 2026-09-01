# 03. Central Recovery + Harness PM SoT / Excel Strategy

## 1. 목표

사용자 4~6명이 동시에 Harness를 사용할 때 다음을 만족한다.

- 동일 작업 재실행으로 Source를 중복 수정하지 않는다.
- 다른 사용자가 같은 PGM을 동시에 실제 수정하지 않는다.
- Agent/IDE/Runner Crash 후 작업 상태를 중앙에서 복구한다.
- PM Task/담당자/일정은 Harness가 SoT다.
- PM은 Excel에서도 편집할 수 있다.
- Excel 충돌이 Canonical을 조용히 덮어쓰지 않는다.

# 2. Central Durable Store 최소 모델

PoC/Pilot은 중앙 RDBMS 계열 Durable Store를 권장한다. 제품 선택은 배포환경에 맞추되 다음 Transaction/Constraint를 지원해야 한다.

## work_unit

```text
work_unit_id PK
project_id
branch
rq_id
task_id
program_id
intent_id
idempotency_key UNIQUE
state
base_commit
canonical_base_revision
target_write_proof_id
owner_user_id
owner_runner_id
lease_until
created_at
updated_at
```

## work_unit_event

Append-only transition journal.

```text
event_id PK
work_unit_id
sequence UNIQUE(work_unit_id, sequence)
from_state
to_state
event_type
payload_ref_or_hash
actor
created_at
```

## program_write_lane

```text
project_id
program_id
owner_work_unit_id
owner_user_id
lease_until
revision
PRIMARY KEY(project_id, program_id)
```

## outbox_event

Canonical/Source/Artifact 후속 동기화를 재시도하기 위한 durable outbox.

# 3. Work Unit State

```text
PREPARED
→ APPLIED
→ VERIFIED
→ COMMITTED
```

예외:

- RECOVERY_REQUIRED
- ABORTED

모든 state 변경과 Outbox 등록은 가능한 한 같은 중앙 Transaction에서 처리한다.

# 4. Multi-user Ownership

## Lease

Work Unit/PGM Lane은 영구 Lock 대신 갱신 가능한 Lease를 가진다.

권장 기본값은 Configurable로 두고 Pilot 시작값은 예를 들어:

- lease duration: 120 seconds
- heartbeat: 30 seconds
- grace: 30 seconds

실제 값은 IDE/Agent Runner 특성으로 조정한다.

Lease 만료가 곧바로 재실행 허용을 의미하지 않는다.

```text
Lease expired
→ current source fingerprint 확인
→ current work_unit state 확인
→ takeover/recovery 판단
```

# 5. Idempotency

권장 key 구성:

```text
project_id
+ branch/workspace
+ task_id
+ program_id/target
+ normalized_intent_hash
+ target_source_revision
+ canonical_revision
```

동일 Key가 `COMMITTED`면 재적용하지 않고 기존 결과를 반환한다.

동일 Key가 `APPLIED`면 Source Fingerprint를 확인하고 Verify/Recovery부터 이어간다.

# 6. 중앙 저장소 장애 정책

중앙 Store에 접근할 수 없으면 다음으로 degradation한다.

| 작업 | 정책 |
|---|---|
| 문서 조회/분석 | ALLOW |
| Candidate/Proposal 생성 | ALLOW |
| PM 조회 | Cached read 가능, stale 표시 |
| PM Excel export | Cached revision 명시 시 가능 |
| PM Excel import | DENY/QUEUE, canonical commit 금지 |
| 실제 Source Write | DENY |
| 기존 APPLIED Work 재적용 | DENY |
| Test 실행 | Source mutation 없는 경우 가능 |
| Merge/Release | DENY |

이유: 4~6명 환경에서 Local fallback write를 허용하면 idempotency와 same-PGM serialization을 보장할 수 없다.

# 7. 보안/감사

- Project별 접근 제어
- user/runner/service identity 구분
- Secret/Source 원문을 Journal payload에 저장하지 않고 hash/ref 우선
- Work Unit state/event는 append-only audit 유지
- 운영 DB credential 등은 별도 Secret Store 사용
- 보존기간/삭제정책은 Project Config로 둔다.

# 8. Backup / Recovery

Pilot 최소 전략:

- 중앙 DB automated backup
- point-in-time 또는 일정 주기 snapshot
- work_unit_event/outbox 보존
- Source는 Git commit/fingerprint와 상호 검증
- Canonical snapshot revision과 중앙 Journal revision을 함께 기록

중앙 Journal 자체가 Source Code SoT는 아니다. Git/Canonical과 상호 참조하는 실행 상태 SoT다.

# 9. B5 Harness PM SoT

Canonical Task Model이 SoT다.

```yaml
task:
  task_id: TASK-0042-DEV-002
  revision: 17
  rq_id: RQ-0042
  program_id: PGM-ATT-0016
  group_id: DWG-RQ0042-01
  assignee: DEV-02
  planned_start: 2026-09-07
  planned_end: 2026-09-08
  estimated_effort_hours: 8
  dependency: [TASK-0042-DEV-001]
  status: READY
```

# 10. Excel 병행 관리

Excel은 다음 필드를 편집 가능하게 한다.

- 담당자
- 계획시작/종료
- 예상공수
- 우선순위
- PM 메모
- 필요 시 Status(허용 Transition만)

다음은 Generated/Protected다.

- Task ID
- RQ/FR/PGM relation
- Work Unit state
- PGM Lane owner
- Canonical revision
- Source/Test verification result

## Excel Row Contract

모든 Row에 최소 포함:

- `task_id`
- `revision`
- `export_batch_id`
- `last_synced_revision`

Import는 현재 Canonical revision과 비교한다.

# 11. Excel Conflict Policy

### Canonical만 변경

Excel 변경 없음 → 최신 Canonical로 Refresh.

### Excel만 변경

Allowed editable field이고 base revision 일치 → Canonical Update.

### 서로 다른 Field 변경

Field-level merge 가능.

### 같은 Field 서로 다른 값

```text
PM_SYNC_CONFLICT
```

자동 Last-write-wins 금지.

예:

```yaml
conflict:
  task_id: TASK-0042-DEV-002
  field: planned_end
  base: 2026-09-08
  canonical: 2026-09-09
  excel: 2026-09-10
  action: REQUIRES_DECISION
```

# 12. Excel ↔ Harness Flow

```text
Harness Canonical
→ Revisioned Excel Export
→ User Edit
→ Import Validator
→ Field Diff
→ Conflict Detection
→ Canonical Transaction
→ PM Change Event
→ Excel/MD Regenerate
```

Excel 파일 자체를 Git/Central Canonical SoT로 취급하지 않는다.

# 13. 4~6명 Pilot 운영 전략

권장 역할 예:

- PM/Lead 1~2명: Task/일정/배정 편집
- Developer 3~4명: Work Unit 실행
- 동일 PGM Lane은 한 명만 Active write owner
- 다른 PGM/Verify Task는 병렬

운영 Dashboard 최소 경고:

- `PGM_LANE_BUSY`
- `WORK_UNIT_RECOVERY_REQUIRED`
- `PM_SYNC_CONFLICT`
- `CENTRAL_STORE_UNAVAILABLE`
- `DRAFT_ASSUMPTION_WRITE`
- `MERGE_RELEASE_DENIED`

# 14. Pilot에서 측정할 Metric

- Same PGM lane wait time
- Work Unit retry count
- Duplicate apply prevented count
- Recovery Required count/time
- Excel sync conflicts / import
- PM field overwrite prevented count
- central store unavailable duration
- developer context switching / work group

이 결과를 보고 중앙 Store HA 수준과 Serial Lane 정책을 다음 단계에서 조정한다.
