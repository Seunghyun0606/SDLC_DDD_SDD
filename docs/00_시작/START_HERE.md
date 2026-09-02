# START HERE — 프로젝트 첫 사용 안내

이 문서는 AI-SDLC Harness를 처음 사용하는 분석가·설계자·개발자·QA를 위한 시작점입니다.

Harness의 기본 사용 경험은 다음 한 줄입니다.

> **프로젝트 자료 제공 → Agent 초안 → 사람이 확인해야 할 항목만 결정 → Agent 문서 완성 → 다음 단계 자동 안내**

사용자가 Rule, Skill, Reference, Contract를 먼저 공부하거나 빈 Stage Template을 직접 작성하는 것은 기본 절차가 아닙니다.

## 1. 프로젝트 종류를 선택한다

모르면 `AUTO`로 시작합니다.

- `GREENFIELD`: 기존 Source 없이 신규 시스템/기능을 설계
- `BROWNFIELD`: 기존 Source/DB/Batch/API 등의 영향 분석이 중요
- `HYBRID`: 기존 영역과 신규 영역이 함께 존재
- `AUTO`: Repository Evidence로 Runtime이 우선 판정

## 2. 실제로 있는 자료만 준비한다

다음 중 프로젝트에 존재하는 자료만 제공합니다.

- 요구사항 XLSX 또는 변경요청 원문
- 고객 문서/SOP/업무 매뉴얼
- 기존 Repository 또는 Source 위치
- Build/Test 방법
- 이미 결정된 기술/보안/운영 기준

없는 자료를 새로 만들어서 시작하지 않습니다. 확인되지 않은 내용은 Agent가 발명하지 않고 `OPEN`으로 남깁니다.

## 3. 최초 실행

```bash
python sdlc/scripts/harness.py setup \
  --name <project-name> \
  --mode AUTO \
  --delivery STANDARD

python sdlc/scripts/harness.py check --setup
```

사용자가 직접 유지하는 기본 설정은 `.sdlc/project.yaml` 하나입니다. 내부 Profile/Contract/Starter Manifest를 먼저 작성하지 않습니다.

## 4. 요구사항을 그대로 인입한다

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

## 5. Agent에게 초안을 맡긴다

먼저 계획만 보고 싶다면:

```bash
python sdlc/scripts/harness.py work --target RQ-001 --plan-only
```

실제 작업:

```bash
python sdlc/scripts/harness.py work --target RQ-001
```

기본적으로 새 사용자 문서는 `docs/10_산출물/` 아래에 생성됩니다. 예:

```text
docs/10_산출물/RQ-001_<요구사항명>_요구사항정의.md
```

이 문서는 **사용자가 빈 Template을 채우는 파일이 아닙니다.** Agent가 Requirement 원문, Canonical, 프로젝트 자료와 Source Evidence로 작성합니다.

Agent는 다음을 먼저 수행합니다.

- 원문과 외부 ID 보존
- Evidence로 확인 가능한 내용 조사
- RQ/FR/AC/설계·테스트 내용 초안
- 근거가 없는 업무 사실은 OPEN 유지
- Source 관찰과 Business Truth 분리
- 다음 작업 후보 계산

## 6. 사람에게는 판단권한이 필요한 항목만 보낸다

`work` 결과의 `user_handoff.review_items`에 항목이 있을 때만 사람이 확인합니다.

사람 검토 대상으로 허용되는 범주는 다음과 같습니다.

- 업무 정책(`BUSINESS_POLICY`)
- 범위 결정(`SCOPE`)
- 승인/권한(`APPROVAL`)
- 프로젝트 기술 선택(`TECHNICAL_CHOICE`)
- 인수/합의(`ACCEPTANCE`)

Source를 더 찾으면 확인할 수 있는 내용, 코드 분석으로 확인 가능한 내용, Agent가 추가 조사해야 하는 내용은 기본적으로 사람에게 떠넘기지 않고 `agent_open_items`로 남깁니다.

### 사람이 결정을 알려주는 방법

검토 문서를 그대로 승인:

```bash
python sdlc/scripts/harness.py review --target RQ-001 --by 홍길동 --approve
```

업무정책·범위·승인·기술 선택 등에 답변:

```bash
python sdlc/scripts/harness.py review \
  --target RQ-001 \
  --by 홍길동 \
  --answer "승인 주체는 팀장으로 한다"
```

수정 요청:

```bash
python sdlc/scripts/harness.py review \
  --target RQ-001 \
  --by 홍길동 \
  --request-change "해외 법인은 이번 범위에서 제외한다"
```

사용자가 Decision JSON을 직접 만들 필요는 없습니다. Review 결과는 근거로 기록되지만, 이 명령 자체가 Business Truth 필드를 조용히 자동 변경하지 않습니다.

## 7. 다음 단계는 결과가 안내한다

`work` 또는 `review` 결과의 `next_command`를 사용합니다.

- 사람 확인이 필요 없으면 다음 `work`
- 사람 답변이 기록되면 다시 `work`하여 문서 반영
- 변경 요청이면 `/change`

따라서 사용자가 Stage 이름이나 내부 Contract 구조를 외워서 다음 단계를 결정하지 않습니다.

## 8. 사용자 문서와 Machine Runtime은 구분한다

사람이 읽고 협의하는 문서:

```text
docs/00_관리/
docs/10_산출물/
```

Machine 검증·추적용 Artifact:

```text
sdlc/runtime/intake/
sdlc/runtime/work-runs/
sdlc/runtime/work-handoff/
sdlc/runtime/customer-decisions/
sdlc/canonical/
```

Machine JSON을 일반 프로젝트 참여자가 직접 편집하는 것은 기본 Workflow가 아닙니다.

## 9. Greenfield / Brownfield 자료 안내

- Greenfield: `sdlc/starter-kits/greenfield/README.md`
- Brownfield: `sdlc/starter-kits/brownfield/README.md`

Greenfield는 Source가 없어도 정상입니다. Brownfield는 찾지 못한 영역을 `영향 없음`으로 해석하지 않고 Coverage Gap으로 남깁니다.

## 10. 문제가 생겼을 때

- setup 상태: `python sdlc/scripts/harness.py check --setup`
- 요구사항 인입 결과: `docs/00_관리/요구사항_인입결과.md`
- 현재 사용자 산출물: `docs/10_산출물/`
- Machine intake 상세: `sdlc/runtime/intake/requirements-import.json`
- 최근 Work handoff: `sdlc/runtime/work-handoff/`
- 설정 상세: `docs/00_시작/프로젝트_설정_가이드.md`

## 검증 경계

Python/fixture Behavioral Test가 통과하더라도 실제 외부 저수준 Agent의 의미 품질과 일반 분석가·설계자·개발자·QA의 First-use usability가 증명되는 것은 아닙니다. 이 두 항목은 별도 실증 대상으로 남깁니다.
