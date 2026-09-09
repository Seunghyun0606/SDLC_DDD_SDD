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
3. `br-input/glossary.csv`가 있으면 고객/프로젝트 표준 업무용어를 먼저 확인한다.
4. FINAL_REVIEW 또는 MANUAL_EDIT_DETECTED 문서를 자동 덮어쓰지 않는다.
5. 필요한 고객문서만 공식 Harness로 초안 생성한다.

```bash
python sdlc/scripts/harness.py projection status --target <RQ>
python sdlc/scripts/harness.py customer-view --target <RQ> --type <customer-artifact-id>
```

6. **Runtime 초안을 그대로 고객문서 완료본으로 제시하지 않는다.** Core Skill의 `고객 문장 작성 단계`에 따라 같은 사실만 사용해 고객 관점의 짧고 자연스러운 한국어 문장으로 다시 작성한다.
7. Java Class/Method, Table/Column, Query ID, 파일 경로, 내부 상태코드 같은 구현 식별자는 고객이 명시적으로 요구하지 않으면 기본 본문에서 제거하고, 확인된 업무 의미로 설명한다. 업무 의미를 확정할 수 없으면 추측하지 않고 확인 필요로 남긴다.
8. Agent가 표현을 다듬은 뒤 해당 파일을 `projection generated`로 다시 등록하여 현재 hash를 생성 문서 기준으로 기록한다.
9. Source/Test까지 최신 반영이 필요한데 근거가 부족하면 `/work`, 업무 의미 변경이면 `/change` 경계로 넘긴다.
10. 완료 후 생성된 고객문서 경로와 `최신 / 검토 대기 / 재검토 필요` 상태만 사람에게 간결하게 설명한다.
