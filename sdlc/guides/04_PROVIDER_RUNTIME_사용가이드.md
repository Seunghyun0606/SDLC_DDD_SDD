# Provider Runtime 사용 가이드 — P0.6~P0.7

## 1. 목적

프로젝트별 Source/Test/Canonical/Deployment 등 도구를 SDLC Harness에 연결할 때 Core Skill이나 업무 문서를 수정하지 않고 Adapter 설정만 교체하기 위한 가이드다.

## 2. 기본 구조

```text
/work | /change | /check
        ↓
Command Router
        ↓
Required Capability
        ↓
Provider Registry
        ↓
AVAILABLE / DEGRADED Provider exact match
        ↓
Provider Request
        ↓
Adapter / Tool
        ↓
Provider Response + Evidence
```

Provider가 없거나 연결되지 않았으면 `OPEN/ACTION_REQUIRED`로 남는다.

## 3. Greenfield

초기 Requirement/Design 단계에서는 Existing Source가 없어도 정상이다.

```yaml
command: /work
project_context:
  mode: GREENFIELD
  stage: DESIGN
requested_capabilities: []
```

이 경우 Source Provider를 강제로 요구하지 않는다. 개발이 시작되어 Source write/test가 필요해지는 시점부터 해당 Capability를 요청한다.

## 4. Brownfield

Source Discovery가 필요한 경우 Stage가 필요한 Capability를 명시한다.

```yaml
requested_capabilities:
  - source.snapshot.read
  - source.search
```

Provider 선택은 기술명이나 파일명 유사도가 아니라 Capability exact match로 한다.

## 5. Custom Adapter 연결

Core Contract는 수정하지 않는다. Project Overlay 또는 Provider Registry에서 구현체를 바인딩한다.

```yaml
- provider_id: project-source
  provider_type: SOURCE
  enabled: true
  provider_state: AVAILABLE
  mode: READ_ONLY
  transport: ADAPTER
  capabilities:
    - source.snapshot.read
    - source.search
    - source.diff
  extensions:
    adapter_name: project-specific-source-adapter
```

언어, Framework, DB, CI 제품명 등은 `extensions` 또는 Adapter 내부 설정에 둔다.

## 6. Provider Type 확장

Provider Type은 닫힌 Core Enum이 아니다. 대문자 식별자 규칙을 사용하며 예를 들어 다음 Type을 추가할 수 있다.

- SOURCE
- TEST
- CANONICAL_REGISTRY
- DEPLOYMENT
- MONITORING
- NOTIFICATION
- ISSUE_PM
- BUSINESS_DOCUMENT

Router는 Type별 switch/case가 아니라 Capability exact match로 동작한다.

## 7. Provider State

- `AVAILABLE`: 사용 가능
- `DEGRADED`: 제한적으로 사용 가능
- `UNAVAILABLE`: 현재 접근 불가
- `UNCONFIGURED`: Adapter/Connection 미연결
- `DISABLED`: 의도적으로 비활성

Example Registry의 Source/Test는 기본 `UNCONFIGURED`다. 예제 파일이 존재한다는 이유만으로 실제 실행 가능하다고 보지 않는다.

## 8. Write 연결

Write Capability는 별도로 광고해야 한다.

```yaml
capabilities:
  - source.patch.apply
mode: READ_WRITE
```

실제 요청에는 최소 다음이 필요하다.

- expected revision
- permission proof reference
- idempotency key
- non-ambiguous target

이 값이 없으면 write를 실행하지 않는다.

## 9. Test Provider

`test.execute`의 Provider `OK`만으로 Verification PASS가 되지 않는다. P0.4 Test Contract와 동일 Source Evidence Set, 실행 Evidence, Required TC 결과가 함께 검증되어야 한다.

또 Provider 상태와 Test Outcome을 분리한다.

```text
process 실행 완료 + exit 0
→ Provider OK / Test PASSED

process 실행 완료 + exit non-zero
→ Provider OK / Test FAILED

timeout / command 실행불가
→ Provider BLOCKED 또는 ERROR
```

## 10. Canonical Registry Provider

`canonical.id.reserve` / `canonical.publish`는 Provider Capability만으로 실행하지 않는다. P0.2 Human/L2 Boundary Decision과 Publish Gate를 먼저 통과해야 한다.

## 11. P0.7 Reference Adapter

P0.7에는 실제 고객 Adapter가 아니라 Contract 검증용 Reference Adapter가 있다.

### Local Filesystem Source

지원:
- `source.snapshot.read`
- `source.object.read`
- `source.search`
- `source.diff`

특징:
- read-only
- bounded file/byte scan
- root 밖 relative path 차단
- Source Evidence는 `OBSERVED`
- 언어/Framework/DB 가정 없음

### Subprocess Test

지원:
- `test.discover`
- `test.execute`
- `test.result.read`

특징:
- `shell=False`
- argv list만 허용
- timeout 상한
- stdout/stderr 제한
- discovery pattern은 Project/Adapter가 주입
- production sandbox가 아님

Reference Adapter를 Production Adapter로 간주하지 않는다.

## 12. Adapter Conformance

새 Adapter는 다음을 확인한다.

- Provider Type이 유효한 대문자 식별자인가?
- Capability 이름이 구현체 명칭이 아니라 기능 의미인가?
- Request ID ↔ Response ID가 보존되는가?
- Provider Revision이 기록되는가?
- Evidence locator가 재현 가능한가?
- 미지원 Operation을 성공으로 반환하지 않는가?
- Source/Test Evidence를 Business Truth로 승격하지 않는가?
- Write가 Read에서 암묵적으로 허용되지 않는가?
- 구현체 고유 필드가 `extensions` 밖의 Core Schema를 바꾸지 않는가?
- timeout/partial/error가 빈 OK로 변환되지 않는가?
- Adapter 교체 시 Core Router/Stage Schema 수정이 불필요한가?

## 13. 검증 명령

### P0.6 Boundary

```text
python sdlc/scripts/validate_p06_contracts.py registry sdlc/config/provider-registry.example.yaml
python sdlc/scripts/validate_p06_contracts.py request <provider-request.yaml> --registry <provider-registry.yaml>
python sdlc/scripts/validate_p06_contracts.py response <provider-response.yaml> --request <provider-request.yaml> --registry <provider-registry.yaml>
python sdlc/scripts/route_provider_command.py <provider-registry.yaml> <runtime-context.yaml> -o <runtime-plan.yaml>
python sdlc/scripts/test_p06_contracts.py
```

### P0.7 Adapter Conformance

```text
python sdlc/scripts/run_provider_conformance.py \
  sdlc/design/validation/p0.7-provider-adapter-conformance-v1/source-adapter-suite.yaml

python sdlc/scripts/run_provider_conformance.py \
  sdlc/design/validation/p0.7-provider-adapter-conformance-v1/test-adapter-suite.yaml

python sdlc/scripts/test_p07_conformance.py
```

## 14. 파일럿 샘플 사용 원칙

첨부 요구사항목록과 기존 근태 Pilot은 Regression Fixture일 뿐이다.

Core Provider/Adapter Contract를 변경하려면 최소 다음을 만족해야 한다.

1. 파일럿 업무명/ID/Table/Symbol 없이 설명 가능
2. Greenfield에도 적용 가능
3. 서로 다른 기술/도메인에서도 같은 Envelope/Capability를 사용할 수 있음
4. 특정 Adapter 요구는 Core Schema 변경 대신 `extensions` 또는 Project Overlay로 해결
5. Generic Conformance가 먼저 통과하고 고객 Pilot은 마지막 회귀검증에만 사용
