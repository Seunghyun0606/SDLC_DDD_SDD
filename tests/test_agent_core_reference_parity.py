import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAMES = [
    "requirement",
    "clarify",
    "process",
    "discovery",
    "impact",
    "design",
    "program",
    "development",
    "test",
    "verify",
]


class AgentCoreReferenceParityTest(unittest.TestCase):
    def test_vendor_neutral_core_references_match_legacy_cursor_mirror(self):
        for name in NAMES:
            with self.subTest(name=name):
                core = ROOT / f"sdlc/agent/skills/work/references/{name}.md"
                legacy = ROOT / f".cursor/skills/work/references/{name}.md"
                self.assertTrue(core.is_file(), core)
                self.assertTrue(legacy.is_file(), legacy)
                self.assertEqual(
                    legacy.read_text(encoding="utf-8"),
                    core.read_text(encoding="utf-8"),
                    f"{name} reference diverged; migrate both or update the compatibility strategy explicitly",
                )


if __name__ == "__main__":
    unittest.main()
