# Project Config 옵션 상세 가이드

이 문서는 `.sdlc/project.yaml`의 **현재 v1.10 기준 옵션 Reference**다. 처음 설정하는 순서는 `02_PROJECT_설정가이드.md`를 보고, 각 옵션의 정확한 역할이나 허용값을 확인할 때 이 문서를 사용한다.

현재 설정 해석의 기준 구현은 다음 두 파일이다.

```text
sdlc/scripts/project_config.py
sdlc/scripts/runtime_config.py
```

Change Level의 실제 적용은 `sdlc/scripts/change_execution_runtime.py`, Customer Projection의 상세 계약/표시 정책은 `sdlc/scripts/customer_projection_runtime.py`가 소비한다.

---

## 1. 가장 중요한 원칙

### 1.1 사람이 직접 관리하는 설정은 하나다

```text
.sdlc/project.yaml
```

다음 파일은 Runtime이 만든 결과이므로 직접 수정하지 않는다.

```text
.sdlc/runtime/effective/project-profile.json
.sdlc/runtime/effective/source-profile.json
.sdlc/runtime/effective/agent-execution.json
.sdlc/runtime/effective/agent-provider.json
.sdlc/runtime/effective/project-context.json
.sdlc/runtime/effective/config-usage.json
.sdlc/runtime/effective/tailoring-config.json
```

### 1.2 Config 옵션은 네 종류로 구분한다

| 종류 | 의미 |
|---|---|
| **Runtime Switch** | 실제 실행 방식, Source 범위, Guard, Change Level, Profile 선택 등에 직접 영향을 준다. |
| **Resolved Policy** | Resolver가 유효한 설정으로 보존하지만 모든 값이 별도 실행 로직을 만드는 것은 아니다. Profile/Lifecycle과 함께 의미가 생긴다. |
| **Document / Agent Context** | Agent와 문서에 프로젝트 문맥을 제공한다. 이 값을 썼다고 Core Runtime 동작이 자동 변경되는 것은 아니다. |
| **Extension Config** | `extensions.*` 아래에서 프로젝트 Extension/Adapter가 읽는 값이다. Core가 의미를 추측하지 않는다. |

알 수 없는 일반 Key는 조용히 무시하지 않는다. `DEAD_CONFIG`로 간주되어 `check --setup`이 실패한다.

### 1.3 YAML은 제한된 문법만 사용한다

Harness는 일반 YAML 전체가 아니라 보수적인 subset을 읽는다.

- 들여쓰기: 2칸 단위
- Mapping: 지원
- Scalar list: 지원
- 문자열/정수/boolean/null: 지원
- List 안의 Object/Mapping: 지원하지 않음
- YAML anchor, merge key, 복잡한 multi-line 문법: 사용하지 않음

권장 방식은 `setup`이 만든 형식을 유지하는 것이다.

---

## 2. 전체 예시

```yaml
schema_version: 1

project:
  name: "order-service"
  mode: "BROWNFIELD"
  description: "주문/결제/재고 연계 서비스를 유지보수하는 프로젝트"

delivery:
  profile: "STANDARD"

change:
  level_policy: "AUTO"
  minimum_level: "L1"
  target_levels:
    RQ-001:
      level: "L3"
      reason: "업무규칙과 기능 영향을 상세 검토해야 함"

agent:
  execution: "INTERACTIVE"

technology:
  language: "Java"
  framework: "Spring Boot"
  build:
    - "./mvnw -q -DskipTests package"
  test:
    - "./mvnw test"

source:
  roots:
    - "src/main/java"
  test_roots:
    - "src/test/java"
  resource_roots:
    - "src/main/resources"
  excludes:
    - ".git/**"
    - "target/**"

architecture:
  style: "Layered"
  modules:
    - "order"
    - "payment"

coding:
  convention: "프로젝트 Java Coding Convention"
  naming: "기존 naming 유지"

data:
  database: "PostgreSQL"
  orm_mapper: "JPA"
  migration: "Flyway"

interface:
  api: "REST"
  event: "Kafka"
  batch: "없음"

security:
  standard: "프로젝트 보안 가이드 v2"

deployment:
  environment: "dev/test/prod"

git:
  branch_strategy: "feature-branch + pull-request"
  protected_branches:
    - "main"

documents:
  language: "ko-KR"
  engineering:
    profile: "ENGINEERING_SDD_COMPACT"
    manual_edit_policy: "TYPO_ONLY"
    freshness: "CANONICAL_REVISION"
  customer:
    profile: "CUSTOMER_STANDARD_3"
    scope: "RQ"
    freshness: "CANONICAL_AND_AS_BUILT"
    final_review:
      human_editable: true
  pm:
    profile: "PM_STANDARD"
  machine:
    visibility: "HIDDEN"

unresolved:
  - "부분취소 시 재고 복구 순서의 업무정책 확인 필요"
```

