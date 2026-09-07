# Change Level Control Plane Reference

이 Reference는 `/work`에서 L1~L5를 어떻게 결정·변경·추적하고 Human Projection과 분리할지 정의한다.

## 1. 핵심 분리

```text
Change Level → Semantic Work / Evidence / Human Review 깊이
Profile      → Human Artifact topology
Stage        → 내부 실행/재진입 의미
```

따라서 Profile이 `PROFILE_PRIMARY_SET`이면 L1/L2 Fast Path라도 PRIMARY Engineering 문서를 생략하지 않는다. 낮은 Level에서는 문서를 `CONCISE`로 짧게 작성할 수 있지만, "문서 자체 없음"으로 처리하지 않는다.

## 2. Level 정의와 상태 위치

정책 정의:

- `sdlc/config/change-execution-policy.json`
- `sdlc/design/contracts/change-level-contract.json`

Target별 Runtime 이력:

- `sdlc/runtime/change-level/<TARGET>.json`

Agent는 Target 작업 시작 시 다음을 확인한다.

- `observed_change_level`: Evidence 기반 AUTO 관측값
- `effective_change_level`: 실제 실행에 적용할 값
- `level_source`: AUTO / Project Target / Manual Default / Human Override
- `safety_floor`: 현재 Evidence가 요구하는 최소 안전 수준
- `level_history`: Level/Source 변경 이력

## 3. Project Config 사전 지정

AUTO 기본:

```yaml
change:
  level_policy: AUTO
  minimum_level: L1
```

프로젝트 전체 Manual 기본:

```yaml
change:
  level_policy: MANUAL
  default_level: L3
```

Target별 사전 지정:

```yaml
change:
  level_policy: AUTO
  target_levels:
    RQ-001:
      level: L3
      reason: "기능 영향과 업무 규칙을 상세 검토해야 함"
```

Target Override가 있으면 일반 AUTO 관측값보다 우선한다. Safety Floor보다 낮게 지정하려면 `accept_below_safety_floor: true`와 명시적 Risk Acceptance가 필요하다.

## 4. 작업 중 Human Override

사용자가 자연어로 다음과 같이 요청할 수 있다.

- `RQ-001은 L3로 진행해줘. 이유는 업무규칙 검토가 필요해서야.`
- `RQ-001을 L4에서 L2로 낮춰줘. 영향이 조회조건 하나로 확인됐어.`
- `RQ-001 Level override를 해제하고 AUTO로 다시 판단해줘.`

Runtime 명령:

```bash
python sdlc/scripts/change_execution_runtime.py set-level --target RQ-001 --level L3 --reason "업무규칙 검토 필요"
python sdlc/scripts/change_execution_runtime.py clear-level --target RQ-001 --reason "AUTO 재평가"
python sdlc/scripts/change_execution_runtime.py show --target RQ-001
```

Human downgrade는 허용하지만 이유가 필수다. 현재 `safety_floor`보다 낮으면 `--accept-below-safety-floor` 없이 거부한다.

## 5. 자동 강등과 명시적 강등

- Evidence 증가로 더 높은 Level이 관측되면 자동 승격 가능.
- AUTO 관측값이 낮아졌다는 이유만으로 자동 강등하지 않는다.
- 사람이 이유를 명시한 downgrade는 허용한다.
- Human Override 해제 후에는 현재 Project/AUTO 정책으로 rebaseline한다.

## 6. Level 변경 후 해야 할 일

Level 변경은 상태 숫자만 바꾸고 끝내지 않는다.

1. `/work --target <TARGET>`을 다시 실행한다.
2. 새 `execution_policy.required_semantic_work/evidence/review`를 계산한다.
3. 부족해진 Semantic Work/Evidence가 있으면 보완한다.
4. `tailoring.required_engineering_artifacts` 또는 `projection_update_set`을 확인한다.
5. 해당 Profile의 required Engineering Projection을 모두 Canonical/Evidence 기준으로 갱신한다.
6. 이전보다 낮은 Level이면 상세 단락을 억지로 삭제하지 않고 근거 있는 `CONCISE` 표현으로 정리한다.
7. Level 이력은 Runtime state에 남기고 사람 문서에는 내부 상태코드를 불필요하게 노출하지 않는다.

## 7. PROFILE_PRIMARY_SET Agent 규칙

`tailoring.projection_topologies.internal == PROFILE_PRIMARY_SET`이면:

- `primary_work_artifact`: 현재 Stage와 가장 직접적으로 맞는 주 편집 문서다.
- `required_engineering_artifacts`: 이번 작업 뒤 반드시 존재·갱신되어야 하는 Profile PRIMARY 문서 집합이다.
- `projection_detail`: L1/L2 `CONCISE`, L3/L4 `STANDARD`, L5 `FULL` 같은 작성 밀도다.

Agent는 `primary_work_artifact`만 작성하고 나머지를 누락해서는 안 된다.

예: HRIS 2종 Profile에서 L1/DEVELOPMENT인 경우

```text
주 편집 문서: 02_작업지시서.md
필수 갱신 문서:
- 01_업무정의서.md   ← CONCISE라도 작성/갱신
- 02_작업지시서.md   ← 현재 구현 중심 상세
```

L1 업무정의서는 정책 재설계를 꾸며내지 않는다. 예를 들어 `업무정책 변경 없음`, `국소 조회조건 변경`, `확인된 영향 없음`처럼 실제 Evidence에 맞게 짧게 기록한다.

## 8. 금지

- L1/L2라는 이유만으로 Custom Profile PRIMARY 문서를 삭제/미생성 처리하지 않는다.
- Level을 문서 개수로 해석하지 않는다.
- 사용자 Level 변경 이유를 대화에만 남기지 않는다.
- Safety Floor 아래 Human downgrade를 묵시적으로 승인하지 않는다.
- Level 변경 후 기존 Projection을 stale 상태로 방치하고 완료라고 보고하지 않는다.
