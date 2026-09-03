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


CONFIG = load("agent_neutral_config", "sdlc/scripts/runtime_config.py")
BOOT = load("agent_neutral_boot", "sdlc/scripts/bootstrap_project.py")
HARNESS = load("agent_neutral_harness", "sdlc/scripts/harness.py")
CHECK = load("agent_neutral_check", "sdlc/scripts/run_check.py")


class AgentNeutralExecutionTest(unittest.TestCase):
    def _bootstrap(self, root: Path, provider_command=None):
        return BOOT.bootstrap(
            root,
            name="agent-neutral-sample",
            mode="GREENFIELD",
            delivery="STANDARD",
            provider_command=provider_command,
            validate=False,
        )

    def _put_requirement(self, root: Path):
        path = root / "sdlc/canonical/store.json"
        store = BOOT.APPLY.load_store(path)
        store["entities"]["RQ-001"] = {
            "id": "RQ-001",
            "entity_type": "RQ",
            "truth_status": "GIVEN",
            "fields": {"title": "sample requirement", "description": "샘플 요구사항"},
            "provenance": [],
        }
        BOOT.APPLY.save_store(path, store)

    def _append(self, root: Path, text: str):
        path = root / ".sdlc/project.yaml"
        path.write_text(path.read_text(encoding="utf-8") + text, encoding="utf-8")

    def test_agent_omitted_defaults_to_interactive_and_is_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._bootstrap(root)
            resolved = CONFIG.resolve_runtime_config(root)
            self.assertEqual("INTERACTIVE", resolved["agent_execution_mode"])
            runtime = CONFIG.resolve_agent_runtime(
                resolved["project"],
                legacy_provider=CONFIG.load_config(root / CONFIG.DEFAULT_PROVIDER_CONFIG_PATH),
            )
            self.assertEqual("INTERACTIVE", runtime["execution_mode"])
            self.assertTrue(runtime["ready"])
            self.assertFalse(runtime["provider_required"])
            self.assertEqual([], resolved["usage"]["dead"])

            checked = CHECK.check(root, setup_only=True)
            self.assertEqual("READY", checked["status"])
            self.assertEqual("INTERACTIVE", checked["setup"]["agent_execution"]["mode"])
            self.assertFalse(checked["setup"]["provider"]["required"])

    def test_explicit_interactive_is_runtime_config_not_dead_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._bootstrap(root)
            self._append(root, '\nagent:\n  execution: "INTERACTIVE"\n')
            resolved = CONFIG.resolve_runtime_config(root)
            self.assertIn("agent.execution", resolved["usage"]["runtime"])
            self.assertEqual([], resolved["usage"]["dead"])
            paths = CONFIG.materialize_effective_profiles(root, resolved)
            execution = json.loads(paths["agent_execution"].read_text(encoding="utf-8"))
            provider = json.loads(paths["provider_config"].read_text(encoding="utf-8"))
            self.assertEqual("INTERACTIVE", execution["execution_mode"])
            self.assertFalse(execution["provider_required"])
            self.assertEqual("INTERACTIVE_AGENT", provider["provider_class"])
            self.assertFalse(provider["enabled"])

    def test_headless_requires_command_and_materializes_external_provider(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._bootstrap(root)
            self._append(root, '\nagent:\n  execution: "HEADLESS"\n')
            with self.assertRaisesRegex(ValueError, "requires agent.provider.command"):
                CONFIG.resolve_runtime_config(root)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._bootstrap(root)
            self._append(
                root,
                '\nagent:\n'
                '  execution: "HEADLESS"\n'
                '  provider:\n'
                '    id: "TEST_PROVIDER"\n'
                '    timeout_seconds: 90\n'
                '    command:\n'
                '      - "python"\n'
                '      - "provider.py"\n'
                '      - "{context_path}"\n'
                '      - "{result_path}"\n',
            )
            resolved = CONFIG.resolve_runtime_config(root)
            paths = CONFIG.materialize_effective_profiles(root, resolved)
            execution = json.loads(paths["agent_execution"].read_text(encoding="utf-8"))
            provider = json.loads(paths["provider_config"].read_text(encoding="utf-8"))
            self.assertEqual("HEADLESS", execution["execution_mode"])
            self.assertTrue(execution["provider_required"])
            self.assertEqual("PROJECT_ENTRY", execution["config_source"])
            self.assertTrue(provider["enabled"])
            self.assertEqual("EXTERNAL_AGENT", provider["provider_class"])
            self.assertEqual("TEST_PROVIDER", provider["provider_id"])
            self.assertEqual(90, provider["timeout_seconds"])

    def test_enabled_legacy_provider_remains_headless_compatibility(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._bootstrap(root, provider_command='python -c "print(1)"')
            resolved = CONFIG.resolve_runtime_config(root)
            legacy = CONFIG.load_config(root / CONFIG.DEFAULT_PROVIDER_CONFIG_PATH)
            runtime = CONFIG.resolve_agent_runtime(resolved["project"], legacy_provider=legacy)
            self.assertEqual("HEADLESS", runtime["execution_mode"])
            self.assertEqual("LEGACY_PROVIDER_CONFIG", runtime["config_source"])
            self.assertTrue(runtime["provider_required"])
            self.assertIn("deprecation", runtime)

    def test_interactive_work_prepares_handoff_without_provider(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._bootstrap(root)
            self._put_requirement(root)
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                rc = HARNESS.main(["work", "--root", str(root), "--target", "RQ-001"])
            self.assertEqual(0, rc, out.getvalue())
            result = json.loads(out.getvalue())
            self.assertEqual("INTERACTIVE_HANDOFF_READY", result["status"])
            self.assertEqual("INTERACTIVE", result["execution_mode"])
            self.assertFalse(result["canonical_applied"])
            self.assertEqual("sdlc/agent/skills/work/SKILL.md", result["core_skill"])
            context = root / result["context_path"]
            stage_result = root / result["result_path"]
            self.assertTrue(context.is_file())
            self.assertFalse(stage_result.is_file())
            ctx = json.loads(context.read_text(encoding="utf-8"))
            self.assertEqual("INTERACTIVE", ctx["agent_execution"]["mode"])
            self.assertIn("interactive_baseline", ctx)

    def test_interactive_change_prepares_handoff_without_provider(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._bootstrap(root)
            self._put_requirement(root)
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                rc = HARNESS.main([
                    "change", "--root", str(root), "--target", "RQ-001",
                    "--change", "조회 조건을 변경한다",
                ])
            self.assertEqual(0, rc, out.getvalue())
            result = json.loads(out.getvalue())
            self.assertEqual("INTERACTIVE_CHANGE_HANDOFF_READY", result["status"])
            self.assertEqual("sdlc/agent/skills/change/SKILL.md", result["core_skill"])
            self.assertFalse(result["canonical_applied"])
            self.assertTrue((root / result["context_path"]).is_file())

    def test_plan_only_keeps_backward_compatible_plan_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._bootstrap(root)
            self._put_requirement(root)
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                rc = HARNESS.main(["work", "--root", str(root), "--target", "RQ-001", "--plan-only"])
            self.assertEqual(0, rc, out.getvalue())
            result = json.loads(out.getvalue())
            self.assertEqual("PLAN_READY", result["status"])
            self.assertEqual("RQ-001", result["plan"]["target"]["id"])
            self.assertEqual("INTERACTIVE", result["plan"]["agent_execution"]["mode"])

    def test_host_adapters_point_to_vendor_neutral_core(self):
        core = ROOT / "sdlc/agent/skills/work/SKILL.md"
        cursor = ROOT / ".cursor/skills/work/SKILL.md"
        codex = ROOT / "AGENTS.md"
        claude = ROOT / "CLAUDE.md"
        self.assertTrue(core.is_file())
        for path in [cursor, codex, claude]:
            self.assertTrue(path.is_file(), path)
            self.assertIn("sdlc/agent/skills/work/SKILL.md", path.read_text(encoding="utf-8"))
        for name in ["requirement", "clarify", "process", "discovery", "impact", "design", "program", "development", "test", "verify"]:
            self.assertTrue((ROOT / f"sdlc/agent/skills/work/references/{name}.md").is_file(), name)


if __name__ == "__main__":
    unittest.main()
