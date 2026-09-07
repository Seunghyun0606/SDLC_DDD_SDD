# 고객 커뮤니케이션 Template

고객 문서는 내부 설계 문서나 Canonical 구조를 그대로 보여주는 문서가 아니다. 내부 업무 의미와 검증 결과를 바탕으로 고객이 이해하고 합의할 내용만 한국어 자연어로 재구성한 Generated View다.

## 표준 원칙
- 고객 본문에는 요청 배경, 기대 결과, 업무 흐름, 업무 규칙, 범위, 영향, 합의·미확정 사항, 테스트·인수·운영 정보처럼 고객에게 필요한 의미만 표시한다.
- Canonical Entity ID, Relation, Revision, Provenance, Evidence Class, Confidence, Stage/Change Level, Queue/Guard Code, Source Hash/Locator 같은 내부 정보는 기본적으로 고객 문서에 표시하지 않는다.
- Canonical ID와 Traceability는 **Machine-side Mapping으로 계속 유지**한다. 고객 문서에서 숨긴다고 내부 추적성이 사라지는 것은 아니다.
- 기술 상세와 근거 상세는 기본 OFF다. 고객/프로젝트가 명시적으로 요구할 때만 선택 부록으로 활성화한다.
- Customer Projection은 필요한 의미를 먼저 Allowlist로 선택한 뒤 자연어 표현으로 변환한다. Sanitizer는 잘못 유입된 내부 표현을 제거하는 2차 방어선으로 사용한다.
- 필수 단락은 모든 고객/프로젝트에서 유지하고 선택 단락은 `sdlc/config/customer-document-profile.json`에서 켜거나 끈다.
- 고객 회의에서 새로 나온 합의나 변경은 고객 문서만 별도 원장처럼 수정하지 않고 `/change` 또는 `/work` Round-trip으로 원래 의미와 근거에 반영한다.
- 고객 용어가 다른 경우 `terminology_overrides`로 표시 용어만 바꾼다. 내부 Canonical 식별자와 관계는 Machine-side에서 유지한다.
