# HITL Interaction Reference — Agent Question Driven UX

## 1. 목적

`/work`와 `/change`에서 사람에게 Template 빈칸을 직접 채우게 하지 않는다.

기본 UX는 다음 순서다.

```text
Agent가 Canonical / Source / 기존 문서 / Evidence를 먼저 읽음
→ Agent가 가능한 항목을 먼저 초안 작성
→ 사람의 업무 판단이 필요한 Gap만 질문으로 생성
→ 사용자는 질문에 자연어로 답변
→ Agent가 답변을 Evidence/Decision으로 구조화
→ Canonical Delta 작성 및 Guard 통과
→ Engineering/Customer Projection 재생성 또는 갱신
```

문서는 **입력 Form이 아니라 Review Surface**다.

사람은 다음을 하지 않는다.

- Template의 빈 표를 처음부터 직접 채우기
- Canonical JSON 직접 수정
- Stage Result 직접 작성
- Source Hash / Trace / Locator 같은 Machine Evidence 수동 관리

## 2. 질문 생성 원칙

Agent는 질문 전에 반드시 다음 순서를 따른다.

1. 현재 Canonical에 이미 답이 있는지 확인한다.
2. Source / DB / Config / 기존 문서에서 기술적으로 확인 가능한지 조사한다.
3. 프로젝트 표준 또는 명시적 기존 Decision으로 결정 가능한지 확인한다.
4. 그래도 **사람의 업무 권위 또는 선택이 필요한 경우에만** 질문한다.

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
- 두 가지 TO-BE 대안 중 어느 정책을 선택할 것인가?
- 고객이 요구한 범위를 이번 Release에 포함할 것인가?

## 3. 질문 묶음 UX

한 번에 Template 전체를 질문하지 않는다.

- 기본 한 턴 최대 3개 질문
- 같은 Decision Cluster는 한 묶음으로 제시
- Source 조사로 줄일 수 있는 질문은 먼저 제거
- 사용자의 앞선 답변으로 파생되는 후속 질문만 다음 턴에 제시
- 중요하지 않은 UI 표현은 `ITERATE`로 남기고 진행 가능

질문은 다음 구조를 따른다.

| 필드 | 의미 |
|---|---|
| Question ID | `HITL-<TARGET>-<NN>` |
| 대상 Block | 답변이 반영될 문서/Canonical 의미 Block |
| 왜 필요한가 | 현재 진행에서 이 결정이 필요한 이유 |
| 현재 알고 있는 것 | GIVEN / OBSERVED / CONFIRMED / INFERRED 구분 |
| 질문 | 사용자가 판단할 한 가지 내용 |
| 선택지 | 실제 근거가 있을 때만 제시; 강제하지 않음 |
| 미응답 시 처리 | SOURCE_BLOCK / ASSUMPTION / ALERT / ITERATE |

사용자에게는 Machine 필드명을 그대로 강요하지 않고 자연어로 보여준다.

## 4. Semantic Work별 질문 기준

| Semantic Work / Stage | Agent가 먼저 할 일 | 사람에게 물을 수 있는 핵심 | 기본 미응답 처리 |
|---|---|---|---|
| INTAKE | 입력자료 요약, 중복/기존 RQ 확인 | 현재 문제, 원하는 결과, 반드시 유지할 조건 중 불명확한 것 | OPEN |
| DECOMPOSE | 요구를 행동/결과/AC 후보로 분해 | 한 RQ인지 여러 업무 변경인지, 범위 경계가 업무적으로 애매한 경우 | OPEN |
| CLARIFY | Source/문서로 답 가능한 질문 제거 | 정책, 예외, 우선순위, 업무 용어 등 Business Authority 필요사항 | SOURCE_BLOCK 또는 ASSUMPTION |
| PROCESS | AS-IS/TO-BE 흐름 후보 작성 | Actor, Trigger, 상태전이, 예외 정책 중 업무 결정 | SOURCE_BLOCK |
| DISCOVERY | Source/DB/Interface Evidence 조사 | Source 접근 불가, 외부 시스템 사실처럼 사람이 제공해야 하는 Evidence | ALERT / Coverage Gap |
| IMPACT | Technical/Functional Candidate 분석 | 실제 업무 영향 포함/제외, 운영 영향 수용 여부 | SOURCE_BLOCK 또는 ALERT |
| DESIGN | 동작/Validation/권한/예외 초안 | TO-BE 정책 선택, 권한/상태/예외의 업무 결정 | SOURCE_BLOCK |
| PROGRAM | 기존 Architecture/유사 Program/표준 조사 | 신규 Program 분리, Architecture Exception 등 사람 승인 필요 결정 | SOURCE_BLOCK |
| DEVELOPMENT | Source Write 준비도와 Open 확인 | 아직 남은 업무/보안/데이터 Guard 결정만 질문 | SOURCE_BLOCK |
| TEST | AC에서 Test 자동 생성 | 기대결과 또는 합격 기준 자체가 불명확한 경우 | SOURCE_BLOCK |
| VERIFY | Spec/Source/Test 차이 정리 | 계획 대비 차이를 승인할지, 미해결 Risk를 수용할지 | DECISION_REQUIRED |
| KNOWLEDGE_PROMOTION | 재사용 후보와 Evidence 정리 | 장기 업무 규칙으로 승격할지 사람이 확정해야 하는 지식 | REVIEW |
| CHANGE | 현재 Block/Canonical 값과 영향 조사 | 무엇이 실제로 달라졌는지, 표현 수정인지 Business Truth 수정인지 애매한 경우 | 변경 적용 보류 |

