import importlib.util
import json
import sys
import tempfile
import unittest
import zipfile
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).parents[1]
SCRIPT_DIR = ROOT / "sdlc" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))


def load(name: str, filename: str):
    path = SCRIPT_DIR / filename
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


INTAKE = load("wp3_intake", "intake_requirements.py")
HARNESS = load("wp3_harness", "harness.py")
WORK = load("wp3_work", "run_work.py")

MAIN = INTAKE.MAIN
REL = INTAKE.REL
HEADERS1 = ["", "업무구분", "", "요구사항", "", "", "관리", "", ""]
HEADERS2 = ["No", "Level1", "Level2", "요구사항\u00a0ID", "요구사항명", "요구사항", "시작일", "종료일", "담당자"]


def colname(n: int) -> str:
    value = ""
    while n:
        n, r = divmod(n - 1, 26)
        value = chr(65 + r) + value
    return value


def cell(ref: str, value: object) -> str:
    return f'<c r="{ref}" t="inlineStr"><is><t>{escape(str(value))}</t></is></c>'


def make_xlsx(path: Path, rows: list[list[object]]) -> None:
    sheet_rows = []
    for ridx, row in enumerate(rows, 1):
        sheet_rows.append(
            f'<row r="{ridx}">'
            + "".join(cell(f"{colname(i)}{ridx}", v) for i, v in enumerate(row, 1))
            + "</row>"
        )
    sheet = f'''<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="{MAIN}"><sheetData>{''.join(sheet_rows)}</sheetData></worksheet>'''
    content = '''<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>'''
    root_rel = '''<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>'''
    wb = f'''<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="{MAIN}" xmlns:r="{REL}"><sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets></workbook>'''
    wbrel = '''<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>'''
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content)
        z.writestr("_rels/.rels", root_rel)
        z.writestr("xl/workbook.xml", wb)
        z.writestr("xl/_rels/workbook.xml.rels", wbrel)
        z.writestr("xl/worksheets/sheet1.xml", sheet)


def fixture(path: Path) -> None:
    make_xlsx(
        path,
        [
            HEADERS1,
            HEADERS2,
            [1, "근태관리", "근무계획", "REQ1", "최초근무계획 자동 설정", "근무계획 저장", "", "", ""],
            [2, "근태관리", "근무계획", "REQ2", "최초근무계획 자동 설정", "근무계획 조회", "", "", ""],
            [3, "근태관리", "Batch", "REQ3", "근무집계 반영", "근무시간집계 수정", "", "", ""],
        ],
    )


