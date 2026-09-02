# SDLC Harness 시작하기

이 문서는 Harness를 처음 사용하는 분석가·설계자·개발자·QA를 위한 **첫 진입점**입니다.

Framework의 Rule, Skill, Reference, Contract, Canonical 구조를 먼저 공부할 필요가 없습니다. 처음에는 아래 순서만 따르면 됩니다.

```text
프로젝트 자료 준비
→ setup 실행
→ Harness가 현재 프로젝트 상태와 부족한 정보를 정리
→ 요구사항/변경요청 등록
→ Agent 초안 생성
→ 사람이 확인이 필요한 판단만 결정
→ 다음 작업 진행
```

> 현재 구현 경계: 이 Branch에는 `setup/work/change/check`가 연결되어 있지만, **빈 프로젝트에서 요구사항 한 건을 입력해 RQ ID를 만들고 바로 `work`로 넘기는 단일 intake 명령은 아직 없습니다.** XLSX 요구사항 후보 추출 Runtime은 존재하지만 Canonical RQ 등록과 첫 Target 반환까지 자동 연결되지는 않습니다. 이 연결은 Session 3 / WP-03 범위입니다. 따라서 아래에서는 가능한 흐름과 아직 끊긴 지점을 명확히 구분합니다.

## 1. 이 Harness로 무엇을 할 수 있나

사용자는 프로젝트 자료와 요구사항 또는 변경요청을 제공합니다. Harness와 Agent는 가능한 근거를 먼저 읽고 다음 산출물의 초안을 만듭니다.

- 요구사항 정리와 기능/인수조건 후보
- 기존 업무/Source 기반 AS-IS 분석
- 영향 범위와 Coverage Gap 후보
- 기능 설계와 Program Spec 초안
- 테스트 시나리오와 검증 결과 초안
- 아직 확정할 수 없는 내용의 `확인 필요 사항`
- 현재 단계가 끝난 뒤의 다음 작업 안내

**사람의 기본 역할은 빈 Template을 채우는 것이 아니라 초안을 검토하고 판단권한이 필요한 항목을 결정하는 것입니다.**

## 2. 프로젝트 종류를 선택한다

| 상황 | 선택 | 설명 |
|---|---|---|
| 새 시스템/새 서비스이고 기존 Source가 없음 | `GREENFIELD` | 요구사항과 프로젝트 기준으로 시작 |
| 기존 운영 시스템의 변경·고도화 | `BROWNFIELD` | Repository와 기존 자료를 근거로 현재 상태부터 확인 |
| 신규/기존 영역이 섞여 있음 | `HYBRID` | 기존 Source 근거와 신규 설계를 함께 사용 |
| 잘 모르겠음 | `AUTO` | Harness가 Source/build/schema 자산을 보고 후보를 판단 |

모르면 `AUTO`로 시작하면 됩니다. Git Repository가 있다는 이유만으로 Brownfield라고 확정하지 않습니다.

## 3. 처음 준비할 자료

모든 자료가 처음부터 완벽할 필요는 없습니다. 있는 자료만 제공하고, 없는 사실은 Agent가 발명하지 않고 `확인 필요`로 남겨야 합니다.

### Greenfield

우선순위가 높은 자료:

- 요구사항, 요청 메일, 회의 결과
- 업무 SOP/매뉴얼/정책 문서가 있다면 원본
- 프로젝트 표준 또는 개발 가이드가 있다면 원본
- 확정된 Architecture/기술 결정사항
- Security/NFR/개인정보/운영 제약 자료

처음부터 화면·API·DB 상세설계를 사람이 작성할 필요는 없습니다.

### Brownfield

우선순위가 높은 자료:

- 실제 Repository 또는 Source bundle
- 변경 요청/장애 개선 요청/고도화 요구
- 기존 설계서와 운영 문서
- DB Schema/ERD/DDL/Mapper 자료
- API/인터페이스/Event/Batch 자료
- Build/Test/배포 자료
- Log/APM/운영 이력 등 현재 동작을 확인할 수 있는 자료

자료를 찾지 못한 경우 `영향 없음`으로 처리하지 않고 Coverage Gap으로 남깁니다.

## 4. 최초 실행

Repository root에서 실행합니다.

```bash
python sdlc/scripts/harness.py setup \
  --name <project-name> \
  --mode AUTO \
  --delivery STANDARD
```

작은 운영 변경이면 `FAST`, 일반 SI/SM 기능이면 `STANDARD`, 대형·고위험 범위이면 `FULL`을 사용합니다.

설정 상태를 확인합니다.

```bash
python sdlc/scripts/harness.py check --setup
```

`CONFIGURED_PROVIDER_REQUIRED` 또는 `SETUP_OR_PROVIDER_REQUIRED`가 보이면 Harness 구조가 실패했다는 뜻이 아니라 **실제 문서를 작성할 Agent Provider 연결이 아직 필요하다는 뜻**입니다.

Provider 연결 방법은 [프로젝트 설정 가이드](./프로젝트_설정_가이드.md)를 확인합니다.

## 5. Agent가 자동으로 해야 하는 일

setup 이후 Agent가 연결되면 사용자가 내부 설정 파일을 해석하는 대신 다음을 우선 수행해야 합니다.

1. 제공된 자료와 Repository에서 확인 가능한 사실을 찾습니다.
2. 확인한 사실과 분석상 추정을 구분합니다.
3. Source에서 보이는 동작만으로 고객의 업무정책을 확정하지 않습니다.
4. 근거가 있는 Section은 빈칸으로 두지 않고 초안을 작성합니다.
5. 모르는 정보는 억지로 채우지 않고 `확인 필요 사항`으로 모읍니다.
6. 현재 산출물과 다음 단계에 실제 필요한 자료만 사용합니다.
7. 작업이 끝나면 사용자가 해야 할 다음 행동을 한 가지 이상 명확하게 안내합니다.

