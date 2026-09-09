from __future__ import annotations

import importlib.util
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def load_validator():
    path = ROOT / "sdlc/scripts/validate_human_facing_language.py"
    spec = importlib.util.spec_from_file_location("human_language_validator_v110", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


VALIDATOR = load_validator()


class HumanFacingLanguageV110Test(unittest.TestCase):
    def test_contract_has_required_plain_korean_mappings(self):
        contract = json.loads(read("sdlc/design/contracts/human-facing-language-contract.json"))
        terms = contract["preferred_terms"]
        expected = {
            "DEFERRED": "보류",
            "SOURCE_BLOCK": "개발 전 확인 필요",
            "ITERATE": "진행 가능·추후 보완",
            "Recheck At": "다시 확인할 시점",
            "Human Decision Queue": "추가 확인이 필요한 사항",
            "Canonical": "기준 정보",
            "Projection": "생성 문서",
            "Provenance": "근거 이력",
            "Evidence": "근거",
            "영속적": "저장 후 계속 유지되는",
        }
        for key, value in expected.items():
            self.assertEqual(value, terms[key])
        self.assertIn("AGENT_USER_MESSAGE", contract["scope"])
        self.assertIn("HITL_QUESTION", contract["scope"])

    def test_hitl_reference_separates_machine_state_from_user_wording(self):
        text = read("sdlc/agent/skills/work/references/hitl.md")
        self.assertIn("사람에게 보여주는 표현이 최우선", text)
        self.assertIn("human-facing-language-contract.json", text)
        self.assertIn("human-language.md", text)
        self.assertIn("DB에 저장되어 계속 유지되어야 하나요?", text)
        self.assertIn("지금 결정하기 어렵다면 보류", text)
        self.assertIn("일반 사용자에게 그대로 출력하지 않는다", text)
        for marker in ["DEFERRED", "SOURCE_BLOCK", "Recheck At", "Human Decision Queue"]:
            self.assertIn(marker, text)

    def test_root_agent_adapters_load_human_language_policy(self):
        agents = read("AGENTS.md")
        claude = read("CLAUDE.md")
        cursor = read(".cursor/rules/20-document-language.mdc")
        for text in [agents, claude, cursor]:
            self.assertIn("보류", text)
            self.assertIn("개발 전 확인 필요", text)
            self.assertIn("다시 확인할 시점", text)
            self.assertIn("영속", text)
        self.assertIn("human-facing-language-contract.json", agents)
        self.assertIn("human-facing-language-contract.json", claude)
        self.assertIn("human-facing-language-contract.json", cursor)

    def test_active_human_templates_do_not_expose_forbidden_raw_terms(self):
        errors = VALIDATOR.validate(ROOT)
        self.assertEqual([], errors, json.dumps(errors, ensure_ascii=False, indent=2))

    def test_hris_business_template_uses_plain_queue_labels(self):
        business = read("sdlc/custom/project/templates/hris-hunel/01_업무정의서.md")
        visible = re.sub(r"<!--.*?-->", "", business, flags=re.S)
        self.assertIn("추가 확인이 필요한 사항", visible)
        self.assertIn("다시 확인할 시점", visible)
        self.assertIn("개발 전 확인 필요", visible)
        self.assertIn("보류", visible)
        for raw in ["DEFERRED", "SOURCE_BLOCK", "ITERATE", "Recheck At", "Human Decision Queue", "영속적", "영속성"]:
            self.assertNotIn(raw, visible)

    def test_project_scaffold_packages_language_contract_and_reference(self):
        scaffold = json.loads(read("sdlc/design/contracts/project-scaffold-contract.json"))
        required = set(scaffold["add_required_files"])
        for rel in [
            "sdlc/design/contracts/human-facing-language-contract.json",
            "sdlc/agent/skills/work/references/human-language.md",
            "sdlc/scripts/validate_human_facing_language.py",
        ]:
            self.assertIn(rel, required)
            self.assertTrue((ROOT / rel).is_file())


if __name__ == "__main__":
    unittest.main()
