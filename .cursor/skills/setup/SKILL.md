# /setup

프로젝트 최초 도입용 설정 Skill. 실제 실행 Runtime은 `sdlc/scripts/bootstrap_project.py`이며 일반 사용자는 `sdlc/scripts/harness.py setup`만 사용한다.

## 사용자에게 보이는 설정은 하나

새 프로젝트에서 사람이 직접 유지하는 기본 설정 파일은 다음 **1개**다.

```text
.sdlc/project.yaml
```

일반 분석가·설계자·개발자·QA에게 `project-profile.yaml`, `source-profile.yaml`, Starter Manifest, Contract 구조를 먼저 학습시키지 않는다.

기존 호환 파일은 Runtime이 계산한다.

```text
.sdlc/project.yaml                         # 사람이 보는 Source of Truth
        ↓ Runtime Resolver
.sdlc/runtime/effective/project-profile.json  # Machine artifact
.sdlc/runtime/effective/source-profile.json   # Machine artifact
.sdlc/runtime/effective/project-context.json  # Machine context
sdlc/config/project-profile.yaml              # Legacy compatibility snapshot
sdlc/config/source-profile.yaml               # Legacy compatibility snapshot
```

Legacy profile에는 `MACHINE-GENERATED ... DO NOT EDIT` 표시를 넣는다. 새 프로젝트에서 두 profile을 수정해 설정을 바꾸는 UX로 회귀하지 않는다.

## 기본 원칙

1. 사용자는 프로젝트명·유형·진행 수준과 실제 프로젝트 자료만 제공한다.
2. Source root, Build/Test, Language/Framework/DB는 Repository에서 먼저 자동 탐색한다.
3. 자동으로 확인하지 못한 값은 `unresolved`에 모은다.
4. 빈 Template이나 수십 개 Config placeholder를 사람이 채우게 하지 않는다.
5. 업무정책·범위·승인·기술 선택처럼 사람의 판단권한이 필요한 것만 확인한다.
6. 알 수 없는 사실은 합리적으로 보인다는 이유로 확정하지 않는다.
7. 설정 key가 Runtime/Extension/문서 중 어디에서도 사용되지 않으면 `DEAD_CONFIG`로 실패시킨다. 조용히 무시하지 않는다.

## 실제 첫 실행

```bash
python sdlc/scripts/harness.py setup \
  --name <project-name> \
  --mode AUTO \
  --delivery STANDARD
```

실제 Agent/CLI Provider가 준비되어 있으면 같은 명령에 연결한다.

```bash
python sdlc/scripts/harness.py setup \
  --name <project-name> \
  --mode AUTO \
  --delivery STANDARD \
  --provider-command '<agent-command> --context {context_path} --result {result_path}'
```

Provider가 연결되지 않았으면 `CONFIGURED_PROVIDER_REQUIRED`로 남긴다. 설정 파일이 존재한다는 이유만으로 실제 Agent 작업 성공이라고 표현하지 않는다.

## Fast Path — 최초 5개 질문

이 5개는 여러 Config 파일을 작성시키기 위한 질문이 아니라 **setup 입력과 프로젝트 자료 위치를 파악하기 위한 질문**이다.

1. **프로젝트 유형**
   - `GREENFIELD / BROWNFIELD / HYBRID / AUTO`
   - 모르면 `AUTO`.
2. **요구사항 또는 변경요청 위치**
   - 실제 파일/문서/Issue 위치만 알려준다.
3. **Source/Repository 위치**
   - Greenfield에서 Source가 없으면 정상이다.
   - Brownfield는 실제 Source 기준점이 필요하다.
4. **Build/Test 경로**
   - 알고 있으면 제공하고, 모르면 Agent/Runtime이 탐색한다.
5. **고객용 문서 필요 여부**
   - 프로젝트 수행 맥락을 위한 질문이며 기본 Project Config를 여러 파일로 늘리지 않는다.

## Mode별 사용자 안내

프로젝트 유형에 따라 참고할 시작 자료만 달라진다. Config 파일 수는 늘어나지 않는다.

- `GREENFIELD` → `sdlc/starter-kits/greenfield/`
- `BROWNFIELD` → `sdlc/starter-kits/brownfield/`
- `HYBRID` → Brownfield Source 기준과 Greenfield 신규 영역을 함께 사용
- `AUTO` → Repository Evidence를 보고 Mode를 결정한 뒤 위 안내로 연결

기존 Starter/Preset 호환을 위해 Machine 내부에는 다음 mapping을 유지할 수 있다.

- `GREENFIELD` → `greenfield-default`
- `BROWNFIELD` → `brownfield-auto`

이 ID들은 **Legacy compatibility용**이며 일반 사용자가 선택·입력하거나 별도 설정 파일로 관리할 필요가 없다. Starter Kit도 또 다른 설정 Source of Truth로 사용하지 않는다.

