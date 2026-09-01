# OPEN Resolution Skill

## Purpose
SOP나 완전한 사전 문서가 없어도 요구사항/분석/설계/Program Spec의 미확정 항목을 실제 해소 가능한 작업으로 바꾸고, 인터뷰·현행 분석·Source/Data 분석·프로젝트 표준·설계/개발 제안을 통해 줄여간다.

## Required Input
- 관련 RQ/FR/SCN/PROC/PGM 또는 현재 Artifact
- 현재 미확정 항목
- 사용 가능한 Evidence: 요구사항, 기존 시스템, Source/Data, 프로젝트 표준, 고객 답변 중 존재하는 것

## Optional Input
- SOP/정책/매뉴얼
- UI/UX 표준
- Data Dictionary / Common Code Dictionary
- Architecture/Integration/Test Standard
- Project `open-resolution-profile.yaml`

## Core Rule
`OPEN`은 단순 질문 목록이 아니라 **무엇을 확인할지, 어떻게 확인할지, 현재 확인값/제안, 확인·결정 담당, 진행 상태**를 가진 설계 Backlog다.

SOP는 유용한 Evidence이지만 필수 입력이 아니다.

사람이 기본적으로 보는 진행 상태는 다음 5개뿐이다.
- `미확정`
- `확인중`
- `제안`
- `확정`
- `보류`

`Category`, `Decision Domain`, `Resolution Method`, `Basis Class`, 내부 Status code, downstream impact는 Trace/Validator에 필요한 Machine metadata다. 가능한 경우 Agent/Script가 계산하고 기본 사용자 문서에서 직접 입력시키지 않는다.

기존 Machine 상태인 `OBSERVED_AS_IS`, `ACCEPTED_DESIGN`, `CONFIRMED_BUSINESS` 등은 하위 호환성과 안전 판정에 유지한다.

## 해소 방법 선택
1. 업무 사실/목적/정책이면 인터뷰·Workshop을 우선한다.
2. Brownfield 화면/Field/CRUD/Data/연계는 기존 시스템과 Source/Data 분석을 우선한다.
3. Greenfield 화면/기술 구조는 설계자/개발자 제안과 프로젝트 표준으로 구체화할 수 있다.
4. 프로젝트 표준으로 결정 가능한 기술 항목은 고객에게 불필요한 질문을 만들지 않는다.
5. 정보가 없지만 합리적 설계안이 필요한 경우 `DESIGNER_PROPOSAL` 또는 `DEVELOPER_PROPOSAL`을 Machine basis로 기록한다.
6. 제안에는 선택 이유와 대안, 영향, 검토 권한자를 남긴다.

## 실행 계약(Agent Execution Contract)
| 항목 | 실행 규칙 |
|---|---|
| 입력 필드 | 관련 ID, 확인/결정할 내용, 현재 값, 사용 가능한 Evidence, 결과 영향 여부를 먼저 확인한다. |
| 근거 분류 | 고객/업무 확정은 CONFIRMED/GIVEN, 현행/Source는 `OBSERVED_AS_IS`, 프로젝트 표준은 PROJECT_STANDARD, 설계자/개발자 제안은 `DESIGNER_PROPOSAL`/`DEVELOPER_PROPOSAL` 또는 TECHNICAL_PROPOSAL로 내부 기록한다. |
| 실행 순서 | 미확정 항목 수집 → 결과를 바꾸는지 확인 → 확인 방법 선택 → 질문/분석 Task/제안 작성 → 근거/대안 기록 → 확인·결정 담당 지정 → Artifact 반영 → 남은 미확정 재평가 순서로 수행한다. |
| 계속/중단 조건 | 미확정이 있어도 설계 가능한 부분은 계속한다. 업무 Truth가 필요한 항목은 제안까지만 진행한다. Execution Guard/법적·보안 Hard Guard는 해당 실행만 중단한다. |
| 출력 필드 매핑 | 사람 View에는 확인 내용/확인 방법/현재값 또는 제안/담당/5단계 진행상태를 기록한다. 세부 Category/Decision Domain/Resolution Method/Basis/Internal Status/downstream impact는 Machine metadata로 동기화한다. |
| 품질 게이트 | 모든 미확정 항목은 최소 하나의 실제 확인 방법과 담당 역할이 있어야 한다. 제안과 업무 확정, AS-IS 관찰과 TO-BE 정책을 혼동하지 않는다. |
| 미확정/실패 처리 | Evidence 없음은 미확정 또는 제안, 분석 중은 확인중, 상충/연기는 보류로 표시한다. 내부적으로 현행 확인은 `OBSERVED_AS_IS`, 기술 채택은 `ACCEPTED_DESIGN`, 업무 확인은 `CONFIRMED_BUSINESS`를 유지한다. |

## 사람 중심 작성 흐름
### 1. 고객/업무 담당자에게 확인할 항목
각 질문에는 필요한 경우 다음을 함께 제시한다.
- 현재 알고 있는 내용
- 왜 결과에 영향을 주는지
- 선택지 또는 설계안
- 누가 답하거나 결정해야 하는지

### 2. 기존 시스템/Source에서 확인할 항목
고객에게 묻기 전에 실제 Evidence로 확인 가능한지 먼저 본다.
- 화면/Menu/Route
- Field/Validation/Default
- CRUD/상태 변화
- Source Symbol/API/Batch/Event
- Table/Column/Mapper/Query
- Common Code/기준정보
- 권한 집행 방식
- 오류/재처리/Integration

확인 결과는 내부적으로 `OBSERVED_AS_IS`이며 TO-BE 정책으로 자동 승격하지 않는다.

### 3. 설계자 제안 가능 항목
- 화면 동선/Layout/Field 표시 방식
- 사용자 입력 방식과 Default 후보
- 업무 흐름 단순화 안
- 상태 전이/예외 UX 후보

### 4. 개발자/Architect 제안 가능 항목
- API/Service 분리
- Transaction/Idempotency
- Query/Index/Paging
- Error Handling/Retry
- Integration 방식
- Logging/Observability
- Test 구조

Project Standard/권한에 따라 기술안은 내부적으로 `ACCEPTED_DESIGN`까지 갈 수 있다.

## Output
- Template: `sdlc/templates/core/open-resolution-workbook.md`
- `interview-questions.md`는 동일 OPEN 정보에서 필요한 고객 질문만 파생하는 View로 사용한다.

## Quality Check
- SOP가 없다는 이유로 모든 항목을 질문으로만 남기지 않았는가
- 현행분석으로 확인 가능한 항목을 고객에게 다시 묻지 않았는가
- 설계/개발 제안을 업무 Truth처럼 적지 않았는가
- 기술 결정까지 불필요하게 고객 승인 대기로 만들지 않았는가
- 해소 후 Functional Design/Program Spec의 미확정이 실제로 감소했는가
- 사람이 Machine taxonomy를 직접 관리하도록 만들지 않았는가

## Do Not
- 경험을 근거 없는 CONFIRMED Business Rule로 만들지 않는다.
- Brownfield 현행 동작을 자동으로 TO-BE 정책으로 승격하지 않는다.
- 모든 OPEN을 고객 질문으로 전가하지 않는다.
- 실제 프로젝트 표준이 있는데 임의의 개인 선호를 우선하지 않는다.
- `Decision Domain`, `Basis Class` 같은 내부 분류를 일반 사용자의 필수 입력으로 만들지 않는다.
