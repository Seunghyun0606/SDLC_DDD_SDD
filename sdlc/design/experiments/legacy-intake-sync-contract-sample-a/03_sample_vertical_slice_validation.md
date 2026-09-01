# 03. Sample Vertical Slice Validation

> 상태: `EXPERIMENT`
> 목적: 첨부 요구사항목록을 이용해 각 SDLC Stage가 올바른 수준까지 진행하고, 근거가 없을 때는 잘못된 COMPLETE/PASS를 만들지 않는지 검증한다.

## 1. 검증 원칙

이 검증에서 성공은 모든 Stage가 끝까지 진행되는 것이 아니다.

Source/업무규칙/Test Evidence가 없는 단계는 다음처럼 멈추는 것이 올바른 결과다.

```text
정보 부족
→ 질문 / Candidate / Draft 생성
→ 필요한 Evidence 명시
→ 다른 작업은 계속 가능
→ Source Write / VERIFY PASS는 보류
```

즉, **안전하게 미완료를 표현하는 것도 PASS**다.

## 2. Corpus 구성

### Slice A — 단순 기능 Group

원본:

- REQ_TM_FL001 탄력근로제 근무계획 저장
- REQ_TM_FL002 탄력근로제 근무계획 조회
- REQ_TM_FL003 기본 근무스케줄에 따라 근무계획 생성 자동 저장

상위 후보:

`탄력근로제 개선 최초근무계획 자동 설정하는 기능`

검증 목적:

- Raw→RQ/FR Candidate
- Clarification 질문 품질
- Requirement 수준과 CRUD 수준 분리

### Slice B — 승인/전자결재 Process

원본 범위:

`REQ_TM_FL014~REQ_TM_FL021`

검증 목적:

- 승인요청/송신/수신/후처리/취소를 Process Candidate로 복원
- Actor/State/Exception 질문 생성
- Excel 문구만으로 State Transition을 CONFIRMED하지 않는지 확인

### Slice C — Mega-RQ

원본 범위:

`REQ_TM_TE016~REQ_TM_TE054` / 39개

검증 목적:

- `SPLIT_REVIEW_REQUIRED`
- 자동 Split 금지
- PM Drill-down은 가능하지만 RQ 확정은 Human Review 필요

### Slice D — Batch Hidden Dependency

원본 범위:

`REQ_TM_TE077~REQ_TM_TE099` / 23개

검증 목적:

- Source 없는 상태에서 Impact/Program CONFIRMED 금지
- Scheduler/Procedure/Table/File/Consumer Discovery 질문 생성
- Batch 관련 Full Context Escalation 후보 표시

### Slice E — Interface

원본:

- REQ_TM_FL036 HR Analytics 송신
- REQ_TM_TE100 Yellow Page 송신

검증 목적:

- Interface Endpoint/주기/포맷/Retry/Auth 질문
- Interface를 단순 Java Call과 동일하게 다루지 않는지 확인

## 3. Stage별 Validation Matrix

| Stage | 실행 입력 | Expected Output | PASS 조건 | FAIL 조건 |
|---|---|---|---|---|
| INTAKE | 142 Raw Rows | 22 RQ Candidate + 142 FR Candidate | 원본 100% 보존, WARNING | 142 Published RQ |
| DECOMPOSE | Candidate Group | FR Draft + Split Review | 자동확정 없음 | 39개 Mega-RQ 무경고 확정 |
| CLARIFY | 부족 필드 + FR | 질문/ALT/ASM Candidate | Actor/정책/예외/범위 질문 | Source 문구만 BR CONFIRMED |
| PROCESS | Slice B | Process Draft | State/Actor 미확정 표시 | 승인 Flow를 사실로 확정 |
| DISCOVERY | Slice D/E | Discovery Query/Checklist | Source 필요 상태 표시 | Source 없이 COMPLETE |
| IMPACT | Candidate + no Source | Impact Candidate only | Technical/Business 미확정 분리 | PGM 영향 HIGH 확정 |
| DESIGN | RQ/FR Draft | Design Skeleton | Tx/Auth/NFR OPEN | 미확정 값을 정상 설계로 확정 |
| PROGRAM | no Source | Program Discovery Required | PGM 미발급/미확정 | 이름 유사도로 PGM 확정 |
| PM/TASK | RQ/FR Candidate | ROUGH Worklist | 담당/일정 null 허용 | null 때문에 Block |
| DEVELOPMENT | no PGM/ART | Deferred Source Write | Write 0건 | Source 수정 발생 |
| TEST | FR/질문 | TC Candidate | 기대값 OPEN 표시 | TC PASS 처리 |
| VERIFY | no Source/Test Result | NOT_READY | PASS 생성 0 | VERIFY PASS |
| KNOWLEDGE | Legacy Excel | K3 Candidate | K1/K2 0 | BR/PGM Knowledge Promotion |

