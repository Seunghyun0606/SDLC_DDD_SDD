# /setup

프로젝트 최초 도입용 설정 Skill. 실제 실행 Runtime은 `sdlc/scripts/bootstrap_project.py`이며 비숙련 사용자는 `sdlc/scripts/harness.py setup`만 사용해도 된다.

## 기본 원칙
신규 프로젝트 담당자가 Harness 내부 Profile 구조를 모두 이해하지 않아도 시작할 수 있어야 한다. 최초 설정은 **5개 질문 Fast Path**로 충분해야 하며, 실제 필요가 확인된 항목만 Advanced Setup으로 연다. Config 파일이 존재한다는 이유만으로 기능이 구현됐다고 간주하지 않는다.

## 실제 첫 실행

```bash
python sdlc/scripts/harness.py setup \
  --name <project-name> \
  --mode AUTO \
  --delivery STANDARD
```

실제 Agent/CLI wrapper가 준비되어 있으면 같은 명령에 Provider command를 연결한다.

```bash
python sdlc/scripts/harness.py setup \
  --name <project-name> \
  --mode AUTO \
  --delivery STANDARD \
  --provider-command '<agent-command> --context {context_path} --result {result_path}'
```

Runtime은 다음 실제 파일만 생성/유지한다.
- `sdlc/config/project-profile.yaml`
- `sdlc/config/source-profile.yaml`
- `sdlc/config/agent-provider.json`
- `sdlc/canonical/store.json`
- `sdlc/runtime/setup/setup-result.json`

생성한 YAML은 다시 읽어 round-trip 검증한다. 실제 Agent Provider가 연결되지 않았으면 `CONFIGURED_PROVIDER_REQUIRED`로 종료하며 `/work` 실행 가능 상태라고 과장하지 않는다.

## Fast Path — 최초 5개 입력

1. **프로젝트 유형**
   - `GREENFIELD / BROWNFIELD / HYBRID / AUTO`
   - 모르면 `AUTO`로 시작한다.
2. **요구사항 또는 변경요청 위치**
   - 파일, 폴더, 이슈, 문서 위치 중 실제 사용 가능한 기준점을 기록한다.
3. **Source/Repository 위치**
   - Greenfield로 Source가 없으면 `없음`으로 둔다.
   - Brownfield는 Repository 또는 Source bundle 기준점이 필요하다.
4. **Build/Test 경로**
   - 알고 있으면 기록한다.
   - 모르면 build file/test root를 탐색하고 찾지 못하면 빈 값/OPEN으로 둔다.
5. **고객용 문서 필요 여부**
   - `internal / customer / both`

이 5개만으로 설정 초안을 만들 수 있다. 단, **실제 문서 생성은 Agent Provider가 연결되어야 한다.**

## 자동 탐색 범위
`bootstrap_project.py`는 다음을 근거 기반으로 조사한다.
- `pom.xml`, Gradle, `package.json`, `pyproject.toml`
- 흔한 Source/Test/Resource root
- Java/Spring/MyBatis/JPA/Kafka 사용 신호
- Schema/DDL 파일
- Maven/Gradle/NPM/Python test command 후보

Git Repository라는 사실만으로 Brownfield라고 판정하지 않는다. Source/build/schema 자산이 없으면 신규 Git Repository도 Greenfield 후보가 될 수 있다.

## Fast Path 자동 기본값
- Starter Kit과 기존 Preset ID는 호환을 위해 유지한다.
- 내부 Compatibility Mapping은 `GREENFIELD → greenfield-default`, `BROWNFIELD → brownfield-auto`다.
- 실제 문서량/Stage 제어는 새 프로젝트에서는 `delivery.profile = FAST / STANDARD / FULL`을 사용한다.
- 문서 언어는 `ko-KR`을 기본으로 한다.
- 고객용 문서는 기본 `MINIMAL`이다.
- OPEN Resolution은 SOP를 요구하지 않는다.
- Brownfield Adapter가 없거나 Coverage가 부족하면 `PARTIAL_PROJECT_ADAPTER_REQUIRED` 또는 Coverage Gap으로 남긴다.
- Source root/build/test를 찾지 못하면 “없음”이나 “영향 없음”으로 확정하지 않는다.