Stage 이름은 내부 Taxonomy다. 일반 사용자는 Stage를 고르지 않고 Agent가 현재 `required_semantic_work`에 맞는 질문만 생성한다.

## 5. 답변 처리 규칙

사용자의 답변을 받은 Agent는 문서만 고치지 않는다.

1. 답변을 `GIVEN`으로 기록한다.
2. 기존 `CONFIRMED_BUSINESS`와 충돌하면 `/change` 의미로 전환하거나 명시적 변경 authorization을 확인한다.
3. 새 Decision/Rule/AC/Scope가 되면 해당 Canonical Entity/Relation Delta를 만든다.
4. 단순 표현 수정이면 Canonical Delta를 만들지 않는다.
5. Canonical Apply가 성공한 뒤 Projection을 갱신한다.
6. 어떤 답변이 어떤 Block/Canonical 항목에 반영됐는지 사용자에게 짧게 알려준다.

## 6. 문서 Block Target 규칙

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
HRIS 작업지시서의 [BLOCK:B-PROC]에서
P_PY_CALC_MAIN의 신규 OUT 파라미터 영향만 재검토해줘.
```

### Block 수정 Routing

Agent는 Block 요청을 다음 셋 중 하나로 분류한다.

- `SEMANTIC_CHANGE`: Requirement / Business Rule / TO-BE / AC / Scope 의미가 바뀜 → `/change` + Canonical Delta
- `EVIDENCE_REFRESH`: Source/DB/Mapping/AS-BUILT 근거를 다시 분석 → `/work` + Evidence/Provenance 갱신
- `PROJECTION_ONLY`: 오탈자/표현/레이아웃만 변경 → Canonical Delta 없음

애매하면 Agent가 한 번의 짧은 확인 질문으로 Routing을 확정한다.

## 7. Stable Block ID 권장 체계

Standard Engineering Projection:

- `WM-SUMMARY`, `WM-UNIT`, `WM-MAPPING`, `WM-AC-TEST`, `WM-OPEN`
- `WU-INTENT`, `WU-ASIS`, `WU-TOBE`, `WU-BUSINESS-RULE`, `WU-IMPACT`, `WU-MAPPING`, `WU-TECH-IMPACT`, `WU-DEV-CONTRACT`, `WU-AC-TEST`, `WU-OPEN-GUARD`, `WU-ASBUILT`, `WU-VERIFY`
- `PGM-INTENT`, `PGM-TARGET`, `PGM-SOURCE-EVIDENCE`, `PGM-DELTA`, `PGM-CONDITIONAL`, `PGM-SOURCE-BOUNDARY`, `PGM-TRACE`, `PGM-READINESS`, `PGM-ASBUILT`

HRIS/hunel Custom Projection:

- 업무정의서: `HRIS-INTENT`, `HRIS-REQUIREMENT`, `HRIS-ASIS`, `HRIS-TOBE`, `HRIS-BUSINESS-RULE`, `HRIS-DATA-AUTH`, `HRIS-INTEGRATION-NFR`, `HRIS-AC`, `HRIS-IMPACT`, `HRIS-OPEN`, `HRIS-HANDOFF`
- 작업지시서: 기존 구조 ID를 그대로 사용한다. `A.1`, `A.2`, `A.3`, `A.4`, `B-SHEET`, `B-TAB`, `B-VUE`, `B-APPL`, `B-PROC`, `B-POPUP`, `B-DYNAMIC`, `B-AUTH`, `B-MIGRATION`, `C.1`, `C.2`, `C.3`, `D.1`, `D.2`, `D.3`, `E.1`, `E.2`, `E.3`

## 8. 금지 UX

- "Template을 열고 1~12번 Section을 작성해 주세요"라고 사용자에게 요구하지 않는다.
- Source에서 확인 가능한 값을 사람에게 질문하지 않는다.
- 사용자 답변을 문서 Text에만 반영하고 Canonical 갱신을 생략하지 않는다.
- 문서 수정을 보고 Business Truth 변경으로 자동 해석하지 않는다.
- Block 지정이 없더라도 Target과 문맥이 명확하면 도움을 거부하지 않는다. 다만 변경 적용 전에 Agent가 해석한 Block을 명시한다.
