# Brownfield Starter Kit

## 목적
기존 Application Source를 보유한 프로젝트에서 실제 Source Evidence를 기준으로 현재 동작, 변경 대상, 영향 범위와 재사용 가능성을 분석하기 위한 시작 패키지다.

Brownfield의 핵심은 문서가 많은 것이 아니라 **분석 Seed와 Repository 기준점이 명확한 것**이다.

## 최소 시작 가능 입력
1. 분석/변경 목적(`analysis_seed`)
2. 접근 가능한 Repository 또는 Source bundle 기준점(`repository.reference`)

Source root/build/test를 모르면 Harness가 탐색할 수 있으나, Repository 기준점 자체가 없으면 DISCOVERY 이후 결과를 실제 Brownfield Source 분석으로 확정해서는 안 된다.

## 권장 패키지
```text
brownfield-starter/
├─ starter-manifest.yaml
├─ change-or-analysis-request.md          # 분석 Seed/변경 목적
├─ source/
│  ├─ repository-reference.md             # URL/path + branch/tag/commit
│  ├─ source-profile.yaml                 # roots/excludes/build/test
│  ├─ module-inventory.md                 # 권장, 없으면 탐색 대상
│  └─ known-hotspots.md                   # 선택
├─ system-evidence/
│  ├─ architecture.md                     # 기존 문서가 있으면 원본/링크
│  ├─ screen-menu-inventory.md            # UI 프로젝트이면 권장
│  ├─ db-schema-and-migrations.md          # 권장
│  ├─ data-query-convention.md             # Query/Mapper 관례가 있으면 권장
│  ├─ common-code-dictionary.md            # 공통코드/기준정보가 있으면 권장
│  ├─ interface-inventory.md              # 권장
│  ├─ runtime-config-inventory.md          # Secret 제외
│  └─ build-test-baseline.md               # 권장
├─ business-docs/
│  └─ originals/                          # SOP, 정책, 매뉴얼, 요구서, 회의자료(PPTX/XLSX 포함) 원본
└─ profiles/
   ├─ terminology-profile.json            # 선택
   └─ customer-document-profile.json      # 선택
```

## Brownfield 기본 탐색 순서
1. 변경/분석 Seed를 RQ/FR/PGM/키워드 후보로 정규화한다.
2. SOP/업무문서가 있으면 포맷 Adapter로 구조 보존 Evidence Chunk를 만들고 `sop-extract` Skill로 6W/PROC/BR/Data/Screen/Integration Candidate를 추출한다.
3. Repository 기준 Commit/Tag/Branch를 고정하고 Source Hash 기준을 만든다.
4. Build file, module, source/test/resource root, UI/menu, DB/mapper/common-code/interface 자산을 먼저 인덱싱한다.
5. 기존 Trace/Index/Program Summary가 있으면 우선 재사용한다.
6. Seed와 직접 관련된 Symbol/Endpoint/Job/Event/Table/Screen 후보를 찾는다.
7. Caller/Consumer와 Callee/Dependency를 양방향으로 확장한다.
8. Data read/write, Transaction, Interface, Event, Config/Feature Flag, Test 관계를 확장한다.
9. 발견되지 않은 동적 호출/Reflection/Stored Procedure/외부 Consumer 가능성은 Coverage Gap으로 남긴다.
10. Business Impact는 Source 관계만으로 자동 확정하지 않는다.
11. 영향 결과에는 `직접 영향 / 간접 영향 / 확인 필요 / 분석 제외`를 구분한다.

## Project Impact Adapter 경계
Core는 `sdlc/design/contracts/brownfield-impact-contract.json`에서 공통 Node/Edge/Coverage/출력 형식만 제공한다.

실제 프로젝트의 다음 해석은 `sdlc/custom/project/adapters/impact/`에서 **별도 구현**해야 한다.
- Java/Spring/.NET/Node 등 언어·Framework별 Call/Symbol 관계
- JPA/MyBatis/JDBC/ORM/SQL/Table lineage
- Stored Procedure/Trigger/ETL
- Kafka/JMS/Event/외부 API 연결
- Reflection/Dynamic dispatch/Runtime wiring
- 프로젝트 고유 Config/Feature Flag/Scheduler