class RequirementIntakeRuntimeTest(unittest.TestCase):
    def test_official_setup_guidance_points_to_start_here_and_intake(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            out = StringIO()
            with redirect_stdout(out):
                code = HARNESS.main([
                    "setup", "--root", str(root), "--name", "sample",
                    "--mode", "GREENFIELD", "--delivery", "STANDARD", "--no-validate",
                ])
            self.assertEqual(0, code, out.getvalue())
            result = json.loads(out.getvalue())
            self.assertEqual("SETUP_READY_PROVIDER_PENDING", result["status"])
            self.assertFalse(result["provider_ready"])
            self.assertEqual("docs/00_시작/START_HERE.md", result["user_entrypoint"]["start_here"])
            self.assertEqual("CONNECTED", result["user_entrypoint"]["zero_to_one_intake"])
            self.assertIn("python sdlc/scripts/harness.py intake <requirement-file.xlsx>", result["next_commands"])
            self.assertFalse(any("<RQ-ID>" in command for command in result["next_commands"]))
            persisted = json.loads((root / "sdlc/runtime/setup/setup-result.json").read_text(encoding="utf-8"))
            self.assertEqual(result["next_commands"], persisted["next_commands"])
            self.assertEqual("SETUP_READY_PROVIDER_PENDING", persisted["status"])

    def test_official_harness_intake_registers_targets_and_work_resolves_decompose(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            xlsx = root / "요구사항목록.xlsx"
            fixture(xlsx)
            stdout = StringIO()
            with redirect_stdout(stdout):
                code = HARNESS.main(["intake", str(xlsx), "--root", str(root)])
            self.assertEqual(code, 0, stdout.getvalue())
            result = json.loads(stdout.getvalue())
            self.assertEqual(result["status"], "INTAKE_READY_FOR_WORK")
            self.assertEqual(result["first_target"], "RQ-001")
            self.assertEqual(result["next_command"], "python sdlc/scripts/harness.py work --target RQ-001")

            store_path = root / "sdlc/canonical/store.json"
            store = json.loads(store_path.read_text(encoding="utf-8"))
            self.assertEqual(store["entities"]["RQ-001"]["truth_status"], "CANDIDATE")
            self.assertEqual(store["entities"]["RQ-001"]["fields"]["current_problem"], "OPEN")
            self.assertEqual(store["entities"]["FR-001"]["fields"]["external_requirement_id"], "REQ1")
            self.assertTrue(any(row["from"] == "RQ-001" and row["kind"] == "HAS_FR_CANDIDATE" for row in store["relations"]))

            plan = WORK.build_plan(root, target_id="RQ-001", store_path=store_path)
            self.assertEqual(plan["selection"]["stage"], "DECOMPOSE")
            self.assertTrue(plan["target"]["canonical_found"])
            self.assertTrue(any(row["entity_type"] == "FR" for row in plan["target"]["related_entities"]))

    def test_standard_headers_need_no_profile_and_reimport_reuses_ids(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            xlsx = root / "requirements.xlsx"
            fixture(xlsx)
            kwargs = dict(
                xlsx=xlsx,
                profile_path=None,
                json_out=root / "sdlc/runtime/intake/requirements-import.json",
                report_out=root / "docs/00_관리/요구사항_인입결과.md",
                store_path=root / "sdlc/canonical/store.json",
                apply_to_canonical=True,
            )
            first = INTAKE.run_intake(**kwargs)
            second = INTAKE.run_intake(**kwargs)
            self.assertEqual(first["canonical"]["rq_target_ids"], ["RQ-001", "RQ-002"])
            self.assertEqual(first["canonical"]["rq_target_ids"], second["canonical"]["rq_target_ids"])
            self.assertEqual(second["canonical"]["status"], "IDEMPOTENT")

    def test_duplicate_external_ids_remain_separate_review_candidates_on_reintake(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            xlsx = root / "duplicate.xlsx"
            make_xlsx(
                xlsx,
                [
                    HEADERS1,
                    HEADERS2,
                    [1, "근태", "계획", "DUP-1", "계획 A", "기능 A", "", "", ""],
                    [2, "근태", "계획", "DUP-1", "계획 B", "기능 B", "", "", ""],
                ],
            )
            kwargs = dict(
                xlsx=xlsx, profile_path=None, json_out=root / "out.json", report_out=root / "report.md",
                store_path=root / "store.json", apply_to_canonical=True,
            )
            first = INTAKE.run_intake(**kwargs)
            second = INTAKE.run_intake(**kwargs)
            self.assertEqual(first["import_result"]["duplicate_external_ids"], 1)
            self.assertEqual(first["import_result"]["fr_candidate_count"], 2)
            store = json.loads((root / "store.json").read_text(encoding="utf-8"))
            frs = [x for x in store["entities"].values() if x["entity_type"] == "FR"]
            self.assertEqual(2, len(frs))
            self.assertEqual(2, len({x["fields"]["intake_stable_key"] for x in frs}))
            self.assertEqual(first["canonical"]["rq_target_ids"], second["canonical"]["rq_target_ids"])

    def test_reintake_does_not_downgrade_confirmed_business(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            xlsx = root / "requirements.xlsx"
            fixture(xlsx)
            store_path = root / "sdlc/canonical/store.json"
            first = INTAKE.run_intake(
                xlsx, profile_path=None, json_out=root / "first.json", report_out=root / "first.md",
                store_path=store_path, apply_to_canonical=True,
            )
            target = first["canonical"]["rq_target_ids"][0]
            store = json.loads(store_path.read_text(encoding="utf-8"))
            store["entities"][target]["truth_status"] = "CONFIRMED_BUSINESS"
            store_path.write_text(json.dumps(store, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            second = INTAKE.run_intake(
                xlsx, profile_path=None, json_out=root / "second.json", report_out=root / "second.md",
                store_path=store_path, apply_to_canonical=True,
            )
            after = json.loads(store_path.read_text(encoding="utf-8"))
            self.assertEqual(second["canonical"]["status"], "APPLIED")
            self.assertIn(target, second["canonical"]["confirmed_entities_preserved"])
            self.assertEqual(after["entities"][target]["truth_status"], "CONFIRMED_BUSINESS")

    def test_report_is_human_view_with_concrete_next_step_not_blank_template(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            xlsx = root / "requirements.xlsx"
            fixture(xlsx)
            INTAKE.run_intake(
                xlsx, profile_path=None,
                json_out=root / "sdlc/runtime/intake/requirements-import.json",
                report_out=root / "docs/00_관리/요구사항_인입결과.md",
                store_path=root / "sdlc/canonical/store.json",
                apply_to_canonical=True,
            )
            report = (root / "docs/00_관리/요구사항_인입결과.md").read_text(encoding="utf-8")
            self.assertIn("## Agent가 다음 단계에서 초안할 내용", report)
            self.assertIn("## 사람이 확인해야 할 항목만", report)
            self.assertIn("python sdlc/scripts/harness.py work --target RQ-001", report)
            self.assertNotIn("{{", report)
            self.assertNotIn("<RQ-ID>", report)

    def test_candidate_only_keeps_canonical_store_untouched(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            xlsx = root / "requirements.xlsx"
            fixture(xlsx)
            data = INTAKE.run_intake(
                xlsx, profile_path=None, json_out=root / "out.json", report_out=root / "report.md",
                store_path=root / "store.json", apply_to_canonical=False,
            )
            self.assertEqual(data["canonical"]["status"], "CANDIDATE_ONLY")
            self.assertFalse((root / "store.json").exists())


if __name__ == "__main__":
    unittest.main()
