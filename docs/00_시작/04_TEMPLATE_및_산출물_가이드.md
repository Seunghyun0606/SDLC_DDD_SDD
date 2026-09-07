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

Profile에 따라 `docs/20_customer/...` 같은 Custom output path를 사용할 수 있다. 실제 출력 경로의 권위는 선택한 Tailoring Profile artifact의 `output_path`다.

## 3. Projection에는 Canonical/Runtime 내부 표현을 최대한 숨긴다

사람이 보는 Projection은 Canonical Store나 Runtime Debug View가 아니다.

Machine-side에 기본 유지하는 정보:

```text
Canonical Entity ID / Entity Type
Relation / Revision / Provenance
Confidence / Evidence taxonomy
Stage / Change Level internal code
Queue ID / Block ID / Guard code
Source Hash / Locator
```

Engineering 문서에는 실제 구현에 필요한 기술정보는 유지한다.

```text
Source/File/Class/Method
Query/Table/Column
Interface/Batch/Procedure
Transaction/권한/입출력
테스트 방법/실제 반영 결과
```

Customer 문서에는 업무·범위·합의·영향·인수에 필요한 의미만 표시한다.

Customer direct Canonical 입력은 **Allowlist-first**이며 Relation/Revision/Provenance를 먼저 펼치지 않는다. Sanitizer는 외부/Legacy 입력까지 포함한 2차 방어다.

Stable Block ID는 Agent가 정확히 수정하기 위해 필요할 수 있으므로 다음처럼 숨김 marker로 유지할 수 있다.

```html
<!-- BLOCK_ID: WU-BUSINESS-RULE -->
```

사람에게 보이는 제목/표에는 Machine ID를 기본 노출하지 않는다.

## 4. 가장 중요한 UX — Template은 입력 Form이 아니다

일반 프로젝트 참여자는 Template 파일을 열어 빈칸을 처음부터 작성하지 않는다.

기본 흐름은 다음이다.

