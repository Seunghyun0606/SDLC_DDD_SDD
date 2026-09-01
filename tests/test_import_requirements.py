import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

import sys
sys.path.insert(0, str(Path(__file__).parents[1] / "sdlc" / "scripts"))
import import_requirements as ir

MAIN = ir.MAIN
REL = ir.REL


def colname(n):
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def cell(ref, value):
    return f'<c r="{ref}" t="inlineStr"><is><t>{escape(str(value))}</t></is></c>'


def make_xlsx(path: Path, rows):
    sheet_rows = []
    for ridx, row in enumerate(rows, 1):
        sheet_rows.append(f'<row r="{ridx}">' + ''.join(cell(f"{colname(i)}{ridx}", v) for i, v in enumerate(row, 1)) + '</row>')
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


HEADERS1 = ["", "업무구분", "", "요구사항", "", "", "관리", "", ""]
HEADERS2 = ["No", "Level1", "Level2", "요구사항 ID", "요구사항명", "요구사항", "시작일", "종료일", "담당자"]


class RequirementImportTest(unittest.TestCase):
    def test_two_row_header_and_exact_grouping(self):
        with tempfile.TemporaryDirectory() as td:
            x = Path(td) / "req.xlsx"
            make_xlsx(x, [HEADERS1, HEADERS2,
                [1,"근태관리","근무계획","REQ1","최초근무계획 자동 설정","근무계획 저장","","",""],
                [2,"근태관리","근무계획","REQ2","최초근무계획 자동 설정","근무계획 조회","","",""],
                [3,"근태관리","Batch","REQ3","근무집계 반영","근무시간집계 수정","","",""],
            ])
            sheet, matrix = ir.read_xlsx_matrix(x)
            records, invalid = ir.map_rows(matrix, ir.IntakeProfile(), x.name, sheet, ir.source_hash(x))
            data = ir.transform(records, invalid)
            self.assertEqual(data["import_result"]["source_rows"], 3)
            self.assertEqual(data["import_result"]["rq_candidate_count"], 2)
            self.assertEqual(data["import_result"]["fr_candidate_count"], 3)
            self.assertEqual(data["fr_candidates"][0]["external_requirement_id"], "REQ1")

    def test_near_duplicate_is_review_not_merge(self):
        records = [
            {"source_record_id":"S1","level1":"근태관리","level2":"선택적근무제","external_requirement_id":"R1","source_requirement_name":"10분단위 근무계획 개선 선택적근무관리 반영을 구현","source_requirement_text":"선택근무관리 조회"},
            {"source_record_id":"S2","level1":"근태관리","level2":"선택적근무제","external_requirement_id":"R2","source_requirement_name":"10분단위 근무계획 개선 선택적근무관리 반영하는 기능","source_requirement_text":"초과근무신청현황 조회"},
        ]
        data = ir.transform(records, [])
        self.assertEqual(data["import_result"]["rq_candidate_count"], 2)
        self.assertGreaterEqual(data["import_result"]["grouping_review_count"], 1)
        self.assertFalse(data["grouping_reviews"][0]["auto_merged"])

    def test_invalid_row_is_non_blocking(self):
        with tempfile.TemporaryDirectory() as td:
            x = Path(td) / "req.xlsx"
            make_xlsx(x, [HEADERS1, HEADERS2,
                [1,"근태관리","근무계획","REQ1","정상 기능","조회","","",""],
                [2,"근태관리","근무계획","","ID 없는 기능","조회","","",""],
            ])
            sheet, matrix = ir.read_xlsx_matrix(x)
            records, invalid = ir.map_rows(matrix, ir.IntakeProfile(), x.name, sheet, ir.source_hash(x))
            data = ir.transform(records, invalid)
            self.assertEqual(data["import_result"]["imported_rows"], 1)
            self.assertEqual(data["import_result"]["invalid_rows"], 1)
            self.assertTrue(data["import_result"]["non_blocking"])

    def test_duplicate_external_id_creates_alert(self):
        records = [
            {"source_record_id":"S1","level1":"A","level2":"B","external_requirement_id":"DUP","source_requirement_name":"N1","source_requirement_text":"T1"},
            {"source_record_id":"S2","level1":"A","level2":"B","external_requirement_id":"DUP","source_requirement_name":"N2","source_requirement_text":"T2"},
        ]
        data = ir.transform(records, [])
        self.assertEqual(data["import_result"]["duplicate_external_ids"], 1)
        self.assertTrue(any(a.get("type") == "DUPLICATE_EXTERNAL_ID" for a in data["alerts"]))

    def test_raw_text_is_preserved_while_cleaned_value_is_derived(self):
        with tempfile.TemporaryDirectory() as td:
            x = Path(td) / "req.xlsx"
            raw = "근태현황\u00a0조회"
            make_xlsx(x, [HEADERS1, HEADERS2, [1,"근태관리","현황","REQ1","현황 기능",raw,"","",""]])
            sheet, matrix = ir.read_xlsx_matrix(x)
            records, _ = ir.map_rows(matrix, ir.IntakeProfile(), x.name, sheet, ir.source_hash(x))
            self.assertEqual(records[0]["source_requirement_text"], "근태현황 조회")
            self.assertEqual(records[0]["raw"]["source_requirement_text"], raw)

    def test_report_mermaid_uses_quoted_labels(self):
        data = ir.transform([], [])
        report = ir.render_report(data, "req.xlsx")
        self.assertIn('A["Source 0 rows"]', report)
        self.assertNotIn("A[/", report)


if __name__ == "__main__":
    unittest.main()
