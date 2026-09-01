# Source → Documentation Reverse Sync Contract — P0 + Structural Redesign v1

상태: `ACTIVE_STRUCTURAL_REDESIGN_V1`

## 목적

요구사항 문서에서 Source로 내려가는 Trace뿐 아니라 Source 변경에서 관련 설계/요구/테스트 문서로 되돌아가는 경로를 표준화한다. Core Reverse Sync는 특정 언어/Framework/업무 패턴을 직접 해석하지 않고 Analyzer가 생성한 generic Source Change Signal과 Confirmed Reference Graph를 소비한다.

## 기본 Pipeline

```text
Changed File
→ Language/Framework Analyzer
→ SOURCE_CHANGE_EVIDENCE
→ Semantic Change Candidate
→ Confirmed Reference Graph Direct Relation
→ Technical STALE Candidate / Human Review Candidate
→ Human Truth 보호
→ Re-analysis / Regenerate / Re-Test
```

## Analyzer / Core Boundary

Analyzer 책임:
- changed symbol / SQL / interface / security / behavior signal 추출
- language/framework specific parsing
- Source Evidence와 revision/hash 보존

Core 책임:
- generic signal classification
- Confirmed direct graph relation만 자동 전파
- STALE/REVIEW candidate 생성
- OPEN/UNKNOWN 보존
- Human Truth 보호

Core에 특정 Java Class, Table Prefix, 업무 Status, 시간값, 도메인 문자열을 hard-code하지 않는다.

## Semantic Change Class

- `TECHNICAL_ONLY`: Refactor, logging, non-behavioral implementation detail
- `FUNCTIONAL_BEHAVIOR`: 사용자 관찰 동작 변화 후보
- `BUSINESS_RULE_CANDIDATE`: 조건/정책/예외 의미 변화 가능성
- `DATA_CONTRACT`: Table/Column/Query semantics 또는 schema 계약 변화
- `INTERFACE_CONTRACT`: API/File/Message 계약 변화
- `SECURITY_BEHAVIOR`: Auth/AuthZ/Security policy 구현 변화
- `UNKNOWN`: 근거 부족

## Evidence Priority

1. Commit/PR에 연결된 RQ/TASK/CR
2. Confirmed Reference Graph direct relation
3. Analyzer Source Evidence / changed symbol / SQL / interface
4. Test delta
5. Runtime/Static evidence
6. Semantic inference

Name similarity 또는 Analyzer inference만으로 BR/FR/PGM relation을 CONFIRMED하지 않는다.

## 자동 처리 가능 범위

Confirmed direct relation이 있는 경우 다음 Technical Node를 `STALE_CANDIDATE`로 만들 수 있다.

- PGM
- ART
- SYMBOL
- DATA
- INT
- TC

추가로:
- 관련 Test 재실행 후보 생성
- Generated Summary 재생성 후보 생성
- Technical Knowledge 재검토 후보 생성

## 자동 처리 금지

다음 Human-facing / Business Node는 Source 변경만으로 STALE 확정 또는 Current Truth overwrite하지 않는다.

- RQ
- FR
- BR
- PROC
- FTR
- AC

이 Node들은 Confirmed direct relation이 있어도 기본적으로 `REVIEW_CANDIDATE`다.

금지:
- Human Truth 문구 자동 overwrite
- `OBSERVED Source Change`를 `CONFIRMED Business Rule`로 승격
- `BUSINESS_RULE_CANDIDATE`, `SECURITY_BEHAVIOR`, `UNKNOWN`을 검토 없이 Current Truth로 반영
- Unconfirmed relation을 따라 자동 STALE 전파
- Direct relation 없는 FR/BR/AC를 단순 키워드/이름 유사도로 변경

## STALE / REVIEW 규칙

- Confirmed direct relation + Technical Node → `STALE_CANDIDATE`
- Confirmed direct relation + Human/Business Node → `REVIEW_CANDIDATE`
- Unconfirmed/Open/Inference-only graph edge → 자동 전파 금지
- Business Rule 변경 후보 → L2/Human Review 필요
- Security Behavior → L2/Human Review 필요
- UNKNOWN → L2/Human Review 필요
- Human Confirmed Truth → `PROTECTED`

## Reverse Sync Input Contract

Authority:

`sdlc/templates/source-change-evidence.yaml`

필수 의미:
- change_id
- source_revision_before / after
- changed_files
- file-level analyzer signals
- analyzer provenance
- unresolved/open items

`changed_symbols`, `direct_program_ids`는 Analyzer가 제공할 수 있으나 Core 필수 필드는 아니다.

## Reverse Sync Candidate 필수 의미

- change_id
- source_revision_before / after
- changed_files
- semantic_change_class
- secondary_classes
- generic signals
- confirmed_graph_edge_ids
- stale_candidates
- review_candidates
- protected_human_truth
- required_review
- status
- open_items

## Runtime

Generic Core:

`sdlc/scripts/build_reverse_sync_from_signals.py`

Classification:

`sdlc/config/reverse-sync-classification.yaml`

기존 fixture-oriented `build_reverse_sync_candidate.py`는 Regression Reference로만 유지하며 Active Core Runtime이 아니다.

## 완료 조건

Reverse Sync는 모든 문서를 자동 수정했을 때 완료되는 것이 아니다. 다음이 충족되면 해당 실행은 완료 가능하다.

1. Source Change Evidence가 revision과 함께 저장됨
2. Analyzer Signal이 값 또는 UNKNOWN으로 존재함
3. 자동 전파가 Confirmed direct relation으로 제한됨
4. Technical STALE Candidate와 Human REVIEW Candidate가 분리됨
5. Human Truth 보호 여부가 명시됨
6. 필요한 Reviewer가 명시됨
7. OPEN/Blind Spot이 조용히 삭제되지 않음
