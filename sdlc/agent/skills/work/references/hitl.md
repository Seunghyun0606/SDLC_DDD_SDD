# HITL Interaction Reference — Agent Question Driven UX

## 0. 사람에게 보여주는 표현이 최우선

HITL 내부 상태와 Runtime 연결에는 기존 machine code를 유지한다. 하지만 **사용자 질문, 답변 안내, 사람용 문서 본문에는 machine code를 그대로 노출하지 않는다.**

표현 기준:
- `sdlc/design/contracts/human-facing-language-contract.json`
- `sdlc/agent/skills/work/references/human-language.md`

예:

| 내부 의미 | 사용자에게 보여줄 표현 |
|---|---|
| `DEFERRED` | 보류 |
| `OPEN` | 확인 필요 |
| `SOURCE_BLOCK` | 개발 전 확인 필요 |
| `ITERATE` | 진행 가능·추후 보완 |
| `ALERT` | 주의 필요 |
| `Recheck At` | 다시 확인할 시점 |
| `Human Decision Queue` | 추가 확인이 필요한 사항 |
| `Canonical` | 기준 정보 |
| `Projection` | 생성 문서 |
| `Provenance` | 근거 이력 |
| `Evidence` | 근거 |
| 영속적 / 영속성 | 저장 후 계속 유지되는 / 저장 여부 |

내부 코드는 Agent/Runtime이 처리한다. 사용자가 해당 코드를 이해해야 답할 수 있는 질문을 만들면 안 된다.

질문은 가능하면 다음처럼 보여준다.

```text
[질문 1]
왜 확인이 필요한가: 승인 후 취소 가능 여부에 따라 저장 로직과 테스트 기준이 달라집니다.
현재 확인한 내용: 현재 시스템에서는 승인 후 취소 기능을 확인하지 못했습니다.
확인이 필요한 내용: 개선 후 승인 완료 건의 취소를 허용할까요?
선택 가능한 내용: ① 허용하지 않음 ② 관리자만 허용
답하지 못할 때 처리: 지금 결정하지 않아도 됩니다. 다만 개발 전에 다시 확인해야 합니다.
다시 확인할 시점: 개발 시작 전
```

다음처럼 묻지 않는다.

```text
이 값을 DB에 영속적으로 보관합니까?
DEFERRED로 둘까요?
SOURCE_BLOCK으로 두고 Recheck At을 DEVELOPMENT로 지정할까요?
```

대신 다음처럼 묻는다.

```text
이 값은 처리 후 DB에 저장되어 계속 유지되어야 하나요?
지금 결정하기 어렵다면 보류하고 다음 작업에서 다시 확인할까요?
이 내용은 개발 전에 확인해야 합니다. 개발 시작 전에 다시 확인할까요?
```

## 1. 목적

`/work`와 `/change`에서 사람에게 Template 빈칸을 직접 채우게 하지 않는다.

기본 UX는 다음 순서다.

```text
Agent가 Canonical / Source / 기존 문서 / Evidence를 먼저 읽음
→ Agent가 가능한 항목을 먼저 초안 작성
→ 사람의 업무 판단이 필요한 Gap만 질문으로 생성
→ 사용자는 질문에 자연어로 답변하거나 "지금 결정 못함"으로 보류
→ 즉시 답변이면 Agent가 Evidence/Decision으로 구조화
→ 미응답이면 문서의 Human Decision Queue + Canonical OPEN/DEFERRED로 carry-forward
→ Canonical Delta 작성 및 Guard 통과
→ Engineering/Customer Projection 재생성 또는 갱신
→ 다음 Semantic Work 진입 시 미해결 Queue를 신규 질문보다 먼저 재검토
```

문서는 **입력 Form이 아니라 Review Surface**다.

사람은 다음을 하지 않는다.

- Template의 빈 표를 처음부터 직접 채우기
- Canonical JSON 직접 수정
- Stage Result 직접 작성
- Source Hash / Trace / Locator 같은 Machine Evidence 수동 관리
- 지금 답을 모른다는 이유로 임의의 업무정책을 확정

## 2. 질문 생성 원칙

Agent는 질문 전에 반드시 다음 순서를 따른다.

1. 현재 Canonical에 이미 답이 있는지 확인한다.
2. 이전 단계에서 carry-forward된 `Human Decision Queue`가 있는지 확인한다.
3. Source / DB / Config / 기존 문서에서 기술적으로 확인 가능한지 조사한다.
4. 프로젝트 표준 또는 명시적 기존 Decision으로 결정 가능한지 확인한다.
5. 그래도 **사람의 업무 권위 또는 선택이 필요한 경우에만** 질문한다.