---

## 3. `schema_version`

```yaml
schema_version: 1
```

- 종류: **Runtime Switch / Schema Guard**
- 필수 현재값: `1`
- 역할: `.sdlc/project.yaml` 구조 버전을 확인한다.
- 다른 값: Fail-closed. 현재 Runtime은 거부한다.

---

## 4. `project.*`

### 4.1 `project.name`

```yaml
project:
  name: "order-service"
```

- 종류: **Document / Agent Context**
- 역할: 프로젝트 식별 이름. Agent Context와 생성 문서에서 사용할 수 있다.
- Runtime Stage/Level을 직접 바꾸지는 않는다.

### 4.2 `project.mode`

```yaml
project:
  mode: "BROWNFIELD"
```

- 종류: **Runtime Switch**
- 허용값: `GREENFIELD | BROWNFIELD | HYBRID | AUTO`
- 역할: Delivery Profile이 어떤 Stage 집합을 활성화할지 결정할 때 사용한다.

의미:

| 값 | 의미 |
|---|---|
| `GREENFIELD` | 신규 구축 중심. 기존 Source 분석 Stage를 기본 전제로 하지 않는다. |
| `BROWNFIELD` | 기존 Source/DB/Config를 기반으로 개선한다. Discovery/Impact 경로가 포함될 수 있다. |
| `HYBRID` | 신규 + 기존 시스템이 함께 있는 프로젝트. 현재 Core Delivery 계산에서는 Brownfield 계열 Stage 집합을 사용한다. |
| `AUTO` | Setup 시 Repository를 탐색해 실제 Mode를 결정하는 용도. Runtime에 AUTO가 남아 있으면 보수적으로 Brownfield 계열로 처리한다. |

권장: 처음에는 `setup --mode AUTO`를 써도 되지만, 생성된 `.sdlc/project.yaml`에는 탐지된 구체 Mode를 유지한다.

### 4.3 `project.description`

- 종류: **Document / Agent Context**
- 역할: 프로젝트 목적과 업무 범위를 Agent에게 전달한다.
- 자유 텍스트다.

---

## 5. `delivery.profile`

```yaml
delivery:
  profile: "STANDARD"
```

- 종류: **Runtime Switch**
- 허용값: `FAST | STANDARD | FULL`
- Change Level과 다른 개념이다.

| Profile | 대표 용도 | Graph Hop | 특징 |
|---|---|---:|---|
| `FAST` | XS/S 운영변경, 소규모 기능 | 1 | 필요한 의미만 수행. 일부 Stage는 조건부. |
| `STANDARD` | 일반 SI/SM 기능 | 3 | 업무흐름·영향·설계·개발·검증 균형. 기본값. |
| `FULL` | 대형 구축, 고위험 변경 | 4 | 전체 Stage와 지식 승격 후보까지 사용. |

주의:

```text
Delivery Profile = 프로젝트 실행 기본 폭
Change Level      = 특정 변경의 의미/Evidence/Review 깊이
Document Profile  = 사람에게 보여줄 문서 topology
```

셋을 같은 개념으로 사용하지 않는다.

---

## 6. `change.*` — Change Level Control Plane

### 6.1 `change.level_policy`

```yaml
change:
  level_policy: "AUTO"
```

- 종류: **Runtime Switch**
- 허용값: `AUTO | MANUAL`

`AUTO`:
- Canonical 구조와 Typed Evidence로 L1~L5를 계산한다.
- 중요한 Unknown이 있으면 Safety Floor가 적용될 수 있다.
- 기존 Effective Level보다 낮은 AUTO 결과가 나와도 자동 강등하지 않는다.

`MANUAL`:
- Target별 설정 또는 `default_level`을 사용한다.
- 둘 다 없고 기존 Human Override도 없으면 `HUMAN_DECISION_REQUIRED`가 된다.

