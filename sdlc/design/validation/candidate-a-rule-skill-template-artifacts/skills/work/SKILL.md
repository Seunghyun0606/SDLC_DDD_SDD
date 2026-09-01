# /work — Candidate A Realization

## Purpose

Legacy Requirement Inventory를 Raw provenance를 유지한 채 RQ/FR Candidate로 정규화하고, 확정되지 않은 Scope를 다음 Stage에 일관된 형식으로 전달한다.

## Required Input

- 현재 Target(Raw/Topic Group/RQ Candidate/RQ/FR/PGM/TASK 중 하나)
- 현재 Canonical revision
- `requirement_scope_snapshot` 또는 Raw provenance

## Optional Input

- 사용자 Boundary Review 답변
- Source/Trace Evidence
- 담당자/일정/공수
- 기존 Knowledge

## Retrieval Strategy

1. Canonical direct relation
2. 최신 `requirement_scope_snapshot`
3. Legacy provenance
4. 관련 질문/답변
5. Process/Source/Trace evidence
6. Historical similarity는 Candidate 제안에만 사용

## Steps

### INTAKE
- Raw Row 보존
- Topic Group 생성
- RQ Boundary 5요소 추출
- 누락은 OPEN
- 1 Row = RQ Publish 금지

### DECOMPOSE
- RQ Boundary Candidate 생성
- FR Candidate 생성
- FR 수가 12 초과이면 `SPLIT_REVIEW_REQUIRED`
- 기술 파일 수만으로 RQ Split 금지

### CLARIFY
Boundary 5요소 중 OPEN인 항목부터 질문한다.

우선순위:
1. Business Goal
2. Observable Outcome
3. Actor/Trigger
4. Policy/State Scope
5. Independent Acceptance/Release

### PROCESS
- Actor/Trigger/State/Exception을 Process Candidate와 연결
- Process가 서로 독립된 Lifecycle을 보이면 `SCOPE_CHANGE_CANDIDATE` 제안

### DISCOVERY / IMPACT
- Source/Trace로 PGM/DATA Candidate 탐색
- 기술 경계와 RQ 경계를 분리 기록
- 기술 경계가 독립 Business Outcome을 증명하지 않으면 RQ Split하지 않음

### DESIGN
- 최신 Boundary revision을 Header에 고정
- Scope 외 요구가 발견되면 설계에 몰래 포함하지 않고 `SCOPE_CHANGE_CANDIDATE`

### PROGRAM
- FR → PGM → TASK로 기술 작업 분해
- RQ를 개발자 배정 단위로 억지 분해하지 않음

### DEVELOPMENT / TEST / VERIFY
- Legacy provenance와 RQ Boundary revision을 유지
- 구현 결과가 Boundary를 변경했다면 VERIFY 전에 Scope Drift를 표시

## Output

각 실행은 최소 다음을 반환한다.

```yaml
work_result:
  target_id: RQC-ATT-001
  stage: CLARIFY
  scope_revision: 3
  artifact:
    type: clarification_questions
    path: docs/02_analysis/RQC-ATT-001/clarification.md
  alerts:
    - SPLIT_REVIEW_REQUIRED
  next_recommended_stage: PROCESS
  publish_permission: DENY
```

## Quality Check

- 모든 Raw Row가 하나 이상의 Candidate에 Trace되는가?
- RQ Boundary 5요소의 Truth 상태가 명시됐는가?
- Split/merge가 발생하면 before/after provenance가 남는가?
- OPEN 값을 Agent가 CONFIRMED로 만들지 않았는가?
- Stage handoff revision이 최신인가?

## Alert Conditions

- `BOUNDARY_INCOMPLETE`
- `SPLIT_REVIEW_REQUIRED`
- `SCOPE_CHANGE_CANDIDATE`
- `SYNC_CONFLICT`
- `LEGACY_TRACE_MISSING`

## Token Strategy

Raw 142행 전체를 매 Stage에 재주입하지 않는다.

```text
Scope Snapshot
→ 관련 Raw Row
→ 필요한 질문/답변
→ 관련 Source Evidence
```

Mega Group은 FR Summary + 선택된 Raw Row만 기본 Context에 넣는다.

## Do Not

- Similarity만으로 다른 RQ를 자동 Merge하지 않는다.
- 대형 Group을 숫자 Threshold만으로 자동 Split하지 않는다.
- Source 파일 경계를 Business Requirement 경계로 대체하지 않는다.
- MD/Excel Timestamp로 Conflict를 덮어쓰지 않는다.
