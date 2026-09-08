from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "sdlc/scripts/extract_document_evidence.py"


def load_module():
    spec = importlib.util.spec_from_file_location("document_encoding_v110", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


EXTRACT = load_module()


class DocumentEncodingV110Test(unittest.TestCase):
    def test_utf8_korean_markdown_is_lossless_and_recorded(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "업무설명.md"
            path.write_bytes("# 근무계획 개선\n\n승인 상태를 확인한다.\n".encode("utf-8"))

            result = EXTRACT.extract(path, "DOC-UTF8")

            self.assertEqual("EXTRACTED", result["extraction_status"])
            self.assertEqual("utf-8", result["text_encoding"]["source_encoding"])
            self.assertEqual("STRICT_PRIMARY", result["text_encoding"]["encoding_detection"])
            self.assertFalse(result["text_encoding"]["lossy_decode"])
            raw = "\n".join(row["raw_text"] for row in result["evidence_chunks"])
            self.assertIn("근무계획 개선", raw)
            self.assertNotIn("\ufffd", raw)

    def test_utf8_bom_csv_is_lossless_and_recorded(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "요구사항.csv"
            path.write_bytes(b"\xef\xbb\xbf" + "요구사항,상태\n근무계획,승인\n".encode("utf-8"))

            result = EXTRACT.extract(path, "DOC-BOM")

            self.assertEqual("EXTRACTED", result["extraction_status"])
            self.assertEqual("utf-8-sig", result["text_encoding"]["source_encoding"])
            self.assertEqual("BOM", result["text_encoding"]["encoding_detection"])
            self.assertEqual("근무계획", result["evidence_chunks"][0]["structured_content"]["rows"][0][0])

    def test_cp949_korean_csv_uses_strict_legacy_fallback(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "현행업무.csv"
            original = "항목,설명\n근무계획,승인 상태 확인\n"
            path.write_bytes(original.encode("cp949"))

            result = EXTRACT.extract(path, "DOC-CP949")

            self.assertEqual("EXTRACTED", result["extraction_status"])
            self.assertEqual("cp949", result["text_encoding"]["source_encoding"])
            self.assertEqual("STRICT_LEGACY_FALLBACK", result["text_encoding"]["encoding_detection"])
            self.assertFalse(result["text_encoding"]["lossy_decode"])
            raw = result["evidence_chunks"][0]["raw_text"]
            self.assertIn("근무계획", raw)
            self.assertIn("승인 상태 확인", raw)
            self.assertNotIn("\ufffd", raw)

    def test_utf16le_bom_text_is_supported_without_locale_dependency(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "회의내용.txt"
            original = "근무계획 변경\n승인 담당자 확인"
            path.write_bytes(original.encode("utf-16"))

            result = EXTRACT.extract(path, "DOC-UTF16")

            self.assertEqual("EXTRACTED", result["extraction_status"])
            self.assertEqual("utf-16-le", result["text_encoding"]["source_encoding"])
            self.assertEqual("BOM", result["text_encoding"]["encoding_detection"])
            self.assertIn("승인 담당자 확인", result["evidence_chunks"][0]["raw_text"])

    def test_unknown_text_encoding_fails_closed_without_replacement_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "broken.txt"
            path.write_bytes(b"\x81")

            result = EXTRACT.extract(path, "DOC-BROKEN")

            self.assertEqual("EXTRACTION_REQUIRED", result["extraction_status"])
            self.assertEqual(0, result["chunk_count"])
            self.assertEqual([], result["evidence_chunks"])
            self.assertEqual("FAILED", result["text_encoding"]["encoding_detection"])
            self.assertFalse(result["text_encoding"]["lossy_decode"])
            self.assertTrue(result["notes"])

    def test_contract_forbids_lossy_replacement_decode(self):
        contract = json.loads(
            (ROOT / "sdlc/design/contracts/br-document-extraction-contract.json").read_text(encoding="utf-8")
        )
        policy = contract["text_encoding_contract"]
        self.assertEqual("LOSSLESS_STRICT_ONLY", policy["decode_policy"])
        self.assertTrue(policy["replacement_decode_for_evidence_forbidden"])
        self.assertTrue(policy["legacy_fallback_must_be_recorded"])
        self.assertEqual("EXTRACTION_REQUIRED", policy["unknown_or_lossy_encoding_status"])


if __name__ == "__main__":
    unittest.main()