Adapter가 없더라도 분석 가능한 범위는 진행하지만 결과는 `PARTIAL_PROJECT_ADAPTER_REQUIRED`이며 완전한 영향분석으로 표시하지 않는다.

## 개발 상세 명세의 프로젝트 근거
Core Template은 화면/필드/CRUD/Logic/Query/Table/Common Code/Integration 항목을 강제하지만 실제 값은 프로젝트별 Evidence가 필요하다.

- 화면/메뉴: 화면 소스, Route/Menu config, 기존 UI 표준 또는 고객 승인 설계
- Field: 화면/DTO/Validation/DB/API 실제 근거
- CRUD: 실제 Entry Point/Service/Repository 행위
- Query/Table: Mapper/Repository/SQL/Schema/Migration
- Common Code: 코드 테이블/Enum/Dictionary/기준정보 API
- Integration: API Client/Message Producer·Consumer/File/Batch 설정

찾지 못한 항목은 `OPEN` 또는 `CHECK_REQUIRED`이며, 존재하지 않는 것으로 확정하지 않는다.

## 입력 수준별 기대 결과
| 입력 수준 | 기대 결과 | 제한 |
|---|---|---|
| Seed + Repository만 있음 | Source/Profile 자동 탐색, 관련 Symbol 후보 | UI/DB/Code/외부 Consumer 누락 가능 |
| Source Profile + Build/Test 있음 | Compile/Test baseline과 정적 Trace 신뢰도 상승 | Runtime dynamic relation은 별도 |
| UI/DB/Common Code/Interface 자료 있음 | 화면·필드·CRUD·Query·Code·Integration 상세화 | 문서와 Source 충돌 시 자동 확정 금지 |
| 업무 원본문서까지 있음 | 6W/기술 영향과 Business Rule Candidate 비교 | Source/SOP를 Business Truth로 자동 승격 금지 |

## Brownfield 영향분석 최소 Coverage 항목
- Entry Point / UI / API / Batch / Event
- Service/Domain/Application Symbol
- Repository/Mapper/Query
- Table/Column/View/Procedure 후보
- Caller/Consumer와 Callee/Dependency
- External API/Message/Event Topic
- Config/Feature Flag/Scheduler
- Transaction/Concurrency/Idempotency
- 관련 Test와 현재 Coverage
- Build/Module dependency
- Runtime/Dynamic 분석이 필요한 사각지대

## Reverse Engineering 범위
현재 Core에서 실제 구현된 범위는 **`DRIFT_CHECK`**다.

### Core 구현 완료: DRIFT_CHECK
다음 입력으로 현재 Source와 기존 산출물의 Source Evidence freshness를 비교한다.
- baseline source manifest
- observed source manifest
- artifact evidence index + 명시적 reverse propagation edge

`detect_source_drift.py`는 다음 결과만 만든다.
- `STALE_SOURCE_EVIDENCE`
- `STALE_PROPAGATED`
- `CHECK_REQUIRED_REVERSE`
- 재생성/사람검토 Reverse Candidate

기존 문서 또는 Business Truth를 자동 덮어쓰지 않는다.

### 고도화 영역
다음은 아직 Core 자동 기능이 아니다.
- 전체 Source Inventory 자동 역설계
- Reverse Program Spec 자동 생성
- Semantic Source Diff
- Source에서 BR을 자동 Business Truth로 승격
- 자동 문서 재작성/병합

## 준비도 판정
### STARTABLE
분석 Seed와 Repository 기준점이 존재한다.

### IMPACT_ANALYSIS_READY
Seed 관련 Source 후보와 직접 관계가 탐색되었고, 분석 Coverage와 사각지대가 함께 기록되어 있다. 프로젝트별 Impact Adapter가 필요한 영역은 구현/설정 상태가 함께 표시되어야 한다.

### IMPLEMENTATION_READY
실제 변경 Target이 확정되고 `developer-spec-contract.json`의 적용 가능한 상세 항목과 Program DoR가 충족되며 Build/Test 실행 경로가 확인되어야 한다.
