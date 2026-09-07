# Cursor Adapter — /work

이 파일은 Cursor 전용 진입 Adapter다. SDLC `/work`의 업무 규칙과 실행 계약을 중복 정의하지 않는다.

## Canonical Core Skill

반드시 다음 Core Skill을 Source of Truth로 사용한다.

`@sdlc/agent/skills/work/SKILL.md`

HITL 질문/Deferred Queue가 필요하면:

`@sdlc/agent/skills/work/references/hitl.md`

Change Level 사전지정/승격/강등/이력/Projection 재생성이 관련되면:

`@sdlc/agent/skills/work/references/change-level.md`

Stage Reference 전체를 미리 읽지 않는다. Core Skill의 Context 최소화 규칙과 `work-context.json`의 `execution_policy.required_semantic_work`에 따라 필요한 Reference만 선택한다.

## Cursor 입력 매핑

일반 사용자는 Target만 지정한다.

```bash
/work --target RQ-001
```

현재 Cursor Agent가 Core Skill의 `INTERACTIVE` Agent 역할을 수행한다. `.sdlc/project.yaml`에서 `agent.execution: HEADLESS`가 명시된 경우에만 Harness가 외부 Provider 경로를 사용한다.

## Change Level UX

Change Level은 문서 개수가 아니라 **Semantic Work / Evidence / Review 깊이**다. Human Artifact topology는 Tailoring Profile이 결정한다.

작업 시작 시 Agent는 Target별 `sdlc/runtime/change-level/<TARGET>.json`의 다음 값을 확인한다.

- 자동 관측 Level (`observed_change_level`)
- 실제 적용 Level (`effective_change_level`)
- 결정 출처 (`level_source`)
- 안전 하한 (`safety_floor`)
- Level 변경 이력 (`level_history`)

사용자가 자연어로 Level을 지정하거나 바꿀 수 있다.

```text
RQ-001은 L3로 진행해줘. 이유는 업무규칙 검토가 필요해서야.
RQ-001을 L4에서 L2로 낮춰줘. 조회조건 하나만 영향 있는 것으로 확인됐어.
RQ-001 Level override를 해제하고 AUTO로 다시 판단해줘.
```

Agent는 이를 대화에만 기억하지 않고 Change Level Runtime의 `set-level / clear-level` 경계로 기록한다. 자동 downgrade는 금지하지만 **명시적 Human downgrade는 이유와 이력을 남기고 허용**한다. 단 `safety_floor` 아래로 낮출 때는 명시적 Risk Acceptance 없이는 진행하지 않는다.

`.sdlc/project.yaml`에서 사전 지정도 가능하다.

```yaml
change:
  level_policy: AUTO
  minimum_level: L1
  target_levels:
    RQ-001:
      level: L3
      reason: "업무정의서 수준 기능 영향 검토 필요"
```

Level을 변경한 뒤에는 `/work`를 다시 실행해 Semantic Plan과 Projection Update Set을 재계산한다.

## Profile-required 문서 규칙

`tailoring.projection_topologies.internal == PROFILE_PRIMARY_SET`이면 `primary_work_artifact` 하나만 만들고 끝내지 않는다.

- `primary_work_artifact`: 현재 Stage와 가장 직접적으로 맞는 주 편집 문서
- `required_engineering_artifacts` / `projection_update_set`: 이번 작업 후 반드시 존재·갱신해야 하는 Engineering PRIMARY 문서 집합
- `projection_detail`: Change Level에 따른 작성 깊이 (`CONCISE / STANDARD / FULL`)

예를 들어 HRIS 2종 Profile의 L1/DEVELOPMENT에서도:

```text
01_업무정의서.md  → CONCISE로라도 갱신
02_작업지시서.md  → 현재 구현 중심으로 갱신
```

L1이라는 이유로 업무정의서를 누락하지 않는다. 자세한 Process 재설계가 필요하지 않으면 `업무 정책 변경 없음`, `국소 변경`, `영향 없음/확인 필요` 등 실제 근거만 짧게 기록한다.

