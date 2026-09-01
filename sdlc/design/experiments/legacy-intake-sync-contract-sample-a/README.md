# Legacy Intake + Sync Contract — Sample A

> 상태: `EXPERIMENT / NOT BASELINE`
> 기준 Baseline: `AI_SDLC_Harness_Full_Design_v1.5.1.md`
> 목적: 첨부 `요구사항목록.xlsx`를 실제 Legacy Requirement Inventory로 가정하여, Requirement Intake Normalization과 MD↔Excel 양방향 Sync 구조가 단계별 SDLC 진행에 적합한지 검증한다.
> 병합 정책: 이 실험 브랜치는 비교 검증용이며 `main`에 자동/임의 병합하지 않는다.

## 1. 이 Branch가 검증하는 설계안

이 Branch는 다음 해석을 **Candidate A**로 둔다.

```text
Legacy Excel Raw Row
→ Raw Requirement Item
→ RQ Candidate Group
→ FR Candidate
→ Human Review
→ Canonical Publish
→ MD / Excel View
```

핵심은 **기존 Excel 한 행을 RQ로 고정하지 않는 것**이다.

- 원본 행은 Provenance가 있는 `Raw Requirement Item`으로 보존한다.
- 프로젝트 Overlay가 Grouping Rule을 제안한다.
- 현재 Sample에서는 `업무 대분류 + 업무 중분류 + 요구사항명`을 RQ Candidate Group으로 사용한다.
- `세부 요구사항`은 FR Candidate로 제안한다.
- Agent가 자동으로 Canonical RQ/FR을 확정하지 않는다.
- 큰 Group은 자동 Split하지 않고 `SPLIT_REVIEW_REQUIRED`를 낸다.

## 2. Sample 사실

검증 파일 기준:

- 원본 행: 142
- 업무 대분류: 1 (`근태관리`)
- 업무 중분류: 10
- 서로 다른 `요구사항명`: 22
- 시작일 입력: 0/142
- 종료일 입력: 0/142
- 담당자 입력: 0/142

대표 Stress Group:

| Group | 원본 ID | 세부기능 수 | 검증 포인트 |
|---|---|---:|---|
| 최초근무계획 자동 설정 | REQ_TM_FL001~003 | 3 | 단순 Grouping / Clarification |
| 고과제·연봉제 예외 승인 | REQ_TM_FL014~021 | 8 | 상태/승인/전자결재 Process |
| 근태마감 10분단위 반영 | REQ_TM_TE016~054 | 39 | Mega-RQ / Split Review |
| 근무집계 Batch 반영 | REQ_TM_TE077~099 | 23 | Hidden Dependency / Batch Impact |
| HR Analytics / Yellow Page 송신 | FL036, TE100 | 각 1 | Interface Contract |

## 3. 비교 검증 축

유저가 다른 Branch와 비교할 때 다음 축으로 판단한다.

| 검증 축 | 질문 |
|---|---|
| 이해성 | Agent 비숙련 사용자가 Raw→RQ→FR 관계를 이해할 수 있는가? |
| 보수성 | 원본 행을 잘못 RQ로 확정하거나 자동 Split하지 않는가? |
| 추적성 | 기존 요구사항 ID와 원본 행을 끝까지 역추적할 수 있는가? |
| 진행성 | 정보가 부족해도 질문/초안/후속 Stage 준비를 계속할 수 있는가? |
| 안전성 | Source Evidence가 없는데 PROGRAM/DEVELOPMENT/VERIFY를 완료 처리하지 않는가? |
| 확장성 | 다른 프로젝트 Excel 형식은 Mapping Overlay만 바꿔 수용 가능한가? |
| PM UX | 담당자/일정이 없어도 Worklist를 만들고 나중에 채울 수 있는가? |
| Sync | MD/Excel 어느 쪽에서 수정해도 Canonical을 통해 안전하게 왕복 가능한가? |

## 4. 문서 구성

1. `01_legacy_requirement_import_normalizer.md`
   - Raw Excel → Candidate Canonical 변환 계약
2. `02_md_excel_bidirectional_sync_contract.md`
   - 전체작업목록 MD↔Excel 충돌/왕복 계약
3. `03_sample_vertical_slice_validation.md`
   - Sample을 단계별로 통과시키는 검증 시나리오
4. `04_validation_checklist.md`
   - PASS/FAIL 판정용 체크리스트
5. `contract-tests/legacy-intake-cases.yaml`
   - 기계 판독 가능한 Intake 기대 결과
6. `contract-tests/sync-cases.yaml`
   - 양방향 Sync 기대 결과

## 5. 이 Branch에서 의도적으로 하지 않는 것

- v1.5.1 Full Baseline 변경
- `main` 병합
- 22개 Group을 실제 Published RQ로 확정
- 39개 근태마감 기능의 자동 Split
- Source Repository가 없는 상태에서 PGM/ART/Impact를 확정
- 실제 업무규칙을 Excel 문구만으로 `CONFIRMED` 처리

## 6. Candidate A의 핵심 가설

> Legacy Requirement 문서는 이미 정규화된 Requirement가 아니라 **업무 범위 Inventory**일 수 있다. 따라서 Import Layer가 원본을 보존하면서 RQ/FR Candidate를 만들고, SDLC Stage는 Candidate의 불확실성을 유지한 채 진행해야 한다.

이 가설이 다른 Branch 설계보다 사용자 이해도, 추적성, 변경 대응성에서 불리하면 Candidate A를 채택하지 않는다.
