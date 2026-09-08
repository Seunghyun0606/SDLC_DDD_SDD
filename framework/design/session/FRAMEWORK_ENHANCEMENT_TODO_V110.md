# Framework Enhancement TODO — Unit Knowledge / AS-IS Canonical Bootstrap / E2E Suite

> 상태: **TODO / 후순위**  
> 범위: **Framework 설계 Backlog 전용**  
> 현재 Runtime 지원 또는 Production Ready로 해석하지 않는다.  
> Project Scaffold에는 배포하지 않는다.

## 0. 목적

현재 v1.10 Harness에서 당장 구현하지 않고 후속 Framework 고도화로 남길 세 영역을 명확히 고정한다.

1. KB 형성과 연계한 Work Unit 누적·고도화
2. AS-IS 시스템 현행 분석을 통한 Canonical Bootstrap
3. Project-wide E2E 통합테스트 Scenario Suite

기존 `framework/design/session/KB_LIFECYCLE_TODO.md`의 Knowledge Lifecycle은 이 Backlog와 연계하지만, 이번 범위에서 상태 전이 Runtime을 구현하지 않는다.

---

## TODO-1. KB 형성 + Work Unit 누적·고도화

### 문제

운영에서는 새로운 RQ가 지속적으로 들어오지만 시스템의 업무/기능 의미는 매번 새 문서로 복제되는 것이 아니라 기존 기능/업무 Unit이 변경·확장되는 경우가 많다.

현재 Canonical은 Entity/Relation/Provenance와 현재 의미를 유지하지만, 장기간 운영 시 다음이 더 명확해야 한다.

- RQ와 지속되는 Work Unit의 Identity 분리
- 동일 Unit에 여러 RQ가 시간순으로 영향을 주는 모델
- Unit의 현재 상태와 과거 상태/변경 이력
- 기존 Canonical/Provenance를 다음 변경에서 어떻게 Retrieval할지
- Projection Profile/Template이 바뀌어도 Unit Knowledge를 지속 참조하는 규칙
- 여러 번 고도화된 Unit을 KB로 Promotion하는 Lifecycle

### 목표 방향

```text
RQ-001 ─┐
RQ-105 ─┼─> Stable Work Unit ─> Current Business/Functional State
RQ-217 ─┘            │
                     ├─ Change/Decision History
                     ├─ Provenance History
                     ├─ AS-BUILT Technical State
                     └─ Knowledge Promotion Candidate
```

### 후속 설계 항목

- Stable Unit ID 생성/재사용 규칙
- RQ → Unit `AFFECTS/CHANGES/EXTENDS` Relation 계약
- Unit Revision 또는 Supersede 모델
- Current vs Historical Semantic State 조회 계약
- Canonical Delta와 Unit History의 관계
- Projection Archive와 Unit History의 경계
- Source/Release/AS-BUILT와 Unit Revision 연결
- Retrieval Priority: Current Canonical → relevant historical decisions/provenance → source evidence → current projection
- KB Candidate 생성 기준과 Unit 성숙도/검증 수준
- `CANDIDATE → REVIEWED → ACCEPTED/PUBLISHED → SUPERSEDED → RETIRED` Lifecycle 구체화
- 오래된/충돌 Knowledge의 재검증 및 폐기 규칙

### 완료 조건 후보

- 동일 Unit에 3개 이상의 순차 RQ를 적용해도 Unit을 중복 복제하지 않는다.
- 특정 Release/시점의 핵심 의미와 변경 이유를 추적할 수 있다.
- Projection Template/Profile 교체 후에도 동일 Unit Knowledge를 재생성할 수 있다.
- 과거 Projection 파일 자체가 Business Truth Retrieval의 필수 전제가 아니다.

---

## TODO-2. AS-IS 시스템 분석 → Canonical Bootstrap

### 문제

Brownfield 프로젝트 시작 시 기존 문서가 불완전하거나 오래된 경우가 많다. Source/DB/Interface/Config를 분석해 현재 시스템의 구조와 업무 맥락 Candidate를 만들 수 있어야 한다.

단, Source Code가 현재 동작을 보여준다고 해서 그것이 곧 승인된 Business Policy라는 뜻은 아니다.

### 목표 방향

```text
Source / DB / Query / Procedure / Interface / Config / Test
                         ↓
               Observed Technical Graph
                         ↓
              Business Context Candidate
                         ↓
      BR/정책문서/담당자 확인 + Conflict Review
                         ↓
                  Canonical Bootstrap
```

### 절대 원칙

