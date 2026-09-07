# Tailoring 설정 가이드

## 1. Tailoring이 결정하는 것

Tailoring Profile은 **어떤 의미를 어떤 Human Artifact로 보여줄지** 결정한다. Canonical 의미나 Change Level을 바꾸지 않는다.

Engineering과 Customer Tailoring은 서로 독립이다.

```text
Canonical Spec
├─ Engineering Profile → 개발용 Living Spec
└─ Customer Profile    → 고객 제출/합의 문서
```

Change Level은 실행 깊이/Evidence/Review 필요성을 정하고, Profile은 사람 문서 topology를 정한다. 따라서 Level의 기본 진입 Stage 하나가 Profile-required 문서를 임의로 없애는 기준이 되어서는 안 된다.

## 2. 표준 Profile

### Engineering

- `ENGINEERING_SDD_COMPACT`: 신규 기본. Work Map + Work Unit SDD + 조건부 Program Spec
- `STANDARD_3`: Legacy/Formal 내부 3종
- `STANDARD_5`: Legacy/Formal 내부 5종
- `STAGE_ORIENTED_FULL`: Legacy/Formal Compatibility

### Customer

- `CUSTOMER_STANDARD_3`: 기본 3종
- `CUSTOMER_WATERFALL_FULL`: Full Waterfall 8종

문서 수는 Project Size나 Change Level로 Runtime이 임의 추측하지 않는다.

## 3. Profile 선택

```yaml
documents:
  engineering:
    profile: ENGINEERING_SDD_COMPACT
  customer:
    profile: CUSTOMER_STANDARD_3
```

예를 들어 고객 제출물이 많아져도 Engineering을 바꿀 필요가 없다.

```yaml
documents:
  engineering:
    profile: ENGINEERING_SDD_COMPACT
  customer:
    profile: CUSTOMER_WATERFALL_FULL
```

Config 옵션별 역할은 `02A_PROJECT_CONFIG_옵션_상세가이드.md`를 본다.

## 4. Engineering Custom

프로젝트 Custom Profile 예:

```text
sdlc/custom/project/tailoring/CUSTOM_A_ENGINEERING.yaml
sdlc/custom/project/templates/engineering/...
```

Profile에서 독립적으로 정할 수 있다.

- artifact id
- template
- output path
- visibility
- source selector
- 조건부 생성 기준
- 문서 topology 정책
- Change Level별 Projection 상세도

Engineering 문서를 Customer 문서와 같은 번호로 맞추지 않는다.

### 4.1 Stage-match 문서와 Profile-required 문서를 구분한다

일반 Standard Profile은 Stage에 따라 필요한 문서만 선택하는 `STAGE_MATCHED` 방식으로 운영할 수 있다.

반대로 프로젝트가 “이 Profile을 쓰면 이 문서들은 항상 존재해야 한다”고 정했다면 `PROFILE_PRIMARY_SET`을 사용한다.

예: HRIS Custom 2종

```text
CUSTOM_HRIS_HUNEL_ENGINEERING
├─ 01_업무정의서.md
└─ 02_작업지시서.md
```

이 경우 L1의 현재 실행 초점이 DEVELOPMENT여도 `02_작업지시서`만 남기고 `01_업무정의서`를 삭제하지 않는다.

```text
L1/L2 → required 문서 유지 + CONCISE
L3/L4 → required 문서 유지 + STANDARD
L5    → required 문서 유지 + FULL
```

즉 Change Level은 문서 존재 여부가 아니라 내용의 분석/작성 깊이에 영향을 준다.

## 5. Customer Custom

Customer artifact는 `projection_type`을 사용해 표준 의미를 여러 제출문서로 split하거나 하나로 merge할 수 있다.

예:

```yaml
artifacts:
  requirements_agreement:
    projection_type: solution_agreement
    audience: CUSTOMER
    template: sdlc/custom/project/templates/customer/requirements.md
    output_path: docs/20_customer/{target}/01_요구사항합의서.md
    authoring: GENERATED_VIEW
    sources:
      stages: [INTAKE, DECOMPOSE, CLARIFY]
      canonical: [RQ, FR, BR, AC]

  functional_design:
    projection_type: solution_agreement
    audience: CUSTOMER
    template: sdlc/custom/project/templates/customer/functional.md
    output_path: docs/20_customer/{target}/04_기능설계서.md
    authoring: GENERATED_VIEW
    sources:
      stages: [DESIGN]
      canonical: [FR, BR, FTR, AC]
```

