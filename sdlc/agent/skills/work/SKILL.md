# SDLC Core Skill — work

이 파일은 특정 IDE나 Agent 제품에 종속되지 않는 `/work`의 **Core Source of Truth**다.
Cursor, Codex, Claude Code 또는 다른 Repository-capable Agent는 각 Host Adapter에서 이 파일을 읽고 동일한 절차를 수행한다.
Host별 명령어 문법이나 Skill 검색 방식은 달라도 아래 Runtime/Contract/Guard는 바꾸지 않는다.

## 1. 실행 모드

프로젝트의 Human-maintained 설정은 `.sdlc/project.yaml` 하나다.

- `agent.execution`이 없으면 `INTERACTIVE`가 기본이다.
- `INTERACTIVE`: 현재 대화/IDE/CLI 세션을 수행 중인 Agent가 Stage Agent다. 별도 Provider subprocess를 실행하지 않는다.
- `HEADLESS`: Harness Runtime이 설정된 외부 Provider command를 실행한다.
- IDE/Agent 제품명(Cursor/Codex/Claude 등)은 프로젝트 업무 Config가 아니다.

`INTERACTIVE`와 `HEADLESS`의 차이는 **Agent를 누가 시작하는가**뿐이다. Stage Result, Target Graph Guard, Business Truth Guard, Canonical Delta/Validator는 동일하다.

## 2. 사용자 진입

자연어 또는 Host가 지원하는 명령 형태로 다음 의도를 받을 수 있다.

- `work --target RQ-001`
- `/work --target RQ-001`
- `RQ-001 다음 단계 작업해줘`

Target ID와 Stage/Artifact는 독립적이다. 사용자가 `--stage` 또는 `--artifact`를 명시할 수 있으나, 이것이 상위 Requirement/Business Truth 변경 권한을 의미하지 않는다.
확정 업무 사실 자체를 바꾸려는 요청은 `/change`가 우선이다.

## 3. 공통 계획 단계

항상 Harness Runtime을 사용해 다음을 결정한다.

1. Canonical Store와 Target 확인
2. Target 중심 relation graph 구성
3. Stage 선택
4. Artifact 선택
5. Stage Reference / Template / Project Context 결합
6. Git/Canonical baseline 확인
7. 해당 실행모드에 따른 Agent handoff

Stage 선택 우선순위:

1. 사용자 `--stage`
2. 기존 `--artifact`의 Stage metadata
3. Target Canonical provenance의 마지막 Stage 다음 단계
4. Target type 기본 Stage
5. 판별할 수 없으면 추정하지 않고 명시적 Stage 요구

기본 Stage 흐름:

`INTAKE → DECOMPOSE → CLARIFY → PROCESS → DISCOVERY → IMPACT → DESIGN → PROGRAM → DEVELOPMENT → TEST → VERIFY → KNOWLEDGE_PROMOTION`

Delivery Profile에 따라 활성 Stage는 줄어들 수 있다.

## 4. INTERACTIVE 실행

현재 Agent가 이미 실행 중이므로 Provider를 다시 호출하지 않는다.

### 4.1 Prepare

공식 진입은 다음과 같다.

```bash
python sdlc/scripts/harness.py work --target <TARGET-ID> [--stage <STAGE>] [--artifact <PATH>]
```

INTERACTIVE에서는 Runtime이 즉시 Stage 완료를 주장하지 않는다. 다음을 생성하고 `INTERACTIVE_HANDOFF_READY`를 반환한다.

- `work-context.json`
- 선택된 Artifact 경로
- `stage-result.json` 예정 경로
- Git/Canonical baseline
- Target Graph와 허용된 변경 범위

### 4.2 현재 Agent가 수행할 작업

1. 반환된 `work-context.json`을 읽는다.
2. `selection.template_path`, `selection.reference_path`, Project Context, Canonical Target/Graph를 근거로 Artifact를 작성한다.
3. 모르는 업무 사실을 발명하지 않는다.
4. 사용자/Source/결정 근거의 Truth Class를 구분한다.
5. 같은 run directory의 `stage-result.json`을 작성한다.
6. finalize를 실행한다.

### 4.3 Finalize

```bash
python sdlc/scripts/harness.py work --target <TARGET-ID> --finalize --run-dir <RUN-DIR>
```

Finalize 전에는 Canonical 적용 성공으로 간주하지 않는다.

Runtime은 다음을 fail-closed로 검사한다.

- Prepare 이후 Git HEAD/branch가 바뀌지 않았는가
- Prepare 당시 이미 dirty였던 파일도 fingerprint 기준으로 추가 변경을 추적했는가
- 허용 범위 밖 파일을 수정하지 않았는가
- Stage / Artifact가 Plan과 정확히 일치하는가
- Canonical revision이 stale하지 않은가
- Target Graph 밖 기존 Entity를 수정하지 않았는가
- 확정 Business Truth 변경 권한을 우회하지 않았는가
- Stage Result Validator가 PASS + executable인가
- DEVELOPMENT면 필요한 build/test가 통과하는가

