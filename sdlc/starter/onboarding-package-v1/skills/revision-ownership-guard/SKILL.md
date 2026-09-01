# Skill — Revision / Ownership Guard

## Purpose
Multi-Agent Source Write 전에 Revision과 File Ownership을 검증하여 stale write, 비소유 파일 덮어쓰기, Agent 간 동시 수정 충돌을 차단한다.

## Required Input
- `change_execution.change_id`
- `agent_id`
- `expected_revision`
- `current_revision`
- `agent_branch`
- `parent_change_branch`
- `ownership.requested_paths`
- `ownership.owned_paths` 또는 `ownership.shared_paths`

## Optional Input
- `ownership.coordination_proof_ref`
- 다른 Agent의 `ownership.active_claims`

## Precondition
- Source Write를 수행하기 전이어야 한다.
- Current Revision은 실제 Repository/Provider에서 읽은 값이어야 한다.

## Retrieval Strategy
1. Stage Pack/Task의 expected revision
2. 현재 Source Provider revision
3. Agent Branch / Parent Change Branch
4. Task Ownership의 owned/shared path
5. Active Agent Claim
6. Shared Path Coordination Proof

## Atomic Steps
1. `expected_revision == current_revision` 검사
2. Agent Branch 존재 검사
3. Parent Change Branch 존재 검사
4. 각 requested path가 owned/shared pattern에 포함되는지 검사
5. shared path면 coordination proof 검사
6. 다른 Agent active claim과 requested path overlap 검사
7. Blocker가 없으면 `ALLOW` + `guard_proof_ref` 생성
8. 하나라도 실패하면 `DENY` + blocker 목록 생성

## Decision Rules
- Revision mismatch는 자동 overwrite 금지
- owned/shared에 없는 Path는 Write 금지
- Shared Path는 Coordination Proof 없이는 Write 금지
- 다른 Agent의 Active Claim과 겹치면 Write 금지
- `ALLOW` 결과를 Source Write 성공과 동일시하지 않는다. 이는 Pre-write permission proof일 뿐이다.

## Output Schema
`artifact_type: REVISION_OWNERSHIP_GUARD_RESULT`

필수 Root:
- `revision_ownership_guard.decision`
- `revision_ownership_guard.requested_paths`
- `revision_ownership_guard.blockers`
- `revision_ownership_guard.truth_guards`

ALLOW 시 필수:
- `revision_ownership_guard.guard_proof_ref`

## Quality Check
- Expected/Current Revision이 실제 값인가?
- 모든 requested path가 Ownership Scope에 속하는가?
- Shared Path의 coordination proof가 있는가?
- 다른 Agent Active Claim을 검사했는가?
- DENY를 무시하고 Source Write를 진행하지 않았는가?

## Alert Conditions
- REVISION_MISMATCH
- BRANCH_CONTEXT_REQUIRED
- PATH_NOT_OWNED
- SHARED_PATH_COORDINATION_REQUIRED
- ACTIVE_OWNERSHIP_CONFLICT

## Stop Conditions
- `ALLOW` 또는 `DENY`가 결정됨
- 모든 Blocker가 구체적 Path/Revision과 함께 기록됨

## Escalation Conditions
- Shared Core File을 여러 Task가 반드시 동시에 수정해야 함 → Change Owner
- Revision이 Provider 간 불일치 → Engineering Owner
- Ownership 경계가 정의되지 않음 → PM/Tech Lead

## Do Not
- Revision mismatch 상태에서 force overwrite
- 다른 Agent Claim을 무시하고 같은 File 수정
- Shared File을 Coordination Proof 없이 수정
- Guard 결과를 실제 Provider Write 성공으로 간주

## Example
정상: `expected_revision == current_revision`, requested path가 `src/**` owned scope이고 다른 Claim이 없으면 `ALLOW`한다.

충돌: 다른 Agent가 동일 `src/service.py`를 Active Claim 중이면 `ACTIVE_OWNERSHIP_CONFLICT`로 `DENY`한다.
