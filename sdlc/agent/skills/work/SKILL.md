# SDLC Core Skill — work

이 파일은 특정 IDE나 Agent 제품에 종속되지 않는 `/work`의 **Core Source of Truth**다.
Cursor, Codex, Claude Code 또는 다른 Repository-capable Agent는 Host Adapter에서 이 파일을 읽고 동일한 Runtime/Guard를 사용한다.

핵심 원칙은 하나다.

> **Change Level이 요구하는 Semantic Work만 수행하고, 필요한 Evidence와 선택된 Human Artifact만 읽는다. Stage 전체 체계를 기본 Context로 로드하지 않는다.**

## 1. 실행 모드

Human-maintained 설정은 `.sdlc/project.yaml` 하나다.

- `agent.execution` 생략 시 `INTERACTIVE`가 기본이다.
- `INTERACTIVE`: 현재 IDE/CLI/대화 Agent가 작업한다. 별도 Provider subprocess를 다시 호출하지 않는다.
- `HEADLESS`: Harness가 설정된 외부 Provider command를 실행한다.
- Agent 제품명은 프로젝트 업무 Config가 아니다.

두 모드는 Agent 시작 방식만 다르다. Target Graph Guard, Business Truth Guard, Stage Result Validator, Canonical Apply는 동일하다.

## 2. 사용자 진입

일반 사용자는 다음처럼 Target만 지정한다.

```bash
python sdlc/scripts/harness.py work --target RQ-001
```

자연어 `RQ-001 다음 작업해줘`도 같은 의도다.

`--stage`와 `--artifact`는 호환성/재진입/debug 용도다. 일반 작업에서는 Runtime이 Change Level과 Tailoring Profile로 실행 의미와 Primary Artifact를 선택한다.

확정된 업무 사실 자체를 바꾸는 요청은 `/change`가 우선이다.

## 3. 기본 계획 — Semantic Work 우선

먼저 Harness가 만든 `work-context.json`만 기준으로 작업 범위를 정한다.

우선 읽을 항목:

1. `target`과 Target 중심 Canonical relation graph
2. `change_level`
3. `execution_policy.required_semantic_work`
4. `execution_policy.required_evidence`
5. `execution_policy.required_human_review`
6. `selection.template_path`와 선택 Artifact
7. Project Context와 실제 필요한 Source 범위

### Context 최소화 규칙

- 모든 Stage Reference를 선로딩하지 않는다.
- 모든 Template을 선로딩하지 않는다.
- 전체 Repository를 LLM으로 먼저 읽지 않는다.
- 선택된 Semantic Work와 관련된 Target Graph/Source symbol/file부터 탐색한다.
- 다른 Stage Reference는 **명시적 Stage 재진입**, 현재 Semantic Work에 실제 필요, 또는 Change Level escalation이 발생한 경우에만 읽는다.
- Customer/PM Projection Template은 내부 작업 초안을 만들 때 기본 Context에 넣지 않는다.
- Machine Runtime JSON은 필요한 필드만 읽고 사람이 직접 유지하지 않는다.

### L1/L2 Fast Path

L1/L2는 Stage를 여러 번 실행하지 않아도 되지만 Source write 전에 다음 분석은 생략할 수 없다.

1. `INTENT_DECOMPOSITION` — 요구 의도와 변경 범위를 분해한다.
2. `AS_IS_SOURCE_ANALYSIS` — 관련 현재 Source/Config/Data 흐름을 확인한다.
3. `IMPACT_CHECK` — 직접 영향과 명백한 주변 영향을 확인한다.

이 세 항목은 별도 Human 문서를 강제하지 않는다. 실제 Source를 수정하는 run에서는 `stage-result.json`의 `pre_write_analysis` Machine Evidence로 요약한다.

L1/L2에서 불확실성이 커지거나 Interface/Batch/Schema/Security/Architecture/Cross-domain 영향이 확인되면 Runtime의 Change Level escalation을 따른다. 자동 downgrade는 하지 않는다.

### L3~L5

L3 이상도 전체 Stage 체계를 무조건 읽지 않는다. `required_semantic_work`에 필요한 설계/영향/프로그램 Reference만 선택적으로 로드한다.

Stage taxonomy는 내부 호환 의미를 보존하지만 일반 Agent의 사고 순서나 문서 개수를 강제하는 체크리스트가 아니다.

