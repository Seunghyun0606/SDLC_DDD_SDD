# Cursor Skill — /customer-view

이 파일은 Cursor에서 고객문서 작성·현행화를 실행하기 위한 Host Adapter다.

실제 운영 규칙은 반드시 다음 Core Skill을 따른다.

```text
@sdlc/agent/skills/customer-view/SKILL.md
```

## 사용자 예

```text
/customer-view RQ-001
/customer-view refresh RQ-001
/customer-view status RQ-001
RQ-001 고객문서 최신화해줘.
A02 영향범위 문서 다시 만들어줘.
지금까지 개발/테스트된 내용으로 고객문서 보여줘.
```

## 실행 원칙

1. 먼저 Core Skill을 읽는다.
2. 프로젝트 Customer Profile과 `projection status`를 확인한다.
3. FINAL_REVIEW 또는 MANUAL_EDIT_DETECTED 문서를 자동 덮어쓰지 않는다.
4. 필요한 고객문서만 공식 Harness로 생성한다.

```bash
python sdlc/scripts/harness.py projection status --target <RQ>
python sdlc/scripts/harness.py customer-view --target <RQ> --type <customer-artifact-id>
```

5. Source/Test까지 최신 반영이 필요한데 근거가 부족하면 `/work`, 업무 의미 변경이면 `/change` 경계로 넘긴다.
6. 완료 후 생성된 고객문서 경로와 `최신 / 검토 대기 / 재검토 필요` 상태만 사람에게 간결하게 설명한다.