## Mode별 시작
- `GREENFIELD` → `sdlc/starter-kits/greenfield/`
- `BROWNFIELD` → `sdlc/starter-kits/brownfield/`
- `HYBRID` → Brownfield Source 기준을 우선하고 신규 영역 요구를 함께 등록한다.
- `AUTO` → 실제 Source/build/schema 자산으로 Mode Candidate를 결정한다.

## Delivery Profile

### FAST
XS/S 운영 변경 및 소규모 기능. 중간 Stage와 관련 없는 Program DoR를 생략한다.

### STANDARD
일반 SI/SM 기능. Requirement → Process/Impact → Design → Program → Development/Test/Verify의 일반 흐름을 사용한다.

### FULL
대형/고위험 프로젝트. 전체 Stage와 Knowledge Promotion 후보까지 사용한다.

Preset을 계속 늘리지 않는다. 프로젝트 규모 차이는 이 3개 Profile 안에서 해결한다.

## Advanced Setup — 필요한 경우에만 설정

### 1. 용어/고객 문서
- 고객사 업무용어가 중요한 경우
- 고객 문서 Section/필드가 다른 경우
- 내부/고객 문서 구성이 달라야 하는 경우

관련 Profile/Overlay:
- `sdlc/config/terminology-profile.example.json`
- `sdlc/config/customer-document-profile.example.json`
- `sdlc/custom/project/`

### 2. 비정형 업무문서
DOCX/PPTX/XLSX/TXT/MD/CSV는 다음 Runtime으로 Evidence Chunk를 만들 수 있다.

```bash
python sdlc/scripts/extract_document_evidence.py \
  --input <file> \
  --output sdlc/runtime/evidence/<name>.json
```

PDF는 text parser가 사용 가능할 때 추출하며, 읽을 수 없으면 `EXTRACTION_REQUIRED`로 닫는다. OCR이 필요한 PDF/IMAGE_SCAN은 외부 Tool/Adapter 책임이다. 추출된 문서는 `.cursor/skills/sop-extract/SKILL.md`에서 의미 Candidate로 분석한다.

### 3. 결정 권한
기본 Authority 역할이 실제 조직과 다를 때만 `open-resolution-profile`을 조정한다. 사용자에게 `Decision Domain`, `Basis Class`, 내부 Status code를 직접 작성시키지 않는다.

### 4. Brownfield Impact Adapter
Core는 공통 Graph/Coverage/Gap 규칙만 제공한다. Project Adapter는 Framework별 관계를 실제로 찾는다.

포함 Adapter:
- `java_spring_mybatis.py`: 좁고 안정적인 Pilot
- `java_spring_enterprise.py`: JPA/JDBC/@Transactional/Feign/Kafka/Scheduled/Config의 정적 후보까지 확장

두 Adapter 모두 Runtime proxy/reflection/live DB/APM/broker topology를 Business Truth처럼 확정하지 않는다. 지원하지 않는 영역은 Coverage Gap 또는 Tool Required다.

### 5. Project Overlay
신규 프로젝트 기본 Customization 개념은 다음 3개만 이해하면 된다.

`Core → Project Overlay → Local Override`

Domain/Preset 세분화는 기존 프로젝트 호환 또는 실제 공유 필요가 확인된 경우에만 사용한다.

## OPEN 처리
사람이 기본적으로 보는 값은 다음뿐이다.
- 무엇을 확인/결정해야 하는가
- 어떻게 확인할 것인가
- 현재 확인된 내용 또는 제안
- 누가 확인/결정하는가
- 진행 상태: `미확정 / 확인중 / 제안 / 확정 / 보류`

Machine taxonomy는 가능한 경우 Agent/Script가 내부 metadata로 관리한다.

## Validation

```bash
python sdlc/scripts/harness.py check --setup
python sdlc/scripts/validate_harness_structure.py .
python sdlc/scripts/validate_document_experience.py .
```

Provider가 준비된 뒤 첫 작업 계획:

```bash
python sdlc/scripts/harness.py work --target <RQ-ID> --plan-only
```

## 준비도 안내
- Starter Kit 최소값 충족은 `STARTABLE`이며 `IMPLEMENTATION_READY`가 아니다.
- OPEN 존재 자체는 실패가 아니다.
- Business Truth는 권한자의 확인 없이 확정하지 않는다.
- Brownfield Repository 기준점/Adapter Coverage가 부족하면 영향분석을 COMPLETE로 표시하지 않는다.
- Production Source write는 Git/Source Target/Build/Test/Canonical Guard를 통과해야 한다.
