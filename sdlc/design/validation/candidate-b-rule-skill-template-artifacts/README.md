# Candidate B — Rule / Skill / Template / Artifact Realization

> 상태: `VALIDATION / NOT BASELINE`
> Parent: `SDLC_DESIGN_SESSION_SECOND/design/stage-evidence-execution-contract-sample-b`
> 목적: 사용자가 Candidate B를 실제 Harness 운영계약으로 적용했을 때 Rule, Skill, Template, Stage 산출물, Task 배분, PM/Excel, 중앙 Recovery가 어떻게 보이는지 비교 검증한다.
> 병합 정책: `main` 병합 금지. Candidate A와 자동 결합 금지.

## User decisions applied

- B1 = Option B: CRITICAL 업무 불확실성에서도 short-lived branch Draft Source Write 허용, Merge/Release 제한
- B2 = Option A: `progress=COMPLETE`는 산출물 작성 완료, 실행 권한은 `action_permissions`로 별도 판단
- B3 = Option A: 동일 PGM 실제 수정은 Serial Ownership
- B4 = Option B: High-blast K1은 Candidate 생성 후 Human scope/temporal 확인
- B5 = Option A: Harness가 PM Task SoT. 단 Excel 병행 관리 필수
- B6 = Option B: 4~6명 사용을 전제로 Central Durable Recovery Store

## 이 검증에서 추가한 설계

1. `Task Group / Assignment Lane` 가이드
   - 동일 PGM 수정 Task를 한 Lane으로 묶어 직렬화
   - 유사 기술/업무 작업을 Developer Work Group으로 보여 Context Switching을 줄임
2. `Harness PM SoT + Excel Projection` 계약
   - Harness Canonical Task/Assignment/Schedule이 SoT
   - Excel은 editable projection
   - Stable ID + revision + conflict detection 필요
3. `Central Recovery Strategy`
   - multi-user idempotency
   - lease/ownership
   - Work Unit journal
   - PGM write serialization
   - transaction/outbox
   - 중앙 저장소 장애 시 안전한 degradation

## 파일

- `01_user_decisions_resolved.md`
- `02_task_grouping_and_assignment_guide.md`
- `03_central_recovery_and_pm_excel_strategy.md`
- `rules/00-candidate-b-core.mdc`
- `skills/work/SKILL.md`
- `templates/stage-evidence-envelope.yaml`
- `templates/work-unit.yaml`
- `sample/01_sample_stage_outputs.md`
- `sample/02_pm-worklist.csv`

## 사용자가 검증할 질문

- `COMPLETE`와 실제 실행 권한 분리가 사용자에게 혼동 없이 보이는가?
- Draft Source Write가 존재해도 Merge/Release 금지가 충분히 눈에 띄는가?
- 같은 PGM Serial Ownership이 4~6명 팀에서 병목을 과도하게 만들지 않는가?
- Agent가 Developer Work Group을 실무적으로 유사한 작업끼리 제안하는가?
- Harness SoT + Excel 편집이 PM에게 자연스러운가?
- 중앙 Recovery Store 장애 시 안전성과 작업 지속성의 균형이 적절한가?
