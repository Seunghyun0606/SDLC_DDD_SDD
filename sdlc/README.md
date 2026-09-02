# AI-SDLC Harness — Project Quick Start

이 문서는 Harness 설계 내부를 모르는 일반 SI/SM 참여자가 **프로젝트 자료를 제공하고 첫 요구사항 작업까지 연결**하기 위한 실행 기준이다. Rule/Skill/Reference/Contract 구조를 먼저 학습할 필요가 없다.

## 1. 기본 사용자 흐름

```text
프로젝트 자료 제공
  → Intake가 근거/후보와 실제 RQ Target 생성
  → Agent가 Requirement 초안 작성
  → 사람은 정책·범위·승인 등 판단 항목만 확인
  → Agent가 문서 완성
  → 다음 Stage 안내
```

사람이 빈 `requirement.md` Template의 placeholder를 직접 채우는 방식은 기본 Workflow가 아니다.

## 2. 최초 설정

```bash
python sdlc/scripts/harness.py setup \
  --name <project-name> \
  --mode AUTO \
  --delivery STANDARD
```

실제 Agent wrapper가 있으면 `--provider-command`를 추가한다. Provider가 없으면 문서 생성 성공으로 취급하지 않지만, Requirement Intake와 계획 확인은 진행할 수 있다.

설정 확인:

```bash
python sdlc/scripts/harness.py check --setup
```

## 3. 요구사항 자료를 그대로 인입한다

표준 한국어 2행 Header XLSX는 별도 Mapping/Profile 없이 바로 실행한다.

```bash
python sdlc/scripts/harness.py intake 요구사항목록.xlsx
```

기본 Header는 `Level1 / Level2 / 요구사항 ID / 요구사항명 / 요구사항`이다. 고객 파일의 컬럼명이 다를 때만 `--profile`을 사용한다.

Intake는 다음을 수행한다.

- 원문, 외부 요구사항 ID, Sheet/Row, Source Hash 보존
- 동일한 업무영역/요구사항명 묶음을 RQ **후보**로 등록
- 각 원본 요구 행을 FR **후보**로 등록
- 유사 그룹은 자동 병합하지 않고 사람 확인 대상으로 남김
- 현재 문제·기대 결과·업무 규칙을 근거 없이 만들지 않고 OPEN 유지
- 기존 `CONFIRMED_BUSINESS`를 재인입 Source로 덮어쓰거나 낮추지 않음
- 실제 `RQ-001` 같은 다음 작업 Target을 반환

기본 출력은 역할을 분리한다.

```text
사용자 확인 문서   docs/00_관리/요구사항_인입결과.md
Machine Artifact  sdlc/runtime/intake/requirements-import.json
Canonical Store   sdlc/canonical/store.json
```

Machine JSON은 사용자가 직접 작성하거나 편집하는 문서가 아니다.

파싱 결과만 보고 Canonical을 변경하지 않으려면 진단용으로 `--candidate-only`를 사용한다.

## 4. Agent 초안으로 이어간다

Intake가 반환한 실제 Target을 그대로 사용한다.

```bash
python sdlc/scripts/harness.py work --target RQ-001
```

Provider가 아직 연결되지 않았다면:

```bash
python sdlc/scripts/harness.py work --target RQ-001 --plan-only
```

Canonical RQ는 기본적으로 DECOMPOSE로 연결되고, 관련 FR 후보도 Agent Context에 포함된다. Agent는 `sdlc/templates/core/requirement.md` 형식의 초안을 만들되, 업무 정책·범위·승인·기술 선택처럼 권한이나 추가 근거가 필요한 값은 OPEN/Proposal로 남긴다.

완성된 Intake 예시는 `sdlc/guides/요구사항_인입_완성예시.md`를 본다. 예시는 작성용 빈 양식이 아니다.

## 5. 사람이 확인하는 범위

사람에게 우선 노출할 것은 다음과 같다.

- 유사 RQ를 실제로 합칠지
- 중복 외부 ID의 기준 원문
- 업무 정책과 적용 범위
- 승인/권한이 필요한 결정
- Source로 확인할 수 없는 기대 결과
- 기술 선택 중 프로젝트 의사결정이 필요한 항목

나머지 근거 정리, ID 연결, 문서 초안, 추적성 표는 Agent/Runtime이 먼저 만든다.

## 6. Delivery Profile

- `FAST`: XS/S 운영 변경·소규모 기능
- `STANDARD`: 일반 SI/SM 기능
- `FULL`: 대형/고위험 구축

Preset을 계속 늘리지 않고 이 세 Profile을 기본으로 사용한다.

## 7. Brownfield와 비정형 자료

Brownfield에서는 Source/build/schema 자산을 Evidence로 조사하되, 찾지 못한 것을 영향 없음으로 확정하지 않는다. 기존 DOCX/PPTX/XLSX/PDF 업무문서의 일반 Evidence 추출은 `extract_document_evidence.py` 경로를 사용한다. 이번 `harness intake`의 Core 입력은 **구조화된 요구사항 XLSX**이며, 모든 문서 포맷을 하나의 새 Framework로 다시 만들지 않는다.

## 8. 변경과 조회

```bash
python sdlc/scripts/harness.py change --target RQ-001 --change '변경 내용'
python sdlc/scripts/harness.py check --target RQ-001
```

`/work`와 `/change`는 Provider/Git/Source Scope/Build/Test/Canonical Guard를 사용한다. Source 관찰만으로 고객/업무 확정 내용을 바꾸지 않는다.

## 9. 배포 구조

Minimum executable core의 실제 파일 목록은 `sdlc/design/contracts/harness-package-contract.json`이 기준이다. `harness.py intake`가 공식 첫 요구사항 경로이므로 `import_requirements.py`도 Core에 포함된다.

추가 기능은 필요할 때만 Extension으로 사용한다.

- Brownfield Source 영향/Reverse
- 고객 산출물 Projection
- 일반 Document Ingestion
- Jira/APM/DB/API Catalog 등 외부 Tool Evidence

Validation/Test/Sample은 Production Project 배포 필수가 아니다.

## 10. Customization

기본 사용자가 이해할 계층은 다음 세 개면 충분하다.

`Core → Project Overlay → Local Override`

Domain/Preset Overlay는 실제 공유 필요나 기존 호환성이 있을 때만 사용한다.

## 11. 현재 검증 한계

Runtime/Behavioral Test가 성공해도 다음은 별도 실증 대상이다.

- 실제 외부 저수준 Agent가 Source Evidence에서 안정적으로 Requirement 초안을 만드는지
- 일반 분석가/설계자/개발자/QA가 설명 없이 `setup → intake → work`를 수행하는지
- 사람이 확인해야 할 항목 수와 불필요한 질문 비율이 실제 프로젝트에서 충분히 낮은지
- 실제 고객 합의가 Candidate/OPEN에서 CONFIRMED로 안전하게 전환되는지

Fixture나 Script 성공을 실제 Agent/Human 사용성 증거로 간주하지 않는다.
