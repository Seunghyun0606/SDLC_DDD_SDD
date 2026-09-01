# Source Write Capability Contract — P0 Runtime Core

상태: `ACTIVE_P0_REDESIGN`

## 1. 목적

실제 Source 변경을 특정 GitHub/GitLab/MCP 구현에 종속시키지 않고 Provider Capability로 표준화한다.

표준 Side-effect Capability:

`source.patch.apply`

P0 Runtime Core는 Source Write Adapter를 기본 제공하지 않는다. Project가 명시적으로 연결한 READ_WRITE Source Provider만 이 Capability를 실행할 수 있다.

## 2. 기본 정책

- 기본 Provider State: `DISABLED`
- 기본 Development Mode: `PROPOSAL_ONLY`
- Source Read Provider와 Source Write Provider는 분리 가능하다.
- `/work` DEVELOPMENT에서 자동 실행하지 않는다.
- 실행 Context가 `requested_side_effect_capabilities: [source.patch.apply]`를 명시해야 한다.
- Stage Routing이 해당 Side-effect Capability를 허용해야 한다.
- Provider Runtime Write Guard를 모두 통과해야 한다.

## 3. Required Write Proof

Provider Request의 Write에는 다음이 필수다.

- `expected_revision`
- `idempotency_key`
- `permission_proof_ref`

`expected_revision` 의미:

- Brownfield 기존 Artifact 변경: 현재 확인된 Source Revision/Hash
- Greenfield 신규 Artifact 생성: `ABSENT` 또는 Adapter가 계약한 Non-existence Revision Token

Adapter는 expected revision이 실제 Target 상태와 다르면 Write를 수행하지 않고 `BLOCKED`를 반환해야 한다.

## 4. Patch Payload

구현체별 Patch 표현은 `provider_request.extensions`에 둔다.

Core는 특정 Patch Format을 강제하지 않는다.

권장 공통 의미:

```text
target locator
expected revision
change/patch payload
scope
post-write verification request
```

Adapter-specific 필드는 Core Config/Skill에 복제하지 않는다.

## 5. 성공 Response

성공 Response는 최소 다음 Evidence를 제공해야 한다.

- Provider Revision after write
- Changed Target Locator
- Before Revision
- After Revision
- Applied change/patch identity

가능하면 다음도 제공한다.

- post-write diff
- changed symbol/data/interface refs

이 Evidence는 `OBSERVED`이며 Business Truth가 아니다.

## 6. Failure / Recovery

Write Request는 자동 재시도하지 않는다.

Adapter 호출 도중 결과가 불명확하면 기존 Invocation Recovery Contract에 따라:

`UNKNOWN_AFTER_WRITE`

로 전환한다.

그 상태에서는 같은 Idempotency Key를 임의 재전송하지 않고 Recovery Evidence를 먼저 확인한다.

## 7. 금지

- Source Revision 확인 없는 Brownfield overwrite
- Permission Proof 없는 Write
- Idempotency Key 없는 Write
- Ambiguous Target 자동 선택
- Provider `PARTIAL/UNKNOWN` 결과를 성공으로 간주
- Source Diff를 Business Rule 확정 근거로 자동 승격
- Adapter 고유 Patch Syntax를 Core Stage Skill에 하드코딩

## 8. DEVELOPMENT Handoff

실제 Write가 실행되지 않으면:

`SOURCE_CHANGE_PROPOSAL`

을 생성하고 다음 상태를 명시한다.

`SOURCE_WRITE_NOT_EXECUTED`

실제 Write가 성공하면:

`SOURCE_CHANGE_RESULT + post-write Evidence + Reverse Sync Candidate`

를 생성한다.

실제 Write가 `UNKNOWN_AFTER_WRITE`이면 DEVELOPMENT를 성공 처리하지 않고 Recovery Action을 Handoff한다.
