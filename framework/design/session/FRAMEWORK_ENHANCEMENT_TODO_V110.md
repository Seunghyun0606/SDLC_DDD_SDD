# Framework Enhancement TODO — Unit Knowledge / AS-IS Canonical Bootstrap / E2E Suite / Multi-writer RQ / Late Reference Ingest

> 상태: **TODO / 후순위**  
> 범위: **Framework 설계 Backlog 전용**  
> 현재 Runtime 지원 또는 Production Ready로 해석하지 않는다.  
> Project Scaffold에는 배포하지 않는다.

## 0. 목적

현재 v1.10 Harness에서 당장 구현하지 않고 후속 Framework 고도화로 남길 다섯 영역을 명확히 고정한다.

1. KB 형성과 연계한 Work Unit 누적·고도화
2. AS-IS 시스템 현행 분석을 통한 Canonical Bootstrap
3. Project-wide E2E 통합테스트 Scenario Suite
4. 여러 사용자/Agent가 동시에 RQ를 생성할 수 있는 RQ ID/Sequence Allocation
5. 프로젝트 진행 중 늦게 들어온 인터뷰/회의록/업무자료를 기존 RQ에 간단히 등록·연결하는 Late Reference Ingest UX

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

## TODO-4. Multi-writer RQ ID / Sequence Allocation

### 현재 문제

현재 `rq-add`와 기존 Requirement Intake의 `RQ-NNN` 생성 방식은 Canonical 현재 파일에서 가장 큰 RQ 번호를 확인하고 다음 번호를 선택한다.

```text
현재: RQ-001, RQ-002, RQ-003
→ 다음 후보: RQ-004
```

Canonical write 자체는 파일 Lock + Revision Guard + Atomic Replace로 보호하지만 **번호 선택 자체를 여러 작성자가 동시에 예약하는 중앙 Sequence Service는 없다.**

따라서 현재 운영은 RQ 생성 담당자 한 명을 전제로 한다. 동시 생성 충돌 시 자동 번호 재선점/재시도를 하지 않고 앞 작업 완료 후 다시 실행한다.

### 목표 방향

향후 여러 사람/Agent가 동시에 RQ를 생성해도 중복 ID, Lost Update, 사용자가 이미 본 ID의 조용한 변경이 발생하지 않는 구조가 필요하다.

```text
User/Agent A ─┐
User/Agent B ─┼─> RQ Allocation Boundary ─> Unique RQ ID ─> Canonical Apply
User/Agent C ─┘
```

### 후속 설계 항목

- RQ ID 할당을 Canonical current-file max scan과 분리할지 여부
- File lock 안에서 `read → allocate → apply`를 하나의 원자 경계로 묶는 방식
- 별도 Sequence Registry / Reservation / Lease 도입 여부
- Optimistic Compare-And-Swap 기반 ID allocation
- 생성 요청의 Idempotency Token
- 충돌 시 사용자에게 보여준 ID를 바꾸는 정책과 금지 조건
- Reservation 후 실패/취소 시 번호 Gap 허용 여부
- Branch/Worktree/분산 실행 환경에서의 ID 범위
- Offline 생성과 중앙 저장소 동기화 정책
- Audit: 누가 언제 어떤 요청으로 ID를 할당받았는지
- 동일 자연어 요청의 중복 생성 방지와 실제 별도 RQ 승인 경계

### 완료 조건 후보

- 동시에 N개의 RQ 생성 요청을 실행해도 중복 RQ ID가 없다.
- Canonical Entity가 Lost Update되지 않는다.
- 충돌/재시도 동작이 결정적이며 조용히 다른 RQ를 덮어쓰지 않는다.
- 사용자에게 성공으로 반환한 RQ ID가 뒤에서 자동 변경되지 않는다.
- 동일 요청 재전송은 Idempotency 정책에 따라 중복 생성되지 않는다.
- 기존 단일작성자 Project도 추가 운영 부담 없이 동일 Runtime을 사용할 수 있다.

---

## TODO-5. Late Reference Ingest / 기존 RQ 참고자료 추가 UX

### 현재 문제

프로젝트 진행 중 고객 인터뷰, 회의록, 정책 설명, 화면 캡처 설명, 운영 담당자 메모 등 요구사항 이해에 필요한 자료가 뒤늦게 들어올 수 있다.

현재 Runtime은 `intake_reference_draft.py`를 통해 기존 RQ와 새 참고문서를 받아 다음 작업을 수행할 수 있다.

