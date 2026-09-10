from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUIDE_ROOT = ROOT / "docs" / "00_시작"


class GuideConsistencyV110Test(unittest.TestCase):
    def read(self, rel: str) -> str:
        return (ROOT / rel).read_text(encoding="utf-8")

    def json(self, rel: str) -> dict:
        return json.loads(self.read(rel))

    def test_start_here_links_all_distributed_start_guides(self):
        start = self.read("docs/00_시작/START_HERE.md")
        package = self.json("sdlc/design/contracts/harness-package-contract.json")
        scaffold = self.json("sdlc/design/contracts/project-scaffold-contract.json")
        excluded = set(scaffold.get("exclude_exact") or [])
        rows = list(package.get(scaffold["base_file_set"], [])) + list(scaffold.get("add_required_files") or [])
        active = sorted({
            rel for rel in rows
            if rel.startswith("docs/00_시작/")
            and rel.endswith(".md")
            and rel not in excluded
            and not rel.endswith("/START_HERE.md")
        })
        self.assertTrue(active)
        for rel in active:
            name = Path(rel).name
            self.assertTrue((ROOT / rel).is_file(), rel)
            self.assertIn(name, start, name)

    def test_start_here_covers_primary_user_entrypoints(self):
        start = self.read("docs/00_시작/START_HERE.md")
        harness = self.read("sdlc/scripts/harness.py")
        for command in ["setup", "intake", "rq-add", "rq-list", "rq-ref", "work", "review", "change", "check", "customer-view"]:
            self.assertIn(command, harness, command)
            self.assertIn(command, start, command)

    def test_cli_reference_covers_every_official_harness_command(self):
        harness = self.read("sdlc/scripts/harness.py")
        guide = self.read("docs/00_시작/18_HARNESS_CLI_기능_참조가이드.md")
        command_line = next(line for line in harness.splitlines() if "Commands: setup |" in line)
        commands = command_line.split("Commands:", 1)[1].split('"', 1)[0].strip().split(" | ")
        self.assertGreaterEqual(len(commands), 10)
        for command in commands:
            self.assertIn(f"`{command}`", guide, command)
        scaffold = self.json("sdlc/design/contracts/project-scaffold-contract.json")
        self.assertIn("docs/00_시작/18_HARNESS_CLI_기능_참조가이드.md", scaffold["add_required_files"])

    def test_guides_use_current_template_roots(self):
        active = [
            "START_HERE.md",
            "02_PROJECT_설정가이드.md",
            "02A_PROJECT_CONFIG_옵션_상세가이드.md",
            "03_TAILORING_설정가이드.md",
            "04_TEMPLATE_및_산출물_가이드.md",
            "05_이해관계자별_작업가이드.md",
            "07_BROWNFIELD_SSOT_현행화가이드.md",
            "11_INPUT_자료_준비가이드.md",
            "12_RQ_작업목록_운영가이드.md",
            "13_RQ_참고문서_레지스트리_가이드.md",
            "14_한글_인코딩_및_외부명령_가이드.md",
            "15_고객문서_미리보기_가이드.md",
            "16_프로젝트_개발가이드_Agent_적용가이드.md",
            "17_RQ_간편추가_가이드.md",
            "18_HARNESS_CLI_기능_참조가이드.md",
        ]
        removed_stage_template_path = "sdlc/templates/" + "core"
        for name in active:
            text = (GUIDE_ROOT / name).read_text(encoding="utf-8")
            self.assertNotIn(removed_stage_template_path, text, name)
            self.assertNotIn("sdlc/guides/", text, name)

    def test_config_reference_covers_runtime_context_and_dead_config_boundaries(self):
        guide = self.read("docs/00_시작/02A_PROJECT_CONFIG_옵션_상세가이드.md")
        for key in [
            "schema_version",
            "project.mode",
            "delivery.profile",
            "change.level_policy",
            "change.minimum_level",
            "change.default_level",
            "change.target_levels",
            "agent.execution",
            "agent.provider.command",
            "technology.build",
            "technology.test",
            "source.roots",
            "source.excludes",
            "git.protected_branches",
            "documents.engineering.profile",
            "documents.customer.profile",
            "documents.customer.projection_contract",
            "documents.customer.projection_config",
            "documents.machine.visibility",
            "unresolved",
            "extensions.*",
        ]:
            self.assertIn(key, guide, key)
        for phrase in [
            "Runtime Switch",
            "Document / Agent Context",
            "Dead Config",
            "source.excludes",
            "Profile의 `output_path`",
            "Allowlist-first",
            "safety_floor",
            "config-usage.json",
        ]:
            self.assertIn(phrase, guide, phrase)

    def test_setup_guide_is_procedure_not_duplicate_config_reference(self):
        setup = self.read("docs/00_시작/02_PROJECT_설정가이드.md")
        self.assertIn("setup --name", setup)
        self.assertIn("check --setup", setup)
        self.assertIn("02A_PROJECT_CONFIG_옵션_상세가이드.md", setup)
        self.assertIn("HEADLESS", setup)
        self.assertIn("ENGINEERING_SDD_COMPACT", setup)
        self.assertIn("CUSTOMER_STANDARD_3", setup)
        self.assertIn("--include-legacy-compatibility", setup)
        self.assertIn("--force", setup)
        self.assertIn("--no-validate", setup)
        self.assertNotIn("## 7. Level 이력은 어디에 남는가", setup)

    def test_tailoring_guide_matches_default_and_legacy_distribution(self):
        guide = self.read("docs/00_시작/03_TAILORING_설정가이드.md")
        scaffold = self.json("sdlc/design/contracts/project-scaffold-contract.json")
        self.assertIn("ENGINEERING_SDD_COMPACT", guide)
        self.assertIn("CUSTOMER_STANDARD_3", guide)
        self.assertIn("CUSTOMER_WATERFALL_FULL", guide)
        self.assertIn("PROFILE_PRIMARY_SET", guide)
        self.assertIn("--include-legacy-compatibility", guide)
        for name in ["STANDARD_3", "STANDARD_5", "STAGE_ORIENTED_FULL"]:
            self.assertIn(name, guide)
            self.assertIn(f"sdlc/tailoring/standard/{name}.yaml", scaffold["exclude_exact"])
            self.assertIn(f"sdlc/tailoring/standard/{name}.yaml", scaffold["legacy_compatibility_package"])

    def test_template_guide_explains_semantic_projection_profile_and_program_threshold(self):
        guide = self.read("docs/00_시작/04_TEMPLATE_및_산출물_가이드.md")
        profile = self.read("sdlc/tailoring/standard/ENGINEERING_SDD_COMPACT.yaml")
        for marker in [
            "sdlc/templates/semantic/",
            "sdlc/templates/engineering/",
            "sdlc/templates/customer/",
            "sdlc/templates/management/",
            "sdlc/tailoring/standard/*.yaml",
        ]:
            self.assertIn(marker, guide, marker)
        self.assertIn("min_change_level: L3", profile)
        self.assertIn("`min_change_level: L3`", guide)
        self.assertIn("Template은 빈 입력 Form이 아니다", guide)

    def test_input_and_worklist_guides_distinguish_bulk_and_incremental_rq(self):
        input_guide = self.read("docs/00_시작/11_INPUT_자료_준비가이드.md")
        worklist_guide = self.read("docs/00_시작/12_RQ_작업목록_운영가이드.md")
        for text in [input_guide, worklist_guide]:
            self.assertIn("rq-add", text)
            self.assertIn("intake", text)
            self.assertIn("17_RQ_간편추가_가이드.md", text)
        self.assertIn("대량", input_guide)
        self.assertIn("소수", input_guide)
        self.assertIn("--candidate-only", input_guide)
        self.assertIn("--profile", input_guide)
        self.assertIn("PM Excel에서 새 RQ ID를 임의 생성하지 않는다", worklist_guide)

    def test_rq_add_guide_matches_runtime_duplicate_semantics(self):
        guide = self.read("docs/00_시작/17_RQ_간편추가_가이드.md")
        runtime = self.read("sdlc/scripts/rq_add.py")
        self.assertIn("같은 요청 원문", guide)
        self.assertIn("같은 제목 + 다른 요청 원문", guide)
        self.assertIn("--allow-duplicate", guide)
        self.assertIn("RQ_ALREADY_EXISTS", runtime)
        self.assertIn("RQ_ADD_DUPLICATE_REVIEW_REQUIRED", runtime)
        self.assertIn("RQ_ADD_CONFLICT_RETRY_REQUIRED", runtime)
        self.assertIn("SINGLE_WRITER_FILE_DERIVED", runtime)

    def test_customer_guide_uses_default_profile_paths_and_labels_custom_example(self):
        guide = self.read("docs/00_시작/15_고객문서_미리보기_가이드.md")
        profile = self.read("sdlc/tailoring/standard/CUSTOMER_STANDARD_3.yaml")
        self.assertIn("docs/20_고객/<RQ>/", guide)
        self.assertIn('output_root: "docs/20_고객"', profile)
        self.assertIn("00_work-map.md", guide)
        self.assertIn("specs/RQ-001.md", guide)
        self.assertIn("HRIS Custom Profile", guide)
        self.assertIn("/customer-view refresh RQ-001", guide)

    def test_project_development_guide_states_policy_vs_runtime_audit_boundary(self):
        guide = self.read("docs/00_시작/16_프로젝트_개발가이드_Agent_적용가이드.md")
        reference = self.read("sdlc/agent/skills/work/references/project-development-context.md")
        self.assertIn("Agent Policy / Skill Contract", guide)
        self.assertIn("Deterministic Runtime Audit", guide)
        self.assertIn("모든 Guide read event", guide)
        self.assertIn("모든 개발가이드를 매번 무조건 선로딩하지 않는다", guide)
        self.assertIn("sdlc/custom/project/rules", reference)
        self.assertIn("sdlc/custom/project/standards", reference)

    def test_encoding_guide_matches_process_contract(self):
        guide = self.read("docs/00_시작/14_한글_인코딩_및_외부명령_가이드.md")
        contract = self.json("sdlc/design/contracts/process-execution-contract.json")
        self.assertIn("현재 지원한다", guide)
        self.assertIn("COMSPEC /d /s /c", guide)
        self.assertIn("pwsh", guide)
        self.assertIn("powershell", guide)
        self.assertIn("ExecutionPolicy Bypass", guide)
        self.assertIn("shell=True", guide)
        self.assertEqual(contract["capture_policy"]["capture_mode"], "BYTES_FIRST")

    def test_config_reference_is_distributed_in_project_scaffold(self):
        scaffold = self.json("sdlc/design/contracts/project-scaffold-contract.json")
        rel = "docs/00_시작/02A_PROJECT_CONFIG_옵션_상세가이드.md"
        self.assertIn(rel, scaffold["add_required_files"])
        self.assertIn("Project Config option reference", scaffold["distribution_boundary"]["PROJECT_REQUIRED"])

    def test_start_here_does_not_tell_distributed_project_to_self_scaffold(self):
        start = self.read("docs/00_시작/START_HERE.md")
        scaffold = self.json("sdlc/design/contracts/project-scaffold-contract.json")
        self.assertIn("Framework 관리자가", start)
        self.assertIn("생성된 Project Scaffold 안에는 포함되지 않는다", start)
        self.assertIn("sdlc/scripts/build_project_scaffold.py", scaffold["framework_distribution_tools"])
        self.assertIn("sdlc/design/contracts/project-scaffold-contract.json", scaffold["framework_distribution_tools"])

    def test_brownfield_guide_labels_reverse_tools_as_extension(self):
        guide = self.read("docs/00_시작/07_BROWNFIELD_SSOT_현행화가이드.md")
        package = self.json("sdlc/design/contracts/harness-package-contract.json")
        self.assertIn("Brownfield Extension", guide)
        self.assertIn("기본 Minimum Executable Core가 아니라", guide)
        for rel in [
            "sdlc/scripts/build_reverse_inputs.py",
            "sdlc/scripts/detect_source_drift.py",
            "sdlc/scripts/run_source_reverse_check.py",
            "sdlc/scripts/generate_program_spec_reverse_candidate.py",
        ]:
            self.assertIn(rel, package["deployment_sets"]["BROWNFIELD_EXTENSION"])
            self.assertIn(rel, guide)

    def test_compatibility_notice_guides_are_not_distributed(self):
        scaffold = self.json("sdlc/design/contracts/project-scaffold-contract.json")
        for rel in [
            "docs/00_시작/01_STANDARD_SCAFFOLD_사용가이드.md",
            "docs/00_시작/06_CUSTOM_SCAFFOLD_적용가이드.md",
        ]:
            self.assertIn(rel, scaffold["exclude_exact"])
        start = self.read("docs/00_시작/START_HERE.md")
        self.assertIn("Compatibility Notice", start)
        self.assertIn("신규 Project Scaffold에는 배포되지", start)

    def test_customer_generated_paths_are_profile_aware_in_scaffold_contract(self):
        scaffold = self.json("sdlc/design/contracts/project-scaffold-contract.json")
        generated = scaffold["distribution_boundary"]["GENERATED"]
        self.assertTrue(any("docs/20_고객/" in row for row in generated))
        self.assertTrue(any("docs/20_customer/" in row for row in generated))
        self.assertEqual(scaffold["customer_output_path_authority"], "selected tailoring profile artifact output_path")

    def test_legacy_requirement_definition_example_is_compatibility_notice(self):
        guide = self.read("docs/00_시작/examples/요구사항_정의_완성예시.md")
        self.assertIn("Compatibility Notice", guide)
        self.assertIn("Work Unit", guide)
        self.assertIn("신규 Project 산출물 Template으로 사용하지 않는다", guide)
        self.assertNotIn("REQ_TM_FL001", guide)


if __name__ == "__main__":
    unittest.main()