즉 기술적으로 조사할 수 있는 질문을 사람에게 떠넘기지 않는다.

### 질문하지 않아야 하는 예

- 실제 Java Method 이름은 무엇인가? → Source에서 조사
- 어떤 XML Query가 호출되는가? → Source에서 조사
- 현재 Table Column은 무엇인가? → DB/Source Evidence에서 조사
- 기존 화면이 어떤 권한 함수를 호출하는가? → Source에서 조사

### 사람에게 질문해야 하는 예

- 승인 후 취소를 허용할 것인가?
- 월 마감 이후 재계산 정책은 무엇인가?
- 특정 프로파일이 수정 권한을 가져야 하는가?
- 두 가지 개선 대안 중 어느 정책을 선택할 것인가?
- 고객이 요구한 범위를 이번 배포에 포함할 것인가?

## 3. 질문 묶음 UX

한 번에 Template 전체를 질문하지 않는다.

- 기본 한 턴 최대 3개 질문
- 같은 Decision Cluster는 한 묶음으로 제시
- Source 조사로 줄일 수 있는 질문은 먼저 제거
- **현재 단계에 재확인 시점이 도래한 기존 Queue를 신규 질문보다 먼저 제시**
- 사용자의 앞선 답변으로 파생되는 후속 질문만 다음 턴에 제시
- 중요하지 않은 UI 표현은 내부적으로 `ITERATE`로 남기고 진행 가능

### 3.1 사용자에게 보여주는 질문 구조

| 사용자 표시 항목 | 의미 |
|---|---|
| 질문 번호 | 같은 질문을 다시 확인할 때 구분하기 위한 번호 |
| 왜 확인이 필요한가 | 현재 진행에서 이 결정이 필요한 이유 |
| 현재 확인한 내용 | Source/문서/기존 결정에서 확인한 사실 |
| 확인이 필요한 내용 | 사용자가 판단할 한 가지 내용 |
| 선택 가능한 내용 | 실제 근거가 있을 때만 제시; 강제하지 않음 |
| 답하지 못할 때 처리 | 지금 보류 가능한지, 어떤 작업 전에 결정해야 하는지 |
| 다시 확인할 시점 | 다음 작업 / 설계 / 개발 시작 전 / 테스트 전 / 최종 검증 전 |

사용자에게는 Machine 필드명을 그대로 강요하지 않고 자연어로 보여준다.

### 3.2 내부 연결 구조

내부적으로는 다음 필드를 유지할 수 있다.

| 내부 필드 | 의미 |
|---|---|
| Question ID | `HITL-<TARGET>-<NN>`; Queue로 이월되어도 같은 ID 유지 |
| 대상 Block | 답변이 반영될 문서/Canonical 의미 Block |
| 현재 알고 있는 것 | GIVEN / OBSERVED / CONFIRMED / INFERRED 구분 |
| 미응답 시 처리 | SOURCE_BLOCK / ALERT / ITERATE + OPEN/DEFERRED |
| Recheck At | 다시 확인할 Semantic Work/실행 경계 |

이 표는 Agent/Runtime용이다. 일반 사용자에게 그대로 출력하지 않는다.

## 4. 사용자가 바로 답하지 못하는 경우 — Human Decision Queue

사용자가 `모르겠다`, `확인 후 답하겠다`, `지금 결정하기 어렵다`, `다음 단계에서 다시 보자`처럼 답하면 Agent는 답을 강요하거나 추정하지 않는다.

해당 질문을 내부적으로 **Human Decision Queue**로 전환하고 선택된 Engineering/Customer Review Surface의 Queue Block에 Agent가 기록한다. 사용자가 표를 직접 관리하지 않는다.

사람용 문서에서는 이 영역의 제목을 `추가 확인이 필요한 사항`으로 표시한다.

사람이 보는 최소 항목:

| 항목 | 의미 |
|---|---|
| 질문 번호 | 기존 질문 번호를 그대로 사용하여 중복 질문 방지 |
| 확인 필요사항 | 사람이 나중에 답해야 할 한 가지 결정 |
| 현재 확인 내용 / 제안 | 현재 근거와 Agent 제안; 확정값처럼 쓰지 않음 |
| 확인 담당 | 실제 결정을 할 담당자 |
| 개발 영향 | 개발 전 확인 필요 / 진행 가능·추후 보완 / 주의 필요 |
| 다시 확인할 시점 | 다음에 반드시 재확인할 작업 시점 |
| 상태 | 확인 필요 / 확인 중 / 제안 / 보류 / 확정 |

