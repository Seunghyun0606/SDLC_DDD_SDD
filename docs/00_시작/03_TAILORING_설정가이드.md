# Tailoring 설정 가이드

이 문서는 **어떤 사람용 문서를 몇 종, 어떤 이름과 경로로 만들지** 프로젝트에 맞게 설정하는 방법을 설명한다.

Config 전체 옵션은 `02A_PROJECT_CONFIG_옵션_상세가이드.md`, Template 작성 원칙은 `04_TEMPLATE_및_산출물_가이드.md`를 본다.

## 1. Tailoring이 결정하는 것

Tailoring Profile은 사람에게 보여줄 문서 구성을 결정한다.

```text
프로젝트 기준 정보
├─ Engineering Profile → 설계·개발자용 생성 문서
└─ Customer Profile    → 고객용 생성 문서
```

Change Level은 분석·근거·검토 깊이를 결정하고, Profile은 문서 구성을 결정한다. 둘을 같은 설정으로 사용하지 않는다.

## 2. 신규 프로젝트의 기본 Profile

### Engineering

```text
ENGINEERING_SDD_COMPACT
```

기본 구성:

```text
docs/10_engineering/<TARGET>/
├─ 00_work-map.md
├─ specs/<TARGET>.md
└─ programs/<TARGET>.md   # 필요할 때만
```

Program Spec은 기본 Profile에서 L3 이상 또는 실제 상세 구현 차이를 별도 문서로 관리할 필요가 있을 때 사용한다.

### Customer

```text
CUSTOMER_STANDARD_3
```

기본 3종:

- 요구·업무·기능 합의서
- 영향·개발범위 공유서
- 테스트·인수·운영 결과서

더 상세한 Waterfall 고객문서가 필요하면 `CUSTOMER_WATERFALL_FULL` 8종을 선택할 수 있다.

## 3. Legacy Formal Profile은 기본 배포가 아니다

다음은 기존 Formal 문서 체계와의 호환용이다.

```text
STANDARD_3
STANDARD_5
STAGE_ORIENTED_FULL
```

이 Profile과 Legacy Tailoring Template은 **신규 Project Scaffold에 기본 포함되지 않는다.** Framework 관리자가 Scaffold 생성 시 다음 옵션을 사용해 Compatibility package를 포함한 프로젝트에서만 사용할 수 있다.

```bash
python sdlc/scripts/build_project_scaffold.py \
  --root . \
  --output <outside-target-directory> \
  --include-legacy-compatibility
```

이 명령은 Framework Repository 관리자가 배포 패키지를 만들 때만 사용한다. 배포받은 프로젝트 참여자가 실행하는 일반 작업 명령이 아니다.

## 4. Profile 선택

`.sdlc/project.yaml`에서 audience별로 독립 선택한다.

```yaml
documents:
  engineering:
    profile: ENGINEERING_SDD_COMPACT
  customer:
    profile: CUSTOMER_STANDARD_3
```

고객 제출문서가 많아졌다고 Engineering Profile을 같이 늘릴 필요는 없다.

```yaml
documents:
  engineering:
    profile: ENGINEERING_SDD_COMPACT
  customer:
    profile: CUSTOMER_WATERFALL_FULL
```

## 5. Project Custom Profile

프로젝트 고유 문서가 필요하면 Core 표준 파일을 수정하지 않고 다음 위치를 사용한다.

```text
sdlc/custom/project/
├─ tailoring/
└─ templates/
   ├─ engineering/
   └─ customer/
```

예:

```text
sdlc/custom/project/tailoring/CUSTOM_HRIS_HUNEL_ENGINEERING.yaml
sdlc/custom/project/templates/hris-hunel/01_업무정의서.md
sdlc/custom/project/templates/hris-hunel/02_작업지시서.md
```

Profile에서 주로 정하는 항목:

- artifact id
- audience
- template 경로
- output path
- 표시 우선순위
- 어떤 작업 근거를 사용할지
- 조건부 생성 기준
- Change Level별 작성 상세도

## 6. 항상 유지할 문서와 조건부 문서

프로젝트에 따라 두 가지 방식이 있다.

### 작업 단계에 따라 필요한 문서만 선택

작업 단계와 조건에 맞는 문서만 생성하는 방식이다. 표준 Compact Profile의 조건부 Program Spec이 대표적이다.

### Profile의 필수 문서 세트를 항상 유지

프로젝트가 “이 Profile을 사용하면 이 문서들은 항상 있어야 한다”고 정한 경우 `projection_topology: PROFILE_PRIMARY_SET`을 사용한다.

예: HRIS Custom 2종

```text
CUSTOM_HRIS_HUNEL_ENGINEERING
├─ 01_업무정의서.md
└─ 02_작업지시서.md
```

이 경우 Change Level이 낮아도 두 문서를 없애지 않고 내용의 상세도만 조절한다.

```text
L1/L2 → 두 문서 유지 + 간결하게
L3/L4 → 두 문서 유지 + 표준 상세도
L5    → 두 문서 유지 + 상세하게
```

즉 **분석 깊이를 줄이는 것과 Profile 필수 문서를 없애는 것은 다른 문제**다.

## 7. Customer Custom Profile

Customer Profile은 Engineering 문서 수나 순번을 따라가지 않는다.

예를 들어 고객이 다음 5종을 요구한다면 Customer Profile에서 5종을 정의한다.

```text
01_요구사항합의서.md
02_업무분석서.md
03_기능설계서.md
04_테스트결과서.md
05_운영인계서.md
```

한 개의 고객 의미군을 여러 문서로 나누거나 여러 의미를 한 문서로 합칠 수 있다. 이때 각 artifact의 `projection_type`, `template`, `output_path`, `sources`를 명시한다.

고객문서에는 개발 내부 식별자와 Runtime 상태를 기본 노출하지 않고 고객에게 필요한 업무 의미만 사용한다. 상세 표현 기준은 `15_고객문서_미리보기_가이드.md`를 본다.

## 8. 출력 경로의 권위

실제 생성 파일 위치는 선택 Profile artifact의 `output_path`가 기준이다.

예:

```yaml
artifacts:
  work_definition:
    template: sdlc/custom/project/templates/engineering/01_업무정의서.md
    output_path: docs/10_engineering/{target}/01_업무정의서.md
```

`.sdlc/project.yaml`의 `documents.*.output_root`만 변경했다고 Profile의 모든 artifact 경로가 자동으로 바뀐다고 가정하지 않는다.

## 9. Profile 검증

```bash
python sdlc/scripts/tailoring_runtime.py validate-profile \
  --profile ENGINEERING_SDD_COMPACT

python sdlc/scripts/tailoring_runtime.py validate-profile \
  --profile CUSTOMER_WATERFALL_FULL
```

Project Custom Profile도 같은 방식으로 검증한다.

```bash
python sdlc/scripts/tailoring_runtime.py validate-profile \
  --profile CUSTOM_HRIS_HUNEL_ENGINEERING
```

검증 시 확인할 핵심은 다음이다.

- 선택한 Template 파일이 실제 존재하는가
- output path가 충돌하지 않는가
- Engineering/Customer 문서 구성이 서로 의도치 않게 묶이지 않았는가
- Profile 필수 문서 세트를 모두 생성·갱신할 수 있는가

## 10. 다음 문서

- Template과 생성 문서 구조: `04_TEMPLATE_및_산출물_가이드.md`
- 프로젝트 Config: `02_PROJECT_설정가이드.md`
- Config 옵션 정확한 Reference: `02A_PROJECT_CONFIG_옵션_상세가이드.md`
- 고객문서 운영: `15_고객문서_미리보기_가이드.md`
