# 02. Developer Work Group / Assignment Guide

## Purpose

B3 `Same PGM Serial Ownership`을 실제 Task 배분에 적용하면서도 4~6명의 개발자가 유사한 작업을 묶어서 이해하고 병렬 수행할 수 있게 한다.

## 1. 두 개념을 분리한다

### Developer Work Group
PM/사용자/Agent가 유사한 Task를 한 묶음으로 보여주고 배정하기 위한 계획 단위다.

### PGM Write Lane
동일 Logical Program의 actual source mutation을 직렬화하는 실행 단위다.

```text
Developer Work Group = 이해/배분 최적화
PGM Write Lane        = 동시 수정 안전성
```

하나의 Work Group 안에 여러 PGM Lane이 있을 수 있다.

# 2. Grouping 우선순위

Agent는 아래 순서로 유사도를 판단한다.

1. 동일 Business Change Outcome / 같은 RQ 또는 밀접한 FR
2. 동일 Logical Program(PGM)
3. 동일 Transaction / State transition / Interface 흐름
4. 동일 Artifact cluster(Java + Mapper + Procedure 등)
5. 동일 Data ownership / Table family
6. 동일 Test/Release dependency
7. 동일 기술 Skill/Standard

단순 파일 확장자 또는 같은 개발자라는 이유만으로 묶지 않는다.

# 3. Group Split Rules

다음이면 별도 Work Group을 우선 제안한다.

- 서로 독립 배포 가능한 변경
- 서로 다른 PGM owner/domain
- 서로 다른 Transaction boundary
- 신규 API/Batch/Interface와 일반 UI 수정이 혼재
- 서로 다른 위험등급/보안경계
- 한 그룹이 너무 커서 Developer가 전체 Context를 유지하기 어려움

# 4. Same PGM Serial Ownership

Actual source mutation 기준 lock key:

```text
project_id + program_id
```

예:

```text
PGM-ATT-0016 lane
  TASK-DEV-001 → ACTIVE
  TASK-DEV-004 → WAITING

PGM-LEV-0012 lane
  TASK-DEV-002 → ACTIVE
```

`PGM-ATT-0016`과 `PGM-LEV-0012`는 서로 다른 개발자가 병렬 수행할 수 있다.

# 5. Agent Assignment Proposal Format

```yaml
developer_work_group:
  group_id: DWG-RQ0042-01
  name: 휴가취소-근태재계산
  reason:
    - same_business_outcome
    - shared_transaction_flow
  tasks:
    - TASK-0042-DEV-001
    - TASK-0042-DEV-002
  program_lanes:
    PGM-LEV-0012:
      tasks: [TASK-0042-DEV-001]
      write_mode: SERIAL
    PGM-ATT-0016:
      tasks: [TASK-0042-DEV-002]
      write_mode: SERIAL
  recommended_assignment:
    min_developers: 1
    max_parallel_developers: 2
  context_pack_shared:
    - RQ-0042
    - BR-LEV-0007
    - BR-ATT-0013
  context_pack_per_lane:
    PGM-LEV-0012:
      - PGM spec
      - related artifacts
    PGM-ATT-0016:
      - PGM spec
      - related artifacts
```

# 6. 배분 가이드

## 1명에게 같이 주기 좋은 경우

- 동일 PGM에 여러 연속 Task
- 같은 Transaction을 반복적으로 건드림
- Source Context 공유율이 높음
- Task별 예상공수가 작고 순차 의존성이 높음

## 여러 명에게 나누기 좋은 경우

- 서로 다른 PGM Lane
- 독립 Test 가능
- Context Pack 겹침이 작음
- 선행관계 없음
- Interface contract가 명확함

# 7. User View

PM 화면/Excel에는 다음 컬럼을 제공한다.

- 작업그룹 ID
- 작업그룹명
- RQ
- PGM
- Task
- 변경유형
- 담당자
- PGM Lane 상태
- 선행 Task
- 병렬가능 여부
- 추천배정 이유

# 8. Agent Rules

- Agent는 동일 PGM Source Write를 두 Developer에게 동시에 `READY_TO_WRITE`로 배정하지 않는다.
- 분석/설계/테스트 준비 Task는 같은 PGM이어도 병렬 수행 가능하다.
- Hotfix가 기존 Lane을 선점해야 하면 자동 탈취하지 않고 `LANE_PREEMPTION_REQUIRED`를 만든다.
- 기존 ACTIVE Work Unit의 사용자/Runner/Branch를 확인한 뒤 새 Write Lane을 발급한다.
- Work Group은 배분 보조정보이며 Canonical RQ/FR/PGM 관계를 변경하지 않는다.

# 9. Sample Requirements 적용 예

`REQ_TM_TE077~099` 근무집계 Batch 반영의 Source가 발견됐다고 가정할 때:

```text
DWG-ATT-BATCH-01 근무집계 계산 변경
  ├─ PGM-ATT-BATCH-001 lane
  │    ├─ 계산식 변경 Task
  │    └─ 재처리 로직 Task
  └─ PGM-ATT-SUMMARY-002 lane
       └─ 집계 저장 Task

DWG-ATT-BATCH-02 외부/후속 Consumer 검증
  └─ VERIFY_ONLY tasks
```

같은 PGM의 두 수정 Task는 직렬이지만 Consumer 검증은 다른 담당자가 병렬 진행할 수 있다.
