# Runtime Invocation / Recovery Contract — P0.8

상태: `ACTIVE_P0_CANDIDATE`

## 목적

P0.6 Provider Boundary와 P0.7 Adapter를 실제 호출하는 공통 실행 계층을 정의한다. 특정 업무, 언어, 프레임워크, CI 제품을 가정하지 않는다.

## Pipeline

```text
Validated Provider Request
→ Exact Provider Selection
→ Invocation Journal STARTED
→ Adapter invoke()
→ Provider Response Validation
→ Journal terminal state
→ Retry / Continue / Stop / Recovery
```

## Journal States

- `PLANNED`
- `STARTED`
- `SUCCEEDED`
- `PARTIAL`
- `BLOCKED`
- `FAILED`
- `UNKNOWN_AFTER_WRITE`

각 attempt는 request_id, provider_id, capability, attempt_no, started_at, finished_at, response_status, retryable, error/open item을 보존한다.

## Retry Rules

### Read
- response `BLOCKED/ERROR`이면서 `retryable: true`인 경우에만 자동 재시도 가능
- 최대 attempt는 config로 제한
- `OK/PARTIAL`은 자동 재시도하지 않음
- 동일 request_id와 target/capability를 유지

### Write
- 기본 자동 재시도 금지
- write dispatch 이후 정상 Provider Response를 받지 못하면 `UNKNOWN_AFTER_WRITE`
- 다음 조건이 모두 증명되기 전에는 재실행하지 않음:
  1. 동일 idempotency key
  2. Provider가 idempotent write/recovery를 지원
  3. 이전 write의 적용 여부를 조회 가능한 recovery evidence
  4. expected revision 충돌 없음
- `UNKNOWN_AFTER_WRITE`는 Human/Engineering recovery action으로 넘긴다.

## PARTIAL Rules

`PARTIAL`은 실패가 아니다. 확보한 Evidence는 downstream reasoning에 사용할 수 있다. 그러나 다음은 금지한다.

- PARTIAL Evidence만으로 Business Truth 확정
- PARTIAL 상태에서 Release Ready 승격
- write target completeness가 필요한 경우 자동 write

## Failure Separation

업무/Test 결과 실패와 Adapter 실패를 분리한다.

- Provider `OK` + domain/test outcome `FAILED` → Provider invocation 성공
- Provider `BLOCKED/ERROR` → 실행 인프라/Capability/Adapter 문제

## Crash / Unknown Rules

- Read 호출 중 runner crash → 해당 attempt `FAILED` 또는 재시도 가능 상태
- Write 호출을 adapter에 전달한 뒤 runner crash/response loss → `UNKNOWN_AFTER_WRITE`
- UNKNOWN 상태를 성공/실패 어느 쪽으로도 추측하지 않는다.

## Evidence / Correlation

- Provider Response는 P0.6 Request와 correlation되어야 한다.
- Evidence truth/locator/revision은 P0.6 Validator를 그대로 사용한다.
- Journal은 Provider 결과를 수정하지 않고 실행 메타데이터만 추가한다.

## Stop Conditions

- OK → `SUCCEEDED`
- PARTIAL → `PARTIAL`
- non-retryable BLOCKED → `BLOCKED`
- ERROR retry exhausted → `FAILED`
- write response unknown → `UNKNOWN_AFTER_WRITE`

## Anti-overfitting

Core runtime에는 Pilot Requirement ID, 업무명, 특정 Table/Symbol, 특정 언어/Framework를 넣지 않는다. Adapter-specific 설정은 registry `extensions` 또는 invocation config로 주입한다.
