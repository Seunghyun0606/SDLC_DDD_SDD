# Tailoring 설정 가이드

## 1. Tailoring이 결정하는 것

Tailoring Profile은 **어떤 의미를 어떤 Human Artifact로 보여줄지** 결정한다. Canonical 의미나 Change Level을 바꾸지 않는다.

Engineering과 Customer Tailoring은 서로 독립이다.

```text
Canonical Spec
├─ Engineering Profile → 개발용 Living Spec
└─ Customer Profile    → 고객 제출/합의 문서
```

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

Engineering 문서를 Customer 문서와 같은 번호로 맞추지 않는다.

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

Customer 입력은 우선 다음 의미 계층을 사용한다.

1. Canonical Spec
2. Canonical Relation
3. Semantic-tagged Engineering Projection
4. Verified Source Evidence
5. Test / Verification Result
6. Operations Knowledge

구형 문서는 Stage metadata/제목/파일명 추론을 compatibility fallback으로만 사용할 수 있다.

## 7. Profile 작성 규칙

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

## 8. 검증

```bash
python sdlc/scripts/tailoring_runtime.py validate-profile --profile ENGINEERING_SDD_COMPACT
python sdlc/scripts/tailoring_runtime.py validate-profile --profile CUSTOMER_WATERFALL_FULL
```

고정 문서 수를 PASS 조건으로 두지 않는다. Profile A를 바꿨을 때 다른 audience topology가 바뀌지 않는지가 핵심 불변조건이다.
