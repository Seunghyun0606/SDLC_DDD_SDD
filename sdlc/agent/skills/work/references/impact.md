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
5. Project Impact Adapter 결과(명시적으로 활성화된 경우)

## 실행 계약(Agent Execution Contract)
| 항목 | 실행 규칙 |
|---|---|
| 입력 필드 | RQ/FR 또는 변경 Seed, Source Evidence, 직접 Trace, Process/BR 후보를 확인한다. Brownfield이면 공통 Impact Contract와 Project Adapter 상태를 함께 확인한다. |
| 근거 분류 | 직접 Source 관계는 OBSERVED, 정적 추론 관계는 INFERRED, 고객/업무 확인은 GIVEN/CONFIRMED로 분리한다. |
| 실행 순서 | 직접 Target 식별 → Project Adapter 실행 여부 판단 → CALLER/CALLEE → DATA/TRANSACTION → INTERFACE/EVENT → CONFIG → TEST/MODULE → Coverage Gap → Functional/Business 영향 순서로 확장한다. |
| 계속/중단 조건 | Project Adapter가 없어도 공통 Trace로 가능한 범위는 분석한다. 단 `PARTIAL_PROJECT_ADAPTER_REQUIRED`를 표시하고 완전한 Brownfield Coverage를 주장하지 않는다. Adapter가 있어도 `coverage_gaps`가 남으면 `PARTIAL_COVERAGE_GAPS`를 유지한다. |
| 출력 필드 매핑 | 각 Node/Edge에 locator/evidence/confidence/status를 기록하고 영향 상태를 DIRECT_IMPACT/INDIRECT_IMPACT/CHECK_REQUIRED/OUT_OF_SCOPE로 분류한다. |
| 품질 게이트 | 공통 Coverage dimension별 상태가 존재하고, 미탐색/미지원 영역이 coverage_gap으로 남으며, 기술 영향과 업무 영향이 분리되어야 한다. |
| 미확정/실패 처리 | `찾지 못함`은 `영향 없음`이 아니다. Dynamic/Framework-specific relation은 Project Adapter 미지원 시 CHECK_REQUIRED로 남긴다. Adapter 실행 실패/미지원은 전체 Workflow 실패가 아니라 Coverage Gap으로 기록한다. |

## Steps
1. Technical Impact Seed와 현재 Source root를 정리한다.
2. Brownfield이면 `sdlc/config/impact-adapter-profile.yaml` 또는 Project Profile에서 Adapter 설정을 확인한다.
3. `adapter.enabled: true`이고 실제 `adapter_id`/implementation이 Project에서 선택된 경우에만 해당 Adapter를 실행한다.
4. Adapter 결과의 `nodes / edges / coverage / coverage_gaps / unsupported_patterns / completion_status`를 먼저 읽는다.
5. `completion_status = PARTIAL_COVERAGE_GAPS`이면 미지원 영역을 CHECK_REQUIRED로 유지한다.
6. Adapter가 없거나 비활성화되어 있으면 Core Trace/Source Evidence로 가능한 범위만 분석하고 `PARTIAL_PROJECT_ADAPTER_REQUIRED`를 남긴다.
7. Technical Impact를 정리한다.
8. Functional Impact를 정리한다.
9. Business Impact는 별도로 판단한다. Source/Adapter 관계만으로 Business Truth를 확정하지 않는다.
10. 각 Candidate에 Evidence/Confidence/Status를 남긴다.
11. Brownfield에서는 `sdlc/design/contracts/brownfield-impact-contract.json`의 모든 Coverage dimension을 평가한다.

## Output
- Business/Functional/Technical Impact
- Impact graph + Coverage/Coverage Gap
- Project Adapter result reference(사용한 경우)
- Template: `sdlc/templates/core/impact-analysis.md`

## Quality Check
- 세 Impact 층이 분리되는가
- Source relation만으로 Business Impact를 확정하지 않았는가
- Project Adapter가 없는데 COMPLETE로 표시하지 않았는가
- Project Adapter가 있어도 Coverage Gap을 숨기지 않았는가
- `available_pilots`를 자동 활성화로 오인하지 않았는가

## Alert Conditions
- CHECK_REQUIRED 영향
- Low confidence 후보
- 외부 Consumer 불명
- Project-specific Impact Adapter 미구현/미설정
- Adapter `PARTIAL_COVERAGE_GAPS`
- Adapter unsupported pattern

## Token Strategy
Direct relation과 고신뢰 후보부터 확장한다. Adapter의 전체 Node/Edge를 무조건 LLM Context에 넣지 말고 Target 주변 관계와 Coverage Gap부터 사용한다.

## Do Not
- 기술 의존성을 업무 영향으로 자동 승격하지 않는다.
- 일부 불확실성 때문에 전체 분석을 중단하지 않는다.
- Core 공통 Impact Contract를 프로젝트별 탐색 구현으로 오인하지 않는다.
- Project Pilot Adapter를 모든 Java/Spring/MyBatis 프로젝트에 자동 적용하지 않는다.
- static Pilot 결과를 runtime call graph 또는 Production 완전성으로 표현하지 않는다.
