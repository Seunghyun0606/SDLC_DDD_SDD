# 04. 6W Business Definition + Development Evidence Blueprint

## Quick Start

Candidate B에서도 업무정의/분석설계는 각 핵심 Scenario를 **Who / When / Where / What / How / Why**로 설명해야 한다.

다만 6W 값마다 `truth / evidence / revision`을 유지한다.

```text
6W Business Scenario + Evidence
→ FR / BR / AC
→ UI / CRUD / Logic / Integration / Query / Data / Code
→ Development Blueprint
→ Current Source Evidence
→ Target Write Proof
→ Work Unit / PGM Lane
→ Draft Source Write
```

`development-evidence-pack.yaml`은 상세명세 자체가 아니라 최신 상세설계와 Evidence를 조립하는 Manifest다.

## 1. 6W Evidence Contract

각 6W는 다음 최소형을 가진다.

```yaml
who:
  value: "ESS Profile을 가진 탄력근로제 근무자"
  truth: GIVEN|OBSERVED|INFERRED|CONFIRMED|OPEN
  evidence: [source#locator]
  revision: 3
```

- Who: Role/Profile/System Actor
- When: Trigger/Frequency/Time Window/State
- Where: Channel/System/Menu/Screen/Batch/API
- What: Business Object/Input/Output/Field
- How: CRUD/Sequence/Validation/State/Exception/Integration
- Why: Business Goal/Policy/Pain Point

`OPEN`은 `progress=COMPLETE`를 막지 않을 수 있지만 해당 영역 `action_permission`을 제한할 수 있다.

## 2. Development Blueprint 필수 영역

1. 6W Scenario
2. Screen/Channel
3. Field Spec
4. CRUD Matrix
5. Core Business Logic
6. State/Validation/Error
7. Integration Contract
8. Query/Data Contract
9. Common Code
10. Transaction/Auth/Audit
11. Current Source Mapping
12. Test Mapping
13. Blind Spots/Open Evidence

## 3. UI/CRUD/Query는 없더라도 명시

- UI 변경 없음: `NO_UI_CHANGE_CONFIRMED` 또는 `NO_UI_CHANGE_ASSUMED`
- 외부 연계 없음: `NONE_CONFIRMED` 또는 `NONE_ASSUMED`
- Delete 없음: `DELETE_NONE_CONFIRMED`

`ASSUMED`는 Source Write Permission 계산에서 약한 Evidence다.

## 4. Common Code Guard

문자열 상수는 Code Master Evidence 없이 확정하지 않는다.

```yaml
code_candidate:
  group: ATT_CLOSE_TYPE
  code: FORCE_CLOSE
  truth: OBSERVED
  authority: SOURCE_LITERAL_ONLY
  canonical_code_master_verified: false
```

실제 write에서 공통코드 신규/변경이 필요하면 별도 Program/Data Impact를 생성한다.

## 5. Query/Data Evidence

Query별로 최소 다음을 기록한다.

- 목적
- parameter
- table/view/procedure
- key/join/filter
- null/default
- lock/concurrency
- expected cardinality/performance
- index/hint evidence
- source statement/path/hash

정적 Source에서 확인되지 않은 Lock/Runtime은 `blind_spot`으로 남긴다.

## 6. Permission 계산

예:

```yaml
coverage:
  six_w: PARTIAL
  ui: ASSUMED_NO_CHANGE
  crud: CONFIRMED_FROM_SOURCE
  business_logic: CONFIRMED_DESIGN
  integration: OPEN_UPSTREAM_APPROVAL
  data: OBSERVED_SOURCE
  common_code: OPEN
permissions:
  proposal: ALLOW
  draft_source_write: CANDIDATE_ONLY
  merge: DENY
  release: DENY
```

## 7. Customer Projection

고객 문서에는 6W를 그대로 보여주되 내부 Evidence Hash나 Target Proof는 숨긴다.

고객이 확인해야 하는 것은:
- 누가 하는가
- 언제 하는가
- 어디서 하는가
- 무엇을 처리하는가
- 어떤 규칙/예외로 처리하는가
- 왜 필요한가

이며, 각 항목의 합의상태만 고객 친화적으로 표시한다.

## 8. 6W Change Routing

- Who → Auth/UI/Test + Target Proof 재검토
- When → State/Scheduler/Batch/Query/Test
- Where → UI/API/Batch/Integration/PGM
- What → Field/Data/CRUD/Query
- How → BR/Process/Logic/Transaction/PGM/Test
- Why → RQ Scope/Goal + downstream 전체

변경된 영역의 `evidence_revision`을 올리고 영향받는 Action Permission을 재계산한다.
