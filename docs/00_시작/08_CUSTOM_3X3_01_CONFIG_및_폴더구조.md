# Custom 3×3 Template Pilot — 01. Config 및 폴더 구조

## 1. 목적

`SDLC_DESIGN_SESSION_FIRST/tailoring-control-plane/v1.9.0`에서 개발용 3종과 고객용 3종 Custom Template을 실제 Runtime에 연결하는 방법을 설명한다.

이번 Pilot의 문서 체계는 다음과 같다.

### 개발/설계자용 `INTERNAL_IT`
1. 업무정의서
2. 화면설계서
3. 프로그램설계서

### 고객용 `CUSTOMER`
1. 업무정의서
2. 화면설계서
3. 프로그램설계서

문서명이 같더라도 두 Layer의 역할은 다르다.

- Internal 문서: 설계/개발자가 읽고 검토하는 Human Review Surface
- Customer 문서: 고객과 합의·확인하기 위한 Generated View
- Canonical Spec: 두 Layer가 공유하는 의미 기준이며 Template 변경으로 축약하거나 별도 복제하지 않는다.

`AGENT_DRAFT_HUMAN_REVIEW`, `GENERATED_VIEW`, `HUMAN_AUTHORITATIVE`, `MACHINE_DERIVED` 같은 Agent/Framework용 ownership 표기는 Profile·Contract·Runtime metadata에서 관리하고 사람용 Markdown 본문에는 기본 노출하지 않는다.

## 2. 사용 파일

Pilot에 필요한 Custom 파일은 Core가 아니라 `sdlc/custom/project/` 아래에 둔다.

```text
.sdlc/
└─ project.yaml                         # 실제 프로젝트 설정 1개

sdlc/custom/project/
├─ tailoring/
│  ├─ CUSTOM_PILOT_INTERNAL_3.yaml     # 개발/설계자용 3종 Mapping
│  └─ CUSTOM_PILOT_CUSTOMER_3.yaml     # 고객용 3종 Mapping
├─ templates/
│  └─ pilot-3x3/
│     ├─ internal/
│     │  ├─ 01_업무정의서.md
│     │  ├─ 02_화면설계서.md
│     │  └─ 03_프로그램설계서.md
│     └─ customer/
│        ├─ A01_업무정의서.md
│        ├─ A02_화면설계서.md
│        └─ A03_프로그램설계서.md
└─ config/
   ├─ project.custom-3x3.example.yaml
   ├─ customer-3x3-document-contract.json
   └─ customer-3x3-projection-profile.json
```

Core `sdlc/templates/`, `sdlc/tailoring/standard/`, `sdlc/scripts/`를 고객사별로 복사해서 수정하지 않는다.

## 3. `.sdlc/project.yaml` 만들기

먼저 예제 파일을 복사한다.

```bash
mkdir -p .sdlc
cp sdlc/custom/project/config/project.custom-3x3.example.yaml .sdlc/project.yaml
```

그 뒤 실제 프로젝트 값으로 수정한다.

가장 중요한 문서 설정은 다음이다.

```yaml
documents:
  language: "ko-KR"

  internal:
    profile: "CUSTOM_PILOT_INTERNAL_3"

  customer:
    profile: "CUSTOM_PILOT_CUSTOMER_3"
    projection_contract: "sdlc/custom/project/config/customer-3x3-document-contract.json"
    projection_config: "sdlc/custom/project/config/customer-3x3-projection-profile.json"

  pm:
    profile: "PM_STANDARD"

  machine:
    visibility: "HIDDEN"
```

각 값의 역할은 다음과 같다.

| Config | 역할 |
|---|---|
| `documents.internal.profile` | Internal Stage/Canonical/Evidence를 어떤 개발용 문서에 Projection할지 결정 |
| `documents.customer.profile` | 고객 문서 종류, Template, output path 결정 |
| `documents.customer.projection_contract` | Internal/Canonical의 어떤 의미 Section을 고객 문서의 어느 Section에 넣을지 결정 |
| `documents.customer.projection_config` | 내부 ID/Hash 노출, 용어 치환, 선택 Section 등 고객 표시정책 결정 |
| `documents.pm.profile` | `/check` PM View 정책 |
| `documents.machine.visibility` | Canonical/Trace/Runtime 내부정보의 사용자 노출 수준 |

`profile`, `projection_contract`, `projection_config`는 서로 다른 책임이다. 하나의 파일에 모두 넣지 않는다.

## 4. 개발용 3종 Mapping

`CUSTOM_PILOT_INTERNAL_3.yaml`의 의미는 다음과 같다.

| 문서 | 내부 Semantic Source | 비고 |
|---|---|---|
| 업무정의서 | DECOMPOSE, CLARIFY, PROCESS, DISCOVERY, IMPACT | 의도/AS-IS/TO-BE/업무규칙/영향을 한 문서로 통합 |
| 화면설계서 | DESIGN | `HAS_UI`일 때만 생성 |
| 프로그램설계서 | PROGRAM, DEVELOPMENT, TEST, VERIFY, KNOWLEDGE_PROMOTION | 구현/테스트/Legacy Discovery/Reconciliation까지 통합 |

