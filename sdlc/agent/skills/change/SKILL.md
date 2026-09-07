# SDLC Core Skill — change

이 파일은 특정 IDE/Agent 제품과 무관한 `/change` Core Source of Truth다.

## 목적

기존 Requirement/Business Truth/Design/Source의 변경 요청을 자연어로 받아 영향 범위와 근거를 확인하고, 확정 업무 사실을 암묵적으로 덮어쓰지 않은 상태에서 guarded Canonical Delta를 만든다.

`/change`의 기본 UX도 Template 입력 방식이 아니다.

> Agent가 현재 Canonical/문서 Block/Source Evidence를 먼저 읽고 변경 전후를 정리한 뒤, 사람 판단이 필요한 부분만 질문한다. 사용자는 질문에 답하거나 특정 Block의 변경을 자연어로 지시한다.

공통 HITL 질문/Block 규칙은 `sdlc/agent/skills/work/references/hitl.md`를 따른다.

## 실행 모드

`.sdlc/project.yaml`의 `agent.execution`을 따른다.

- 미지정: `INTERACTIVE`
- `INTERACTIVE`: 현재 IDE/CLI Agent가 Change Stage Agent 역할을 수행한다.
- `HEADLESS`: Harness가 설정된 Provider를 실행한다.

두 모드 모두 같은 Stage Result Validator, Target Graph Guard, Business Truth Guard, Canonical apply 경계를 사용한다.

## 사용자 입력 UX

일반 사용자는 변경 내용을 자연어로 말하면 된다.

```bash
python sdlc/scripts/harness.py change --target RQ-001 --change "월 마감 이후 재계산 정책을 변경"
```

이미 생성된 문서의 특정 부분을 수정할 때는 **문서 + Block ID를 지정하는 방식**을 권장한다.

```text
RQ-001 Work Unit SDD의 [BLOCK:WU-BUSINESS-RULE]에서
"월 마감 후 재계산 금지"를 "급여 마감 전까지만 재계산 허용"으로 변경해줘.
```

```text
HRIS 업무정의서의 [BLOCK:HRIS-DATA-AUTH]에서
급여담당 프로파일의 수정 권한을 제거해줘.
```

Block ID가 없더라도 문맥이 명확하면 Agent가 해석한 Block을 먼저 알려주고 진행한다. 여러 Block 후보가 있으면 변경 내용을 적용하기 전에 Block 선택만 짧게 확인한다.

### Block 요청 Routing

Agent는 먼저 요청을 다음 중 하나로 판정한다.

- `SEMANTIC_CHANGE`: Requirement / Business Rule / TO-BE / AC / Scope 의미 변경 → 이 `/change` 흐름으로 Canonical Delta 생성
- `EVIDENCE_REFRESH`: Source/DB/Mapping/AS-BUILT 재분석 요청 → `/work`로 Routing
- `PROJECTION_ONLY`: 오탈자/표현/레이아웃만 변경 → Canonical Delta 없음

문서가 수정 대상이라는 이유만으로 Business Truth 변경으로 간주하지 않는다.

## HITL 질문 규칙

Agent는 사용자에게 "Template을 열고 빈칸을 작성해 달라"고 요구하지 않는다.

변경 요청을 받은 뒤 다음 순서로 처리한다.

1. Target과 지정 Block의 현재 Canonical 의미를 확인한다.
2. 관련 Source/Decision/Evidence를 조사한다.
3. `Before → Requested After → 영향 후보`를 Agent가 먼저 정리한다.
4. 표현 수정인지 Semantic 변경인지 판정한다.
5. 기존 `CONFIRMED_BUSINESS` 변경에 사람의 명시적 authorization이 필요하거나, 요청 내용에 두 가지 해석이 있을 때만 질문한다.
6. 질문은 한 턴 기본 최대 3개이며 답변이 반영될 Block과 이유를 함께 보여준다.
7. 답변을 받은 뒤 `GIVEN`/Decision provenance와 Canonical Delta를 연결한다.
8. Canonical Apply 후 관련 Projection을 갱신한다.

사람에게 물어볼 수 있는 것은 정책/범위/업무 예외/권한/Acceptance 같은 Business Authority 영역이다. Java Method, XML Query, Table Column처럼 Source에서 확인할 수 있는 값은 Agent가 조사한다.

## INTERACTIVE 흐름

1. `python sdlc/scripts/harness.py change --target <TARGET> --change "<변경 요청>"`
2. `INTERACTIVE_CHANGE_HANDOFF_READY`를 확인한다.
3. 반환된 `change-context.json` 또는 `work-context.json`에서 현재 Target/Graph/Change Request/Artifact/Canonical baseline을 읽는다.
4. 변경 Target Block과 현재 값을 확인하고 Source/Evidence를 먼저 조사한다.
5. 필요한 경우 HITL 질문을 생성해 사용자 답변을 받는다.
6. 변경 분류(`CLARIFICATION / BEHAVIOR_CHANGE / TECHNICAL_CHANGE / NEW_REQUIREMENT`)와 근거를 정리한다.
7. 선택된 Change Artifact와 `stage-result.json`을 작성한다.
8. finalize 명령을 실행한다.
9. Harness가 `APPLIED / IDEMPOTENT / NO_CHANGE / DRY_RUN_VALIDATED`를 반환한 경우에만 완료로 보고한다.

