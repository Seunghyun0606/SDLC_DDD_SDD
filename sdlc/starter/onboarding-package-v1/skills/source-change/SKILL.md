# Skill — Blueprint to Source Change

## Purpose
Engineering Design/Development Blueprint와 Current Source Evidence로 기존 Convention을 보존한 Source Change Proposal 또는 허용된 Source Change를 수행하고 Reverse Sync Candidate를 생성한다.

## Required Input
- Stage Input Pack
- Engineering Design 또는 Development Blueprint
- Source Analysis Result
- Source Profile
- Current revision
- Test command 또는 명시적 OPEN

## Optional Input
- Applicable Standards
- Existing similar implementation
- Release/rollback metadata

## Precondition
- Source Target이 direct evidence로 식별되어야 한다.
- 실제 write는 project execution policy가 허용해야 한다.
- Ambiguous Target이면 write하지 않는다.

## Retrieval Strategy
1. TASK/PGM direct relation
2. Current file/symbol
3. Preserve할 architecture/convention
4. Related data/interface/test

## Atomic Steps
1. Intent와 AC 확인
2. Target/revision 검증
3. Preserve pattern 기록
4. OPEN/Blocking 정리
5. File별 변경 계획
6. 허용된 경우 최소 Source 변경
7. Scope Validation
8. Test 실행 또는 미실행 사유 기록
9. Implementation Result 생성
10. Changed File/Symbol Evidence 수집
11. `reverse-sync-candidate.yaml` 생성
12. 관련 PGM/RQ/FR/BR/AC/TC STALE Candidate 계산

## Decision Rules
- unrelated refactoring 금지
- actual common code OPEN이면 hardcode 금지
- Source Diff는 OBSERVED이며 Business Rule Change는 Candidate
- `BUSINESS_RULE_CANDIDATE`, `SECURITY_BEHAVIOR`, `UNKNOWN`은 Human Review 필요

## Output Schema
- Source Change Proposal 또는 Source Diff
- Implementation Result
- Reverse Sync Candidate
- 갱신된 Stage Input Pack

## Quality Check
- 변경 파일이 TASK/PGM Scope 안인가?
- current revision을 기준으로 했는가?
- AC/Test Mapping이 있는가?
- Reverse Sync Candidate가 생성되었는가?
- Human Truth가 자동 overwrite되지 않았는가?

## Alert Conditions
- TARGET_AMBIGUOUS
- COMMON_CODE_OPEN
- DB_WRITE_BOUNDARY_OPEN
- TEST_COMMAND_OPEN
- BUSINESS_RULE_CHANGE_CANDIDATE
- REVERSE_SYNC_UNKNOWN

## Stop Conditions
- 계획된 File/Symbol 변경과 Test/미실행 상태가 기록됨
- 다음 변경이 다른 PGM/Interface/Table로 Scope 확장을 요구함
- Target/Revision/Permission이 불명확함

## Escalation Conditions
- Security/Authorization change → L3_OR_HUMAN
- Cross-system transaction → L3
- Business Rule change candidate → HUMAN_REVIEW
- Unknown reverse-sync meaning → L2_OR_HUMAN

## Do Not
- unrelated refactoring
- new layer/framework invention
- unknown code hardcoding
- executed test 없는 verify-pass
- Source Diff로 Human Truth 자동 수정

## Example
정상: 명확한 Mapper statement의 조건식 변경 후 관련 PGM과 AC Test를 재실행 후보로 연결한다.

OPEN: 조건식 변경이 업무정책 자체의 변경인지 단순 버그 수정인지 판단할 근거가 없으면 `BUSINESS_RULE_CANDIDATE`로 기록하고 업무 문구는 수정하지 않는다.
