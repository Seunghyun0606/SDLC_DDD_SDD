# Usability Simplification vNext — Minimal Prototype v1

> 상태: `DECISION_REQUIRED`
>
> 목적: Red Team Review에서 확인된 P0/P1 문제를 Current Core를 전면 재작성하지 않고 최소 계약으로 검증한다.
>
> 이 폴더는 실험용이며 `SDLC_DESIGN_SESSION_SECOND/base`나 `main`에 자동 반영하지 않는다.

## Prototype 범위

1. Artifact Profile: `Lite / Standard / Enterprise`
2. Stage Input Pack: Agent 교체 가능하고 self-contained한 handoff
3. Low-Agent Skill Procedure Contract: Decision/Stop/Escalation을 명시
4. Source Diff Reverse Sync Contract
5. `REQ_TM_TE017` 근태마감 Pilot Handoff Example

## Before

```text
15 Artifact
→ 13개 default required
→ Starter는 Brownfield 입력과 Source Profile을 기본 전제
→ Skill은 단계 목록은 있으나 Decision/Stop/Escalation이 약함
→ Development Context Pack 개념은 있으나 모든 Stage 공통 Handoff는 아님
→ /change와 STALE은 있으나 Source Diff → 업무문서 영향 분류가 명시적이지 않음
```

## After Prototype

```text
Project Profile
→ Artifact Profile 선택
→ 각 Stage 실행 전 Stage Input Pack 생성
→ Skill Procedure로 한정된 작업 수행
→ Deterministic Validator 실행
→ 불확실하면 OPEN + Escalation
→ Source 변경 후 Reverse Sync Candidate 생성
```

## 기대 효과

- 작은 프로젝트에서 Enterprise 내부 계약을 사용자에게 노출하지 않는다.
- L1 Agent가 임의로 RQ Boundary/Source 의미를 완성하는 것을 줄인다.
- Stage 담당 Agent가 바뀌어도 이전 Conversation History를 요구하지 않는다.
- Source 변경이 문서 Revision 후보로 역전파될 경로를 만든다.
- Config / Skill / Adapter / Core 변경 경계를 명확하게 한다.

## 포함 파일

```text
profiles/artifact-profiles.yaml
contracts/low-agent-skill-procedure.md
contracts/source-reverse-sync.md
templates/stage-input-pack.yaml
sample/REQ_TM_TE017_pilot-stage-input-pack.yaml
```

## 채택하지 않은 것

이번 Prototype에서는 다음을 구현하지 않는다.

- Canonical Core 재작성
- Jira/Confluence/Sonar/Datadog 실제 Adapter
- Source Parser/Static Analyzer 구현
- Semantic Merge 구현
- 실제 Source Write
- main merge

## 검증 기준

Pilot에서 다음을 확인한다.

1. 원본 `REQ_TM_TE017`을 잃지 않는가.
2. RQ grouping이 불명확하면 자동 확정하지 않는가.
3. 입력에 없는 Who/When/Where/Why를 창작하지 않는가.
4. Source가 없으면 Impact/PGM을 CONFIRMED로 만들지 않는가.
5. 다음 Agent가 이 Pack만 읽고 현재 상태/OPEN/필요 Action을 이해할 수 있는가.
6. 단순 ID/Trace/Required/Open 보존은 Validator 대상으로 분리되는가.

## 결론

이 Prototype은 기존 Harness를 대체하는 설계가 아니다. 첫 고객 Pilot 전에 가장 큰 불확실성을 낮추는 최소 변경 후보이며 최종 채택은 `DECISION_REQUIRED`다.
