# START HERE — 프로젝트 첫 사용 안내

이 문서는 AI-SDLC Harness를 처음 사용하는 분석가·설계자·개발자·QA를 위한 시작점입니다.

## 1. 프로젝트 종류를 선택한다

모르면 `AUTO`로 시작합니다.

- `GREENFIELD`: 기존 Source 없이 신규 시스템/기능을 설계
- `BROWNFIELD`: 기존 Source/DB/Batch/API 등의 영향 분석이 중요
- `HYBRID`: 기존 영역과 신규 영역이 함께 존재
- `AUTO`: Repository Evidence로 Runtime이 우선 판정

## 2. 처음 준비할 자료

최소한 다음 중 실제로 있는 자료만 제공합니다.

- 요구사항 XLSX 또는 변경요청 원문
- 고객 문서/SOP/업무 매뉴얼
- 기존 Repository 또는 Source 위치
- Build/Test 방법
- 이미 결정된 기술/보안/운영 기준

없는 자료를 새로 만들어서 시작할 필요는 없습니다. 알 수 없는 정보는 OPEN으로 남깁니다.

## 3. 최초 실행

```bash
python sdlc/scripts/harness.py setup \
  --name <project-name> \
  --mode AUTO \
  --delivery STANDARD

python sdlc/scripts/harness.py check --setup
```

사용자가 직접 유지하는 기본 설정은 `.sdlc/project.yaml` 하나입니다. 내부 Profile/Contract/Starter Manifest를 먼저 작성하지 않습니다.

## 4. 요구사항 또는 변경요청을 등록한다

표준 2행 Header XLSX라면 다음 명령으로 바로 인입합니다.

```bash
python sdlc/scripts/harness.py intake 요구사항목록.xlsx
```

Runtime은 원본 행·Sheet·외부 요구사항 ID·Source Hash를 보존하고 RQ/FR Candidate를 Canonical에 등록합니다. 유사 제목은 자동 병합하지 않습니다.

결과에는 실제 Target과 다음 명령이 포함됩니다.

```text
first_target: RQ-001
next_command: python sdlc/scripts/harness.py work --target RQ-001
```

비표준 고객 Column 명칭만 선택적으로 `--profile`을 사용합니다.

## 5. Agent가 자동으로 해야 하는 일

- Repository/문서에서 확인 가능한 사실을 먼저 탐색
- 요구 원문을 훼손하지 않고 구조화
- RQ/FR/AC/설계 초안 작성
- 근거가 없는 업무 사실은 OPEN 유지
- Source Evidence와 Business Truth를 구분
- 다음 단계와 필요한 확인 항목 안내

## 6. 사람이 반드시 확인하는 일

- 유사 요구사항의 실제 병합 여부
- 중복 외부 ID의 기준 원문
- 업무정책·범위·승인·권한
- 실제 프로젝트 기술 선택
- Source/문서로 끝내 확인되지 않는 OPEN

사람이 빈 Requirement Template을 처음부터 작성하는 것은 기본 절차가 아닙니다.

## 7. 실제 작업 진행

```bash
python sdlc/scripts/harness.py work --target RQ-001 --plan-only
```

계획을 확인한 뒤 Provider가 연결되어 있으면 실제 작업을 실행합니다.

```bash
python sdlc/scripts/harness.py work --target RQ-001
```

RQ는 기존 Work Runtime의 `DECOMPOSE` 단계로 연결됩니다.

## 8. Greenfield / Brownfield 자료 안내

- Greenfield: `sdlc/starter-kits/greenfield/README.md`
- Brownfield: `sdlc/starter-kits/brownfield/README.md`

Greenfield는 Source가 없어도 정상입니다. Brownfield는 찾지 못한 영역을 `영향 없음`으로 해석하지 않고 Coverage Gap으로 남깁니다.

## 9. 문제가 생겼을 때 어디를 볼까

- setup 상태: `python sdlc/scripts/harness.py check --setup`
- 요구사항 인입 결과: `docs/00_관리/요구사항_인입결과.md`
- Machine intake 상세: `sdlc/runtime/intake/requirements-import.json`
- 설정 상세: `docs/00_시작/프로젝트_설정_가이드.md`

실제 외부 Agent 품질과 일반 사용자 First-use usability는 Python/fixture 테스트만으로 증명되지 않습니다.
