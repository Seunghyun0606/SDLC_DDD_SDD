from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class FrameworkGovernanceV110Test(unittest.TestCase):
    def read(self, rel: str) -> str:
        return (ROOT / rel).read_text(encoding="utf-8")

    def test_active_design_metadata_is_v110(self):
        metadata = self.read("framework/design/branch-version.yaml")
        self.assertIn("branch: SDLC_DESIGN_SESSION_FIRST/projection-separation/v1.10.0", metadata)
        self.assertIn("version: 1.10.0", metadata)
        self.assertIn("candidate: v1.10.0-projection-separation", metadata)
        self.assertIn("status: ACTIVE_CANONICAL_SOURCE", metadata)
        self.assertIn("framework/design/current/V110_PROJECTION_SEPARATION_DESIGN.md", metadata)
        self.assertIn("framework/archive/INDEX.md", metadata)

    def test_current_design_entrypoint_exists_and_marks_history(self):
        governance = self.read("framework/design/README.md")
        current = self.read("framework/design/current/V110_PROJECTION_SEPARATION_DESIGN.md")
        self.assertIn("현재 설계 Source of Truth", governance)
        self.assertIn("HISTORICAL", governance)
        self.assertIn("ENGINEERING_SDD_COMPACT", current)
        self.assertIn("CUSTOMER_STANDARD_3", current)
        self.assertIn("sdlc/templates/semantic/", current)
        self.assertIn("framework/archive/", current)

    def test_session_metadata_points_to_current_framework_design(self):
        session = self.read("framework/design/session/SDLC_DESIGN_SESSION_FIRST.yaml")
        self.assertIn("branch_metadata_file: framework/design/branch-version.yaml", session)
        self.assertIn("current_branch: SDLC_DESIGN_SESSION_FIRST/projection-separation/v1.10.0", session)
        self.assertIn("current_version: 1.10.0", session)
        self.assertIn("SDLC_DESIGN_SESSION_FIRST/tailoring-control-plane/v1.9.0", session)
        self.assertIn("SDLC_DESIGN_SESSION_FIRST/projection-separation/v1.10.0", session)

    def test_archive_has_policy_index_and_v19_metadata_snapshot(self):
        archive_readme = self.read("framework/archive/README.md")
        archive_index = self.read("framework/archive/INDEX.md")
        snapshot = self.read("framework/archive/design-metadata/branch-version-v1.9.0.yaml")
        self.assertIn("현재 Runtime/설계의 Source of Truth가 아닌", archive_readme)
        self.assertIn("branch-version-v1.9.0.yaml", archive_index)
        self.assertIn("Original active path: framework/design/branch-version.yaml", snapshot)
        self.assertIn("branch: SDLC_DESIGN_SESSION_FIRST/tailoring-control-plane/v1.9.0", snapshot)
        self.assertIn("source blob db483ca22faecd13cb94e1118c859d4e96a11976", snapshot)

    def test_framework_inventory_describes_current_design_and_archive(self):
        framework = self.read("framework/README.md")
        inventory = self.read("framework/ASSET_INVENTORY_V110.md")
        for text in [framework, inventory]:
            self.assertIn("framework/design/branch-version.yaml", text)
            self.assertIn("framework/archive/", text)
            self.assertIn("sdlc/templates/semantic/", text)
        self.assertIn("ARCHIVED", inventory)
        self.assertIn("design-metadata/branch-version-v1.9.0.yaml", inventory)

    def test_active_framework_docs_do_not_reintroduce_old_stage_template_path(self):
        forbidden = "sdlc/templates/" + "core"
        active = [
            "framework/README.md",
            "framework/ASSET_INVENTORY_V110.md",
            "framework/design/README.md",
            "framework/design/branch-version.yaml",
            "framework/design/current/V110_PROJECTION_SEPARATION_DESIGN.md",
            "framework/validation/PROJECTION_SEPARATION_V110_VALIDATION.md",
            "framework/validation/TEMPLATE_ROLE_BOUNDARY_V110.md",
            "framework/validation/GUIDE_CONSISTENCY_V110.md",
            "framework/validation/FRAMEWORK_GOVERNANCE_V110.md",
        ]
        for rel in active:
            self.assertNotIn(forbidden, self.read(rel), rel)

    def test_changelog_records_v19_and_v110(self):
        changelog = self.read("framework/design/CHANGELOG.md")
        self.assertIn("## v1.10", changelog)
        self.assertIn("## v1.9", changelog)
        self.assertIn("Projection Separation", changelog)
        self.assertIn("Archive", changelog)


if __name__ == "__main__":
    unittest.main()
