# Command Runtime Integration — P0.9

상태: `ACTIVE_P0_CANDIDATE`

## 목적

사용자 표면은 `/work`, `/change`, `/check`만 유지하면서 P0.6 Router Plan과 P0.8 Provider Invocation을 실제 한 실행 흐름으로 결합한다.

## Pipeline

```text
Command Context
→ Required Capabilities
→ Provider Runtime Plan
→ capability별 Provider Request
→ P0.8 Invocation Journal
→ Provider Responses
→ Command Runtime Result
```

## 원칙

- Command 이름으로 Adapter 구현체를 hardcode하지 않는다.
- Router는 capability/provider 선택까지만 한다.
- 실제 invoke/retry/recovery는 P0.8에 위임한다.
- `/check`처럼 외부 capability가 필요 없는 경우 local COMPLETE 가능하다.
- missing/unavailable capability는 `ACTION_REQUIRED`로 남긴다.
- Human Action이 있어도 `blocks_action: false`인 작업은 병행 가능하다.
- `UNKNOWN_AFTER_WRITE` 하나라도 있으면 전체 결과는 `RECOVERY_REQUIRED`다.
- PARTIAL Provider 결과가 있으면 전체 `PARTIAL`이며 Release Ready로 승격하지 않는다.

## Result States

- `COMPLETE`
- `PARTIAL`
- `ACTION_REQUIRED`
- `RECOVERY_REQUIRED`
- `INVALID`

## Truth Guard

Command Runtime은 Provider Response/E2E Status를 집계할 뿐 Business Boundary, Canonical ID, Test PASS를 생성하지 않는다.

## Anti-overfitting

Capability input은 `capability_inputs`로 주입하며 특정 Requirement/도메인/Stack별 field를 Command Core schema에 추가하지 않는다.
