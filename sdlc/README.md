# AI-SDLC Harness — Project Quick Start

이 문서는 **처음 Harness를 프로젝트 Repository에 도입하는 일반 SI/SM 참여자**를 위한 실행 기준이다. Contract/Profile 이름을 먼저 학습할 필요가 없다.

## 1. Production Project에 무엇을 가져가는가

### 최소 실행 Core
다음 범위가 기본 배포 대상이다.

- `.cursor/rules/**`
- `.cursor/skills/work`, `change`, `check`, `setup`
- `sdlc/scripts/harness.py`
- `sdlc/scripts/bootstrap_project.py`, `runtime_config.py`
- `sdlc/scripts/run_work.py`, `run_change.py`, `run_check.py`
- `sdlc/scripts/apply_canonical_delta.py`, `validate_agent_stage_result.py`, `validate_program_spec.py`
- `sdlc/templates/core/**`
- `sdlc/config/program-spec-readiness.json`
- 실행에 필요한 `sdlc/design/contracts/**` 공통 Contract

정확한 목록은 `sdlc/design/contracts/harness-package-contract.json`의 `core_required_files`가 기준이다.

### 필요할 때만 추가
- Brownfield Source 영향/Reverse: `deployment_sets.BROWNFIELD_EXTENSION`
- 고객 산출물: `deployment_sets.CUSTOMER_EXTENSION`
- DOCX/PPTX/XLSX/PDF 업무문서 ingestion: `deployment_sets.DOCUMENT_INGEST_EXTENSION`
- Jira/APM/DB/API Catalog 등 외부 결과: `deployment_sets.EXTERNAL_TOOL_EXTENSION`

### Production Project에 복사할 필요가 없는 것
- `tests/**`
- `sdlc/validation/**`
- `docs/99_파일럿/**`
- Validation report / Sample fixture

이들은 Harness 자체 검증용이며 프로젝트 수행 필수 파일이 아니다.

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

Setup Runtime이 실제 생성하는 파일:

```text
sdlc/config/project-profile.yaml
sdlc/config/source-profile.yaml
sdlc/config/agent-provider.json
sdlc/canonical/store.json
sdlc/runtime/setup/setup-result.json
```

Provider가 연결되지 않았으면 `CONFIGURED_PROVIDER_REQUIRED`로 끝난다. 이 상태를 작업 실행 성공으로 보지 않는다.

## 3. 설정 확인

```bash
python sdlc/scripts/harness.py check --setup
python sdlc/scripts/validate_harness_structure.py .
```

확인할 것:
- Greenfield/Brownfield Mode
- Delivery Profile
- Source root
- Build/Test command
- Agent Provider
- 현재 Git branch/dirty 상태

## 4. 작은 변경과 큰 프로젝트를 다르게 수행한다

### FAST
XS/S 운영 변경·소규모 기능.
- 불필요한 PROCESS/DISCOVERY/VERIFY는 조건부
- Program Spec 준비도는 7개 핵심 항목만 필수
- Customer 문서는 기본 최소
- Reverse는 직접 관련 범위 우선

### STANDARD
일반 SI/SM 기능.
- 업무흐름/영향/설계/Program/Test/Verify 사용
- Program Spec 17개 준비도 사용

### FULL
대형/고위험 구축.
- 전체 Stage + Knowledge Promotion 후보
- 조직별 Architecture/Governance는 Project Overlay로 추가

새 Preset을 계속 만들지 말고 기본적으로 이 3개만 사용한다.

## 5. 첫 요구사항 진행

Requirement가 Canonical에 등록된 뒤 실제 변경 전에 계획부터 확인한다.

```bash
python sdlc/scripts/harness.py work --target RQ-001 --plan-only
```

Provider가 준비됐으면:

```bash
python sdlc/scripts/harness.py work --target RQ-001
```

`/work`는 다음을 실제 Guard한다.
- Provider 미연결 실패
- 기본 `main/master` 직접 write 금지
- dirty workspace 기본 차단
- 실행 중 Git HEAD 변경 차단
- 허용 Source root 밖 Provider write 차단
- DEVELOPMENT build/test 실패 시 Canonical commit 금지
- 실패 시 이번 Provider 실행에서 생긴 Git working-tree 변경 rollback
- Canonical file lock + 최신 revision 재확인 + atomic replace

Hosting 서비스의 Branch Protection 자체는 프로젝트에서 별도로 켜야 한다.

## 6. 변경과 조회

```bash
python sdlc/scripts/harness.py change \
  --target RQ-001 \
  --change '환불 상태 조회를 추가한다'

python sdlc/scripts/harness.py check --target RQ-001
```

`/change`도 `/work`와 같은 Git/Canonical Guard를 사용한다. Source 관찰만으로 고객/업무 확정 내용을 바꾸지 않는다.

