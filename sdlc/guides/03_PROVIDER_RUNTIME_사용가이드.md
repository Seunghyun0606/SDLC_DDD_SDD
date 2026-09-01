# Provider Runtime 사용 가이드 — P0.6

## 1. 목적

프로젝트별 Source/Test/Canonical 도구를 SDLC Harness에 연결할 때 Core Skill이나 업무 문서를 수정하지 않고 Adapter 설정만 교체하기 위한 가이드다.

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

예:

```yaml
command: /work
project_context:
  mode: GREENFIELD
  stage: DESIGN
requested_capabilities: []
```

이 경우 Source Provider를 강제로 요구하지 않는다.

개발이 시작되어 Source write/test가 필요해지는 시점부터 해당 Capability를 요청한다.

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

## 6. Provider State

- `AVAILABLE`: 사용 가능
- `DEGRADED`: 제한적으로 사용 가능
- `UNAVAILABLE`: 현재 접근 불가
- `UNCONFIGURED`: Adapter/Connection 미연결
- `DISABLED`: 의도적으로 비활성

Example Registry의 Source/Test는 기본 `UNCONFIGURED`다. 예제 파일이 존재한다는 이유만으로 실제 실행 가능하다고 보지 않는다.

## 7. Write 연결

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

## 8. Test Provider

`test.execute`의 `OK` Response만으로 Verification PASS가 되지 않는다. P0.4 Test Contract와 동일 Source Evidence Set, 실행 Evidence, Required TC 결과가 함께 검증되어야 한다.

## 9. Canonical Registry Provider

`canonical.id.reserve` / `canonical.publish`는 Provider Capability만으로 실행하지 않는다. P0.2 Human/L2 Boundary Decision과 Publish Gate를 먼저 통과해야 한다.

## 10. Adapter 구현 체크리스트

- Provider Type이 Core Enum 중 하나인가?
- Capability 이름이 구현체 명칭이 아니라 기능 의미인가?
- Request ID ↔ Response ID가 보존되는가?
- Provider Revision이 기록되는가?
- Evidence locator가 재현 가능한가?
- 미지원 Operation을 성공으로 반환하지 않는가?
- Source/Test Evidence를 Business Truth로 승격하지 않는가?
- Write가 Read에서 암묵적으로 허용되지 않는가?
- 구현체 고유 필드가 `extensions` 밖의 Core Schema를 바꾸지 않는가?

## 11. 검증 명령

```text
python sdlc/scripts/validate_p06_contracts.py registry sdlc/config/provider-registry.example.yaml
python sdlc/scripts/validate_p06_contracts.py request <provider-request.yaml> --registry <provider-registry.yaml>
python sdlc/scripts/validate_p06_contracts.py response <provider-response.yaml> --request <provider-request.yaml> --registry <provider-registry.yaml>
python sdlc/scripts/route_provider_command.py <provider-registry.yaml> <runtime-context.yaml> -o <runtime-plan.yaml>
python sdlc/scripts/test_p06_contracts.py
```

## 12. 파일럿 샘플 사용 원칙

첨부 요구사항목록과 근태마감 Pilot은 Regression Fixture일 뿐이다.

Core Provider Contract를 변경하려면 최소 다음을 만족해야 한다.

1. 파일럿 업무명/ID/Table/Symbol 없이 설명 가능
2. Greenfield에도 적용 가능
3. 서로 다른 두 개 이상의 기술/도메인 예제로 동일 Capability가 설명 가능
4. 특정 Adapter가 필요한 경우 Core Schema 변경 대신 `extensions` 또는 Project Overlay로 해결
