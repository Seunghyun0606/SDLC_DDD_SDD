# Runtime / Provider Adapter Boundary — P0.6

상태: `ACTIVE_P0_CANDIDATE`

## 목적

SDLC 계약을 실제 Source/Test/Canonical/Command 도구와 연결하되 특정 업무도메인, 언어, 프레임워크, DB, CI 제품에 종속시키지 않는다.

핵심 원칙:

1. Provider Contract에는 업무도메인 명칭을 넣지 않는다.
2. Java/MyBatis/Oracle/GitHub 등 기술 고유값은 Adapter 또는 `extensions`에만 둔다.
3. Provider가 없으면 Agent가 결과를 발명하지 않고 `OPEN/BLOCKED`를 반환한다.
4. Greenfield는 Source Provider 부재를 정상 상태로 허용할 수 있다.
5. Brownfield/Hybrid에서 Source Evidence가 필요한 Stage는 Source Capability 부재 시 차단한다.
6. Read와 Write Capability를 분리하고 Write는 명시적 권한·revision·idempotency proof를 요구한다.
7. Provider Response의 Evidence는 Truth Class를 포함하며 Source/Test 관찰은 기본 `OBSERVED`다.
8. Router는 orchestration만 수행하며 Business Truth, Provider Result, Canonical ID를 생성하지 않는다.

## Provider Types

- `SOURCE`
- `TEST`
- `CANONICAL_REGISTRY`
- `COMMAND_ROUTER`

추가 Provider는 동일 Envelope를 사용해 확장할 수 있다. 예: BusinessDocument, Issue/PM, Deployment, Monitoring, Notification.

## Capability Naming

`<provider-domain>.<resource>.<verb>` 형식을 사용한다.

예:
- `source.snapshot.read`
- `source.search`
- `source.diff`
- `source.patch.apply`
- `test.discover`
- `test.execute`
- `test.result.read`
- `canonical.id.reserve`
- `canonical.publish`
- `command.route.check`

Capability 문자열은 구현체 이름이 아니라 기능 의미를 표현한다.

## Request Envelope

필수:
- `request_id`
- `provider_type`
- `operation`
- `project_context.mode`
- `target`
- `write_intent`

Write 요청 추가 필수:
- `expected_revision`
- `idempotency_key`
- `permission_proof_ref`

도메인/도구 고유 필드는 `extensions` 아래에만 둔다.

## Response Envelope

필수:
- `request_id`
- `provider_id`
- `provider_type`
- `operation`
- `status`
- `provider_revision`
- `outputs`
- `evidence`
- `open_items`

`status`:
- `OK`
- `PARTIAL`
- `BLOCKED`
- `ERROR`

Provider 오류나 미지원 Capability를 빈 성공으로 변환하지 않는다.

## Evidence Rules

각 Evidence:
- `evidence_id`
- `truth`
- `locator`
- `revision`
- `observed_value`

허용 Truth:
- `GIVEN`
- `OBSERVED`
- `INFERRED`
- `CONFIRMED`
- `OPEN`

Source/Test 실행 Evidence는 Provider가 Business Decision을 소유하지 않는 한 `CONFIRMED` Business Truth로 승격하지 않는다.

## Project Mode Rules

### GREENFIELD
- Existing Source Capability는 선택사항.
- `source.snapshot.read` 미지원만으로 초기 Requirement/Design을 차단하지 않는다.
- Source가 생성된 뒤 Development/Verify 단계에서는 configured capability 정책을 적용한다.

### BROWNFIELD
- Discovery/Impact에 Source Evidence가 필요하면 Source Provider가 필수다.
- Revision 없는 Source write는 금지한다.

### HYBRID
- Existing 영역은 Brownfield 규칙, 신규 영역은 Greenfield 규칙을 target scope별 적용한다.

### AUTO
- Provider 존재만으로 Mode를 확정하지 않는다. Project evidence와 profile rule로 결정한다.

## Write Safety

Write Capability는 Read Capability에서 암묵적으로 추론하지 않는다.

필수 Guard:
- capability explicitly advertised
- provider mode `READ_WRITE`
- target revision known
- permission proof present
- idempotency key present
- ambiguous target false

Canonical Publish는 추가로 Human/L2 Boundary Decision과 preallocated/reserved ID가 필요하다.

## Command Router

외부 사용자 명령은 `/work`, `/change`, `/check`를 유지한다.

Router 책임:
1. command intent 분류
2. 현재 E2E status 로드
3. 필요한 capability 계산
4. provider registry에서 exact capability 선택
5. unavailable/ambiguous provider는 OPEN/BLOCKED
6. 실행 계획 반환

Router 금지:
- Provider 결과 추측
- Blocker 우회
- Business Boundary 자동확정
- Canonical ID 임의 생성
- Test 미실행을 PASS 처리

## Adapter Conformance

Provider 구현체는 최소 다음을 검증해야 한다.

- registry capability와 실제 지원 operation 일치
- request/response correlation 유지
- provider revision/evidence locator 존재
- write guard 준수
- unsupported operation은 `BLOCKED/ERROR`
- implementation-specific field가 core envelope를 오염시키지 않음

## Anti-overfitting Rule

파일럿 Requirement, 특정 업무명, 특정 Table/API/Symbol은 Core Provider Contract의 필드명·상태·Capability 정의에 사용하지 않는다.

파일럿은 오직 다음 용도로만 사용한다.
- conformance example
- regression fixture
- evidence payload sample

Core Contract 변경은 최소 두 개의 서로 다른 도메인/기술 조합에서 설명 가능해야 한다.