### 6.2 `change.minimum_level`

```yaml
change:
  minimum_level: "L2"
```

- 종류: **Runtime Switch**
- 허용값: `L1 | L2 | L3 | L4 | L5`
- 역할: **AUTO 판정의 프로젝트 하한**이다.
- 예: AUTO 계산이 L1이어도 `minimum_level: L2`이면 L2부터 시작한다.

중요: `minimum_level`은 명시적 Target/Human Override를 금지하는 절대 하한이 아니다. 명시적 Override는 별도 정책이며, 실제 안전 하한은 Evidence 기반 `safety_floor`가 담당한다.

### 6.3 `change.default_level`

```yaml
change:
  level_policy: "MANUAL"
  default_level: "L3"
```

- 종류: **Runtime Switch**
- 허용값: `L1..L5`
- 역할: `MANUAL` 정책에서 Target별 Level이 없을 때 쓰는 프로젝트 기본값.
- `AUTO`에서는 일반적인 기본값으로 사용하지 않는다.

### 6.4 `change.target_levels.<TARGET>.level`

```yaml
change:
  target_levels:
    RQ-001:
      level: "L4"
```

- 종류: **Runtime Switch**
- 역할: 특정 Target의 사전 Level Override.
- AUTO 관측값 및 `default_level`보다 우선한다.
- 문자열 축약형 `RQ-001: "L4"`도 읽을 수 있지만, 이유 이력을 위해 Mapping 형태를 권장한다.

### 6.5 `reason`

```yaml
      reason: "승인 Process와 타 모듈 영향 존재"
```

- 종류: **Runtime Control Metadata**
- 역할: 왜 해당 Level을 지정했는지 `level_history`와 상태 설명에 남긴다.
- Mapping 형태에서 입력한다면 빈 문자열을 사용하지 않는다.

### 6.6 `accept_below_safety_floor`

```yaml
      accept_below_safety_floor: true
```

- 종류: **High-risk Runtime Switch**
- 기본: `false`
- 역할: Evidence가 요구하는 `safety_floor`보다 낮은 명시적 Target Level을 위험수용과 함께 허용한다.
- 단순히 문서를 줄이기 위해 사용하지 않는다.

### 6.7 Level 적용 우선순위

현재 Runtime의 실질 우선순위는 다음과 같다.

```text
현재 Human Override(set-level)
        ↓
project.yaml target_levels.<TARGET>
        ↓
MANUAL default_level
        ↓
AUTO classification + minimum_level
```

어떤 명시적 값이든 Evidence `safety_floor` 아래로 내려가면 별도 Risk Acceptance가 필요하다.

Runtime 상태는 다음에 남는다.

```text
sdlc/runtime/change-level/<TARGET>.json
```

---

## 7. `agent.*`

### 7.1 `agent.execution`

```yaml
agent:
  execution: "INTERACTIVE"
```

- 종류: **Runtime Switch**
- 허용값: `INTERACTIVE | HEADLESS`
- 기본: `INTERACTIVE`

`INTERACTIVE`:
- 현재 IDE/Chat/CLI Host Agent가 작업한다.
- `agent.provider.*`를 같이 쓰면 Config 오류다.

`HEADLESS`:
- Harness가 외부 Provider Command를 실행한다.
- `agent.provider.command`가 필수다.

### 7.2 `agent.provider.id`

- 종류: **Runtime Switch / Metadata**
- HEADLESS에서만 사용.
- 기본: `PROJECT_AGENT_PROVIDER`
- Provider 실행 주체를 식별한다.

### 7.3 `agent.provider.command`

```yaml
agent:
  execution: "HEADLESS"
  provider:
    command:
      - "python"
      - "tools/run_agent.py"
```

또는 한 문자열 Command도 허용한다.

- 종류: **Runtime Switch**
- HEADLESS 필수.
- Harness가 실제로 실행할 외부 Agent command다.

### 7.4 `agent.provider.timeout_seconds`

- 종류: **Runtime Switch**
- 기본: `180`
- 조건: 양의 정수
- Provider 실행 timeout.

### 7.5 `agent.provider.result_filename`

- 종류: **Runtime Switch**
- 기본: `stage-result.json`
- Provider가 생성하는 Stage Result 파일명.

주의: Provider를 쓰더라도 Protected Branch, Stage Result Validator, Canonical Apply Guard를 우회하지 않는다.

