# Project Impact Adapter

Brownfield 프로젝트의 언어/Framework/DB/메시징 관계 탐색은 **Project Custom 영역**이다. Core는 공통 Node/Edge/Coverage 계약과 `찾지 못함 != 영향 없음` 규칙만 제공한다.

## 포함 Adapter

### 1. Java/Spring/MyBatis 좁은 Pilot
- ID: `JAVA_SPRING_MYBATIS_STATIC_PILOT_V0_1`
- 구현: `java_spring_mybatis.py`
- 상태: `PILOT_PARTIAL_COVERAGE`
- 자동 활성화: **아니오**

```bash
python sdlc/custom/project/adapters/impact/java_spring_mybatis.py \
  --source-root <repository-or-source-root> \
  --out <impact-result.json>
```

실제 지원:
- Java class/method 후보
- 명시적 field receiver의 direct call 후보
- Spring method mapping / Controller naming entry 후보
- MyBatis mapper statement
- MyBatis SQL Table READ/WRITE
- SQL `CREATE TABLE` asset
- Coverage Gap/Unsupported Pattern

미지원:
- compiler/type-solver 수준 call graph
- Spring runtime proxy/AOP/wiring
- Reflection/Dynamic dispatch
- Transaction runtime propagation
- JPA/JDBC/SP/Trigger/ETL
- External API/Kafka/JMS runtime contract
- Config effective value
- Test semantic coverage

### 2. Java/Spring Enterprise 정적 확장 Pilot
- ID: `JAVA_SPRING_ENTERPRISE_STATIC_V0_2`
- 구현: `java_spring_enterprise.py`
- 상태: `PILOT_PARTIAL_COVERAGE`
- `java_spring_mybatis.py` 결과를 기반으로 확장

```bash
python sdlc/custom/project/adapters/impact/java_spring_enterprise.py \
  --source-root <repository-or-source-root> \
  --out <impact-result.json>
```

추가로 정적 후보를 만드는 범위:
- JPA `@Entity/@Table`, Spring Data Repository
- Java 안의 JDBC SQL literal Table READ/WRITE
- `@Transactional`
- Feign/RestTemplate/WebClient/HttpClient 후보
- `@KafkaListener`, Kafka publish hint
- `@Scheduled`
- `application*.yml/properties` Config asset

이 확장 Adapter도 다음을 **확정하지 않는다**.
- JPA query method의 실제 SQL/동작
- 실제 transaction manager/proxy/propagation
- live DB metadata
- 실제 broker topology/schema registry
- dynamic dispatch/reflection
- stored procedure/trigger/ETL
- 업무 목적/Business Truth

따라서 annotation이나 relation을 찾았어도 `STRUCTURAL_COVERAGE_COMPLETE` 또는 업무 영향 확정으로 올리지 않는다. 정적 후보는 `OBSERVED/CHECK_REQUIRED`, 미지원 영역은 Coverage Gap으로 남긴다.

## Adapter 선택법

`/setup` 결과의 `adapter_assessment`를 먼저 본다.

- Spring + MyBatis 위주, 단순 정적 관계 → 좁은 Pilot부터 사용
- Spring + JPA/Kafka/Feign/Transactional 등이 중요 → Enterprise 정적 Pilot 검토
- .NET/Node/Python/Legacy framework → Project Adapter 필요
- DB/APM/Broker/API Catalog의 실제 runtime 정보가 중요 → Tool/MCP Evidence 필요

Config에 Adapter ID를 적었다고 기능이 생기는 것은 아니다. `sdlc/config/impact-adapter-profile.example.yaml`의 기본 `enabled: false`는 유지한다.

## 공통 출력 계약
Adapter는 `brownfield-impact-contract.json`을 만족해야 한다.

최소 출력:
- `adapter_id / project_context`
- `nodes / edges`
- `coverage / coverage_gaps`
- `unsupported_patterns`

Adapter가 없더라도 일반 분석 Workflow는 진행할 수 있지만 Brownfield 영향분석을 COMPLETE로 표시할 수 없다.

## Project 적용 원칙
1. 실제 Source 구조에 맞는 Adapter인지 먼저 확인한다.
2. `coverage_gaps`를 “영향 없음”으로 바꾸지 않는다.
3. static result를 runtime truth로 승격하지 않는다.
4. Project Adapter를 바꿔도 Core Node/Edge/Coverage 경계를 유지한다.
5. Pilot fixture PASS는 실제 Production Repository 정확도/완전성을 의미하지 않는다.
