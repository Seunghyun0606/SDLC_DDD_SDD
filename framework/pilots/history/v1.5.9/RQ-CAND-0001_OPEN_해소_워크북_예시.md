# RQ-CAND-0001 OPEN 해소 워크북 예시

## 목적
첨부 요구사항 `REQ_TM_FL001~003`만 있고 SOP/실제 Source가 없는 상황에서 OPEN을 설계자가 어떻게 구조적으로 채워갈지 검증한다.

### 원본 요구사항
- `REQ_TM_FL001`: 탄력근로제 근무계획 저장
- `REQ_TM_FL002`: 탄력근로제 근무계획 조회
- `REQ_TM_FL003`: 기본 근무스케줄에 따라 근무계획 생성 자동 저장

사용자가 제시한 예시인 `ESS 프로파일을 가진 탄력근로제 근무자 / 매일 / 탄력근로제 근무계획 메뉴 / 날짜와 시간 / 선택 후 저장 / 매일 근무시간 입력 필요`는 **업무정의 후보를 구체화하는 입력 예시**로 사용하되 고객 확정 Business Truth로 간주하지 않는다.

## OPEN 해소 목록
| OPEN ID | 분류 | 현재 Gap | 우선 해소 방법 | 관찰/제안 값 | 근거 구분 | 결정 권한자 | 상태 | 후속 영향 |
|---|---|---|---|---|---|---|---|---|
| OPEN-FL-001 | SIX_W_WHO | 실제 사용자/권한 미확정 | BUSINESS_OWNER_INTERVIEW | ESS 프로파일을 가진 탄력근로제 근무자 | DESIGN_PROPOSAL/사용자 예시 | Business Owner | PROPOSED | 권한, Data Scope, 화면 접근 |
| OPEN-FL-002 | SIX_W_WHEN | 저장 주기/Trigger 미확정 | BUSINESS_OWNER_INTERVIEW | 매일 | DESIGN_PROPOSAL/사용자 예시 | Business Owner | PROPOSED | Validation, 마감, Batch |
| OPEN-FL-003 | SIX_W_WHERE | 실제 메뉴/화면 미확정 | DESIGNER_PROPOSAL | 탄력근로제 근무계획 메뉴 | DESIGN_PROPOSAL/사용자 예시 | UX/Functional Owner | PROPOSED | 화면 ID, Menu 권한 |
| OPEN-FL-004 | FIELD | 실제 입력 Field 미확정 | DESIGNER_PROPOSAL | 근무일자, 시작시간, 종료시간 후보 | DESIGN_PROPOSAL/사용자 예시 | Functional Owner | PROPOSED | DTO, Validation, DB |
| OPEN-FL-005 | SIX_W_WHY | 업무 목적/정책 근거 미확정 | BUSINESS_OWNER_INTERVIEW | 근무자는 매일 예정 근무시간을 입력해야 함 | DESIGN_PROPOSAL/사용자 예시 | Business Owner | PROPOSED | BR, AC, 고객 문서 |
| OPEN-FL-006 | CRUD | 저장/조회 행위 | REQUIREMENT_GIVEN + DESIGNER_PROPOSAL | 조회와 저장을 별도 사용자 행위로 제공 | GIVEN + DESIGN_PROPOSAL | Functional Owner | CANDIDATE | 화면 버튼/API |
| OPEN-FL-007 | BUSINESS_RULE | 기존 근무계획 존재 시 처리 미확정 | BUSINESS_OWNER_INTERVIEW | 덮어쓰기/수정 유도/자동생성 Skip 중 결정 필요 | ASSUMPTION | Business Owner | OPEN | 자동생성, 중복처리 |
| OPEN-FL-008 | BUSINESS_RULE | 자동생성 Trigger 미확정 | WORKSHOP | 최초 진입/일자 선택/Batch 중 결정 필요 | ASSUMPTION | Business Owner | OPEN | Program Entry Point |
| OPEN-FL-009 | AUTHORIZATION | 본인/타인 계획 편집 범위 미확정 | BUSINESS_OWNER_INTERVIEW | 본인 데이터만 편집 후보 | DESIGN_PROPOSAL | Business Owner | PROPOSED | Security/Data Filter |
| OPEN-FL-010 | DATA_QUERY | 실제 Table/Query 미확정 | SOURCE_ANALYSIS 또는 DEVELOPER_PROPOSAL | Brownfield는 Source/Schema 확인, Greenfield는 Target Data Model 제안 | TECHNICAL_PROPOSAL | Data/Technical Owner | OPEN | Repository/Mapper/SQL |
| OPEN-FL-011 | COMMON_CODE | 근무유형/상태 코드 미확정 | DATA_ANALYSIS 또는 PROJECT_STANDARD | 기존 Code Dictionary 확인, 없으면 신규 Code Group 제안 | TECHNICAL_PROPOSAL | Data/Functional Owner | OPEN | Field, Validation |
| OPEN-FL-012 | EXCEPTION | 중복저장/시간역전/휴일/마감 후 수정 등 예외 미확정 | WORKSHOP + DEVELOPER_PROPOSAL + QA_ANALYSIS | 오류/검증 후보를 제시하고 업무/기술 영역별 결정 | DESIGN_PROPOSAL/TECHNICAL_PROPOSAL | Functional/Technical/QA Owner | PROPOSED | Logic, Error, TC |

