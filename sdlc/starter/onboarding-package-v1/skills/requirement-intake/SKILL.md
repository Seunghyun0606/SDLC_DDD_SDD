# Skill — Requirement Intake

## Purpose
고객 Requirement Workbook을 Source Truth로 보존하여 Stage Runtime에 전달한다. Workbook Row를 Canonical RQ/FR로 자동 승격하지 않는다.

## Required Input
- Requirement `.xlsx` 파일
- `sdlc/config/requirement-intake.yaml`

## Optional Input
- Worksheet 이름
- 처리할 Source Requirement ID 목록
- Project Overlay의 추가 Header Alias

## Precondition
- 입력 파일이 읽기 가능해야 한다.
- Required Header `source_requirement_id`, `requirement_name`, `requirement_text`를 찾을 수 있어야 한다.

## Retrieval Strategy
1. 명시된 Worksheet가 있으면 해당 Sheet
2. 없으면 첫 Worksheet
3. 상단 `header_scan_rows` 범위에서 Required Header Alias 탐색
4. Optional Header는 발견된 경우만 사용
5. 데이터 Row는 Workbook 순서와 실제 Row 번호를 보존

## Atomic Steps
1. XLSX OOXML 구조를 읽는다.
2. Workbook SHA-256을 계산한다.
3. Header Row와 Column Mapping을 결정한다.
4. Source Requirement Row를 순서대로 읽는다.
5. Required Field 누락 Row를 `skipped_rows`에 보존한다.
6. Duplicate Source Requirement ID를 검사한다.
7. 선택된 Row를 `truth_state: GIVEN`으로 출력한다.
8. Worksheet/Header Row/Source Row/File Revision을 Provenance로 기록한다.

## Decision Rules
- Workbook 값은 `GIVEN`이다.
- Intake 단계는 Canonical RQ/FR/BR/AC ID를 생성하지 않는다.
- 빈 Cell을 추측해서 채우지 않는다.
- Header 위치는 고정 Column 번호보다 Alias 탐색을 우선한다.
- Duplicate Source Requirement ID 또는 Required Field 누락은 정상 성공으로 숨기지 않는다.

## Output Schema
`artifact_type: REQUIREMENT_INTAKE`

필수 Root:
- `requirement_intake.source`
- `requirement_intake.header_mapping`
- `requirement_intake.source_row_count`
- `requirement_intake.records`
- `requirement_intake.truth_guards`

각 Record 필수 Provenance:
- `source_row`
- `source_requirement_id`
- `truth_state: GIVEN`

## Quality Check
- Workbook hash가 존재하는가?
- 실제 Worksheet/Header/Source Row 번호가 보존되는가?
- Duplicate ID가 검사되었는가?
- Required Field 누락이 숨겨지지 않았는가?
- Canonical ID가 Intake에서 생성되지 않았는가?

## Alert Conditions
- REQUIREMENT_HEADER_NOT_FOUND
- DUPLICATE_SOURCE_REQUIREMENT_ID
- REQUIRED_FIELD_MISSING
- WORKSHEET_NOT_FOUND
- XLSX_READ_ERROR

## Stop Conditions
- 모든 선택 Row가 값 또는 명시적 누락 상태로 보존됨
- Duplicate/Skip 결과가 기록됨
- 다음 단계가 Requirement Boundary 또는 Stage Pack 생성으로 넘어감

## Escalation Conditions
- Header 의미가 여러 Column에서 충돌 → BA/Harness Admin
- Source Requirement ID가 중복되며 어느 Row가 Authority인지 불명확 → Human
- Workbook 보호/암호화/비표준 외부 링크 때문에 직접 읽기 불가 → Harness Admin

## Do Not
- Workbook 내용을 보고 Canonical Requirement를 자동 생성
- 누락 담당자/일정을 임의 생성
- Row 번호를 재정렬된 Index로 대체
- 고객별 Column 이름을 Core Script에 하드코딩

## Example
정상: `REQ-001`이 Workbook Row 15에 존재하면 `source_row: 15`, `truth_state: GIVEN`으로 보존한다.

OPEN/Failure: Required Header를 찾지 못하면 Column을 추측하지 않고 `REQUIREMENT_HEADER_NOT_FOUND`로 중단한다.
