# Skill — Brownfield Source Analysis

## Purpose
현재 Stage Input Pack의 RQ/FR/BR Candidate를 Existing Source와 연결하여 Change Target과 Blind Spot을 찾는다. Source 동작을 Business Truth로 확정하지 않는다.

## Required Input
- Stage Input Pack
- Source Profile
- Current repository revision

## Optional Input
- Business Definition / Customer View
- Existing Trace/Program Summary
- Build/Test metadata

## Precondition
- 분석 Root가 설정되어 있어야 한다.
- Current revision이 없으면 Source write 후보를 확정하지 않는다.
- RQ Boundary OPEN은 분석을 막지 않지만 결과를 Confirmed Business Impact로 승격하지 않는다.

## Retrieval Strategy
1. Exact Legacy ID / Menu / URL / Symbol
2. JSP/View 또는 API Entry
3. Controller/Handler
4. Service/Transaction
5. Mapper/Repository
6. SQL/Procedure/Table/Code
7. Downstream/Batch/Interface
8. Similar implementation은 마지막 Candidate 근거로만 사용

## Atomic Steps
1. Entry Point Candidate 수집
2. File/Symbol Evidence 기록
3. Call Chain 구성
4. Current Behavior를 OBSERVED로 기록
5. Data R/W, Transaction, Auth, Integration 수집
6. Direct PGM/ART 후보 생성
7. Dynamic SQL/Procedure/Runtime blind spot 확인
8. Impact Candidate와 Confidence 기록
9. Stage Input Pack의 Evidence/Open/Next Action 갱신

## Decision Rules
- Exact/direct relation 우선
- 이름 유사성은 Candidate만 생성
- Business Impact는 Source relation만으로 CONFIRMED 금지
- Write Target은 current revision + direct evidence가 있어야 함
- 후보 점수가 비슷하면 AMBIGUOUS_TARGET

## Output Schema
`templates/source-analysis-result.yaml` + 갱신된 Stage Input Pack

## Quality Check
- Source revision이 기록되었는가?
- 모든 PGM/ART 후보에 File/Symbol Evidence가 있는가?
- OBSERVED와 Business Truth가 분리되었는가?
- Dynamic SQL/Procedure/Downstream blind spot을 확인했는가?

## Alert Conditions
- TARGET_AMBIGUOUS
- SOURCE_REVISION_UNKNOWN
- MAPPER_RELATION_BROKEN
- CODE_VALUE_OPEN
- DB_KEY_NOT_VERIFIED
- DYNAMIC_SQL_BLIND_SPOT
- PROCEDURE_BLIND_SPOT
- DOWNSTREAM_UNKNOWN

## Stop Conditions
- Direct/Configured Retrieval 범위를 모두 탐색함
- 필요한 Entry→Data/Integration 경로가 값 또는 OPEN으로 채워짐
- 다음 탐색이 Runtime/권한/새 Tool을 요구함
- 동일 Evidence가 반복됨

## Escalation Conditions
- Dynamic/runtime-only relation → L3
- High blast radius / cross-system transaction → L3
- Ambiguous write target → L2_OR_HUMAN
- Security critical path → L3_OR_HUMAN

## Do Not
- 전체 Repository 무제한 탐색
- 오래된 Summary/파일명 similarity만으로 target 확정
- Source 동작을 Business Truth로 확정
- revision 없는 Source write target 확정

## Example
정상: exact URL→Controller→Service→Mapper→Table direct chain이 있으면 Technical Impact HIGH Candidate를 만든다.

OPEN: Mapper가 동적 Statement를 조립하고 실제 SQL이 Runtime에서만 결정되면 `DYNAMIC_SQL_BLIND_SPOT`으로 남기고 L3/Runtime Evidence를 요청한다.
