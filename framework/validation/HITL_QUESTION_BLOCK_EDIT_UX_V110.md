# HITL Question / Block Edit UX 검토

기준 Branch: `SDLC_DESIGN_SESSION_FIRST/hris-hunel-engineering/v1.10.1`

## 1. 문제 정의

기존 `/work`와 `/change`는 INTERACTIVE handoff와 Canonical Delta/Guard를 이미 제공하지만, 사람이 실제로 사용하는 UX 관점에서는 다음 Gap이 있었다.

1. Template 빈칸이 많아 사용자가 문서를 직접 작성해야 하는 것처럼 보였다.
2. Agent가 Source에서 조사할 수 있는 내용과 사람에게 물어야 할 업무 결정을 구분하는 명시적 질문 계약이 없었다.
3. 생성 문서에서 사용자가 수정할 때 어떤 의미 단위를 지시해야 Canonical Round-trip이 가능한지 가이드가 없었다.
4. 문서 직접 편집은 Projection 변경과 Canonical Business Truth 변경을 혼동시킬 수 있었다.

## 2. 채택한 UX 원칙

```text
Agent First Research
→ Agent Draft
→ Human Decision Questions Only
→ User Natural-language Answer
→ GIVEN / Decision Provenance
→ Canonical Delta
→ Projection Refresh
```

Human Artifact는 입력 Form이 아니라 Review Surface다.

사람은 Template 전체를 직접 작성하지 않고 다음에 집중한다.

- 업무정책/범위/예외/권한/Acceptance 결정
- Agent 질문에 대한 자연어 답변
- Agent가 생성한 Projection Review
- 특정 Block을 지정한 수정 요청

## 3. 질문 생성 경계

Agent가 사람에게 질문하기 전에 반드시 다음을 우선한다.

1. Canonical 확인
2. 기존 Requirement/Document Evidence 확인
3. Brownfield Source/DB/Config/Trace 조사
4. Project Standard/Decision 확인
5. 초안 작성
6. 그래도 Business Authority가 필요한 Gap만 질문

따라서 Java Method, XML Query, Table/Column, 현재 호출관계처럼 기술적으로 조사 가능한 내용은 HITL 질문으로 넘기지 않는다.

질문은 기본 한 턴 최대 3개로 제한하고, 각 질문에 대상 Block과 이유를 표시한다.

## 4. Block Edit Round-trip

권장 사용자 요청:

```text
RQ-0042 Work Unit SDD의 [BLOCK:WU-BUSINESS-RULE]에서
월 마감 정책을 ...로 변경해줘.
```

Agent Routing:

| 분류 | 의미 | 실행 |
|---|---|---|
| `SEMANTIC_CHANGE` | RQ/Rule/TO-BE/AC/Scope 의미 변경 | `/change` + Canonical Delta |
| `EVIDENCE_REFRESH` | Source/DB/Mapping/AS-BUILT 근거 갱신 | `/work` + Provenance/Evidence |
| `PROJECTION_ONLY` | 오탈자/표현/레이아웃 | Canonical Delta 없음 |

Block ID가 없더라도 문맥이 명확하면 Agent가 해석한 Block을 먼저 표시하고 진행할 수 있다. 여러 후보가 있을 때만 짧게 확인한다.

## 5. Standard Engineering Block ID

### Work Map

- `WM-SUMMARY`
- `WM-UNIT`
- `WM-MAPPING`
- `WM-AC-TEST`
- `WM-OPEN`
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
- `PGM-ASBUILT`

## 6. HRIS Custom Block ID

업무정의서는 `HRIS-*` Stable Block을 사용한다.

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
- `HRIS-HANDOFF`

작업지시서는 기존 구조 자체가 충분히 식별 가능하므로 `A.1`, `A.2`, `B-PROC`, `B-AUTH`, `C.1`, `D.1`, `E.3` 등의 기존 Section ID를 Block ID로 사용한다.

## 7. 변경 파일

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

## 8. Runtime 경계

이번 변경은 새로운 두 번째 Canonical 입력 저장소를 만들지 않는다.

기존 Runtime의 다음 경계를 그대로 사용한다.

- INTERACTIVE work/change handoff
- Stage Result
- Target Graph Guard
- Business Truth Guard
- Canonical Delta
- `UPSERT_ENTITY / UPSERT_RELATION / ADD_PROVENANCE`
- Canonical revision / Git baseline Guard

즉 HITL 답변은 별도의 문서 원장이 아니라 기존 Canonical Delta/Provenance에 흡수한다.

## 9. 현재 의도적으로 하지 않은 것

이번 변경에서는 질문을 별도 Runtime JSON Queue로 저장하거나 `HITL_REQUIRED`를 Validator 필수 상태로 추가하지 않았다.

이유:

1. 현재 사용자는 IDE/대화 Agent와 바로 상호작용하는 INTERACTIVE 모드가 기본이다.
2. Core Canonical Delta/Business Truth Guard가 이미 의미 변경의 실행 경계를 제공한다.
3. 별도 Question Store를 만들면 또 하나의 상태 원장과 동기화 문제가 생긴다.

향후 완전 HEADLESS orchestration, Web UI Question Inbox, 비동기 승인 Queue가 필요해지는 경우에만 Machine-readable HITL Queue Contract를 별도 Capability로 추가한다.

## 10. 검증 상태

정적 회귀 테스트 `tests/test_hitl_block_edit_ux.py`를 추가하여 다음을 고정한다.

- Core `/work`와 `/change`가 HITL Reference를 사용함
- Cursor Adapter가 같은 UX를 노출함
- Standard Engineering Template에 Stable Block ID가 존재함
- HRIS Custom Template이 Block Target을 제공함
- 사용자 가이드가 Block → `/work`/`/change` → Canonical Round-trip을 설명함
- Template을 직접 채우도록 요구하지 않는 원칙이 유지됨

Remote CI 실행 결과가 확인되기 전에는 이 문서를 CI PASS 증거로 사용하지 않는다.