- `br-input/manifest.yaml` 문서 등록
- 지원 형식 Evidence 추출
- 기존 RQ와 참고문서 연결 후보 생성
- `제안` 상태의 Review Surface 생성

또한 `rq-ref link`로 Manifest에 이미 등록된 문서를 기존 RQ에 직접 연결할 수 있다.

하지만 공식 Harness UX에는 **새 참고문서를 등록하면서 기존 RQ에 연결 초안까지 만드는 단일 사용자 명령**이 없다. 따라서 사용자가 저수준 Runtime을 직접 알아야 하는 Gap이 있다.

### 목표 방향

```text
고객 인터뷰 / 회의록 / 추가 업무자료
              ↓
        rq-ref add/ingest
              ↓
      Manifest 문서 등록
              ↓
        Evidence 추출
              ↓
   기존 RQ Reference 제안
              ↓
      Agent/사람 검토
              ↓
       확정 / 제외
              ↓
 /work에서 실제 사용한 사실만 Provenance
```

예상 사용자 UX:

```bash
python sdlc/scripts/harness.py rq-ref add \
  --target RQ-001 \
  --reference br-input/originals/고객인터뷰.md
```

자연어 Skill UX:

```text
오늘 받은 고객 인터뷰 결과를 RQ-001 참고자료로 추가해줘.
```

### 후속 설계 항목

- `rq-ref add` 또는 `rq-ref ingest` 공식 subcommand 명칭 확정
- 기존 `intake_reference_draft.py`의 등록/추출/제안 기능을 재사용하는 Facade 설계
- 여러 `--target`과 여러 `--reference`를 한 번에 받을 수 있는 many-to-many 입력
- 새 문서를 특정 RQ에 바로 `확정` 연결할지 기본 `제안`으로 둘지 정책
- 문서가 프로젝트 밖에 있을 때 `br-input/originals/` 복사 정책 유지
- 동일 path/hash 재등록 시 idempotency
- 문서 교체/새 버전 도착 시 lifecycle/version 처리
- 인터뷰/회의록처럼 특정 발언 위치가 중요한 문서의 locator 표현
- 신규 자료가 기존 Requirement/BR과 충돌할 때 `/change`로 넘기는 경계
- 신규 자료에서 완전히 새로운 요구가 발견될 때 `rq-add`로 넘기는 경계
- `rq-ref` Skill과 13번 사용자 가이드의 자연어 Flow 통합

### 완료 조건 후보

- 기존 RQ를 다시 Requirement Intake하지 않고 새 참고자료를 등록할 수 있다.
- 하나의 RQ에 여러 참고문서를 연결할 수 있다.
- 하나의 참고문서를 여러 RQ에 연결할 수 있다.
- Reference 연결만으로 Canonical Business Truth가 자동 변경되지 않는다.
- 실제 `/work`에서 사용한 근거만 Canonical Provenance로 승격된다.
- 같은 문서를 다시 등록해도 Manifest/Reference가 불필요하게 중복되지 않는다.

---

## 6. 우선순위

현재 우선순위는 다음과 같이 둔다.

```text
현재 v1.10 사용성/실행 안정화
        ↓
RQ Intake / Reference / PM 운영 UX 안정화
        ↓
TODO-5 Late Reference Ingest UX
        ↓
TODO-4 Multi-writer RQ Allocation
        ↓
TODO-1 Unit Knowledge History
        ↓
TODO-2 AS-IS Canonical Bootstrap
        ↓
TODO-3 E2E Scenario Suite
        ↓
KB Lifecycle 완성/통합
```

단, 실제 Pilot 결과에서 Brownfield Bootstrap, E2E, 동시 RQ 생성 또는 진행 중 Reference 추가 문제가 더 큰 장애로 확인되면 순서를 재조정할 수 있다.

## 7. 이번 작업에서 하지 않는 것

- Stable Unit History Runtime 구현
- Canonical Event Sourcing 도입
- Source에서 Business Truth 자동 확정
- Project-wide E2E Registry Runtime 구현
- KB Publish/Supersede/Retire Runtime 구현
- Multi-writer RQ Sequence/Reservation Runtime 구현
- Late Reference Ingest 공식 `rq-ref add/ingest` Runtime 구현
- 기존 테스트/문서를 근거 없이 `VALIDATED` 또는 `PRODUCTION READY`로 승격

이 문서는 구현 완료 선언이 아니라 후속 설계를 위한 명시적 Framework Backlog다.
