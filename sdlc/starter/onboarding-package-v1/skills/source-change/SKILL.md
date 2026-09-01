# Skill — Design to Source Change

## Purpose

Engineering Design/Program Spec와 현재 Stage Evidence를 이용해 Greenfield/Brownfield/Hybrid에서 구현 범위를 결정하고 Source Change Proposal 또는 허용된 Source Change Result를 만든다.

P0 Runtime Core v1의 기본값은 `PROPOSAL_ONLY`다. 실제 Source Write는 별도 Side-effect Capability가 명시적으로 표준화·허용된 경우에만 수행한다.

## Required Input

- Stage Input Pack v2
- Engineering Design 또는 Program Spec
- Project Mode
- Current Target/Revision 또는 명시적 OPEN
- Test Command 또는 명시적 OPEN

## Optional Input

- Source Evidence Set
- Analyzer Evidence
- Source/Profile/Project Overlay
- Existing similar implementation
- Applicable Standards
- Release/Rollback metadata

## Precondition

- 변경 Intent와 관련 AC가 식별되어 있어야 한다.
- Brownfield 실제 Write Target 확정에는 Direct Evidence와 Current Revision이 필요하다.
- Greenfield 신규 Artifact는 Program Spec과 Architecture/Project Standard 근거가 있어야 한다.
- Ambiguous Target이면 실제 Write를 수행하지 않는다.
- 실제 Write는 Runtime의 명시적 Side-effect Capability와 Permission/Idempotency/Recovery Contract를 통과해야 한다.

## Retrieval Strategy

1. Stage Pack의 TASK/PGM/ART/SYMBOL/DATA/INT Direct Reference
2. Engineering Design / Program Spec
3. 현재 Source Evidence와 Revision
4. Project Standard / Overlay
5. 관련 AC/Test Mapping
6. 기존 유사 구현은 직접 관계가 부족할 때 참고 Candidate로만 사용

## Atomic Steps

1. Requirement Intent와 관련 AC를 확인한다.
2. Project Mode와 기존/신규 Artifact 여부를 확인한다.
3. 변경 대상 PGM/ART/SYMBOL/DATA/INT Scope를 Stage Pack에서 확인한다.
4. Brownfield이면 Current Revision과 Direct Evidence를 검증한다.
5. Greenfield이면 새 Artifact 책임과 Project Standard 근거를 확인한다.
6. Preserve해야 할 Architecture/Convention을 기록한다.
7. OPEN/Guard/Blocking 상태를 정리한다.
8. File/Artifact 단위 Source Change Plan을 작성한다.
9. 기본적으로 `SOURCE_CHANGE_PROPOSAL`을 생성한다.
10. 별도 Side-effect Capability가 허용·요청되고 Write Guard가 통과한 경우에만 실제 Source Change를 수행한다.
11. 실제 변경이 존재하면 Changed File/Symbol/Data/Interface Evidence와 Revision을 수집한다.
12. Test 실행 가능 여부와 AC/Test Mapping을 기록한다.
13. Implementation Result를 생성한다.
14. 실제 Source Diff가 있으면 Reverse Sync Candidate를 생성한다.
15. 갱신된 Stage Input Pack에 ART/SYMBOL/DATA/INT/SOURCE 관계와 OPEN을 보존한다.

## Decision Rules

- unrelated refactoring 금지.
- Brownfield Name Similarity만으로 Write Target 확정 금지.
- Greenfield에서 Project 근거 없이 새 Layer/Framework를 만들지 않는다.
- Actual Common Code/DB Contract가 OPEN이면 값을 임의 Hardcode하지 않는다.
- Source Diff는 `OBSERVED`; Business Rule 변경은 Candidate다.
- `BUSINESS_RULE_CANDIDATE`, `SECURITY_BEHAVIOR`, `UNKNOWN`은 Human/L2 Review 없이 Human Truth에 반영하지 않는다.
- Runtime에 Source Write Capability가 없으면 실제 Write를 수행하지 않고 Proposal로 종료한다.

## Output Schema

- `SOURCE_CHANGE_PROPOSAL` 또는 허용된 `SOURCE_CHANGE_RESULT`
- `IMPLEMENTATION_RESULT`
- 실제 Diff가 있는 경우 `REVERSE_SYNC_CANDIDATE`
- 갱신된 Stage Input Pack v2

## Quality Check

- 변경 Scope가 TASK/PGM/Design 범위 안인가?
- Brownfield Source Claim에 Current Revision/Evidence가 있는가?
- Greenfield 신규 Artifact에 책임/표준 근거가 있는가?
- AC/Test Mapping이 있는가?
- Actual Write라면 Permission/Idempotency/Recovery Guard를 통과했는가?
- Changed ART/SYMBOL/DATA/INT가 Handoff에 보존됐는가?
- Human Truth가 Source Diff로 자동 overwrite되지 않았는가?

## Alert Conditions

- TARGET_AMBIGUOUS
- SOURCE_REVISION_OPEN
- SOURCE_WRITE_CAPABILITY_UNAVAILABLE
- COMMON_CODE_OPEN
- DB_WRITE_BOUNDARY_OPEN
- TEST_COMMAND_OPEN
- BUSINESS_RULE_CHANGE_CANDIDATE
- REVERSE_SYNC_UNKNOWN

## Stop Conditions

- Source Change Proposal과 관련 Test/Handoff가 기록됐다.
- 또는 허용된 Source Change Result와 Revision/Evidence가 기록됐다.
- 다음 변경이 다른 PGM/Data/Interface로 Scope 확장을 요구한다.
- Target/Revision/Permission이 불명확해 실제 Write를 진행할 수 없다.

## Escalation Conditions

- Security/Authorization change → L3_OR_HUMAN
- Cross-system transaction → L3_OR_HUMAN
- Business Rule change candidate → HUMAN_REVIEW
- Ambiguous Target → L2_OR_HUMAN
- Source Write Capability 추가 필요 → HARNESS_OWNER

## Do Not

- Source Write Capability 없이 실제 Write 수행
- unrelated refactoring
- Project 근거 없는 새 Framework/Layer 도입
- unknown code/common value hardcoding
- 실행 Evidence 없는 Verify PASS 생성
- Source Diff로 Human Truth 자동 수정

## Example

Brownfield에서 `PGM-ORDER-001`과 `src/order/service.py`가 Direct Trace되고 Current Revision이 확인됐지만 P0 Runtime에 Source Write Capability가 아직 연결되지 않았다면, 변경 대상 Symbol과 예상 Diff, Test Mapping을 포함한 `SOURCE_CHANGE_PROPOSAL`까지만 만든다.

Greenfield에서는 기존 Source Evidence가 없어도 Program Spec과 Project Standard가 충분하면 신규 Artifact Proposal을 만들 수 있다. Source가 없다는 이유만으로 DEVELOPMENT 자체를 중단하지 않는다.
