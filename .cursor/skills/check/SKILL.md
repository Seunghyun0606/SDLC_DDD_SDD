# /check

현재 Harness/Project/Target 상태를 **Agent 해석 없이도 먼저 확인하는** Runtime이다. 실제 실행기는 `sdlc/scripts/run_check.py`이고 일반 사용자는 다음을 사용한다.

```bash
python sdlc/scripts/harness.py check --setup
python sdlc/scripts/harness.py check --target RQ-001
```

## /check가 실제로 확인하는 것
- Project Profile 존재 및 Mode/Delivery Profile
- Source Profile과 Source write root
- Agent Provider 설정/활성 여부
- Git HEAD/branch/dirty workspace
- Canonical revision/entity/relation 수
- Target 존재 여부와 마지막 Stage/다음 Stage
- Target 내부의 OPEN/CHECK_REQUIRED/CONFLICT 등 확인 필요 상태
- 관련 Entity 범위
- 최신 Reverse report와 review candidate 존재 여부

Provider가 없으면 `SETUP_OR_PROVIDER_REQUIRED`로 표시하며 정상 실행 가능 상태로 보지 않는다.

## Source-enabled 프로젝트
최소 다음을 구분한다.
- Source 연결 여부
- Trace/Impact Evidence 존재 여부
- 실제 수정 대상 확정 여부
- Build/Test command/evidence 존재 여부
- 검증되지 않은 Candidate/Assumption
- 현재 Artifact의 Source Evidence hash가 현재 Source와 일치하는지
- `STALE_SOURCE_EVIDENCE / STALE_PROPAGATED / CHECK_REQUIRED_REVERSE` 존재 여부

## Brownfield 프로젝트
추가로 다음을 확인한다.
- `brownfield-impact-contract.json` 공통 Coverage 상태
- Project Impact Adapter 필요 여부
- Adapter가 없으면 `PARTIAL_PROJECT_ADAPTER_REQUIRED`
- Coverage Gap / Unsupported Pattern
- JPA/Kafka/Runtime wiring 등 정적 Adapter가 다루지 못한 영역은 영향 없음으로 해석하지 않는다.

## Source Drift
Source Drift report가 있으면 자동 갱신된 문서가 있다고 가정하지 않는다. `reverse_candidates` 또는 Program Spec candidate는 사람 검토가 필요한 상태로 요약한다.

## 역할별 해석
- 분석가: 미확정/충돌/결정 필요사항을 본다.
- 설계자: 다음 DESIGN/PROGRAM 작업과 stale 여부를 본다.
- 개발자: Git dirty/Source target/Build-Test 준비도를 본다.
- QA: AC/TC와 Verify 근거 누락을 본다.
- PM: Target별 다음 Stage와 blocked/coverage gap을 본다.

## Do Not
- 파일이 없다는 이유만으로 기능이 없다고 단정하지 않는다. Coverage Gap일 수 있다.
- Reverse candidate를 자동 문서 반영 완료로 표시하지 않는다.
- Provider 미연결을 PASS로 표시하지 않는다.
- Git branch protection이 Script Guard로 대체됐다고 주장하지 않는다. Hosting 정책은 별도다.
