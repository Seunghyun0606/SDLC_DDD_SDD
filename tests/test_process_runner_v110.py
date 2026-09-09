from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
SCRIPT_DIR = ROOT / "sdlc/scripts"


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPT_DIR / filename)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


PROCESS = load("process_runner_v110_test", "process_runner.py")
CONFIG = load("runtime_config_process_v110_test", "runtime_config.py")
WORK = load("run_work_process_v110_test", "run_work.py")


class ProcessRunnerV110Test(unittest.TestCase):
    def test_cp949_subprocess_output_is_lossless(self):
        with tempfile.TemporaryDirectory() as td:
            code = "import sys; sys.stdout.buffer.write('근무계획 승인'.encode('cp949'))"
            result = PROCESS.run_process([sys.executable, "-c", code], cwd=td, timeout=10)

            self.assertEqual(0, result.returncode)
            self.assertEqual("근무계획 승인", result.stdout)
            self.assertEqual("cp949", result.stdout_decode.encoding)
            self.assertFalse(result.stdout_decode.lossy)
            self.assertTrue(result.output_decode_ok)

    def test_utf16_without_bom_process_output_is_detected_before_locale_fallback(self):
        raw = "PowerShell 결과 한글".encode("utf-16-le")
        decoded = PROCESS.decode_process_bytes(raw)

        self.assertEqual("utf-16-le", decoded.encoding)
        self.assertEqual("PowerShell 결과 한글", decoded.text)
        self.assertFalse(decoded.lossy)

    def test_utf16be_without_bom_process_output_is_detected(self):
        raw = "PowerShell 결과 한글".encode("utf-16-be")
        decoded = PROCESS.decode_process_bytes(raw)

        self.assertEqual("utf-16-be", decoded.encoding)
        self.assertEqual("PowerShell 결과 한글", decoded.text)
        self.assertFalse(decoded.lossy)

    def test_unknown_process_output_fails_closed_but_hash_is_preserved(self):
        decoded = PROCESS.decode_process_bytes(b"\x81")

        self.assertEqual("UNDECODABLE", decoded.status)
        self.assertEqual("", decoded.text)
        self.assertFalse(decoded.lossy)
        self.assertTrue(decoded.sha256.startswith("sha256:"))
        self.assertEqual(1, decoded.byte_length)

    def test_nul_delimited_utf8_is_allowed_only_when_requested(self):
        raw = "src/근태/근무계획.java\x00docs/설계.md\x00".encode("utf-8")
        blocked = PROCESS.decode_process_bytes(raw)
        allowed = PROCESS.decode_process_bytes(raw, allow_nul=True)

        self.assertEqual("UNDECODABLE", blocked.status)
        self.assertEqual("DECODED_PRIMARY", allowed.status)
        self.assertIn("근무계획.java\x00", allowed.text)

    def test_cmd_script_uses_comspec_without_shell_true(self):
        command, mode = PROCESS.prepare_command(
            [r".\build.cmd", "테스트"],
            platform_name="nt",
            env={"COMSPEC": r"C:\Windows\System32\cmd.exe"},
            which_fn=lambda _: None,
        )

        self.assertEqual("CMD_AUTO", mode)
        self.assertEqual(r"C:\Windows\System32\cmd.exe", command[0])
        self.assertEqual(["/d", "/s", "/c"], command[1:4])
        self.assertIn(r".\build.cmd", command[4])
        self.assertIn("테스트", command[4])

    def test_powershell_script_auto_resolves_pwsh_and_preserves_korean_path(self):
        def which(name: str):
            return r"C:\Program Files\PowerShell\7\pwsh.exe" if name == "pwsh.exe" else None

        command, mode = PROCESS.prepare_command(
            [r".\scripts\빌드.ps1", "-Mode", "Test"],
            platform_name="nt",
            which_fn=which,
        )

        self.assertEqual("PWSH_AUTO", mode)
        self.assertEqual(r"C:\Program Files\PowerShell\7\pwsh.exe", command[0])
        self.assertIn("-NoProfile", command)
        self.assertIn("-NonInteractive", command)
        self.assertIn("-File", command)
        self.assertNotIn("Bypass", command)
        self.assertIn(r".\scripts\빌드.ps1", command)

    def test_explicit_cmd_and_powershell_commands_are_not_rewrapped(self):
        cmd = ["cmd.exe", "/c", "echo", "한글"]
        ps = ["powershell.exe", "-NoProfile", "-Command", "Write-Output '한글'"]

        self.assertEqual((cmd, "CMD_EXPLICIT"), PROCESS.prepare_command(cmd, platform_name="nt"))
        self.assertEqual((ps, "POWERSHELL_EXPLICIT"), PROCESS.prepare_command(ps, platform_name="nt"))

    def test_windows_config_preserves_backslashes_and_execution_strips_escaped_outer_quotes(self):
        mvn = CONFIG.split_command_string(r".\mvnw.cmd test", platform_name="nt")
        ps = CONFIG.split_command_string(
            r"powershell.exe -File \".\scripts\빌드.ps1\"",
            platform_name="nt",
        )

        self.assertEqual(r".\mvnw.cmd", mvn[0])
        self.assertEqual("test", mvn[1])
        self.assertEqual("powershell.exe", ps[0])
        self.assertEqual("-File", ps[1])
        self.assertIn(r".\scripts\빌드.ps1", ps[2])

        prepared, mode = PROCESS.prepare_command(ps, platform_name="nt")
        self.assertEqual("POWERSHELL_EXPLICIT", mode)
        self.assertEqual(r".\scripts\빌드.ps1", prepared[2])

    def test_git_changed_paths_preserves_korean_filename(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            subprocess.run(["git", "init"], cwd=root, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            path = root / "src/근태/근무계획.java"
            path.parent.mkdir(parents=True)
            path.write_text("class X {}\n", encoding="utf-8")

            changed = WORK.git_changed_paths(root)

            self.assertIn("src/근태/근무계획.java", changed)

    def test_work_runtime_no_longer_uses_text_true_for_captured_processes(self):
        source = (SCRIPT_DIR / "run_work.py").read_text(encoding="utf-8")
        self.assertIn("PROCESS.run_process", source)
        self.assertNotIn("text=True", source)
        self.assertIn("core.quotepath=false", source)
        self.assertIn("--name-only\", \"-z", source)

    def test_process_execution_contract_is_fail_closed_and_shell_explicit(self):
        contract = json.loads(
            (ROOT / "sdlc/design/contracts/process-execution-contract.json").read_text(encoding="utf-8")
        )
        self.assertEqual("BYTES_FIRST", contract["capture_policy"]["capture_mode"])
        self.assertTrue(contract["capture_policy"]["text_true_for_captured_output_forbidden"])
        self.assertTrue(contract["capture_policy"]["exit_code_preserved_even_when_output_decode_fails"])
        self.assertTrue(contract["shell_policy"]["shell_true_forbidden"])
        self.assertEqual("COMSPEC /d /s /c", contract["shell_policy"]["cmd_bat_on_windows"])
        self.assertTrue(contract["git_policy"]["nul_delimited_changed_paths"])


if __name__ == "__main__":
    unittest.main()
