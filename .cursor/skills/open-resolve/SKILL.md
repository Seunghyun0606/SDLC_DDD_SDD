# OPEN Resolution Skill

## Purpose
SOP나 완전한 사전 문서가 없어도 요구사항/분석/설계/Program Spec의 OPEN을 설계 가능한 작업 단위로 바꾸고, 인터뷰·현행 분석·Source/Data 분석·프로젝트 표준·설계/개발 제안을 통해 해소한다.

## Required Input
- 관련 RQ/FR/SCN/PROC/PGM 또는 현재 Artifact
- OPEN 항목 목록
- 가능한 Evidence: 요구사항, 기존 시스템, Source/Data, 프로젝트 표준, 고객 답변 중 존재하는 것

## Optional Input
- SOP/정책/매뉴얼
- UI/UX 표준
- Data Dictionary / Common Code Dictionary
- Architecture/Integration/Test Standard
- Project `open-resolution-profile.yaml`

## Core Rule
`OPEN`은 단순 질문 목록이 아니라 **해소 방법, 제안/관찰 값, 근거, 결정 권한자, 상태, 후속 영향**을 가진 설계 Backlog로 관리한다.

SOP는 유용한 Evidence이지만 필수 입력이 아니다.

## 해소 방법 선택
1. 업무 사실/목적/정책이면 인터뷰·Workshop을 우선한다.
2. Brownfield의 화면/Field/CRUD/Data/연계는 기존 시스템과 Source/Data 분석을 우선한다.
3. Greenfield의 화면/기술 구조는 설계자/개발자 제안과 프로젝트 표준으로 구체화할 수 있다.
4. 프로젝트 표준으로 결정 가능한 기술항목은 고객에게 불필요한 질문을 만들지 않는다.
5. 정보가 없지만 합리적 설계안이 필요한 경우 `DESIGNER_PROPOSAL` 또는 `DEVELOPER_PROPOSAL`을 만든다.
6. 제안값에는 반드시 선택 이유, 대안, 영향, 검토 권한자를 기록한다.

## 실행 계약(Agent Execution Contract)
| 항목 | 실행 규칙 |
|---|---|
| 입력 필드 | OPEN ID, 관련 RQ/FR/SCN/PGM, 현재 값, Category, downstream impact, 사용 가능한 Evidence를 확인한다. |
| 근거 분류 | 고객/업무 확정은 CONFIRMED/GIVEN, 현행/Source는 OBSERVED, 프로젝트 표준은 PROJECT_STANDARD, 설계자/개발자 제안은 DESIGN_PROPOSAL/TECHNICAL_PROPOSAL로 분리한다. |
| 실행 순서 | OPEN 수집 → Category/Decision Domain 분류 → 해소 방법 선택 → 질문/분석 Task/제안안 작성 → 근거/대안 기록 → 권한자 판정 → Artifact 반영 → 남은 OPEN 재평가 순서로 수행한다. |
| 계속/중단 조건 | OPEN이 있어도 설계 가능한 부분은 계속한다. 업무 Truth가 필요한 항목은 제안만 하고 확정하지 않는다. Execution Guard/법적·보안 Hard Guard는 해당 실행만 중단한다. |
| 출력 필드 매핑 | `open-resolution-workbook.md`의 OPEN 목록, 6W, UI/Field/CRUD, BR/State/Exception, Data/Query/Common Code, Integration/Auth/NFR/AC-TC, Decision Log를 갱신한다. |
| 품질 게이트 | 모든 해소값은 Resolution Method + Basis + Rationale/Evidence + Decision Owner + Status를 가져야 한다. 제안과 확정이 구분되어야 한다. |
| 미확정/실패 처리 | Evidence 없음은 PROPOSED/OPEN, 상충은 CONFLICT, 현행만 확인된 것은 OBSERVED_AS_IS, 프로젝트 권한자가 채택한 기술안은 ACCEPTED_DESIGN, 업무 권한자가 확인한 업무 사실/정책은 CONFIRMED_BUSINESS로 둔다. |

## 사람 중심 작성 흐름
### 1. 인터뷰로 채울 항목
각 질문에 다음을 함께 제공한다.
- 왜 이 질문이 필요한가
- 현재 알고 있는 내용
- 권장 선택지/예시
- 답변에 따라 바뀌는 설계 영역
- 답변자/결정권자 역할

질문만 던지지 말고 설계자가 회의를 진행할 수 있는 형태로 만든다.

### 2. 기존 시스템 분석으로 채울 항목
- 실제 화면/Menu/Route
- Field/Validation/Default
- CRUD와 상태 변화
- Source Symbol/API/Batch/Event
- Table/Column/Mapper/Query
- Common Code/Enum/기준정보
- 권한 집행 방식
- 오류/재처리/Integration

확인된 결과는 `OBSERVED_AS_IS`로 기록한다.

### 3. 설계자 경험으로 제안할 항목
- 화면 동선/Layout/Field 표시 방식
- 사용자 입력 방식과 Default 후보
- 업무 흐름 단순화 안
- 상태 전이/예외 UX 후보

업무 정책을 바꾸는 제안은 BUSINESS/FUNCTIONAL 결정권자 검토가 필요하다.

### 4. 개발자 경험으로 제안할 항목
- API/Service 분리
- Transaction/Idempotency
- Query/Index/Paging
- Error Handling/Retry
- Integration 방식
- Logging/Observability
- Test 구조

Project Standard/Architect 권한으로 결정 가능한 경우 `ACCEPTED_DESIGN`까지 갈 수 있다.

## Output
- Template: `sdlc/templates/core/open-resolution-workbook.md`
- 기존 `interview-questions.md`는 고객 질문 View로 유지할 수 있으나 OPEN의 전체 해소 상태는 Workbook을 Source of Resolution으로 사용한다.

## Quality Check
- SOP가 없다는 이유만으로 모든 항목을 질문으로만 남기지 않았는가
- 현행분석으로 확인 가능한 항목을 고객에게 다시 묻지 않았는가
- 설계자/개발자 제안을 업무 Truth처럼 적지 않았는가
- 기술 결정까지 불필요하게 고객 승인 대기로 만들지 않았는가
- 제안에 선택 이유와 대안이 있는가
- 해소 후 Functional Design/Program Spec의 OPEN이 실제로 감소했는가

## Do Not
- 경험을 근거 없는 CONFIRMED Business Rule로 만들지 않는다.
- Brownfield 현행 동작을 자동으로 TO-BE 정책으로 승격하지 않는다.
- 모든 OPEN을 고객 질문으로 전가하지 않는다.
- 실제 프로젝트 표준이 있는데 임의의 개인 선호를 우선하지 않는다.
