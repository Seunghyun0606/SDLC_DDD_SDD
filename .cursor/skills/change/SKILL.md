# Cursor Adapter — /change

이 파일은 Cursor 전용 `/change` 진입 Adapter다. 실제 업무 규칙은 다음 Core Skill을 사용한다.

`@sdlc/agent/skills/change/SKILL.md`

HITL 질문/Deferred Queue/Block Target 규칙은 다음 Reference를 사용한다.

`@sdlc/agent/skills/work/references/hitl.md`

## 일반 사용자 입력

사용자는 변경 내용을 자연어로 말하면 된다.

```bash
python sdlc/scripts/harness.py change \
  --target <RQ/PGM/TASK/기타 ID> \
  --change '<변경 요청 원문>'
```

이미 생성된 문서의 일부를 바꾸려면 **문서 + Block을 지정하는 방식**을 권장한다.

```text
RQ-0042 Work Unit SDD의 [BLOCK:WU-BUSINESS-RULE]에서
월 마감 정책을 "급여 마감 전까지만 재계산 허용"으로 변경해줘.
```

```text
HRIS 업무정의서의 [BLOCK:HRIS-DATA-AUTH]에서
급여담당 프로파일은 조회만 가능하도록 바꿔줘.
```

## HITL UX

Cursor Agent는 Template 전체를 사용자에게 작성시키지 않는다.

기본 흐름:

```text
/change 요청
→ Agent가 Target/Block의 현재 Canonical 의미 확인
→ 기존 Human Decision Queue + Source/Decision/Evidence 조사
→ Before / Requested After / 영향 후보 정리
→ 현재 Recheck At에 도달한 Queue를 먼저 재확인
→ 정말 필요한 Business Decision만 질문
→ 사용자 답변 또는 "지금은 확인 불가"
→ 답변 가능: Canonical Delta + Provenance
→ 답변 불가: 같은 Question ID로 문서 Queue + OPEN/DEFERRED carry-forward
→ 관련 Projection 갱신
→ finalize
```

질문은 한 턴 최대 3개를 기본으로 하고 다음을 함께 보여준다.

- 왜 이 질문이 필요한지
- 현재 확인된 사실
- 답변이 반영될 `[BLOCK:...]`
- 미응답 시 `SOURCE_BLOCK / ITERATE / ALERT` 중 어떤 영향인지
- 다시 확인할 `Recheck At`

Source에서 확인할 수 있는 Java Method, XML Query, Table/Column, 기존 호출관계는 사람에게 묻지 않고 Agent가 조사한다.

사용자가 `확인 후 답변`, `모르겠다`, `다음 단계에서 다시`라고 하면 변경을 승인/거절한 것으로 해석하지 않는다. Agent가 Human Decision Queue를 갱신하고 Canonical OPEN/DEFERRED로 의미 상태를 유지한다. 다음 `/work` 또는 `/change`에서 `Recheck At`에 도달하면 신규 질문보다 먼저 재확인한다.

## Block Routing

- `SEMANTIC_CHANGE` → `/change` 계속 진행, Canonical Delta 필요
- `EVIDENCE_REFRESH` → `/work`로 전환
- `PROJECTION_ONLY` → 오탈자/표현만 변경, Canonical Delta 없음
- Queue의 일정/상태 조정 → Queue metadata 갱신; 실제 답변은 그 의미에 따라 `/change` 또는 `/work`

Block ID가 없지만 대상이 명확하면 Agent가 해석한 Block을 먼저 알려주고 진행한다. 여러 Block 후보가 있으면 적용 전에 Block 선택만 짧게 확인한다.

## INTERACTIVE 흐름

1. `python sdlc/scripts/harness.py change --target <TARGET> --change "<변경 요청>"`
2. `INTERACTIVE_CHANGE_HANDOFF_READY`를 확인한다. 완료가 아니다.
3. Context에서 Target/Graph/Change Request/Artifact/Canonical baseline을 읽는다.
4. 관련 Canonical/기존 Queue/Source/Evidence를 먼저 조사한다.
5. 현재 `Recheck At`에 도달한 Queue가 있으면 신규 질문보다 먼저 재질문한다.
6. 사람 판단 Gap이 있으면 새 HITL 질문을 생성한다.
7. 답하지 못한 질문은 같은 ID로 Queue + OPEN/DEFERRED에 carry-forward한다.
8. 답변을 `GIVEN`/Decision provenance로 구조화한다.
9. 변경을 `CLARIFICATION / BEHAVIOR_CHANGE / TECHNICAL_CHANGE / NEW_REQUIREMENT`로 분류한다.
10. Change Artifact와 `stage-result.json`을 작성한다.
11. finalize를 실행한다.
12. `APPLIED / IDEMPOTENT / NO_CHANGE / DRY_RUN_VALIDATED`일 때만 완료로 보고한다.

## Business Truth 안전 규칙

- Source 관찰은 `OBSERVED`이며 TO-BE Business Truth가 아니다.
- 기존 `CONFIRMED_BUSINESS` 변경에는 명시적 사용자 authorization과 근거가 필요하다.
- `DEFERRED`는 확정 또는 승인 Evidence가 아니다.
- Block을 지정했다는 사실만으로 상위 Requirement 전체 변경 권한이 생기지 않는다.
- 사용자 답변을 문서 Text에만 반영하고 Canonical/Provenance 반영을 빼먹지 않는다.
- 표현 수정이면 억지 Canonical Delta를 만들지 않는다.

## Plan Only

실제 변경 전에 범위와 기준점만 확인하려면 `--plan-only`를 사용한다. Plan은 Target graph, Canonical base revision, Git baseline, 변경 원문, 허용 Entity 범위, Source write root, Business Truth Guard를 보여준다.

## Stage Result / Canonical 적용

변경 분석도 `/work`와 같은 Stage Result Validator와 locked atomic Canonical apply 경계를 사용한다.

지원 Operation:

- `UPSERT_ENTITY`
- `UPSERT_RELATION`
- `ADD_PROVENANCE`

문서 표현만 바뀌면 `operations: []`과 `no_change_reason`을 사용한다.

## Source Drift / Customer Decision

Source 변화는 자동 Business Truth 변경이 아니다. Reverse Candidate는 Review 후보이며 자동 적용하지 않는다.

Customer Projection에서 받은 실제 업무 변경 의견은 연결된 Canonical Block/의미를 찾은 뒤 `/change` Round Trip으로 반영한다. 즉시 답할 수 없는 고객 결정은 관련 Human Decision Queue에 남겨 다음 합의/설계 경계에서 재확인한다. 단순 문구 수정은 Projection-only로 처리한다.

## Do Not

- Source hash 변화만으로 업무 규칙이 바뀌었다고 판단하지 않는다.
- Change classification만으로 변경 권한을 얻었다고 간주하지 않는다.
- 자동 Merge/commit으로 충돌을 숨기지 않는다.
- `INTERACTIVE_CHANGE_HANDOFF_READY`나 `HITL_REQUIRED`를 완료로 표현하지 않는다.
- 사용자에게 Template 전체를 작성하도록 요구하지 않는다.
- 기술적으로 조사 가능한 질문을 사용자에게 넘기지 않는다.
- 미응답 질문을 대화에만 남기거나 단계마다 새 ID로 복제하지 않는다.
- `DEFERRED`를 Business Truth 승인으로 취급하지 않는다.