`INTERACTIVE_CHANGE_HANDOFF_READY`와 `HITL_REQUIRED`는 준비/질문 상태이며 Canonical 변경 성공이 아니다.

## 변경 안전 규칙

- 사용자의 단순 표현 수정과 실제 Business Truth 변경을 구분한다.
- 기존 `CONFIRMED_BUSINESS`를 바꾸려면 명시적 사용자 authorization과 적절한 Evidence가 필요하다.
- Source에서 관찰된 현재 구현은 `OBSERVED`이며 TO-BE Business Truth를 자동 결정하지 않는다.
- `--artifact`, Stage, Source 위치 또는 Block을 지정했다고 해서 상위 Requirement 전체 변경 권한이 생기지 않는다.
- Target Graph 밖 기존 Entity 변경은 금지한다.
- protected branch / stale Git HEAD / stale Canonical revision을 우회하지 않는다.
- Change 분석 Artifact만 만들고 Canonical 적용이 끝났다고 말하지 않는다.
- 사용자의 HITL 답변을 Projection Text에만 반영하고 Canonical/Provenance 갱신을 생략하지 않는다.

## Stage Result

Change도 공통 Stage Result Envelope를 사용한다.

- `stage`: `CHANGE`
- `artifact_path`: Plan이 선택한 Change Artifact와 정확히 일치
- `canonical_delta.base_revision`: prepare 시점 Canonical revision
- `canonical_delta.stage`: `CHANGE`
- `canonical_delta.source_artifact`: `artifact_path`와 동일
- `quality_gate`, `alerts`, `uncertainty`를 숨기지 않는다.
- HITL 답변이 Semantic 변경 근거라면 관련 `GIVEN`/Decision provenance를 포함한다.

문서 표현만 바뀌고 Semantic Delta가 없다면 `operations: []` + `no_change_reason`을 사용한다.

## Canonical 변경 적용

검증된 Delta는 `sdlc/scripts/apply_canonical_delta.py`의 locked atomic write 경계를 사용한다.

일반 `/change` 실행에서는 `run_change.py`가 이 경계를 자동 사용한다. Delta만 독립 검증하거나 기존 자동화와 호환해야 할 때는 low-level dry-run 경로를 유지한다.

지원 Operation:
- `UPSERT_ENTITY`
- `UPSERT_RELATION`
- `ADD_PROVENANCE`

DELETE는 자동 지원하지 않는다.

### Business Truth 안전 규칙
- 기존 `CONFIRMED_BUSINESS`를 바꾸려면 `evidence_class: CONFIRMED`가 필요하다.
- `/change`에서도 사용자가 실제 업무 확정을 명시하지 않았다면 `--allow-business-truth-change`를 사용하지 않는다.
- Source가 기존 업무정책과 다르게 동작해도 Source 관찰을 Business Truth로 자동 승격하지 않는다.
- 값 변경 없이 현행 근거를 연결할 때는 `ADD_PROVENANCE`를 우선한다.

## Source Version / Write Guard

`run_change.py`는 공통 `/work` executor를 사용하므로 다음 Guard를 공유한다.

- 기본 `main/master` 직접 쓰기 금지
- 실행 시작 시 Git HEAD/branch 기록
- Provider가 HEAD를 변경하면 중단
- 허용 Source root/선택 Artifact 밖의 파일 변경 차단
- DEVELOPMENT Source write는 필요한 build/test Guard를 따른다.
- Stage/Canonical 실패 시 Canonical 적용을 중단한다.
- Canonical은 file lock → 최신 revision 재읽기 → atomic replace 경계를 사용한다.

Repository hosting의 Branch Protection 설정까지 이 Script가 대신하는 것은 아니다. 프로젝트 GitHub/GitLab 정책에서도 default branch 보호를 별도로 활성화한다.

## Source Drift Reverse 처리

외부에서 Source가 변경됐거나 Merge/Rebase 이후 기준점이 바뀐 경우 Source reverse check를 통해 `STALE_SOURCE_EVIDENCE`, `STALE_PROPAGATED`, `CHECK_REQUIRED_REVERSE` 후보를 만든다.

Source 변경은 자동 Business Truth 변경이 아니다. Program Reverse Candidate도 업무 시나리오/업무 규칙을 자동 변경하지 않고 사람 Review가 필요한 후보로 유지한다.

## Customer Decision Round Trip

고객 문서 검토 결과는 Customer Decision Round-trip으로 CONFIRMED provenance에 연결할 수 있다. 실제 업무 필드 변경은 명시적 field update와 Business Change authorization이 함께 있을 때만 적용한다.

고객이 문서에서 특정 문구를 바꾸고 싶다고 말하면 가능한 경우 Customer 문서의 Section/Block을 식별한 뒤 연결된 Canonical 의미를 찾아 `/change`로 처리한다.

## Do Not

- Source hash 변화만으로 업무 규칙이 바뀌었다고 판단하지 않는다.
- Change classification만으로 권한을 획득했다고 간주하지 않는다.
- 자동 Merge/commit으로 동시 작업 충돌을 숨기지 않는다.
- 사람에게 Template 전체를 작성하도록 넘기지 않는다.
- 기술적으로 조사 가능한 질문을 사람에게 묻지 않는다.
- HITL 답변을 문서에만 반영하고 Canonical Delta/Provenance를 누락하지 않는다.
