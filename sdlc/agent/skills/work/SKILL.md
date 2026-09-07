# SDLC Core Skill — work

이 파일은 특정 IDE나 Agent 제품에 종속되지 않는 `/work`의 **Core Source of Truth**다.
Cursor, Codex, Claude Code 또는 다른 Repository-capable Agent는 Host Adapter에서 이 파일을 읽고 동일한 Runtime/Guard를 사용한다.

핵심 원칙은 세 가지다.

> **Change Level은 Semantic Work / Evidence / Human Review의 깊이를 결정한다. Human Artifact 개수나 Profile topology를 결정하지 않는다.**
>
> **현재 Stage와 가장 잘 맞는 `primary_work_artifact`를 편집 초점으로 사용하되, Profile이 `PROFILE_PRIMARY_SET`이면 `required_engineering_artifacts` 전체를 필요한 깊이로 갱신한다.**
>
> **사람에게 Template을 작성시키지 않는다. Agent가 먼저 조사·초안 작성하고, 사람의 업무 판단이 필요한 Gap만 질문한다. 사용자가 즉시 답하지 못하면 Human Decision Queue로 이월하고 다음 Semantic Work에서 재확인한다.**

## 1. 실행 모드

Human-maintained 설정은 `.sdlc/project.yaml` 하나다.

- `agent.execution` 생략 시 `INTERACTIVE`가 기본이다.
- `INTERACTIVE`: 현재 IDE/CLI/대화 Agent가 작업한다. 별도 Provider subprocess를 다시 호출하지 않는다.
- `HEADLESS`: Harness가 설정된 외부 Provider command를 실행한다.
- Agent 제품명은 프로젝트 업무 Config가 아니다.

두 모드는 Agent 시작 방식만 다르다. Target Graph Guard, Business Truth Guard, Stage Result Validator, Canonical Apply, Change Level/Projection Guard는 동일하다.

## 2. 사용자 진입

일반 사용자는 다음처럼 Target만 지정한다.

```bash
python sdlc/scripts/harness.py work --target RQ-001
```

자연어 `RQ-001 다음 작업해줘`도 같은 의도다.

`--stage`와 `--artifact`는 호환성/재진입/debug 용도다. 일반 작업에서는 Runtime이 Change Level로 실행 깊이와 기본 내부 진입 Stage를 정하고, Tailoring Profile이 Human Artifact topology와 편집 초점을 정한다.

확정된 업무 사실 자체를 바꾸는 요청은 `/change`가 우선이다.

### 2.1 Change Level 사용자 제어

Change Level의 상세 제어는 `sdlc/agent/skills/work/references/change-level.md`를 따른다.

사용자는 Project Config에서 사전 정의하거나 작업 중 자연어로 올리거나 내릴 수 있다.

```text
RQ-001은 L3로 진행해줘. 업무규칙 검토가 필요해서야.
RQ-001을 L4에서 L2로 낮춰줘. 조회조건 하나만 영향 있는 것으로 확인됐어.
RQ-001 Level override를 해제하고 AUTO로 다시 판단해줘.
```

Agent는 Level 요청을 대화에만 남기지 않고 `change_execution_runtime.py set-level / clear-level` 경계로 기록한다.

- 자동 승격: 허용
- 자동 강등: 금지
- 명시적 Human 강등: 이유를 남기면 허용
- 현재 `safety_floor`보다 낮은 강등: 명시적 Risk Acceptance 없이는 차단

Level 변경 후에는 같은 Target으로 `/work`를 다시 실행하여 Semantic Plan과 Projection Update Set을 재계산한다.

## 3. 기본 계획 — Semantic Work + Projection Update Set

먼저 Harness가 만든 `work-context.json`만 기준으로 작업 범위를 정한다.

우선 읽을 항목:

