# /work

현재 대상(RQ/PGM/TASK)의 다음 실행 가능한 단계를 선택하고 해당 Reference Contract를 수행한다.

## 단계 흐름
`INTAKE → DECOMPOSE → CLARIFY → PROCESS → DISCOVERY → IMPACT → DESIGN → PROGRAM → DEVELOPMENT → TEST → VERIFY → KNOWLEDGE PROMOTION`

## 문서 대상(Audience)
- `internal`: 설계/개발용 내부 산출물만 생성한다.
- `customer`: 기존 내부 산출물/Canonical을 근거로 고객 커뮤니케이션 View를 생성한다.
- `both`: 내부 산출물을 먼저 갱신한 뒤 고객 View를 파생한다.
- 고객 View에서 새 업무 사실을 만들지 않는다. 고객 협의 결과가 바뀌면 `/change` 또는 현재 `/work` Stage로 Canonical에 반영한다.

## 작성 원칙
- 사용자에게 보이는 본문은 한국어 자연어를 기본으로 한다.
- RQ/FR/BR/PGM/AC/TC 등은 첫 등장 시 한국어 명칭을 함께 적는다.
- 같은 업무정보를 여러 단계 문서에 복사하지 않는다. 이전 단계에서 확정된 내용은 ID/Section/Version으로 참조하고 현재 단계에서 새로 결정되는 Delta만 작성한다.
- 단계 전체를 승인 대기로 막지 않는다. 미확정 사항은 주의/가정/OPEN으로 이월한다.
- **OPEN은 대기표시가 아니라 해소할 설계 Backlog다.** CLARIFY/DESIGN/PROGRAM에서 OPEN이 발견되면 `.cursor/skills/open-resolve/SKILL.md`와 `open-resolution-contract.json`을 사용한다.
- 사람에게 보이는 OPEN 상태는 `미확정 / 확인중 / 제안 / 확정 / 보류`를 기본으로 한다. `Decision Domain`, `Basis Class`, 내부 상태 코드는 Machine metadata로 유지하고 사용자의 필수 입력으로 만들지 않는다.
- SOP는 선택 Evidence다. SOP가 없어도 인터뷰/현행분석/Source·Data 분석/Project Standard/설계·개발 제안으로 진행한다.
- 설계자/개발자 경험으로 채운 값은 Proposal로 기록하며 Business Truth로 자동 확정하지 않는다.
- Project Authority Profile이 허용하는 기술/Data/Integration 결정은 고객 승인 없이 내부적으로 `ACCEPTED_DESIGN`으로 해소할 수 있다. Business 정책/목적은 업무 권한자가 확인해야 `CONFIRMED_BUSINESS`가 된다.
- Source가 연결된 경우 DISCOVERY 이후에는 가능한 위치(파일/심볼/라인/Locator)와 Source Hash를 Machine provenance로 남긴다.
- Source write 전 Target confidence와 Execution Guard를 확인한다.
- Output은 Canonical relation을 갱신하고 해당 Template 기반 Artifact를 생성/갱신한다.
- 모든 Stage Reference의 `## 실행 계약(Agent Execution Contract)`을 실행 지침으로 사용한다. 저수준 Agent가 임의 순서를 만들지 않고 `입력 필드 → 근거 분류 → 실행 순서 → 계속/중단 → 출력 매핑 → 품질 게이트 → 미확정/실패 처리`를 따른다.
- 공통 실행계약은 `sdlc/design/contracts/agent-execution-contract.json`을 따른다.
- PROCESS/DESIGN에서는 `business-scenario-sixw-contract.json`의 누가/언제/어디서/무엇을/어떻게/왜를 업무 기준으로 유지한다. 누락은 OPEN으로 두고 발명하지 않는다.
- PROGRAM에서는 6W를 다시 작성하지 않고 Functional Design의 SCN/Section을 참조한다.
- DESIGN은 `developer-spec-contract.json`에 따라 화면/필드/CRUD/핵심 업무규칙/논리 Data/Integration/권한/예외/AC의 **의미상 Source of Truth**를 만든다.
- PROGRAM은 Functional Design을 반복하지 않고 실제 PGM/Entry Point/Source Symbol, Field→DTO/API/DB Mapping, Query/Table/Column, Transaction, Integration 기술계약, Error/Security/Observability, TASK/AC/TC/Source 및 구현 준비도만 추가한다.
- 17개 Program DoR는 17개 별도 Section이 아니라 `program-spec.md`의 단일 구현 준비도 표에서 관리한다.
- SOP/업무규정/운영매뉴얼/PPTX/XLSX 등 고객 문서가 있으면 포맷 Adapter의 구조 보존 Evidence Chunk를 우선 만들고 `.cursor/skills/sop-extract/SKILL.md`를 사용해 SCN/PROC/BR/FR/Data/Screen/Integration Candidate를 추출한 뒤 PROCESS/DESIGN 입력으로 사용한다.
- 프로젝트 고유 탐색/Framework 해석과 포맷별 Parser 구현은 Core Reference에 발명하지 않고 Project Profile/Adapter에서 제공한다.
- `detect_source_drift.py`는 Source Drift와 Reverse Review Candidate 기능이며 전체 Reverse Engineering 또는 문서 자동 재작성 기능으로 표현하지 않는다.

## References
- `references/requirement.md`
- `references/clarify.md`
- `references/process.md`
- `references/discovery.md`
- `references/impact.md`
- `references/design.md`
- `references/program.md`
- `references/development.md`
- `references/test.md`
- `references/verify.md`
