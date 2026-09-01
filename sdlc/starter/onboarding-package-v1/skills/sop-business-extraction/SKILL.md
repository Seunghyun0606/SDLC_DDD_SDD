# Skill — SoP / Business Source Extraction

## Purpose
PPT/XLSX/Word/PDF/MD 원본문서에서 Provenance를 유지하면서 6W/RQ/FR/BR/UI/Data/Integration 후보를 추출한다. 한 실행의 목표는 원문을 확정된 업무정책으로 바꾸는 것이 아니라 다음 Stage가 사용할 Evidence와 Candidate를 만드는 것이다.

## Required Input
- Business Source Manifest
- Original Document

## Optional Input
- Glossary
- Project/domain hints
- 기존 Requirement Boundary record
- Legacy Requirement Normalization record

## Precondition
- 원본 Source ID/Locator를 만들 수 있어야 한다.
- Revision을 알 수 없으면 `SOURCE_REVISION_OPEN`을 기록한다.
- Legacy Requirement Inventory라면 `sdlc/config/legacy-requirement-normalizer.yaml`을 먼저 적용한다.

## Retrieval Strategy
1. 문서 구조/Sheet/Slide/Heading
2. Legacy Requirement ID와 상위 분류
3. 명시된 Actor/Trigger/Object/Action/Purpose
4. CRUD/Rule/Exception/State
5. UI/Data/Code/Integration

## Atomic Steps
1. Source Locator 생성
2. 원문 ID를 `source_requirement_id`로 보존
3. Legacy Inventory이면 Source Row를 `SOURCE_ROW`로 등록
4. `EXACT_LEVEL2_REQUIREMENT_NAME` 규칙으로 1차 `GROUP_CANDIDATE` 생성
5. Candidate Group은 `OPEN + UNRESOLVED + publish_canonical=false`로 유지
6. 필요하면 명시적 반복 Label만 이용해 `SUBGROUP_CANDIDATE` 생성하되 Truth는 `INFERRED`
7. 명시된 값만 Evidence Fragment로 추출
8. 6W/FR/BR/AC Candidate 생성
9. RQ Boundary는 `sdlc/config/rq-boundary.yaml`로 Row/Group/Subgroup 범위를 판정
10. 모호한 Boundary는 `UNRESOLVED + BOUNDARY_AMBIGUOUS`
11. 질문을 Evidence 요구사항과 함께 우선순위화
12. Stage Input Pack은 기본적으로 Candidate Group별 1개 생성
13. Pack Split은 서로 다른 질문/Owner/Process/Source Path가 있을 때만 수행

## Decision Rules
- 사람이 명시한 원문은 GIVEN
- 문서에서 직접 읽은 현행 설명은 GIVEN/OBSERVED 성격을 Source authority에 맞춰 보존하며 자동 CONFIRMED BR로 승격하지 않는다.
- 정확히 같은 Level2+요구사항명은 Review Group Evidence일 뿐 같은 Business Outcome의 증명이 아니다.
- CRUD 이름 유사성만으로 RQ Merge/Split 금지
- Subgroup Candidate는 Canonical Split이 아니다.
- 없는 Why/Actor/권한/예외는 OPEN

## Output Schema
- Legacy Requirement Normalization
- Evidence Fragment
- Requirement Boundary Record
- Group-level Stage Input Pack
- 6W/FR/BR/AC Candidate

## Quality Check
- 원본 ID와 Locator가 모두 남아 있는가?
- 모든 Source Row가 정확히 하나의 1차 Group Candidate에 속하는가?
- Candidate Group이 Canonical RQ/FR로 자동 발행되지 않았는가?
- 모든 Candidate가 Evidence로 역추적되는가?
- 없는 값을 창작하지 않았는가?
- BOUNDARY_AMBIGUOUS를 Canonical RQ로 발행하지 않았는가?
- Stage Pack 수가 Row 수에 비례해 불필요하게 증가하지 않았는가?

## Alert Conditions
- SOURCE_REVISION_OPEN
- EVIDENCE_CONFLICT
- BOUNDARY_AMBIGUOUS
- AUTHORITY_UNKNOWN
- GROUP_TOO_LARGE
- GROUPING_CONFLICT

## Stop Conditions
- Required Output이 값 또는 OPEN으로 채워짐
- 현재 문서의 Configured Range를 모두 읽음
- 다음 판단이 업무 Boundary/정책 결정임
- 동일 Evidence가 반복됨
- Candidate Group별 Stage Pack이 생성되고 추가 Row Pack이 새로운 정보를 만들지 않음

## Escalation Conditions
- RQ Merge/Split이 Scope/Owner/Release/AC를 바꿈 → L2_OR_HUMAN
- Group이 크고 복수 Process/Owner가 섞인 정황 → L2_REVIEW
- 상충하는 공식 문서 → HUMAN
- Cross-domain Boundary → L3_OR_HUMAN

## Do Not
- 없는 Why 창작
- Screenshot만 보고 hidden validation 추정
- 회의록 자동 공식정책 승격
- 최신 문서=최고 Authority 간주
- Source 구현=BR 자동 승격
- CRUD 이름만으로 RQ grouping
- Exact Group Candidate를 Canonical RQ로 자동 승격
- Legacy Row마다 Stage Input Pack을 무조건 1개씩 생성

## Example
정상: 동일 Level2와 동일 요구사항명을 가진 39개 Legacy Row는 `GROUP_CANDIDATE` 1개로 묶어 검토량을 줄일 수 있지만, `publish_canonical=false`를 유지한다.

OPEN: `REQ_TM_TE016~054`가 하나의 Canonical RQ인지 여러 RQ인지 근거가 없으면 Group Boundary를 `UNRESOLVED`, `BOUNDARY_AMBIGUOUS`, `L2_OR_HUMAN`으로 종료한다.