1. `target`과 Target 중심 Canonical relation graph
2. `change_level.observed_change_level`
3. `change_level.effective_change_level`
4. `change_level.level_source / safety_floor / level_history`
5. `execution_policy.required_semantic_work`
6. `execution_policy.required_evidence`
7. `execution_policy.required_human_review`
8. `tailoring.primary_work_artifact`
9. `tailoring.required_engineering_artifacts / projection_update_set`
10. 선택/필수 Artifact와 Target 관련 문서의 미해결 `Human Decision Queue`
11. Project Context와 실제 필요한 Source 범위

### Context 최소화 규칙

- 모든 Stage Reference를 선로딩하지 않는다.
- 모든 Template을 무조건 선로딩하지 않는다.
- 단 `required_engineering_artifacts`에 들어간 Template은 이번 Run의 갱신 대상이므로 필요한 Block만 읽는다.
- 전체 Repository를 LLM으로 먼저 읽지 않는다.
- 선택된 Semantic Work와 관련된 Target Graph/Source symbol/file부터 탐색한다.
- 다른 Stage Reference는 **명시적 Stage 재진입**, 현재 Semantic Work에 실제 필요, Change Level escalation, 또는 Level Control이 필요한 경우에만 읽는다.
- Customer/PM Projection Template은 내부 구현 작업 초안을 만들 때 기본 Context에 넣지 않는다.
- Machine Runtime JSON은 필요한 필드만 읽고 사람이 직접 유지하지 않는다.
- Queue를 확인하기 위해 unrelated 문서 전체를 선로딩하지 않고 현재 Target과 연결된 Artifact의 Queue Block만 우선 확인한다.

### L1/L2 Fast Path

L1/L2는 Stage를 여러 번 실행하지 않아도 되지만 Source write 전에 다음 분석은 생략할 수 없다.

1. `INTENT_DECOMPOSITION` — 요구 의도와 변경 범위를 분해한다.
2. `AS_IS_SOURCE_ANALYSIS` — 관련 현재 Source/Config/Data 흐름을 확인한다.
3. `IMPACT_CHECK` — 직접 영향과 명백한 주변 영향을 확인한다.

이 세 분석을 각각 별도의 **Stage 문서**로 만들 필요는 없다. 그러나 선택된 Engineering Profile이 `PROFILE_PRIMARY_SET`이면 Profile-required Human Artifact는 유지해야 한다.

즉:

```text
L1/L2 Fast Path
= Stage 문서 체인을 줄일 수 있음
≠ Custom Profile PRIMARY 문서를 삭제/미생성할 수 있음
```

Runtime이 검사하는 Source Write key:

- `INTENT_DECOMPOSED`
- `AS_IS_SOURCE_ANALYZED`
- `IMPACT_CHECKED`

L1/L2에서 불확실성이 커지거나 Interface/Batch/Schema/Security/Architecture/Cross-domain 영향이 확인되면 Runtime의 Change Level escalation을 따른다.

Profile이 `level_projection_detail`을 제공하면 L1/L2 문서는 `CONCISE`로 작성할 수 있다. 상세 Process나 정책 변경을 발명하지 않고 실제 확인된 변경 목적, 영향, 정책 변경 유무, 확인사항만 짧게 기록한다.

### L3~L5

L3 이상도 전체 Stage 체계를 무조건 읽지 않는다. `required_semantic_work`에 필요한 설계/영향/프로그램 Reference만 선택적으로 로드한다.

Stage taxonomy는 내부 호환 의미를 보존하지만 일반 Agent의 사고 순서나 문서 개수를 강제하는 체크리스트가 아니다.

## 4. HITL — Agent Question Driven UX

상세 질문/Queue 기준은 `sdlc/agent/skills/work/references/hitl.md`를 따른다.

### 4.1 사람이 하는 일

사람은 **문서를 작성하는 사람**이 아니라 다음 역할만 한다.

