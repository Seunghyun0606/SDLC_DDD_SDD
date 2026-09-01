# Provider Adapter Conformance Contract — P0.7

상태: `ACTIVE_P0_CANDIDATE`

## 목적

P0.6 Provider Boundary를 실제 Adapter 구현과 연결하면서 Core Stage/Skill을 특정 Tool, 업무도메인, 언어, Framework에 종속시키지 않는다.

Reference Adapter는 제품 기능이 아니라 **교체 가능한 Adapter의 최소 동작 예시**다.

## Adapter Protocol

각 Adapter module은 다음 두 함수를 제공한다.

```text
describe() -> provider descriptor
invoke(provider_request, adapter_config) -> provider_response
```

`describe()` 필수:
- provider_id
- provider_type
- provider_state
- mode
- capabilities
- adapter_version

`invoke()`는 P0.6 `provider-request.yaml`과 `provider-response.yaml` Envelope를 그대로 사용한다.

## Conformance 필수 규칙

1. 요청한 operation이 `describe().capabilities`에 없으면 성공을 반환하지 않는다.
2. `request_id`, `provider_type`, `operation` correlation을 유지한다.
3. Provider Evidence는 locator와 revision을 가진다.
4. Source/Test 관찰을 Business Truth `CONFIRMED`로 승격하지 않는다.
5. Tool 고유 필드는 `extensions` 또는 `outputs`에 둔다.
6. Partial/Timeout/Error를 빈 `OK`로 변환하지 않는다.
7. Adapter가 바뀌어도 Core Stage Input Pack/Skill/Router Schema는 변경하지 않는다.

## Provider 상태와 업무 결과 분리

Provider `status`는 Adapter/Tool 호출 자체의 상태다.

- `OK`: Adapter 호출 완료. 업무 결과 성공을 뜻하지 않는다.
- `PARTIAL`: 제한/누락이 있으나 Evidence 일부 확보.
- `BLOCKED`: 실행 전제조건 부족, timeout, 권한/환경 차단 등.
- `ERROR`: Adapter 자체 오류 또는 계약 위반.

예: `test.execute` 프로세스가 정상 실행되고 assertion이 실패했다면 Provider는 `OK`, output의 `test_status`는 `FAILED`다.

## Timeout / Retryable

Adapter는 timeout을 무한대기하지 않는다.

- timeout은 `BLOCKED`
- `open_items`에 `ADAPTER_TIMEOUT`
- 일시적 재실행 가능성이 있으면 `retryable: true`
- retry 횟수/백오프 정책은 Adapter 내부가 아닌 Runtime 정책에서 관리

Reference Adapter는 자동 retry를 수행하지 않는다.

## Reference Source Adapter

`local_filesystem_source`는 범용 파일시스템 Snapshot/Read/Search/Diff만 제공한다.

- language/framework/database를 가정하지 않는다.
- root 밖 path traversal을 금지한다.
- file count/byte limit을 넘으면 `PARTIAL`로 종료한다.
- Binary/읽기불가 파일은 warning 또는 PARTIAL evidence로 남긴다.
- Source Evidence는 `OBSERVED`다.

## Reference Test Adapter

`subprocess_test`는 shell 없이 argv list를 실행한다.

- `shell=True` 금지
- command는 list 형식만 허용
- timeout 필수 상한 적용
- stdout/stderr 크기 제한
- exit code 0 → `test_status: PASSED`
- exit code != 0 → `test_status: FAILED`
- process 완료 자체는 Provider `OK`
- timeout/command not found → Provider `BLOCKED`

이 Adapter는 production sandbox가 아니다. 실제 고객 환경에서는 별도 Test Provider/Container/CI Adapter로 교체한다.

## Conformance Harness

Harness는 Adapter 구현에 대해 다음을 검증한다.

- descriptor validity
- advertised capability exact match
- request/response correlation
- Provider Evidence truth/locator/revision
- success
- partial
- unsupported operation
- timeout
- tool/test failure
- unavailable input
- implementation-specific extension isolation

## Anti-overfitting

Core Adapter Protocol/Harness/Reference Adapter는 파일럿 요구사항 ID, 업무명, 특정 고객 Table/Symbol을 포함하지 않는다.

Conformance는 최소 다음 종류의 독립 사례를 포함한다.

- generic text/code source snapshot/search
- generic source diff
- generic passing subprocess test
- generic failing subprocess test
- timeout
- unsupported capability

파일럿 요구사항은 필요 시 별도 regression fixture로만 사용한다.

## 완료 조건

P0.7은 다음을 만족하면 완료된다.

1. 최소 Reference Source Adapter 존재
2. 최소 Reference Test Adapter 존재
3. 동일 P0.6 Envelope 사용
4. Conformance runner 존재
5. positive/negative/timeout/failure case 존재
6. Adapter 교체에 Core Router/Stage Contract 수정이 필요하지 않음
7. Pilot-specific token이 Core P0.7 구현에 없음