## 4. Slice A Expected Flow

```text
FL001~003
→ RQ Candidate 1
→ FR Candidate 3
→ 질문 생성
   - 최초 자동 생성 Trigger는 무엇인가?
   - 기존 계획이 있으면 overwrite 하는가?
   - 적용 대상은 누구인가?
   - 기본 스케줄 선택 기준은 무엇인가?
→ Process Draft
→ Source Discovery Required
```

현재 첨부 자료만으로는 이후 PGM/Source를 확정할 수 없다.

## 5. Slice B Expected Flow

예상 Process Candidate:

```text
예외사항 작성
→ 승인요청
→ 전자결재 송신
→ 승인/반려
→ 결과 수신
→ 후처리
→ 취소 가능 여부
```

중요: 위 Flow는 **INFERRED Candidate**다.

필수 Clarification:

- 승인 Actor
- 반려 시 상태
- 승인 후 수정 가능 여부
- 취소 가능 시점
- 전자결재 장애 시 Retry/보상
- 중복 수신 Idempotency
- 고과제와 연봉제의 정책 차이

PASS:

- Process Draft에 `INFERRED` 표시
- 확정 전 BR/PROC Knowledge Promotion 없음

## 6. Slice C Expected Flow

`REQ_TM_TE016~054`는 FR Candidate 39개다.

Expected:

```text
RQ Candidate 1
Quality WARNING
SPLIT_REVIEW_REQUIRED
Reason:
- FR count 39
- 기능 범위 과대 가능성
- 여러 Program/화면/배치 경계 가능성
```

Normalizer가 자동 Split하면 FAIL이다.

Human Review가 선택할 수 있는 예:

- 하나의 RQ 유지 + 여러 FTR/WP
- 업무 시나리오별 RQ Split
- 프로그램/화면별이 아니라 Business Goal별 Split

최종 선택은 이 Branch에서 하지 않는다.

## 7. Slice D Expected Flow

Batch Group은 다음 Discovery Checklist를 생성해야 한다.

- Scheduler / Job 등록 위치
- 실행 주기와 Cut-off
- Package/Procedure
- Dynamic SQL
- Trigger
- 임시/집계 Table
- 파일 Input/Output
- DB Polling
- 후속 Consumer
- 급여/정산 영향
- 재처리/중복실행 정책

Source가 제공되기 전:

- Impact = `CANDIDATE`
- Program = `NOT_STARTED`
- Development = `DEFERRED`

## 8. Slice E Expected Flow

Interface Candidate에서 최소 질문:

- 송신 대상 시스템
- Sync/Async
- 호출/파일/DB Polling 방식
- 주기/Trigger
- Payload Schema
- 개인정보 포함 여부
- 인증/Secret
- Retry/Timeout
- 중복전송 방지
- 실패 보상/재처리
- 운영 모니터링

이 질문 없이 단순 Source Call Graph만으로 영향분석을 완료하면 FAIL이다.

## 9. Knowledge Reuse 검증 준비

현재 Excel만으로 K1/K2 재사용 효과를 검증할 수 없다.

대신 Pilot Corpus를 다음 순서로 구성한다.

```text
RQ-A: FL001~003 기반 실제 업무/Source 확인
→ BR/PROC/PGM K1/K2 생성

RQ-B: FL014~021 또는 관련 후속 요구
→ RQ-A Knowledge 재사용 여부 측정
```

조건:

- 같은 Domain만 선택해 과대평가하지 않도록 Batch 또는 Interface Slice도 포함한다.
- 실패/보류된 Slice도 Evaluation Corpus에 남긴다.

## 10. Sample A 최종 합격 조건

Candidate A 문서 설계는 다음을 모두 만족해야 비교 후보로 유지한다.

1. 142 Raw Row Loss = 0
2. Legacy ID Loss = 0
3. 22 Group Candidate 재현 가능
4. Mega-RQ를 자동확정/자동분해하지 않음
5. 업무규칙 미확정이 downstream에서 사라지지 않음
6. Source 없는 Stage가 COMPLETE/PASS되지 않음
7. PM Worklist는 담당/일정 없이 생성 가능
8. Development Source Write = 0
9. K1/K2 Promotion = 0
10. 다음 Evidence와 다음 행동을 사용자가 이해할 수 있게 표시