- Agent가 제시한 업무/정책 질문에 자연어로 답변
- 지금 답할 수 없으면 `확인 후 답변`, `다음 단계에서 재확인`처럼 보류 의사 표현
- Agent 초안을 Review
- 두 개 이상의 합리적 대안 중 의사결정
- 업무 권한이 필요한 Rule/Scope/Exception/AC 확정
- 생성 문서의 특정 Block을 지정해 수정 요청
- 필요하면 Change Level 승격/강등과 그 이유 명시

### 4.2 Agent가 먼저 해야 하는 일

질문 전에 다음 순서를 반드시 수행한다.

1. Canonical에 이미 답이 있는지 확인
2. Change Level 상태/이력과 Safety Floor 확인
3. 현재 Target의 미해결 Human Decision Queue 확인
4. 기존 요구사항/문서 Evidence 확인
5. Brownfield면 Source/DB/Config/Trace에서 기술적으로 조사
6. 프로젝트 Standard/Decision으로 결정 가능한지 확인
7. Agent가 채울 수 있는 항목은 먼저 초안 작성
8. 그래도 사람의 업무 권위가 필요한 Gap만 HITL 질문으로 생성

따라서 `Program ID`, `Java Method`, `XML Query`, `Table Column`, 현재 권한 호출처럼 Source에서 확인할 수 있는 항목을 사람에게 작성시키지 않는다.

### 4.3 질문 방식

- 한 턴 기본 최대 3개
- 같은 Decision Cluster는 묶어서 질문
- **`Recheck At`이 현재 Semantic Work/실행 경계인 기존 Queue를 신규 질문보다 먼저 제시**
- 각 질문에는 `왜 필요한가`, `현재 알고 있는 것`, `답변이 반영될 Block`을 짧게 표시
- 선택지는 근거가 있을 때만 제안
- 사용자가 답하지 않아도 되는 세부 UI 표현은 `ITERATE`로 남길 수 있음
- 답이 없으면 Source Write가 위험한 항목만 `SOURCE_BLOCK`으로 유지

질문의 내부 식별은 `HITL-<TARGET>-<NN>` 형식을 권장한다. Queue로 이월될 때도 같은 ID를 유지하여 단계마다 중복 질문을 만들지 않는다.

### 4.4 사용자가 즉시 답하지 못한 경우

Agent는 질문을 강제하거나 Business Truth를 추정하지 않는다.

1. 해당 질문을 관련 Engineering Artifact의 `Human Decision Queue` Block에 기록/갱신한다.
2. Queue ID는 기존 HITL Question ID를 그대로 사용한다.
3. `Related Block`, 현재 확인값/제안, Decision Owner, 영향 분류, `Recheck At`, 상태를 기록한다.
4. 의미적으로는 기존 OPEN 해소 계약을 사용하여 `OPEN` 또는 `DEFERRED`로 유지한다. 사용자가 나중에 답하기로 한 경우 resolution method는 `DEFER`를 사용한다.
5. `SOURCE_BLOCK / ITERATE / ALERT`에 따라 현재 진행 가능 범위를 결정한다.
6. 다음 Semantic Work 진입 시 이 Queue를 신규 질문보다 먼저 재검토한다.

문서 Queue는 Human-facing Projection이고 두 번째 SSOT가 아니다. 실제 의미 상태는 Canonical OPEN/Decision/Provenance 및 기존 `open-resolution-contract`에 연결한다.

### 4.5 다음 Semantic Work 진입 시 Carry-forward Queue

1. 현재 Target/관련 Artifact의 미해결 Queue를 읽는다.
2. Queue가 이미 Canonical/Evidence 변경으로 해소됐는지 확인한다.
3. 기술 조사로 해소할 수 있으면 사람에게 다시 묻기 전에 Source/DB/Config를 조사한다.
4. 현재 `Recheck At`에 도달한 사람 소유 Queue를 신규 HITL 질문보다 먼저 재확인한다.
5. 또 답하지 못하면 동일 Queue ID로 상태와 다음 `Recheck At`만 갱신한다.
6. 답을 받으면 `GIVEN`/Decision provenance와 필요한 Canonical Delta를 만들고 Queue를 확정/해소한다.

