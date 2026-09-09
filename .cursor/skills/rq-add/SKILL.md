# Cursor Skill — /rq-add

프로젝트 진행 중 새 요구사항을 자연어로 간단히 추가하는 Skill이다.

실제 운영 규칙은 반드시 다음 Core Skill을 따른다.

```text
@sdlc/agent/skills/rq-add/SKILL.md
```

## 사용자 예

```text
/rq-add 승인 완료된 근무계획은 일반 사용자가 수정할 수 없게 해줘.
새 RQ 추가해줘. 퇴직자도 과거 급여명세서를 조회할 수 있어야 해.
요구사항 하나 추가하고 바로 분석해줘: 승인 완료 후에는 수정할 수 없게 해줘.
```

## 실행

1. 기존 RQ 의미 변경인지 새 RQ인지 먼저 구분한다.
2. 사용자가 말한 요구 원문을 바꾸지 않고 보존한다.
3. 원문 의미를 확장하지 않는 짧은 제목을 만든다.
4. 다음 공식 Harness 명령을 사용한다.

```bash
python sdlc/scripts/harness.py rq-add \
  --title "<짧은 제목>" \
  --request "<사용자 원문>"
```

외부 요구 ID가 실제로 주어졌을 때만 `--external-id`를 추가한다.

5. 성공하면 생성된 RQ ID, 제목, 원문, RQ 작업목록 갱신 상태를 사람에게 짧게 알려준다.
6. 사용자가 `바로 분석해줘`라고 요청한 경우에만 새 RQ를 Target으로 `/work`를 이어서 수행한다.

기존 RQ를 바꾸는 요청은 `/change`, 대량 Excel 요구사항은 `/intake`, PM 정보만 바꾸는 요청은 `/rq-list`로 보낸다.