## 4. INTERACTIVE 실행

### 4.1 Prepare

```bash
python sdlc/scripts/harness.py work --target <TARGET-ID>
```

Runtime은 `INTERACTIVE_HANDOFF_READY`와 함께 다음을 제공한다.

- `work-context.json`
- 선택된 Artifact/Template
- `stage-result.json` 예정 경로
- Git/Canonical baseline
- Target Graph와 허용 변경 범위
- Change Level / Semantic Execution Policy

`INTERACTIVE_HANDOFF_READY`는 작업 준비 완료이지 Stage 완료가 아니다.

### 4.2 현재 Agent가 수행할 일

1. `work-context.json`에서 필요한 필드만 읽는다.
2. Requirement intent를 확인한다.
3. Brownfield/Hybrid에서 Source write 가능성이 있으면 관련 AS-IS Source를 먼저 분석한다.
4. 영향 범위를 확인하고 Change Level escalation 조건이 보이면 숨기지 않는다.
5. 선택된 `selection.template_path`만 기본 Human 작성면으로 사용한다.
6. 모르는 업무 사실은 발명하지 않고 OPEN/uncertainty로 남긴다.
7. Artifact와 같은 run directory의 `stage-result.json`을 작성한다.
8. finalize를 실행한다.

Source를 실제 수정한 L1/L2 예:

```json
{
  "pre_write_analysis": {
    "intent": {"status": "CONFIRMED_OR_BOUNDED", "evidence_refs": ["RQ-001"]},
    "as_is_source": {"status": "OBSERVED", "evidence_refs": ["src/.../Service.java#method"]},
    "impact": {"status": "CHECKED", "evidence_refs": ["PGM-001"], "coverage": "COMPLETE_OR_PARTIAL"}
  }
}
```

문서-only DEVELOPMENT 결과에는 이 Evidence와 Build/Test를 억지로 만들지 않는다.

### 4.3 Finalize

```bash
python sdlc/scripts/harness.py work --target <TARGET-ID> --finalize --run-dir <RUN-DIR>
```

Runtime은 fail-closed로 다음을 확인한다.

- Prepare 이후 Git HEAD/branch와 Canonical revision이 stale하지 않은가
- 허용 범위 밖 파일을 수정하지 않았는가
- Target Graph 밖 기존 Entity를 수정하지 않았는가
- Confirmed Business Truth 변경 권한을 우회하지 않았는가
- Stage Result와 선택 Artifact가 일치하는가
- Validator가 PASS + executable인가
- **실제 Source root 파일이 변경된 경우에만** 필요한 pre-write analysis와 Build/Test Evidence가 있는가

Interactive 실패 시 사용자의 파일을 자동 rollback하지 않고 Canonical 적용을 중지한 뒤 `manual_recovery_required`를 표시한다.

## 5. HEADLESS 실행

HEADLESS에서는 `.sdlc/project.yaml`에 Provider command가 있어야 한다.

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

Provider도 `work-context.json`의 Semantic Work만 수행해야 한다. Provider 성공 자체는 작업 성공이 아니며 동일 Validator/Canonical Guard를 통과해야 한다.

## 6. Stage Result Contract

최소 Envelope:

```json
{
  "schema_version": 1,
  "stage": "DEVELOPMENT",
  "artifact_path": "docs/10_산출물/RQ-001/...md",
  "canonical_delta": {
    "schema_version": 1,
    "delta_id": "WORK-RQ-001-001",
    "base_revision": 10,
    "stage": "DEVELOPMENT",
    "source_artifact": "docs/10_산출물/RQ-001/...md",
    "operations": []
  },
  "quality_gate": {"status": "PASS", "failures": []},
  "alerts": [],
  "uncertainty": []
}
```

- `artifact_path`는 실제 Repository 상대경로여야 한다.
- `canonical_delta.stage`와 `source_artifact`는 결과와 일치해야 한다.
- `{{placeholder}}`가 남은 Artifact는 완료 결과로 인정하지 않는다.
- 문서 표현만 바뀌면 억지 Canonical Entity update를 만들지 않고 `operations: []` + `no_change_reason`을 사용한다.
- L1/L2 Source write에서는 `pre_write_analysis`가 Requirement/AS-IS/Impact 분석의 Machine Evidence다.

## 7. 공통 Guard

### Target Graph Guard

