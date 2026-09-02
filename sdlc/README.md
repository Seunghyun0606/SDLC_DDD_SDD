# AI-SDLC Harness — Project Quick Start

이 문서는 **처음 Harness를 프로젝트 Repository에 도입하는 일반 SI/SM 참여자**를 위한 실행 기준이다. Contract/Profile 이름을 먼저 학습할 필요가 없다.

## 1. 첫 설정에서 알아야 할 것은 하나

새 프로젝트에서 사람이 직접 유지하는 기본 설정 파일은 다음 하나다.

```text
.sdlc/project.yaml
```

`project-profile.yaml`, `source-profile.yaml`, Runtime effective profile은 Framework 내부 호환/실행용이다. 일반 사용자가 이 파일들을 나눠 수정하지 않는다.

설정 흐름:

```text
프로젝트 자료/Repository
→ harness.py setup
→ .sdlc/project.yaml
→ Runtime Resolver
→ Machine effective config
→ work/change/check
```

모르는 기술/업무 사실은 예시 값으로 채우지 않고 `unresolved` 또는 이후 산출물의 확인 필요 항목으로 남긴다.

## 2. 첫 명령 — /setup

```bash
python sdlc/scripts/harness.py setup \
  --name <project-name> \
  --mode AUTO \
  --delivery STANDARD
```

`AUTO`는 Git Repository라는 사실만으로 Brownfield라고 판단하지 않고 실제 Source/build/schema 자산을 본다.

실제 Agent wrapper가 준비되어 있으면:

```bash
python sdlc/scripts/harness.py setup \
  --name <project-name> \
  --mode AUTO \
  --delivery STANDARD \
  --provider-command '<agent-command> --context {context_path} --result {result_path}'
```

Setup 이후 역할은 다음처럼 나뉜다.

```text
.sdlc/project.yaml
  사람이 유지하는 프로젝트 설정 Source of Truth

.sdlc/runtime/effective/**
  Runtime이 계산하는 Machine config/context

sdlc/config/project-profile.yaml
sdlc/config/source-profile.yaml
  기존 Executor 호환용 Machine snapshot

sdlc/config/agent-provider.json
  Agent 연결 정보. Project setting과 분리
```

Provider가 연결되지 않았으면 `CONFIGURED_PROVIDER_REQUIRED`로 끝난다. 이 상태를 작업 실행 성공으로 보지 않는다.

## 3. `.sdlc/project.yaml`을 어떻게 다루는가

사람이 빈 설정표를 수십 칸 작성하지 않는다. `setup`이 Repository에서 확인할 수 있는 값을 먼저 채운다.

주요 영역:

- 프로젝트명 / Greenfield·Brownfield·Hybrid
- `FAST / STANDARD / FULL`
- 확인된 Language/Framework
- Source/Test/Resource root
- Build/Test command
- Git 보호 Branch
- 확인된 Data/Interface/Architecture/Security 등의 프로젝트 맥락
- 아직 확인이 필요한 항목

작성 완료 예시는 `sdlc/config/project.example.yaml`에 있다. 예시 값을 실제 프로젝트 사실처럼 복사하면 안 된다.

설정 확인:

```bash
python sdlc/scripts/harness.py check --setup
```

확인할 것:

- `config_source = PROJECT_ENTRY`인지
- Mode / Delivery Profile
- Source root
- Build/Test command
- Agent Provider
- `unresolved`
- Dead Config가 없는지

## 4. Config가 실제로 소비되는지 확인한다

Config key는 다음 네 범주로 나눈다.

1. **Runtime 소비** — Delivery, Source root, Build/Test, 보호 Branch 등 실행에 직접 반영
2. **Extension 영역** — 설치된 프로젝트 Extension이 쓰는 `extensions.*`
3. **문서/프로젝트 Context** — Architecture, Coding, Data, Interface, Security 등
4. **Dead Config** — 등록된 소비자가 없는 key

Dead Config는 조용히 무시하지 않고 Runtime resolution에서 실패시킨다.

Machine inventory는 `sdlc/design/config-usage-inventory.json`에 있다. 일반 프로젝트 사용자가 이 파일을 수정할 필요는 없다.

## 5. FAST / STANDARD / FULL

### FAST
XS/S 운영 변경·소규모 기능.
- 불필요한 PROCESS/DISCOVERY/VERIFY는 조건부
- Program Spec 준비도는 핵심 항목 중심
- Reverse는 직접 관련 범위 우선

### STANDARD
일반 SI/SM 기능.
- 업무흐름/영향/설계/Program/Test/Verify 사용

### FULL
대형/고위험 구축.
- 전체 Stage + Knowledge Promotion 후보

