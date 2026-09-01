# 수정사항 발생 시 어디서부터 고칠까 — Candidate A Pilot

## 시나리오 1: 업무정책 변경 — 이번 CR
`월마감 후 승인 수정요청만 재집계, FORCE_CLOSE 제외`

시작점: `CR/Requirement`.

```text
Requirement Scope/BR
→ Process
→ Impact
→ Functional Design
→ PGM Spec
→ Task/Test
→ Source
→ Verify
```

## 시나리오 2: UI 문구만 변경
업무동작/AC/PGM 영향이 없으면 RQ/BR을 다시 만들지 않는다. 관련 UI Task/PGM Spec부터 변경하고 Trace만 유지한다.

## 시나리오 3: Mapper SQL 성능 개선
결과 의미가 동일하면 Requirement/Process는 `UNCHANGED`. `Impact/PGM Spec/Task/Test(performance)`부터 수정한다.

## 시나리오 4: Source 분석 중 RQ가 둘로 나뉘어야 함을 발견
`SCOPE_CHANGE_CANDIDATE`를 생성하고 Human Review 전에는 조용히 Split하지 않는다. Split 승인 후 새 RQ/FR relation과 downstream STALE을 재계산한다.

## Pilot 결론
'항상 requirement.md부터 전부 다시 작성'도 아니고 'Source만 바로 수정'도 아니다. 변경의 의미가 처음 달라지는 Canonical Entity/Artifact를 찾고 그 하위만 STALE 전파하는 방식이 적합하다.