Interactive 실패 시 Harness가 사용자의 기존 작업물을 자동 rollback하지 않는다. 대신 Canonical 적용을 중지하고 `manual_recovery_required`를 명시한다.

## 5. HEADLESS 실행

HEADLESS에서는 `.sdlc/project.yaml`에 Provider command가 있어야 한다.

예:

```yaml
agent:
  execution: HEADLESS
  provider:
    command:
      - python
      - path/to/provider_adapter.py
      - --context
      - "{context_path}"
      - --result
      - "{result_path}"
```

Harness는 기존 `sdlc/scripts/work_handoff.py` → `run_work.py` 경계를 통해 Provider subprocess를 실행한다.
Provider는 Artifact와 Stage Result를 만든다. Provider 실행 성공 자체가 Stage 성공은 아니며 동일 Validator/Canonical Guard를 통과해야 한다.

## 6. Stage Result Contract

최소 Envelope:

```json
{
  "schema_version": 1,
  "stage": "DESIGN",
  "artifact_path": "docs/10_산출물/RQ-001/...md",
  "canonical_delta": {
    "schema_version": 1,
    "delta_id": "WORK-RQ-001-DESIGN-001",
    "base_revision": 10,
    "stage": "DESIGN",
    "source_artifact": "docs/10_산출물/RQ-001/...md",
    "operations": []
  },
  "quality_gate": {
    "status": "PASS",
    "failures": []
  },
  "alerts": [],
  "uncertainty": []
}
```

문서 표현만 바뀌고 Canonical 의미 변화가 없으면 억지 Entity update를 만들지 않는다.

```json
{
  "operations": [],
  "no_change_reason": "문서 표현만 수정하고 Canonical 의미는 변경하지 않음"
}
```

## 7. 공통 Guard

### Target Graph Guard

- 기존 Entity 수정은 Target 중심 Graph 또는 사용자가 지정한 Artifact가 실제 참조하는 범위로 제한한다.
- Graph 밖 기존 Entity 수정은 `OUTSIDE_TARGET_GRAPH_MUTATION`으로 차단한다.
- 새 Entity도 relation endpoint와 Evidence 규칙을 따라야 한다.

### Business Truth Guard

- Source 관찰은 `OBSERVED`이며 고객/업무 확정과 다르다.
- Agent의 설계 경험은 Proposal이지 Business Truth가 아니다.
- 기존 `CONFIRMED_BUSINESS` 변경은 명시적 사용자 authorization과 확정 Evidence가 필요하다.
- Stage/Artifact override만으로 확정 업무 사실 변경 권한이 생기지 않는다.

### Source Write Guard

- DEVELOPMENT 외 Stage는 선택 Artifact와 Runtime 결과 범위만 수정한다.
- DEVELOPMENT는 Project Config의 Source root 범위 안에서만 Source write를 허용한다.
- protected branch write는 차단한다.
- stale Git HEAD는 차단한다.

## 8. Artifact 작성 원칙

- 사용자에게 보이는 본문은 한국어 자연어를 기본으로 한다.
- 이전 단계 확정 내용을 반복 복사하지 않고 현재 Stage의 새 의미 Delta에 집중한다.
- OPEN은 숨기지 않고 해소할 설계 Backlog로 유지한다.
- PROCESS/DESIGN의 6W는 근거 없는 값을 발명하지 않는다.
- PROGRAM은 Functional Design을 다시 서술하지 않고 구현 Target/Mapping/Query/Transaction/기술 제어/Source Delta를 추가한다.
- 고객 View는 내부 Artifact/Canonical의 파생 View이며 새 Business Truth를 만들지 않는다.

## 9. Stage별 Reference

현재 Stage Reference의 표준 파일명은 다음이며 Core 위치로 점진적으로 승격한다.

- `references/requirement.md`
- `references/clarify.md`
- `references/process.md`
- `references/discovery.md`
- `references/impact.md`
- `references/design.md`
- `references/program.md`
- `references/development.md`
- `references/test.md`
- `references/verify.md`

Runtime이 `selection.reference_path`를 제공하면 그 파일을 우선 사용한다. Reference가 없어도 Contract/Template/Context를 임의로 대체하지 않는다.

## 10. 완료 판정

다음 중 하나가 Runtime 결과로 확인될 때만 성공으로 말한다.

- `APPLIED`
- `IDEMPOTENT`
- `NO_CHANGE`
- 명시적 검증 목적의 `DRY_RUN_VALIDATED`

`INTERACTIVE_HANDOFF_READY`는 Agent 작업 준비 완료일 뿐 Stage 완료가 아니다.
`PLAN_READY`는 계획만 생성한 상태다.
Provider/Host UI가 성공 메시지를 표시해도 Harness Validator가 실패하면 Stage 성공으로 기록하지 않는다.
