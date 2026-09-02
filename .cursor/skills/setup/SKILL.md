# /setup

프로젝트 최초 도입용 Setup Instruction이다. 실제 실행 Runtime은 `sdlc/scripts/bootstrap_project.py`이고 사용자 CLI 진입점은 `sdlc/scripts/harness.py setup`이다.

## 목표

신규 프로젝트 참여자가 Framework 내부 Config/Profile/Contract를 이해하지 않고도 시작하게 한다.

사용자에게 보여줄 기본 흐름은 다음뿐이다.

```text
프로젝트명/유형/진행수준 선택
→ setup
→ 자동 탐색 결과와 확인 필요 사항 확인
→ 자료 제공
→ Agent 실행 준비
```

사용자 문서의 첫 진입점은 `docs/00_시작/START_HERE.md`다.

## 사용자에게 필요한 기본 입력

기본 setup에서는 다음 세 가지를 우선 사용한다.

1. 프로젝트명
2. 프로젝트 유형: `GREENFIELD / BROWNFIELD / HYBRID / AUTO`
3. 진행 수준: `FAST / STANDARD / FULL`

잘 모르는 프로젝트 유형은 `AUTO`, 일반 SI/SM 진행수준은 `STANDARD`를 기본으로 안내한다.

Source root, Build/Test, Framework, DB 등은 Repository에서 먼저 자동 탐색한다. 탐색할 수 없는 값만 `확인 필요`로 남긴다.

고객 문서 수준, Provider 연결, 특수 Adapter 같은 값은 실제 필요가 생겼을 때만 추가로 확인한다.

## 최초 실행

```bash
python sdlc/scripts/harness.py setup \
  --name <project-name> \
  --mode AUTO \
  --delivery STANDARD
```

상태 확인:

```bash
python sdlc/scripts/harness.py check --setup
```

실제 Agent Provider command가 준비되어 있으면 setup에 연결할 수 있다.

```bash
python sdlc/scripts/harness.py setup \
  --name <project-name> \
  --mode AUTO \
  --delivery STANDARD \
  --provider-command '<agent-command> --context {context_path} --result {result_path}'
```

## Agent 실행 순서

1. 사용자가 지정한 프로젝트 유형과 진행수준을 읽는다.
2. `AUTO`이면 Source/build/schema 자산으로 Mode 후보를 판단한다.
3. 일반적인 Source/Test/Resource root와 Build/Test command 후보를 탐색한다.
4. 확인된 기술 신호와 확인하지 못한 항목을 분리한다.
5. 실제 Runtime Config를 생성한다.
6. 생성 Config를 다시 읽어 round-trip 검증한다.
7. 구조 Validator가 있으면 실행한다.
8. Provider 준비 여부와 OPEN을 setup 결과에 기록한다.
9. 사용자에게 `docs/00_시작/START_HERE.md`와 다음 행동을 안내한다.

Git Repository라는 사실만으로 Brownfield라고 판정하지 않는다.

## 사용자가 준비하는 자료

### Greenfield

- 요구사항/요청 원문
- SOP/업무정책 자료가 있으면 원본
- 프로젝트 표준
- Architecture 결정사항
- Security/NFR 자료

### Brownfield

- Repository/Source bundle
- 변경 요청
- 기존 설계/운영자료
- DB/Interface/Event/Batch 자료
- Build/Test/배포 자료
- 필요한 경우 Log/APM 등 운영 근거

자료가 없으면 Agent가 내용을 발명하지 않고 `확인 필요` 또는 Coverage Gap으로 남긴다.

## 사람이 확인할 내용

사람에게 묻는 것은 판단권한이 필요한 항목으로 제한한다.

- 프로젝트 범위
- 업무정책
- 고객 공유 수준
- 기술/Architecture 선택 승인
- Security/운영 제약
- Source write 허용 범위
- 분석 제외 범위

Source root나 build file처럼 자동 탐색할 수 있는 사실을 사용자에게 먼저 작성시키지 않는다.

## Runtime 내부 동작

이 Section은 Agent/Harness 관리자용이다. 일반 사용자에게 setup 선행 지식으로 요구하지 않는다.

