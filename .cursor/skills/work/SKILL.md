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
- 단계 전체를 승인 대기로 막지 않는다. 미확정 사항은 주의/가정/OPEN으로 이월한다.
- Source가 연결된 경우 DISCOVERY 이후에는 가능한 위치(파일/심볼/라인/Locator)와 Source Hash를 남긴다.
- Source write 전 Target confidence와 Execution Guard를 확인한다.
- Output은 Canonical relation을 갱신하고 해당 Template 기반 Artifact를 생성/갱신한다.
- 모든 Stage Reference의 `## 실행 계약(Agent Execution Contract)`을 실행 지침으로 사용한다. 저수준 Agent가 임의 순서를 만들지 않고 `입력 필드 → 근거 분류 → 실행 순서 → 계속/중단 → 출력 매핑 → 품질 게이트 → 미확정/실패 처리`를 따른다.
- 공통 실행계약은 `sdlc/design/contracts/agent-execution-contract.json`을 따른다.
- PROCESS/DESIGN/PROGRAM에서는 `business-scenario-sixw-contract.json`의 누가/언제/어디서/무엇을/어떻게/왜를 업무 기준으로 유지한다. 누락은 OPEN으로 두고 발명하지 않는다.
- DESIGN/PROGRAM에서는 `developer-spec-contract.json`에 따라 화면/필드/CRUD/핵심 로직/Query·Data/Common Code/Integration/권한/예외를 `RESOLVED / OPEN / N/A(사유)`로 관리한다.
- SOP/업무규정/운영매뉴얼/PPTX/XLSX 등 고객 문서가 있으면 포맷 Adapter의 구조 보존 Evidence Chunk를 우선 만들고 `.cursor/skills/sop-extract/SKILL.md`를 사용해 SCN/PROC/BR/FR/Data/Screen/Integration Candidate를 추출한 뒤 PROCESS/DESIGN 입력으로 사용한다.
- 프로젝트 고유 탐색/Framework 해석과 포맷별 Parser 구현은 Core Reference에 발명하지 않고 Project Profile/Adapter에서 제공한다.

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
