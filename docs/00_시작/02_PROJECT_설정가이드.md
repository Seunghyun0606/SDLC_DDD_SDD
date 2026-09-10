# Project 설정 가이드

이 문서는 **프로젝트를 처음 설정하고 `.sdlc/project.yaml`을 운영하는 순서**만 설명한다. 각 Config Key의 정확한 허용값·기본값·Runtime 적용 여부는 `02A_PROJECT_CONFIG_옵션_상세가이드.md`를 사용한다.

## 1. 사람이 관리하는 설정은 하나

```text
.sdlc/project.yaml
```

Runtime이 만드는 `.sdlc/runtime/effective/*` 파일은 결과 파일이므로 직접 수정하지 않는다.

## 2. 최초 설정

가장 짧은 형태:

```bash
python sdlc/scripts/harness.py setup --name <project-name> --mode AUTO
```

일반 권장 예:

```bash
python sdlc/scripts/harness.py setup \
  --name <project-name> \
  --mode AUTO \
  --delivery STANDARD

python sdlc/scripts/harness.py check --setup
```

`setup`은 Repository에서 확인 가능한 다음 후보를 조사한다.

- 기존 Source root
- Test/Resource root
- Build/Test command
- Language/Framework/DB 후보

확인할 수 없는 값은 추측하지 않고 `unresolved`로 남긴다. 생성된 `.sdlc/project.yaml`을 프로젝트 실제 상황에 맞게 검토한다.

### 주의해서 사용할 Setup 옵션

```text
--force
→ 이미 존재하는 .sdlc/project.yaml을 포함한 사용자 설정을 덮어쓸 수 있다.
→ 일반적인 재실행 옵션으로 사용하지 않는다.

--no-validate
→ Setup 뒤 Harness 구조 검증을 생략한다.
→ 정상적인 최초 설정보다 Framework 문제 진단/관리 목적에서만 사용한다.
```

`--customer`, `--reverse`는 과거 CLI 호환을 위해 남아 있는 인자다. 신규 프로젝트의 사용자 설정 필드로 사용하지 않는다.

`setup --provider-command`도 과거 자동화와의 호환을 위한 편의 경로다. 신규 프로젝트에서 HEADLESS Agent Provider를 설정하려면 이 일회성 인자보다 `.sdlc/project.yaml`의 `agent.execution`과 `agent.provider.command`를 기준으로 관리한다.

## 3. Project Mode

```yaml
project:
  mode: BROWNFIELD
```

지원 값은 다음과 같다.

- `GREENFIELD`: 신규 구축 중심
- `BROWNFIELD`: 기존 시스템 개선 중심
- `HYBRID`: 신규 + 기존 시스템 혼합
- `AUTO`: Setup에서 Repository를 보고 후보를 판단할 때 사용

처음에는 `AUTO`를 사용할 수 있지만 설정이 끝난 뒤에는 확인된 구체 Mode를 유지하는 것을 권장한다.

## 4. Agent 실행 방식

기본은 현재 IDE/Chat/CLI의 Agent가 작업하는 `INTERACTIVE`다.

```yaml
agent:
  execution: INTERACTIVE
```

CI/Batch 등에서 Harness가 외부 Provider command를 실행해야 할 때만 `HEADLESS`를 사용한다.

```yaml
agent:
  execution: HEADLESS
  provider:
    command:
      - python
      - tools/run_agent.py
```

`HEADLESS`의 Provider 상세 옵션은 `02A_PROJECT_CONFIG_옵션_상세가이드.md`를 본다.

## 5. Source / Build / Test 확인

예:

```yaml
technology:
  language: Java
  build:
    - ./mvnw -q -DskipTests package
  test:
    - ./mvnw test

source:
  roots:
    - src/main/java
  test_roots:
    - src/test/java
  resource_roots:
    - src/main/resources
  excludes:
    - .git/**
    - target/**
```

Brownfield 프로젝트에서는 실제 기존 Source가 Repository root 옆에 그대로 존재하고 Harness가 그 Source를 조사하는 구조다. Source를 Harness 하위 전용 폴더로 옮기는 것이 기본 구조가 아니다.

Windows `.cmd/.bat/.ps1` 명령과 한글 출력 처리 기준은 `14_한글_인코딩_및_외부명령_가이드.md`를 본다.

## 6. 생성 문서 Profile 설정

신규 프로젝트 권장값:

```yaml
documents:
  engineering:
    profile: ENGINEERING_SDD_COMPACT
    manual_edit_policy: TYPO_ONLY
    freshness: CANONICAL_REVISION

  customer:
    profile: CUSTOMER_STANDARD_3
    scope: RQ
    freshness: CANONICAL_AND_AS_BUILT
    final_review:
      human_editable: true

  pm:
    profile: PM_STANDARD

  machine:
    visibility: HIDDEN
```

