# Candidate A — Rule / Skill / Template / Artifact Realization

> 상태: `VALIDATION / NOT BASELINE`
> Parent: `SDLC_DESIGN_SESSION_SECOND/design/legacy-intake-sync-contract-sample-a`
> 목적: 사용자가 Candidate A를 실제 Harness 설계로 적용했을 때 Rule, Skill, Template, Stage 산출물이 어떻게 보이는지 비교 검증한다.
> 병합 정책: `main` 병합 금지. Candidate B와 자동 결합 금지.

## User decisions applied

- A1 = Option 2: Raw → Candidate → Human Review → Publish
- A2 = Option 2: 22개 Group은 Candidate이며 자동 RQ 확정 금지
- A3 = Option 3: Mega Group은 `SPLIT_REVIEW_REQUIRED`, 자동 Split 금지
- A4 = Option 2: Legacy ID와 Canonical ID 분리
- A5 = Option 2: MD/Excel 양방향 편집 + Canonical 3-way Sync
- A6 = Option 2: 같은 Field 충돌은 `SYNC_CONFLICT`
- A7 = 사용성 검증 후 결정

## 이 검증에서 추가 제안하는 핵심

A2/A3의 미정 영역을 `RQ Boundary Contract`로 구체화한다.

```text
Raw Row
→ Topic Group
→ RQ Boundary Candidate
→ FR Candidate
→ Boundary Review
→ Canonical Publish
```

RQ는 기술 파일/화면 수가 아니라 다음을 중심으로 묶는다.

1. 하나의 Business Goal
2. 주 Actor/Trigger
3. 사용자가 확인할 수 있는 Outcome
4. 동일한 정책/상태 적용범위
5. 독립적인 Acceptance/Release 필요성

기술 경계(Program/Table/API)는 기본적으로 RQ Split의 직접 기준이 아니라 FR/PGM/TASK Split의 신호다.

## 파일

- `01_user_decisions_and_rq_boundary_contract.md`: A1~A7 및 RQ/Grouping 세분화 기준
- `rules/00-candidate-a-core.mdc`: Agent가 항상 지킬 Candidate A Rule
- `skills/work/SKILL.md`: `/work` 단계별 처리 계약
- `templates/rq-boundary-card.md`: RQ 경계 검토 Template
- `templates/stage-handoff.yaml`: Stage 간 Agent 전달 형식
- `sample/01_sample_stage_outputs.md`: 첨부 요구사항목록을 사용한 단계별 Sample 산출물
- `sample/02_worklist-view.csv`: Canonical Worklist의 Excel/CSV View 예

## 검증 질문

사용자는 이 Branch를 보고 다음을 판단한다.

- RQ Boundary Card가 실제 업무 담당자에게 이해 가능한가?
- 39/22/23 Mega Group을 자동 Split하지 않아도 검토 비용이 수용 가능한가?
- Agent가 Stage가 바뀌어도 같은 RQ Scope를 일관되게 전달받는가?
- Legacy ID와 Canonical ID 이중 관리가 혼란보다 추적성 이점이 큰가?
- MD↔Excel 병행 관리가 실제 운영 방식에 적합한가?

최종 채택 여부는 `A7`로 남긴다.
