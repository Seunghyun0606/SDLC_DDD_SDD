# Design / Validation History

이 폴더는 **프로젝트 참여자의 Runtime 진입점이 아니며 Active Machine Authority가 아니다.**

운영 시 Primary Authority는 `sdlc/config/contract-authority.yaml`에서 확인한다.

## 분류

- `contracts/`: 설계 계약의 설명/기록. 실제 실행 Authority는 대응하는 `sdlc/config/*`와 Runtime Script다.
- `baselines/`: 과거/비교용 Baseline 문서.
- `consolidation/`: 설계 통합 과정 기록.
- `reviews/`: Red Team/Architecture Review 기록.
- `experiments/`: 실험/후보 구현 기록.
- `validation/`: Self-test/E2E 검증 이력과 상태 기록.
- `CHANGELOG.md`: 설계 변경 이력.

`ACTIVE`, `CURRENT`, `BASELINE` 같은 표현이 과거 설계 문서 안에 남아 있더라도 현재 Runtime Authority를 의미하지 않는다. 충돌 시 `sdlc/config/contract-authority.yaml`과 거기서 지정한 Primary Authority가 우선한다.

처음 Repository를 받은 사용자는 `sdlc/START_HERE.md`부터 시작한다.
