# Command Runtime Integration — P0.9 + Structural Redesign v1

상태: `ACTIVE_STRUCTURAL_REDESIGN_V1`

## 목적

사용자 표면은 `/work`, `/change`, `/check`만 유지하면서 Stage Resolver가 결정한 Capability와 P0.6 Router Plan, P0.8 Provider Invocation을 실제 한 실행 흐름으로 결합한다.

## Pipeline

```text
Stage Input Pack
→ Stage Execution Plan
→ Command Context
→ Required / Optional Capabilities
→ Provider Runtime Plan
→ Unblocked capability별 Provider Request
→ P0.8 Invocation Journal
→ Provider Responses
→ Command Runtime Result
```

## 원칙

- Command 이름으로 Adapter 구현체를 hardcode하지 않는다.
- Caller/Agent가 Required Capability를 임의로 만들지 않는다. `stage-routing.yaml`이 결정한다.
- Router는 capability/provider 선택까지만 한다.
- 실제 invoke/retry/recovery는 P0.8에 위임한다.
- `/check`처럼 외부 capability가 필요 없는 경우 local COMPLETE 가능하다.
- Optional capability missing/unavailable → `OPEN + PARTIAL`, 다른 작업 계속 가능.
- Required capability missing/unavailable → 해당 capability/action만 `ACTION_REQUIRED`.
- 하나의 Action이 Guard되어도 독립된 Read/Analysis capability는 실행할 수 있다.
- Human Action은 `blocks_action=true`이며 capability/action scope가 일치할 때만 해당 실행을 Guard한다.
- `UNKNOWN_AFTER_WRITE` 하나라도 있으면 전체 결과는 `RECOVERY_REQUIRED`다.
- PARTIAL Provider 결과가 있으면 전체 `PARTIAL`이며 Release Ready로 승격하지 않는다.
- Side-effect capability는 Stage Pack의 `execution.requested_actions`에 명시적으로 요청된 경우에만 Runtime에 올라간다.

## OPEN / Action Scope

```yaml
open_id: OPEN-001
blocks_reasoning: false
blocks_action: true
action_scopes: [source.write]
```

위 OPEN은 `source.write`만 막는다. `source.object.read`, 분석, 문서 초안은 계속 가능하다.

Provider OPEN도 동일하다.

- Required provider capability → `blocks_action: true`
- Optional provider capability → `blocks_action: false`

## Write Proof

Write capability에는 capability별 다음이 필요하다.

```yaml
expected_revision:
idempotency_key:
permission_proof_ref:
```

없는 값은 `WRITE_PROOF_REQUIRED` Human Action으로 변환한다.

Write dispatch 이후 응답이 불명확하면 P0.8의 `UNKNOWN_AFTER_WRITE`를 유지하며 자동 재시도하지 않는다.

## Result States

- `COMPLETE`
- `PARTIAL`
- `ACTION_REQUIRED`
- `RECOVERY_REQUIRED`
- `INVALID`

`ACTION_REQUIRED`는 다른 독립 capability가 이미 성공적으로 수행되지 않았다는 의미가 아니다. `partial_progress_performed`와 `invocations/skipped_invocations`를 함께 확인한다.

## Truth Guard

Command Runtime은 Provider Response/E2E Status를 집계할 뿐 Business Boundary, Canonical ID, Test PASS를 생성하지 않는다.

## Anti-overfitting

Capability input은 `capability_inputs`로 주입하며 특정 Requirement/도메인/Stack별 field를 Command Core schema에 추가하지 않는다.
