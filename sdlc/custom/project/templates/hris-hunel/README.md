# HRIS / hunel Custom Engineering Template

이 Template은 HRIS 프로젝트 예시 문서를 그대로 복제한 것이 아니라, 현재 v1.10 Framework의 **Semantic → Tailoring Profile → Engineering Projection** 경계를 유지하면서 hunel 5.0의 구현 특성을 Custom Projection으로 분리한 것입니다.

## 왜 Standard를 교체하지 않는가

`ENGINEERING_SDD_COMPACT`는 기술스택에 독립적인 기본 Engineering View입니다. 반면 hunel 프로젝트는 다음 구현 특성이 강합니다.

- JSP + Java + SQLResource XML의 Program 단위 밀결합
- `hunelCommonDS`, `IPreparedData`, `VarStatement`, `CUDSQLManager`
- ibsheet / doAction 기반 UI-Server 연결
- `chkAuthMenu`, `chkAuthTrans`, `<com:auth>` 기반 권한 연결
- DB Procedure가 핵심 업무 로직을 소유할 수 있으며 실제 DB 반영 주체가 Agent와 다름

이 정보는 다른 프로젝트의 Standard Template에 강제할 수 없으므로 Custom Engineering Profile로 둡니다.

## Standard에서 일반화한 개선

HRIS 예시에서 다음 개념은 특정 프레임워크와 무관하므로 `sdlc/templates/engineering/standard/`에도 반영했습니다.

1. Work Unit과 Program을 구분하고 1:N을 허용하는 변경 경계
2. AS-IS Evidence와 Coverage Gap을 구분하는 구조
3. 실제 변경 특성에 따라 필요한 기술 단락만 남기는 조건부 구현 블록
4. Agent 직접수정 / Script 산출 / 사람 실행 / 검증전용을 구분하는 Source Change Boundary
5. 미확정 항목을 `SOURCE_BLOCK / ITERATE / ALERT`로 나눠 Source Write 영향만 명확히 하는 방식

## Custom 2문서 구조

| 문서 | 단위 | 역할 | 주요 Stage |
|---|---|---|---|
| `01_업무정의서.md` | Work Unit | WHAT/WHY, AS-IS Evidence, TO-BE, Rule, AC, 영향, Open | DECOMPOSE~IMPACT |
| `02_작업지시서.md` | Program 또는 개발 Target | hunel 구현 Pattern, 조건부 Block, JSP/Java/XML Mapping, Source Write Guard | DESIGN~VERIFY |

업무정의서에서 hunel 구현 방식은 제거하고, 구현 상세는 작업지시서로 모았습니다. 특히 프로파일 권한의 **업무 의미**와 `chkAuthMenu`/`<com:auth>` 같은 **기술 구현**을 분리합니다.

## 적용 Profile

`CUSTOM_HRIS_HUNEL_ENGINEERING`

Profile 경로:

```text
sdlc/custom/project/tailoring/CUSTOM_HRIS_HUNEL_ENGINEERING.yaml
```

Runtime은 Custom Profile을 `sdlc/custom/project/tailoring/`에서 우선 탐색하므로 Core Config를 수정할 필요가 없습니다.

## 프로젝트 적용

프로젝트 root의 `.sdlc/project.yaml`에서 Engineering Profile만 선택합니다.

```yaml
documents:
  engineering:
    profile: "CUSTOM_HRIS_HUNEL_ENGINEERING"
    manual_edit_policy: "HUMAN_REVIEW"
    freshness: "CANONICAL_REVISION"
```

`documents.internal.profile`은 호환 alias이므로 신규 설정에서는 사용하지 않습니다. `template_set` 같은 별도 키도 필요하지 않습니다.

전체 예시는 다음 파일을 참고합니다.

```text
sdlc/custom/project/config/project.hris-hunel.example.yaml
```

Customer/PM Profile은 Engineering Profile과 독립적이므로 기존 `CUSTOMER_STANDARD_3`, `PM_STANDARD` 등을 그대로 선택할 수 있습니다.

## 사용 원칙

- Brownfield Source는 AS-IS Evidence이며 자동으로 TO-BE Business Truth가 되지 않습니다.
- Program ID나 3-file set이 실제 Source에서 확인되지 않으면 임의로 파일을 만들지 않습니다.
- Procedure Source가 Repository에 없으면 Agent는 DB에 직접 반영하지 않고 Script 산출물과 사람 적용 절차를 분리합니다.
- `SOURCE_BLOCK`은 Stage 전체를 중단한다는 뜻이 아니라 잘못된 Source Write를 막는 실행 가드입니다.
- 예상 밖 다른 Program/DB Object 영향이 발견되면 Source Change Boundary를 조용히 확장하지 않고 영향/Task 후보로 되돌립니다.
