# Greenfield First Prompt

이 Repository는 신규 Greenfield 프로젝트다.

1. `project_bootstrap` 결과와 현재 제공된 Project Context / 고객 표준 / 회사 SOP / 요구사항만 사용한다.
2. 개발 언어, Framework, DB, 배포환경, Architecture, Coding/Naming/Logging/Error/Security/Test/CI-CD/Document Rule을 `CONFIRMED / CANDIDATE / OPEN`으로 분리한다.
3. 미확정 기술 선택이나 Business Truth를 임의로 확정하지 않는다.
4. 필요한 Human Decision은 OPEN Item으로 만들고, 각 항목의 owner와 필요한 evidence를 적는다.
5. 선택된 Artifact Profile(LITE/STANDARD/ENTERPRISE)을 확인한다.
6. 현재 Requirement가 있으면 INTAKE Stage Input Pack을 생성한다.
7. Conditional 산출물은 필요 근거가 있을 때만 `execution.requested_outputs`에 추가한다.
8. Source가 아직 없으면 Source Provider 부재를 실패로 처리하지 않는다.
9. 부작용 Action은 자동 요청하지 않는다.
10. 다음 실행 가능한 작업과 다음 Human Decision만 정리한다.
