# Brownfield First Prompt

이 Repository는 기존 시스템 기반 Brownfield 프로젝트다.

1. `project_bootstrap`과 `SOURCE_INVENTORY` 결과를 먼저 확인한다.
2. 전체 Repository를 무제한 Scan하지 않는다. 현재 Requirement에 필요한 범위만 Bounded Trace한다.
3. README/Architecture/Build/Test/Data/Interface/Standard 후보를 Evidence Source로 목록화한다.
4. Source에서 관찰한 Coding/Architecture/Transaction/Error 패턴은 `OBSERVED`로 기록한다.
5. Source Behavior를 Business Truth로 자동 승격하지 않는다.
6. Java/Spring, SQL/Procedure/Trigger, Batch/Scheduler, Interface 등 필요한 Analyzer가 `UNCONFIGURED`이면 OPEN Item으로 남긴다.
7. 확인할 수 없는 정보는 OPEN으로 유지하고 이름 유사성만으로 PGM/BR 관계를 CONFIRMED하지 않는다.
8. Requirement 작성에 필요한 Evidence가 충분한지 판단한다.
9. 현재 Requirement가 있으면 DISCOVERY 또는 INTAKE Stage Input Pack을 생성한다.
10. Source write, DB write, Canonical publish 같은 부작용 Action은 명시적 요청과 revision/permission/idempotency proof 없이는 실행하지 않는다.
11. 다음 Human Decision과 다음 실행 가능한 작업을 정리한다.
