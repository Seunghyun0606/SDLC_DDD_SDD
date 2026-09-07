# Framework Archive

`framework/archive/`는 **현재 Runtime/설계의 Source of Truth가 아닌, 대체되거나 폐기된 Framework 운영 메타데이터와 스냅샷**을 보존하는 위치다.

## 원칙

- Archive 파일은 현재 동작을 설명하는 문서로 사용하지 않는다.
- 현재 자산 분류는 `framework/ASSET_INVENTORY_V110.md`를 따른다.
- 현재 설계는 `framework/design/branch-version.yaml`과 `framework/design/current/`를 따른다.
- 과거 Design Baseline/Candidate/Review 자체는 설계 이력의 일부이므로 `framework/design/`에 유지한다.
- `archive/`에는 과거의 **active metadata, inventory, migration snapshot**처럼 현재 파일로 남아 있으면 혼동되는 자산을 보존한다.
- Archive snapshot은 원칙적으로 수정하지 않는다. 설명이 필요하면 `INDEX.md`에 상태와 대체 경로를 추가한다.
- Project Scaffold에는 `framework/**`가 배포되지 않으므로 Archive도 프로젝트 Runtime에 포함되지 않는다.

## 현재 구조

```text
framework/archive/
├─ README.md
├─ INDEX.md
├─ config-usage-inventory-v19.json
└─ design-metadata/
   └─ branch-version-v1.9.0.yaml
```

Archive에서 현재 설정이나 현재 설계를 복사해 사용하지 않는다.
