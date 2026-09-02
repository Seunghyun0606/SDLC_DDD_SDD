import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name, rel):
    path = ROOT / rel
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


CONFIG = load("wp02_config", "sdlc/scripts/runtime_config.py")
BOOT = load("wp02_boot", "sdlc/scripts/bootstrap_project.py")
HARNESS = load("wp02_harness", "sdlc/scripts/harness.py")
CHECK = load("wp02_check", "sdlc/scripts/run_check.py")


VALID_PROJECT = '''schema_version: 1
project:
  name: "sample"
  mode: "BROWNFIELD"
delivery:
  profile: "FAST"
technology:
  language: "Java"
  framework: "Spring"
  build:
    - "./mvnw -q -DskipTests package"
  test:
    - "./mvnw test"
source:
  roots:
    - "app/src/main/java"
  test_roots:
    - "app/src/test/java"
  resource_roots: []
  excludes:
    - "target/**"
git:
  branch_strategy: "pull-request"
  protected_branches:
    - "main"
documents:
  language: "ko-KR"
unresolved: []
'''


class ProjectEntryConfigTest(unittest.TestCase):
    def _bootstrap(self, root: Path, delivery="STANDARD"):
        return BOOT.bootstrap(
            root,
            name="sample",
            mode="GREENFIELD",
            delivery=delivery,
            validate=False,
        )

    def _put_requirement(self, root: Path):
        store_path = root / "sdlc/canonical/store.json"
        store = BOOT.APPLY.load_store(store_path)
        store["entities"]["RQ-001"] = {
            "id": "RQ-001",
            "entity_type": "RQ",
            "truth_status": "GIVEN",
            "fields": {"title": "sample requirement"},
            "provenance": [],
        }
        BOOT.APPLY.save_store(store_path, store)

    def test_bootstrap_creates_one_human_entry_and_machine_compatibility(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = self._bootstrap(root)
            entry = root / ".sdlc/project.yaml"
            self.assertTrue(entry.is_file())
            self.assertEqual(".sdlc/project.yaml", report["user_config"])
            self.assertEqual("PROJECT_ENTRY", report["runtime_config_source"])
            self.assertEqual([], report["config_usage"]["dead"])
            self.assertNotIn("{{", entry.read_text(encoding="utf-8"))

            for rel in ["sdlc/config/project-profile.yaml", "sdlc/config/source-profile.yaml"]:
                text = (root / rel).read_text(encoding="utf-8")
                self.assertIn("MACHINE-GENERATED COMPATIBILITY SNAPSHOT", text)
                self.assertIn("DO NOT EDIT", text)
                self.assertIn(".sdlc/project.yaml", text)

            for rel in [
                ".sdlc/runtime/effective/project-profile.json",
                ".sdlc/runtime/effective/source-profile.json",
                ".sdlc/runtime/effective/project-context.json",
                ".sdlc/runtime/effective/config-usage.json",
            ]:
                self.assertTrue((root / rel).is_file(), rel)

    def test_fast_standard_full_are_resolved_from_project_entry(self):
        expected = {
            "FAST": (1, False),
            "STANDARD": (3, True),
            "FULL": (4, True),
        }
        for profile, (hops, has_verify) in expected.items():
            with self.subTest(profile=profile), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self._bootstrap(root, profile)
                resolved = CONFIG.resolve_runtime_config(root)
                policy = CONFIG.delivery_policy(resolved["project_profile"])
                self.assertEqual(profile, policy["profile"])
                self.assertEqual(hops, policy["graph_hops"])
                self.assertEqual(has_verify, "VERIFY" in policy["enabled_stages"])

    def test_harness_work_uses_project_entry_for_delivery_and_source_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._bootstrap(root)
            (root / ".sdlc/project.yaml").write_text(VALID_PROJECT, encoding="utf-8")
            self._put_requirement(root)

            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                rc = HARNESS.main(["work", "--root", str(root), "--target", "RQ-001", "--plan-only"])
            self.assertEqual(0, rc, out.getvalue())
            result = json.loads(out.getvalue())
            plan = result["plan"]
            self.assertEqual("FAST", plan["delivery"]["profile"])
            self.assertIn("app/src/main/java", plan["source_policy"]["allowed_write_roots"])

            effective = json.loads((root / ".sdlc/runtime/effective/source-profile.json").read_text(encoding="utf-8"))
            self.assertEqual(["./mvnw -q -DskipTests package"], effective["build"]["commands"])
            self.assertEqual(["./mvnw test"], effective["test"]["commands"])

    def test_stale_legacy_profile_cannot_override_project_entry_in_official_harness(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._bootstrap(root)
            (root / ".sdlc/project.yaml").write_text(VALID_PROJECT, encoding="utf-8")
            (root / "sdlc/config/source-profile.yaml").write_text(
                "schema_version: 1\nsource:\n  roots:\n    - \"DO_NOT_USE_THIS_ROOT\"\nbuild:\n  commands: []\ntest:\n  commands: []\n",
                encoding="utf-8",
            )
            routed, resolved = HARNESS._runtime_profile_args(["--root", str(root), "--target", "RQ-001", "--plan-only"])
            self.assertEqual("PROJECT_ENTRY", resolved["source_kind"])
            self.assertNotIn("DO_NOT_USE_THIS_ROOT", CONFIG.source_roots(resolved["source_profile"]))
            source_arg = Path(routed[routed.index("--source-profile") + 1])
            effective = json.loads(source_arg.read_text(encoding="utf-8"))
            self.assertIn("app/src/main/java", CONFIG.source_roots(effective))
            self.assertNotIn("DO_NOT_USE_THIS_ROOT", CONFIG.source_roots(effective))

    def test_dead_config_is_rejected_instead_of_silently_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._bootstrap(root)
            entry = root / ".sdlc/project.yaml"
            entry.write_text(entry.read_text(encoding="utf-8") + "mystery:\n  unused_switch: true\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "mystery.unused_switch"):
                CONFIG.resolve_runtime_config(root)
            checked = CHECK.main(["--root", str(root), "--setup"])
            self.assertEqual(2, checked)

    def test_check_reads_single_entry_even_if_legacy_snapshots_are_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._bootstrap(root)
            (root / "sdlc/config/project-profile.yaml").unlink()
            (root / "sdlc/config/source-profile.yaml").unlink()
            result = CHECK.check(root, setup_only=True)
            self.assertEqual("PROJECT_ENTRY", result["setup"]["config_source"])
            self.assertTrue(result["setup"]["project_config"])
            self.assertFalse(result["setup"]["project_profile"])
            self.assertFalse(result["setup"]["source_profile"])
            self.assertEqual("STANDARD", result["project"]["delivery_profile"])

    def test_legacy_profiles_remain_a_fallback_only_when_project_entry_is_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "sdlc/config").mkdir(parents=True)
            (root / "sdlc/config/project-profile.yaml").write_text(
                "project:\n  name: \"legacy\"\n  mode: GREENFIELD\ndelivery:\n  profile: FAST\ndocuments:\n  language: ko-KR\nworkflow:\n  protected_branches:\n    - main\n",
                encoding="utf-8",
            )
            (root / "sdlc/config/source-profile.yaml").write_text(
                "schema_version: 1\nsource:\n  roots:\n    - src\n  test_roots: []\n  resource_roots: []\n  excludes: []\nbuild:\n  commands: []\ntest:\n  commands: []\n",
                encoding="utf-8",
            )
            resolved = CONFIG.resolve_runtime_config(root)
            self.assertEqual("LEGACY_PROFILES", resolved["source_kind"])
            self.assertEqual("FAST", CONFIG.delivery_profile(resolved["project_profile"]))
            self.assertEqual(["src"], CONFIG.source_roots(resolved["source_profile"]))

    def test_completed_example_has_no_dead_config(self):
        example = CONFIG.load_config(ROOT / "sdlc/config/project.example.yaml")
        classified = CONFIG.classify_project_config(example)
        self.assertEqual([], classified["dead"])
        self.assertIn("architecture.style", classified["document"])
        self.assertIn("technology.build", classified["runtime"])


if __name__ == "__main__":
    unittest.main()
