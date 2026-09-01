# /change

자연어 변경을 `CLARIFICATION / BEHAVIOR_CHANGE / TECHNICAL_CHANGE / NEW_REQUIREMENT`로 구조화한다.

1. Target과 Before/After를 식별한다.
2. RQ/FR/BR/PROC/PGM/TASK/AC/TC 관계를 따라 영향 범위를 계산한다.
3. 기존 Source Evidence와 충돌하면 기존 설계/Knowledge를 `STALE` 처리한다.
4. 확정되지 않은 변경은 Alert/Assumption과 함께 진행하며 위험 Source write만 Guard한다.
5. 변경 원문과 provenance를 보존한다.

## Source Drift Reverse 처리
Source 기준점이 바뀌었거나 외부에서 Source가 수정된 경우 다음 공통 절차를 사용한다.

1. 기존 산출물과 연결된 `baseline source manifest`를 준비한다.
2. 현재 Source의 `observed source manifest`를 준비한다.
3. Artifact별 Source Evidence와 역방향 전파 관계를 `artifact evidence index`로 준비한다.
4. `python sdlc/scripts/detect_source_drift.py --baseline <baseline.json> --observed <observed.json> --artifact-index <artifact-index.json> --output <reverse-report.json>`을 실행한다.
5. `STALE_SOURCE_EVIDENCE`는 실제 Source hash가 달라진 직접 영향 산출물이다.
6. 명시적 전파 Edge가 `STALE`이면 `STALE_PROPAGATED`, `CHECK_REQUIRED`이면 `CHECK_REQUIRED_REVERSE`로 기록한다.
7. Reverse 결과는 Candidate만 만든다. 기존 문서나 Canonical Business Truth를 자동 덮어쓰지 않는다.
8. 재생성/검토가 끝난 뒤에만 현재 Source Evidence hash로 Artifact를 갱신한다.

### 안전 규칙
- 신규 Source가 생겼다는 이유만으로 관련 없는 기존 문서를 자동 STALE 처리하지 않는다.
- Source-derived 설계/프로그램 문서는 `STALE` 전파가 가능하지만, 고객 승인 Requirement/BR 등 권위 있는 업무 사실은 기본적으로 `CHECK_REQUIRED`가 적절하다.
- 역방향 전파는 명시된 Artifact Edge를 통해서만 수행한다.
- Source 변경은 Business Truth 변경의 증거 후보이지 자동 정책 변경이 아니다.