---

## 8. `technology.*`

### 8.1 `technology.language`

- 종류: **Document / Agent Context**
- 예: `Java`, `JavaScript/TypeScript`, `Python`
- Source/설계 문맥에 사용한다. 값 자체가 특정 Adapter 설치를 의미하지 않는다.

### 8.2 `technology.framework`

- 종류: **Document / Agent Context**
- 예: `Spring Boot`, `Vue`, `JSP/Servlet`
- 값만 적는다고 Framework-specific 분석 기능이 자동 설치되는 것은 아니다.

### 8.3 `technology.build`

```yaml
technology:
  build:
    - "./mvnw -q -DskipTests package"
```

- 종류: **Runtime Switch**
- 문자열 또는 문자열 목록.
- Source Write를 포함하는 작업에서 Build 검증 경계에 사용된다.

### 8.4 `technology.test`

```yaml
technology:
  test:
    - "./mvnw test"
```

- 종류: **Runtime Switch**
- Source 변경 검증에 사용할 Test Command.

모르는 Build/Test command를 추측해서 적지 않는다. `unresolved`에 남기고 확인한다.

---

## 9. `source.*`

### 9.1 `source.roots`

- 종류: **Runtime Switch**
- Source 분석 및 허용 Write Root 계산의 핵심 입력.
- 실제 Source Directory만 넣는다.

### 9.2 `source.test_roots`

- 종류: **Runtime Switch**
- Test Source Root.
- Core Source scope 계산에 포함된다.

### 9.3 `source.resource_roots`

- 종류: **Runtime Switch**
- XML, Config, SQL Resource 같은 비코드 Source Root.
- Core Source scope 계산에 포함된다.

### 9.4 `source.excludes`

- 종류: **Document / Agent Context**
- Effective Source Profile에도 전달된다.
- 예: `.git/**`, `target/**`, `node_modules/**`

중요: 현재 Config 분류상 `source.excludes`는 `source.roots`와 같은 Core Runtime write-scope switch가 아니다. 즉 exclude를 적었다고 그 값만으로 Source Write Guard의 허용 Root가 재설계된다고 가정하지 않는다. 분석/Scanner/Agent가 제외 문맥으로 활용하는 값으로 본다.

---

## 10. `git.*`

### 10.1 `git.branch_strategy`

- 종류: **Document / Agent Context**
- 예: `feature-branch + pull-request`
- 팀 운영 규칙 설명용이다.

### 10.2 `git.protected_branches`

```yaml
git:
  protected_branches:
    - "main"
    - "master"
```

- 종류: **Runtime Switch**
- 문자열 목록.
- Work/Change Provider 실행 전에 직접 쓰기를 차단하는 Guard에 전달된다.

Repository Hosting의 실제 Branch Protection 설정 자체를 생성하는 옵션은 아니다. GitHub/GitLab 보호 규칙은 별도로 구성한다.

---

## 11. 프로젝트 문맥 영역

다음 Prefix 아래의 값은 **Document / Agent Context**다.

```text
architecture.*
coding.*
data.*
interface.*
security.*
deployment.*
```

예:

```yaml
architecture:
  style: "Layered"
  modules:
    - "hr"
    - "payroll"

coding:
  convention: "사내 Java 표준"

data:
  database: "Oracle"
  orm_mapper: "MyBatis"

interface:
  api: "REST"
  batch: "Quartz"

security:
  standard: "개인정보 처리 기준 v3"

deployment:
  environment: "dev/test/prod"
```

이 영역은 Agent가 분석·설계·문서 작성 시 참고한다. **Config에 `security.standard`을 적었다고 Change Level이 자동 L4가 되는 식의 실행 규칙은 없다.** Change Level은 Canonical/Typed Evidence의 실제 영향 Fact를 기준으로 계산한다.

이 Prefix 안에서는 프로젝트별 문맥 Key를 추가할 수 있지만, 해당 Key를 실제 Runtime Switch처럼 사용하려면 별도 Extension/Contract가 필요하다.

---

## 12. `documents.*`

### 12.1 `documents.language`

```yaml
documents:
  language: "ko-KR"
```

- 종류: **Document / Agent Context**
- 기본 문서 언어 문맥.
- 값만으로 모든 외부 문서를 자동 번역하는 기능은 아니다.