각 Profile의 역할은 다음과 같다.

```text
Engineering Profile → 설계·개발자가 보는 문서 구성
Customer Profile    → 고객이 보는 문서 구성
PM Profile          → 관리용 View 구성
```

Engineering과 Customer 문서 수/순번은 서로 맞출 필요가 없다.

Tailoring 상세는 `03_TAILORING_설정가이드.md`를 본다.

## 7. Legacy Formal Profile

다음 Profile은 **신규 Project Scaffold의 기본 포함 항목이 아니다.**

```text
STANDARD_3
STANDARD_5
STAGE_ORIENTED_FULL
```

기존 프로젝트의 Formal 산출물 체계를 유지해야 해서 Framework 관리자가 Project Scaffold 생성 시 `--include-legacy-compatibility`를 명시적으로 사용한 경우에만 선택한다.

신규 프로젝트에서는 `documents.engineering.profile`에 `ENGINEERING_SDD_COMPACT` 또는 프로젝트 Custom Profile을 사용하는 것이 기본이다.

과거 `documents.internal.profile`은 v1.9 호환 입력으로 읽을 수 있지만 신규 `.sdlc/project.yaml`에는 작성하지 않는다.

## 8. Change Level 설정

Change Level은 **문서 개수**가 아니라 변경의 분석·근거·검토 깊이를 결정한다.

일반 프로젝트 기본:

```yaml
change:
  level_policy: AUTO
  minimum_level: L1
```

프로젝트가 특정 RQ의 Level을 사전에 정해야 한다면:

```yaml
change:
  level_policy: AUTO
  minimum_level: L1
  target_levels:
    RQ-001:
      level: L3
      reason: "업무규칙과 기능 영향을 상세 검토해야 함"
```

작업 중 Level을 변경하거나 현재 판정 이유를 확인하는 상세 방법은 `02A_PROJECT_CONFIG_옵션_상세가이드.md`의 Change Level 항목을 본다.

중요한 구분:

```text
Change Level → 분석·근거·검토 깊이
작업 단계   → 현재 내부 실행 초점
Profile     → 사람이 보는 문서 구성
```

작은 변경도 Source 수정 전 다음 세 가지는 확인한다.

```text
요구 의도 확인
→ 현재 Source 확인
→ 영향 범위 확인
```

내부 Runtime에는 이 확인을 기계적으로 검증하는 상태 코드가 있지만 일반 사용자가 그 코드를 외우거나 문서에 직접 입력할 필요는 없다.

## 9. 프로젝트 Custom 위치

Framework 표준 파일을 고객 프로젝트에서 직접 수정하지 않는다.

```text
sdlc/custom/project/
├─ tailoring/      # Project Custom Profile
├─ templates/      # Project Custom 문서 Template
├─ standards/      # 개발 가이드/표준
├─ rules/          # Agent 강제 규칙/금지사항
└─ config/         # Project Extension 설정
```

- 문서 Profile Custom: `03_TAILORING_설정가이드.md`
- Template/산출물: `04_TEMPLATE_및_산출물_가이드.md`
- 개발가이드/Rule: `16_프로젝트_개발가이드_Agent_적용가이드.md`

## 10. 출력 경로 주의

`documents.*.output_root`가 있다고 해서 선택 Profile 안의 모든 `output_path`가 자동 치환되는 것은 아니다. 실제 생성 파일 경로의 권위는 선택한 Tailoring Profile artifact의 `output_path`다.

따라서 출력 폴더를 바꾸려면 Custom Profile의 artifact 경로를 함께 설계한다.

## 11. 설정 확인

```bash
python sdlc/scripts/harness.py check --setup
```

확인할 것:

- Project Mode가 실제 프로젝트와 맞는가
- Source roots가 실제 Source 위치를 가리키는가
- Build/Test command가 실제 실행 가능한가
- Engineering/Customer Profile이 원하는 문서 구성을 가리키는가
- 확인하지 못한 항목이 `unresolved`에 남아 있는가
- 사용하지 않는 잘못된 Config Key가 없는가

Config Key의 정확한 분류와 오류 조건은 `02A_PROJECT_CONFIG_옵션_상세가이드.md`를 사용한다.

## 12. 다음 작업

설정이 끝나면 다음 순서로 진행한다.

```text
입력자료 준비
→ Requirement Intake 또는 rq-add
→ RQ 작업목록/참고자료 확인
→ /work
→ /check
```

- Input: `11_INPUT_자료_준비가이드.md`
- 소수 신규 RQ: `17_RQ_간편추가_가이드.md`
- RQ 관리: `12_RQ_작업목록_운영가이드.md`
- 전체 CLI 기능: `18_HARNESS_CLI_기능_참조가이드.md`