## 6. 사람이 반드시 확인하는 일

사람은 다음처럼 **판단권한이 필요한 내용**에 집중합니다.

- 업무 목표와 범위 포함/제외
- 고객 정책과 예외 정책
- 사용자 권한과 승인 기준
- 우선순위와 일정상 선택
- Architecture/기술 선택 승인
- 위험 수용 여부
- 테스트 인수와 배포 판단

Source 경로, Mapper 후보, 관련 Table, 기존 호출관계처럼 Evidence로 확인 가능한 내용을 사람이 처음부터 직접 채우는 방식으로 진행하지 않습니다.

## 7. 요구사항 또는 변경요청을 등록한다

### 기존 RQ가 이미 있는 경우

현재 Target을 확인한 뒤 계획부터 볼 수 있습니다.

```bash
python sdlc/scripts/harness.py check --target <RQ-ID>
python sdlc/scripts/harness.py work --target <RQ-ID> --plan-only
```

기존 RQ의 변경요청은 다음처럼 입력합니다.

```bash
python sdlc/scripts/harness.py change \
  --target <RQ-ID> \
  --change "변경 내용을 자연어로 입력"
```

### XLSX 요구사항 원본만 있는 경우 — 현재 전환 경로

현재 구현에는 XLSX 원본을 보존하며 Requirement Candidate를 만드는 importer가 있습니다.

```bash
python sdlc/scripts/import_requirements.py <requirements.xlsx>
```

하지만 이 명령은 **Candidate 생성까지만 수행하며 첫 RQ를 Canonical에 등록하고 Target ID를 반환하는 Zero-to-One intake는 아직 아닙니다.** 신규 사용자가 내부 Canonical 파일을 수동 편집해 이 Gap을 메우는 것은 권장하지 않습니다.

Session 3 / WP-03에서 목표 명령은 다음처럼 통합될 예정입니다.

```text
python sdlc/scripts/harness.py intake <file-or-text>
→ RQ ID 반환
→ python sdlc/scripts/harness.py work --target <RQ-ID>
```

## 8. 첫 `work`에서 기대할 것

`work --plan-only`는 Source를 바로 수정하는 명령이 아닙니다. 먼저 현재 Target에서 다음에 수행할 Stage와 필요한 입력을 확인하는 용도입니다.

실제 Agent 실행에서는 다음 경험을 목표로 합니다.

```text
프로젝트 자료
→ Agent가 근거 기반 초안 작성
→ 확인되지 않은 내용은 OPEN
→ 사람이 확인해야 하는 항목만 검토
→ Agent가 문서를 보완
→ 다음 단계 안내
```

Agent Provider가 연결되지 않았거나 Target이 아직 없으면 실제 문서 생성 성공으로 보지 않습니다.

## 9. 문제가 생겼을 때 어디를 볼까

| 상황 | 먼저 할 일 |
|---|---|
| setup 상태를 모르겠음 | `python sdlc/scripts/harness.py check --setup` |
| Agent가 실행되지 않음 | [프로젝트 설정 가이드](./프로젝트_설정_가이드.md)의 Provider 항목 확인 |
| 어떤 프로젝트 유형인지 모르겠음 | `--mode AUTO`로 setup 후 탐색 결과 확인 |
| Brownfield인데 Source 영향이 충분히 안 나옴 | Coverage Gap을 확인하고 필요한 Repository/DB/Interface 자료를 추가 |
| 업무정책을 Agent가 확정해 버림 | 해당 내용을 확정으로 사용하지 말고 `확인 필요`로 되돌린 뒤 권한자 확인 |
| 첫 요구사항을 넣었는데 RQ ID가 없음 | 현재 WP-03 미구현 Gap. 내부 Canonical을 수동 편집하지 말고 intake 연결 작업 필요 |
| 다음에 뭘 해야 할지 모르겠음 | `check --target <ID>` 또는 현재 산출물의 `다음 작업` 확인 |

## 10. 처음에는 읽지 않아도 되는 것

일반 프로젝트 참여자는 아래 Framework 내부 구조를 먼저 학습할 필요가 없습니다.

- 내부 Rule/Skill/Reference 계층
- Runtime Contract와 Schema
- Canonical 저장 형식
- Overlay/Preset 내부 구조
- Validation/Pilot 역사 문서

필요한 내부 규칙은 Harness와 Agent Runtime이 실행할 때 적용해야 합니다.

## 11. 현재 WP-01 완료 범위와 남은 연결

이번 Onboarding의 역할은 **어디서 시작하고, 무엇을 준비하고, Agent와 사람이 각각 무엇을 하는지**를 한 문서에서 이해하게 하는 것입니다.

아직 별도 Work Package가 필요한 항목:

- 단일 `.sdlc/project.yaml` 진입점: WP-02
- `harness.py intake`와 첫 RQ 자동 등록: WP-03
- 사용자 산출물 `docs/**` / Machine artifact `.sdlc/**` 완전 분리와 Workspace 자동 생성: WP-04
- 모든 Template의 Agent Draft First 전환과 Gold Sample: WP-05/06/10

따라서 **이 문서를 읽었다는 사실만으로 Production Project Ready라고 판정하지 않습니다.** 실제 사용자와 실제 Agent의 반복 수행 검증은 별도 Pilot이 필요합니다.