## 7. Greenfield 시작법

Source가 없는 것은 정상이다. 부족한 기술 선택은 Proposal/Open으로 진행할 수 있으며 업무 정책은 권한 확인 없이 확정하지 않는다.

권장 첫 Prompt:

> 이 Repository는 신규 Greenfield 프로젝트다. 현재 제공된 요구사항과 프로젝트 자료를 확인하고 개발 언어, Framework, DB, UI/API, Build/Test, Architecture/Coding/Naming/Test 정책 중 확정된 것과 미확정된 것을 구분해줘. Source가 없는 것은 정상으로 취급하고 기술 항목은 근거가 있으면 Proposal로 제안하되 고객/업무 정책은 임의 확정하지 마. 첫 요구사항의 FR/AC를 만들고 다음 설계까지 반드시 결정할 항목과 나중에 결정해도 되는 OPEN을 분리해줘.

## 8. Brownfield 시작법

먼저 실제 Evidence coverage를 조사한다. “찾지 못함”을 “영향 없음”으로 해석하지 않는다.

권장 첫 Prompt:

> 이 Repository는 Brownfield 프로젝트다. 변경 설계 전에 Source root, 모듈, Build/Test, Language/Framework, Controller/API, Service, Repository/Mapper, DB Schema, Batch/Scheduler, Interface/Event, Test, 배포구조, 기존 문서와 Git history를 조사해줘. 확인한 내용은 현행 근거로 기록하고 찾지 못한 항목은 Coverage Gap으로 남겨줘. 현재 Adapter가 분석 가능한 범위와 추가 Adapter/Tool이 필요한 범위를 구분한 뒤 Project/Source Profile 초안을 만들어줘. Source만 보고 Business 목적이나 정책을 확정하지 마.

포함 Adapter:
- `java_spring_mybatis.py`: 직접 호출/MyBatis/Table 중심 Pilot
- `java_spring_enterprise.py`: JPA/JDBC/@Transactional/Feign/Kafka/Scheduled/Config 정적 후보 확장

두 Adapter 모두 Runtime proxy/reflection/live DB/APM/broker topology는 완전 분석하지 않는다.

## 9. 기존 DOCX/PPTX/XLSX/PDF 업무문서

원본을 다시 작성시키지 않는다.

```bash
python sdlc/scripts/extract_document_evidence.py \
  --input <customer-file> \
  --output sdlc/runtime/evidence/<name>.json
```

- DOCX/PPTX/XLSX는 OOXML 구조를 사용해 paragraph/slide/cell range를 보존한다.
- PDF는 text parser가 사용 가능할 때만 추출한다.
- 읽을 수 없으면 `EXTRACTION_REQUIRED`; 규칙이 없다고 판단하지 않는다.
- OCR/스캔은 외부 Document Tool이 필요하다.

## 10. 고객 문서

Active Customer View는 A01/A02/A03 세 종류만 기본 사용한다.

고객 피드백/승인을 다시 근거로 연결할 때:

```bash
python sdlc/scripts/capture_customer_decision.py --input <customer-decision.json>
```

승인 결과를 기록하는 것과 Business Truth 필드를 변경하는 것은 별개다. 실제 업무 필드 변경에는 명시적 `--apply-business-change`가 필요하다.

## 11. 외부 Tool/MCP

새 Tool마다 새 Stage/Contract를 만들지 않는다. Tool 결과를 JSON으로 받은 후 공통 Evidence로 정규화한다.

```bash
python sdlc/scripts/normalize_external_evidence.py \
  --input <provider-result.json> \
  --provider <JIRA|SONAR|DATADOG|DB_CATALOG|API_CATALOG|...> \
  --output <evidence.json>
```

공통 경계:

`External Provider → Evidence Chunk → Stage/Canonical Context`

## 12. 사용자에게 보이는 문서

한국어 자연어가 기본이다.
- 근거 위치
- 원본 식별값
- 확인 수준
- 현재 상태
- 제안
- 미확정
- 현행 확인

`Locator / Source Hash / Confidence` 같은 Machine 이름은 frontmatter/comment 또는 내부 metadata로 유지한다.

## 13. Customization

기본 사용자가 이해할 계층은 세 개만 둔다.

`Core → Project Overlay → Local Override`

Domain/Preset Overlay는 실제 공유 필요나 기존 호환성이 있을 때만 사용한다.

## 14. 현재 검증 한계

이 Branch의 Runtime/Behavioral Test가 통과하더라도 다음은 별도 실증이 필요하다.
- 실제 외부 Agent Provider 품질
- 저수준 Agent 반복 수행 품질
- 일반 분석가/개발자의 첫 사용성
- 실제 고객 합의 품질
- 프로젝트 GitHub/GitLab Branch Protection 정책

Fixture Provider 성공은 실제 Agent 성공으로 간주하지 않는다.