- Source 관찰만으로 `CONFIRMED_BUSINESS`를 자동 생성하지 않는다.
- Source 기반 사실은 기본 `OBSERVED`다.
- 업무 의도/정책은 별도 BR Evidence 또는 Human Business Authority 확인이 필요하다.
- `not found`를 `no impact/no rule`로 해석하지 않는다.
- Dynamic dispatch/Procedure/Trigger/Batch/Interface 등 미분석 영역은 Coverage Gap으로 남긴다.

### 후속 설계 항목

- Repository inventory → Entry Point → Call Graph → Data Lineage → Interface/Event → Auth/Transaction → Test Graph Pipeline
- JSP/Java/XML/SQL/Procedure 중심 Brownfield Adapter 표준화
- Framework별 Adapter Contract와 Coverage Metric
- Technical Graph Node/Edge → Canonical Candidate Mapping 규칙
- Actor/Trigger/Precondition/Normal Flow/Exception/Decision/Status/Data/Auth/Outcome 추출 모델
- 기존 BR 문서와 Source 관찰의 Conflict Resolution
- Confidence/Evidence Class와 Human Confirmation Gate
- 재실행 가능한 Bootstrap Snapshot 및 Drift 비교
- 초기 Canonical 생성 이후 일반 `/work`/`/change` Flow로 전환하는 기준

### 완료 조건 후보

- 문서가 거의 없는 Brownfield Sample에서 기술 Graph와 Business Context Candidate를 재현 가능하게 생성한다.
- Source 관찰과 Business Confirmation이 데이터 구조상 분리된다.
- Coverage Gap이 숨겨지지 않는다.
- Human Confirmation 전에는 Business Truth를 확정하지 않는다.

---

## TODO-3. Project-wide E2E 통합테스트 Scenario Suite

### 문제

현재 RQ/AC 중심 Test Scenario는 존재하지만 실제 통합테스트는 여러 RQ와 Work Unit, Program, DB, Interface, Batch를 하나의 업무 시나리오로 통과하는 경우가 많다.

따라서 RQ별 TC의 단순 집합이 아니라 **Business Scenario 기반 E2E Suite**가 필요하다.

### 목표 방향

```text
Business E2E Scenario
   ├─ RQ-012 / Unit-A
   ├─ RQ-031 / Unit-B
   ├─ Program/API/Batch
   ├─ DB State Transition
   ├─ External Interface
   ├─ AC/TC Coverage
   └─ Execution Evidence
```

### 후속 설계 항목

- E2E Scenario ID/Registry
- Scenario와 RQ/Unit/AC/TC Relation 계약
- Actor/Channel/Precondition/Test Data/Step/Expected Business State
- Program/API/Batch/Procedure/DB/Interface Mapping
- 정상/예외/권한/경계값/재처리 Scenario
- Test Data Setup/Cleanup/Rollback
- Environment Dependency와 `NOT_EXECUTED/ENV_BLOCKED/FAILED/PASSED` 상태
- 실행 Evidence/Log/Screenshot/DB Result/Interface Payload Locator
- 변경 영향 기반 Regression Scenario Selection
- 여러 RQ 배포 묶음/Release 단위 E2E Coverage
- 고객 인수 시나리오와 내부 기술 통합테스트의 Projection 분리

### 완료 조건 후보

- 하나의 E2E Scenario가 여러 RQ/Unit을 관계로 연결할 수 있다.
- 변경된 Unit/Program으로부터 영향 E2E Scenario를 역조회할 수 있다.
- 실행하지 않은 Scenario를 PASS로 기록하지 않는다.
- Release별 E2E Coverage와 실패 근거를 재현할 수 있다.

---

## 4. 우선순위

현재 우선순위는 다음과 같이 둔다.

```text
현재 v1.10 사용성/실행 안정화
        ↓
RQ Intake / Reference / PM 운영 UX 안정화
        ↓
TODO-1 Unit Knowledge History
        ↓
TODO-2 AS-IS Canonical Bootstrap
        ↓
TODO-3 E2E Scenario Suite
        ↓
KB Lifecycle 완성/통합
```

단, 실제 Pilot 결과에서 Brownfield Bootstrap 또는 E2E 문제가 더 큰 장애로 확인되면 순서를 재조정할 수 있다.

## 5. 이번 작업에서 하지 않는 것

- Stable Unit History Runtime 구현
- Canonical Event Sourcing 도입
- Source에서 Business Truth 자동 확정
- Project-wide E2E Registry Runtime 구현
- KB Publish/Supersede/Retire Runtime 구현
- 기존 테스트/문서를 근거 없이 `VALIDATED` 또는 `PRODUCTION READY`로 승격

이 문서는 구현 완료 선언이 아니라 후속 설계를 위한 명시적 Framework Backlog다.