Machine 의미는 기존 `sdlc/design/contracts/open-resolution-contract.json`을 재사용한다.

- 즉시 미확정: `OPEN`
- 사용자가 나중에 답하기로 명시: `DEFERRED` / resolution method `DEFER`
- Agent가 Source로 조사 중: `ANALYZING`
- Agent 대안 제안만 존재: `PROPOSED`
- 사람 결정 완료: 적절한 Authority/Evidence에 따라 `CONFIRMED_BUSINESS` 또는 `ACCEPTED_DESIGN`

**별도의 Question Store나 두 번째 Business Truth 원장을 만들지 않는다.** 문서 Queue는 Human-facing Projection이며 실제 의미 보존은 기존 OPEN/Decision/Provenance 계약으로 연결한다.

### 4.1 Recheck At 결정

Agent가 다음 중 가장 이른 의미 있는 경계를 내부적으로 지정한다.

- `NEXT_SEMANTIC_WORK`: 다음 작업 시작 시
- 특정 의미 작업: `PROCESS`, `IMPACT`, `DESIGN`, `PROGRAM`, `DEVELOPMENT`, `TEST`, `VERIFY`
- `BEFORE_SOURCE_WRITE`: 소스 변경 전에 반드시 결정 필요
- `BEFORE_TEST`: 기대결과/AC가 테스트 실행 전에 필요
- `BEFORE_VERIFY`: 최종 승인/위험 수용 판단이 최종 검증 전에 필요

사용자 문서에는 위 code 대신 `다음 작업`, `상세설계`, `프로그램설계`, `개발 시작 전`, `테스트 전`, `최종 검증 전`처럼 표시한다.

단순히 시간이 지났다는 이유로 `SOURCE_BLOCK`으로 자동 승격하지 않는다. 실제 downstream 실행 위험이 커질 때만 Guard를 강화한다.

### 4.2 다음 단계 진입 시 Queue 재확인 순서

새 Semantic Work/Stage를 시작하는 Agent는 반드시 다음 순서로 수행한다.

1. Target과 연결된 현재 Artifact에서 미해결 Human Decision Queue를 읽는다.
2. Queue와 연결된 Canonical OPEN/DEFERRED가 이미 다른 Evidence로 해소됐는지 확인한다.
3. Source/DB/Config 조사로 해소 가능한 항목은 **사람에게 다시 묻기 전에 Agent가 조사**한다.
4. `Recheck At`이 현재 단계 또는 현재 실행 경계에 도달한 사람 소유 항목은 신규 HITL 질문보다 먼저 재질문한다.
5. 사용자가 여전히 답하지 못하면 같은 Queue ID를 유지하고 상태/`Recheck At`만 갱신한다. 새 행을 중복 생성하지 않는다.
6. 답변을 받으면 Queue를 `확정`으로 갱신하고 `GIVEN`/Decision provenance 및 필요한 Canonical Delta를 만든다.
7. Queue 해소 결과를 현재 Artifact와 이후 Projection에 반영한다.

### 4.3 미응답 상태에서 진행 가능 범위

- `SOURCE_BLOCK`: **해당 결정에 의존하는 Source/Action만 제한**한다. 사용자에게는 `개발 전 확인 필요`로 표시한다.
- `ITERATE`: 큰 방향이 확정되어 다음 단계로 진행 가능하지만 `Recheck At` 이전에 재검토한다. 사용자에게는 `진행 가능·추후 보완`으로 표시한다.
- `ALERT`: 현재 실행을 제한하지 않지만 다음 단계 Review Surface에서 계속 노출한다. 사용자에게는 `주의 필요`로 표시한다.
- 업무 Business Truth는 사용자가 답하지 않았다는 이유로 `ASSUMED` 값으로 조용히 확정하지 않는다.

## 5. Semantic Work별 질문 기준

아래 표는 Agent 내부 기준이다. 사람에게 질문할 때는 작업 단계 code를 빼고 업무 의미만 보여준다.