## 인터뷰에서 바로 사용할 질문 예시
| 질문 | 현재 알고 있는 내용 | 권장 선택지/예시 | 왜 필요한가 | 결정권자 |
|---|---|---|---|---|
| 누가 근무계획을 입력합니까? | 탄력근로제 근무자라는 후보가 있음 | 본인만 / 부서담당 대행 / 관리자 대행 | 권한과 Data Scope 결정 | Business Owner |
| 언제 입력해야 합니까? | `매일` 후보 | 매일 사전입력 / 주 단위 계획 / 변경 시 갱신 | Validation/마감/알림 결정 | Business Owner |
| 이미 계획이 있으면 자동생성을 어떻게 합니까? | 원문에 없음 | Skip / 기존값 유지 / 재생성 / 사용자 확인 | 중복 및 데이터 손상 방지 | Business Owner |
| 어떤 시간 단위를 입력합니까? | 날짜/시간 후보 | 시작·종료 / 총시간 / 휴게시간 포함 여부 | Field/Validation/계산 Rule 결정 | Functional Owner |

## 기존 시스템 분석으로 채울 항목 예시
Brownfield라면 다음은 고객에게 먼저 묻기보다 실제 시스템에서 확인한다.
- Menu/Route/Screen ID와 현재 표시 Field
- 저장/조회 Endpoint 및 Service/Repository
- 실제 Table/Column/Mapper/SQL
- 현재 Role/Profile과 Data Scope 집행 코드
- 근무유형/상태 Common Code
- 현재 Validation/Error Message

이 결과는 `OBSERVED_AS_IS`로 기록한다. 현행 동작이 잘못되었을 수 있으므로 TO-BE 정책으로 자동 확정하지 않는다.

## 설계자·개발자 제안으로 채울 항목 예시
### Designer Proposal
- 달력 또는 일자 목록에서 날짜를 선택하고 시작/종료시간을 입력하는 화면
- 기존 계획이 있는 날짜를 시각적으로 구분
- 저장 전 필수값/시간 역전 Validation

### Developer Proposal
- 저장 API는 idempotency/중복 요청 방지 필요 여부 검토
- 조회는 사용자+기간 조건을 기본으로 하고 Page/정렬 기준 제안
- Transaction 경계와 낙관적 Lock 필요 여부 검토
- 공통코드는 기존 Code Dictionary 재사용 우선

제안안은 Project Standard/Architect/Functional Owner에 의해 채택되면 `ACCEPTED_DESIGN`으로 올릴 수 있지만, 업무정책을 바꾸는 내용은 Business Owner 확인이 필요하다.

## 평가
이 예시는 SOP가 없어도 OPEN을 그대로 방치하지 않고 다음 행동으로 전환할 수 있음을 보여준다.

`요구사항 → OPEN 생성 → 인터뷰/현행분석/설계·개발 제안 → 결정권자 검토 → Functional Design/Program Spec 반영`

따라서 목표 상태는 `모든 정보가 사전 입력으로 존재`하는 것이 아니라 **모든 OPEN이 해소 방법과 결정 경로를 가진 상태**이다.
