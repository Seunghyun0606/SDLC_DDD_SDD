# Design Reference & History

`sdlc/design/`은 **설계 근거·검토·검증·이력**을 보존하는 Reference 영역이다. Active Runtime Authority가 아니다.

현재 실행 동작을 확인할 때는 다음 순서를 사용한다.

1. `sdlc/config/contract-authority.yaml`
2. 해당 Machine Authority (`sdlc/config/*.yaml`)
3. Runtime 구현 (`sdlc/scripts/`, `sdlc/adapters/`)
4. 사용자 진입점 (`sdlc/START_HERE.md`)

하위 폴더 의미:

- `baselines/` — 시점별 Full Design baseline. 과거 capability claim을 현재 Runtime 구현으로 간주하지 않는다.
- `contracts/` — 설계 당시 계약 설명과 Architecture Decision reference. 동일 개념의 현재 Machine Authority가 있으면 Machine Authority가 우선한다.
- `reviews/` — Red Team/검토 결과. 실행 규칙이 아니다.
- `validation/` — Self-test/실증 결과와 Gate 이력. PASS 기록 자체가 Production Evidence를 대신하지 않는다.
- `experiments/` — 실험/후보 설계. Current Contract가 아니다.
- `consolidation/` — 과거 통합/정리 결정의 기록.
- `CHANGELOG.md` — Design 변경 이력.

새 설계를 추가할 때 `design/` 문서만 수정하여 Runtime capability를 선언하지 않는다. 실행 기능을 추가했다면 Machine Config/Runtime/Test를 함께 변경하고 검증한다.
