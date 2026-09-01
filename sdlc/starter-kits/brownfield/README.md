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
│  ├─ db-schema-and-migrations.md          # 권장
│  ├─ interface-inventory.md              # 권장
│  ├─ runtime-config-inventory.md          # Secret 제외
│  └─ build-test-baseline.md               # 권장
├─ business-docs/
│  └─ originals/                          # 정책, 매뉴얼, 요구서, 회의록 등 원본
└─ profiles/
   ├─ terminology-profile.json            # 선택
   └─ customer-document-profile.json      # 선택
```

## Brownfield 기본 탐색 순서
1. 변경/분석 Seed를 RQ/FR/PGM/키워드 후보로 정규화한다.
2. Repository 기준 Commit/Tag/Branch를 고정하고 Source Hash 기준을 만든다.
3. Build file, module, source/test/resource root, DB/mapper/interface 자산을 먼저 인덱싱한다.
4. 기존 Trace/Index/Program Summary가 있으면 우선 재사용한다.
5. Seed와 직접 관련된 Symbol/Endpoint/Job/Event/Table 후보를 찾는다.
6. Caller/Consumer와 Callee/Dependency를 양방향으로 확장한다.
7. Data read/write, Transaction, Interface, Event, Config/Feature Flag, Test 관계를 확장한다.
8. 발견되지 않은 동적 호출/Reflection/Stored Procedure/외부 Consumer 가능성은 Coverage Gap으로 남긴다.
9. Business Impact는 Source 관계만으로 자동 확정하지 않는다.
10. 영향 결과에는 `직접 영향 / 간접 영향 / 확인 필요 / 분석 제외`를 구분한다.

## 입력 수준별 기대 결과
| 입력 수준 | 기대 결과 | 제한 |
|---|---|---|
| Seed + Repository만 있음 | Source/Profile 자동 탐색, 관련 Symbol 후보 | Build/Test/DB/외부 Consumer 누락 가능 |
| Source Profile + Build/Test 있음 | Compile/Test baseline과 정적 Trace 신뢰도 상승 | Runtime dynamic relation은 별도 |
| DB/Interface/Config 자료 있음 | Data/Integration 영향 확대 | 문서와 Source 충돌 시 자동 확정 금지 |
| 업무 원본문서까지 있음 | 기술 영향과 Business Rule Candidate 비교 | Source 구현을 Business Truth로 승격 금지 |

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

## Reverse Engineering 입력
현재 Branch에서는 Reverse Engineering 자체를 Core 기능으로 확정하지 않는다. 다만 향후 비교를 위해 다음 입력을 예약한다.
- `baseline_ref`: 기존 산출물과 연결된 Source 기준점
- `observed_ref`: 현재 Source 기준점
- `reverse_scope`: INVENTORY | DRIFT_CHECK | REVERSE_SPEC | SOURCE_DIFF

이 값이 있더라도 현재는 자동 Business Truth 수정이 아니라 Reverse Candidate 생성 대상으로만 취급한다.

## 준비도 판정
### STARTABLE
분석 Seed와 Repository 기준점이 존재한다.

### IMPACT_ANALYSIS_READY
Seed 관련 Source 후보와 직접 관계가 탐색되었고, 분석 Coverage와 사각지대가 함께 기록되어 있다.

### IMPLEMENTATION_READY
실제 변경 Target이 확정되고 Program DoR가 충족되며 Build/Test 실행 경로가 확인되어야 한다.
