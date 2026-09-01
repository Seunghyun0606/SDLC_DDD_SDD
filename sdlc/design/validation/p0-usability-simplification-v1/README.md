# P0 Usability Simplification Validation

상태: `ACTIVE_P0_CANDIDATE`

## 범위

1. Legacy Requirement → Canonical RQ Boundary
2. Lite / Standard / Enterprise Artifact Profile
3. Stage Input Pack
4. Low-Agent Procedure / Stop / Escalation
5. Source → Documentation Reverse Sync
6. Deterministic Contract Validator

## P0 Acceptance Criteria

- 원본 Requirement ID가 Canonical 정규화 중 사라지지 않는다.
- Boundary가 모호하면 자동 RQ Merge/Split을 하지 않는다.
- Stage Input Pack만으로 다음 Agent가 Target, Evidence, OPEN, 다음 Action을 이해한다.
- 입력에 없는 Business Fact는 OPEN으로 남긴다.
- Source 동작을 Business Truth로 자동 확정하지 않는다.
- Source Diff에서 관련 PGM/문서로 Reverse Sync Candidate를 생성할 수 있다.
- Required Field, ID Reference, OPEN Preservation, Boundary Cardinality는 Validator가 실패시킨다.

## 실행

```text
python sdlc/scripts/validate_p0_contracts.py stage-pack <stage-input-pack.yaml>
python sdlc/scripts/validate_p0_contracts.py rq-boundary <requirement-boundary.yaml>
```

PyYAML이 없으면 Validator는 조용히 Skip하지 않고 dependency 오류로 종료한다.

## Pilot 기준

기존 `REQ_TM_TE017` 예제는 Boundary를 자동 확정하지 않고 `BOUNDARY_AMBIGUOUS`로 유지하는 것이 정답이다. Source/정책 자료가 없으므로 Who/When/Where, PGM, BR, AC를 창작하면 실패다.

## 아직 P0에서 하지 않는 것

- Starter 기본 mode AUTO 전환
- Stack-neutral Source Adapter 전환
- Jira/Sonar/Monitoring 실제 Provider 연결
- Semantic Merge 구현
- Action Permission / Recovery 구현

위 항목은 P1/P2 후보이며 P0에 포함시켜 복잡도를 키우지 않는다.
