# P0.1 Legacy Requirement Normalizer Validation

상태: `ACTIVE_P0_1_CANDIDATE`

## 목표

P0 Pilot에서 확인된 세 가지 Gap을 구현한다.

1. Legacy Requirement Normalizer
2. Group-level Requirement Boundary
3. Stage Input Pack Granularity Rule

## 실행 흐름

```text
Extraction Layer
→ SOURCE_ROW
→ EXACT Group Candidate
→ optional INFERRED Subgroup Candidate
→ Group-level Stage Input Pack
→ Boundary Review
→ Canonical RQ/FR
```

Normalizer는 Canonical RQ/FR를 발행하지 않는다.

## Deterministic Normalizer

입력은 Workbook 자체가 아니라 Extraction Layer가 만든 YAML이다.

```bash
python sdlc/scripts/normalize_legacy_requirements.py input.yaml -o normalization.yaml
python sdlc/scripts/validate_p0_contracts.py legacy-normalization normalization.yaml
```

기본 Group Key는 `Level2 + 요구사항명 EXACT`이다.

Group ID는 exact key의 SHA-256 앞 10자를 사용하므로 같은 입력에서는 Agent/실행순서와 무관하게 동일하다.

## Validator

```bash
python sdlc/scripts/test_p01_contracts.py

python sdlc/scripts/validate_p0_contracts.py legacy-normalization \
  sdlc/design/validation/p0.1-legacy-normalizer-v1/attendance-close-normalization.yaml

python sdlc/scripts/validate_p0_contracts.py rq-boundary \
  sdlc/design/validation/p0.1-legacy-normalizer-v1/attendance-close-group-boundary.yaml

python sdlc/scripts/validate_p0_contracts.py stage-pack \
  sdlc/design/validation/p0.1-legacy-normalizer-v1/attendance-close-stage-input-pack.yaml
```

## 근태마감 Pilot 기대 결과

`REQ_TM_TE016~054` 39건은 exact key 기준으로 Group Candidate 1개가 된다.

- Source ID: 39/39 보존
- Group Candidate: 1
- Canonical RQ 자동발행: 0
- Canonical FR 자동발행: 0
- Boundary: `OPEN / UNRESOLVED`
- Stage Pack Granularity: `GROUP`
- Boundary Escalation: `L2_OR_HUMAN`

기존 Pilot의 8개 Subgroup Candidate는 검토 편의를 위한 `INFERRED` 후보이며 Canonical Split을 의미하지 않는다.

## Fail Conditions

다음은 Validator가 실패시킨다.

- Source ID 중복/누락
- exact group 안에 다른 Level2 또는 요구사항명 혼입
- Source Row가 여러 exact group에 중복 소속
- Normalizer가 `publish_canonical=true`
- `UNRESOLVED`인데 Canonical ID 발행
- 여러 Row Boundary인데 ROW scope 사용
- 여러 Row Stage Pack인데 ROW granularity 사용
- GROUP/SUBGROUP Pack인데 source_group_id 누락

## P0.1 판정 기준

이 P0.1은 Legacy Inventory의 Intake/Decompose/Handoff 재현성을 개선한다.
Source Repository가 없는 상태에서는 DISCOVERY 이후를 완료시키지 않으며 기존 P0의 Safe Stop을 유지한다.
