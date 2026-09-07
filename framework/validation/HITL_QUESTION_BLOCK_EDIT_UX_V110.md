# HITL Question / Block Edit / Deferred Queue UX 검토

기준 Branch: `SDLC_DESIGN_SESSION_FIRST/hris-hunel-engineering/v1.10.1`

## 1. 문제 정의

기존 `/work`와 `/change`는 INTERACTIVE handoff와 Canonical Delta/Guard를 이미 제공하지만, 사람이 실제로 사용하는 UX 관점에서는 다음 Gap이 있었다.

1. Template 빈칸이 많아 사용자가 문서를 직접 작성해야 하는 것처럼 보였다.
2. Agent가 Source에서 조사할 수 있는 내용과 사람에게 물어야 할 업무 결정을 구분하는 명시적 질문 계약이 없었다.
3. 생성 문서에서 사용자가 수정할 때 어떤 의미 단위를 지시해야 Canonical Round-trip이 가능한지 가이드가 없었다.
4. 문서 직접 편집은 Projection 변경과 Canonical Business Truth 변경을 혼동시킬 수 있었다.
5. **사용자가 질문에 즉시 답하지 못하면 질문이 현재 대화에서 유실되거나 다음 단계 Agent가 다시 확인하지 못할 수 있었다.**

## 2. 채택한 UX 원칙

```text
Agent First Research
→ Existing Deferred Queue Recheck
→ Agent Draft
→ Human Decision Questions Only
→ User Natural-language Answer OR Defer
→ Answer: GIVEN / Decision Provenance → Canonical Delta
→ Defer: Human Decision Queue → Canonical OPEN/DEFERRED
→ Projection Refresh
→ Next Semantic Work rechecks due Queue before new questions
```

Human Artifact는 입력 Form이 아니라 Review Surface다.

사람은 Template 전체를 직접 작성하지 않고 다음에 집중한다.

- 업무정책/범위/예외/권한/Acceptance 결정
- Agent 질문에 대한 자연어 답변
- 즉시 답할 수 없을 때 `확인 후 답변`, `다음 단계 재확인` 의사 표시
- Agent가 생성한 Projection Review
- 특정 Block을 지정한 수정 요청

## 3. 질문 생성 경계

Agent가 사람에게 질문하기 전에 반드시 다음을 우선한다.

1. Canonical 확인
2. 현재 Target의 미해결 Human Decision Queue 확인
3. 기존 Requirement/Document Evidence 확인
4. Brownfield Source/DB/Config/Trace 조사
5. Project Standard/Decision 확인
6. 초안 작성
7. 그래도 Business Authority가 필요한 Gap만 질문

따라서 Java Method, XML Query, Table/Column, 현재 호출관계처럼 기술적으로 조사 가능한 내용은 HITL 질문으로 넘기지 않는다.

질문은 기본 한 턴 최대 3개로 제한하고, 각 질문에 대상 Block과 이유를 표시한다. 현재 `Recheck At`에 도달한 기존 Queue는 신규 질문보다 먼저 처리한다.

## 4. Deferred Human Decision Queue

사용자가 `모르겠다`, `확인 후 답하겠다`, `다음 단계에서 다시 보자`라고 하면 Agent는 답을 추정하지 않는다.

선택 Artifact에 다음 Human View를 남긴다.

| 필드 | 목적 |
|---|---|
| Queue ID | 원래 `HITL-<TARGET>-<NN>` Question ID를 유지하여 중복 방지 |
| Related Block | 최종 답변이 반영될 Stable Block |
| 질문 / 결정 필요사항 | 사람이 나중에 답할 내용 |
| 현재 확인값 / 제안 | Evidence/Proposal. 확정값 아님 |
| 결정 담당 | 실제 Project Authority |
| 영향 분류 | `SOURCE_BLOCK / ITERATE / ALERT` |
| Recheck At | 다음 Semantic Work 또는 `BEFORE_SOURCE_WRITE / BEFORE_TEST / BEFORE_VERIFY` |
| 상태 | 미확정 / 확인중 / 제안 / 보류 / 확정 |

### 4.1 Canonical 의미 보존

새 Question Store를 만들지 않는다. 기존 `sdlc/design/contracts/open-resolution-contract.json`을 재사용한다.

- resolution method: `DEFER`
- unresolved status: `OPEN`
- 명시적 보류: `DEFERRED`
- human mapping: `DEFERRED → 보류`
- non-blocking rule: 가능한 설계는 계속하되 미해소 항목을 구현 Guard에 반영