단순히 여러 단계를 지나왔다는 이유만으로 자동 `SOURCE_BLOCK` 승격하지 않는다. 실제 Source Write/Test/Verify 안전 경계에 도달한 경우에만 영향 분류를 재판정한다.

### 4.6 답변 반영

- 답변을 `GIVEN` Evidence로 기록한다.
- Rule/Decision/Scope/AC 등 Semantic 의미가 생기면 Canonical Delta를 작성한다.
- 기존 `CONFIRMED_BUSINESS`와 충돌하면 자동 덮어쓰지 않고 `/change` 경계로 전환한다.
- 단순 표현/오탈자 수정이면 Canonical Delta를 만들지 않는다.
- 대응 Queue가 있으면 같은 Queue ID를 해소하고 OPEN/DEFERRED 상태도 함께 정리한다.
- Canonical Apply 성공 후 Engineering/Customer Projection을 갱신한다.

## 5. 생성 문서 Block 수정 UX

사람이 생성된 Engineering 문서에서 수정할 내용을 발견한 경우 **파일을 직접 편집하는 것보다 Block을 지정해 Agent에게 지시하는 것을 기본 방식**으로 한다.

권장 요청:

```text
RQ-0042 Work Unit SDD의 [BLOCK:WU-BUSINESS-RULE]에서
월 마감 후 재계산 정책을 "급여 마감 전까지만 허용"으로 바꿔줘.
```

```text
PGM-ATT-0016 Program Spec의 [BLOCK:PGM-SOURCE-EVIDENCE]를
현재 Source 기준으로 다시 분석해서 갱신해줘.
```

```text
RQ-0042 Work Unit SDD의 [BLOCK:WU-HITL-QUEUE]에서
HITL-RQ-0042-02는 지금 답하기 어려우니 PROGRAM 단계에서 다시 확인해줘.
```

Agent Routing:

- `SEMANTIC_CHANGE`: Requirement/Business Rule/TO-BE/AC/Scope 의미 변경 → `/change`
- `EVIDENCE_REFRESH`: AS-IS/Source/DB/Mapping/AS-BUILT 근거 갱신 → `/work`
- `PROJECTION_ONLY`: 오탈자/표현/레이아웃만 수정 → Canonical Delta 없음
- Change Level 변경 → Change Level Runtime에 이력 반영 후 `/work` 재계산

Queue의 일정/상태 조정 자체는 Business Truth 변경이 아니다. Queue 질문에 실제 업무 답을 제공하면 답변의 의미에 따라 `/change` 또는 `/work`로 Routing한다.

사용자가 Block ID를 쓰지 않았더라도 문맥이 명확하면 Agent가 해석한 Block을 먼저 명시하고 진행한다. 애매하면 Block 선택만 짧게 확인한다.

Stable Block ID 목록과 HRIS Custom Block 규칙은 `references/hitl.md`를 사용한다.

## 6. INTERACTIVE 실행

### 6.1 Prepare

```bash
python sdlc/scripts/harness.py work --target <TARGET-ID>
```

Runtime은 `INTERACTIVE_HANDOFF_READY`와 함께 다음을 제공한다.

- `work-context.json`
- Change Level 상태와 Execution Policy
- `primary_work_artifact`
- `required_engineering_artifacts / projection_update_set`
- `projection_detail`
- `stage-result.json` 예정 경로
- Git/Canonical baseline
- Target Graph와 허용 변경 범위

`INTERACTIVE_HANDOFF_READY`는 작업 준비 완료이지 Stage 완료가 아니다.

### 6.2 현재 Agent가 수행할 일

