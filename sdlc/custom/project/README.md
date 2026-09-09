# Project Overlay

Core Harness를 복사해 수정하지 않고 이 프로젝트의 차이만 둔다.

권장 하위 구조:

```text
sdlc/custom/project/
├─ config/
├─ rules/
├─ templates/
└─ standards/
```

- `config/`: Source root, Stage 표시, Artifact 정책, PM 컬럼 등 프로젝트별 설정 보조자료
- `rules/`: 프로젝트 Architecture/금지사항/Convention/Tool 사용 강제 규칙
- `templates/`: Core Template의 Section 추가/대체 규칙
- `standards/`: Java/JSP/DB/SQL/Test/Security/배포 등 프로젝트 개발표준/가이드

Agent는 `/work`에서 현재 작업에 적용되는 `rules/`를 필수 규칙으로 확인하고, `standards/`는 현재 Stage/기술/변경 범위와 관련된 문서만 선택해서 읽는다. 모든 개발가이드를 매번 무조건 선로딩하지 않는다.

고객이 제공한 원본 개발표준 PDF/DOCX/XLSX는 `br-input/originals/`에 보존할 수 있다. 반복 적용할 확정 규칙은 `rules/` 또는 `standards/`에 사람이 읽기 쉬운 형태로 정리한다.

상세 사용법은 다음 가이드를 따른다.

```text
docs/00_시작/16_프로젝트_개발가이드_적용가이드.md
```

Core 안전 invariant를 제거하는 Override는 허용하지 않고 Validation Warning으로 남긴다.
