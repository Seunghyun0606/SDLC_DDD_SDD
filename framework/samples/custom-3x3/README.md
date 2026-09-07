# Historical Custom 3×3 Pilot

이 디렉터리는 v1.9 `Custom 3×3 Template Pilot`의 목적과 이력을 보존하는 Framework-only archive다. 일반 프로젝트의 시작 가이드가 아니며 Project Scaffold에 포함하지 않는다.

## 왜 active guide에서 제거했는가

과거 Pilot 문서는 다음과 같은 v1.9 전용 가정을 포함했다.

- `documents.internal.profile` 중심 설명
- Engineering 3종 / Customer 3종 고정 예시
- `STANDARD_3`, `STANDARD_5`, `STAGE_ORIENTED_FULL`을 신규 프로젝트 선택지처럼 설명
- Customer Projection topology를 3종 중심으로 설명

v1.10의 현재 원칙은 다르다.

```text
Canonical = 의미 기준
Engineering Projection = 구현용 Living Spec topology
Customer Projection = 제출/합의용 topology
```

Engineering과 Customer topology는 서로 독립이며 3/5/8/13/N 조합을 독립적으로 선택할 수 있다. 신규 기본 Engineering Profile은 `ENGINEERING_SDD_COMPACT`이며 `documents.internal.profile`은 compatibility alias다.

## 현재 참고 위치

- Project 설정: `docs/00_시작/02_PROJECT_설정가이드.md`
- Tailoring/Custom Profile: `docs/00_시작/03_TAILORING_설정가이드.md`
- Template/산출물: `docs/00_시작/04_TEMPLATE_및_산출물_가이드.md`
- Framework 자산 분류: `framework/ASSET_INVENTORY_V110.md`

## 과거 원문

삭제된 다음 문서는 Git history에서 확인할 수 있다.

- `docs/00_시작/08_CUSTOM_3X3_01_CONFIG_및_폴더구조.md`
- `docs/00_시작/09_CUSTOM_3X3_02_이해관계자_실행프로세스.md`
- `docs/00_시작/10_CUSTOM_3X3_03_TEST_및_ChatGPT_분석가이드.md`

과거 원문을 신규 프로젝트 설정의 기준으로 사용하지 않는다.
