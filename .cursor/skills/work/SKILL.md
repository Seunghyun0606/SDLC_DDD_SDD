# Cursor Adapter — /work

이 파일은 Cursor 전용 진입 Adapter다. SDLC `/work`의 업무 규칙과 실행 계약을 중복 정의하지 않는다.

## Canonical Core Skill

반드시 먼저 다음 파일을 읽고 그 내용을 Source of Truth로 수행한다.

`@sdlc/agent/skills/work/SKILL.md`

Stage별 세부 Reference는 다음 Core 경로를 사용한다.

`@sdlc/agent/skills/work/references/`

## Cursor 입력 매핑

사용자가 다음과 같이 입력하면:

`/work --target RQ-001 [--stage DESIGN] [--artifact <path>]`

현재 Cursor Agent가 Core Skill의 **INTERACTIVE** Stage Agent 역할을 수행한다. `.sdlc/project.yaml`에서 `agent.execution: HEADLESS`가 명시된 경우에만 Harness가 외부 Provider 실행 경로를 사용한다.

INTERACTIVE 기본 흐름:

1. `python sdlc/scripts/harness.py work --target <TARGET> ...`로 Work Context를 준비한다.
2. 결과가 `INTERACTIVE_HANDOFF_READY`인지 확인한다. 이 상태를 Stage 완료로 표현하지 않는다.
3. 반환된 `context_path`, Core Stage Reference, Template을 읽는다.
4. 선택 Artifact와 `stage-result.json`을 작성한다.
5. 반환된 finalize command 또는 `python sdlc/scripts/harness.py work --target <TARGET> --finalize --run-dir <RUN-DIR>`를 실행한다.
6. `APPLIED / IDEMPOTENT / NO_CHANGE / DRY_RUN_VALIDATED` 중 하나가 확인된 경우에만 완료로 보고한다.

## 금지

- Cursor 자체 동작을 Business Truth 근거로 사용하지 않는다.
- Provider가 없다는 이유로 INTERACTIVE 실행을 실패 처리하지 않는다.
- `INTERACTIVE_HANDOFF_READY`를 Canonical 적용 성공으로 표현하지 않는다.
- Core Skill/Contract/Validator를 Cursor 전용 규칙으로 재정의하지 않는다.
