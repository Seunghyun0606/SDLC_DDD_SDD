# SOP / Business Document Extraction Skill

## Purpose
고객이 제공한 SOP, 업무규정, 운영매뉴얼, 요구자료, 회의자료 등의 Evidence Chunk를 읽고 업무 분석/설계에 사용할 Candidate를 일관된 항목으로 추출한다.

이 Skill은 PPTX/XLSX/PDF 자체를 파싱하는 도구가 아니다. 포맷별 Adapter가 `br-document-extraction-contract.json` 형식으로 제공한 Evidence Chunk를 입력으로 사용한다.

## Required Input
- `document_id`
- 원본 문서 메타데이터(가능한 범위)
- `content_kind`, `locator`, `raw_text`, `source_hash`, `extraction_status`
- 표/슬라이드/셀 구조가 있으면 `structured_content`, `format_context`

## Optional Input
- 문서 authority / lifecycle / effective period
- 고객 용어집
- 기존 RQ/FR/BR/PROC/PGM
- Project/Domain Overlay

## 사전 추출 Prompt
다음 지침을 순서대로 적용한다.

1. 원문에서 명시적으로 확인되는 사실만 추출한다. 빠진 정보는 추측하지 말고 `OPEN`으로 둔다.
2. 업무 시나리오마다 6하원칙을 확인한다.
   - 누가(Who): 사용자/역할/프로파일/권한/대상자
   - 언제(When): Trigger/주기/시점/마감/유효기간
   - 어디서(Where): 시스템/메뉴/화면/채널/업무 단계
   - 무엇을(What): 업무 객체/입력값/대상 데이터/결과
   - 어떻게(How): 절차/행위/CRUD/검증/승인/상태변화
   - 왜(Why): 업무 목적/정책 근거/법적·운영 의무/기대 결과
3. 조건-판단-행동-결과-예외 형태의 문장을 Business Rule Candidate로 분리한다.
4. 순서가 있는 단계는 Process Candidate로 분리하고 Actor/Trigger/Pre-State/Post-State를 찾는다.
5. 표/양식/화면 설명에서는 Field, 필수 여부, 코드값, 계산식, Validation, 표시 조건을 추출한다.
6. 코드표/분류표에서는 **공통코드/코드 그룹**, 코드값, 명칭, 유효기간, 우선순위를 추출한다.
7. 승인/반려/취소/마감/확정 등은 상태 전이와 권한 조건으로 추출한다.
8. 외부 시스템·배치·메시지·파일·API가 언급되면 Integration Candidate로 추출한다.
9. 예외, 재처리, Escalation, Deadline, SLA, 감사·통제 조건을 별도 항목으로 추출한다.
10. 서로 다른 문서 또는 같은 문서 내 상충 내용은 하나로 합치지 말고 `CONFLICT` 후보로 만든다.
11. 모든 Candidate에는 `document_id + locator + source_hash + confidence`를 붙이고 원문과 정규화 문장을 모두 보존한다.
12. Source/SOP에서 추출됐다는 이유만으로 `CONFIRMED_BR`로 승격하지 않는다. 문서 권위 또는 사람의 확인이 필요하다.

## 실행 계약(Agent Execution Contract)
| 항목 | 실행 규칙 |
|---|---|
| 입력 필드 | Evidence Chunk와 문서 메타데이터를 사용한다. 원본 파일 자체를 임의 변환하거나 수정하지 않는다. |
| 근거 분류 | 문서에 직접 있는 내용은 GIVEN/OBSERVED_DOCUMENT, 구조적 연결은 INFERRED, 비어 있는 항목은 OPEN으로 둔다. |
| 실행 순서 | 문서 맥락 → 6W 시나리오 → Actor/권한 → 절차 → BR → 상태/예외 → Data/공통코드 → Screen → Integration → Control/SLA → Conflict/Question 순서로 추출한다. |
| 계속/중단 조건 | 일부 Chunk 추출 실패는 PARTIAL로 계속한다. 문서 전체가 읽히지 않으면 `EXTRACTION_REQUIRED`로 종료하고 규칙 부재로 해석하지 않는다. |
| 출력 필드 매핑 | SCENARIO/PROC/BR/FR/DATA/SCREEN/INTEGRATION/CLARIFICATION Candidate와 provenance를 출력한다. |
| 품질 게이트 | 모든 Candidate가 원문 Locator로 돌아갈 수 있고, 6W 누락은 OPEN이며, 표/셀 관계가 가능한 한 보존되어야 한다. |
| 미확정/실패 처리 | OCR/구조 손실은 PARTIAL, 모순은 CONFLICT, 권위 미확정 규칙은 REVIEW_REQUIRED로 둔다. |

## Output
- Template: `sdlc/templates/core/sop-extraction-result.md`
- Canonical에 바로 확정하지 않고 Candidate Set을 생성한다.

## Quality Check
- 원문과 정규화 문장이 모두 남아 있는가
- 6하원칙 중 누락을 추측으로 채우지 않았는가
- 표/슬라이드/XLSX의 구조적 의미를 평문으로 손실시키지 않았는가
- Business Rule과 단순 시스템 구현 관찰을 구분했는가
- 충돌/미확정을 숨기지 않았는가

## Do Not
- PPTX/XLSX/PDF parser 구현을 이 Skill의 책임으로 간주하지 않는다.
- Source/SOP 문장을 자동으로 최종 Business Truth로 승격하지 않는다.
- 문서에 없는 화면, 테이블, 코드, 업무 목적을 발명하지 않는다.
