# /check

RQ/PGM/TASK의 현재 Stage, Progress, Quality, Validity, Open Alert/Guard, Source Evidence coverage, AC/TC coverage, 다음 추천 작업을 요약한다.

Source-enabled 프로젝트에서는 최소한 다음을 구분한다.
- Source 연결 여부
- Trace/Impact Evidence 존재 여부
- 실제 수정 대상 확정 여부
- Build/Test Evidence 존재 여부
- 검증되지 않은 Candidate/Assumption
- 현재 Artifact의 Source Evidence hash가 현재 Source와 일치하는지
- `STALE_SOURCE_EVIDENCE / STALE_PROPAGATED / CHECK_REQUIRED_REVERSE` 존재 여부

Brownfield 프로젝트에서는 추가로 다음을 표시한다.
- `brownfield-impact-contract.json` 공통 Coverage 상태
- Project Impact Adapter 설정 여부
- Adapter가 없으면 `PARTIAL_PROJECT_ADAPTER_REQUIRED`
- Coverage Gap / Unsupported Pattern

Source Drift report가 있으면 자동 갱신된 문서가 있다고 가정하지 말고 `reverse_candidates`의 재생성/사람 검토 필요 여부를 요약한다.