두 artifact가 같은 `solution_agreement` 의미군을 쓰더라도 파일 수/이름/Section은 Customer Profile이 독립적으로 결정한다.

## 6. Customer Runtime이 사용하지 않는 것

다음은 Customer artifact 선택 기준이 아니다.

- Engineering Profile ID
- Engineering 문서 개수
- Engineering artifact order
- Engineering expected path
- 같은 파일 순번

Customer direct Canonical 입력은 **Allowlist-first**다.

```text
Canonical 전체
  ↓
Customer-safe 의미 필드 allowlist
  ↓
Customer Section Mapping
  ↓
Sanitizer 2차 방어
  ↓
Customer Projection
```

따라서 다음 Machine 정보는 direct Customer Canonical 입력에서 기본 차단한다.

- Canonical Entity ID / Entity Type
- Relation 및 Relation Type
- Revision
- Provenance / Evidence metadata
- Confidence
- Stage / Change Level
- Queue ID / Block ID / Guard code
- Source Hash / Locator

Customer Runtime은 Canonical relation graph를 direct projection에 펼치지 않는다. 필요한 고객 의미는 안전한 Canonical scalar/scalar-list 필드와 Semantic-tagged Artifact/Evidence를 통해 들어온다.

외부/Legacy 문서는 다음 입력으로 사용할 수 있지만 Customer Contract의 Section Mapping과 Sanitizer를 통과해야 한다.

1. Customer-safe Canonical semantic fields
2. Semantic-tagged Engineering/Stage Artifact
3. Verified Source Evidence
4. Test / Verification Result
5. Operations Knowledge

구형 문서는 Stage metadata/제목/파일명 추론을 compatibility fallback으로만 사용할 수 있다.

## 7. Human Projection에는 Machine Taxonomy를 그대로 노출하지 않는다

Profile의 `sources.canonical`, `sources.stages`, 내부 artifact id 같은 Selector는 Machine-side 설정이므로 유지할 수 있다. 하지만 사람이 읽는 최종 Template에는 다음을 기본 노출하지 않는다.

```text
RQ / FR / BR / FTR / TASK / AC / TC 같은 Canonical taxonomy
CONFIRMED_BUSINESS / DEFERRED 같은 내부 상태 enum
SOURCE_BLOCK / ITERATE / ALERT 같은 Guard code
Queue ID / Recheck At enum
Canonical Revision / Provenance / Source Hash
```

필요한 의미는 사용자 언어로 번역한다.

```text
SOURCE_BLOCK       → 개발 전에 반드시 확인
ITERATE            → 진행 가능, 추후 보완
ALERT              → 주의사항
BEFORE_SOURCE_WRITE→ 개발 시작 전
```

Stable Block ID는 Agent 수정 경계를 위해 HTML comment 등 숨김 marker로 유지할 수 있다.

## 8. Profile 작성 규칙

최소 필드:

```yaml
schema_version: 1
profile_id: MY_PROFILE
artifacts:
  my_artifact:
    audience: CUSTOMER
    template: ...
    output_path: ...
    authoring: GENERATED_VIEW
    sources:
      stages: [...]
```

Engineering Profile은 기본적으로 Canonical semantic owner와 Agent projection owner를 사용한다.

```yaml
semantic_owner: CANONICAL
projection_owner: AGENT
manual_edit_policy: TYPO_ONLY
```

프로젝트 Config의 `documents.*.output_root`만 바꿔 Profile artifact 경로가 자동 이동한다고 가정하지 않는다. 실제 artifact output path의 권위는 Profile의 `output_path`다.

## 9. 검증

```bash
python sdlc/scripts/tailoring_runtime.py validate-profile --profile ENGINEERING_SDD_COMPACT
python sdlc/scripts/tailoring_runtime.py validate-profile --profile CUSTOMER_WATERFALL_FULL
python sdlc/scripts/tailoring_runtime.py validate-profile --profile CUSTOM_HRIS_HUNEL_ENGINEERING
```

고정 문서 수를 Framework 전체의 PASS 조건으로 두지 않는다. Profile A를 바꿨을 때 다른 audience topology가 바뀌지 않는지가 핵심 불변조건이다.

`PROFILE_PRIMARY_SET` Profile은 별도로 required artifact set이 모두 갱신되었는지도 확인한다. 하나라도 빠지면 완료로 보지 않고 Projection Refresh가 필요하다.
