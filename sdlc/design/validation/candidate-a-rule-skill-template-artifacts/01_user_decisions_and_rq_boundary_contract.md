# 01. User Decisions + RQ Boundary / Grouping Contract

## 1. 확정된 사용자 결정

| Decision | 선택 | 적용 |
|---|---|---|
| A1 | 2 | Raw Row를 바로 RQ로 Publish하지 않는다. |
| A2 | 2 | 22개 Group은 RQ Candidate로만 생성한다. |
| A3 | 3 | Mega Group은 Human Split Review를 요구한다. |
| A4 | 2 | `legacy_source_id`와 Canonical UID/Display ID를 분리한다. |
| A5 | 2 | MD/Excel 모두 편집 가능하되 Canonical을 통해 동기화한다. |
| A6 | 2 | Same-field divergent edit는 `SYNC_CONFLICT`다. |
| A7 | 보류 | 사용성 검증 후 Candidate A 채택 여부를 결정한다. |

# 2. RQ Scope 사전 정의 제안

## 2.1 RQ 정의

> 하나의 RQ는 **하나의 설명 가능한 Business Change Outcome**을 가지며, 업무 담당자가 Acceptance 기준으로 독립적으로 확인할 수 있는 변경 단위다.

RQ를 다음으로 정의하지 않는다.

- Excel 한 행
- 화면 하나
- Java 파일 하나
- Procedure 하나
- 개발자 한 명에게 배정하기 좋은 크기

이들은 FR/PGM/TASK 경계가 될 수 있지만 RQ 경계와 동일하지 않다.

## 2.2 RQ Boundary 5요소

모든 RQ Candidate는 아래 5개를 채운다.

1. `business_goal`: 왜 바꾸는가
2. `actor_trigger`: 누가/무엇이 시작하는가
3. `observable_outcome`: 사용자가 확인할 결과
4. `policy_state_scope`: 같은 정책/상태 범위인가
5. `acceptance_release_scope`: 독립적으로 검증/배포 판단할 필요가 있는가

## 2.3 Split Signal

다음 중 하나가 강하게 성립하면 RQ Split Candidate를 만든다.

- 서로 다른 Business Goal
- 서로 독립적인 Actor/Trigger
- 서로 독립적으로 성공/실패 판정할 수 있는 Outcome
- 정책 적용범위/유효기간/권한 주체가 다름
- 하나가 취소/연기돼도 다른 하나를 독립적으로 Release해야 함
- 서로 다른 업무 Lifecycle/State Machine을 가짐

다음은 **단독으로는 RQ Split 사유가 아니다.**

- Program이 여러 개임
- Table이 여러 개임
- API/Batch가 포함됨
- Java와 PL/SQL이 함께 수정됨
- 개발 담당자가 다름

이 기술 경계는 우선 `FR → PGM → TASK`에서 분해한다.

# 3. Grouping Granularity 제안

## 3.1 4단계 Grouping

```text
L0 Raw Item
→ L1 Topic Group
→ L2 RQ Boundary Candidate
→ L3 FR Candidate
```

### L0 Raw Item
원본 행. 내용과 Legacy ID를 수정하지 않고 보존한다.

### L1 Topic Group
검색/검토 편의를 위한 묶음. Sample 기본 Key:

```text
업무 대분류 + 업무 중분류 + 요구사항명
```

L1은 RQ가 아니다.

### L2 RQ Boundary Candidate
L1 안에서 RQ Boundary 5요소를 기준으로 실제 RQ 후보를 만든다.

### L3 FR Candidate
RQ Outcome을 구성하는 테스트 가능한 행동으로 세분화한다.

# 4. Mega Group 처리

`FR Candidate > 12`는 자동 Split 기준이 아니라 `SPLIT_REVIEW_REQUIRED` Trigger다.

Agent는 다음 순서로 Split Proposal만 만든다.

1. Business Goal 차이 탐색
2. Actor/Trigger 차이 탐색
3. Outcome 차이 탐색
4. State/Lifecycle 차이 탐색
5. Policy Scope 차이 탐색
6. Independent Acceptance/Release 차이 탐색
7. 마지막에 Technical Boundary를 보조 Evidence로 제시

Agent는 제안마다 원본 Legacy ID 범위를 유지해야 한다.

# 5. Sample 적용

`REQ_TM_TE016~054` 39건은 현재 Evidence만으로 자동 RQ Split하지 않는다.

```yaml
topic_group:
  id: TG-ATT-CLOSE-10MIN
  legacy_ids: REQ_TM_TE016..REQ_TM_TE054
  item_count: 39
  status: SPLIT_REVIEW_REQUIRED
rq_boundary_status: OPEN
reason:
  - 동일 요구사항명만 확인됨
  - 독립 Business Goal 여부 미확인
  - Actor/Trigger/Outcome/State 범위 미확인
agent_action:
  - split_questions 생성
  - split_candidates 제안 가능
  - publish 금지
```

# 6. Stage 간 Agent 전달 포맷

각 Stage는 원문 전체를 재해석하지 않고 `requirement_scope_snapshot`을 전달한다.

```yaml
requirement_scope_snapshot:
  candidate_id: RQC-ATT-001
  revision: 3
  business_goal:
    value: "10분 단위 근무계획을 근태마감에 반영"
    truth: INFERRED
  actor_trigger:
    value: null
    truth: OPEN
  observable_outcome:
    value: "마감 결과에 10분 단위 계획 반영"
    truth: INFERRED
  policy_state_scope:
    value: null
    truth: OPEN
  acceptance_release_scope:
    independent_release: null
    truth: OPEN
  source_legacy_ids:
    - REQ_TM_TE016
    - REQ_TM_TE017
  split_review:
    required: true
    reasons:
      - "39 FR candidates"
      - "state/policy boundary not confirmed"
```

# 7. 단계별 사용 규칙

| Stage | Scope Snapshot 사용 방식 |
|---|---|
| INTAKE | Raw/Topic Group 생성, Boundary 5요소 결측 표시 |
| DECOMPOSE | RQ/FR Candidate 작성, 자동 Publish 금지 |
| CLARIFY | 결측 Boundary 요소를 질문으로 변환 |
| PROCESS | Actor/Trigger/State를 Process와 대조 |
| DISCOVERY | 기술 Evidence가 RQ 경계를 바꾸는지 아닌지 분리 기록 |
| IMPACT | PGM/Data 경계는 RQ Split의 보조 Evidence로만 사용 |
| DESIGN | 확정된 RQ Boundary 안에서 목표 동작 정의 |
| PROGRAM | FR별 PGM/TASK 분해 |
| DEVELOPMENT | RQ Scope Snapshot 변경 금지; 변경 필요 시 `SCOPE_CHANGE_CANDIDATE` |
| TEST | RQ Outcome + FR AC 기준 Coverage |
| VERIFY | 최초 Boundary와 실제 구현 결과의 일치 확인 |

# 8. Scope Change Contract

후속 Stage에서 RQ가 너무 크거나 서로 다른 업무목표임이 발견되면 조용히 재분류하지 않는다.

```text
DISCOVERY/DESIGN finding
→ SCOPE_CHANGE_CANDIDATE
→ affected Raw/FR 목록
→ before/after Boundary Card
→ Human Review
→ RQ split/merge revision
→ downstream STALE propagation
```

이 방식으로 초기 Grouping 오류가 Source 분석 단계에서 발견되어도 Trace를 잃지 않는다.
