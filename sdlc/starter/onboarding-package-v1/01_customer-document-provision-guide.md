# 01. 고객 문서 제공 가이드

## 목적
비정형 고객문서를 **원본 보존 + 최소 Metadata** 방식으로 제공한다. 고객에게 모든 문서를 BR/RQ 형식으로 사전 재작성하도록 요구하지 않는다.

## 권장 제공 문서

| 우선 | 문서 | 기대 정보 |
|---|---|---|
| P0 | 요구사항 XLSX/Word | 변경 요구, 기능 범위 |
| P0 | 업무정책/규정 | Rule, 예외, Authority |
| P0 | 업무 Process/SoP | Actor, Trigger, Process, Decision |
| P1 | 화면/기능정의 | 메뉴, 필드, CRUD, Validation |
| P1 | 운영매뉴얼 | 현행 사용흐름, 예외 |
| P1 | 데이터/코드 정의 | Table/Column/Code 의미 |
| P2 | 기존 설계서 | Legacy Design |
| P2 | 회의록 | 미확정 합의/질문 |
| P2 | 장애/문의사례 | 예외/현행 문제 |

## 원본 보존
- 원본 파일명 유지 권장
- 가공본은 `_normalized`, `_translated`, `_redacted`
- Secret 제거
- 개인정보/민감정보는 정책에 맞게 마스킹
- 스캔 PDF는 가능하면 원본 Office 파일도 제공

## 파일별 Extraction

### XLSX
- Sheet/Header/Merged Cell
- Legacy ID
- 대상자/권한
- 주기/Trigger
- 요구사항/CRUD
- 메뉴/Program
- 상태/예외
- Code/Table/Interface
- Locator: `Sheet!Cell`

### PPT/PPTX
- Slide/Section
- Actor
- Process/Decision
- AS-IS/TO-BE
- Screenshot Field/Button
- 연계
- Speaker Notes
- Locator: `Slide N / Shape/Table`

### Word/PDF
- Heading/Page/Section
- 정책 문장
- 조건/예외
- 승인/책임주체
- 변경이력

## 문서만으로 알 수 없는 것은 OPEN
- 메뉴명 없음 → `Where=OPEN`
- 실제 Role/Profile ID 없음 → `auth_profile=OPEN`
- 업무상태명이 있어도 DB 실제 Code 없음 → `actual_code=OPEN`
- 회의록 제안 → 자동 `CONFIRMED BR` 금지

## Authority
- `A1_OFFICIAL_APPROVED`
- `A2_OWNER_CONFIRMED`
- `A3_PROJECT_AGREED`
- `A4_LEGACY_DOCUMENT`
- `A5_INFORMAL_REFERENCE`

Authority가 높아도 Scope/Effective Period가 없으면 확인이 필요하다.

## 고객 Checklist
- [ ] 원본 파일
- [ ] Owner/부서
- [ ] 문서 유형
- [ ] 공식/참고 여부
- [ ] 적용 회사/국가/업무
- [ ] 유효기간
- [ ] 구버전 대체관계
- [ ] 기밀등급
- [ ] 중요 Section/Sheet
- [ ] 확인 담당자
