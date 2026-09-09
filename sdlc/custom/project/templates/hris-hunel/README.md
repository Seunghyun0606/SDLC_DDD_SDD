# HRIS / hunel 프로젝트용 개발 문서 Template

이 Template은 HRIS 예시 문서를 그대로 복제한 것이 아닙니다. Framework 내부의 **작업 내용 → 프로젝트 문서 구성 → 개발 문서 생성** 흐름을 유지하면서 hunel 5.0의 구현 특성을 프로젝트 전용 문서에 담은 것입니다.

Framework 자체를 설명할 때 필요한 내부 용어는 한 번만 병기합니다: 문서 구성(Tailoring Profile), 생성 문서(Engineering Projection).

## 왜 Standard를 교체하지 않는가

`ENGINEERING_SDD_COMPACT`는 기술 종류와 관계없이 사용할 수 있는 기본 개발 문서입니다. 반면 hunel 프로젝트는 다음 구현 특성이 강합니다.

- JSP + Java + SQLResource XML이 Program 단위로 밀접하게 연결됨
- `hunelCommonDS`, `IPreparedData`, `VarStatement`, `CUDSQLManager`
- ibsheet / doAction 기반 UI-Server 연결
- `chkAuthMenu`, `chkAuthTrans`, `<com:auth>` 기반 권한 연결
- DB Procedure가 핵심 업무 로직을 가질 수 있고 실제 DB 반영 담당자가 Agent와 다를 수 있음

이 정보는 모든 프로젝트의 Standard Template에 강제할 수 없으므로 HRIS 프로젝트 전용 개발 문서 구성으로 둡니다.

## Standard에도 반영한 공통 개선

HRIS 예시에서 다음 개념은 특정 프레임워크와 무관하므로 `sdlc/templates/engineering/standard/`에도 반영했습니다.

1. 하나의 업무 단위에 여러 Program이 연결될 수 있도록 변경 범위를 구분
2. 현재 소스에서 확인한 내용과 아직 확인하지 못한 영역을 구분
3. 실제 변경에 필요한 기술 단락만 남기는 조건부 구현 블록
4. Agent 직접 수정 / Script 산출 / 사람 실행 / 검증 전용을 구분하는 소스 변경 방식
5. 미확정 항목을 `개발 전 확인 필요 / 진행 가능·추후 보완 / 주의 필요`로 나눠 실제 개발 영향만 명확히 표시

## Custom 2문서 구조

| 문서 | 단위 | 역할 | 주로 다루는 내용 |
|---|---|---|---|
| `01_업무정의서.md` | 업무 단위 | 무엇을 왜 바꾸는지 정리 | 요구, 현재 상태, 개선 후 흐름, 업무 규칙, 인수 기준, 영향 |
| `02_작업지시서.md` | Program 또는 개발 대상 | 실제 구현 방법 정리 | hunel 구현 방식, JSP/Java/XML 연결, 소스 변경 범위, 검증 |

업무정의서에서는 hunel 구현 상세를 최소화하고, 구현 내용은 작업지시서로 모았습니다. 특히 프로파일 권한의 **업무 의미**와 `chkAuthMenu`/`<com:auth>` 같은 **기술 구현**을 분리합니다.

## 적용 Profile

`CUSTOM_HRIS_HUNEL_ENGINEERING`

설정 파일:

```text
sdlc/custom/project/tailoring/CUSTOM_HRIS_HUNEL_ENGINEERING.yaml
```

Runtime은 프로젝트 전용 설정을 `sdlc/custom/project/tailoring/`에서 우선 찾으므로 Core Config를 수정할 필요가 없습니다.

## 프로젝트 적용

프로젝트 root의 `.sdlc/project.yaml`에서 Engineering Profile만 선택합니다.

```yaml
documents:
  engineering:
    profile: "CUSTOM_HRIS_HUNEL_ENGINEERING"
    manual_edit_policy: "HUMAN_REVIEW"
    freshness: "CANONICAL_REVISION"
```

`documents.internal.profile`은 이전 버전 호환용 이름이므로 신규 설정에서는 사용하지 않습니다. `template_set` 같은 별도 키도 필요하지 않습니다.

전체 예시는 다음 파일을 참고합니다.

```text
sdlc/custom/project/config/project.hris-hunel.example.yaml
```

고객 문서와 PM 문서 구성은 개발 문서 구성과 독립적이므로 기존 `CUSTOMER_STANDARD_3`, `PM_STANDARD` 등을 그대로 선택할 수 있습니다.

## 사용 원칙

- 기존 시스템의 소스는 현재 상태를 확인하는 근거이며, 개선 후 업무 규칙으로 자동 확정하지 않습니다.
- Program ID나 3-file set이 실제 소스에서 확인되지 않으면 임의로 파일을 만들지 않습니다.
- Procedure Source가 Repository에 없으면 Agent는 DB에 직접 반영하지 않고 Script 산출물과 사람 적용 절차를 분리합니다.
- **개발 전 확인 필요**는 전체 작업을 중단한다는 뜻이 아니라, 해당 결정이 필요한 소스 수정을 먼저 하지 않는다는 뜻입니다.
- 예상하지 못한 다른 Program/DB Object 영향이 발견되면 소스 변경 범위를 조용히 넓히지 않고 영향 대상으로 다시 검토합니다.
