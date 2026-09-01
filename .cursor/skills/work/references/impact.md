# Impact Reference

## Purpose
Technical relation과 Business impact를 분리하고 confidence/status/evidence를 기록한다.

## Required Input
- Stage: `IMPACT`
- RQ/FR + Trace + Source Evidence

## Optional Input
- Process/BR/Knowledge/Overlay

## Retrieval Strategy
1. Direct Canonical relation
2. Trace graph
3. Relevant symbol/data evidence
4. 영향 Consumer/Caller 후보

## Steps
1. Technical Impact를 정리한다.
2. Functional Impact를 정리한다.
3. Business Impact는 별도로 판단한다.
4. 각 Candidate에 Evidence/Confidence/Status를 남긴다.

## Output
- Business/Functional/Technical Impact
- Template: `sdlc/templates/core/impact-analysis.md`

## Quality Check
- 세 Impact 층이 분리되는가
- Source relation만으로 Business Impact를 확정하지 않았는가

## Alert Conditions
- CHECK_REQUIRED 영향
- Low confidence 후보
- 외부 Consumer 불명

## Token Strategy
Direct relation과 고신뢰 후보부터 확장한다.

## Do Not
- 기술 의존성을 업무 영향으로 자동 승격하지 않는다.
- 일부 불확실성 때문에 전체 분석을 중단하지 않는다.
