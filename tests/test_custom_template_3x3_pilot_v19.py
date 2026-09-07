from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "sdlc" / "scripts"


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


CONFIG = load("custom_3x3_config", "runtime_config_v19.py")
TAILOR = load("custom_3x3_tailor", "tailoring_runtime.py")
CUSTOMER = load("custom_3x3_customer", "customer_projection_runtime.py")


class CustomTemplate3x3PilotV19Test(unittest.TestCase):
    def test_project_config_registers_customer_projection_paths(self):
        project = CONFIG.load_config(ROOT / "sdlc/custom/project/config/project.custom-3x3.example.yaml")
        usage = CONFIG.classify_project_config(project)
        self.assertEqual([], usage["dead"])
        self.assertIn("documents.customer.projection_contract", usage["runtime"])
        self.assertIn("documents.customer.projection_config", usage["runtime"])
        self.assertEqual("CUSTOM_PILOT_INTERNAL_3", CONFIG.nested(project, "documents", "internal", "profile"))
        self.assertEqual("CUSTOM_PILOT_CUSTOMER_3", CONFIG.nested(project, "documents", "customer", "profile"))

    def test_custom_profiles_are_three_document_profiles(self):
        internal, _ = TAILOR.load_profile(ROOT, "CUSTOM_PILOT_INTERNAL_3")
        customer, _ = TAILOR.load_profile(ROOT, "CUSTOM_PILOT_CUSTOMER_3")
        self.assertEqual({"business_definition", "screen_design", "program_design"}, set(internal["artifacts"]))
        self.assertEqual({"solution_agreement", "delivery_scope", "acceptance_handover"}, set(customer["artifacts"]))
        self.assertTrue(all(x["audience"] == "INTERNAL_IT" for x in internal["artifacts"].values()))
        self.assertTrue(all(x["audience"] == "CUSTOMER" for x in customer["artifacts"].values()))
        self.assertTrue(all(x["authoring"] == "GENERATED_VIEW" for x in customer["artifacts"].values()))

    def make_project(self) -> Path:
        tmp = Path(tempfile.mkdtemp(prefix="sdlc-custom-3x3-"))
        (tmp / ".sdlc").mkdir(parents=True)
        shutil.copy2(
            ROOT / "sdlc/custom/project/config/project.custom-3x3.example.yaml",
            tmp / ".sdlc/project.yaml",
        )
        shutil.copytree(ROOT / "sdlc/custom/project", tmp / "sdlc/custom/project")
        (tmp / "sdlc/canonical").mkdir(parents=True)
        (tmp / "sdlc/canonical/store.json").write_text(
            json.dumps({"revision": 7, "entities": {}, "relations": []}, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return tmp

    def generate_case(self, *, internal_rel: str, body: str, document_type: str, out_name: str, short_name: str):
        root = self.make_project()
        self.addCleanup(lambda: shutil.rmtree(root, ignore_errors=True))
        source = root / internal_rel
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text(body, encoding="utf-8")
        result = CUSTOMER.generate(
            root,
            target="RQ-001",
            document_type=document_type,
            inputs=[internal_rel],
            out=f"docs/20_고객/RQ-001/{out_name}",
            short_name=short_name,
        )
        text = (root / result["artifact_path"]).read_text(encoding="utf-8")
        metadata = json.loads((root / f"sdlc/runtime/projections/RQ-001-{result['artifact_id']}.json").read_text(encoding="utf-8"))
        return result, text, metadata

    def test_business_definition_uses_custom_customer_template(self):
        result, text, metadata = self.generate_case(
            internal_rel="docs/10_산출물/RQ-001/01_업무정의서.md",
            document_type="solution_agreement",
            out_name="A01_업무정의서.md",
            short_name="주문상태 개선",
            body="""# 업무정의서\n\n## 한눈에 보기\n주문 상태 표시 개선\n\n## 요구사항 및 업무 목적\n고객이 배송 상태를 쉽게 확인한다.\n\n## AS-IS / TO-BE\nAS-IS는 코드값, TO-BE는 한글 상태명이다.\n\n## 업무 범위와 규칙\n주문 상세 화면만 변경한다.\n\n## 미확정 사항\n없음\n\n## 다음 작업\n화면 설계를 확인한다.\n""",
        )
        self.assertEqual("CUSTOM_PILOT_CUSTOMER_3", result["customer_tailoring_profile"])
        self.assertTrue(result["template_path"].endswith("customer/A01_업무정의서.md"))
        self.assertEqual(["IMPACT"], result["source_stages"])
        self.assertIn("# 주문상태 개선 업무정의서", text)
        self.assertIn("고객이 배송 상태를 쉽게 확인한다.", text)
        self.assertNotIn("요구·업무·기능 합의서", text)
        self.assertNotIn("{{", text)
        self.assertEqual("CUSTOM_PILOT_CUSTOMER_3", metadata["profile_id"])
        self.assertFalse(metadata["business_truth_authority"])

    def test_screen_design_uses_custom_customer_template(self):
        result, text, _ = self.generate_case(
            internal_rel="docs/10_산출물/RQ-001/02_화면설계서.md",
            document_type="delivery_scope",
            out_name="A02_화면설계서.md",
            short_name="주문상태 개선",
            body="""# 화면설계서\n\n## 한눈에 보기\n주문 상세 화면 개선\n\n## 화면 목적과 사용자\n주문 고객이 사용한다.\n\n## AS-IS 화면 / TO-BE 화면\n코드 상태를 한글 라벨로 변경한다.\n\n## 화면 구성과 필드\n배송상태 필드를 변경한다.\n\n## 동작·Validation\n조회 시 상태 라벨을 표시한다.\n\n## AC / Test\n배송중 상태가 정상 노출된다.\n\n## 미확정 사항\n없음\n\n## 다음 작업\n프로그램 설계를 진행한다.\n""",
        )
        self.assertEqual(["DESIGN"], result["source_stages"])
        self.assertTrue(result["template_path"].endswith("customer/A02_화면설계서.md"))
        self.assertIn("# 주문상태 개선 화면설계서", text)
        self.assertIn("주문 고객이 사용한다.", text)
        self.assertNotIn("{{", text)

    def test_program_design_uses_custom_customer_template(self):
        result, text, _ = self.generate_case(
            internal_rel="docs/10_산출물/RQ-001/03_프로그램설계서.md",
            document_type="acceptance_handover",
            out_name="A03_프로그램설계서.md",
            short_name="주문상태 개선",
            body="""# 프로그램설계서\n\n## 한눈에 보기\n주문 조회 프로그램 변경\n\n## 실제 구현 Target\nOrderDetailService의 상태 변환을 변경한다.\n\n## 구현 Delta\n코드값 표시를 사용자 라벨 표시로 변경한다.\n\n## 조건부 기술 제어\n추가 Interface 영향 없음.\n\n## 테스트 연결\n배송 상태 표시 회귀 테스트를 수행한다.\n\n## Reconciliation / AS-BUILT\n실제 Source와 설계 변경을 비교한다.\n\n## 미확정 사항\n없음\n\n## 다음 작업\n고객 인수 후 AS-BUILT를 현행화한다.\n""",
        )
        self.assertEqual(["KNOWLEDGE_PROMOTION"], result["source_stages"])
        self.assertTrue(result["template_path"].endswith("customer/A03_프로그램설계서.md"))
        self.assertIn("# 주문상태 개선 프로그램설계서", text)
        self.assertIn("OrderDetailService의 상태 변환을 변경한다.", text)
        self.assertNotIn("{{", text)


if __name__ == "__main__":
    unittest.main()
