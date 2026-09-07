# Template 및 산출물 가이드

## 1. Template과 Tailoring Profile을 먼저 구분한다

둘은 같은 종류의 문서가 아니다.

| 위치 | 역할 |
|---|---|
| `sdlc/templates/semantic/` | Requirement/Analysis/Impact/Design/Program/Test/Verify 등 **Stage에서 어떤 의미를 작성할지** 정의 |
| `sdlc/templates/engineering/` | 개발자/설계자용 Engineering Projection Template |
| `sdlc/templates/customer/` | 고객 커뮤니케이션용 Customer Projection Template |
| `sdlc/templates/management/` | PM/관리 View Template |
| `sdlc/templates/tailoring/standard/` | `STANDARD_3/5`, `STAGE_ORIENTED_FULL`용 Legacy Compatibility Template |
| `sdlc/tailoring/standard/*.yaml` | Template이 아니라 **어떤 산출물을 어떤 Template/Stage/출력경로로 조립할지 정하는 Profile** |

따라서 다음처럼 이해한다.

```text
Canonical + Stage Evidence
        ↓
sdlc/templates/semantic/          # 단계별 의미 구조
        ↓
sdlc/tailoring/standard/*.yaml    # 조립/선택 규칙
        ↓
Engineering / Customer Projection
```

v1.10부터 Stage Semantic Template의 정식 경로는 `sdlc/templates/semantic/` 하나뿐이다. 별도 alias나 symlink 경로를 두지 않으며 Runtime, Contract, Test, Guide도 이 경로를 직접 사용한다.

## 2. 문서는 두 종류로 생각한다

### Engineering Projection

개발자와 Agent가 실제 구현을 수행하기 위한 Living Spec이다.

기본 위치:

```text
docs/10_engineering/<TARGET>/
├─ 00_work-map.md
├─ specs/<WORK-UNIT>.md
└─ programs/<PGM>.md   # 필요할 때만
```

### Customer Projection

고객과 협의·제출·검수·인수하기 위한 Human-oriented Waterfall View다.

기본 위치:

```text
docs/20_고객/<TARGET>/
├─ A01_요구_업무_기능_합의서.md
├─ A02_영향_개발범위_공유서.md
└─ A03_테스트_인수_운영_결과서.md
```

Profile에 따라 `docs/20_customer/...` 같은 Custom output root를 사용할 수 있다.

## 3. 가장 중요한 UX — Template은 입력 Form이 아니다

일반 프로젝트 참여자는 Template 파일을 열어 빈칸을 처음부터 작성하지 않는다.

기본 흐름은 다음이다.

```text
/work 또는 /change
→ Agent가 Canonical / 기존 문서 / Source / DB / Config를 먼저 조사
→ Agent가 문서 초안을 먼저 작성
→ 사람의 업무 판단이 필요한 Gap만 질문
→ 사용자는 질문에 자연어로 답변
→ Agent가 답변을 Canonical Delta / Provenance에 반영
→ Engineering / Customer Projection 갱신
```

즉 사람은 **문서 작성자**보다 **Reviewer / Decision Maker** 역할을 한다.

Agent가 Source에서 확인할 수 있는 다음 정보는 사람에게 질문하지 않는다.

- Java Class / Method
- JSP / XML 파일 경로
- Query / Table / Column
- 현재 호출 관계
- 현재 권한 함수 사용 여부

사람에게 묻는 것은 정책, 범위, 예외, 권한 의미, Acceptance 같은 Business Authority가 필요한 내용이다.

질문 상세 규칙은 `sdlc/agent/skills/work/references/hitl.md`를 사용한다.

## 4. Work Map

목적은 상세설계를 반복하는 것이 아니라 다음 질문에 빨리 답하는 것이다.

- 무엇을 구현해야 하는가?
- 어떤 기능/업무 단위인가?
- 어떤 Program/Source를 수정하는가?
- 어떤 Test로 확인하는가?
- 현재 어디까지 진행됐는가?

최소 연결:

```text
RQ → FR/FTR → WP → Design TASK / Development TASK / Test TASK
   → PGM → ART/Source → AC → TC
```

표준 Work Map에는 수정 요청용 Stable Block ID가 있다.

- `WM-SUMMARY`
- `WM-UNIT`
- `WM-MAPPING`
- `WM-AC-TEST`
- `WM-OPEN`

## 5. Work Unit SDD

Stage 문서를 이어 붙인 문서가 아니다. 하나의 기능/업무 단위가 Lifecycle을 따라 발전한다.

```text
CHANGE → IMPACT → SPEC → PLAN → IMPLEMENT → VERIFY → AS-BUILT
```

표준 의미 Block:

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

## 6. Program Spec

Program Spec은 Functional 의미를 다시 쓰는 문서가 아니다.

```text
Functional/Work Unit Spec = 무엇을 왜 어떻게 동작시킬 것인가
Program Spec              = 실제 어떤 Source에 어떤 Delta를 구현할 것인가
```

기본 Readiness 정책은 **Core Required 6 + Risk-triggered Conditional**이다. Data, Transaction, Interface, Security, Migration 같은 조건이 실제로 있을 때만 Conditional 항목을 추가하며, `LEGACY_FULL_17`은 기존 Formal/Legacy 계약을 위한 호환 모드다.

Source에서 다시 생성 가능한 Query/Table/Symbol/Locator/Hash는 Machine-derived Evidence로 관리한다.

주요 Block ID:

- `PGM-INTENT`
- `PGM-TARGET`
- `PGM-SOURCE-EVIDENCE`
- `PGM-DELTA`
- `PGM-CONDITIONAL`
- `PGM-SOURCE-BOUNDARY`
- `PGM-TRACE`
- `PGM-READINESS`
- `PGM-ASBUILT`

