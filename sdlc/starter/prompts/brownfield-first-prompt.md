# Brownfield First Prompt

이 Repository는 기존 시스템 기반 Brownfield 프로젝트다. 별도 구두 설명 없이 아래 순서로 시작한다.

1. `sdlc/START_HERE.md` 기준으로 요구사항, Source Repository, 기준 Commit/Revision, Build/Test 정보의 존재 여부를 먼저 Inventory한다.
2. `.ai-sdlc/project-bootstrap.yaml`이 없으면 임의 Source Profile을 만들지 말고 `ai_sdlc.py init`에 필요한 입력 누락을 보고한다.
3. 실제 Git HEAD를 확인하고 분석 Evidence에 Revision을 남긴다. Revision 확인 전 Source write를 요청하지 않는다.
4. 전체 Repository를 무제한 Scan하지 않는다. README/Architecture/Build/Test/Data/Interface/Standard 후보를 먼저 확인한 뒤 현재 Requirement에 필요한 범위만 Bounded Trace한다.
5. Source에서 관찰한 Coding/Architecture/Transaction/Error/Interface 패턴은 `OBSERVED`로 기록한다. Source Behavior를 Business Truth로 자동 승격하지 않는다.
6. Java/Spring과 SQL Analyzer의 maturity/limitations를 확인한다. Interface 계약 파일이 있으면 `interface-contract` Analyzer(OpenAPI/Swagger/AsyncAPI/WSDL)를 사용한다.
7. Batch/Scheduler/동적 Runtime 관계처럼 Analyzer가 `UNCONFIGURED` 또는 지원하지 않는 영역은 OPEN/Blind Spot으로 남긴다.
8. 이름 유사성만으로 PGM/BR/Requirement 관계를 CONFIRMED하지 않는다.
9. Requirement가 있으면 INTAKE 또는 DISCOVERY Stage Input Pack을 만들고 Human Artifact Registry의 Template을 사용한다.
10. Source write 전에는 actual Git revision, Agent Branch, Parent Change Branch, Atomic Claim, Revision/Ownership Guard, Permission/Idempotency Proof를 확인한다.
11. Test가 실행되지 않았거나 Provider가 unavailable이면 PASS/Success로 기록하지 않는다.
12. 마지막에 `확인된 AS-IS Evidence / Business Truth와 구분된 추론 / OPEN / 다음 Analyzer 또는 Human Decision / 다음 실행 가능한 작업`을 정리한다.
