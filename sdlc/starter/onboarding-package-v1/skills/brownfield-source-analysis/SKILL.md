# Skill — Brownfield Java/MyBatis Source Analysis

## Purpose
6W/RQ/FR/BR를 JSP/Spring/MyBatis/Oracle 구현과 연결하고 Change Target/Blind Spot을 찾는다.

## Required Input
- Source Profile
- Current repository revision
- Business Definition
- Requirement/Design candidates

## Retrieval Strategy
1. 업무용어/Menu/Legacy ID
2. JSP/URL
3. Controller
4. Service/Transaction
5. Mapper Interface/XML
6. Table/Code/Procedure
7. Downstream/Batch/Interface
8. Similar implementation

## Steps
- File/Symbol 확인
- Call chain
- Current behavior
- Data R/W
- Auth/Transaction
- Dynamic SQL/Procedure/Trigger
- Code Master
- Similar Pattern
- Change Candidate/Blind Spot

## Output
`templates/source-analysis-result.yaml`

## Alerts
- TARGET_AMBIGUOUS
- SOURCE_REVISION_UNKNOWN
- MAPPER_RELATION_BROKEN
- CODE_VALUE_OPEN
- DB_KEY_NOT_VERIFIED
- DYNAMIC_SQL_BLIND_SPOT
- PROCEDURE_BLIND_SPOT
- DOWNSTREAM_UNKNOWN

## Do Not
오래된 Summary/파일명 similarity만으로 target 확정 금지. Source 동작을 Business Truth로 확정 금지.