새 Preset을 계속 만들지 않고 기본적으로 이 세 Profile을 사용한다.

## 6. 첫 Requirement 작업

Requirement가 Canonical에 등록된 뒤 실제 변경 전에 계획부터 확인한다.

```bash
python sdlc/scripts/harness.py work --target RQ-001 --plan-only
```

공식 `harness.py` 경로는 `.sdlc/project.yaml`을 읽어 Machine effective profile을 계산한 뒤 기존 Work Executor에 전달한다. 사람이 legacy profile 경로를 선택할 필요가 없다.

Provider가 준비됐으면:

```bash
python sdlc/scripts/harness.py work --target RQ-001
```

`/work`는 Provider/Git/Source write/Build/Test/Canonical Guard를 사용한다. Source 관찰만으로 고객의 업무정책을 확정하지 않는다.

## 7. 변경과 조회

```bash
python sdlc/scripts/harness.py change \
  --target RQ-001 \
  --change '환불 상태 조회를 추가한다'

python sdlc/scripts/harness.py check --target RQ-001
```

`/change`도 같은 단일 Project Config와 Git/Canonical Guard를 사용한다.

## 8. Greenfield 시작

Source가 없는 것은 정상이다. `setup`이 확인하지 못한 Framework/DB/Build 등의 기술 사실은 `unresolved`로 남길 수 있다. 사람은 업무정책, 범위, 승인, 기술 선택처럼 실제 판단이 필요한 항목에 집중한다.

Agent는 자료에서 확인할 수 있는 내용은 먼저 초안으로 만들고, 모르는 내용을 업무 사실로 발명하지 않는다.

## 9. Brownfield 시작

먼저 실제 Evidence coverage를 조사한다. “찾지 못함”을 “영향 없음”으로 해석하지 않는다.

Brownfield에서 Agent/도구가 먼저 확인해야 하는 항목:

- Source root / Module
- Build/Test
- Language/Framework
- Controller/API, Service, Repository/Mapper
- DB Schema
- Batch/Scheduler
- Interface/Event
- 기존 Test/배포 자료

확인 결과는 `.sdlc/project.yaml`과 이후 분석 산출물에 반영하고, 분석하지 못한 영역은 Coverage Gap 또는 확인 필요로 남긴다. 사용자에게 Project Profile/Source Profile 두 개를 별도로 작성시키지 않는다.

## 10. 기존 프로젝트 Compatibility

`.sdlc/project.yaml`이 없는 기존 프로젝트만 기존 `project-profile.yaml` + `source-profile.yaml`을 fallback으로 읽는다.

`setup`이 legacy 파일을 발견하면 현재 Runtime에서 실제 사용하는 핵심 값을 단일 Project Entry로 옮기고, 이후 legacy 두 파일은 Machine compatibility snapshot으로 재생성한다.

새 Project Entry가 존재하면 우선순위는 항상 다음과 같다.

```text
.sdlc/project.yaml > legacy profile
```

## 11. 기존 DOCX/PPTX/XLSX/PDF 업무문서

원본을 다시 작성시키지 않는다.

```bash
python sdlc/scripts/extract_document_evidence.py \
  --input <customer-file> \
  --output sdlc/runtime/evidence/<name>.json
```

읽을 수 없는 문서는 규칙이 없다고 판단하지 않고 Extraction/Coverage Gap으로 남긴다.

## 12. 사용자에게 보이는 문서

한국어 자연어가 기본이다.

- 근거 위치
- 원본 식별값
- 확인 수준
- 현재 상태
- 제안
- 미확정
- 현행 확인

Machine 이름은 내부 metadata에서 유지하더라도 사용자 입력값으로 요구하지 않는다.

## 13. Validation

```bash
python -m unittest tests.test_project_entry_config -v
python sdlc/scripts/harness.py check --setup
```

이 검증은 Config/Runtime 연결을 확인한다. 실제 외부 Agent 품질이나 일반 분석가·개발자의 최초 사용성을 증명하지는 않는다.

## 14. 현재 검증 한계

별도 실증이 필요한 것:

- 실제 외부 Agent Provider가 `.sdlc/project.yaml` 기반 실행에서 일관되게 동작하는가
- 저수준 Agent가 모르는 정보를 OPEN으로 남기는가
- 일반 분석가/개발자/QA가 하나의 설정 파일만 보고 필요한 변경을 할 수 있는가
- 실제 고객 정책을 Source Evidence로 오승격하지 않는가
- Hosting의 Branch Protection이 실제 적용됐는가

Fixture/Test 성공은 실제 Agent/Human 성공으로 간주하지 않는다.
