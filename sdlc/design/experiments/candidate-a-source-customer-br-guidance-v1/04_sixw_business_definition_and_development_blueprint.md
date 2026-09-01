# 04. 6W Business Definition + Development Blueprint Contract

## Quick Start

업무정의서/분석설계서는 기능명이나 BR 목록만으로 끝내지 않는다. 최소한 각 주요 업무 시나리오를 **누가(Who) / 언제(When) / 어디서(Where) / 무엇을(What) / 어떻게(How) / 왜(Why)** 관점으로 설명한다.

```text
6W Business Scenario
→ FR / BR / AC
→ UI / CRUD / Logic / Integration / Query / Data / Code
→ Development Blueprint
→ Development Context Pack(manifest)
→ Source
```

`development-context-pack.yaml`은 상세설계 그 자체가 아니라 **개발 입력을 묶는 Manifest/Index**로 사용한다.

## 1. 왜 6W가 필요한가

기존 RQ/FR/BR만으로는 Agent나 개발자가 다음을 놓치기 쉽다.

- 실제 사용 주체와 필요한 권한
- 업무가 발생하는 시점/주기/선행상태
- 메뉴/화면/배치/API 등 실행 위치
- 입력/조회/저장 대상 데이터
- 정상 처리 순서와 검증/예외
- 업무 목적과 정책 근거

따라서 각 핵심 Scenario는 다음 형식을 만족해야 한다.

| 6W | 필수 내용 |
|---|---|
| Who | 사용자 Role, 권한/Profile, 시스템 Actor |
| When | Trigger, 주기, 시간대, 선행/후행 상태 |
| Where | 채널, 메뉴, 화면, Batch/API/프로세스 위치 |
| What | 입력/조회/변경 대상, 필드, Business Object |
| How | CRUD, Validation, 계산, 상태전이, 예외, 연계 순서 |
| Why | Business Goal, 정책/규정, Pain Point, 기대효과 |

값이 확인되지 않았으면 임의 보완하지 않고 `OPEN`으로 남긴다.

## 2. 사용자 예시의 6W 구조화

```yaml
scenario_id: SCN-FLEX-PLAN-001
who:
  role: 탄력근로제 근무자
  auth_profile: ESS_PROFILE
when:
  frequency: DAILY
  trigger: 매일 근무계획 입력 시
where:
  channel: ESS
  menu: 탄력근로제 근무계획
what:
  business_object: 근무계획
  fields: [근무일자, 시작시간, 종료시간]
how:
  action: 저장
  sequence:
    - 날짜 선택
    - 시작/종료시간 입력
    - 유효성 검증
    - 근무계획 저장
why:
  purpose: 근무자는 매일 예정 근무시간을 등록해야 한다
```

이 Scenario에서 화면 Field/Validation/Data/Code/CRUD가 후속 설계로 내려가야 한다.

## 3. Development Blueprint

Source-ready 설계는 다음 12개 영역을 명시한다.

1. `business_scenarios_6w`
2. `screen_or_channel_spec`
3. `field_spec`
4. `crud_matrix`
5. `core_business_logic`
6. `state_and_validation`
7. `integration_contract`
8. `query_and_data_contract`
9. `common_code_contract`
10. `transaction_security_error`
11. `source_mapping`
12. `test_mapping`

### 3.1 화면/채널

화면이 변경되지 않더라도 `NO_UI_CHANGE`를 명시한다. 화면이 있으면 최소 다음을 적는다.

- 메뉴/화면 ID와 이름
- 진입 권한
- 조회조건
- Grid/Form 구조
- 버튼/Action
- 표시/입력/필수/Read-only 조건
- 상태별 Enable/Disable
- 메시지/Validation

### 3.2 Field Spec

| Field | 의미 | Type | 필수 | Source/Code | Validation | UI |
|---|---|---|---|---|---|---|
| workDate | 근무일 | DATE | Y | 업무일자 | 미래/마감상태 검증 | 입력 |

필드가 DB Column과 1:1이 아니면 Mapping Rule을 적는다.

### 3.3 CRUD Matrix

각 업무행위가 무엇을 읽고/생성/수정/삭제하는지 명시한다.

```text
Scenario / Action
→ Screen/API
→ Service Method
→ Mapper Statement
→ Table/View/Procedure
→ CRUD
```

### 3.4 핵심 Business Logic

자연어와 결정표를 같이 사용한다.

```text
IF 월마감 아님
  THEN 10분 단위 계획 반영
ELSE IF FORCE_CLOSE
  THEN reject
ELSE IF 승인 수정요청 있음
  THEN 재집계
ELSE reject
```

### 3.5 Integration

연계가 없으면 `NONE_CONFIRMED` 또는 `NONE_ASSUMED`를 구분한다. 연계가 있으면:

- Caller/Consumer
- Protocol/Transport
- Request/Response/Payload
- Auth
- Timeout/Retry/Duplicate
- Sync/Async
- Failure/Compensation

을 적는다.

### 3.6 Query/Data

Query는 "어떤 테이블을 본다"를 넘어서 다음을 포함한다.

- Query 목적
- 입력 Parameter
- Join/Filter 핵심조건
- Key/Uniqueness
- Read/Write Table/Column
- Null/Default
- Lock/Concurrency
- 예상 Cardinality/성능 제약
- Index/Hint가 확인되지 않았으면 OPEN

### 3.7 Common Code

공통코드를 문자열 상수로 임의 생성하지 않는다.

```yaml
common_code:
  group: ATT_CLOSE_TYPE
  values:
    - code: FORCE_CLOSE
      meaning: 강제마감
  authority: CODE_MASTER
  evidence: OPEN | OBSERVED | CONFIRMED
```

## 4. Context Pack 역할 변경

기존 `development-context-pack.yaml`은 다음 파일들의 최신 revision을 참조한다.

```yaml
artifacts:
  business_definition: docs/.../business-definition.md#r3
  functional_design: docs/.../functional-design.md#r3
  development_blueprint: docs/.../development-blueprint.md#r3
  pgm_spec: docs/.../PGM-xxx.md#r3
  test_spec: docs/.../test-scenarios.md#r3
```

즉 Agent가 YAML 한 장만 보고 구현하지 않는다.

## 5. Source-ready Gate

다음이 `OPEN`이면 해당 영역 Source 생성은 제한한다.

- Who 권한/Profile
- 화면 Field/Action
- CRUD 대상
- 핵심 Rule/Exception
- 연계 대상/계약
- Query 대상/Key
- Common Code Authority
- Transaction Boundary
- AC/Test

단, 관련 없는 다른 영역의 분석/설계는 계속할 수 있다.

## 6. Change Routing

6W 중 어떤 항목이 바뀌었는지에 따라 STALE 범위를 계산한다.

- Who 변경 → 권한/UI/BR/Test 재검토
- When 변경 → Scheduler/State/기간 Rule/Test 재검토
- Where 변경 → UI/API/Batch/Integration/PGM 재검토
- What 변경 → Field/Data/CRUD/Query/Test 재검토
- How 변경 → BR/Process/Logic/Transaction/PGM/Test 재검토
- Why 변경 → RQ Scope/Goal 자체 재검토

`Why`가 변경되면 가장 높은 수준의 Scope 변경으로 취급한다.
