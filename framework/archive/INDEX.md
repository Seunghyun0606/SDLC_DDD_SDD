# Archive Index

| Archive Asset | 원래 역할 | Archived Version | 현재 대체 경로 | 상태 |
|---|---|---:|---|---|
| `config-usage-inventory-v19.json` | v1.9 Config 사용 분류 Snapshot | v1.9 | `framework/ASSET_INVENTORY_V110.md`, `.sdlc/project.yaml`, `sdlc/scripts/project_config.py` | HISTORICAL_ONLY |
| `design-metadata/branch-version-v1.9.0.yaml` | v1.9 active branch metadata | v1.9 | `framework/design/branch-version.yaml` | IMMUTABLE_SNAPSHOT |

## Archive 판정 규칙

다음에 해당하면 Archive 후보로 본다.

1. 현재 파일명/경로에 남아 있으면 최신 상태로 오해될 수 있다.
2. Runtime은 더 이상 읽지 않는다.
3. 삭제하면 과거 설계/운영 판단 근거를 잃는다.
4. 현재 대체 Source of Truth가 명확하다.

반대로 Baseline/Candidate/Review/Validation처럼 **설계 진화 자체를 설명하는 이력**은 `framework/design/` 또는 `framework/validation/legacy/`에 유지하며 무조건 Archive로 옮기지 않는다.