## `.sdlc/project.yaml` 작성 원칙

Bootstrap은 빈 항목을 대량 생성하지 않는다. 확인된 값 중심으로 만든다.

예시:

```yaml
schema_version: 1
project:
  name: "order-service"
  mode: "BROWNFIELD"
delivery:
  profile: "STANDARD"
technology:
  language: "Java"
  framework: "Spring"
  build:
    - "./mvnw -q -DskipTests package"
  test:
    - "./mvnw test"
source:
  roots:
    - "src/main/java"
git:
  protected_branches:
    - "main"
documents:
  language: "ko-KR"
unresolved:
  - "부분취소 업무정책 확인 필요"
```

Architecture/Coding/Data/Interface/Security/Deployment 같은 프로젝트 맥락은 **확인된 값이 있을 때만** 추가한다. 상세 작성 완료 예시는 `sdlc/config/project.example.yaml`을 참고한다. 예시 값을 실제 프로젝트의 사실처럼 복사하지 않는다.

## Config 소비 구분

`runtime_config.py`는 모든 leaf key를 다음으로 분류한다.

- **Runtime 소비**: Delivery, Source root, Build/Test, 보호 Branch 등 실행에 직접 사용
- **Extension 소비 영역**: `extensions.*`
- **문서/프로젝트 Context**: Language/Framework/Architecture/Coding/Data/Interface/Security/Deployment 등
- **Dead Config**: 등록된 소비자가 없는 key. Runtime resolution 실패

기계 판정 목록은 `sdlc/design/config-usage-inventory.json`에 기록한다. 사용자에게 이 내부 inventory를 작성하도록 요구하지 않는다.

## 자동 탐색 범위

`bootstrap_project.py`는 다음을 근거 기반으로 조사한다.

- `pom.xml`, Gradle, `package.json`, `pyproject.toml`
- 흔한 Source/Test/Resource root
- Java/Spring/MyBatis/JPA/Kafka 사용 신호
- Schema/DDL 파일
- Maven/Gradle/NPM/Python Test command 후보

Git Repository라는 사실만으로 Brownfield라고 판정하지 않는다. 찾지 못한 Source/Build/Test를 `없음`이나 `영향 없음`으로 확정하지 않는다.

## Delivery Profile

- `FAST`: 소규모 운영 변경/기능
- `STANDARD`: 일반 SI/SM 기능
- `FULL`: 대형·고위험 범위

새 Preset을 계속 만들지 않고 이 세 Profile을 Runtime 정책으로 사용한다.

## 기존 프로젝트 Compatibility

`.sdlc/project.yaml`이 없는 기존 프로젝트만 `sdlc/config/project-profile.yaml` + `source-profile.yaml`을 Legacy fallback으로 읽을 수 있다.

`setup` 실행 시 기존 Legacy profile만 발견되면 사용되는 핵심 값을 `.sdlc/project.yaml`로 옮긴 뒤 두 profile은 Machine compatibility snapshot으로 재생성한다.

신규 Project Entry가 존재하는 순간:

```text
.sdlc/project.yaml > Legacy profile
```

순서가 고정된다.

## OPEN 처리

사람이 보는 핵심은 다음뿐이다.

- 무엇을 확인해야 하는가
- 현재 확인된 근거는 무엇인가
- 어떤 판단/승인이 필요한가
- 누가 결정하는가

기술 탐색으로 확인할 수 있는 내용을 사람에게 질문하지 않는다. Source에서 확인한 사실만으로 Business Truth를 확정하지 않는다.

## Validation

```bash
python sdlc/scripts/harness.py check --setup
python -m unittest tests.test_project_entry_config -v
```

확인 기준:

- `.sdlc/project.yaml` 하나로 Delivery가 FAST/STANDARD/FULL에 실제 반영되는가
- Source root가 Work Runtime의 write scope로 전달되는가
- Build/Test가 Development verification 설정으로 전달되는가
- Legacy profile 변경이 Project Entry를 덮어쓰지 못하는가
- 등록되지 않은 Config key가 `DEAD_CONFIG`로 실패하는가

Provider가 준비된 뒤 첫 작업 계획:

```bash
python sdlc/scripts/harness.py work --target <RQ-ID> --plan-only
```

## 준비도 경계

- Config/Runtime/Test가 연결되어도 실제 저수준 Agent 반복실행 검증을 대신하지 않는다.
- 실제 Human이 `.sdlc/project.yaml`을 별도 설명 없이 수정할 수 있는지는 Human Pilot에서 확인해야 한다.
- Brownfield Coverage가 부족하면 Impact COMPLETE로 표현하지 않는다.
- Business Truth는 권한자 확인 없이 확정하지 않는다.
