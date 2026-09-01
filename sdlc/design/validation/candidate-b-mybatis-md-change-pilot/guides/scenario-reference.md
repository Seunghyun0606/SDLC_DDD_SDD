# Candidate B Pilot Scenario Reference Guide

> 목적: Stage Evidence / Action Permission / Work Unit / PGM Lane이 실제 변경 시나리오에서 어떻게 적용되는지 재사용 가능한 가이드로 남긴다.

## Scenario Index

| ID | 시나리오 | 핵심 판단 | 실행 안전성 |
|---|---|---|---|
| B-S01 | 신규 업무요구 | Stage Evidence 작성 | Source Write는 Target Proof 전 DENY |
| B-S02 | 업무정책 변경 | downstream Evidence revision 갱신 | Draft Write 가능, Merge/Release 제한 가능 |
| B-S03 | 동일 PGM 두 Task | Developer Work Group은 같이, Write Lane은 Serial | 두 번째 Write DENY/WAIT |
| B-S04 | Source 적용 후 Agent Crash | 기존 Work Unit/idempotency key 탐색 | Patch 재적용 금지, RESUME_VERIFY |
| B-S05 | Central Store 장애 | 읽기/분석과 Mutating action 분리 | Source Write/Merge/PM Import DENY |
| B-S06 | SQL 성능/Refactoring | business scope unchanged | 필요한 Stage부터 Evidence 재작성 |

## B-S01 신규 업무요구

```text
Subject Snapshot
→ Stage Evidence Envelope
→ Analysis / Process
→ Discovery / Impact
→ Target Write Proof
→ PGM / Task
→ Work Unit PREPARED
→ Draft Source Write
→ Test
→ Verify
```

`progress=COMPLETE`만으로 Source Write를 허용하지 않는다.

## B-S02 업무 정책 변경

변경 예:

> 월마감 이후 승인 수정요청은 재집계 허용. FORCE_CLOSE는 제외.

```text
CR Evidence
→ requirement/process evidence_revision 변경
→ impact/design/program STALE
→ Target Proof 재검증
→ action_permissions 재계산
→ Work Unit
→ Draft Source Write
→ Test/Verify
```

정책 미확정이 남더라도 B1 Option B 조건을 만족하면 short-lived branch Draft Write는 가능하지만 Merge/Release는 DENY할 수 있다.

## B-S03 동일 PGM 경쟁

```text
Developer Work Group
├ TASK-DEV-01 → PGM-ATT-CLOSE-001
└ TASK-DEV-02 → PGM-ATT-CLOSE-001
```

두 Task를 같은 개발자/유사작업 Group으로 배정할 수 있으나 Actual Write는 `program_write_lane`을 통해 직렬화한다.

- Lane owner: Source Write ALLOW
- Non-owner: Analysis/Test preparation ALLOW, Source Write DENY/WAIT

## B-S04 Source 적용 후 Crash

Reference: `runtime/WU-P017-001.md`

```text
PREPARED
→ APPLIED
→ RUNNER_LOST
→ 동일 idempotency key 발견
→ fingerprint 확인
→ RECOVERY_ACQUIRED
→ RESUME_VERIFY
```

동일 Patch를 다시 적용하지 않는다.

## B-S05 Central Store 장애

4~6명 환경에서는 Local fallback mutation을 허용하지 않는다.

| Action | Store unavailable |
|---|---|
| 문서/Source 분석 | ALLOW |
| Proposal/Candidate 생성 | ALLOW |
| Cached PM 조회 | ALLOW + STALE |
| PM Excel import commit | DENY |
| Source Write | DENY |
| Merge/Release | DENY |

## B-S06 기술 변경

업무 결과가 동일한 SQL 성능 변경이나 내부 Refactoring은 Requirement Stage까지 강제로 되돌아가지 않는다.

```text
Technical Evidence
→ Impact/Program evidence revision
→ Target Proof
→ Task/Work Unit
→ Source
→ Regression/Performance Test
```

## Action Permission Reference

`runtime/action-permission-timeline.md`를 사용자/Agent 공통 참조로 사용한다.

변경마다 다음 권한을 독립 계산한다.

- `next_stage_draft`
- `canonical_publish`
- `draft_source_write`
- `source_write`
- `merge`
- `release`
- `test_pass`
- `verify_pass`
- `knowledge_promotion`

이 가이드는 Stage 산출물이 존재하는 것과 실제 실행이 안전한 것을 혼동하지 않기 위한 기준이다.