`documents.customer_language`도 Compatibility/Context Key로 인식되지만 신규 프로젝트는 `documents.language`와 Customer Template/Profile 정책을 우선 사용한다.

### 12.2 `documents.engineering.profile`

```yaml
documents:
  engineering:
    profile: "ENGINEERING_SDD_COMPACT"
```

- 종류: **Runtime Switch**
- 기본: `ENGINEERING_SDD_COMPACT`
- 개발자/설계자용 Human Artifact topology를 선택한다.
- Custom Profile은 `sdlc/custom/project/tailoring/`에서 선택 가능하다.

Change Level과 독립이다. Profile이 `PROFILE_PRIMARY_SET`이면 L1이라도 Profile-required 문서는 유지하고 내용 깊이만 `CONCISE`가 될 수 있다.

### 12.3 `documents.engineering.manual_edit_policy`

허용값:

```text
TYPO_ONLY
READ_ONLY
HUMAN_REVIEW
```

- 종류: **Resolved Policy**
- 기본: `TYPO_ONLY`
- Projection Lifecycle metadata에 기록되는 직접 수정 정책이다.

의미:

| 값 | 의미 |
|---|---|
| `TYPO_ONLY` | 오탈자/표현 수정 외 의미 변경은 `/work` 또는 `/change`로 돌린다. |
| `READ_ONLY` | Generated View를 원칙적으로 직접 수정하지 않는다. |
| `HUMAN_REVIEW` | 사람이 Review/보완하는 Custom 문서 운영을 허용한다. 의미 변경의 Canonical Round-trip은 여전히 필요하다. |

파일 시스템 자체를 잠그는 OS 권한 옵션은 아니다.

### 12.4 `documents.engineering.freshness`

```yaml
freshness: "CANONICAL_REVISION"
```

- 종류: **Resolved Policy**
- 기본: `CANONICAL_REVISION`
- Engineering Projection의 Freshness 의도를 나타낸다.

현재 Resolver는 이 값을 별도 Enum으로 강제하지 않는다. Core Projection Lifecycle의 실제 Stale 판단은 Canonical revision 및 생성/검토 hash를 사용한다. 따라서 임의의 새 문자열을 넣는다고 새 Freshness Algorithm이 생기지는 않는다. 신규 프로젝트는 기본값을 유지하는 것을 권장한다.

### 12.5 `documents.engineering.output_root`

- 종류: **Document Context**
- 인식되는 경로 설정이지만 현재 Standard/Custom Profile의 실제 산출 경로는 Profile artifact의 `output_path`가 권위다.
- 이 값만 바꿔 모든 Profile output path가 자동 재작성된다고 가정하지 않는다.

### 12.6 `documents.internal.*`

- `documents.internal.profile`: **Legacy Compatibility Alias**
- 신규 프로젝트에서는 사용하지 않는다.
- `documents.engineering.profile`이 있으면 Engineering 설정이 우선한다.
- `documents.internal.output_root`도 Compatibility/Document Context다.

### 12.7 `documents.customer.profile`

```yaml
customer:
  profile: "CUSTOMER_STANDARD_3"
```

- 종류: **Runtime Switch**
- 기본: `CUSTOMER_STANDARD_3`
- Customer Artifact topology를 선택한다.
- Engineering Profile과 독립이다.

### 12.8 `documents.customer.scope`

허용값:

```text
RQ
MILESTONE
PROJECT
```

- 종류: **Resolved Policy**
- 기본: `RQ`
- 고객 문서를 어느 수준에서 운영할지 나타낸다.

현재 low-level Customer Projection 명령은 `--target`을 받는 Target 단위 생성기다. `scope: PROJECT`를 적었다고 모든 RQ를 자동 병합하는 의미는 아니다. Milestone/Project 집계는 선택 Profile 또는 상위 Orchestration이 그 범위를 실제로 구현해야 한다.

### 12.9 `documents.customer.freshness`

```yaml
freshness: "CANONICAL_AND_AS_BUILT"
```

- 종류: **Resolved Policy**
- 기본: `CANONICAL_AND_AS_BUILT`
- 고객 View는 Business 의미뿐 아니라 구현/검증 결과까지 현행성이 중요하다는 정책 표현이다.

