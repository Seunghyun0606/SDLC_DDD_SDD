# Traceability & Pilot Findings — Candidate A+

## End-to-End Trace

```text
REQ_TM_FL001 / TE001  저장/등록
REQ_TM_TE002           수정
REQ_TM_TE003~005       조회/Calendar/예상시간
REQ_TM_TE006~008       기본값
REQ_TM_TE009           알람메일
        +
PPT Slide1~6           Who/When/Where/Why/UI/Rule/Integration
        +
Brownfield Source      JSP/Service/Mapper/XML/Table/Common Code/AS-IS
        ↓
SCN-FLEX-01~03
        ↓
RQ-FLEX-PLAN-001
        ↓
FR-FLEX-01~07 / BR-FLEX-01~07 / AC-FLEX-01~08
        ↓
Customer Functional Spec
        ↓
Development Blueprint
```

## What Each Source Contributed

| Source | Strong | Weak |
|---|---|---|
| 요구사항 XLSX | 기능 Inventory, CRUD 이름, Legacy Trace | Actor/Trigger/Menu/Purpose/Rule/Data |
| PPT SoP | 6W, UI, 업무Rule, 업무연계 | Physical Source/SQL/Table Current Truth |
| Brownfield Source | Current Program/Data/Query/Common Code/AS-IS | Business Purpose/Authority |

## Important Finding 1 — 6W가 Requirement와 Development 사이의 Missing Layer를 채움

XLSX의 `10분단위 근무계획 등록`만으로는 개발자에게 업무 맥락이 부족하다. 6W Scenario로 `누가/언제/어디서/왜`가 추가되어 화면/권한/주기/연계 판단 근거가 생긴다.

## Important Finding 2 — Context Pack보다 Development Blueprint가 실제 개발입력에 적합

Manifest/YAML만으로는 Field, CRUD, Decision Table, Query, Common Code, Source Mapping이 부족했다. 상세 Blueprint가 있어야 Source-ready 판단이 가능했다.

## Important Finding 3 — Card-first보다 Extraction Skill-first가 자연스러움

고객이 BR Card를 작성하는 대신 원본 XLSX/PPT를 유지하고 Skill이 Candidate를 추출하는 방식이 도입비용이 낮고 Provenance를 유지하기 쉽다.

## Important Finding 4 — Source와 SoP가 충돌하는 경우 AS-IS/TO-BE로 구분 필요

- PPT/XLSX: 10분 단위 요구
- Current Source: 30분 단위

이는 Conflict가 아니라 `Current AS-IS vs Desired TO-BE`다.

반대로 PPT가 `삭제 가능`이라고 하고 Source/업무정책이 `삭제 금지`라면 `CONTRADICTION`으로 별도 처리해야 한다.

## Change Scenario

예: 고객이 "확정 후에도 당일 18시 전에는 수정 가능"으로 Rule을 바꾸면:

```text
PPT/CR Evidence
→ SCN-FLEX-01 How/When revision
→ BR-FLEX-05 STALE
→ Customer Spec STALE
→ Development Blueprint Decision Table STALE
→ Service Source Target STALE
→ Test Case STALE
```

XLSX Inventory 자체는 `UNCHANGED`일 수 있다.

## Candidate A+ Verdict

`USABILITY IMPROVED / NEEDS REAL DOCUMENT PARSER + REAL REPOSITORY PILOT`

추천 다음 검증:
1. 실제 고객 PPT/XLSX 1건으로 locator extraction 검증
2. 실제 JSP/MyBatis Repository에서 Source mapping 자동생성 검증
3. 개발자가 Blueprint만 읽고 Patch Proposal을 작성하는 Blind Test