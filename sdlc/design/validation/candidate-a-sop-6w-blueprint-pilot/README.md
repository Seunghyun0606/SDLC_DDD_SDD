# Candidate A+ Pilot — SoP Extraction → 6W → Development Blueprint

> 상태: `VALIDATION PILOT / NOT BASELINE`
> Parent: `SDLC_DESIGN_SESSION_SECOND/design/candidate-a-source-customer-br-guidance-v1`
> 원칙: Candidate B와 결합하지 않으며 `main`에 병합하지 않는다.

## Pilot Goal

동일 업무를 서로 다른 3개 Evidence에서 읽어 실제 산출물로 연결한다.

1. 실제 `요구사항목록.xlsx` — `REQ_TM_FL001~003`, `REQ_TM_TE001~009`
2. 가상 고객 PPT SoP Fixture — Slide 단위 업무정의/화면/규칙/연계
3. 가상 Brownfield JSP/Spring/MyBatis Source Fixture — 현재 구현/DB/공통코드

```text
XLSX + PPT SoP + Current Source
→ SoP Extraction
→ Evidence Merge
→ 6W Business Scenario
→ RQ / FR / BR / AC
→ Customer Functional Specification
→ Development Blueprint
→ Source-ready 판단
```

## Key Validation Question

- XLSX만 있을 때 무엇이 OPEN인가?
- PPT SoP가 Who/When/Where/Why와 UI/Rule을 얼마나 보완하는가?
- Current Source가 실제 File/Query/Table/Common Code를 얼마나 확정하는가?
- 최종 Blueprint만으로 개발자가 화면/CRUD/Logic/Integration/SQL/Data/Code/Test를 이해할 수 있는가?

## Pilot Result Summary

- XLSX Evidence: 기능명/CRUD Candidate는 충분하나 `Who/When/Where/Why`는 부족
- PPT Evidence: 6W, 화면 Field, 업무 Rule, 업무 연계 보완
- Source Evidence: JSP/Service/Mapper/XML/Table/Common Code/AS-IS 30분 구현 보완
- 최종 Scenario: `SCN-FLEX-01 일일 근무계획 저장/수정`, `SCN-FLEX-02 조회/Calendar`, `SCN-FLEX-03 기본값/미입력 알림`
- 최종 RQ Candidate: `RQ-FLEX-PLAN-001`
- Development Blueprint: UI/CRUD/Core Logic/Integration/Query/Data/Common Code/Source Mapping/Test 포함

## Files

- `input/01_requirements-xlsx-extract.md`
- `input/02_customer-sop-ppt-fixture.md`
- `input/03_brownfield-source-fixture.md`
- `extraction/01_evidence-merge.md`
- `outputs/01_business-definition-6w.md`
- `outputs/02_requirement-analysis.md`
- `outputs/03_customer-functional-spec.md`
- `outputs/04_development-blueprint.md`
- `outputs/05_traceability-and-findings.md`

## Verdict

`PASS AS A DOCUMENT-TO-BLUEPRINT PILOT / IMPLEMENTATION NOT EXECUTED`

실제 고객 PPT/PDF/Word Parser와 실제 Java/MyBatis Repository 실행은 별도 검증이 필요하다.