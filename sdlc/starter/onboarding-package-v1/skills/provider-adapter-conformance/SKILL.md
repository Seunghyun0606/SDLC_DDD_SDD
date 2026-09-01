# Skill — Provider Adapter Conformance

## Purpose

새 Source/Test/Canonical/Deployment 등 Provider Adapter가 P0.6 Runtime Boundary를 준수하는지 검증한다. 특정 고객 업무나 기술스택을 Core Contract에 추가하지 않는다.

## Required Input

- Provider Adapter module 또는 실행 가능한 Adapter endpoint
- Provider descriptor
- 지원 capability 목록
- generic conformance case
- P0.6 Provider Request/Response Contract

## Optional Input

- 실제 고객 regression fixture
- timeout/retry 정책
- project-specific extensions

## Precondition

- Adapter가 `describe()`와 `invoke()` 또는 동등한 protocol을 제공한다.
- 지원 operation이 capability 문자열로 표현된다.
- 실제 credential/secret은 conformance fixture에 저장하지 않는다.

## Retrieval Strategy

1. Core Provider Contract
2. Adapter descriptor
3. generic fixture
4. Adapter-specific extension
5. 고객 Pilot은 마지막 regression 검증에만 사용

## Atomic Steps

1. descriptor 필수값 확인
2. capability exact match 확인
3. generic Provider Request 생성
4. Adapter invoke
5. Provider Response correlation 검증
6. Evidence truth/locator/revision 검증
7. success/failure/partial/timeout/unavailable case 실행
8. Tool 결과와 Provider 상태가 분리되는지 확인
9. Core Schema에 Adapter 고유 필드가 추가되지 않았는지 확인
10. Pilot 고유 토큰이 Core Adapter/Harness에 없는지 확인
11. conformance result 생성

## Decision Rules

- Adapter 교체만으로 Core Router/Stage Schema 변경이 필요하면 FAIL
- 미지원 operation을 OK로 반환하면 FAIL
- timeout을 빈 성공으로 반환하면 FAIL
- TEST assertion 실패는 Provider ERROR로 분류하지 않는다
- Source/Test Evidence를 Business Truth CONFIRMED로 올리면 FAIL
- 기술 고유값은 `extensions` 또는 output 내부에서만 허용
- Pilot 요구사항은 regression evidence일 뿐 contract definition 근거가 아니다

## Output Schema

- `PROVIDER_CONFORMANCE_RESULT`
- case별 provider status
- failure reason
- adapter descriptor snapshot
- generic/pilot regression 구분

## Quality Check

- generic 사례만으로 주요 상태를 검증했는가?
- Greenfield/Brownfield 중 하나에만 맞춰지지 않았는가?
- Source/Test Provider 상태와 실제 결과가 분리됐는가?
- Adapter-specific field가 Core Envelope를 오염시키지 않았는가?
- timeout/path scope/subprocess 안전장치가 있는가?

## Alert Conditions

- CAPABILITY_MISMATCH
- RESPONSE_CORRELATION_BROKEN
- ADAPTER_TIMEOUT
- PROVIDER_RESULT_CONFLATION
- CORE_SCHEMA_POLLUTION
- PILOT_OVERFITTING
- UNBOUNDED_SOURCE_SCOPE
- UNSAFE_PROCESS_EXECUTION

## Stop Conditions

- required conformance case가 모두 값 또는 명시적 BLOCKED 상태를 가짐
- 다음 검증이 실제 credential/runtime을 요구함
- Adapter 교체에 Core 변경이 필요함

## Escalation Conditions

- credential/permission integration → Engineering/L3
- production sandbox/secret handling → Security/Platform
- Business Truth interpretation → L2/Human

## Do Not

- 고객 업무명으로 capability 정의
- 특정 Table/API/Symbol로 Provider Type 정의
- Adapter별 별도 Stage Schema 생성
- timeout 무시
- shell string 실행을 Reference Test Adapter 기본으로 사용
- 실제 실행하지 않은 test를 PASS 처리

## Example

정상:
`test.execute`가 subprocess exit code 4를 받아 Provider `OK` + output `test_status=FAILED`를 반환한다.

잘못:
테스트 실패를 Provider `ERROR`로 바꿔 Runtime 장애처럼 보이게 한다.
