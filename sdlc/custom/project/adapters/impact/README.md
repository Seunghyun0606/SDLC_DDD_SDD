# Project Impact Adapter 구현 위치

이 디렉터리는 Brownfield 프로젝트의 언어/Framework/DB/메시징 특성에 맞는 영향 관계 탐색기를 구현하는 **Project Custom 영역**이다. 이 디렉터리의 구현은 Core capability가 아니며 프로젝트 특성에 맞게 선택·교체한다.

## Core와 Project 책임 분리
Core가 제공하는 것:
- `sdlc/design/contracts/brownfield-impact-contract.json`
- 공통 Node/Edge 어휘
- Coverage dimension
- Adapter 출력 계약
- `찾지 못함 != 영향 없음` 규칙
- Adapter가 없을 때 `PARTIAL_PROJECT_ADAPTER_REQUIRED` 판정

Project에서 별도 구현해야 하는 것:
- Java/Spring, .NET, Node 등 언어/Framework별 Symbol/Call 관계
- JPA/MyBatis/JDBC/ORM 및 SQL/Table lineage
- Stored Procedure/Trigger/ETL
- Kafka/JMS/Event/외부 API 연결
- Reflection/Dynamic dispatch/Runtime wiring
- 프로젝트 고유 Config/Feature Flag/Scheduler 해석

## 현재 포함된 Pilot Adapter

### Java/Spring/MyBatis 정적 Pilot
- Adapter ID: `JAVA_SPRING_MYBATIS_STATIC_PILOT_V0_1`
- 구현: `java_spring_mybatis.py`
- 상태: `PILOT_PARTIAL_COVERAGE`
- 기본 자동 활성화: **아니오**
- 검증 기준: `sdlc/validation/pilot/source-fixture/`의 simulated source fixture

실행 예:
```bash
python sdlc/custom/project/adapters/impact/java_spring_mybatis.py \
  --source-root <repository-or-source-root> \
  --out <impact-result.json>
```

현재 Pilot이 실제로 수행하는 범위:
- Java class/method `SOURCE_SYMBOL` 후보 추출
- 명시적 field receiver의 직접 `receiver.method(...)` 호출에 대한 CALLER/CALLEE 후보 추출
- Spring `@GetMapping/@PostMapping/.../@RequestMapping` method annotation이 있으면 `ENTRY_POINT`를 `HIGH / OBSERVED`로 생성
- Spring annotation이 없고 `*Controller` naming만 있으면 `ENTRY_POINT`를 `MEDIUM / CHECK_REQUIRED` 후보로 생성
- MyBatis mapper namespace와 statement를 `SOURCE_SYMBOL`로 생성
- SELECT/FROM/JOIN 및 INSERT/UPDATE/DELETE/MERGE의 Table READS/WRITES 정적 후보 추출
- `CREATE TABLE`이 있는 `.sql` 파일을 `DATA_ASSET` 근거로 연결
- Core contract의 모든 Coverage dimension을 출력하고, 분석하지 못한 영역을 `coverage_gaps`로 보고

현재 Pilot이 **수행하지 않는 범위**:
- Java compiler/AST/type solver 수준의 완전한 call graph
- interface/overload/generic/lambda/method reference의 정밀 해석
- Spring bean container, proxy, AOP, runtime wiring
- Reflection/Dynamic dispatch
- `@Transactional` propagation/실제 transaction boundary
- JPA/JDBC/Stored Procedure/Trigger/ETL lineage
- Feign/WebClient/RestTemplate 등 외부 API 계약
- Kafka/JMS/Event 관계
- Config/Profile/Feature Flag/Scheduler
- Maven/Gradle dependency graph의 의미 분석
- Test coverage 의미 분석
- 업무 영향 또는 Business Truth 확정

따라서 이 Adapter 결과에 일부 관계가 존재해도 Brownfield 영향분석 전체를 `COMPLETE`로 판정하지 않는다. Coverage Gap이 있으면 `PARTIAL_COVERAGE_GAPS`를 유지한다.

## 구현 계약
Adapter는 `brownfield-impact-contract.json`의 `adapter_output_contract`를 만족해야 한다.
최소 출력:
- adapter_id / project_context
- nodes / edges
- coverage / coverage_gaps
- unsupported_patterns

Adapter를 구현하지 않은 상태에서도 일반 SDLC Workflow는 중단하지 않는다. 다만 Brownfield 영향분석 결과는 COMPLETE로 표시할 수 없다.

## Project 적용 원칙
1. `sdlc/config/impact-adapter-profile.example.yaml`의 기본값은 계속 `enabled: false`다.
2. 실제 프로젝트에 적용하기 전에 Source 구조와 Framework 사용방식이 Pilot 지원범위에 맞는지 확인한다.
3. 지원하지 않는 Framework/패턴은 `coverage_gaps`/`unsupported_patterns`로 남기며 “관계 없음”으로 바꾸지 않는다.
4. Project에 맞는 Adapter를 추가하거나 교체하더라도 Core contract의 Node/Edge/Coverage 출력 경계를 유지한다.
5. Pilot fixture PASS는 실제 Production Repository의 정확도/완전성을 의미하지 않는다.
