# Source Analyzer Adapter Boundary

이 디렉터리는 **Core SDLC Runtime이 직접 알아서는 안 되는 Stack-specific Source 해석 로직**을 둔다.

## Core와 Adapter의 경계

Core가 아는 것:

- Source Provider Capability
- Source Revision / File Hash
- `SOURCE_EVIDENCE_SET`
- `ANALYZER_EVIDENCE`
- RQ/PGM/ART/SYMBOL/DATA/INT Reference
- OPEN / Blind Spot

Core가 직접 알아서는 안 되는 것:

- Java Method 정규식
- MyBatis Mapper XML 문법
- Spring Annotation
- 특정 DB Table prefix
- PL/SQL Procedure 문법
- 특정 Batch Scheduler 구조
- 특정 업무 Domain Constant
- Pilot/Sample ID

## 권장 Analyzer Capability

```text
analysis.source.symbols
analysis.source.dependencies
analysis.source.data_refs
analysis.source.interface_refs
```

Analyzer가 반환하는 사실은 기본적으로 `OBSERVED` Evidence다.

Analyzer 결과만으로 Business Rule을 `CONFIRMED`하지 않는다.

## Adapter 예

```text
sdlc/adapters/analyzers/
├ java-mybatis/
├ dotnet-ef/
├ node-sql/
├ plsql/
├ batch-scheduler/
└ interface-contract/
```

위 이름은 예시일 뿐 Core 필수 목록이 아니다.

## Unsupported Stack

Analyzer가 없거나 분석이 불완전하면 다음처럼 처리한다.

```text
Analyzer unavailable
→ SOURCE Evidence는 가능한 범위까지 유지
→ SYMBOL/DATA/INTERFACE 관계는 OPEN
→ Unsupported Stack Alert
→ L2/L3 Adapter Candidate
→ 비위험 분석/설계는 계속
```

전체 Repository를 추측으로 해석하거나 Name Similarity만으로 Canonical Trace를 만들지 않는다.

## Legacy P0 Fixture

기존 `sdlc/scripts/discover_source_evidence.py`와 `build_reverse_sync_candidate.py`에 포함된 Java/MyBatis/Attendance Fixture 로직은 범용 Core Analyzer 규격으로 간주하지 않는다.

후속 P0 단계에서 해당 로직 중 재사용 가능한 부분은 Adapter/Validation Fixture로 이동하고, Core Runtime에서는 Stack-neutral Evidence만 소비하도록 정리한다.
