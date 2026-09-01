# /work

현재 대상의 다음 실행 가능한 단계를 수행하거나, 사용자가 명시적으로 지정한 Stage/문서를 다시 수행한다. `/work`의 실행 Runtime은 `sdlc/scripts/run_work.py`다.

## 대상 선택 원칙
- Target은 `RQ/FR/BR/SCN/PROC/PGM/TASK/AC/TC`에 한정하지 않는다. Canonical에 등록된 프로젝트 고유 ID 또는 사용자가 명시한 `ANA001` 같은 ID도 받을 수 있다.
- **Target ID와 실행 Stage는 독립적이다.** `RQ-001`을 입력해도 `DESIGN` 문서를 다시 고칠 수 있고, `PGM-001`을 입력해 `PROGRAM` 또는 `DEVELOPMENT` Stage로 재진입할 수 있다.
- **Target ID와 수정 문서도 독립적이다.** 사용자가 `--artifact`를 지정하면 그 문서를 우선 수정 대상으로 사용한다.
- Canonical에 없는 임의 ID는 `--stage` 또는 Stage가 식별 가능한 기존 `--artifact`가 있을 때 실행할 수 있다.

### 실행 예시
```bash
# Target의 현재 provenance를 기준으로 다음 Stage 계획
python sdlc/scripts/run_work.py --target RQ-001 --plan-only

# PGM을 Program 단계에서 명시적으로 다시 작업
python sdlc/scripts/run_work.py --target PGM-001 --stage PROGRAM --plan-only

# RQ를 기준으로 기능설계 문서만 명시적으로 다시 작업
python sdlc/scripts/run_work.py \
  --target RQ-001 \
  --stage DESIGN \
  --artifact docs/design/RQ-001-functional-design.md \
  --plan-only

# Project 고유 분석 ID도 Stage를 지정하면 사용 가능
python sdlc/scripts/run_work.py \
  --target ANA001 \
  --stage DESIGN \
  --artifact docs/analysis/ANA001.md \
  --plan-only
```

`--stage` 또는 `--artifact`를 지정했다는 이유만으로 상위 Requirement/Business Truth 변경 권한이 생기지 않는다. 확정된 업무 사실을 실제로 변경하려면 `/change`를 우선 사용한다. 정말 `/work`에서 반영해야 하고 권한 있는 사용자가 변경을 명시적으로 확인한 경우에만 `--allow-business-truth-change`를 사용한다.

## Stage 선택 우선순위
`run_work.py`는 다음 순서로 Stage를 결정한다.

1. 사용자가 `--stage`로 명시한 Stage
2. 사용자가 지정한 기존 `--artifact`의 Stage metadata
3. Target Canonical provenance의 마지막 Stage 다음 단계
4. Target type의 기본 Stage
5. 어느 것도 판별할 수 없으면 임의 추정하지 않고 명시적 `--stage`를 요구

문서 선택 우선순위는 다음과 같다.

1. 사용자가 지정한 `--artifact`
2. Target/연결 Graph에서 같은 Stage의 기존 provenance Artifact
3. 새 `sdlc/runtime/work/<target>/<stage>_<template>` 경로

## 단계 흐름
`INTAKE → DECOMPOSE → CLARIFY → PROCESS → DISCOVERY → IMPACT → DESIGN → PROGRAM → DEVELOPMENT → TEST → VERIFY → KNOWLEDGE PROMOTION`

Stage를 명시적으로 다시 수행하더라도 위 순서를 “현재 위치”로 강제하지 않는다. 재진입은 허용하지만, 결과 Delta는 현재 Target Graph와 Business Truth Guard를 통과해야 한다.

## 실제 /work 실행 순서
1. Canonical Store와 Target을 읽는다.
2. Target 중심 relation graph를 제한된 hop으로 구성한다.
3. Stage와 Artifact를 위 우선순위로 선택한다.
4. Stage Reference와 Template 경로를 Work Context에 넣는다.
5. Project가 설정한 Agent/LLM Provider command를 실행한다.
6. Provider가 선택된 Artifact와 Stage Result Envelope를 생성한다.
7. Stage/Artifact가 사용자가 선택한 대상과 정확히 같은지 확인한다.
8. Delta가 Target Graph 밖의 기존 Canonical Entity를 수정하지 않는지 확인한다.
9. 확정된 Business Truth 변경이 명시적으로 허용됐는지 확인한다.
10. `validate_agent_stage_result.py`로 결과를 검증한다.
11. Canonical dry-run이 가능한 경우에만 실제 Delta를 적용한다.
12. 다음 Stage Candidate를 결과에 남긴다.

Provider가 비활성화되어 있으면 Runtime은 계획을 만들 수 있지만 실행을 성공했다고 주장하지 않고 `NOT_EXECUTED_PROVIDER_UNAVAILABLE_OR_DISABLED`를 반환한다.

## Provider 연결
기본 예시는 `sdlc/config/agent-repeatability-profile.example.json`과 같은 Provider command 형식을 사용할 수 있다. 실행 Command에는 다음 placeholder를 사용할 수 있다.

