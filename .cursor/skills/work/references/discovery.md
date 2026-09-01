# Discovery Reference

## Purpose
Static Analysis First로 관련 Source/Symbol/Data 후보와 Evidence locator를 수집한다.

## Required Input
- Stage: `DISCOVERY`
- RQ/FR + Source Profile + Repository

## Optional Input
- 기존 Trace/Program Summary/Knowledge/Overlay
- Brownfield Impact Adapter Profile

## Retrieval Strategy
1. 기존 Index/Trace/Program Summary
2. Symbol/Mapper/DB/Interface candidate
3. Relevant source snippet
4. 필요한 경우에만 full file

## 실행 계약(Agent Execution Contract)
| 항목 | 실행 규칙 |
|---|---|
| 입력 필드 | RQ/FR 또는 분석 Seed, Repository 기준점, Source Profile을 확인한다. Brownfield에서 Repository 기준점이 없으면 실제 Source 분석으로 확정하지 않는다. |
| 근거 분류 | 파일/심볼/SQL/설정에서 직접 확인한 사실은 OBSERVED, 이름·근접성 기반 연결은 INFERRED, 사용자 제공 설명은 GIVEN/CONFIRMED로 분리한다. |
| 실행 순서 | Source root/제외경로 확인 → Build/Module 자산 인덱싱 → Seed 관련 후보 검색 → Locator/Hash 확보 → 직접 관계 확장 → Coverage Gap 기록 순서로 수행한다. |
| 계속/중단 조건 | 일부 Source root/build 정보가 없어도 탐색 가능한 범위는 계속한다. Repository가 없거나 읽을 수 없으면 `OPEN_REAL_SOURCE`로 남긴다. |
| 출력 필드 매핑 | Artifact/Symbol/Data Candidate, locator, source_hash, confidence, status, retrieval_method, coverage_gap을 Trace/Evidence에 기록한다. |
| 품질 게이트 | 모든 OBSERVED 후보에 실제 locator/hash가 있고, 추론 후보와 분리되며, 탐색하지 못한 영역이 Coverage Gap으로 표시되어야 한다. |
| 미확정/실패 처리 | 동적 호출/Reflection/Procedure/외부 Consumer 등 미지원 패턴은 `CHECK_REQUIRED`/coverage_gap으로 남기며 `찾지 못함=없음`으로 결론내리지 않는다. |

## Steps
1. Source Profile의 roots/excludes를 적용한다.
2. 후보 Artifact/Symbol/Data를 수집한다.
3. Locator/Source Hash/Confidence/Status를 기록한다.
4. Business 의미는 Candidate로 유지한다.
5. Brownfield에서는 `brownfield-impact-contract.json`의 공통 Coverage 항목을 기록하되 실제 프로젝트별 관계 해석은 Project Impact Adapter가 담당한다.

## Output
- Trace/Program/Data candidates
- Coverage Gap
- Template: `sdlc/templates/core/impact-analysis.md`

## Quality Check
- Source Evidence locator가 있는가
- Candidate와 CONFIRMED가 분리되는가
- Brownfield에서 Project Adapter가 없으면 `PARTIAL_PROJECT_ADAPTER_REQUIRED`로 표시되는가

## Alert Conditions
- Source/Profile 불완전
- Trace 충돌
- Target ambiguity
- Project-specific Impact Adapter 미구현/미설정

## Token Strategy
Static Analysis/Index 결과로 후보를 줄인 후 Source를 읽는다.

## Do Not
- Repository 전체를 LLM으로 먼저 읽지 않는다.
- Source 구현을 Business Rule로 자동 확정하지 않는다.
- Core 공통 계약만으로 언어/Framework별 Call Graph가 완전하다고 주장하지 않는다.
