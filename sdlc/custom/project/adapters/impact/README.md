# Project Impact Adapter 구현 위치

이 디렉터리는 Brownfield 프로젝트의 언어/Framework/DB/메시징 특성에 맞는 영향 관계 탐색기를 구현하는 **Project Custom 영역**이다.

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

## 구현 계약
Adapter는 `brownfield-impact-contract.json`의 `adapter_output_contract`를 만족해야 한다.
최소 출력:
- adapter_id / project_context
- nodes / edges
- coverage / coverage_gaps
- unsupported_patterns

Adapter를 구현하지 않은 상태에서도 일반 SDLC Workflow는 중단하지 않는다. 다만 Brownfield 영향분석 결과는 COMPLETE로 표시할 수 없다.