- 기존 Entity 수정은 Target 중심 Graph 또는 명시적 Artifact가 실제 참조하는 범위로 제한한다.
- Graph 밖 기존 Entity 수정은 `OUTSIDE_TARGET_GRAPH_MUTATION`으로 차단한다.
- Stage/Artifact override는 다른 Requirement 수정 권한이 아니다.

### Business Truth Guard

- Source 관찰은 `OBSERVED`이며 고객/업무 확정과 다르다.
- Agent 경험은 Proposal이지 Business Truth가 아니다.
- `GIVEN / OBSERVED / INFERRED / ASSUMED`는 기존 `CONFIRMED_BUSINESS`를 덮어쓰거나 downgrade할 수 없다.
- 확정 업무 사실 변경에는 명시적 사용자 authorization과 확정 Evidence가 필요하다.
- Source 관찰만 추가할 때는 값 변경보다 `ADD_PROVENANCE`를 우선한다.

### Source Write Guard

- Project Config의 Source root 밖 Source write는 허용하지 않는다.
- protected branch와 stale Git HEAD는 차단한다.
- 실제 Source 변경 전에 Intent/AS-IS/Impact를 확인한다.
- 실제 Source 변경이 없다면 Build/Test와 pre-write analysis를 형식적으로 강제하지 않는다.

## 8. Artifact / Tailoring 원칙

`Stage / Canonical / Evidence → Tailoring Profile → Human Artifact`

- Template은 문서 모양이다.
- Tailoring Profile은 어떤 의미를 어떤 Human Artifact에 보여줄지 결정한다.
- Change Level은 RQ별 실행 깊이이며 문서 개수와 동일하지 않다.
- 일반 사용자는 `STANDARD_5` 내부 문서 Profile, `CUSTOMER_STANDARD_3`, `PM_STANDARD`를 기본값으로 사용한다.
- `STAGE_ORIENTED_FULL`은 Legacy/Formal compatibility용이며 신규 기본값이 아니다.
- 이전 내용을 반복 복사하지 않고 현재 변경의 의미 Delta에 집중한다.
- Source Hash/Locator/Trace 등 재생성 가능한 값은 Machine-derived로 관리한다.

## 9. Customer / PM Projection

Customer/PM View는 내부 Canonical/Evidence에서 파생한 `GENERATED_VIEW`다.

- Customer View가 새 Business Truth를 만들지 않는다.
- Customer 문서 직접 수정이 Canonical을 자동 수정하지 않는다.
- 기본 고객 View는 `solution_agreement / delivery_scope / acceptance_handover` 3종이다.
- Projection은 Stage/Canonical 의미를 사용하며 특정 Internal Profile의 Artifact ID에 종속시키지 않는다.
- `STALE_VIEW`는 승인 기준에서 제외하고 재생성한다.

## 10. OPEN 해소

OPEN은 대기표시가 아니라 해소할 설계 Backlog다.

- 업무 권위가 필요한 OPEN은 사람의 결정으로 닫는다.
- 기술적으로 조사 가능한 OPEN은 Source/설계 Evidence로 해소한다.
- SOP는 유용한 Evidence지만 필수 입력이 아니다.
- OPEN을 근거 없는 추정으로 닫지 않는다.

상세 절차가 필요할 때만 `.cursor/skills/open-resolve/SKILL.md`를 읽는다.

## 11. Stage Reference — 필요할 때만

Core Reference는 `sdlc/agent/skills/work/references/` 아래에 있다.

일반 `work --target`에서는 이 디렉터리 전체를 읽지 않는다. 다음 경우에만 선택된 Reference 하나 또는 필요한 최소 집합을 읽는다.

- 사용자가 `--stage`를 명시했다.
- `execution_policy.required_semantic_work`가 해당 전문 규칙을 요구한다.
- Change Level escalation으로 추가 설계/영향 규칙이 필요하다.

`.cursor/skills/work/references/`는 Legacy Mirror다. 동일 이름의 Core Reference가 있으면 Core 경로를 우선한다.

## 12. 완료 판정

다음 Runtime 결과가 확인될 때만 성공으로 말한다.

- `APPLIED`
- `IDEMPOTENT`
- `NO_CHANGE`
- 검증 목적의 `DRY_RUN_VALIDATED`

`INTERACTIVE_HANDOFF_READY`와 `PLAN_READY`는 완료가 아니다.