Engineering freshness와 마찬가지로 현재 Resolver는 임의 문자열까지 별도 Enum으로 제한하지 않는다. 실제 Stale 상태는 Projection Lifecycle이 Canonical revision/hash를 중심으로 판단하므로 기본값 또는 계약에 정의된 값만 사용한다.

### 12.10 `documents.customer.projection_contract`

```yaml
projection_contract: "sdlc/design/contracts/customer-document-contract.json"
```

- 종류: **Runtime Switch**
- 생략 시 위 경로가 기본값.
- Customer Section 의미, 필수/선택 Section, 안전한 Projection 규칙을 정의하는 Contract 경로다.
- Repository 밖으로 탈출하는 경로는 허용하지 않는다.

### 12.11 `documents.customer.projection_config`

```yaml
projection_config: "sdlc/config/customer-document-profile.json"
```

- 종류: **Runtime Switch**
- 생략 시 위 경로가 기본값.
- Customer 표시 옵션, optional section 활성/비활성 등 Renderer 정책을 선택한다.

이 값은 `documents.customer.profile`과 다르다.

```text
customer.profile            = 몇 개의 어떤 문서를 만들지
customer.projection_config  = 그 문서 안에 무엇을 어떻게 표시할지
customer.projection_contract= 어떤 의미 Section을 허용할지
```

### 12.12 `documents.customer.final_review.human_editable`

```yaml
final_review:
  human_editable: true
```

- 종류: **Resolved Policy**
- 기본: `true`
- 최종 제출 직전 사람이 표현/레이아웃을 검토할 수 있다는 정책값이다.
- `true`가 자동 승인이나 Canonical 수정 권한을 의미하지 않는다.
- 실제 `FINAL_REVIEW` 전환은 Projection Lifecycle의 명시적 Review 동작으로 수행한다.

### 12.13 `documents.customer.output_root`

- 종류: **Document Context**
- 실제 Customer artifact 경로의 권위는 선택한 Customer Profile의 `output_path`다.
- `output_root` 하나만 바꿔 Profile의 모든 출력 경로가 자동 치환된다고 가정하지 않는다.

### 12.14 `documents.pm.profile`

```yaml
pm:
  profile: "PM_STANDARD"
```

- 종류: **Runtime Switch / Profile Selector**
- 기본: `PM_STANDARD`
- PM/Review View topology 선택.

### 12.15 `documents.pm.output_root`

- 종류: **Document Context**
- Profile이 명시한 output path보다 우선하는 자동 rewrite switch가 아니다.

### 12.16 `documents.machine.visibility`

```yaml
machine:
  visibility: "HIDDEN"
```

- 종류: **Runtime Switch**
- 허용값: `HIDDEN | DEBUG`
- 기본: `HIDDEN`

`HIDDEN`:
- Canonical ID, Relation, Provenance, Confidence, Queue/Guard code 같은 Machine detail을 일반 Human Projection에 기본 노출하지 않는다.

`DEBUG`:
- Harness 관리자/디버깅 목적의 Machine Evidence 가시성을 높이는 모드.
- Customer 문서가 내부 Canonical 전체를 출력하도록 허용하는 옵션은 아니다. Customer direct Canonical 입력은 별도 Visibility Contract에 따라 Allowlist-first를 유지한다.

---

## 13. `unresolved`

```yaml
unresolved:
  - "실제 운영 DB 종류 확인 필요"
  - "부분취소 업무정책 확인 필요"
```

- 종류: **Document / Agent Context**
- 모르는 값을 거짓으로 채우지 않고 남기는 곳이다.
- 이 목록 자체가 자동 `SOURCE_BLOCK`이나 Change Level을 만드는 실행 스위치는 아니다.
- `/work`에서 실제 Evidence/업무 판단으로 해소하면 관련 Canonical OPEN/HITL Queue/문서 상태도 함께 갱신한다.

---

## 14. `extensions.*`

```yaml
extensions:
  my_adapter:
    enabled: true
    profile: "CUSTOM_A"
```

- 종류: **Extension Config**
- `extensions.*` 아래 Key는 Core가 Dead Config로 막지 않는다.
- 하지만 Core가 그 의미를 자동 해석하지도 않는다.
- 해당 Extension/Adapter가 실제로 이 값을 읽는 코드와 Contract를 갖고 있어야 효과가 있다.

즉 `extensions.foo.enabled: true`만 적고 실제 `foo` Extension이 없으면 기능이 생기지 않는다.

