# 05. Template-driven SoP Extraction Contract

## Status

`ENHANCED / PARTIALLY_SUPERSEDES 03_business_source_package_and_br_normalization.md`

기존 `Business Source Card` 개념은 폐기하지 않지만 **고객이 작성하는 Primary Input** 역할은 철회한다.

```text
SUPERSEDED AS PRIMARY INPUT:
Customer → business-source-card.yaml 직접 작성

ENHANCED:
Customer Original SoP/PPT/XLSX/Word/PDF
+ 최소 Source Metadata
→ Format-aware Extraction Skill
→ SoP Extraction Package
→ 6W Business Definition Candidate
→ RQ/FR/BR/UI/Data/Integration Candidate
→ Human Clarification/Confirmation
→ Canonical
```

## 1. 왜 Skill + Template 방식이 더 적합한가

고객 문서는 이미 자체 구조와 업무맥락을 가진다. 이를 사전에 BR Card로 재작성하도록 요구하면:

- 고객 도입비용이 큼
- 원본의 화면/표/프로세스 맥락이 소실됨
- 한 문서에 여러 RQ/BR/예외가 섞인 경우 Card 작성자가 선분류 오류를 낼 수 있음
- PPT/XLSX의 구조정보를 활용하지 못함

따라서 고객에게 요구할 것은 가능한 한:

1. 원본 문서
2. 문서명/소유부서
3. 문서 성격(정책/매뉴얼/요구사항/회의록 등)
4. 승인/공식성
5. 적용범위/시행일 — 알 수 있는 경우

정도다.

## 2. Extraction Skill의 역할

Skill이 문서 Format별 Prompt를 가진다.

- XLSX: Sheet/Header/Merged Cell/Row/Cell/ID/CRUD Column
- PPTX: Slide/Process Shape/Table/Screen Capture/Notes
- DOCX/PDF: Heading/Page/Table/Footnote/Approval/Revision

그리고 공통적으로 6W를 추출한다.

```text
Who / When / Where / What / How / Why
```

6W에서 파생해 다음 Candidate를 생성한다.

- RQ/FR
- BR/Exception
- Screen/Menu/Field
- CRUD
- State/Validation
- Data/Query
- Integration
- Common Code
- Clarification Question

## 3. Business Source Card의 새 역할

Card는 Agent가 추출한 Rule Candidate의 요약/Trace View다.

즉:

```text
Original Document
→ Extraction
→ Evidence Fragment
→ BR Candidate
→ business-source-card.yaml (derived view)
```

Card를 사람이 수작업으로 먼저 만드는 것을 기본 Workflow로 하지 않는다.

## 4. Template Contract

Primary output은 `templates/sop-extraction-output.yaml`을 따른다.

모든 Item에:

- source locator
- raw text/visual reference
- 6W
- Candidate objects
- questions

를 넣는다.

## 5. Quality Gate

다음이면 Extraction은 끝났어도 Canonical Publish하지 않는다.

- Why가 OPEN이고 RQ Goal이 불명확
- Who/Profile이 OPEN인데 권한 Rule을 만들려 함
- 문서 간 정책 충돌
- Source authority가 Informal뿐임
- 적용범위/시행기간이 필요한 Rule인데 누락
- 화면 Screenshot만으로 숨은 Rule을 추정

## 6. Customizing

고객별 Customizing은 Skill의 Core Prompt를 Fork하지 않고 Profile/Template Overlay로 한다.

예:

```yaml
customer_overlay:
  xlsx:
    requirement_id_columns: [요구사항ID, Req ID]
    role_columns: [사용자, 대상자, 권한]
    menu_columns: [화면, 메뉴, 프로그램]
    action_keywords:
      조회: READ
      등록: CREATE
      수정: UPDATE
      삭제: DELETE
      승인: APPROVE
      마감: CLOSE
  pptx:
    process_slide_keywords: [업무흐름, 프로세스, AS-IS, TO-BE]
```

Core Extraction Schema와 6W Contract는 유지한다.

## DECISION_REQUIRED

실제 고객 Pilot에서 검증할 항목:

1. PPT/XLSX별 기본 Template만으로 6W 추출률이 충분한가?
2. 고객 Overlay 작성 비용이 수동 BR 정규화보다 낮은가?
3. Screenshot/Diagram 추출을 어느 수준까지 자동화할 것인가?
4. 어떤 Authority부터 BR Confirm Evidence로 인정할 것인가?
