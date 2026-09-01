# Skill — Test / Verification

## Purpose
Acceptance Criteria와 Test Contract를 기준으로 Test 실행 상태와 Verification 상태를 분리하여 판정한다. 실행하지 않은 Test를 PASS로 만들거나 Synthetic Fixture를 Production Verify로 승격하지 않는다.

## Required Input
- Stage Input Pack
- Test Contract
- Source Evidence Set
- Test Execution Result 또는 명시적 NOT_EXECUTED

## Optional Input
- Implementation Result
- Test command / CI metadata
- Runtime log / DB evidence
- Business Rule review decision

## Precondition
- Required AC가 식별되어 있어야 한다.
- Required TC가 AC에 매핑되어 있어야 한다.
- Source Evidence Set ID가 Test Contract와 일치해야 한다.
- VERIFIED_PASS 후보는 실제 Runtime 환경이어야 한다.

## Retrieval Strategy
1. AC 목록
2. TC→AC direct mapping
3. Source Evidence Set
4. Test execution evidence
5. Failure/Blocker evidence
6. Business Rule review state
7. Production/Synthetic source 구분

## Atomic Steps
1. Required AC/TC ID 유효성 검사
2. AC Coverage 계산
3. Source Evidence Set 일치 검사
4. 각 TC 상태를 PASSED/FAILED/BLOCKED/NOT_EXECUTED/SKIPPED_WITH_REASON 중 하나로 기록
5. PASSED/FAILED는 실행 Evidence 확인
6. 미실행/차단 사유 기록
7. Runtime 환경의 actual 여부 확인
8. Business Rule Candidate review 여부 확인
9. Verification Gate 평가
10. Verification Result와 다음 Stage Handoff 생성

## Decision Rules
- AC Coverage 100%는 테스트 설계 완전성이지 실행 성공이 아니다.
- PASSED/FAILED는 runtime evidence가 없으면 사용하지 않는다.
- NOT_EXECUTED는 actual_result를 가지면 안 된다.
- CONTRACT_PASS_RUNTIME_NOT_EXECUTED는 runtime/production pass를 주장하지 않는다.
- VERIFIED_PASS는 모든 Required TC가 실제 환경에서 PASSED이고 Evidence가 있어야 한다.
- Synthetic Fixture는 Production Verified가 될 수 없다.
- 미검토 BUSINESS_RULE_CANDIDATE가 있으면 VERIFIED_PASS 금지.

## Output Schema
- `templates/test-execution-result.yaml`
- `templates/verification-result.yaml`
- 갱신된 Stage Input Pack

## Quality Check
- Required AC Coverage가 100%인가?
- 모든 Required TC가 명시적 상태를 갖는가?
- PASS/FAIL에 Evidence가 있는가?
- Source Evidence Set이 동일한가?
- 실제 Runtime과 Synthetic Fixture가 구분되는가?
- OPEN Blocker가 Verify 상태에 반영됐는가?

## Alert Conditions
- AC_COVERAGE_GAP
- TEST_EVIDENCE_MISSING
- TEST_COMMAND_OPEN
- RUNTIME_ENVIRONMENT_UNAVAILABLE
- SOURCE_EVIDENCE_SET_MISMATCH
- BUSINESS_RULE_REVIEW_OPEN
- SYNTHETIC_ONLY_EVIDENCE

## Stop Conditions
- 모든 Required TC가 상태를 가짐
- 다음 실행에 실제 Runtime/권한/환경이 필요함
- Evidence 부족으로 더 이상 Verification 승격이 불가능함

## Escalation Conditions
- Business Rule Candidate review → L2_OR_HUMAN
- Production release/verification claim → HUMAN_OR_RELEASE_AUTHORITY
- Runtime-only failure cause → L3
- Security/Authorization test → L3_OR_HUMAN

## Do Not
- 실행하지 않은 Test PASS 처리
- 정적 코드 inspection을 runtime test evidence로 둔갑
- Synthetic Fixture를 Production Verify로 승격
- AC Coverage 100%만으로 VERIFIED_PASS
- Open blocker를 숨기거나 제거

## Example
정상: Required TC 4건이 실제 환경에서 전부 PASSED이고 로그/리포트가 있으면 VERIFIED_PASS 후보가 된다.

현재 P0.4 Fixture: TC 4건은 AC-01~05를 100% 커버하지만 Runtime 미실행이므로 `CONTRACT_PASS_RUNTIME_NOT_EXECUTED`가 최대 상태다.
