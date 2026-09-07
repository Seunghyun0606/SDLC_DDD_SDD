from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = ROOT / "sdlc/custom/project/templates/pilot-3x3"


class ProjectionTemplatesHideAgentOwnershipV19Test(unittest.TestCase):
    def test_human_projection_templates_hide_agent_ownership_labels(self):
        paths = [
            TEMPLATE_ROOT / "internal/01_업무정의서.md",
            TEMPLATE_ROOT / "internal/02_화면설계서.md",
            TEMPLATE_ROOT / "internal/03_프로그램설계서.md",
            TEMPLATE_ROOT / "customer/A01_업무정의서.md",
            TEMPLATE_ROOT / "customer/A02_화면설계서.md",
            TEMPLATE_ROOT / "customer/A03_프로그램설계서.md",
        ]
        forbidden = [
            "HUMAN_AUTHORITATIVE",
            "HUMAN_REVIEWED",
            "MACHINE_DERIVED",
            "AGENT_DRAFT_HUMAN_REVIEW",
            "GENERATED_VIEW",
            "<!--",
        ]
        for path in paths:
            text = path.read_text(encoding="utf-8")
            for marker in forbidden:
                self.assertNotIn(marker, text, f"{path} exposes framework/agent marker {marker}")


if __name__ == "__main__":
    unittest.main()
