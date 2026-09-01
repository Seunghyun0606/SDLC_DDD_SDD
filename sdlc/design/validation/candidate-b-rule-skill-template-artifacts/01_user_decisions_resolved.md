# 01. User Decisions Resolved — Candidate B

> 본 문서는 원 Candidate B의 `04_decision_required.md`를 삭제/변경하지 않고, 검증 Branch에서 사용자의 선택을 적용한 실행 프로파일이다.

| Decision | User Choice | Validation Profile |
|---|---|---|
| B1 | Option B | Draft Source Write 허용, Merge/Release DENY until uncertainty resolved |
| B2 | Option A | progress와 action permission 분리 |
| B3 | Option A | 동일 PGM 실제 Source Write Serial Ownership |
| B4 | Option B | High-blast K1 Human scope/temporal confirmation |
| B5 | Option A + Excel | Harness PM SoT + editable Excel projection |
| B6 | Option B | Central Durable Recovery Store for 4~6 users |

# B1 — Draft Source Write Contract

CRITICAL business uncertainty가 있어도 다음은 허용 가능하다.

```text
Analysis / Design / Test Candidate
+ Short-lived Branch Draft Source Write
```

단 아래 조건을 모두 만족해야 실제 Draft Write가 가능하다.

- `target_write_proof = PASS`
- Work Unit 생성 및 중앙 Journal 등록 성공
- `assumption_lineage` 존재
- protected/main branch가 아님
- `merge_permission = DENY`
- `release_permission = DENY`
- 사용자 View에 `가정 기반 Draft` 표시

# B2 — Progress vs Permission

```yaml
progress: COMPLETE
action_permissions:
  source_write: ALLOW
  merge: DENY
  release: DENY
  verify_pass: DENY
```

`COMPLETE`는 문서/Stage 작업 작성 완료만 의미한다. UI의 최종 `완료`는 Verify-grade 상태에만 사용한다.

# B3 — Same PGM Serial Ownership

동일 `project_id + program_id`에 실제 Source Write를 수행하는 Work Unit은 동시에 하나만 ACTIVE ownership을 가진다.

분석/Review/Test 설계는 병렬 가능하지만 actual mutating write는 직렬화한다.

추가 요구: 사용자/Agent가 Task를 Developer에게 배분할 때 유사한 작업을 묶을 수 있도록 `Developer Work Group`을 생성한다. 세부 기준은 `02_task_grouping_and_assignment_guide.md`에 정의한다.

# B4 — K1 Promotion

High-blast Business Knowledge는 Agent가 K1 Candidate까지만 생성한다.

Human confirmation required:

- authority
- scope
- effective_from / effective_to
- exceptions
- affected domain/company/country/role

# B5 — Harness PM SoT + Excel

Canonical Harness가 다음의 최종 SoT다.

- TASK identity
- Parent/RQ/FR/PGM relation
- Assignment
- Schedule
- Effort
- Dependency
- Status

Excel은 PM 편의용 editable projection이다.

```text
Harness Canonical Task Revision
→ Excel Export
→ PM Edit
→ Import Diff
→ Conflict Check
→ Canonical Commit
→ Excel/MD Regenerate
```

Excel이 직접 SoT가 되지 않는다.

# B6 — Central Durable Recovery

4~6명 사용자를 전제로 Local JSONL/SQLite 단독 운영은 채택하지 않는다.

최소 중앙 기능:

- durable work unit journal
- idempotency unique key
- current state + append-only transition history
- runner/user lease
- program write ownership lock
- optimistic revision
- transactional outbox
- audit identity/time

중앙 저장소가 unavailable일 때:

- Read/Analysis/Draft Document: 가능
- 실제 Source mutation: 기본 DENY
- 이미 APPLIED 상태의 Work Unit: 복구 확인 없이는 재적용 금지

# Remaining validation, not user decision yet

다음은 이번 선택을 구현 가능한 수준으로 검증해야 한다.

- Lease TTL/heartbeat 운영 적합성
- Central Store HA/backup 요구수준
- Excel 동시편집 Conflict 빈도
- 동일 PGM serial lane 병목
- Draft Write가 사용자에게 완료로 오인되지 않는 UI