```text
/work 또는 /change
→ Agent가 Canonical / 기존 문서 / Source / DB / Config를 먼저 조사
→ 이전 단계 Human Decision Queue 확인
→ Agent가 문서 초안을 먼저 작성
→ 사람의 업무 판단이 필요한 Gap만 질문
→ 사용자는 질문에 자연어로 답변하거나 "지금은 확인 불가"라고 보류
→ 즉시 답변: Agent가 Canonical Delta / Provenance에 반영
→ 보류: Agent가 문서 Queue + Canonical OPEN/DEFERRED로 carry-forward
→ 다음 Semantic Work에서 Recheck At이 도래한 Queue를 신규 질문보다 먼저 재확인
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

### 4.1 바로 답할 수 없으면 "모른다"고 답해도 된다

사용자가 모든 질문을 그 자리에서 확정할 필요는 없다.

예:

```text
이건 지금 확정하기 어려워. 고객에게 확인한 뒤 다음 DESIGN 단계에서 다시 물어봐줘.
```

```text
Procedure 변경 여부는 아직 DBA 확인 전이야. Source 수정 전에 다시 확인해줘.
```

이 경우 Agent는 임의의 값을 채우지 않고 해당 질문을 **Human Decision Queue**에 남긴다.

Machine-side Queue는 같은 Question ID, 관련 Block, Guard/Recheck 정보를 유지하되, 사람 문서에는 내부 Enum을 그대로 노출하지 않고 다음처럼 자연어로 표시한다.

| 사람에게 보이는 항목 | 의미 |
|---|---|
| 확인 필요사항 | 나중에 사람이 답할 내용 |
| 현재 확인값 / 제안 | Source/Evidence와 Agent Proposal. 확정값 아님 |
| 결정 담당 | 실제 Authority |
| 개발 영향 | 개발 전 확인 필요 / 진행 가능·추후 보완 / 주의사항 |
| 다시 확인할 시점 | 개발 시작 전 / 테스트 전 / 최종 검증 전 등 |
| 상태 | 미확정 / 확인중 / 제안 / 보류 / 확정 |

Queue 표는 Agent가 관리한다. 사용자가 문서 표를 직접 편집할 필요는 없다.

### 4.2 다음 단계에서는 Queue부터 확인한다

Agent는 새 질문을 만들기 전에 현재 경계에 재확인 시점이 도래한 Queue를 먼저 확인한다.

1. 이미 다른 Evidence로 해소됐으면 Agent가 스스로 갱신한다.
2. Source/DB/Config로 확인 가능하면 사람에게 다시 묻기 전에 조사한다.
3. 여전히 Business Authority가 필요하면 기존 Queue ID로 다시 질문한다.
4. 아직 답이 없으면 동일 Queue의 상태와 다음 재확인 시점만 갱신한다.
5. 답을 받으면 Canonical Decision/Provenance를 반영하고 Queue를 확정 처리한다.

Machine-side `SOURCE_BLOCK`은 관련 Source/Action만 제한하며 전체 프로젝트를 자동 중단시키지 않는다. `ITERATE`와 `ALERT`도 Machine 상태로 유지하고 사람 View에서는 자연어로 번역한다.

## 5. Work Map

목적은 상세설계를 반복하는 것이 아니라 다음 질문에 빨리 답하는 것이다.

- 무엇을 구현해야 하는가?
- 어떤 기능/업무 단위인가?
- 어떤 Program/Source를 수정하는가?
- 어떤 Test로 확인하는가?
- 현재 어디까지 진행됐는가?

Machine-side에서는 RQ/FR/FTR/WP/TASK/PGM/ART/AC/TC 연결을 유지할 수 있지만, 사람에게 보이는 Work Map은 업무/기능, 개발 작업, 프로그램/소스, 테스트, 상태처럼 읽기 쉬운 표현을 우선한다.

표준 Work Map에는 숨김 Stable Block ID가 있다.

- `WM-SUMMARY`
- `WM-UNIT`
- `WM-MAPPING`
- `WM-AC-TEST`
- `WM-OPEN`
- `WM-HITL-QUEUE`

## 6. Work Unit SDD

Stage 문서를 이어 붙인 문서가 아니다. 하나의 기능/업무 단위가 Lifecycle을 따라 발전한다.

Machine-side Stage/상태를 사람이 직접 관리하게 하지 않고, 사람 View에는 업무 목적, 현행, 개선안, 업무규칙, 영향, 개발계약, 인수/테스트, 미확정 사항을 중심으로 보여준다.

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
- `WU-HITL-QUEUE`
- `WU-ASBUILT`
- `WU-VERIFY`

이 Block ID들은 수정 경계용 Machine marker이며 최종 Human Body에서 직접 노출할 필요는 없다.

## 7. Program Spec

Program Spec은 Functional 의미를 다시 쓰는 문서가 아니다.

```text
Functional/Work Unit Spec = 무엇을 왜 어떻게 동작시킬 것인가
Program Spec              = 실제 어떤 Source에 어떤 Delta를 구현할 것인가
```

기본 Readiness 정책은 **Core Required 6 + Risk-triggered Conditional**이다. Data, Transaction, Interface, Security, Migration 같은 조건이 실제로 있을 때만 Conditional 항목을 추가하며, `LEGACY_FULL_17`은 기존 Formal/Legacy 계약을 위한 호환 모드다.

Source에서 다시 생성 가능한 Query/Table/Symbol/Locator/Hash는 Machine-derived Evidence로 관리한다. 단, 개발자가 구현에 실제 필요한 File/Class/Method/Query/Table/Transaction 등의 기술 정보는 Engineering Projection에 남긴다.

주요 숨김 Block ID:

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

## 8. Fast Path에서도 없어지지 않는 분석

L1/L2는 **분석·작성 깊이를 줄일 수 있지만**, Source 변경 전 다음 의미 검증은 유지한다.

- Requirement Intent Decomposition
- AS-IS Source Analysis
- Impact Check

Change Level이 Human Artifact topology를 소유하지 않는다.

- `STAGE_MATCHED` Profile은 Stage 조건에 따라 문서를 선택할 수 있다.
- `PROFILE_PRIMARY_SET` Profile은 required 문서를 L1/L2에서도 유지하고 `CONCISE`하게 작성할 수 있다.

예를 들어 HRIS 2종 Profile은 L1/DEVELOPMENT에서도 업무정의서와 작업지시서를 모두 유지하되, 업무정의서는 확인된 변경 범위만 간결하게 기록한다.

내부 Runtime에서는 Fast Path의 의미 Gate를 Machine 상태로 확인한다. 일반 사용자가 내부 상수를 직접 관리할 필요는 없다.

## 9. 생성 문서를 수정하고 싶을 때

### 9.1 기본 원칙

오탈자를 제외하면 파일을 직접 고치기보다 **Agent에게 문서/Target + 의미 Block을 지정해서 수정 요청**한다.

권장 예:

```text
RQ-0042 Work Unit SDD의 업무 규칙 부분에서
월 마감 이후 재계산 정책을 "급여 마감 전까지만 허용"으로 바꿔줘.
```

Machine Block ID를 알고 있다면 `[BLOCK:WU-BUSINESS-RULE]`처럼 지정해도 되지만 필수는 아니다. Agent가 문맥으로 Block을 찾을 수 있어야 한다.

### 9.2 Agent Routing

| 수정 내용 | 처리 |
|---|---|
| Requirement / Business Rule / TO-BE / AC / Scope 의미 변경 | `/change` → Canonical Delta |
| AS-IS / Source / DB / Mapping / AS-BUILT 재분석 | `/work` → Evidence/Provenance 갱신 |
| Queue 상태 / 재확인 시점 조정 | Queue metadata 갱신. 실제 Business Truth 변화 없음 |
| Queue 질문에 실제 업무 답변 제공 | 답변의 의미에 따라 `/change` 또는 `/work` → Canonical/Provenance 반영 |
| 오탈자 / 문장 표현 / 레이아웃 | Projection-only → Canonical 변화 없음 |

Block을 지정하지 않아도 문맥이 명확하면 Agent가 자신이 해석한 Block을 먼저 알려주고 진행한다. 여러 후보가 있을 때만 Block 선택을 짧게 질문한다.

### 9.3 직접 편집했을 때

Generated hash와 파일이 다르면 Projection Lifecycle에서 `MANUAL_EDIT_DETECTED` 경고가 가능하다. 직접 편집 내용은 **자동으로 Canonical Business Truth가 되지 않는다**.

직접 편집 후 의미 변경을 Canonical에 반영하려면 Agent에게 다음처럼 알려준다.

```text
방금 수정한 Work Unit SDD의 개선안 부분을 Canonical 기준으로 검토해서 반영해줘.
```

Agent가 diff를 읽고 `Semantic Change / Evidence Refresh / Projection-only`를 판정한 뒤 필요한 경우 `/change`를 수행한다.

## 10. Customer Template

기본 3종은 다음 목적에 맞춘다.

- A01: 요구/업무/기능 합의
- A02: 영향/개발범위 공유
- A03: 테스트/인수/운영 결과

`CUSTOMER_WATERFALL_FULL`은 같은 semantic contract를 8개의 제출 단위로 split한 예시다. 프로젝트는 Custom Profile로 다른 N종을 만들 수 있다.

고객 문서는 Canonical ID/Relation/Provenance/Confidence를 기본 표시하지 않는다. 기술 상세·근거 상세 부록도 기본 OFF이며 프로젝트가 명시적으로 필요로 할 때만 선택한다.

고객이 즉시 답하지 못한 Business Decision도 관련 Customer/Engineering Review Surface의 Queue로 연결하고 Canonical OPEN/DEFERRED로 유지한다. 다음 합의/설계 경계에서 다시 확인한다.

## 11. Customer Final Human Edit

진행 중 문서는 Agent-generated View다. Final Submission 직전 `FINAL_REVIEW`에서 표현/레이아웃을 사람이 다듬을 수 있다.

- 표현 수정 → Canonical 변화 없음
- Business Rule 수정 → 관련 의미 Section을 지정해 `/change`
- Final Review 이후 Canonical 변경 → `STALE_VIEW`, 자동 overwrite 금지, 재검수 필요

Rich Text Merge Engine을 따로 만들지 않는다.

## 12. Template을 추가할 때 체크

Semantic Template:

- 특정 Stage의 의미와 Evidence 구조를 정의하는가?
- 최종 제출 문서 형식을 강제하고 있지는 않은가?
- Canonical Business Truth를 임의로 만들지 않는가?

Engineering Template:

- Functional 의미를 중복하지 않는가?
- 실제 구현에 필요한 Program/Source/Test 연결을 보여주는가?
- AS-BUILT/Verification을 담을 수 있는가?
- Stable Block ID가 숨김 marker로 있어 Agent가 특정 의미 단위를 수정할 수 있는가?
- 즉시 답하지 못한 질문을 사람이 이해할 수 있는 자연어 Queue로 보여주는가?
- Canonical/Runtime 내부 taxonomy가 본문에 과도하게 노출되지 않는가?
- 사용자가 빈칸을 직접 작성하는 Form처럼 보이지 않는가?

Customer Template:

- 고객에게 필요한 자연어 문맥인가?
- 내부 ID/Relation/Revision/Provenance/Hash/Confidence가 불필요하게 노출되지 않는가?
- direct Canonical 입력이 allowlist-first 경계를 지키는가?
- 어떤 `projection_type`의 의미를 표현하는가?
- Engineering 파일명/순번에 의존하지 않는가?
- 고객 미결정 사항이 대화에서 유실되지 않고 OPEN/Queue로 round-trip 되는가?

Tailoring Profile:

- 실제 Template 경로가 존재하는가?
- Stage/Canonical source selector가 의도와 맞는가?
- Engineering/Customer Profile을 서로의 문서 수나 파일명에 의존시키지 않는가?
- required artifact topology가 필요한 경우 `PROFILE_PRIMARY_SET`을 사용했는가?
- Change Level별 상세도와 문서 존재 여부를 혼동하지 않았는가?

## 13. Framework Standard / Project Custom / Generated 구분

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
- docs/20_고객/ 또는 Customer Profile output path
```

고객별 요구 때문에 Framework Standard 자체를 직접 수정하지 않는다.
