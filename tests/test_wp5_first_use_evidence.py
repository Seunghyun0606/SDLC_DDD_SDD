import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "sdlc/scripts/harness.py"
MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def run_cli(*args: str) -> tuple[int, dict]:
    cp = subprocess.run(
        [sys.executable, str(HARNESS), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    try:
        payload = json.loads(cp.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"non-JSON CLI output rc={cp.returncode}\nstdout={cp.stdout}\nstderr={cp.stderr}") from exc
    return cp.returncode, payload


def colname(n: int) -> str:
    value = ""
    while n:
        n, r = divmod(n - 1, 26)
        value = chr(65 + r) + value
    return value


def cell(ref: str, value: object) -> str:
    return f'<c r="{ref}" t="inlineStr"><is><t>{escape(str(value))}</t></is></c>'


def make_xlsx(path: Path) -> None:
    rows = [
        ["", "업무구분", "", "요구사항", "", "", "관리", "", ""],
        ["No", "Level1", "Level2", "요구사항\u00a0ID", "요구사항명", "요구사항", "시작일", "종료일", "담당자"],
        [1, "근태관리", "근무계획", "REQ-100", "근무계획 승인", "근무계획 저장 시 승인 주체가 필요하다.", "", "", ""],
    ]
    sheet_rows = []
    for ridx, row in enumerate(rows, 1):
        sheet_rows.append(
            f'<row r="{ridx}">' + "".join(cell(f"{colname(i)}{ridx}", v) for i, v in enumerate(row, 1)) + "</row>"
        )
    sheet = f'<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="{MAIN}"><sheetData>{"".join(sheet_rows)}</sheetData></worksheet>'
    content = '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>'
    root_rel = '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>'
    wb = f'<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="{MAIN}" xmlns:r="{REL}"><sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets></workbook>'
    wbrel = '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>'
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content)
        zf.writestr("_rels/.rels", root_rel)
        zf.writestr("xl/workbook.xml", wb)
        zf.writestr("xl/_rels/workbook.xml.rels", wbrel)
        zf.writestr("xl/worksheets/sheet1.xml", sheet)


def write_review_fixture_provider(path: Path) -> None:
    path.write_text(textwrap.dedent('''\
        import argparse
        import json
        from pathlib import Path

        ap = argparse.ArgumentParser()
        ap.add_argument("--context", required=True)
        ap.add_argument("--result", required=True)
        args = ap.parse_args()
        context = json.loads(Path(args.context).read_text(encoding="utf-8"))
        stage = context["selection"]["stage"]
        target = context["target"]["id"]
        artifact_rel = context["selection"]["artifact_path"]
        artifact = Path(artifact_rel)
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text(
            f"---\\nstage: {stage}\\ndocument_type: wp5_first_use_fixture\\nstatus: CURRENT\\n---\\n"
            f"# {target} 요구사항 초안\\n\\n"
            "## 문서 목적\\nEvidence 기반 요구사항 초안을 작성한다.\\n\\n"
            "## 한눈에 보기\\n- 근무계획 저장 시 승인 주체 결정이 필요하다.\\n\\n"
            "## 업무 흐름\\n1. 근무계획 저장 요청\\n2. 승인 정책 확인 필요\\n\\n"
            "## 입력 및 근거\\n- REQ-100: 근무계획 저장 시 승인 주체가 필요하다.\\n\\n"
            "## 상세 내용\\n승인 주체 자체는 원문에 없으므로 OPEN으로 유지한다.\\n\\n"
            "## 미확정 사항·주의·가정\\n- 승인 주체: OPEN (업무정책 결정 필요)\\n- 저장 구현 위치: CHECK_REQUIRED (Agent 추가 조사 대상)\\n\\n"
            f"## 관련 ID 및 추적성\\n- {target}\\n- REQ-100\\n\\n"
            "## 다음 작업\\n승인 주체만 확인한 뒤 Agent가 문서를 갱신한다.\\n",
            encoding="utf-8",
        )
        result = {
            "schema_version": 1,
            "stage": stage,
            "artifact_path": artifact_rel,
            "canonical_delta": {
                "schema_version": 1,
                "delta_id": f"WP5-FIRST-USE-{target}-{stage}",
                "base_revision": context["canonical"]["base_revision"],
                "stage": stage,
                "source_artifact": artifact_rel,
                "operations": [],
                "no_change_reason": "첫사용 Behavioral fixture는 Canonical 업무 의미를 자동 변경하지 않는다."
            },
            "quality_gate": {"status": "PASS", "failures": []},
            "alerts": ["WP5_BEHAVIORAL_FIXTURE_NOT_EXTERNAL_AGENT"],
            "uncertainty": [
                {
                    "state": "OPEN",
                    "category": "BUSINESS_POLICY",
                    "requires_human_decision": True,
                    "question": "근무계획 저장의 승인 주체를 누구로 결정합니까?",
                    "evidence": "REQ-100"
                },
                {
                    "state": "CHECK_REQUIRED",
                    "category": "SOURCE_EVIDENCE",
                    "requires_human_decision": False,
                    "question": "저장 구현 위치는 Source 조사로 확인한다.",
                    "evidence": None
                }
            ]
        }
        out = Path(args.result)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
    '''), encoding="utf-8")


class WP5FirstUseEvidenceTest(unittest.TestCase):
    def test_public_cli_first_use_flow_is_nonblocking_until_work_and_provider_can_be_connected_without_force(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            xlsx = root / "요구사항목록.xlsx"
            make_xlsx(xlsx)

            rc, setup = run_cli(
                "setup", "--root", str(root), "--name", "first-use-pilot",
                "--mode", "GREENFIELD", "--delivery", "STANDARD",
            )
            self.assertEqual(0, rc, setup)
            self.assertEqual("SETUP_READY_PROVIDER_PENDING", setup["status"])
            self.assertFalse(setup["provider_ready"])
            self.assertIn("intake", " ".join(setup["next_commands"]))

            project_entry = root / ".sdlc/project.yaml"
            before_project = project_entry.read_bytes()

            rc, checked = run_cli("check", "--root", str(root), "--setup")
            self.assertEqual(0, rc, checked)
            self.assertEqual("SETUP_READY_PROVIDER_PENDING", checked["status"])
            self.assertEqual("AGENT_PROVIDER_PENDING", checked["work_blocked_reason"])

            rc, intake = run_cli("intake", str(xlsx), "--root", str(root))
            self.assertEqual(0, rc, intake)
            self.assertEqual("INTAKE_READY_FOR_WORK", intake["status"])
            self.assertEqual("RQ-001", intake["first_target"])

            provider = root / "wp5_provider.py"
            write_review_fixture_provider(provider)
            command = f'{sys.executable} {provider} --context {{context_path}} --result {{result_path}}'
            rc, connected = run_cli("setup", "--root", str(root), "--provider-command", command)
            self.assertEqual(0, rc, connected)
            self.assertEqual("READY_FOR_PLAN", connected["status"])
            self.assertTrue(connected["provider_ready"])
            self.assertTrue(connected["provider_connection"]["project_config_preserved"])
            self.assertEqual(before_project, project_entry.read_bytes())

            provider_config = json.loads((root / "sdlc/config/agent-provider.json").read_text(encoding="utf-8"))
            self.assertTrue(provider_config["enabled"])
            self.assertEqual("EXTERNAL_AGENT", provider_config["provider_class"])

            rc, work = run_cli("work", "--root", str(root), "--target", "RQ-001")
            self.assertEqual(0, rc, work)
            handoff = work["user_handoff"]
            self.assertTrue(handoff["review_required"])
            self.assertEqual(1, len(handoff["review_items"]))
            self.assertEqual("BUSINESS_POLICY", handoff["review_items"][0]["category"])
            self.assertEqual(1, len(handoff["agent_open_items"]))
            self.assertTrue(handoff["document"].startswith("docs/10_산출물/"))
            self.assertTrue((root / handoff["document"]).is_file())
            self.assertTrue((root / work["handoff_path"]).is_file())

            before_review = json.loads((root / "sdlc/canonical/store.json").read_text(encoding="utf-8"))
            self.assertEqual("OPEN", before_review["entities"]["RQ-001"]["fields"]["current_problem"])

            rc, review = run_cli(
                "review", "--root", str(root), "--target", "RQ-001",
                "--by", "분석가 김민수", "--answer", "승인 주체는 팀장으로 한다",
            )
            self.assertEqual(0, rc, review)
            self.assertEqual("REVIEW_RECORDED", review["status"])
            self.assertFalse(review["business_fields_auto_changed"])
            self.assertIn("work --target RQ-001", review["next_command"])

            after_review = json.loads((root / "sdlc/canonical/store.json").read_text(encoding="utf-8"))
            rq = after_review["entities"]["RQ-001"]
            self.assertEqual("OPEN", rq["fields"]["current_problem"])
            self.assertTrue(any("CUSTOMER_DECISION ACKNOWLEDGE" in row.get("note", "") for row in rq["provenance"]))


if __name__ == "__main__":
    unittest.main()
