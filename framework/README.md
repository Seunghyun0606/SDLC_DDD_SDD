# SDLC Framework 개발 자산

이 디렉터리는 **실제 프로젝트에 배포하지 않는 SDLC Harness Framework 개발/검증 자산**의 명시적 경계다.

## 원칙

- 실제 프로젝트 사용자 진입점: `docs/00_시작/START_HERE.md`
- 실제 프로젝트 설정 SSOT: `.sdlc/project.yaml`
- 프로젝트 실행 Runtime: `sdlc/scripts/` 중 Project Runtime/선택 Extension
- Runtime Contract: `sdlc/design/contracts/`에 유지한다. 이 경로는 실제 Runtime dependency다.
- Framework Pilot/Test/Sample/Design History는 Project Scaffold에 복사하지 않는다.
- `framework/` 아래 자산은 무조건 `FRAMEWORK_ONLY`다.

## 현재 물리 구조

```text
framework/
├─ README.md
├─ ASSET_INVENTORY_V110.md
├─ design/                  # baseline/candidate/review/session/validation 설계 이력
├─ management/              # Framework 자체 작업목록/관리자료
├─ pilots/                  # Framework Pilot 및 과거 pilot history
├─ samples/                 # 비교/교육/검증 fixture
└─ validation/              # 검증 보고서 + validation assets/provider/fixture

tests/                      # CI convention 때문에 저장소 최상위 유지, FRAMEWORK_ONLY
.github/                    # Framework CI, FRAMEWORK_ONLY
sdlc/design/contracts/      # Runtime/Extension Contract, Project 배포 대상
sdlc/validation             # framework/validation/assets 를 가리키는 compatibility symlink
sdlc/guides                 # 제거됨; 사용자 가이드 SoT는 docs/00_시작

docs/00_관리/               # Project-generated / PM-facing output 전용
```

## Compatibility 원칙

과거 경로를 참조하는 기존 테스트/도구 때문에 필요한 경우 **복제 파일을 다시 만들지 않는다**. 가능한 경우 symlink 또는 최소 compatibility notice만 남기며, Project Scaffold에서는 제외한다.

예:

- `sdlc/validation` → `framework/validation/assets`
- `sdlc/config/customer-document-profile.example.json` → `customer-document-profile.json`

신규 Runtime과 신규 Project Scaffold는 항상 정식 경로를 사용해야 한다.

세부 파일별 판정은 `framework/ASSET_INVENTORY_V110.md`를 따른다.
