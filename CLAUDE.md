# Claude Code Adapter — SDLC Harness

이 파일은 Claude Code용 Host Adapter다. SDLC 업무 규칙을 별도로 복제하지 않는다.

## Core Source of Truth

`work` 요청을 받으면 먼저 다음을 읽는다.

- `sdlc/agent/skills/work/SKILL.md`
- 선택 Stage에 해당하는 `sdlc/agent/skills/work/references/<stage>.md`
- `.sdlc/project.yaml`

사용자가 `/work --target RQ-001`, `work --target RQ-001`, 또는 동일한 자연어 의도를 요청하면 위 Core Skill을 수행한다.

기본 `agent.execution`은 `INTERACTIVE`다. 이 경우 현재 Claude Code 세션 자체가 Stage Agent이며 별도 LLM/Provider subprocess를 다시 실행하지 않는다.

INTERACTIVE 실행:

1. `python sdlc/scripts/harness.py work --target <TARGET> ...`
2. `INTERACTIVE_HANDOFF_READY` 확인
3. 반환된 `work-context.json`과 Core Reference/Template을 근거로 Artifact 작성
4. 같은 run directory에 `stage-result.json` 작성
5. Harness finalize 실행
6. `APPLIED / IDEMPOTENT / NO_CHANGE / DRY_RUN_VALIDATED`일 때만 완료 보고

`agent.execution: HEADLESS`이면 Harness가 설정된 Provider를 실행하게 하고 Claude Code 세션이 그 Provider 실행을 암묵적으로 대체하지 않는다.

## Guard

- Business Truth를 추정으로 확정하지 않는다.
- Source Evidence와 고객/업무 확정을 구분한다.
- Target Graph/Protected Branch/Canonical Revision Guard를 우회하지 않는다.
- Prepare 상태를 완료 상태로 표현하지 않는다.
- Host 고유 지침과 Core SDLC Contract가 충돌하면 SDLC Contract/Validator의 안전 경계를 우선한다.