- `{context_path}`: Target/Stage/Artifact/Canonical Graph가 들어 있는 Work Context JSON
- `{result_path}`: Provider가 생성해야 하는 Stage Result JSON
- `{artifact_path}`: 실제 Artifact 절대경로
- `{artifact_rel}`: Repository 상대 Artifact 경로
- `{target_id}`
- `{stage}`
- `{root}`
- `{run_dir}`

Core는 특정 LLM SDK를 강제하지 않는다. Project가 실제 CLI/Agent wrapper를 연결한다.

## 문서 대상(Audience)
- `internal`: 설계/개발용 내부 산출물만 생성한다.
- `customer`: 기존 내부 산출물/Canonical을 근거로 고객 커뮤니케이션 View를 생성한다.
- `both`: 내부 산출물을 먼저 갱신한 뒤 고객 View를 파생한다.
- 고객 View에서 새 업무 사실을 만들지 않는다.
- 신규 고객 View는 `solution_agreement / delivery_scope / acceptance_handover` 3개만 사용한다.
- 고객 View 생성은 `sdlc/scripts/render_customer_document.py`를 사용한다.

## 작성 원칙
- 사용자에게 보이는 본문은 한국어 자연어를 기본으로 한다.
- 같은 업무정보를 여러 단계 문서에 복사하지 않는다. 이전 단계의 확정 내용은 참조하고 현재 Stage에서 새로 생기는 Delta만 추가한다.
- OPEN은 대기표시가 아니라 해소할 설계 Backlog다. CLARIFY/DESIGN/PROGRAM에서 실제 해소 작업이 필요하면 `.cursor/skills/open-resolve/SKILL.md`를 사용하고 동일 OPEN을 별도 Truth로 복제하지 않는다.
- 설계자/개발자 경험은 Proposal이며 Business Truth로 자동 확정하지 않는다.
- Source 관찰은 `OBSERVED`이며 고객/업무 확정과 다르다.
- Source가 연결된 경우 Locator/Source Hash는 Machine provenance로 남긴다.
- Source write 전 Target confidence와 Execution Guard를 확인한다.
- PROCESS/DESIGN의 Business Scenario는 확인되지 않은 6W를 발명하지 않는다.
- PROGRAM은 Functional Design의 업무 의미를 다시 쓰지 않고 구현 Target/Mapping/Query/Transaction/기술 제어/Source Delta만 추가한다.
- Project별 Framework 탐색과 Raw 문서 Parser 구현은 Project Adapter/Tool 책임이다.

## Target Graph Guard
`/work` Provider가 Repository 전체를 볼 수 있더라도 아무 Canonical Entity나 수정할 수 있는 것은 아니다.

- 기존 Entity 수정은 Target 중심 Canonical relation graph 또는 사용자가 지정한 Artifact에서 실제 참조되는 Entity 범위로 제한한다.
- Graph 밖 기존 Entity 수정은 `OUTSIDE_TARGET_GRAPH_MUTATION`으로 차단한다.
- 새 Entity 생성은 허용하지만 relation endpoint와 Evidence는 기존 Canonical 규칙을 따라야 한다.
- `RQ-001 --stage DESIGN` 실행이 `RQ-OTHER`를 수정하는 권한이 되지 않는다.

## Agent Stage Result 실행 경계
Stage Artifact를 작성한 것만으로 Stage 실행 완료로 간주하지 않는다. 저수준 Agent는 사용자용 Artifact와 함께 Machine용 Stage Result Envelope를 만든다.

### 최소 Stage Result Envelope
```json
{
  "schema_version": 1,
  "stage": "DESIGN",
  "artifact_path": "docs/design/RQ-001-functional-design.md",
  "canonical_delta": {
    "schema_version": 1,
    "delta_id": "WORK-RQ-001-DESIGN-001",
    "base_revision": 10,
    "stage": "DESIGN",
    "source_artifact": "docs/design/RQ-001-functional-design.md",
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

- `artifact_path`는 Repository 상대경로이며 실제 생성된 Artifact를 가리켜야 한다.
- `canonical_delta.stage`는 Stage Result의 `stage`와 같아야 한다.
- `canonical_delta.source_artifact`는 `artifact_path`와 같아야 한다.
- Artifact에 `{{placeholder}}`가 남아 있으면 실행 결과로 인정하지 않는다.
- `quality_gate.status`는 `PASS / WARNING / FAIL` 중 하나다.
- `alerts`와 `uncertainty`는 숨기지 않는다.

### 문서만 변경하고 Canonical 의미가 바뀌지 않는 경우
사용자가 특정 문서의 표현/구성만 수정했거나 실제 Semantic Delta가 없는 경우 빈 `operations`를 억지 Entity update로 만들지 않는다. 대신 다음처럼 명시한다.

```json
{
  "operations": [],
  "no_change_reason": "문서 표현만 수정하고 Canonical 의미는 변경하지 않음"
}
```

Validator/Canonical Runtime은 이를 `NO_CHANGE`로 검증하며 Store revision을 올리지 않는다.

### Stage Result 검증
Artifact와 Delta를 만든 뒤 Canonical write 전에 다음 Validator를 실행한다.

`python sdlc/scripts/validate_agent_stage_result.py --result <stage-result.json> --store sdlc/canonical/store.json --out <validation-result.json>`

다음 조건이 모두 만족되어야 다음 단계로 진행한다.
- `validation.status = PASS`
- `validation.executable = true`
- Canonical check가 `APPLIED`, `IDEMPOTENT` 또는 명시적 문서-only `NO_CHANGE`

`FAIL`, stale revision, Artifact/Delta 불일치, 미해결 Template placeholder가 있으면 Canonical을 적용했다고 기록하지 않는다.

### 반복 실행 비교
단일 Stage Result 비교는 다음처럼 수행할 수 있다.

`python sdlc/scripts/validate_agent_stage_result.py --result <run-1.json> --compare <run-2.json>`

실제 `/work` 전체 Provider 실행 경계를 반복 검증하려면 다음 Runtime을 사용한다.

```bash
python sdlc/scripts/run_work_repeatability_experiment.py \
  --provider-config <actual-provider.json> \
  --target RQ-001 \
  --stage DESIGN \
  --artifact sdlc/runtime/repeatability/design.md \
  --baseline-store <snapshot.json> \
  --run-root sdlc/runtime/repeatability/run \
  --output sdlc/runtime/repeatability/result.json
