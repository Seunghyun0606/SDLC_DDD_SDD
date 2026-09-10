import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
SCRIPTS = ROOT / "sdlc/scripts"


def load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


SAFE = load_module("customer_view_safety_v110", "customer_view_safe.py")


class CustomerViewSafetyAndCliGuideParityV110Test(unittest.TestCase):
    def read(self, rel: str) -> str:
        return (ROOT / rel).read_text(encoding="utf-8")

    def _customer_root(self, root: Path) -> None:
        (root / ".sdlc").mkdir(parents=True)
        (root / ".sdlc/project.yaml").write_text(
            """schema_version: 1
project:
  name: customer-safe-test
  mode: BROWNFIELD
delivery:
  profile: STANDARD
agent:
  execution: INTERACTIVE
documents:
  engineering:
    profile: ENGINEERING_SDD_COMPACT
  customer:
    profile: CUSTOMER_STANDARD_3
  pm:
    profile: PM_STANDARD
  machine:
    visibility: HIDDEN
""",
            encoding="utf-8",
        )
        copies = [
            "sdlc/tailoring/standard/CUSTOMER_STANDARD_3.yaml",
            "sdlc/design/contracts/customer-document-contract.json",
            "sdlc/config/customer-document-profile.json",
            "sdlc/templates/customer/standard/A01_요구_업무_기능_합의서.md",
            "sdlc/templates/customer/standard/A02_영향_개발범위_공유서.md",
            "sdlc/templates/customer/standard/A03_테스트_인수_운영_결과서.md",
        ]
        for rel in copies:
            dst = root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / rel, dst)
        store = root / "sdlc/canonical/store.json"
        store.parent.mkdir(parents=True)
        store.write_text(
            json.dumps(
                {
                    "revision": 1,
                    "entities": {
                        "RQ-001": {
                            "entity_type": "RQ",
                            "fields": {
                                "name": "승인 후 수정 제한",
                                "original_requirement": "승인된 계획은 일반 사용자가 수정할 수 없게 해주세요.",
                                "scope": "근무계획",
                            },
                        }
                    },
                    "relations": [],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def test_official_customer_view_blocks_final_review_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._customer_root(root)
            created = SAFE.generate_safe(
                root,
                target="RQ-001",
                document_type="solution_agreement",
                inputs=[],
            )
            self.assertEqual("CUSTOMER_VIEW_GENERATED", created["status"])
            artifact = root / created["artifact_path"]
            artifact.write_text("고객이 확정한 최종 문구\n", encoding="utf-8")
            reviewed = SAFE.LIFE.review(
                root,
                target="RQ-001",
                artifact_id="solution_agreement",
                reviewer="고객담당자",
                accepted=True,
                final_review=True,
            )
            self.assertEqual("FINAL_REVIEW", reviewed["status"])

            store = root / "sdlc/canonical/store.json"
            data = json.loads(store.read_text(encoding="utf-8"))
            data["revision"] = 2
            store.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

            blocked = SAFE.generate_safe(
                root,
                target="RQ-001",
                document_type="solution_agreement",
                inputs=[],
            )
            self.assertEqual("CUSTOMER_VIEW_OVERWRITE_BLOCKED", blocked["status"])
            self.assertEqual("고객이 확정한 최종 문구\n", artifact.read_text(encoding="utf-8"))

    def test_preview_keeps_official_lifecycle_metadata(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._customer_root(root)
            created = SAFE.generate_safe(
                root,
                target="RQ-001",
                document_type="solution_agreement",
                inputs=[],
            )
            official_meta = SAFE.LIFE.metadata_path(root, "RQ-001", "solution_agreement")
            before = official_meta.read_bytes()
            preview = SAFE.generate_safe(
                root,
                target="RQ-001",
                document_type="solution_agreement",
                inputs=[],
                out="docs/20_고객/RQ-001/미리보기_A01.md",
            )
            self.assertEqual("CUSTOMER_VIEW_PREVIEW_GENERATED", preview["status"])
            self.assertTrue(preview["official_lifecycle_preserved"])
            self.assertEqual(before, official_meta.read_bytes())
            self.assertNotEqual("solution_agreement", preview["artifact_id"])
            self.assertTrue(
                SAFE.LIFE.metadata_path(root, "RQ-001", preview["artifact_id"]).is_file()
            )
            self.assertTrue((root / preview["artifact_path"]).is_file())
            self.assertEqual(created["artifact_path"], preview["official_artifact_path"])

    def test_missing_target_routes_to_rq_creation_first(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._customer_root(root)
            result = SAFE.generate_safe(
                root,
                target="RQ-999",
                document_type="solution_agreement",
                inputs=[],
            )
            self.assertEqual("CUSTOMER_VIEW_TARGET_NOT_FOUND", result["status"])
            self.assertIn("rq-add", result["next_action"])
            self.assertIn("intake", result["next_action"])

    def test_guides_match_xlsx_and_separate_customer_refresh(self):
        input_guide = self.read("docs/00_시작/11_INPUT_자료_준비가이드.md")
        self.assertIn("주 입력 형식은 구조화된 XLSX", input_guide)
        self.assertIn("CSV는 요구사항의 주 Intake 파일로 직접 넣는 형식이 아니다", input_guide)

        artifact_guide = self.read("docs/00_시작/04_TEMPLATE_및_산출물_가이드.md")
        self.assertIn("Customer 문서는 `/work`나 `/change`만 실행했다고 자동 재작성되는 문서가 아니다", artifact_guide)
        self.assertIn("/customer-view refresh RQ-001", artifact_guide)

    def test_customer_guide_documents_review_and_preview_safety(self):
        guide = self.read("docs/00_시작/15_고객문서_미리보기_가이드.md")
        for marker in [
            "projection review",
            "--final-review",
            "--business-policy-edit",
            "별도 미리보기 Lifecycle",
            "자동으로 덮어쓰지 않는다",
        ]:
            self.assertIn(marker, guide, marker)

    def test_cli_reference_covers_actual_advanced_subcommands(self):
        guide = self.read("docs/00_시작/18_HARNESS_CLI_기능_참조가이드.md")
        for marker in [
            "구조화된 XLSX 요구사항 일괄 인입",
            "--provider-command",
            "projection review",
            "DEVELOPMENT_STARTED",
            "AS_BUILT_RECONCILED",
            "record\nrecommend\ndiscover\nmetrics",
            "baseline",
            "compact",
            "metrics summary",
            "--source-root`는 반복",
        ]:
            self.assertIn(marker, guide, marker)

    def test_harness_scaffold_check_and_package_use_current_safe_boundaries(self):
        harness = self.read("sdlc/scripts/harness.py")
        scaffold = json.loads(self.read("sdlc/design/contracts/project-scaffold-contract.json"))
        package = json.loads(self.read("sdlc/design/contracts/harness-package-contract.json"))
        check = self.read("sdlc/scripts/tailored_check.py")
        safe_rel = "sdlc/scripts/customer_view_safe.py"

        self.assertIn('"customer_view_safe.py"', harness)
        self.assertIn(safe_rel, scaffold["add_required_files"])
        self.assertIn(safe_rel, package["deployment_sets"]["CUSTOMER_EXTENSION"])
        self.assertNotIn(safe_rel, package["core_required_files"])
        self.assertIn("customer-view는 CUSTOMER_EXTENSION이 필요", package["deployment_sets"]["MINIMUM_EXECUTABLE_CORE"]["notes"])

        experience = package["document_experience"]
        self.assertEqual(safe_rel, experience["customer_view_safe_facade"])
        self.assertEqual("sdlc/scripts/customer_projection_runtime.py", experience["customer_projection_runtime"])
        self.assertEqual("sdlc/scripts/harness.py customer-view", experience["official_customer_view_entrypoint"])
        self.assertTrue(experience["customer_official_generation_uses_safe_facade"])
        self.assertTrue(experience["customer_final_review_overwrite_blocked"])
        self.assertTrue(experience["customer_preview_lifecycle_isolated_from_official_artifact"])

        for old in [
            "STALE_VIEW를 재생성",
            "Semantic Work Plan으로 개발",
            "Build Evidence를 확인",
            "Customer Acceptance 결정을 받는다",
            "Accepted Delta를 AS-BUILT에 Reconcile",
        ]:
            self.assertNotIn(old, check)
        self.assertIn("현재 기준에 맞게 생성 문서를 다시 만들고", check)
        self.assertIn("무엇이 바뀌었는가?", check)


if __name__ == "__main__":
    unittest.main()