## 사용자 UX — 문서 작성이 아니라 질문 응답

Cursor Agent는 생성된 Template을 사용자에게 열어 주고 "채워 달라"고 요청하지 않는다.

기본 UX:

```text
/work 요청
→ Change Level 상태/이력/override 확인
→ Agent가 Canonical / 관련 Source / 기존 Evidence 분석
→ Profile-required Projection Update Set 확인
→ 이전 단계 Human Decision Queue 재확인
→ Agent가 가능한 부분을 먼저 초안 작성
→ 사람 판단이 필요한 Gap만 최대 3개 질문
→ 사용자 자연어 답변 또는 "지금은 확인 불가"
→ 답변 가능: Canonical Delta + Artifact 반영
→ 답변 불가: 같은 Question ID로 문서 Queue + OPEN/DEFERRED에 carry-forward
→ required Engineering Projection 모두 갱신
→ 다음 Semantic Work에서 Recheck At 도래 Queue를 신규 질문보다 먼저 재확인
→ finalize
```

질문 전에 Source로 확인할 수 있는 값은 반드시 먼저 조사한다. Java Method, XML Query, Table/Column, 현재 호출관계 같은 기술 Evidence를 사용자에게 작성시키지 않는다.

질문 시에는 다음을 짧게 표시한다.

- 질문이 필요한 이유
- 현재 Agent가 확인한 내용
- 답변이 반영될 `[BLOCK:...]`
- 미응답 시 `SOURCE_BLOCK / ALERT / ITERATE` 중 어떤 영향인지
- 다시 확인할 `Recheck At`

사용자가 `모르겠다`, `확인 후 답하겠다`, `다음 단계에서 다시 보자`라고 하면 답을 강요하지 않는다. Agent가 선택 Artifact의 `Human Decision Queue`를 갱신하고 기존 OPEN 해소 계약의 `OPEN/DEFERRED`로 남긴다. Queue는 사람이 직접 작성하거나 관리하는 별도 원장이 아니다.

## 생성 문서 수정 요청

사용자가 문서에서 수정할 부분을 발견하면 직접 편집보다 Block 지정 지시를 유도한다.

예:

```text
RQ-0042의 [BLOCK:WU-BUSINESS-RULE]에서 월 마감 정책을 이렇게 바꿔줘: ...
```

```text
PGM-001의 [BLOCK:PGM-SOURCE-EVIDENCE]를 현재 Source 기준으로 다시 분석해줘.
```

```text
RQ-0042의 [BLOCK:WU-HITL-QUEUE]에서 HITL-RQ-0042-02는 PROGRAM 단계에서 다시 확인해줘.
```

Agent Routing:

- 의미 변경 → `/change`
- Evidence/Mapping 갱신 → `/work`
- 오탈자/표현만 → Projection-only, Canonical Delta 없음
- Queue 일정/상태만 조정 → Queue metadata 갱신; 실제 답변이면 의미에 따라 `/change` 또는 `/work`

Block 지정이 없지만 문맥이 명확하면 Agent가 해석한 Block을 먼저 알려주고 진행한다. 여러 후보가 있으면 Block만 짧게 확인한다.

## INTERACTIVE 기본 흐름

1. `python sdlc/scripts/harness.py work --target <TARGET>`로 Work Context를 준비한다.
2. `INTERACTIVE_HANDOFF_READY`를 확인한다. 이 상태를 작업 완료로 표현하지 않는다.
3. `context_path`에서 Target, Change Level의 observed/effective/source/history, `required_semantic_work`, 필요한 Evidence를 읽는다.
4. `tailoring.required_engineering_artifacts`와 `projection_update_set`을 확인한다.
5. 현재 Target/Artifact의 미해결 Queue와 `Recheck At`을 확인한다.
6. Canonical/Source/Evidence를 먼저 조사하고 Agent 초안을 만든다.
7. 현재 단계에 도달한 기존 Queue를 신규 질문보다 먼저 재확인한다.
8. 사람 판단이 필요한 새 Gap이 있으면 HITL 질문을 생성한다.
9. 사용자가 답하지 못하면 같은 ID로 Queue + OPEN/DEFERRED에 carry-forward한다.
10. 답변이 Semantic 의미를 바꾸면 Canonical Delta/Provenance에 연결한다.
11. `primary_work_artifact`를 중심으로 작업하되 Profile-required Engineering Artifact를 모두 필요한 깊이로 갱신한다.
12. 실제 Source를 수정하는 L1/L2라면 Requirement Intent → AS-IS Source → Impact 분석을 `pre_write_analysis`로 남긴다.
13. `stage-result.json`을 작성하고 반환된 finalize command를 실행한다.
14. `APPLIED / IDEMPOTENT / NO_CHANGE / DRY_RUN_VALIDATED` 중 하나와 required projection 누락이 없음을 확인한 경우에만 완료로 보고한다.