Stage 이름은 사용자가 순서대로 실행해야 하는 문서 단계가 아니라 내부 compatibility taxonomy다. 일반 작업은 Change Level이 필요한 Semantic Work만 선택한다.

## 5. 고객용 3종 Mapping

`CUSTOM_PILOT_CUSTOMER_3.yaml`의 문서 ID는 기존 Customer Runtime과 호환하기 위해 다음 의미 ID를 유지한다.

| 고객 파일명 | Artifact ID | Canonical 중심 의미 |
|---|---|---|
| A01 업무정의서 | `solution_agreement` | RQ, FR, BR, PROC, AC |
| A02 화면설계서 | `delivery_scope` | RQ, FR, PROC, PGM, AC |
| A03 프로그램설계서 | `acceptance_handover` | RQ, PGM, DATA, AC, TC |

파일명은 고객사 양식으로 바꿀 수 있지만 Artifact ID는 Runtime 계약으로 유지하는 것을 권장한다.

## 6. Customer renderer 연결

현재 v1.9에서는 공식 `harness customer-view`가 `.sdlc/project.yaml`을 읽어 다음 순서로 동작한다.

```text
project.yaml
  ↓
documents.customer.profile
  ↓
CUSTOM_PILOT_CUSTOMER_3.yaml
  ↓
artifact.template
  ↓
Custom Customer Markdown Template
```

고객 본문에 넣을 데이터는 별도 `projection_contract`와 `projection_config`가 결정한다.

즉 Template 파일을 추가하는 것만으로는 Customizing이 끝나지 않는다.

## 7. Template Placeholder 규칙

고객용 Template에서 사용할 수 있는 기본 Placeholder는 다음과 같다.

```text
{{short_name}}
{{customer_purpose}}
{{customer_summary}}
{{section_고객과_함께_확인할_내용}}
{{section_합의된_내용}}
{{section_미확정_사항}}
{{section_다음_단계}}
{{optional_appendix}}
```

Custom Contract의 Section 이름은 다음 규칙으로 Placeholder가 된다.

```text
"AS-IS / TO-BE"
→ {{section_AS_IS_TO_BE}}

"업무 범위와 규칙"
→ {{section_업무_범위와_규칙}}
```

알 수 없는 `{{...}}`가 남으면 Customer View 생성은 실패한다. 잘못된 Template을 조용히 배포하지 않는다.

## 8. Config 검증

먼저 Project Config가 DEAD_CONFIG 없이 읽히는지 확인한다.

```bash
python sdlc/scripts/harness.py check --setup
```

Profile을 각각 검증한다.

```bash
python sdlc/scripts/tailoring_runtime.py validate-profile \
  --profile CUSTOM_PILOT_INTERNAL_3

python sdlc/scripts/tailoring_runtime.py validate-profile \
  --profile CUSTOM_PILOT_CUSTOMER_3
```

대표 RQ의 Mapping도 확인한다.

```bash
python sdlc/scripts/tailoring_runtime.py resolve \
  --target RQ-001 \
  --stage DESIGN
```

결과에서 다음을 확인한다.

```text
profiles.internal = CUSTOM_PILOT_INTERNAL_3
profiles.customer = CUSTOM_PILOT_CUSTOMER_3
projection_creates_business_truth = false
```

## 9. Template 수정 시 지켜야 할 규칙

1. 고객사 문서명/순서/표현은 변경 가능하다.
2. Canonical 의미를 고객 Template마다 새로 정의하지 않는다.
3. Agent/Framework ownership 정보는 Profile·Contract·Runtime metadata에서 관리하고 사람용 Markdown에는 표시하지 않는다.
4. Source에서 재생성 가능한 File/Method/Query/Table/Column/Hash를 사람이 수동 SSOT로 유지하게 만들지 않는다.
5. 개발자에게 Source Mapping은 보여줄 수 있지만, 가능한 경우 Agent가 Source Evidence에서 생성하고 개발자는 정확성만 Review한다.
6. 고객 문서는 Generated View 성격을 유지한다.
7. 고객 문서의 업무정책 수정은 Canonical auto-update가 아니라 Decision/Review로 되돌린다.
8. 화면이 없는 RQ에서는 `HAS_UI` 조건 때문에 화면설계서를 강제로 만들지 않는다.

사람용 문서에서 숨길 대표 내부정보:

```text
HUMAN_AUTHORITATIVE
HUMAN_REVIEWED
MACHINE_DERIVED
AGENT_DRAFT_HUMAN_REVIEW
GENERATED_VIEW
Canonical revision
Source Hash
Provenance/Trace JSON
Stage Result 내부 구조
Agent instruction
```

단, 안전성과 정합성을 위해 이 정보 자체를 삭제하는 것은 아니다. Human Projection에서만 숨기고 Machine Runtime에는 유지한다.

## 10. 다음 가이드

실제 역할별 실행 순서와 설계문서 수정 시 `직접 편집 / work / change` 선택 기준은 `09_CUSTOM_3X3_02_이해관계자_실행프로세스.md`를 따른다.
