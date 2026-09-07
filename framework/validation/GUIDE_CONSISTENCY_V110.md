# v1.10 Guide Consistency Validation

기준 Branch: `SDLC_DESIGN_SESSION_FIRST/projection-separation/v1.10.0`

## 목적

정리된 v1.10 Runtime/Config/Profile/Template/Project Scaffold 구조를 기준으로 `docs/00_시작` 사용자 가이드가 실제 동작과 일치하는지 점검한다.

## 점검 대상

- `START_HERE.md`
- `02_PROJECT_설정가이드.md`
- `03_TAILORING_설정가이드.md`
- `04_TEMPLATE_및_산출물_가이드.md`
- `05_이해관계자별_작업가이드.md`
- `07_BROWNFIELD_SSOT_현행화가이드.md`
- `11_INPUT_자료_준비가이드.md`
- `01_STANDARD_SCAFFOLD_사용가이드.md`, `06_CUSTOM_SCAFFOLD_적용가이드.md`의 Compatibility 경계
- `harness-package-contract.json`
- `project-scaffold-contract.json`

## 발견 및 조치

### 1. 이해관계자 가이드의 Legacy `internal` 예제

기존 `05_이해관계자별_작업가이드.md`가 `documents.internal.profile: STANDARD_5`와 `INTERNAL_IT`를 현행 사용 예처럼 노출하고 있었다.

조치:
- 신규 예제를 `documents.engineering.profile: ENGINEERING_SDD_COMPACT`로 변경
- BA/설계/개발 View를 `Engineering Projection`으로 통일
- Customer/PM/Machine 역할 용어를 현재 Projection 모델에 맞게 정리

### 2. Brownfield 가이드의 Optional Script 오인 가능성

기존 `07_BROWNFIELD_SSOT_현행화가이드.md`는 `run_source_reverse_check.py`를 기본 Project Runtime처럼 바로 실행하도록 안내했다.

실제 Contract에서는 해당 Script가 `BROWNFIELD_EXTENSION`이다.

조치:
- 기본 Project에서는 `/work` + `/check`를 우선 사용하도록 변경
- Reverse/Drift Script는 Brownfield Extension이 실제 포함된 경우에만 사용하도록 명시
- Extension 부재를 `Drift 없음`으로 해석하지 않도록 경고 추가
- `Internal Artifact` 용어를 `Engineering Projection`으로 정리

### 3. START_HERE의 Framework Distribution 경계

`build_project_scaffold.py`는 Framework distribution tool이며 생성 Project에는 포함되지 않는다.

조치:
- 해당 명령은 Framework Repository에서 Framework 관리자가 실행하는 명령임을 명시
- 배포 프로젝트가 자기 자신을 다시 Scaffold하는 흐름이 아님을 명시
- 현재 활성 가이드 목록에 `07_BROWNFIELD...`, `11_INPUT...`을 추가
- `01`, `06`은 Compatibility Notice이며 신규 Project Scaffold에서 제외됨을 명시

### 4. Project Config Legacy 예제

`02_PROJECT_설정가이드.md`가 `documents.internal.profile` YAML을 복사 가능한 예제로 보여주고 있었다.

조치:
- 신규 프로젝트의 유일한 활성 예제는 `documents.engineering.profile`로 유지
- `documents.internal.profile`은 기존 v1.9 입력을 읽기 위한 Runtime migration compatibility임만 설명
- 신규 `.sdlc/project.yaml`에는 다시 작성하지 않도록 명시

### 5. Template 역할

`03`, `04`, `11`은 현재 구조와 대체로 일치했다.

현재 사용자 가이드의 Template 역할은 다음으로 고정한다.

```text
sdlc/templates/semantic/          = Stage 의미/Evidence 구조
sdlc/templates/engineering/       = Engineering Projection Template
sdlc/templates/customer/          = Customer Projection Template
sdlc/templates/tailoring/standard = Legacy/Formal Projection Template
sdlc/tailoring/standard/*.yaml    = Artifact 조립/선택 Profile
```

## 자동 회귀

`tests/test_guide_consistency_v110.py`를 추가했다.

검증 항목:
- START_HERE가 현재 활성 가이드를 모두 연결하는지
- 활성 가이드에 제거된 Stage Template 경로가 다시 들어오지 않는지
- 이해관계자 가이드가 Engineering 용어를 사용하는지
- Framework distribution tool을 Project Runtime 도구처럼 안내하지 않는지
- Brownfield Reverse Script가 Extension으로 설명되는지
- Compatibility Notice 01/06이 신규 Project Scaffold에서 제외되는지
- Template 가이드가 Semantic / Projection / Tailoring Profile 역할을 구분하는지

## 최종 자동 검증

최종 보고서 반영 직전 Head `cc001f1be05434707e4b2fd4ff86ab377ee86279`에서 다음 PR Workflow가 모두 성공했다.

- P0 P1 Production Readiness #321 — SUCCESS
- Worklist sync quality #1235 — SUCCESS
- Docs quality #485 — SUCCESS
- Greenfield Work Executor E2E #331 — SUCCESS
- Public Brownfield Pilot #344 — SUCCESS

`Worklist sync quality`의 전체 unittest에는 Guide consistency 6개가 포함되어 모두 통과했다.

## 판정

**GUIDE_CONSISTENCY_PASS_WITH_AUTOMATED_REGRESSION**

Guide 구조는 v1.10 Projection Separation, Semantic Template 역할, Project Scaffold asset boundary와 일치하도록 현행화되었고 자동 회귀가 추가되었다.

이 판정은 Repository/Runtime/Contract/Test 일관성 범위이며 실제 신규 사용자 관찰 기반 사용성 Pilot을 대체하지 않는다.
