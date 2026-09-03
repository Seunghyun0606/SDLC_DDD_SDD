# SDLC Core Skill — change

이 파일은 특정 IDE/Agent 제품과 무관한 `/change` Core Source of Truth다.

## 목적

기존 Requirement/Business Truth/Design/Source의 변경 요청을 자연어로 받아 영향 범위와 근거를 확인하고, 확정 업무 사실을 암묵적으로 덮어쓰지 않은 상태에서 guarded Canonical Delta를 만든다.

## 실행 모드

`.sdlc/project.yaml`의 `agent.execution`을 따른다.

- 미지정: `INTERACTIVE`
- `INTERACTIVE`: 현재 IDE/CLI Agent가 Change Stage Agent 역할을 수행한다.
- `HEADLESS`: Harness가 설정된 Provider를 실행한다.

두 모드 모두 같은 Stage Result Validator, Target Graph Guard, Business Truth Guard, Canonical apply 경계를 사용한다.

## INTERACTIVE 흐름

1. `python sdlc/scripts/harness.py change --target <TARGET> --change "<변경 요청>"`
2. `INTERACTIVE_CHANGE_HANDOFF_READY`를 확인한다.
3. 반환된 `change-context.json`에서 현재 Target/Graph/Change Request/Artifact/Canonical baseline을 읽는다.
4. 변경 분류(`CLARIFICATION / BEHAVIOR_CHANGE / TECHNICAL_CHANGE / NEW_REQUIREMENT`)와 근거를 정리한다.
5. 선택된 Change Artifact와 `stage-result.json`을 작성한다.
6. finalize 명령을 실행한다.
7. Harness가 `APPLIED / IDEMPOTENT / NO_CHANGE / DRY_RUN_VALIDATED`를 반환한 경우에만 완료로 보고한다.

`INTERACTIVE_CHANGE_HANDOFF_READY`는 준비 상태이며 Canonical 변경 성공이 아니다.

## 변경 안전 규칙

- 사용자의 단순 표현 수정과 실제 Business Truth 변경을 구분한다.
- 기존 `CONFIRMED_BUSINESS`를 바꾸려면 명시적 사용자 authorization과 적절한 Evidence가 필요하다.
- Source에서 관찰된 현재 구현은 `OBSERVED`이며 TO-BE Business Truth를 자동 결정하지 않는다.
- `--artifact`, Stage, Source 위치를 지정했다고 해서 상위 Requirement 변경 권한이 생기지 않는다.
- Target Graph 밖 기존 Entity 변경은 금지한다.
- protected branch / stale Git HEAD / stale Canonical revision을 우회하지 않는다.
- Change 분석 Artifact만 만들고 Canonical 적용이 끝났다고 말하지 않는다.

## Stage Result

Change도 공통 Stage Result Envelope를 사용한다.

- `stage`: `CHANGE`
- `artifact_path`: Plan이 선택한 Change Artifact와 정확히 일치
- `canonical_delta.base_revision`: prepare 시점 Canonical revision
- `canonical_delta.stage`: `CHANGE`
- `canonical_delta.source_artifact`: `artifact_path`와 동일
- `quality_gate`, `alerts`, `uncertainty`를 숨기지 않는다.

문서 표현만 바뀌고 Semantic Delta가 없다면 `operations: []` + `no_change_reason`을 사용한다.
