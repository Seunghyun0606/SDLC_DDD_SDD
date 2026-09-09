# Project Development Context

`/work`에서 프로젝트별 개발 가이드와 강제 규칙을 빠뜨리지 않기 위한 공통 Context 계약이다.

## 1. 읽기 우선순위

프로젝트 작업에서는 다음 순서로 Context를 적용한다.

```text
Core Safety / Authority Contract
→ .sdlc/project.yaml
→ sdlc/custom/project/rules/
→ 현재 작업에 관련된 sdlc/custom/project/standards/
→ 현재 Target Domain의 sdlc/custom/domain/<domain>/rules|standards/
→ br-input/glossary.csv (업무/고객 용어가 필요한 경우)
→ Target 관련 Source / Evidence
```

## 2. Project rules

위치:

```text
sdlc/custom/project/rules/
```

존재하는 프로젝트 Rule은 `/work` 시작 시 확인한다. 특히 Architecture 금지사항, Security, Tool 사용 의무, Source 변경 제한처럼 위반 시 구현이 잘못되는 규칙은 반드시 적용한다.

Project Rule은 Core의 안전/권한/추적성 규칙을 약화시킬 수 없다. 충돌하면 임의로 선택하지 말고 Configuration Gap으로 보고한다.

## 3. Project standards

위치:

```text
sdlc/custom/project/standards/
```

Standards 전체를 매번 선로딩하지 않는다. 현재 작업의 기술/Stage와 관련된 문서만 선택해서 읽는다.

예:

```text
Java 수정     → java-coding-guide.md
DB/SQL 수정   → database-guide.md, sql-guide.md
테스트 작성   → test-guide.md
배포 작업     → deployment-guide.md
```

단, 해당 문서가 현재 작업에 적용된다는 사실을 확인하기 전 Source를 수정하지 않는다.

## 4. Domain overlay

현재 RQ/PGM에 Domain이 지정되어 있을 때만:

```text
sdlc/custom/domain/<domain>/rules/
sdlc/custom/domain/<domain>/standards/
```

을 추가 적용한다. 모든 Domain 문서를 항상 읽지 않는다.

## 5. 고객/업무 용어

프로젝트에서 사용하는 실제 업무 용어는:

```text
br-input/glossary.csv
```

를 우선한다. Source의 변수명이나 일반적인 IT 용어를 고객 업무 용어보다 우선하지 않는다.

## 6. Context 최소화

- Rule: 적용 가능성이 있는 프로젝트 Rule은 먼저 확인한다.
- Standard: 현재 작업에 관련된 문서만 읽는다.
- Source: Target과 관련된 symbol/file부터 읽는다.
- 대형 개발 가이드는 Java/DB/Test/Security처럼 주제별로 나누는 것을 권장한다.
- Guide가 100페이지 PDF 원본이라면 원본은 `br-input/originals/`에 보존하고, Agent가 따라야 할 현재 적용 규칙은 `sdlc/custom/project/standards/`에 간결하게 정리한다.

## 7. 적용 여부를 작업 결과에 남긴다

개발/설계 결과에는 필요한 범위에서 다음을 확인 가능하게 남긴다.

- 어떤 Project Rule/Standard를 적용했는지
- 적용할 가이드가 없었는지
- 가이드와 현재 Source가 충돌하는지
- Tool 사용 의무가 있었는지와 실제 사용 결과

Machine taxonomy를 사람 문서 본문에 과도하게 노출하지 않고, 개발자에게 필요한 가이드명과 중요한 제약만 간결하게 적는다.
