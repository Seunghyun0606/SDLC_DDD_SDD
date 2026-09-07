# Cursor Adapter — /work

이 파일은 Cursor 전용 진입 Adapter다. SDLC `/work`의 업무 규칙과 실행 계약을 중복 정의하지 않는다.

## Canonical Core Skill

반드시 다음 Core Skill을 Source of Truth로 사용한다.

`@sdlc/agent/skills/work/SKILL.md`

Stage Reference 전체를 미리 읽지 않는다. Core Skill의 Context 최소화 규칙과 `work-context.json`의 `execution_policy.required_semantic_work`에 따라 필요한 Reference만 선택한다.

## Cursor 입력 매핑

일반 사용자는 Target만 지정한다.

```bash
/work --target RQ-001
```

현재 Cursor Agent가 Core Skill의 `INTERACTIVE` Agent 역할을 수행한다. `.sdlc/project.yaml`에서 `agent.execution: HEADLESS`가 명시된 경우에만 Harness가 외부 Provider 경로를 사용한다.

INTERACTIVE 기본 흐름:

1. `python sdlc/scripts/harness.py work --target <TARGET>`로 Work Context를 준비한다.
2. `INTERACTIVE_HANDOFF_READY`를 확인한다. 이 상태를 작업 완료로 표현하지 않는다.
3. `context_path`에서 Target, Change Level, `required_semantic_work`, 필요한 Evidence, 선택 Template만 읽는다.
4. 선택 Artifact와 `stage-result.json`을 작성한다.
5. 실제 Source를 수정하는 L1/L2라면 Requirement Intent → AS-IS Source → Impact 분석을 `pre_write_analysis`로 남긴다.
6. 반환된 finalize command를 실행한다.
7. `APPLIED / IDEMPOTENT / NO_CHANGE / DRY_RUN_VALIDATED` 중 하나가 확인된 경우에만 완료로 보고한다.

## Context 최소화

- `sdlc/agent/skills/work/references/` 전체를 읽지 않는다.
- 모든 Template을 읽지 않는다.
- Customer/PM Projection Template을 내부 구현 작업의 기본 Context에 넣지 않는다.
- 전체 Repository를 LLM으로 먼저 읽지 않고 Target과 관련된 Source symbol/file부터 탐색한다.
- L1/L2라도 Intent/AS-IS/Impact 분석은 생략하지 않되 별도 Stage 문서 생성을 강제하지 않는다.
- L3 이상도 `required_semantic_work`에 필요한 Reference만 읽는다.

명시적 재진입/debug가 필요할 때만 다음 형태를 사용한다.

```bash
python sdlc/scripts/harness.py work --target PGM-001 --stage PROGRAM
python sdlc/scripts/harness.py work --target RQ-001 --stage DESIGN --artifact docs/10_산출물/RQ-001/custom.md
```

일반 사용자는 Tailoring이 Primary Artifact를 선택하므로 `--stage`/`--artifact`를 기본 사용법으로 쓰지 않는다.

## 실행 경계

문서를 작성했다는 사실만으로 완료가 아니다. `/work --finalize`가 다음 경계를 통과해야 한다.

- Target Graph Guard
- Business Truth Guard
- Canonical revision / Git baseline Guard
- Stage Result Validator
- 실제 Source 변경 시 Source write scope + pre-write analysis + Build/Test Guard

문서-only DEVELOPMENT 결과에는 Source Build/Test나 `pre_write_analysis`를 형식적으로 만들지 않는다.

Canonical Delta 지원 Operation은 `UPSERT_ENTITY`, `UPSERT_RELATION`, `ADD_PROVENANCE`다. Source 관찰을 값 변경 없이 연결할 때는 `ADD_PROVENANCE`를 우선하며 이것이 Confirmed Business Truth 변경 권한을 만들지는 않는다.

OPEN은 대기표시가 아니라 해소할 설계 Backlog다. 업무 권위가 필요한 OPEN은 사람의 결정으로, 기술적으로 조사 가능한 OPEN은 Source/설계 Evidence로 해소한다. 상세 절차가 필요할 때만 `.cursor/skills/open-resolve/SKILL.md`를 사용한다.

## v1.9 Tailoring 연결

`Stage / Canonical / Evidence → Tailoring Profile → Human Artifact`

- 내부 기본 Profile: `STANDARD_5`
- 고객 Projection: `CUSTOMER_STANDARD_3`
- PM View: `PM_STANDARD`
- `STAGE_ORIENTED_FULL`: Legacy/Formal compatibility

Customer/PM View는 `GENERATED_VIEW`이며 새 Business Truth를 만들지 않는다. Cursor Adapter가 Stage 이름과 고객사 문서 이름을 1:1로 재정의하지 않는다.

## 금지

- Cursor 자체 동작을 Business Truth 근거로 사용하지 않는다.
- Provider가 없다는 이유로 INTERACTIVE 실행을 실패 처리하지 않는다.
- `INTERACTIVE_HANDOFF_READY`를 완료로 표현하지 않는다.
- 모든 Stage Reference/Template을 선로딩하지 않는다.
- Core Skill/Contract/Validator를 Cursor 전용 규칙으로 재정의하지 않는다.
- OPEN을 근거 없는 추정으로 닫지 않는다.
