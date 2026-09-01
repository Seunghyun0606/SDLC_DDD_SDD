# Skill — Blueprint to Source Change Proposal

## Purpose
Development Blueprint와 Current Source Evidence로 Brownfield Convention을 보존한 Source Change Proposal을 만든다.

## Required Input
- Development Blueprint
- Source Analysis Result
- Source Profile
- RQ/FR/BR/AC
- applicable Skills
- current revision
- Test command

## Steps
1. Intent
2. Target 검증
3. Preserve pattern
4. OPEN/Blocking
5. File별 변경계획
6. UI/Logic/Data/Integration
7. Test Mapping
8. Patch Proposal
9. Readiness

## Readiness
- PROPOSAL_ONLY
- READY_FOR_DRAFT_WRITE
- BLOCKED

## Blocking
- actual common code OPEN
- auth/profile OPEN
- target revision unknown
- DB key/write boundary unknown
- interface conflict
- critical scope decision OPEN

## Do Not
unrelated refactoring, new layer/framework invention, unknown code hardcoding, executed test 없는 verify-pass 금지.
