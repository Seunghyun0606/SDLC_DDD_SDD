# Candidate B+ Pilot — SoP Evidence → 6W → Development Evidence Blueprint

> 상태: `VALIDATION PILOT / NOT BASELINE`
> Parent: `SDLC_DESIGN_SESSION_SECOND/design/candidate-b-source-customer-br-guidance-v1`
> Candidate A와 결합하지 않으며 `main`에 병합하지 않는다.

## Goal

Candidate A+와 동일한 업무/입력 Fixture를 사용하되 다음을 추가 검증한다.

- 6W 값별 Truth/Evidence/Revision
- UI/CRUD/Logic/Data/Code의 Evidence sufficiency
- `progress complete != source write permission`
- OPEN/ASSUMED 항목이 실제 Write/Merge/Verify Permission에 미치는 영향

## Inputs

1. 실제 `요구사항목록.xlsx`: FL001~003, TE001~009
2. 동일 가상 고객 PPT SoP Slide 1~6
3. 동일 가상 JSP/Spring/MyBatis/Oracle Source Fixture

## Output Flow

```text
Raw Evidence
→ Format-aware Extraction
→ 6W Evidence Merge
→ RQ/FR/BR/AC Candidate
→ Customer Decision & Acceptance View
→ Development Evidence Blueprint
→ Target Proof / Action Permission
```

## Result

- Business Definition: 충분한 Candidate 수준
- Physical Target: Fixture 기준 식별 가능
- Common Code: `WORK_TYPE/FLEX` 관찰, `CONFIRMED` 실제 Code는 OPEN
- Draft Patch Proposal: ALLOW
- Actual customer Source Write: `REQUIRES_REAL_SOURCE_EVIDENCE`
- Merge/Release: DENY
- Verify PASS: DENY

## Files

- `input/01_requirements-xlsx-extract.md`
- `input/02_customer-sop-ppt-fixture.md`
- `input/03_brownfield-source-fixture.md`
- `extraction/01_evidence-merge-and-permission.md`
- `outputs/01_business-definition-6w-evidence.md`
- `outputs/02_customer-decision-acceptance-view.md`
- `outputs/03_development-evidence-blueprint.md`
- `outputs/04_execution-readiness-and-findings.md`

## Verdict

`PASS AS AN EVIDENCE/PERMISSION PILOT / NO REAL SOURCE WRITE OR TEST EXECUTION`