# Skill — Stack-neutral Source Discovery

## Purpose

Brownfield/Hybrid 프로젝트에서 현재 Work Unit과 관련된 Source/Artifact/Symbol/Data/Interface Evidence를 **Provider Capability와 Analyzer Adapter를 통해 제한적으로 수집**한다.

Core Skill은 특정 언어, Framework, ORM, DB Naming Rule을 직접 해석하지 않는다.

## Required Input

- Stage Input Pack v2
- Current project mode
- Source Provider State
- `sdlc/config/stage-routing.yaml`
- 현재 Source Revision 또는 명시적 OPEN

## Optional Input

- Direct RQ/PGM/ART/SYMBOL/DATA Reference
- 기존 Reference Graph
- Existing Source Summary
- Source Analyzer Provider
- Project Overlay / Source Profile

## Precondition

- Brownfield/Hybrid이면 Source Provider State가 명시적으로 알려져 있어야 한다.
- Source Provider가 없으면 Source Claim을 만들지 않고 `OPEN` 결과를 생성할 수 있다.
- Current Revision이 없으면 Write Target을 확정하지 않는다.

## Retrieval Strategy

1. 기존 Stable ID / Direct Trace
2. Source Provider `source.object.read`
3. Source Provider `source.search`
4. 제한된 `source.snapshot.read`
5. 가능한 경우 Source Analyzer Capability
   - `analysis.source.symbols`
   - `analysis.source.dependencies`
   - `analysis.source.data_refs`
   - `analysis.source.interface_refs`
6. Runtime/Procedure/Batch/External Consumer는 별도 Provider/Analyzer Evidence가 없으면 OPEN

## Atomic Steps

1. 현재 Target ID와 Source Requirement ID를 확인한다.
2. 기존 Direct Reference가 있으면 우선 사용한다.
3. Stage Runtime이 제공한 Source Provider 결과의 Revision/Evidence를 기록한다.
4. Source Search/Object 결과를 `OBSERVED` Evidence로 기록한다.
5. Analyzer Provider가 있으면 Symbol/Dependency/Data/Interface Evidence를 추가한다.
6. Analyzer가 없거나 지원하지 않는 Stack이면 `UNSUPPORTED_STACK_ANALYZER` OPEN을 생성한다.
7. Direct PGM/ART/SYMBOL/DATA/INT 후보를 Reference Graph Update 후보로 만든다.
8. Dynamic/Runtime-only 관계와 외부 Consumer Blind Spot을 기록한다.
9. Name Similarity만 있는 관계는 Candidate로 유지한다.
10. Stage Input Pack의 `art/symbol/data/int/source` related IDs를 갱신한다.
11. `SOURCE_EVIDENCE_SET`을 생성하거나 PARTIAL/OPEN으로 기록한다.
12. 다음 Stage `IMPACT` Handoff를 준비한다.

## Decision Rules

- Provider 결과가 없으면 Source가 없다고 결론내리지 않는다.
- Provider `PARTIAL`은 `COMPLETE`로 승격하지 않는다.
- Source File/Symbol 존재는 `OBSERVED`다.
- Source 조건/예외는 Business Rule의 단독 확정 근거가 아니다.
- Stack-specific Syntax 판단은 Analyzer Adapter 결과만 소비한다.
- Direct Relation 없는 Name Similarity는 Canonical Trace가 아니다.

## Output Schema

- `SOURCE_EVIDENCE_SET`
- Analyzer Evidence가 있는 경우 `ANALYZER_EVIDENCE`
- 갱신된 Stage Input Pack v2
- Reference Graph Update Candidate
- OPEN / Blind Spot

## Quality Check

- Source Revision 또는 명시적 OPEN이 있는가?
- 모든 Source Evidence에 Locator/Revision이 있는가?
- ART/SYMBOL/DATA/INT 관련 ID가 Handoff에 보존되는가?
- Provider PARTIAL이 숨겨지지 않았는가?
- Unsupported Stack이 추측으로 보완되지 않았는가?
- Source Behavior와 Business Truth가 분리되었는가?

## Alert Conditions

- SOURCE_PROVIDER_UNCONFIGURED
- SOURCE_REVISION_OPEN
- PROVIDER_PARTIAL
- UNSUPPORTED_STACK_ANALYZER
- AMBIGUOUS_TARGET
- DYNAMIC_RUNTIME_ONLY
- PROCEDURE_BLIND_SPOT
- BATCH_BLIND_SPOT
- DOWNSTREAM_UNKNOWN

## Stop Conditions

- 현재 Work Unit의 Direct/Configured Retrieval 범위를 모두 탐색했다.
- Source Evidence가 값 또는 명시적 OPEN/PARTIAL로 정리됐다.
- 다음 탐색이 새로운 Provider/권한/Runtime을 요구한다.
- 동일 Evidence가 반복된다.

## Escalation Conditions

- Unsupported Stack + Symbol/Data Trace 필수 → L2/L3 Adapter 구현
- Dynamic/runtime-only relation → L3
- High blast radius → L3
- Ambiguous write target → L2_OR_HUMAN
- Business Rule 확정 필요 → HUMAN

## Do Not

- Core Skill에서 Java/MyBatis/PLSQL 등 Syntax 직접 파싱
- Table Prefix로 Data Object 의미 추측
- Sample/Pilot Constant 사용
- 전체 Repository 무제한 Scan
- Name Similarity로 Canonical Trace 확정
- Source Behavior를 CONFIRMED Business Rule로 승격

## Example

Source Provider에서 `orders/service.py`가 검색되고 Python Analyzer Adapter가 `close_order` Symbol과 `orders` Table Reference를 반환했다면 해당 사실은 `OBSERVED` Evidence로 기록한다.

반대로 Python Analyzer가 연결되지 않았다면 파일 내용을 보고 임의 Regex를 새로 작성하지 않는다. `UNSUPPORTED_STACK_ANALYZER`를 OPEN으로 남기고 가능한 File-level Evidence까지만 다음 IMPACT Stage에 전달한다.
