# TEMPLATE / 산출물 가이드

## Quick Start

산출물은 사용자가 빈 문서부터 작성하는 것이 아니라 Agent 초안을 검토·수정하는 것을 기본으로 한다.

```mermaid
flowchart LR
    I[입력/Canonical] --> T[Template] --> A[Agent Draft] --> H[Human Review] --> O[Current Artifact]
```

## 파일명 규칙

`<대표ID>_<짧은업무명>_<산출물종류>.<확장자>`

예: `RQ-0042_휴가취소근태반영_영향분석.md`

## Template 공통 Section

1. 문서 목적
2. 30초 요약
3. Workflow
4. 입력/Evidence
5. 본문
6. 미확정/Alert/Assumption
7. 관련 ID/Traceability
8. 다음 작업

## 주요 산출물

| 산출물 | 목적 | 대표 파일명 |
|---|---|---|
| 요구사항 | 한 RQ를 빠르게 이해 | `RQ-xxxx_업무명_요구사항.md` |
| 요구분석 | FR/BR 후보/AC/질문 | `RQ-xxxx_업무명_요구분석.md` |
| 프로세스분석 | AS-IS/TO-BE 업무 흐름 | `RQ-xxxx_업무명_프로세스분석.md` |
| 영향분석 | Business/Functional/Technical 영향 | `RQ-xxxx_업무명_영향분석.md` |
| 기능설계 | 목표 시스템 동작 | `RQ-xxxx_업무명_기능설계.md` |
| 프로그램설계 | 개발 대상 PGM 상세 | `PGM-xxxx_업무명_프로그램설계.md` |
| 구현결과 | 실제 Source 변경 결과 | `RQ-xxxx_업무명_구현결과.md` |
| 검증결과 | AC/TC/PGM 기준 최종 검증 | `RQ-xxxx_업무명_검증결과.md` |
| 전체작업목록 | PM/작업자 공통 Work List | `전체작업목록.md/.xlsx` |
