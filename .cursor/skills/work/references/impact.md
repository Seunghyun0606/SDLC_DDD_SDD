# Impact Reference

## Purpose
Technical relation과 Business impact를 분리하고 confidence/status/evidence를 기록한다.

## Required Input
- Stage: `IMPACT`
- RQ/FR + Trace + Source Evidence

## Optional Input
- Process/BR/Knowledge/Overlay
- `sdlc/config/impact-adapter-profile.yaml`

## Retrieval Strategy
1. Direct Canonical relation
2. Trace graph
3. Relevant symbol/data evidence
4. 영향 Consumer/Caller 후보
5. Project Impact Adapter 결과(제공된 경우)

## 실행 계약(Agent Execution Contract)
| 항목 | 실행 규칙 |
|---|---|
| 입력 필드 | RQ/FR 또는 변경 Seed, Source Evidence, 직접 Trace, Process/BR 후보를 확인한다. Brownfield이면 공통 Impact Contract와 Project Adapter 상태를 함께 확인한다. |
| 근거 분류 | 직접 Source 관계는 OBSERVED, 정적 추론 관계는 INFERRED, 고객/업무 확인은 GIVEN/CONFIRMED로 분리한다. |
| 실행 순서 | 직접 Target 식별 → CALLER/CALLEE → DATA/TRANSACTION → INTERFACE/EVENT → CONFIG → TEST/MODULE → Coverage Gap → Functional/Business 영향 순서로 확장한다. |
| 계속/중단 조건 | Project Adapter가 없어도 공통 Trace로 가능한 범위는 분석한다. 단 `PARTIAL_PROJECT_ADAPTER_REQUIRED`를 표시하고 완전한 Brownfield Coverage를 주장하지 않는다. |
| 출력 필드 매핑 | 각 Node/Edge에 locator/evidence/confidence/status를 기록하고 영향 상태를 DIRECT_IMPACT/INDIRECT_IMPACT/CHECK_REQUIRED/OUT_OF_SCOPE로 분류한다. |
| 품질 게이트 | 공통 Coverage dimension별 상태가 존재하고, 미탐색/미지원 영역이 coverage_gap으로 남으며, 기술 영향과 업무 영향이 분리되어야 한다. |
| 미확정/실패 처리 | `찾지 못함`은 `영향 없음`이 아니다. Dynamic/Framework-specific relation은 Project Adapter 미지원 시 CHECK_REQUIRED로 남긴다. |

## Steps
1. Technical Impact를 정리한다.
2. Functional Impact를 정리한다.
3. Business Impact는 별도로 판단한다.
4. 각 Candidate에 Evidence/Confidence/Status를 남긴다.
5. Brownfield에서는 `sdlc/design/contracts/brownfield-impact-contract.json`의 Coverage를 평가한다.
6. 실제 언어/Framework/DB/메시징 관계 탐색은 `sdlc/custom/project/adapters/impact/`의 프로젝트별 Adapter 책임으로 둔다.

## Output
- Business/Functional/Technical Impact
- Impact graph + Coverage/Coverage Gap
- Template: `sdlc/templates/core/impact-analysis.md`

## Quality Check
- 세 Impact 층이 분리되는가
- Source relation만으로 Business Impact를 확정하지 않았는가
- Project Adapter가 없는데 COMPLETE로 표시하지 않았는가

## Alert Conditions
- CHECK_REQUIRED 영향
- Low confidence 후보
- 외부 Consumer 불명
- Project-specific Impact Adapter 미구현/미설정

## Token Strategy
Direct relation과 고신뢰 후보부터 확장한다.

## Do Not
- 기술 의존성을 업무 영향으로 자동 승격하지 않는다.
- 일부 불확실성 때문에 전체 분석을 중단하지 않는다.
- Core 공통 Impact Contract를 프로젝트별 탐색 구현으로 오인하지 않는다.