## Context 최소화

- `sdlc/agent/skills/work/references/` 전체를 읽지 않는다.
- 모든 Template을 읽지 않는다. 단 `required_engineering_artifacts`에 포함된 Template은 갱신 대상이므로 필요한 부분을 읽는다.
- Customer/PM Projection Template을 내부 구현 작업의 기본 Context에 넣지 않는다.
- 전체 Repository를 LLM으로 먼저 읽지 않고 Target과 관련된 Source symbol/file부터 탐색한다.
- L1/L2라도 Intent/AS-IS/Impact 분석은 생략하지 않는다.
- **L1/L2가 Profile-required PRIMARY Engineering 문서를 생략한다는 뜻은 아니다.**
- L3 이상도 `required_semantic_work`에 필요한 Reference만 읽는다.
- HITL 질문/Queue가 실제 필요할 때만 `references/hitl.md`를 읽는다.
- Level 지정/변경/이력 또는 `PROFILE_PRIMARY_SET`가 관련될 때 `references/change-level.md`를 읽는다.

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

OPEN은 대기표시가 아니라 해소할 설계 Backlog다. 업무 권위가 필요한 OPEN은 HITL 질문으로, 사용자가 바로 답하지 못하면 Human Decision Queue + `DEFERRED`로, 기술적으로 조사 가능한 OPEN은 Source/설계 Evidence로 해소한다. 상세 절차가 필요할 때만 `.cursor/skills/open-resolve/SKILL.md`를 사용한다.

## Tailoring 연결

```text
Change Level → Semantic Depth / Evidence / Review
Stage        → Internal execution focus
Profile      → Human Artifact topology
Canonical   → Projection content
```

Human Artifact는 입력 Form이 아니라 Agent가 만든 Review Surface다. Human Decision Queue도 이 Review Surface 일부이며 별도 SSOT가 아니다. Customer/PM View는 `GENERATED_VIEW`이며 새 Business Truth를 만들지 않는다.

## 금지

- Cursor 자체 동작을 Business Truth 근거로 사용하지 않는다.
- Provider가 없다는 이유로 INTERACTIVE 실행을 실패 처리하지 않는다.
- `INTERACTIVE_HANDOFF_READY` 또는 `HITL_REQUIRED`를 완료로 표현하지 않는다.
- 모든 Stage Reference/Template을 선로딩하지 않는다.
- Core Skill/Contract/Validator를 Cursor 전용 규칙으로 재정의하지 않는다.
- OPEN을 근거 없는 추정으로 닫지 않는다.
- 사람에게 Template의 빈칸을 직접 채우도록 요구하지 않는다.
- 기술적으로 조사 가능한 내용을 사람에게 질문하지 않는다.
- 사용자가 답하지 못한 질문을 대화에만 남기고 다음 단계로 넘기지 않는다.
- 같은 미해결 질문을 단계마다 새 ID로 복제하지 않는다.
- 사용자 답변을 문서 Text에만 반영하고 Canonical/Provenance 갱신을 누락하지 않는다.
- Change Level 변경 이유를 대화에만 남기지 않는다.
- AUTO Level이 낮다는 이유로 `PROFILE_PRIMARY_SET`의 PRIMARY 문서를 누락하지 않는다.