현재 Runtime은 호환성을 위해 다음 파일을 생성/사용한다.

- `sdlc/config/project-profile.yaml`
- `sdlc/config/source-profile.yaml`
- `sdlc/config/agent-provider.json`
- `sdlc/canonical/store.json`
- `sdlc/runtime/setup/setup-result.json`

이 다중 Config를 사용자 설정 하나로 통합하는 작업은 WP-02 범위다. 이번 WP-01에서는 사용자가 이 파일들을 직접 편집해야 한다고 안내하지 않는다.

## Mode별 처리

- `GREENFIELD`: Source가 없어도 정상 시작 가능
- `BROWNFIELD`: Repository/Source Evidence 기준으로 현재 동작과 Coverage를 확인
- `HYBRID`: 기존 Source와 신규 영역을 함께 취급
- `AUTO`: 실제 자산으로 후보를 결정

Source root/build/test를 찾지 못하면 `없음`이나 `영향 없음`으로 확정하지 않는다.

## Delivery Profile

- `FAST`: 작은 운영 변경
- `STANDARD`: 일반 SI/SM 기능
- `FULL`: 대형/고위험 범위

Preset 종류를 사용자 선택지로 늘리지 않는다.

## Provider 처리

Provider가 연결되지 않았으면 실제 문서 생성이 가능한 상태라고 과장하지 않는다.

- 기본 Config 생성 가능
- setup 상태는 `CONFIGURED_PROVIDER_REQUIRED`가 될 수 있음
- 실제 Agent generation은 Provider 준비 후 진행

공식 Reference Provider 제공은 WP-09 범위다.

## OPEN 처리

사용자에게는 가능한 한 다음 다섯 가지 정보만 보여준다.

- 무엇을 확인해야 하는가
- 현재 Agent가 확인한 내용
- 왜 확인이 필요한가
- 누가 결정해야 하는가
- 다음 행동

내부 Machine taxonomy를 사용자 입력 양식으로 요구하지 않는다.

## Zero-to-One Requirement 현재 경계

현재 `harness.py`에는 통합 `intake` 명령이 없다.

`import_requirements.py`는 XLSX Requirement Candidate를 만들 수 있지만 Canonical RQ 등록과 첫 Target 반환까지 자동 연결하지 않는다.

따라서 setup 결과에서 존재하지 않는 `<RQ-ID>`로 곧바로 `work`하라고 성공 경로처럼 안내하지 않는다. 기존 RQ가 있을 때만 `work --target <RQ-ID>`를 안내한다.

신규 요구 한 건 → RQ 생성 → 첫 work 연결은 WP-03 범위다.

## 절대 하지 말 것

- 사용자에게 Rule/Skill/Reference/Contract 위치를 찾아 읽으라고 요구
- 사용자에게 내부 Profile/Overlay 종류를 먼저 선택하게 함
- Source 관찰을 Business Truth로 자동 승격
- 발견하지 못한 Source/DB/Interface를 `영향 없음`으로 처리
- Provider가 없는데 Agent 실행 준비 완료라고 표현
- 빈 프로젝트에 RQ가 없는데 `work --target <RQ-ID>`를 바로 다음 성공 단계로 표시
- setup을 이유로 사용자에게 빈 산출물 Template을 직접 작성하게 함

## Quality Check

setup 완료 시 확인한다.

- project mode가 의도와 맞는가
- delivery profile이 실제 Runtime에 반영되는가
- auto-detect 결과와 OPEN이 구분되는가
- Provider 준비 여부가 사실대로 표시되는가
- 사용자 안내가 `docs/00_시작/START_HERE.md`로 연결되는가
- 내부 Config 구조를 사용자가 알아야만 다음 행동을 찾는 상태가 아닌가

## 다음 단계

1. `python sdlc/scripts/harness.py check --setup`
2. 사용자에게 `docs/00_시작/START_HERE.md`의 다음 행동을 안내
3. 기존 RQ가 있으면 `work --plan-only`
4. 첫 RQ가 없으면 WP-03 intake Gap을 명확히 알리고 내부 저장소 수동 편집을 유도하지 않음