따라서 구조는 다음과 같다.

```text
Canonical OPEN / DEFERRED / Decision Provenance   # 의미 상태
                  ↓ projection
Human Decision Queue in Engineering/Customer doc  # 사람이 보는 Review Surface
```

문서 Queue가 Business Truth를 별도로 소유하지 않는다.

### 4.2 다음 단계 Carry-forward

다음 Semantic Work Agent는 다음 순서로 Queue를 처리한다.

1. Target/Artifact의 미해결 Queue를 읽는다.
2. Canonical/Evidence에서 이미 해소됐는지 확인한다.
3. 기술 조사로 해소 가능하면 사람에게 다시 묻기 전에 조사한다.
4. `Recheck At`이 현재 경계인 사람 소유 Queue를 신규 질문보다 먼저 재확인한다.
5. 아직 답이 없으면 같은 Queue ID로 상태/다음 `Recheck At`만 갱신한다.
6. 답을 받으면 `GIVEN`/Decision provenance와 필요한 Canonical Delta를 만든다.
7. Queue를 확정/해소하고 이후 Projection을 갱신한다.

Queue의 나이만으로 자동 `SOURCE_BLOCK` 승격하지 않는다. 실제 downstream 위험이 생길 때 영향 분류를 재평가한다.

### 4.3 실행 영향

- `SOURCE_BLOCK`: 해당 결정에 의존하는 Source/Action만 제한
- `ITERATE`: 다음 단계 진행 가능, 지정된 경계에서 재확인
- `ALERT`: 진행 가능, 계속 노출/추적

## 5. Block Edit Round-trip

권장 사용자 요청:

```text
RQ-0042 Work Unit SDD의 [BLOCK:WU-BUSINESS-RULE]에서
월 마감 정책을 ...로 변경해줘.
```

```text
RQ-0042 Work Unit SDD의 [BLOCK:WU-HITL-QUEUE]에서
HITL-RQ-0042-02는 PROGRAM 단계에서 다시 확인해줘.
```

Agent Routing:

| 분류 | 의미 | 실행 |
|---|---|---|
| `SEMANTIC_CHANGE` | RQ/Rule/TO-BE/AC/Scope 의미 변경 | `/change` + Canonical Delta |
| `EVIDENCE_REFRESH` | Source/DB/Mapping/AS-BUILT 근거 갱신 | `/work` + Provenance/Evidence |
| Queue metadata | Recheck At/상태만 변경 | Queue/Open metadata 갱신, Business Truth 변화 없음 |
| Queue answer | 실제 업무/기술 답변 | 답변 의미에 따라 `/change` 또는 `/work` |
| `PROJECTION_ONLY` | 오탈자/표현/레이아웃 | Canonical Delta 없음 |

Block ID가 없더라도 문맥이 명확하면 Agent가 해석한 Block을 먼저 표시하고 진행할 수 있다. 여러 후보가 있을 때만 짧게 확인한다.

## 6. Standard Engineering Block ID

### Work Map

- `WM-SUMMARY`
- `WM-UNIT`
- `WM-MAPPING`
- `WM-AC-TEST`
- `WM-OPEN`
- `WM-HITL-QUEUE`
- `WM-NEXT`

### Work Unit SDD

- `WU-INTENT`
- `WU-ASIS`
- `WU-TOBE`
- `WU-BUSINESS-RULE`
- `WU-IMPACT`
- `WU-MAPPING`
- `WU-TECH-IMPACT`
- `WU-DEV-CONTRACT`
- `WU-AC-TEST`
- `WU-OPEN-GUARD`
- `WU-HITL-QUEUE`
- `WU-ASBUILT`
- `WU-VERIFY`

### Program Spec

- `PGM-INTENT`
- `PGM-TARGET`
- `PGM-SOURCE-EVIDENCE`
- `PGM-DELTA`
- `PGM-CONDITIONAL`
- `PGM-SOURCE-BOUNDARY`
- `PGM-TRACE`
- `PGM-READINESS`
- `PGM-HITL-QUEUE`
- `PGM-ASBUILT`

## 7. HRIS Custom Block ID

업무정의서는 `HRIS-*` Stable Block을 사용하며 `HRIS-HITL-QUEUE`를 포함한다.

