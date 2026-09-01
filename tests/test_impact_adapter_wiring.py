import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ImpactAdapterWiringTest(unittest.TestCase):
    def test_impact_reference_requires_explicit_opt_in(self):
        text = (ROOT / ".cursor/skills/work/references/impact.md").read_text(encoding="utf-8")
        self.assertIn("adapter.enabled: true", text)
        self.assertIn("`available_pilots`에 존재한다는 이유만으로 자동 실행하지 않는다", text)
        self.assertIn("JAVA_SPRING_MYBATIS_STATIC_PILOT_V0_1", text)
        self.assertIn("PARTIAL_COVERAGE_GAPS", text)
        self.assertIn("static Pilot 결과를 runtime call graph 또는 Production 완전성으로 표현하지 않는다", text)

    def test_project_adapter_is_discoverable_but_not_core_required(self):
        harness = json.loads((ROOT / "sdlc/design/contracts/harness-package-contract.json").read_text(encoding="utf-8"))
        adapter = "sdlc/custom/project/adapters/impact/java_spring_mybatis.py"
        self.assertNotIn(adapter, harness["core_required_files"])
        profile = (ROOT / "sdlc/config/impact-adapter-profile.example.yaml").read_text(encoding="utf-8")
        self.assertIn("enabled: false", profile)
        self.assertIn(f"implementation: {adapter}", profile)
        self.assertIn("auto_enable: false", profile)
        self.assertIn("pilot_fixture_pass_does_not_mean_production_complete: true", profile)


if __name__ == "__main__":
    unittest.main()
