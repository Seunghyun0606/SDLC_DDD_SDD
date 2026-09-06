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

Target과 Stage/Artifact는 독립적이다. Harness 관리자 또는 명시적 재진입이 필요한 경우 다음 형태를 지원한다.

```bash
python sdlc/scripts/harness.py work --target PGM-001 --stage PROGRAM
python sdlc/scripts/harness.py work --target ANA001 --stage DESIGN
python sdlc/scripts/harness.py work --target RQ-001 --stage DESIGN --artifact docs/10_산출물/RQ-001/custom.md
```

일반 사용자는 v1.9 Tailoring이 Primary Artifact를 선택하므로 `--stage`/`--artifact`를 기본 사용법으로 쓰지 않는다.

## Agent Stage Result 실행 경계

Stage Agent가 문서를 작성했다는 사실만으로 완료가 아니다. `stage-result.json`은 반드시 Core Validator와 Canonical Apply 경계를 통과해야 한다.

```bash
python sdlc/scripts/validate_agent_stage_result.py --result <stage-result.json> --store sdlc/canonical/store.json
python sdlc/scripts/apply_canonical_delta.py --delta <delta.json> --dry-run
```

실제 `/work --finalize`는 이 검증을 Runtime Guard 안에서 수행한다. 성공 경계는 `validation.status = PASS` 및 `validation.executable = true`이며, Validator가 실패하거나 Target Graph/Business Truth/Canonical revision Guard가 실패하면 적용하지 않는다.

동일 입력에 대한 반복 실행의 의미 차이를 확인할 때는 Validator의 `--compare` 경로와 semantic fingerprint를 사용할 수 있다. 이 비교는 **Agent/LLM 자체가 결정론적임을 증명하는 기능이 아니다**. Timestamp 같은 비의미 필드를 제외하고 실제 생성 결과의 semantic drift를 찾는 검증 보조수단이다.

Canonical Delta의 지원 Operation은 `UPSERT_ENTITY`, `UPSERT_RELATION`, `ADD_PROVENANCE`다. Source 관찰을 값 변경 없이 연결할 때는 `ADD_PROVENANCE`를 우선하며, 이것이 Confirmed Business Truth 변경 권한을 만들지는 않는다.

OPEN은 대기표시가 아니라 해소할 설계 Backlog다. 업무권위가 필요한 OPEN은 사람의 결정으로, 기술적으로 조사 가능한 OPEN은 Source/설계 Evidence로 해소하며 Agent가 근거 없이 채우지 않는다. OPEN 해소 절차가 필요하면 `.cursor/skills/open-resolve/SKILL.md`를 사용한다.

## Canonical 실행 경로

`/work --finalize`가 Stage Result Validator를 통과한 뒤에만 `sdlc/scripts/apply_canonical_delta.py`의 locked/atomic apply 경계를 사용한다. 문서가 작성됐다는 사실이나 Provider command 성공만으로 Canonical 적용 성공을 주장하지 않는다.

## v1.9 Tailoring 연결

내부 Stage는 계속 실행 의미를 보존한다. 다만 일반 사용자가 검토할 문서는 `.sdlc/project.yaml`의 Artifact Profile이 결정한다.

`Stage / Canonical / Evidence → Tailoring Profile → Human Artifact`

따라서 Cursor Adapter가 Stage 이름과 고객사 문서 이름을 1:1로 재정의하지 않는다.

## 금지

- Cursor 자체 동작을 Business Truth 근거로 사용하지 않는다.
- Provider가 없다는 이유로 INTERACTIVE 실행을 실패 처리하지 않는다.
- `INTERACTIVE_HANDOFF_READY`를 Canonical 적용 성공으로 표현하지 않는다.
- Core Skill/Contract/Validator를 Cursor 전용 규칙으로 재정의하지 않는다.
- OPEN을 근거 없는 추정으로 닫지 않는다.
