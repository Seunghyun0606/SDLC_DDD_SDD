# 05. Template-driven SoP Evidence Extraction Contract

## Status

`ENHANCED / PARTIALLY_SUPERSEDES 03_business_evidence_package_and_k1_contract.md`

`Business Evidence Card`를 고객의 Primary 작성양식으로 사용하지 않는다. Card는 추출 후 Evidence/Rule Candidate를 요약하는 Derived View로 둔다.

## 1. New Flow

```text
Customer Original SoP/PPT/XLSX/Word/PDF
+ Source Metadata
→ Format-aware Extraction Skill
→ Business Evidence Package
→ 6W Evidence Scenario
→ RQ/FR/BR/UI/Data/Integration Candidates
→ Authority/Scope/Effective Review
→ BR Confirm Candidate
→ High-blast Human Confirmation
→ K1 Eligibility
```

## 2. 왜 Card-first를 낮추는가

Card-first는 고객이 이미 구조화/분류를 수행해야 하므로 도입비용이 높고 원문 문맥을 잃기 쉽다.

Extraction Skill은 다음을 그대로 보존한다.

- XLSX sheet/cell/range
- PPT slide/shape/table/notes
- PDF/DOCX page/heading/table
- raw text/visual reference
- source authority/scope/effective

## 3. Evidence-aware 6W

모든 6W 값은:

```yaml
value: ...
truth: GIVEN|OBSERVED|INFERRED|CONFIRMED|OPEN
evidence: [source#locator]
revision: 1
```

을 가진다.

Extraction Skill이 6W를 다 채웠다는 이유만으로 Truth/K1을 승격하지 않는다.

## 4. Permission Separation

```yaml
extraction_complete: true
br_candidate: ALLOW
customer_review_view: ALLOW
br_confirm: REQUIRES_AUTHORITY_SCOPE_EFFECTIVE
k1_promotion: REQUIRES_HUMAN_IF_HIGH_BLAST
source_write: DENY_BY_EXTRACTION_ALONE
```

## 5. Customer Overlay

고객별 차이는 Schema Fork 대신 Extraction Overlay로 관리한다.

```yaml
customer_overlay:
  xlsx:
    id_columns: [요구사항ID, 업무ID]
    actor_columns: [대상자, 사용자, Role]
    auth_columns: [권한, Profile]
    timing_columns: [주기, 일자, 시점]
    location_columns: [메뉴, 화면, 프로그램, Batch]
    object_columns: [항목, 필드, 데이터]
    action_keywords:
      조회: READ
      등록: CREATE
      저장: CREATE_OR_UPDATE
      수정: UPDATE
      삭제: DELETE
      승인: APPROVE
      마감: CLOSE
  pptx:
    process_keywords: [업무흐름, Process, AS-IS, TO-BE]
```

Core 6W/Evidence Schema는 고객마다 바꾸지 않는다.

## 6. Conflict / Staleness

서로 다른 SoP가 충돌하면:

```text
CONFLICTING_EVIDENCE
→ authority/effective/scope compare
→ human resolution
→ evidence_revision update
→ affected BR/RQ/Design STALE
→ action_permissions recalc
```

최근 문서라는 이유만으로 자동승자 처리하지 않는다.

## 7. Business Evidence Card의 새 역할

```text
Original Source
→ Extraction Package
→ Evidence Fragment
→ BR Candidate
→ Business Evidence Card (derived review/audit view)
```

즉 Card는 Traceability와 Human Review에는 유지하되 입력부담을 고객에게 전가하지 않는다.

## DECISION_REQUIRED

1. 실제 고객 PPT/XLSX에서 Format Skill의 추출 정확도가 수동분류보다 충분한가?
2. High-blast가 아닌 Low-risk BR는 어느 Authority 수준에서 자동 Confirm 후보가 될 수 있는가?
3. Visual screenshot/diagram Evidence를 Knowledge Promotion Evidence로 어디까지 인정할 것인가?
4. Source 문서 변경 시 자동 재추출 범위를 파일/Section/Item 중 어느 수준으로 할 것인가?
