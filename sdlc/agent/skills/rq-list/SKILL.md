# SDLC Core Skill — rq-list

이 파일은 특정 IDE나 Agent 제품에 종속되지 않는 PM용 RQ 작업목록 관리 Skill의 **Core Source of Truth**다.

목표는 PM이 Canonical/Runtime JSON을 직접 수정하지 않고 **Excel/CSV와 자연어 요청으로 RQ 배정·일정·메모를 관리**하도록 돕는 것이다.

## 1. 사용자 의도

다음 요청은 모두 이 Skill로 처리한다.

- `RQ 작업목록 보여줘`
- `PM용 RQ 관리 엑셀 만들어줘`
- `RQ_작업관리.xlsx 수정한 내용 반영해줘`
- `RQ-001 담당 개발자를 홍길동으로 지정해줘`
- `/rq-list refresh`
- `/rq-list export`
- `/rq-list import docs/00_관리/RQ_작업관리.xlsx`

## 2. 가장 중요한 원칙

1. **PM 계획정보는 업무 기준 정보를 변경하지 않는다.**
   - `rq-list`는 `sdlc/canonical/store.json`의 Requirement/Business Rule/Scope를 수정하지 않는다.
   - 일정·담당자·WBS·우선순위·메모는 `.sdlc/management/rq-planning.json`에만 저장한다.
2. **RQ 식별자는 Intake가 만든 값을 사용한다.**
   - Excel/CSV에서 새 RQ를 임의 생성하지 않는다.
   - 새 요구사항은 먼저 `harness.py intake`로 등록한다.
3. **진행상태는 사람이 수동으로 완료 처리하지 않는다.**
   - 현재 상태, 사람 확인 필요, 검증근거, 생성 문서 상태, 다음 작업은 Runtime 근거로 다시 계산한다.
4. **일반 PM에게 JSON 편집을 요구하지 않는다.**
   - 기본 UX는 Excel/CSV Export → 편집 → Import 또는 자연어 요청이다.
5. 사람에게 설명할 때 내부 상태명보다 `현재 상태`, `확인 필요`, `검증근거`, `다음 작업`처럼 쉬운 표현을 사용한다.

## 3. 기본 실행 경계

실제 Runtime 진입점은 하나다.

```bash
python sdlc/scripts/harness.py rq-list <command>
```

직접 `rq_worklist.py`를 호출하기보다 공식 Harness 진입점을 우선한다.

## 4. 요청별 처리

### 4.1 현재 전체 목록을 보고 싶을 때

```bash
python sdlc/scripts/harness.py rq-list refresh
```

갱신 결과:

```text
.sdlc/management/rq-planning.json        # PM 계획정보
sdlc/runtime/management/rq-worklist.json # 기계용 합성 결과
docs/00_관리/RQ_작업목록.md              # 사람이 보는 목록
```

Agent는 실행 후 `docs/00_관리/RQ_작업목록.md`의 핵심만 요약한다. 전체 Runtime JSON을 그대로 사용자에게 덤프하지 않는다.

### 4.2 PM용 Excel을 만들 때

기본 권장 명령:

```bash
python sdlc/scripts/harness.py rq-list export \
  --format xlsx \
  --output docs/00_관리/RQ_작업관리.xlsx
```

CSV 요청이면:

```bash
python sdlc/scripts/harness.py rq-list export \
  --format csv \
  --output docs/00_관리/RQ_작업관리.csv
```

`RQ`, `요구사항명`, `외부 요구ID`는 식별/조회용이다. 그 뒤 PM 컬럼은 프로젝트가 자유롭게 추가하거나 삭제할 수 있다.

### 4.3 PM이 수정한 Excel/CSV를 반영할 때

```bash
python sdlc/scripts/harness.py rq-list import docs/00_관리/RQ_작업관리.xlsx
```

기본 Import는 파일에 있는 PM 컬럼 구성을 현재 PM 관리 컬럼으로 사용한다.

일부 컬럼만 합치고 기존 PM 컬럼을 유지해야 한다는 의도가 명확할 때만:

```bash
python sdlc/scripts/harness.py rq-list import 일부수정.csv --merge-columns
```

Import 전에 다음을 확인한다.

- 파일이 실제로 존재하는가
- `RQ` 컬럼이 있는가
- RQ 값이 현재 Canonical에 존재하는가
- `요구사항명`, `외부 요구ID`는 조회용이며 업무 의미 변경 입력으로 사용하지 않는가

Import 후에는 결과를 refresh하여 사람이 보는 목록까지 갱신됐는지 확인한다.

### 4.4 한 RQ의 담당자/우선순위만 빠르게 바꿀 때

고급/자동화 호환 경로:

```bash
python sdlc/scripts/harness.py rq-list assign \
  --target RQ-001 \
  --engineering-owner "홍길동" \
  --test-owner "김QA" \
  --priority HIGH
```

사용자가 자연어로 한두 항목만 바꾸어 달라고 하면 `assign`을 사용할 수 있다. 다수 RQ 일괄관리는 Excel/CSV를 우선한다.

## 5. PM 파일에서 허용되는 것

예:

```text
담당개발자
업무담당
고객담당
우선순위
Sprint
목표배포일
계약WBS
이슈
PM메모
```

이 컬럼들은 프로젝트 관리용이며 Framework 고정 Schema일 필요가 없다.

## 6. PM 파일에서 업무 변경으로 처리하면 안 되는 것

다음 요청은 `rq-list`로 처리하지 않는다.

- 요구사항 내용 변경
- Business Rule 변경
- TO-BE 정책 변경
- Scope 변경
- 취소/삭제의 업무적 의미 확정

이런 내용은 `/change` 경계로 넘긴다.

Source/DB/Program 실제 현행을 다시 조사해야 하는 요청은 `/work`로 넘긴다.

## 7. 오류/불일치 처리

- 존재하지 않는 RQ가 있으면 새 RQ를 만들지 말고 Intake 필요를 알려준다.
- 파일의 `요구사항명`이 현재 기준 정보와 달라도 그 값으로 Canonical을 덮어쓰지 않는다.
- Import 실패 시 `.sdlc/management/rq-planning.json`을 사람이 직접 고치라고 안내하지 않는다. 원인을 설명하고 입력 파일을 수정한다.
- Runtime에서 계산한 `현재 상태`를 PM 입력값으로 덮어쓰지 않는다.

## 8. 사람에게 보여줄 결과

작업 완료 보고는 간결하게 다음을 우선한다.

- 처리한 RQ 수
- PM 컬럼 수 또는 변경한 항목
- 생성/갱신 파일 경로
- 실패/확인 필요 항목
- Canonical 업무 기준 정보는 변경하지 않았다는 사실

상세 운영법은 `docs/00_시작/12_RQ_작업목록_운영가이드.md`를 따른다.
