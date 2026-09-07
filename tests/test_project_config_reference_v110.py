from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / "docs/00_시작/02A_PROJECT_CONFIG_옵션_상세가이드.md"


def load(name: str, rel: str):
    path = ROOT / rel
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


CONFIG = load("test_config_reference_current", "sdlc/scripts/project_config.py")


class ProjectConfigReferenceV110Test(unittest.TestCase):
    def guide(self) -> str:
        return GUIDE.read_text(encoding="utf-8")

    def test_reference_mentions_every_current_explicit_config_leaf(self):
        text = self.guide()
        supported = set(CONFIG.BASE.RUNTIME_CONSUMED_PATHS)
        supported.update(CONFIG.BASE.DOCUMENT_ONLY_PATHS)
        supported.update(CONFIG.CONTROL_RUNTIME_PATHS)
        supported.update(CONFIG.CONTROL_DOCUMENT_PATHS)
        for path in sorted(supported):
            self.assertIn(path, text, msg=f"Project Config reference is missing supported key: {path}")

    def test_reference_mentions_context_and_extension_prefixes(self):
        text = self.guide()
        for prefix in CONFIG.BASE.DOCUMENT_CONTEXT_PREFIXES:
            self.assertIn(prefix + "*", text, msg=f"Project Config reference is missing context prefix: {prefix}")
        for prefix in CONFIG.BASE.EXTENSION_PREFIXES:
            self.assertIn(prefix + "*", text, msg=f"Project Config reference is missing extension prefix: {prefix}")
        self.assertIn("change.target_levels", text)

    def test_reference_matches_validated_option_enums_and_defaults(self):
        text = self.guide()
        for value in ["GREENFIELD", "BROWNFIELD", "HYBRID", "AUTO"]:
            self.assertIn(value, text)
        for value in ["FAST", "STANDARD", "FULL"]:
            self.assertIn(value, text)
        for value in ["INTERACTIVE", "HEADLESS"]:
            self.assertIn(value, text)
        for value in ["TYPO_ONLY", "READ_ONLY", "HUMAN_REVIEW"]:
            self.assertIn(value, text)
        for value in ["RQ", "MILESTONE", "PROJECT"]:
            self.assertIn(value, text)
        for value in ["HIDDEN", "DEBUG"]:
            self.assertIn(value, text)
        for value in ["L1", "L2", "L3", "L4", "L5"]:
            self.assertIn(value, text)
        for default in [
            CONFIG.DEFAULT_ENGINEERING_PROFILE,
            CONFIG.DEFAULT_CUSTOMER_PROFILE,
            CONFIG.DEFAULT_PM_PROFILE,
        ]:
            self.assertIn(default, text)

    def test_reference_distinguishes_effective_runtime_from_context_only_settings(self):
        text = self.guide()
        for phrase in [
            "Runtime Switch",
            "Resolved Policy",
            "Document / Agent Context",
            "Extension Config",
            "Dead Config",
            "source.excludes",
            "Profile의 `output_path`",
            "파일 시스템 자체를 잠그는 OS 권한 옵션은 아니다",
            "Customer direct Canonical 입력은 별도 Visibility Contract에 따라 Allowlist-first",
        ]:
            self.assertIn(phrase, text)

    def test_completed_example_remains_dead_config_free_and_links_reference(self):
        example_path = ROOT / "sdlc/config/project.example.yaml"
        example = CONFIG.load_config(example_path)
        classified = CONFIG.classify_project_config(example)
        self.assertEqual([], classified["dead"])
        raw = example_path.read_text(encoding="utf-8")
        self.assertIn("02A_PROJECT_CONFIG_옵션_상세가이드.md", raw)

    def test_customer_runtime_metadata_does_not_claim_relation_is_direct_input(self):
        runtime = (ROOT / "sdlc/scripts/customer_projection_runtime.py").read_text(encoding="utf-8")
        self.assertIn('"CANONICAL_ALLOWLIST_FIELDS"', runtime)
        self.assertNotIn('"CANONICAL_RELATION",', runtime)
        self.assertIn('"canonical_relation_expansion": False', runtime)


if __name__ == "__main__":
    unittest.main()
