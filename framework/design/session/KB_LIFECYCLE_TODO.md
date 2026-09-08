# TODO — 운영 Knowledge Base Lifecycle

상태: **DEFERRED / 후순위**

현재 Framework는 `run_knowledge_promotion.py`를 통해 검증된 Canonical Evidence에서 재사용 지식 후보를 만들고 Human Review를 요구하는 단계까지만 지원한다. 후보는 자동으로 운영 지식으로 승격되지 않는다.

## 현재 지원 경계

```text
Verified Canonical Evidence
→ Knowledge Promotion Candidate
→ Human Review Required
```

- 후보 대상 예: BR / DATA / API / NFR / STD / PROC
- `review_required = true`
- `auto_apply = false`
- Business Truth 자동 승격 금지

## 후속 구현 TODO

정식 운영 Knowledge Registry를 구현할 때 최소 다음 Lifecycle을 정의한다.

```text
CANDIDATE
→ REVIEWED
→ ACCEPTED / PUBLISHED
→ SUPERSEDED
→ RETIRED
```

필수 설계 항목:

1. Knowledge ID와 Version
2. Authority / 승인자
3. Effective From / Effective To
4. 원 Canonical Entity / Provenance / Source lineage
5. 적용 시스템·업무 Domain·Scope
6. 새 RQ/Work Unit Retrieval 규칙
7. Supersede/Retire 정책
8. 충돌 지식 Resolution
9. Project Knowledge와 Enterprise Knowledge 경계
10. 운영 중 Source Drift/Business Change 발생 시 재검토 정책
11. 검색/Context Injection 시 최신 유효 Version 선택 규칙
12. Project 종료 후 SM/운영 Repository로 승계하는 Export/Import 계약

## 안전 원칙

- Knowledge Registry가 Canonical Business Truth를 우회해 자동 수정하지 않는다.
- Source에서 관찰된 구현을 곧바로 업무 정책으로 승격하지 않는다.
- 이전 Version을 물리 삭제하지 않고 supersede/retire 관계를 추적한다.
- 운영 RQ는 유효 Knowledge를 참고하되 새로운 사실은 다시 Evidence/Review를 거친다.

이 TODO는 Project Scaffold 배포 자산이 아니라 Framework 설계 Backlog다.
