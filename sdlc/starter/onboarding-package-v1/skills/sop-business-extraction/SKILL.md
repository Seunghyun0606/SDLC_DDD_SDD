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

## Precondition
- 원본 Source ID/Locator를 만들 수 있어야 한다.
- Revision을 알 수 없으면 `SOURCE_REVISION_OPEN`을 기록한다.

## Retrieval Strategy
1. 문서 구조/Sheet/Slide/Heading
2. Legacy Requirement ID와 상위 분류
3. 명시된 Actor/Trigger/Object/Action/Purpose
4. CRUD/Rule/Exception/State
5. UI/Data/Code/Integration

## Atomic Steps
1. Source Locator 생성
2. 원문 ID를 `source_requirement_id`로 보존
3. 명시된 값만 Evidence Fragment로 추출
4. 6W Candidate 생성
5. FR/BR/AC Candidate 생성
6. RQ Boundary는 `sdlc/config/rq-boundary.yaml`로 판정
7. 모호한 Boundary는 `UNRESOLVED + BOUNDARY_AMBIGUOUS`
8. 질문을 Evidence 요구사항과 함께 우선순위화
9. Stage Input Pack 생성 또는 갱신

## Decision Rules
- 사람이 명시한 원문은 GIVEN
- 문서에서 직접 읽은 현행 설명은 GIVEN/OBSERVED 성격을 Source authority에 맞춰 보존하며 자동 CONFIRMED BR로 승격하지 않는다.
- CRUD 이름 유사성만으로 RQ Merge/Split 금지
- 없는 Why/Actor/권한/예외는 OPEN

## Output Schema
- Evidence Fragment
- Requirement Boundary Record
- Stage Input Pack
- 6W/FR/BR/AC Candidate

## Quality Check
- 원본 ID와 Locator가 모두 남아 있는가?
- 모든 Candidate가 Evidence로 역추적되는가?
- 없는 값을 창작하지 않았는가?
- BOUNDARY_AMBIGUOUS를 Canonical RQ로 발행하지 않았는가?

## Alert Conditions
- SOURCE_REVISION_OPEN
- EVIDENCE_CONFLICT
- BOUNDARY_AMBIGUOUS
- AUTHORITY_UNKNOWN

## Stop Conditions
- Required Output이 값 또는 OPEN으로 채워짐
- 현재 문서의 Configured Range를 모두 읽음
- 다음 판단이 업무 Boundary/정책 결정임
- 동일 Evidence가 반복됨

## Escalation Conditions
- RQ Merge/Split이 Scope/Owner/Release/AC를 바꿈 → L2_OR_HUMAN
- 상충하는 공식 문서 → HUMAN
- Cross-domain Boundary → L3_OR_HUMAN

## Do Not
- 없는 Why 창작
- Screenshot만 보고 hidden validation 추정
- 회의록 자동 공식정책 승격
- 최신 문서=최고 Authority 간주
- Source 구현=BR 자동 승격
- CRUD 이름만으로 RQ grouping

## Example
정상: `REQ_A`가 독립 Outcome이라고 고객 문서에 명시되면 `KEEP_AS_RQ` Candidate를 만들 수 있다.

OPEN: `REQ_TM_TE017 일근태입력/마감 조회`가 독립 RQ인지 상위 `근태마감`의 FR인지 근거가 없으면 `UNRESOLVED`, `BOUNDARY_AMBIGUOUS`, `L2_OR_HUMAN`으로 종료한다.