| Semantic Work / Stage | Agent가 먼저 할 일 | 사람에게 물을 수 있는 핵심 | 기본 미응답 처리 |
|---|---|---|---|
| INTAKE | 입력자료 요약, 중복/기존 RQ 확인 | 현재 문제, 원하는 결과, 반드시 유지할 조건 중 불명확한 것 | OPEN → Queue |
| DECOMPOSE | 요구를 행동/결과/AC 후보로 분해 | 한 RQ인지 여러 업무 변경인지, 범위 경계가 업무적으로 애매한 경우 | OPEN → Queue |
| CLARIFY | Source/문서로 답 가능한 질문 제거 | 정책, 예외, 우선순위, 업무 용어 등 Business Authority 필요사항 | SOURCE_BLOCK 또는 ITERATE → Queue |
| PROCESS | AS-IS/TO-BE 흐름 후보 작성 | Actor, Trigger, 상태전이, 예외 정책 중 업무 결정 | SOURCE_BLOCK → Queue |
| DISCOVERY | Source/DB/Interface Evidence 조사 | Source 접근 불가, 외부 시스템 사실처럼 사람이 제공해야 하는 Evidence | ALERT / Coverage Gap → Queue |
| IMPACT | Technical/Functional Candidate 분석 | 실제 업무 영향 포함/제외, 운영 영향 수용 여부 | SOURCE_BLOCK 또는 ALERT → Queue |
| DESIGN | 동작/Validation/권한/예외 초안 | TO-BE 정책 선택, 권한/상태/예외의 업무 결정 | SOURCE_BLOCK → Queue |
| PROGRAM | 기존 Architecture/유사 Program/표준 조사 | 신규 Program 분리, Architecture Exception 등 사람 승인 필요 결정 | SOURCE_BLOCK → Queue |
| DEVELOPMENT | Source Write 준비도와 Open 확인 | 아직 남은 업무/보안/데이터 Guard 결정만 질문 | SOURCE_BLOCK, `BEFORE_SOURCE_WRITE` |
| TEST | AC에서 Test 자동 생성 | 기대결과 또는 합격 기준 자체가 불명확한 경우 | SOURCE_BLOCK, `BEFORE_TEST` |
| VERIFY | Spec/Source/Test 차이 정리 | 계획 대비 차이를 승인할지, 미해결 Risk를 수용할지 | DEFERRED, `BEFORE_VERIFY` |
| KNOWLEDGE_PROMOTION | 재사용 후보와 Evidence 정리 | 장기 업무 규칙으로 승격할지 사람이 확정해야 하는 지식 | REVIEW / DEFERRED |
| CHANGE | 현재 Block/Canonical 값과 영향 조사 | 무엇이 실제로 달라졌는지, 표현 수정인지 Business Truth 수정인지 애매한 경우 | 변경 적용 보류 + Queue |

Stage 이름은 내부 Taxonomy다. 일반 사용자는 Stage를 고르지 않고 Agent가 현재 `required_semantic_work`에 맞는 질문만 생성한다.

## 6. 답변 처리 규칙

사용자의 답변을 받은 Agent는 문서만 고치지 않는다.

1. 답변을 `GIVEN`으로 기록한다.
2. 기존 `CONFIRMED_BUSINESS`와 충돌하면 `/change` 의미로 전환하거나 명시적 변경 authorization을 확인한다.
3. 새 Decision/Rule/AC/Scope가 되면 해당 Canonical Entity/Relation Delta를 만든다.
4. 단순 표현 수정이면 Canonical Delta를 만들지 않는다.
5. 대응 Queue가 있으면 같은 Queue ID를 `확정` 처리하고 OPEN/DEFERRED를 해소한다.
6. Canonical Apply가 성공한 뒤 Projection을 갱신한다.
7. 어떤 답변이 어떤 Block/Canonical 항목에 반영됐는지 사용자에게는 쉬운 한국어로 짧게 알려준다.

## 7. 문서 Block Target 규칙

생성 문서를 수정하고 싶을 때 사용자는 문서를 직접 고치기보다 **문서 + Block을 지정해서 Agent에게 지시**한다.

권장 문법:

```text
<문서 또는 Target>의 [BLOCK:<BLOCK-ID>]를 <변경 내용>으로 수정해줘.
```

예:

```text
RQ-0042 업무정의서의 [BLOCK:WU-BUSINESS-RULE]에서
"월 마감 이후 자동 재계산 금지"를 "급여 마감 전까지만 자동 재계산 허용"으로 변경해줘.
```

```text
PGM-ATT-0016 Program Spec의 [BLOCK:PGM-SOURCE-EVIDENCE]를
현재 Source 기준으로 다시 분석해서 갱신해줘.
```

