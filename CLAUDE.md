# Claude Code Adapter — SDLC Harness

이 파일은 Claude Code용 Host Adapter다. SDLC 업무 규칙을 별도로 복제하지 않는다.

## Core Source of Truth

`work` 요청을 받으면 먼저 다음을 읽는다.

- `sdlc/agent/skills/work/SKILL.md`
- 선택 Stage에 해당하는 `sdlc/agent/skills/work/references/<stage>.md`
- `sdlc/agent/skills/work/references/project-development-context.md`
- `sdlc/agent/skills/work/references/human-language.md`
- `sdlc/design/contracts/human-facing-language-contract.json`
- `.sdlc/project.yaml`
- `sdlc/custom/project/rules/`의 현재 작업 적용 규칙
- `sdlc/custom/project/standards/`의 현재 Stage/기술/변경 범위 관련 가이드
- 현재 RQ/PGM이 특정 Domain에 속하면 `sdlc/custom/domain/<domain>/rules/`, `standards/`

`rules/`는 현재 작업에 적용되면 강제 규칙으로 취급하고, `standards/`는 관련 개발/검증 기준으로 사용한다. 모든 standards를 무조건 선로딩하지 않고 필요한 문서만 선택한다.

사용자가 `/work --target RQ-001`, `work --target RQ-001`, 또는 동일한 자연어 의도를 요청하면 위 Core Skill을 수행한다.

기본 `agent.execution`은 `INTERACTIVE`다. 이 경우 현재 Claude Code 세션 자체가 Stage Agent이며 별도 LLM/Provider subprocess를 다시 실행하지 않는다.

INTERACTIVE 실행:

1. `python sdlc/scripts/harness.py work --target <TARGET> ...`
2. `INTERACTIVE_HANDOFF_READY` 확인
3. 반환된 `work-context.json`, Core Reference/Template, Project rules/standards를 근거로 Artifact 작성
4. 같은 run directory에 `stage-result.json` 작성
5. Harness finalize 실행
6. `APPLIED / IDEMPOTENT / NO_CHANGE / DRY_RUN_VALIDATED`일 때만 완료 보고

`agent.execution: HEADLESS`이면 Harness가 설정된 Provider를 실행하게 하고 Claude Code 세션이 그 Provider 실행을 암묵적으로 대체하지 않는다.

## 프로젝트 개발 가이드 경계

- 고객이 제공한 원본 개발표준 PDF/DOCX는 `br-input/originals/`에 근거로 보존할 수 있다.
- 반복 적용할 확정 개발표준은 `sdlc/custom/project/standards/`에 정리한다.
- 반드시 지켜야 하는 Architecture 금지사항/Tool 사용 강제 규칙은 `sdlc/custom/project/rules/`에 둔다.
- `rules/`와 `standards/`가 충돌하면 `rules/`를 우선하되 충돌을 숨기지 않는다.
- 개발표준으로 업무 정책을 임의 생성하거나 변경하지 않는다.

## 새 RQ 간편추가

사용자가 프로젝트 진행 중 새 요구사항 한두 건을 자연어로 추가해 달라고 하면 `sdlc/agent/skills/rq-add/SKILL.md`를 따른다.

```text
새 RQ 추가해줘. 승인 완료된 근무계획은 일반 사용자가 수정할 수 없게 해줘.
```

Agent는 원문을 보존하고 다음 공식 Runtime을 사용한다.

```bash
python sdlc/scripts/harness.py rq-add --title "<짧은 제목>" --request "<사용자 원문>"
```

기존 RQ의 의미 변경은 `/change`, 대량 요구사항은 `/intake`로 처리한다.

## 사람에게 보여주는 표현

HITL 질문과 사람용 문서는 쉬운 한국어를 우선한다.
내부 상태 코드와 Framework 용어는 Runtime/Contract 안에서는 유지할 수 있지만 사용자에게 그대로 이해하도록 요구하지 않는다.

예:
- `DEFERRED` → `보류`
- `SOURCE_BLOCK` → `개발 전 확인 필요`
- `Recheck At` → `다시 확인할 시점`
- `Human Decision Queue` → `추가 확인이 필요한 사항`
- `Canonical` → `기준 정보`
- `Projection` → `생성 문서`
- `영속적` → `DB에 저장되어 계속 유지되는`

사용자에게 질문할 때는 내부 코드보다 왜 확인이 필요한지, 현재 확인된 내용, 결정할 내용, 답하지 못할 때의 처리, 다시 확인할 시점을 먼저 설명한다.

## Guard

- Business Truth를 추정으로 확정하지 않는다.
- Source Evidence와 고객/업무 확정을 구분한다.
- Target Graph/Protected Branch/Canonical Revision Guard를 우회하지 않는다.
- Prepare 상태를 완료 상태로 표현하지 않는다.
- Host 고유 지침과 Core SDLC Contract가 충돌하면 SDLC Contract/Validator의 안전 경계를 우선한다.
