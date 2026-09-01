# End-to-End Runtime Flow

## 0. Onboarding

입력:
- project-onboarding.yaml
- Business Source Manifest
- Glossary
- Artifact Selection
- Source Profile
- Customer PPT/XLSX/Word/PDF
- Brownfield Repository/Snapshot

기본 실행모드: `PROPOSAL_ONLY`.

## 1. Business Source Extraction

Starter Pack의 SoP Extraction Skill로 원문 구조를 보존한다.

```text
PPT: Slide/Shape/Table/Note
XLSX: Sheet/Cell/Merged/Header/Legacy ID
Word/PDF: Section/Page/Table
```

Output:
- Evidence Fragment
- 6W Candidate
- RQ/FR/BR/UI/Data/Integration Candidate
- OPEN/Question

## 2. Candidate A — Business Definition

```text
Raw Evidence
→ Topic/RQ Boundary
→ Scenario별 6W
→ RQ/FR/BR/AC
→ Process
→ Customer Functional Specification
```

고객이 검토하는 핵심:
- 누가/언제/어디서/무엇을/어떻게/왜
- AS-IS / TO-BE
- Rule / Exception
- UI/업무 접점
- Scope / Out of Scope
- Acceptance Criteria
- Open Decision

## 3. Brownfield Discovery

Starter Source Analysis Skill + Source Profile을 이용한다.

```text
JSP/Controller
→ Service
→ Mapper Interface
→ Mapper XML
→ Oracle Table/Procedure/Code Master
```

Output:
- Current Source Evidence
- PGM/ART/DATA/CODE Candidate
- Call/transaction/data-flow
- Similar implementation pattern
- Blind spot / dynamic behavior
- Skill Candidate

## 4. Candidate A — Engineering Design

6W/RQ/BR/AC + Current Source Evidence로 Development Blueprint를 생성한다.

필수 영역:
- Screen/Layout/Field
- CRUD
- Core Business Logic / Decision Table
- Validation/State/Error
- Integration
- Query/Data/Key/Lock
- Common Code
- Transaction/Auth/Audit
- Current Source Mapping
- Test Mapping

`Development Context Pack`은 상세설계가 아니라 위 Artifact들의 Manifest/Index다.

## 5. Candidate B — Evidence Overlay

각 중요 값에 다음을 붙인다.

```yaml
value: ...
truth: GIVEN|OBSERVED|INFERRED|CONFIRMED|OPEN
evidence: ...
revision: ...
freshness: ...
authority: ...
```

계산:
- completeness
- quality
- blind_spot
- contradiction
- assumption debt
- action_permissions

## 6. Source-ready Execution Gate

```text
Development Blueprint
+ Current Source Evidence
+ Project Convention Skill
+ Target Write Proof
+ PGM Lane
+ Work Unit
= Draft Source Write Eligibility
```

기본 권한:
- analysis/customer/design draft: ALLOW
- patch proposal: ALLOW when target known
- actual source write: DENY until guards pass
- merge/release: DENY until test/verify gates pass

## 7. Development / Recovery

```text
PREPARED
→ APPLIED
→ VERIFIED
→ COMMITTED
```

Crash/Retry:

```text
existing idempotency key
→ Work Unit state 확인
→ source fingerprint 확인
→ APPLIED이면 patch 재적용 금지
→ RESUME_VERIFY
```

Same PGM:
- planning/analysis는 병렬 가능
- actual mutation은 PGM Write Lane으로 직렬화

## 8. Test / Verify

A의 AC/Test Mapping과 B의 실행 Evidence를 결합한다.

```text
AC
→ TC
→ Executed Result
→ Source/Runtime Evidence
→ Verify
```

최종 상태:
- VERIFIED: 실제 Evidence 충족
- TESTED_WITH_GAPS: 일부 실행/Blind Spot 존재
- NOT_READY: 필수 Evidence 미충족

## 9. Knowledge Promotion

BR/Source Pattern/Operational Finding을 바로 K1/K2로 올리지 않는다.

- Scope
- Authority
- Effective Period
- Freshness
- Contradiction
- Blast Radius

검증 후 Promotion한다.

## 10. Change Request

변경 발생 시 처음부터 전체를 재작성하지 않는다.

업무 의미 변경은 6W/BR/AC부터, 기술 변경은 Impact/Blueprint부터 시작한다. 영향을 받는 downstream artifact는 `STALE`, 영향 없는 상위 artifact는 `UNCHANGED`로 표시한다.
