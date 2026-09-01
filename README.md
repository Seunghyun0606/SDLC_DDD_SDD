# SDLC_DDD_SDD

AI-SDLC Harness 설계·Runtime·검증 저장소입니다.

## 처음 사용하는 프로젝트 담당자

설계 Baseline이나 Validation report부터 읽지 말고 **`sdlc/README.md`**에서 시작합니다.

최초 실행:

```bash
python sdlc/scripts/harness.py setup --name <project-name> --mode AUTO --delivery STANDARD
python sdlc/scripts/harness.py check --setup
```

실제 Agent Provider가 연결된 뒤:

```bash
python sdlc/scripts/harness.py work --target <RQ-ID> --plan-only
```

사용자 실행 명령은 네 개로 통합합니다.

```text
setup   최초 Project/Source/Provider/Canonical 설정
work    다음 Stage 또는 지정 Stage 실행
change  자연어 변경요청 실행
check   현재 Setup/Target/Git/Canonical 상태 확인
```

## Delivery Profile

- `FAST`: XS/S 운영변경·소규모 기능
- `STANDARD`: 일반 SI/SM 기능
- `FULL`: 대형/고위험 구축

새 프로젝트는 여러 Preset/Profile 계층을 먼저 이해할 필요가 없습니다. 기본 Customization은 `Core → Project Overlay → Local Override`만 사용합니다.

## Production Project 배포

최소 배포 파일은 `sdlc/design/contracts/harness-package-contract.json`의 `core_required_files`입니다.

필요 시 다음 Extension만 추가합니다.
- Brownfield Source/Reverse
- 고객 문서
- 비정형 문서 ingestion
- External Tool Evidence

`tests/**`, `sdlc/validation/**`, `docs/99_파일럿/**`은 Harness 검증 자료이며 Production Project 필수 배포물이 아닙니다.

## 현재 안전 경계

Runtime은 다음을 실제로 Guard합니다.
- Agent Provider 미연결 false success 방지
- 기본 `main/master` Source write 방지
- dirty workspace / stale Git HEAD 방지
- Provider write scope 제한
- DEVELOPMENT build/test 실패 시 Canonical commit 금지
- 실패한 Provider working-tree 변경 rollback
- Canonical file lock + 최신 revision 재확인 + atomic replace
- Source observation의 Business Truth 자동 승격 금지

GitHub/GitLab의 Branch Protection 자체는 Repository 운영 정책에서 별도로 활성화해야 합니다.

## 검증 수준 주의

Fixture Provider PASS는 실제 Agent 성공이 아닙니다. 실제 외부 Agent Provider와 일반 사용자에 대한 empirical pilot은 별도 검증 항목으로 유지합니다.

## 상세 문서

- 프로젝트 Quick Start: `sdlc/README.md`
- Starter Kit: `sdlc/starter-kits/`
- 공통 Contract: `sdlc/design/contracts/`
- Project Custom: `sdlc/custom/project/`
- Branch/Design metadata: `sdlc/design/branch-version.yaml`
