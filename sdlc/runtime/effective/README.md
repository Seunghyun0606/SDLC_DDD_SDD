# Effective Harness Runtime

`resolve_overlay.py`가 Core + Project/Domain Overlay를 합성한 결과를 생성하는 디렉터리다.

- Custom Source: `sdlc/custom/**`
- Generated Effective View: `sdlc/runtime/effective/**`
- Effective View를 직접 수정하지 않는다.
- `effective-manifest.json`에서 적용 순서와 파일별 SHA provenance를 확인한다.
