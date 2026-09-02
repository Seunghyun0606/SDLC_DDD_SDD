# AI-SDLC Harness — Project Quick Start

처음 Harness를 프로젝트에 도입하는 일반 SI/SM 참여자는 `docs/00_시작/START_HERE.md`에서 시작한다. Contract/Profile/Starter Manifest 구조를 먼저 학습할 필요가 없다.

## 원하는 사용자 흐름

```text
프로젝트 자료 제공
→ setup
→ Agent/Runtime이 확인 가능한 설정과 근거를 먼저 구성
→ intake로 요구사항 원본을 RQ/FR Candidate로 등록
→ 사람이 판단해야 할 항목만 확인
→ 실제 RQ Target으로 work 진행
→ 다음 단계 자동 안내
```

사람이 빈 Template이나 여러 Config 파일을 먼저 채우는 것을 기본 절차로 만들지 않는다.

## 1. 프로젝트 설정은 하나

새 프로젝트에서 사람이 직접 유지하는 설정 Source of Truth는 다음 하나다.

```text
.sdlc/project.yaml
```

첫 실행:

```bash
python sdlc/scripts/harness.py setup \
  --name <project-name> \
  --mode AUTO \
  --delivery STANDARD

python sdlc/scripts/harness.py check --setup
```

`setup`은 Repository에서 Source root, Build/Test, Language/Framework/DB 신호를 먼저 탐색한다. 확인할 수 없는 것은 `unresolved`로 남긴다.

Machine artifact는 Runtime이 계산한다.

```text
.sdlc/runtime/effective/project-profile.json
.sdlc/runtime/effective/source-profile.json
.sdlc/runtime/effective/agent-provider.json
.sdlc/runtime/effective/project-context.json
.sdlc/runtime/effective/config-usage.json
```

기존 `sdlc/config/project-profile.yaml`, `source-profile.yaml`은 Legacy compatibility snapshot이며 새 프로젝트의 사용자 설정 Source of Truth가 아니다.

## 2. 요구사항 원본을 바로 인입

표준 2행 Header XLSX는 별도 Column Profile 없이 인입할 수 있다.

```bash
python sdlc/scripts/harness.py intake 요구사항목록.xlsx
```

기본 결과:

- Machine artifact: `sdlc/runtime/intake/requirements-import.json`
- Human report: `docs/00_관리/요구사항_인입결과.md`
- Canonical store: `sdlc/canonical/store.json`
- 실제 작업 Target: `RQ-001` 같은 RQ ID

Source row, Sheet, 외부 요구사항 ID, Source Hash는 근거로 보존한다. 유사 제목은 자동 병합하지 않고 Review 대상으로 남긴다. 업무 사실은 `CANDIDATE` 또는 OPEN이며 자동으로 `CONFIRMED_BUSINESS`가 되지 않는다.

비표준 고객 Column 명칭만 `--profile`을 선택적으로 사용한다.

## 3. 반환된 Target으로 작업

먼저 계획을 확인한다.

```bash
python sdlc/scripts/harness.py work --target RQ-001 --plan-only
```

실제 Provider가 준비되어 있으면:

```bash
python sdlc/scripts/harness.py work --target RQ-001
```

RQ는 기존 Work Runtime에서 `DECOMPOSE`로 연결되며 관련 FR Candidate도 Canonical graph를 통해 Context에 포함된다.

## 4. 사람과 Agent의 역할

Agent/Runtime이 먼저 할 일:

- Repository/문서에서 확인 가능한 기술 사실 탐색
- 요구사항 원본과 Provenance 보존
- RQ/FR/AC/설계 초안 작성
- 불확실한 사실은 OPEN 유지
- 다음 작업 명령 안내

사람이 확인할 일:

- 유사 요구사항 실제 병합 여부
- 중복 외부 ID의 기준 원문
- 업무정책·범위·승인·권한
- 프로젝트 기술 선택
- 실제 의사결정권한이 필요한 OPEN

## 5. Greenfield / Brownfield

Greenfield는 Source가 없어도 시작할 수 있다. 기술 상세가 없으면 업무 사실처럼 발명하지 않는다.

Brownfield는 먼저 실제 Evidence coverage를 확인한다. 찾지 못한 영역을 영향 없음으로 해석하지 않는다. Source root, API/Controller, Service, Mapper/Repository, DB, Batch, Interface/Event, Test/Build coverage gap을 명시한다.

시작 자료:

- `sdlc/starter-kits/greenfield/`
- `sdlc/starter-kits/brownfield/`

## 6. FAST / STANDARD / FULL

- `FAST`: 소규모 운영 변경/기능
- `STANDARD`: 일반 SI/SM 기능
- `FULL`: 대형·고위험 범위

새 Preset을 계속 추가하지 않고 세 Delivery Profile을 Runtime 정책으로 사용한다.

## 7. 기존 업무문서

DOCX/PPTX/XLSX 등 기존 자료는 원본을 다시 작성시키지 않고 Evidence로 추출한다.

```bash
python sdlc/scripts/extract_document_evidence.py \
  --input <customer-file> \
  --output sdlc/runtime/evidence/<name>.json
```

읽지 못한 영역은 Coverage Gap으로 남긴다.

## 8. 변경과 조회

```bash
python sdlc/scripts/harness.py change \
  --target RQ-001 \
  --change '환불 상태 조회를 추가한다'

python sdlc/scripts/harness.py check --target RQ-001
```

`work/change`는 `.sdlc/project.yaml`에서 계산된 Project Context와 Git/Source/Canonical Guard를 사용한다.

## 9. Validation

```bash
python -m unittest tests.test_project_entry_config tests.test_requirement_intake_runtime -v
python sdlc/scripts/validate_harness_structure.py .
python sdlc/scripts/validate_document_experience.py .
```

Behavioral Test는 Runtime 연결을 확인한다. 실제 외부 저수준 Agent의 문맥 이해력이나 일반 분석가·개발자·QA의 First-use usability는 별도 실증 대상이며, fixture/test 성공만으로 Production Ready라고 판정하지 않는다.