1. `work-context.json`에서 필요한 필드만 읽는다.
2. Change Level의 observed/effective/source/safety/history를 확인한다.
3. Requirement intent를 확인한다.
4. `tailoring.required_engineering_artifacts`와 각 `projection_detail`을 확인한다.
5. 현재 Target/Artifact의 미해결 Human Decision Queue와 `Recheck At`을 확인한다.
6. Brownfield/Hybrid에서 Source write 가능성이 있으면 관련 AS-IS Source를 먼저 분석한다.
7. 영향 범위를 확인하고 Change Level escalation 조건이 보이면 숨기지 않는다.
8. HITL Reference에 따라 사람에게 질문하기 전에 Agent가 조사 가능한 항목을 먼저 채운다.
9. 현재 단계에 재확인해야 할 Queue가 있으면 신규 질문보다 먼저 처리한다.
10. 사람 판단이 필요한 새 Gap이 있으면 해당 Block과 이유를 표시해 질문한다.
11. 사용자가 답하지 못하면 Artifact Queue + OPEN/DEFERRED로 carry-forward한다.
12. 답변을 받은 뒤 Canonical Delta 후보와 Engineering Projection 초안을 함께 갱신한다.
13. `primary_work_artifact`를 중심으로 작업하되 **required Engineering Artifact 전체를 갱신**한다.
14. 모르는 업무 사실은 발명하지 않고 OPEN/uncertainty로 남긴다.
15. Artifact와 같은 run directory의 `stage-result.json`을 작성한다.
16. finalize를 실행한다.

Source를 실제 수정한 L1/L2 예:

```json
{
  "pre_write_analysis": {
    "INTENT_DECOMPOSED": {"status": "PASS", "evidence_refs": ["RQ-001"]},
    "AS_IS_SOURCE_ANALYZED": {"status": "PASS", "evidence_refs": ["src/.../Service.java#method"]},
    "IMPACT_CHECKED": {"status": "PASS", "evidence_refs": ["PGM-001"]}
  }
}
```

문서-only DEVELOPMENT 결과에는 이 Evidence와 Build/Test를 억지로 만들지 않는다.

### 6.3 Finalize

```bash
python sdlc/scripts/harness.py work --target <TARGET-ID> --finalize --run-dir <RUN-DIR>
```

Runtime은 fail-closed로 다음을 확인한다.

- Prepare 이후 Git HEAD/branch와 Canonical revision이 stale하지 않은가
- 허용 범위 밖 파일을 수정하지 않았는가
- Target Graph 밖 기존 Entity를 수정하지 않았는가
- Confirmed Business Truth 변경 권한을 우회하지 않았는가
- Stage Result와 Primary Artifact가 일치하는가
- Validator가 PASS + executable인가
- 실제 Source root 파일이 변경된 경우에만 필요한 pre-write analysis와 Build/Test Evidence가 있는가
- **`required_engineering_artifacts`가 모두 실제 파일로 갱신되어 Projection lifecycle에 등록됐는가**

필수 Projection이 하나라도 빠지면 Semantic 결과가 성공이더라도 최종 상태는 `PROJECTION_REFRESH_REQUIRED`다. 빠진 문서를 현재 Canonical/Evidence에서 갱신한 뒤 다시 finalize한다.

Interactive 실패 시 사용자의 파일을 자동 rollback하지 않고 Canonical 적용을 중지한 뒤 `manual_recovery_required`를 표시한다.

## 7. HEADLESS 실행

HEADLESS에서도 Provider는 `work-context.json`의 Semantic Work와 `required_engineering_artifacts`를 모두 처리해야 한다.

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

Provider 성공 자체는 작업 성공이 아니며 동일 Validator/Canonical/Projection Guard를 통과해야 한다.

HITL이 필요한 HEADLESS 실행은 Provider가 `HITL_REQUIRED`와 질문 목록을 결과에 남기고 Canonical/Source Write를 완료 처리하지 않는다. 외부 Orchestrator가 즉시 답변을 다시 공급할 수 없는 경우에도 관련 Engineering Artifact의 Human Decision Queue와 OPEN/DEFERRED에 같은 질문 ID를 남겨 다음 실행에서 재확인할 수 있어야 한다.