- `HRIS-INTENT`
- `HRIS-REQUIREMENT`
- `HRIS-ASIS`
- `HRIS-TOBE`
- `HRIS-BUSINESS-RULE`
- `HRIS-DATA-AUTH`
- `HRIS-INTEGRATION-NFR`
- `HRIS-AC`
- `HRIS-IMPACT`
- `HRIS-OPEN`
- `HRIS-HITL-QUEUE`
- `HRIS-HANDOFF`

작업지시서는 기존 Section ID와 별도 `HITL-QUEUE` Block을 사용한다. 특히 `B-PROC`, `B-AUTH`, `D.1` 같은 구현 경계의 보류 Decision을 `BEFORE_SOURCE_WRITE`로 이월할 수 있다.

## 8. 변경 파일

- `sdlc/agent/skills/work/references/hitl.md`
- `sdlc/agent/skills/work/SKILL.md`
- `sdlc/agent/skills/change/SKILL.md`
- `.cursor/skills/work/SKILL.md`
- `.cursor/skills/change/SKILL.md`
- `sdlc/templates/engineering/standard/00_work-map.md`
- `sdlc/templates/engineering/standard/work-unit-sdd.md`
- `sdlc/templates/engineering/standard/program-spec.md`
- `sdlc/custom/project/templates/hris-hunel/01_업무정의서.md`
- `sdlc/custom/project/templates/hris-hunel/02_작업지시서.md`
- `docs/00_시작/04_TEMPLATE_및_산출물_가이드.md`
- `docs/00_시작/05_이해관계자별_작업가이드.md`
- `tests/test_hitl_block_edit_ux.py`
- `framework/validation/HITL_QUESTION_BLOCK_EDIT_UX_V110.md`

## 9. Runtime / Contract 경계

이번 변경은 새로운 두 번째 Canonical 입력 저장소를 만들지 않는다.

기존 Runtime/Contract의 다음 경계를 그대로 사용한다.

- INTERACTIVE work/change handoff
- Stage Result
- Target Graph Guard
- Business Truth Guard
- Canonical Delta
- `UPSERT_ENTITY / UPSERT_RELATION / ADD_PROVENANCE`
- Canonical revision / Git baseline Guard
- `open-resolution-contract.json`의 `OPEN / DEFERRED / DEFER`

즉 HITL 답변은 기존 Canonical Delta/Provenance에 흡수하고, 미응답은 기존 OPEN/DEFERRED 의미 상태에 남긴다. 문서 Queue는 그 상태의 Human-facing Projection이다.

## 10. 현재 의도적으로 하지 않은 것

이번 변경에서는 별도 Runtime JSON Question Store 또는 비동기 승인 Inbox를 만들지 않았고 `HITL_REQUIRED`를 Validator 필수 상태로 추가하지 않았다.

이유:

1. 현재 기본은 IDE/대화 Agent와 바로 상호작용하는 INTERACTIVE 모드다.
2. 기존 OPEN Resolution Contract가 `DEFER / DEFERRED`와 downstream impact를 이미 표현한다.
3. 문서 Queue + Canonical OPEN을 분리하면 Human Review와 의미 SSOT를 동시에 만족할 수 있다.
4. 별도 Question Store를 만들면 또 하나의 상태 원장과 동기화 문제가 생긴다.

향후 완전 HEADLESS orchestration, Web UI Question Inbox, 비동기 승인 Queue가 필요해지는 경우에만 Machine-readable HITL Queue Capability를 별도로 검토한다.

## 11. 검증 상태

정적 회귀 테스트 `tests/test_hitl_block_edit_ux.py`를 갱신하여 다음을 고정한다.

- Core `/work`와 `/change`가 HITL Reference를 사용함
- Cursor Adapter가 같은 Deferred Queue UX를 노출함
- 기존 `open-resolution-contract.json`에 `DEFER / DEFERRED`가 존재하고 이를 재사용함
- Standard Engineering Template에 Stable Queue Block이 존재함
- HRIS Custom Template에 Queue Block이 존재함
- `Recheck At`이 다음 Semantic Work 재확인 경계를 표현함
- 기존 Queue를 신규 질문보다 먼저 확인하도록 명시함
- 사용자 가이드가 `지금 답변 불가 → Queue → 다음 단계 재확인` 흐름을 설명함
- Template을 직접 채우도록 요구하지 않는 원칙이 유지됨

Remote CI 실행 결과가 확인되기 전에는 이 문서를 CI PASS 증거로 사용하지 않는다.