---

## 15. 설정과 실제 동작의 관계를 확인하는 방법

### 15.1 기본 검증

```bash
python sdlc/scripts/harness.py check --setup
```

다음을 확인한다.

- Project Config parse 성공
- 허용되지 않은 값 없음
- Dead Config 없음
- Profile resolution 성공
- Runtime/Agent 설정 생성 가능

### 15.2 어떤 Key가 어떻게 분류됐는지 확인

Setup/Check 후 다음 Machine 파일을 확인할 수 있다.

```text
.sdlc/runtime/effective/config-usage.json
```

형태:

```json
{
  "runtime": [],
  "extension": [],
  "document": [],
  "dead": []
}
```

`dead`가 하나라도 있으면 “설정했으니 적용됐겠지”라고 진행하지 말고 Key 이름이나 지원 여부를 먼저 수정한다.

### 15.3 실제 Effective 값 확인

```text
.sdlc/runtime/effective/project-context.json
.sdlc/runtime/effective/tailoring-config.json
.sdlc/runtime/effective/agent-execution.json
.sdlc/runtime/effective/agent-provider.json
```

이 파일은 확인용이며 직접 편집하지 않는다.

---

## 16. 자주 하는 실수

### `delivery.profile`과 Change Level을 같은 것으로 생각함

잘못된 이해:

```text
FAST = L1
FULL = L5
```

아니다. Delivery는 프로젝트 기본 실행 폭이고 Change Level은 Target 변경 깊이다.

### `change.minimum_level`을 모든 Override의 절대 하한으로 생각함

`minimum_level`은 AUTO 하한이다. 명시적 Target/Human Override는 별도이며 Evidence `safety_floor`가 실제 안전 하한을 통제한다.

### L1이면 Profile 문서를 삭제함

Change Level은 문서 topology를 소유하지 않는다. `PROFILE_PRIMARY_SET` Profile이라면 L1에서도 required 문서는 유지하고 내용만 `CONCISE`로 작성한다.

### `source.excludes`를 Write Guard라고 생각함

허용 Source Write Root는 `source.roots/test_roots/resource_roots`와 실행 Plan/Guard가 결정한다. `source.excludes`는 현재 Core 분류상 Context 값이다.

### `documents.*.output_root`만 바꾸면 경로가 모두 이동한다고 생각함

현재 artifact output의 권위는 Tailoring Profile의 `output_path`다. 프로젝트별 경로를 바꾸려면 Custom Profile의 output path를 함께 설계한다.

### `documents.machine.visibility: DEBUG`로 고객 문서 내부 정보를 전부 노출할 수 있다고 생각함

Customer Projection Visibility는 별도 Contract가 있고 direct Canonical은 Allowlist-first다. DEBUG는 Customer 안전 경계를 해제하는 bypass가 아니다.

### `architecture.*`, `security.*`를 쓰면 Runtime 정책이 자동 활성화된다고 생각함

이 값은 기본적으로 Agent/문서 Context다. 실제 실행 규칙이 필요하면 Typed Evidence/Canonical Fact 또는 별도 Extension Contract가 필요하다.

### 임의 Key를 추가함

일반 Top-level/일반 경로의 미지원 Key는 Dead Config가 되어 실패한다. 프로젝트 Extension 전용 설정만 `extensions.*` 아래에 둔다.

---

## 17. 권장 변경 절차

`.sdlc/project.yaml`을 수정한 뒤 항상 다음 순서로 확인한다.

```bash
python sdlc/scripts/harness.py check --setup
python sdlc/scripts/harness.py check project
```

Change Level/Profile을 바꿨다면 영향 Target을 다시 실행한다.

```bash
python sdlc/scripts/harness.py work --target RQ-001
```

Target별 Level을 작업 중 명시적으로 바꿀 때는 JSON State를 직접 수정하지 않고 다음 경계를 사용한다.

```bash
python sdlc/scripts/change_execution_runtime.py set-level \
  --target RQ-001 --level L3 --reason "기능 영향 상세 검토 필요"

python sdlc/scripts/change_execution_runtime.py clear-level \
  --target RQ-001 --reason "AUTO 정책으로 복귀"
```

설정 변경 후 생성된 Effective Config와 Projection이 서로 다른 기준을 가리키지 않도록 `/work` 재실행까지 완료한다.
