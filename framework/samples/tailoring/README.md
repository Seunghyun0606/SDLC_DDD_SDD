# Tailoring Framework Sample

이 디렉터리는 **프로젝트 Runtime이 직접 읽지 않는 Framework 비교/교육/검증용 Sample**이다.

Runtime Profile 검색 경로는 다음 두 곳이다.

```text
sdlc/custom/project/tailoring/
sdlc/tailoring/standard/
```

따라서 여기의 `project-*.example.yaml`과 비교 fixture는 `.sdlc/project.yaml`의 실제 설정 Source of Truth가 아니다.

## 포함 파일

- `project-standard-3.example.yaml`: Legacy/Formal 내부 3종 비교용
- `project-standard-5.example.yaml`: Legacy/Formal 내부 5종 비교용
- `project-full.example.yaml`: Stage-oriented Full 호환 비교용
- `CUSTOMER_A_INTERNAL_3.yaml`: 고객사 Custom 3종 Profile 작성 예시
- `comparison-canonical.example.json`: 구조 비교용 합성 Canonical fixture
- `PROFILE_COMPARISON_3_5_FULL.md`: 동일 Canonical에서 3/5/Full 구조 비교 결과

## 재현

```bash
python sdlc/scripts/generate_tailoring_profile_comparison.py \
  --root . \
  --store framework/samples/tailoring/comparison-canonical.example.json \
  --target RQ-COMP-001 \
  --change-level L3 \
  --out-json sdlc/runtime/tailoring-comparison.json \
  --out-md sdlc/runtime/tailoring-comparison.md
```

이 Sample은 구조 검증용이며 신규 프로젝트 기본값은 `ENGINEERING_SDD_COMPACT`다. 실제 프로젝트에서 Custom Profile을 사용할 때는 `sdlc/custom/project/tailoring/` 아래에 배치한다.
