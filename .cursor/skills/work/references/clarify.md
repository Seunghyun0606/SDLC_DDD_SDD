# Clarify Reference

## Purpose
결과를 바꿀 수 있는 질문만 생성하고 답이 없어도 다음 단계 진행이 가능한 상태를 만든다.

## Required Input
- Stage: `CLARIFY`
- RQ/FR + OPEN/불확실 항목

## Optional Input
- 기존 Knowledge / Project Overlay / Domain Overlay / PM 정보

## Retrieval Strategy
1. Canonical direct relation
2. 기존 Program/Process/BR summary
3. Trace/Static Analysis candidate
4. Relevant symbol/source snippet
5. 필요한 경우에만 full file

## Steps
1. 입력과 Evidence provenance를 분리한다.
2. 중요 질문을 우선순위화한다.
3. 미확정은 ALT/ASM으로 남긴다.
4. Canonical relation과 Artifact를 동기화한다.

## Output
- INT/ALT/ASM
- Template: `sdlc/templates/core/interview-questions.md`

## Quality Check
- 질문이 실제 결과를 바꾸는가
- Human Truth와 OBSERVED/INFERRED가 구분되는가

## Alert Conditions
- Business Truth 미확정
- Evidence 충돌
- 정책 확인 필요

## Token Strategy
관련 RQ/FR/BR 후보만 사용한다.

## Do Not
- 답변이 없다는 이유로 Workflow 전체를 막지 않는다.
- Source 구현을 정책 답변으로 대신하지 않는다.