```

Validation fixture Provider 성공은 실제 Agent 성공으로 간주하지 않는다. `provider_class=EXTERNAL_AGENT`인 실제 Provider가 실행된 경우에만 empirical Agent result로 분류한다.

Validator는 `generated_at / updated_at / created_at / checked_at / observed_at` 같은 시간 필드를 semantic fingerprint에서 제외한다. **Agent/LLM 자체가 결정론적임을 증명하는 기능이 아니다.** 동일 입력의 실제 실행 결과를 비교 가능하게 만드는 검증 경계다.

## Canonical 실행 경로
Canonical은 문서에 “갱신했다”고 서술하는 것으로 끝내지 않는다. `sdlc/scripts/apply_canonical_delta.py`가 실제 저장 경계다.

지원 Operation:
- `UPSERT_ENTITY`
- `UPSERT_RELATION`
- `ADD_PROVENANCE`

`DELETE`와 자동 Business Truth 역갱신은 지원하지 않는다.

### Idempotency 안전 규칙
- 적용된 Delta에는 semantic `payload_hash`를 저장한다.
- 같은 `delta_id + 같은 semantic payload`만 `IDEMPOTENT`다.
- 같은 `delta_id + 다른 payload`는 `DELTA_ID_CONTENT_CONFLICT`로 차단한다.
- 과거 Runtime이 payload hash 없이 저장한 동일 ID 재사용은 semantic identity를 증명할 수 없으므로 fail-closed 한다.

### Business Truth 안전 규칙
- 기존 `CONFIRMED_BUSINESS`의 field/status를 바꾸려면 `evidence_class: CONFIRMED`가 필요하다.
- `GIVEN / OBSERVED / INFERRED / ASSUMED`는 기존 확정 업무 사실을 덮어쓰거나 낮출 수 없다.
- `/work`는 위 Canonical 규칙에 더해 기존 확정 Business Truth의 실제 변경에 명시적 사용자 authorization을 요구한다.
- Source 관찰을 값 변경 없이 연결할 때는 `ADD_PROVENANCE`를 우선한다.
- Canonical 적용 성공과 Source Code write 승인은 별개다.

실제 Delta 적용 전에는 기존 방식과 동일하게 `--dry-run`을 사용할 수 있다.

```bash
python sdlc/scripts/apply_canonical_delta.py --delta <delta.json> --dry-run
```

## Source Drift / Reverse Review
매번 `baseline / observed manifest / artifact-index`를 사람이 작성하지 않는다.

첫 기준점 생성:
```bash
python sdlc/scripts/run_source_reverse_check.py \
  --source-root <source-root> \
  --artifact-root <artifact-root> \
  --source-ref <commit-or-ref> \
  --baseline sdlc/runtime/reverse/baseline.json \
  --output sdlc/runtime/reverse/result.json \
  --create-baseline
```

이후 비교:
```bash
python sdlc/scripts/run_source_reverse_check.py \
  --source-root <source-root> \
  --artifact-root <artifact-root> \
  --source-ref <current-ref> \
  --baseline sdlc/runtime/reverse/baseline.json \
  --output sdlc/runtime/reverse/result.json
```

`build_reverse_inputs.py`가 Source file hash, Artifact의 Source Evidence, Canonical provenance/공유 Entity를 이용해 입력을 만든다. 자동 생성 upstream edge는 보수적으로 `CHECK_REQUIRED`이며 Business Truth를 자동 변경하지 않는다.

`detect_source_drift.py`와 `generate_program_spec_reverse_candidate.py`는 계속 Candidate-only 기능이다. Full Reverse Engineering 또는 문서 자동 재작성으로 표현하지 않는다.

## References
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
