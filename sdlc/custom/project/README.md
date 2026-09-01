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

- `config/`: Source root, Stage 표시, Artifact 정책, PM 컬럼 등
- `rules/`: 프로젝트 Architecture/금지사항/Convention
- `templates/`: Core Template의 Section 추가/대체 규칙
- `standards/`: Java/DB/Test 등 프로젝트 개발표준

Core 안전 invariant를 제거하는 Override는 허용하지 않고 Validation Warning으로 남긴다.
