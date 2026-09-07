# Cursor Adapter — /work

이 파일은 Cursor 전용 진입 Adapter다. SDLC `/work`의 업무 규칙과 실행 계약을 중복 정의하지 않는다.

## Canonical Core Skill

반드시 다음 Core Skill을 Source of Truth로 사용한다.

`@sdlc/agent/skills/work/SKILL.md`

HITL 질문/Deferred Queue가 필요하면 다음 Reference만 추가로 읽는다.

`@sdlc/agent/skills/work/references/hitl.md`

Stage Reference 전체를 미리 읽지 않는다. Core Skill의 Context 최소화 규칙과 `work-context.json`의 `execution_policy.required_semantic_work`에 따라 필요한 Reference만 선택한다.

## Cursor 입력 매핑

일반 사용자는 Target만 지정한다.

```bash
/work --target RQ-001
```

현재 Cursor Agent가 Core Skill의 `INTERACTIVE` Agent 역할을 수행한다. `.sdlc/project.yaml`에서 `agent.execution: HEADLESS`가 명시된 경우에만 Harness가 외부 Provider 경로를 사용한다.

## 사용자 UX — 문서 작성이 아니라 질문 응답

Cursor Agent는 생성된 Template을 사용자에게 열어 주고 "채워 달라"고 요청하지 않는다.

기본 UX:

```text
/work 요청
→ Agent가 Canonical / 관련 Source / 기존 Evidence 분석
→ 이전 단계 Human Decision Queue 재확인
→ Agent가 가능한 부분을 먼저 초안 작성
→ 사람 판단이 필요한 Gap만 최대 3개 질문
→ 사용자 자연어 답변 또는 "지금은 확인 불가"
→ 답변 가능: Canonical Delta + Artifact 반영
→ 답변 불가: 같은 Question ID로 문서 Queue + OPEN/DEFERRED에 carry-forward
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
3. `context_path`에서 Target, Change Level, `required_semantic_work`, 필요한 Evidence, 선택 Template만 읽는다.
4. 현재 Target/Artifact의 미해결 Queue와 `Recheck At`을 확인한다.
5. Canonical/Source/Evidence를 먼저 조사하고 Agent 초안을 만든다.
6. 현재 단계에 도달한 기존 Queue를 신규 질문보다 먼저 재확인한다.
7. 사람 판단이 필요한 새 Gap이 있으면 HITL 질문을 생성한다.
8. 사용자가 답하지 못하면 같은 ID로 Queue + OPEN/DEFERRED에 carry-forward한다.
9. 답변이 Semantic 의미를 바꾸면 Canonical Delta/Provenance에 연결한다.
10. 선택 Artifact와 `stage-result.json`을 작성한다.
11. 실제 Source를 수정하는 L1/L2라면 Requirement Intent → AS-IS Source → Impact 분석을 `pre_write_analysis`로 남긴다.
12. 반환된 finalize command를 실행한다.
13. `APPLIED / IDEMPOTENT / NO_CHANGE / DRY_RUN_VALIDATED` 중 하나가 확인된 경우에만 완료로 보고한다.

## Context 최소화

- `sdlc/agent/skills/work/references/` 전체를 읽지 않는다.
- 모든 Template을 읽지 않는다.
- Customer/PM Projection Template을 내부 구현 작업의 기본 Context에 넣지 않는다.
- 전체 Repository를 LLM으로 먼저 읽지 않고 Target과 관련된 Source symbol/file부터 탐색한다.
- L1/L2라도 Intent/AS-IS/Impact 분석은 생략하지 않되 별도 Stage 문서 생성을 강제하지 않는다.
- L3 이상도 `required_semantic_work`에 필요한 Reference만 읽는다.
- HITL 질문/Queue가 실제 필요할 때만 `references/hitl.md`를 읽는다.

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

`Stage / Canonical / Evidence → Tailoring Profile → Human Artifact`

Human Artifact는 입력 Form이 아니라 Agent가 만든 Review Surface다. Human Decision Queue도 이 Review Surface 일부이며 별도 SSOT가 아니다. Customer/PM View는 `GENERATED_VIEW`이며 새 Business Truth를 만들지 않는다. Cursor Adapter가 Stage 이름과 고객사 문서 이름을 1:1로 재정의하지 않는다.

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
