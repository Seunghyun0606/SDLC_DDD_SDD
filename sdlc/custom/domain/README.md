# Domain Overlay

Domain별 차이는 `sdlc/custom/domain/<domain>/` 아래에 둔다.

```text
<domain>/
├─ config/
├─ rules/
├─ templates/
└─ standards/
```

현재 RQ/PGM Domain이 일치할 때만 Context에 주입하며, 모든 Domain 규칙을 항상 로드하지 않는다.