```text
RQ-0042 Work Unit SDD의 [BLOCK:WU-HITL-QUEUE]에서
HITL-RQ-0042-02는 아직 고객 확인이 안 됐으니 PROGRAM 단계에서 다시 물어봐줘.
```

### Block 수정 Routing

Agent는 Block 요청을 다음 셋 중 하나로 분류한다.

- `SEMANTIC_CHANGE`: Requirement / Business Rule / TO-BE / AC / Scope 의미가 바뀜 → `/change` + Canonical Delta
- `EVIDENCE_REFRESH`: Source/DB/Mapping/AS-BUILT 근거를 다시 분석 → `/work` + Evidence/Provenance 갱신
- `PROJECTION_ONLY`: 오탈자/표현/레이아웃만 변경 → Canonical Delta 없음

Queue의 `Recheck At`/상태 변경은 Business Truth 자체가 아니므로 Queue metadata 갱신으로 처리한다. Queue 질문에 실제 답을 주면 해당 답변의 Semantic 의미에 따라 `/change` 또는 `/work`로 Routing한다.

애매하면 Agent가 한 번의 짧은 확인 질문으로 Routing을 확정한다.

## 8. Stable Block ID 권장 체계

Standard Engineering Projection:

- `WM-SUMMARY`, `WM-UNIT`, `WM-MAPPING`, `WM-AC-TEST`, `WM-OPEN`, `WM-HITL-QUEUE`
- `WU-INTENT`, `WU-ASIS`, `WU-TOBE`, `WU-BUSINESS-RULE`, `WU-IMPACT`, `WU-MAPPING`, `WU-TECH-IMPACT`, `WU-DEV-CONTRACT`, `WU-AC-TEST`, `WU-OPEN-GUARD`, `WU-HITL-QUEUE`, `WU-ASBUILT`, `WU-VERIFY`
- `PGM-INTENT`, `PGM-TARGET`, `PGM-SOURCE-EVIDENCE`, `PGM-DELTA`, `PGM-CONDITIONAL`, `PGM-SOURCE-BOUNDARY`, `PGM-TRACE`, `PGM-READINESS`, `PGM-HITL-QUEUE`, `PGM-ASBUILT`

HRIS/hunel Custom Projection:

- 업무정의서: `HRIS-INTENT`, `HRIS-REQUIREMENT`, `HRIS-ASIS`, `HRIS-TOBE`, `HRIS-BUSINESS-RULE`, `HRIS-DATA-AUTH`, `HRIS-INTEGRATION-NFR`, `HRIS-AC`, `HRIS-IMPACT`, `HRIS-OPEN`, `HRIS-HITL-QUEUE`, `HRIS-HANDOFF`
- 작업지시서: 기존 구조 ID와 `HITL-QUEUE`를 사용한다. `A.1`, `A.2`, `A.3`, `A.4`, `B-SHEET`, `B-TAB`, `B-VUE`, `B-APPL`, `B-PROC`, `B-POPUP`, `B-DYNAMIC`, `B-AUTH`, `B-MIGRATION`, `C.1`, `C.2`, `C.3`, `D.1`, `D.2`, `D.3`, `HITL-QUEUE`, `E.1`, `E.2`, `E.3`

## 9. 금지 UX

- "Template을 열고 1~12번 Section을 작성해 주세요"라고 사용자에게 요구하지 않는다.
- Source에서 확인 가능한 값을 사람에게 질문하지 않는다.
- 사용자가 즉시 답하지 못한다고 해서 근거 없는 값을 확정하지 않는다.
- 미응답 질문을 현재 대화에서만 기억하고 Artifact/OPEN에 남기지 않은 채 다음 단계로 넘기지 않는다.
- 같은 미해결 질문을 단계마다 새 Question ID로 중복 생성하지 않는다.
- 사용자 답변을 문서 Text에만 반영하고 Canonical 갱신을 생략하지 않는다.
- 문서 수정을 보고 Business Truth 변경으로 자동 해석하지 않는다.
- Block 지정이 없더라도 Target과 문맥이 명확하면 도움을 거부하지 않는다. 다만 변경 적용 전에 Agent가 해석한 Block을 명시한다.
- 사용자에게 `DEFERRED`, `SOURCE_BLOCK`, `Recheck At`, `Human Decision Queue`, `영속적` 같은 표현을 설명 없이 그대로 노출하지 않는다.