## 8. Stage Result Contract

최소 Envelope:

```json
{
  "schema_version": 1,
  "stage": "DEVELOPMENT",
  "artifact_path": "docs/10_engineering/RQ-001/...md",
  "canonical_delta": {
    "schema_version": 1,
    "delta_id": "WORK-RQ-001-001",
    "base_revision": 10,
    "stage": "DEVELOPMENT",
    "source_artifact": "docs/10_engineering/RQ-001/...md",
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
- HITL 답변이 Semantic 변경의 근거라면 `uncertainty`를 조용히 제거하지 말고 관련 `GIVEN`/Decision provenance와 Canonical Delta를 연결한다.
- 미응답 HITL은 대화에서만 사라지게 두지 않고 Artifact Queue와 관련 OPEN/DEFERRED 상태에 남긴다.
- Stage Result의 단일 `artifact_path`는 현재 실행의 Primary 결과이며, Profile-required 추가 Projection의 존재를 부정하지 않는다.

## 9. 공통 Guard

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
- 사용자가 답하지 못한 Queue 항목을 `ASSUMED` Business Truth로 조용히 승격하지 않는다.

### Change Level Guard

- AUTO가 낮게 관측됐다는 이유로 기존 Effective Level을 자동 강등하지 않는다.
- Human Override는 이유와 `level_history`를 남긴다.
- Safety Floor 아래 Override는 명시적 Risk Acceptance가 없으면 차단한다.
- Level 변경 자체가 Canonical Business Truth를 변경하지 않는다.
- Level 변경 후 Projection Update Set을 다시 계산한다.

### Source Write Guard

- Project Config의 Source root 밖 Source write는 허용하지 않는다.
- protected branch와 stale Git HEAD는 차단한다.
- 실제 Source 변경 전에 Intent/AS-IS/Impact를 확인한다.
- 실제 Source 변경이 없다면 Build/Test와 pre-write analysis를 형식적으로 강제하지 않는다.
- 사람 판단이 필요한 `SOURCE_BLOCK`을 Template 빈칸으로 남겨놓고 Source Write를 강행하지 않는다.
- Queue가 있더라도 `ITERATE`/`ALERT` 항목만으로 전체 Stage를 무조건 중단하지 않는다.

## 10. Artifact / Tailoring 원칙

```text
Change Level → Semantic Work / Evidence / Review Depth
Stage        → Internal Execution Focus
Profile      → Human Artifact Topology
Canonical   → Projection Content
```

- Template은 문서 모양이다.
- Tailoring Profile은 어떤 의미를 어떤 Human Artifact에 보여줄지 결정한다.
- Change Level은 RQ별 실행 깊이이며 문서 개수와 동일하지 않다.
- `projection_topology: PROFILE_PRIMARY_SET`이면 PRIMARY Engineering Artifact 집합을 유지한다.
- `primary_work_artifact`는 현재 편집 초점이지 유일한 필수 문서라는 뜻이 아니다.
- `required_engineering_artifacts`는 이번 Run 뒤 존재·갱신되어야 하는 Engineering 문서다.
- `projection_detail`은 `CONCISE / STANDARD / FULL`의 작성 밀도다.
- 일반 사용자는 현재 Project Config의 Engineering/Customer/PM Profile을 따른다.
- `STAGE_ORIENTED_FULL`은 Legacy/Formal compatibility용이며 신규 기본값이 아니다.
- 이전 내용을 반복 복사하지 않고 현재 변경의 의미 Delta에 집중한다.
- Source Hash/Locator/Trace 등 재생성 가능한 값은 Machine-derived로 관리한다.
- Human Artifact는 사람이 처음부터 채우는 Template Form이 아니라 Agent 초안을 검토하는 Projection이다.
- Human Decision Queue 역시 사람이 수동 관리하는 원장이 아니라 Agent가 OPEN/DEFERRED를 보여주는 Review Surface다.

### HRIS 2종 예

L1 / DEVELOPMENT라도:

```text
주 편집: 02_작업지시서.md
필수 갱신:
- 01_업무정의서.md → CONCISE
- 02_작업지시서.md → CONCISE
```

업무정의서에는 실제 근거가 없다면 상세 Process를 발명하지 않는다. `업무 정책 변경 없음`, `국소 변경`, `주변 영향 없음/확인 필요`처럼 이번 변경에 필요한 최소 정보만 남긴다.

## 11. Customer / PM Projection

Customer/PM View는 내부 Canonical/Evidence에서 파생한 `GENERATED_VIEW`다.

- Customer View가 새 Business Truth를 만들지 않는다.
- Customer 문서 직접 수정이 Canonical을 자동 수정하지 않는다.
- 고객이 의미 변경을 요청하면 Block/문맥을 기준으로 `/change` Round Trip으로 반영한다.
- 고객이 즉시 결정하지 못한 사항은 Customer/Engineering의 적절한 Human Decision Queue에 연결하고 Canonical OPEN/DEFERRED로 유지한다.
- Projection은 Stage/Canonical 의미를 사용하며 특정 Internal Profile의 Artifact ID에 종속시키지 않는다.
- `STALE_VIEW`는 승인 기준에서 제외하고 재생성한다.

## 12. OPEN 해소

OPEN은 대기표시가 아니라 해소할 설계 Backlog다.

- 업무 권위가 필요한 OPEN은 HITL 질문으로 사람의 결정을 받는다.
- 사람이 즉시 답하지 못한 OPEN은 `DEFERRED`로 명시하고 Human Decision Queue에 투영한다.
- Queue는 `Recheck At`에 도달한 다음 Semantic Work에서 신규 질문보다 먼저 재검토한다.
- 기술적으로 조사 가능한 OPEN은 사람에게 묻기 전에 Source/설계 Evidence로 해소한다.
- SOP는 유용한 Evidence지만 필수 입력이 아니다.
- OPEN을 근거 없는 추정으로 닫지 않는다.

상세 절차가 필요할 때만 `.cursor/skills/open-resolve/SKILL.md`를 읽는다.

## 13. Reference — 필요할 때만

Core Reference는 `sdlc/agent/skills/work/references/` 아래에 있다.

일반 `work --target`에서는 이 디렉터리 전체를 읽지 않는다. 다음 경우에만 선택된 Reference 하나 또는 필요한 최소 집합을 읽는다.

- 사용자가 `--stage`를 명시했다.
- `execution_policy.required_semantic_work`가 해당 전문 규칙을 요구한다.
- Change Level escalation으로 추가 설계/영향 규칙이 필요하다.
- Level 사전 지정/승격/강등/이력 또는 `PROFILE_PRIMARY_SET`가 관련되면 `change-level.md`를 읽는다.
- 사람 판단 Gap 또는 carry-forward Queue가 있으면 `hitl.md`를 읽는다.

`.cursor/skills/work/references/`는 Legacy Mirror다. 동일 이름의 Core Reference가 있으면 Core 경로를 우선한다.

## 14. 완료 판정

다음 Runtime 결과가 확인되고 **required Engineering Projection이 모두 갱신됐을 때만** 성공으로 말한다.

- `APPLIED`
- `IDEMPOTENT`
- `NO_CHANGE`
- 검증 목적의 `DRY_RUN_VALIDATED`

다음은 완료가 아니다.

- `INTERACTIVE_HANDOFF_READY`
- `PLAN_READY`
- `HITL_REQUIRED`
- `PROJECTION_REFRESH_REQUIRED`

`ITERATE`/`ALERT` Queue가 남아 있다는 사실 자체는 해당 Semantic Work의 완료를 자동 부정하지 않으며 실제 Guard와 `Recheck At`을 기준으로 판단한다.
