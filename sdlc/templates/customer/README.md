# 고객 커뮤니케이션 Template

고객 문서는 내부 설계 문서를 다시 작성하는 별개의 진실 저장소가 아니다. 내부 Canonical과 단계 산출물을 바탕으로 고객이 이해하기 쉬운 한국어 자연어 View를 만든다.

## 표준 원칙
- 필수 단락은 모든 고객/프로젝트에서 유지한다.
- 선택 단락은 `sdlc/config/customer-document-profile.json`에서 켜거나 끈다.
- 기술 상세는 기본적으로 부록이며 고객/프로젝트 성격에 따라 본문으로 승격할 수 있다.
- 고객 회의에서 새로 나온 합의/변경은 고객 문서만 수정하지 말고 `/change` 또는 `/work`를 통해 Canonical에 다시 반영한다.
- 고객 용어가 다른 경우 `terminology_overrides`로 표시 용어만 바꾸며 RQ/FR/BR/PGM/AC/TC Canonical ID는 유지한다.
