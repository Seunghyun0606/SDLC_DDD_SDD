# SDLC Framework 개발 자산

이 디렉터리는 **실제 프로젝트에 배포하지 않는 SDLC Harness Framework 개발/검증 자산**의 명시적 경계다.

## 원칙

- 실제 프로젝트 사용자 진입점: `docs/00_시작/START_HERE.md`
- 실제 프로젝트 설정 SSOT: `.sdlc/project.yaml`
- 프로젝트 실행 Runtime: `sdlc/scripts/` 중 Project Runtime/선택 Extension
- Runtime Contract: 현재 `sdlc/design/contracts/`에 유지한다. 이 경로는 이름과 달리 일부가 실제 Runtime dependency다.
- Framework Pilot/Test/Sample/Design History는 Project Scaffold에 복사하지 않는다.
- `framework/` 아래 자산은 무조건 `FRAMEWORK_ONLY`다.

## 현재 물리 구조와 이동 정책

```text
framework/
├─ README.md
├─ ASSET_INVENTORY_V110.md
└─ samples/                 # Framework 비교/교육/검증 fixture

기존 위치 중 Framework-only이지만 아직 이동하지 않은 경로
├─ tests/                   # CI convention 때문에 현재 위치 유지
├─ .github/                 # Framework CI
├─ docs/99_파일럿/          # Pilot evidence; 향후 framework/pilots/로 이동 후보
├─ docs/00_관리/            # 현재 legacy framework report와 project-generated 관리문서가 혼재
└─ sdlc/design/
   ├─ contracts/            # PROJECT dependency가 있으므로 유지
   ├─ baselines/            # FRAMEWORK_ONLY
   ├─ candidates/           # FRAMEWORK_ONLY
   ├─ reviews/              # FRAMEWORK_ONLY
   └─ validations/          # FRAMEWORK_ONLY
```

`framework/ASSET_INVENTORY_V110.md`가 각 폴더/파일의 현재 판정과 후속 이동/삭제 기준을 정의한다.
