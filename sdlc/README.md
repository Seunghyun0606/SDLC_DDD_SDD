# AI-SDLC Harness — 실행 안내

일반 프로젝트 참여자의 시작 문서는 이 파일이 아닙니다.

**처음 사용하는 경우 `docs/00_시작/START_HERE.md`에서 시작하세요.**

이 문서는 Harness 운영자에게 현재 실행 경계와 사용자 진입점을 짧게 설명합니다.

## 1. 사용자에게 보이는 기본 흐름

```text
프로젝트 자료 제공
→ setup
→ 현재 상태/부족한 정보 확인
→ 요구사항 또는 변경요청 Target 확보
→ Agent 초안
→ 사람이 확인할 판단만 결정
→ 다음 단계 진행
```

사용자에게 내부 Rule/Reference/Contract 구조를 먼저 읽게 하지 않습니다.

## 2. 실행 명령

```bash
python sdlc/scripts/harness.py setup --name <project-name> --mode AUTO --delivery STANDARD
python sdlc/scripts/harness.py check --setup
```

RQ Target이 이미 있다면:

```bash
python sdlc/scripts/harness.py check --target <RQ-ID>
python sdlc/scripts/harness.py work --target <RQ-ID> --plan-only
```

기존 요구사항 변경은:

```bash
python sdlc/scripts/harness.py change \
  --target <RQ-ID> \
  --change "변경 내용을 자연어로 입력"
```

## 3. 현재 구현 경계

### 실제 연결됨

- `setup`: 프로젝트 Mode/Delivery와 Repository 기술 신호 탐색
- `check`: setup 또는 Target 상태 확인
- `work`: Target이 있는 경우 Stage 계획/Agent 실행
- `change`: 기존 Target의 변경 등록
- Agent Provider가 없으면 실제 생성 성공으로 처리하지 않음
- Source 관찰만으로 Business Truth를 자동 확정하지 않음

### 아직 연결되지 않음

빈 프로젝트에서 요구사항 원문 한 건을 넣어 RQ ID를 만들고 바로 `work`로 넘기는 통합 intake는 아직 없습니다.

현재 XLSX importer:

```bash
python sdlc/scripts/import_requirements.py <requirements.xlsx>
```

는 원본을 보존하며 Requirement Candidate를 만들지만 Canonical RQ 등록과 첫 Target 반환까지 연결하지 않습니다. 이 단절은 WP-03에서 `harness.py intake`로 해결해야 합니다.

## 4. Project Mode

- `GREENFIELD`: 기존 Source가 없는 신규 구축
- `BROWNFIELD`: 기존 Source를 근거로 변경·고도화
- `HYBRID`: 기존/신규 영역 혼합
- `AUTO`: Source/build/schema 자산을 보고 후보 판단

Git Repository라는 사실만으로 Brownfield를 확정하지 않습니다.

## 5. Delivery

- `FAST`: 작은 운영 변경
- `STANDARD`: 일반 SI/SM 기능
- `FULL`: 대형·고위험 범위

사용자에게 Preset/Overlay 세부 종류를 선택하도록 요구하지 않습니다.

## 6. Agent와 사람의 역할

Agent가 먼저 해야 하는 일:

- 제공 문서와 Source에서 확인 가능한 사실 정리
- 근거가 있는 Section 초안 작성
- AS-IS/영향/설계/Test 후보 작성
- 불확실한 내용은 `확인 필요`로 분리
- 다음 행동 안내

사람이 확인하는 일:

- 업무정책
- 범위 포함/제외
- 우선순위
- 권한/승인
- 기술 선택 승인
- 위험 수용
- 인수/배포 판단

사용자에게 빈 Template의 수십 개 placeholder를 먼저 채우게 하는 방식은 목표 UX가 아닙니다.

## 7. Greenfield 시작

준비하면 좋은 자료:

- 요구사항/요청 원문
- SOP/업무 정책 자료가 있다면 원본
- 프로젝트 표준
- Architecture 결정사항
- Security/NFR 자료

Source가 없다는 것은 정상입니다. 확인되지 않은 업무정책은 Agent가 만들지 않습니다.

상세: `sdlc/starter-kits/greenfield/README.md`

## 8. Brownfield 시작

준비하면 좋은 자료:

- Repository/Source bundle
- 변경요청
- 기존 설계/운영자료
- DB/Interface/Event/Batch 자료
- Build/Test/배포 정보
- 필요한 경우 Log/APM 등 운영 근거

찾지 못한 영역을 `영향 없음`으로 간주하지 않고 Coverage Gap으로 남깁니다.

상세: `sdlc/starter-kits/brownfield/README.md`

## 9. Provider가 없을 때

setup 결과가 `CONFIGURED_PROVIDER_REQUIRED`여도 기본 설정 파일 생성 자체가 실패했다는 뜻은 아닙니다. 실제 초안 생성을 수행할 Agent Provider가 아직 연결되지 않았다는 의미입니다.

연결 방법은 `docs/00_시작/프로젝트_설정_가이드.md`를 확인합니다.

## 10. 문제 확인 순서

1. `python sdlc/scripts/harness.py check --setup`
2. `docs/00_시작/START_HERE.md`
3. `docs/00_시작/프로젝트_설정_가이드.md`
4. 그 다음에만 Harness 관리자용 구현/검증 자료를 확인

## 11. Production Ready 표현 기준

Runtime test나 fixture provider가 통과했다는 이유만으로 실제 프로젝트 사용성이 증명되었다고 표현하지 않습니다.

별도로 필요한 실증:

- 실제 외부 Agent 반복 실행
- 일반 분석가/설계자/개발자/QA의 첫 사용
- Business Truth 오승격 여부
- Evidence 조작/환각 여부
- 사용자가 설계자 도움 없이 다음 단계를 찾는지 여부