## 7. Fast Path에서도 없어지지 않는 분석

L1/L2가 문서 수를 줄여도 Source 변경 전 다음 의미 검증은 유지한다.

- Requirement Intent Decomposition
- AS-IS Source Analysis
- Impact Check

내부 Runtime에서는 각각 `INTENT_DECOMPOSED`, `AS_IS_SOURCE_ANALYZED`, `IMPACT_CHECKED` Gate로 확인한다. 일반 사용자가 이 상수를 직접 관리할 필요는 없다.

## 8. 생성 문서를 수정하고 싶을 때

### 8.1 기본 원칙

오탈자를 제외하면 파일을 직접 고치기보다 **Agent에게 문서/Target + Block을 지정해서 수정 요청**한다.

권장 예:

```text
RQ-0042 Work Unit SDD의 [BLOCK:WU-BUSINESS-RULE]에서
월 마감 이후 재계산 정책을 "급여 마감 전까지만 허용"으로 바꿔줘.
```

```text
PGM-ATT-0016 Program Spec의 [BLOCK:PGM-SOURCE-EVIDENCE]를
현재 Source 기준으로 다시 분석해서 갱신해줘.
```

```text
HRIS 작업지시서의 [BLOCK:B-PROC]에서
P_PY_CALC_MAIN의 OUT Parameter 영향만 다시 확인해줘.
```

### 8.2 Agent Routing

| 수정 내용 | 처리 |
|---|---|
| Requirement / Business Rule / TO-BE / AC / Scope 의미 변경 | `/change` → Canonical Delta |
| AS-IS / Source / DB / Mapping / AS-BUILT 재분석 | `/work` → Evidence/Provenance 갱신 |
| 오탈자 / 문장 표현 / 레이아웃 | Projection-only → Canonical 변화 없음 |

Block을 지정하지 않아도 문맥이 명확하면 Agent가 자신이 해석한 Block을 먼저 알려주고 진행한다. 여러 후보가 있을 때만 Block 선택을 짧게 질문한다.

### 8.3 직접 편집했을 때

Generated hash와 파일이 다르면 Projection Lifecycle에서 `MANUAL_EDIT_DETECTED` 경고가 가능하다. 직접 편집 내용은 **자동으로 Canonical Business Truth가 되지 않는다**.

직접 편집 후 의미 변경을 Canonical에 반영하려면 Agent에게 다음처럼 알려준다.

```text
방금 수정한 Work Unit SDD의 [BLOCK:WU-TOBE] 변경 내용을 Canonical 기준으로 검토해서 반영해줘.
```

Agent가 diff를 읽고 `Semantic Change / Evidence Refresh / Projection-only`를 판정한 뒤 필요한 경우 `/change`를 수행한다.

## 9. Customer Template

기본 3종은 다음 목적에 맞춘다.

- A01: 요구/업무/기능 합의
- A02: 영향/개발범위 공유
- A03: 테스트/인수/운영 결과

`CUSTOMER_WATERFALL_FULL`은 같은 semantic contract를 8개의 제출 단위로 split한 예시다. 프로젝트는 Custom Profile로 다른 N종을 만들 수 있다.

## 10. Customer Final Human Edit

진행 중 문서는 Agent-generated View다. Final Submission 직전 `FINAL_REVIEW`에서 표현/레이아웃을 사람이 다듬을 수 있다.

- 표현 수정 → Canonical 변화 없음
- Business Rule 수정 → Block/Section을 지정해 `/change`
- Final Review 이후 Canonical 변경 → `STALE_VIEW`, 자동 overwrite 금지, 재검수 필요

Rich Text Merge Engine을 따로 만들지 않는다.

## 11. Template을 추가할 때 체크

Semantic Template:

- 특정 Stage의 의미와 Evidence 구조를 정의하는가?
- 최종 제출 문서 형식을 강제하고 있지는 않은가?
- Canonical Business Truth를 임의로 만들지 않는가?

Engineering Template:

- Functional 의미를 중복하지 않는가?
- TASK/PGM/Source/AC/TC가 연결되는가?
- AS-BUILT/Verification을 담을 수 있는가?
- Stable Block ID가 있어 사용자가 특정 의미 단위를 지시할 수 있는가?
- 사용자가 빈칸을 직접 작성하는 Form처럼 보이지 않는가?

Customer Template:

- 고객에게 필요한 자연어 문맥인가?
- 내부 ID/Hash/Confidence가 불필요하게 노출되지 않는가?
- 어떤 `projection_type`의 의미를 표현하는가?
- Engineering 파일명/순번에 의존하지 않는가?

Tailoring Profile:

- 실제 Template 경로가 존재하는가?
- Stage/Canonical source selector가 의도와 맞는가?
- Engineering/Customer Profile을 서로의 문서 수나 파일명에 의존시키지 않는가?

## 12. Framework Standard / Project Custom / Generated 구분

```text
Framework Standard
- sdlc/tailoring/standard/
- sdlc/templates/semantic/
- sdlc/templates/engineering/
- sdlc/templates/customer/

Legacy/Formal Projection
- sdlc/templates/tailoring/standard/
- STANDARD_3 / STANDARD_5 / STAGE_ORIENTED_FULL

Project Custom
- sdlc/custom/project/

Generated
- sdlc/runtime/
- docs/10_engineering/
- docs/20_고객/ 또는 Customer Profile output root
```

고객별 요구 때문에 Framework Standard 자체를 직접 수정하지 않는다.
