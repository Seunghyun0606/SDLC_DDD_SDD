# v1.9 Tailoring 실행 Sample

이 디렉터리는 같은 SDLC Stage/Canonical 의미를 유지하면서 프로젝트별 산출물 체계만 바꾸는 예시다.

## 핵심 확인점

```text
같은 RQ / 같은 Runtime Stage / 같은 Canonical snapshot
        ↓ documents.internal.profile만 변경
STANDARD_3          → 3종 통합 산출물
STANDARD_5          → 5종 역할 분리 산출물
STAGE_ORIENTED_FULL → 기존 Stage-oriented 10종 산출물
CUSTOMER_A_INTERNAL_3 → 고객사 Custom 3종 산출물
```

Stage를 3개/5개로 합치는 예제가 아니다. `DECOMPOSE → ... → DESIGN → PROGRAM → ...` 실행 의미는 유지된다.

## 파일

- `project-standard-3.example.yaml`: 내부 3종 + 고객 3종 + PM View
- `project-standard-5.example.yaml`: 내부 5종 + 고객 3종 + PM View
- `project-full.example.yaml`: 기존 Stage-oriented Full 호환
- `CUSTOMER_A_INTERNAL_3.yaml`: 고객사 Custom 3종 Profile 예시
- `comparison-canonical.example.json`: 3/5/Full 비교 전용 합성 Canonical fixture. 실제 고객 사실을 표현하지 않는다.
- `PROFILE_COMPARISON_3_5_FULL.md`: 동일 Canonical/RQ/L3/Stage sequence의 구조 비교 결과
- `sdlc/scripts/generate_tailoring_profile_comparison.py`: 위 비교를 재생성하는 실행 도구

## Profile 기본 검증

샘플 파일을 프로젝트의 `.sdlc/project.yaml`로 그대로 복사해서 사용하지 말고, 필요한 설정을 실제 프로젝트 사실에 맞춰 반영한다.

```bash
python sdlc/scripts/tailoring_runtime.py validate-profile --profile STANDARD_3
python sdlc/scripts/tailoring_runtime.py validate-profile --profile STANDARD_5
python sdlc/scripts/tailoring_runtime.py validate-profile --profile STAGE_ORIENTED_FULL
```

대표 RQ에 대해 다음을 비교한다.

```bash
python sdlc/scripts/harness.py work --target RQ-001 --stage DESIGN --plan-only
```

Profile을 바꾸더라도 `selection.stage`는 DESIGN으로 유지되고, `selection.artifact_path`/`template_path`만 Profile에 따라 달라져야 한다.

## 동일 Canonical 3/5/Full 구조 비교

재현 가능한 비교는 실제 프로젝트 Canonical을 변경하지 않고 전용 fixture를 입력으로 사용한다.

```bash
python sdlc/scripts/generate_tailoring_profile_comparison.py \
  --root . \
  --store sdlc/samples/tailoring/comparison-canonical.example.json \
  --target RQ-COMP-001 \
  --change-level L3 \
  --out-json sdlc/runtime/tailoring-comparison.json \
  --out-md sdlc/runtime/tailoring-comparison.md
```

기대 결과는 다음과 같다.

- `STANDARD_3`: 고유 Human Artifact 3종
- `STANDARD_5`: 고유 Human Artifact 5종
- `STAGE_ORIENTED_FULL`: 고유 Human Artifact 10종
- 세 Profile 모두 동일 Canonical fingerprint 사용
- 세 Profile 모두 동일 Runtime Stage sequence 유지
- `stage_preserved = true`
- `projection_creates_business_truth = false`

이 비교는 구조 검증이다. Agent가 각 Profile의 실제 문서 본문을 작성했을 때 의미가 동일한지, 사용자가 어느 Profile을 더 쉽게 검토하는지는 External Agent/Human first-use Pilot에서 별도로 검증한다.

## Custom Profile 적용

`CUSTOMER_A_INTERNAL_3.yaml`을 실제 프로젝트에서는 예를 들어 다음 위치로 둔다.

```text
sdlc/custom/project/tailoring/CUSTOMER_A_INTERNAL_3.yaml
```

그리고 `.sdlc/project.yaml`에서는 복잡한 Stage Mapping을 쓰지 않고 Profile ID만 선택한다.

```yaml
documents:
  internal:
    profile: CUSTOMER_A_INTERNAL_3
```

Custom Profile/Template이 누락되거나 잘못되면 명시적 Custom 설정은 fail-closed 해야 한다. 단, v1.8 Minimum Core만 배포된 Legacy 프로젝트에는 `STAGE_ORIENTED_FULL` package 누락 시 기존 Core Stage Artifact를 보존하는 호환 fallback이 적용된다.
