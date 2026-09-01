import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "sdlc" / "scripts"))
import sync_worklist as sw

CONFIG = '''version: 1
locale: ko-KR
columns:
  - key: work_item_id
    label: 작업ID
    required: true
  - key: parent_id
    label: 상위작업ID
    required: false
  - key: requirement_id
    label: 요구사항ID
    required: false
  - key: item_type
    label: 작업구분
    required: true
  - key: name
    label: 작업명
    required: true
  - key: stage
    label: 단계
    required: true
  - key: status
    label: 상태
    required: true
  - key: assignee
    label: 담당자
    required: false
  - key: planned_start
    label: 계획시작일
    required: false
  - key: estimated_effort
    label: 예상공수
    required: false
  - key: program_ids
    label: 관련프로그램ID
    required: false
  - key: acceptance_test_ids
    label: 완료기준ID
    required: false
  - key: updated_at
    label: 최근변경일시
    required: false
    generated: true
  - key: revision
    label: 변경버전
    required: false
    generated: true
  - key: note
    label: 비고
    required: false
'''


def sample_records():
    return [
        {
            "work_item_id": "RQ-0042", "parent_id": "", "requirement_id": "RQ-0042",
            "item_type": "요구사항", "name": "휴가 취소 후 근태 자동 반영", "stage": "분석",
            "status": "진행중", "assignee": "", "planned_start": "", "estimated_effort": "",
            "program_ids": "PGM-LEV-0012,PGM-ATT-0016",
            "acceptance_test_ids": "AC-0042-01,TC-0042-001",
            "updated_at": "2026-09-01T09:00:00+09:00", "revision": 3, "note": "PM 필드는 선택",
        },
        {
            "work_item_id": "TASK-0042-DEV-002", "parent_id": "RQ-0042", "requirement_id": "RQ-0042",
            "item_type": "작업", "name": "근태 재계산 개발", "stage": "개발", "status": "미시작",
            "assignee": "개발자A", "planned_start": "2026-09-02", "estimated_effort": 2.5,
            "program_ids": "PGM-ATT-0016", "acceptance_test_ids": "AC-0042-03,TC-0042-003",
            "updated_at": "2026-09-01T09:00:00+09:00", "revision": 1, "note": "",
        },
    ]


class WorklistSyncTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.config = self.root / "cols.yaml"
        self.config.write_text(CONFIG, encoding="utf-8")
        self.specs = sw.columns(self.config)

    def tearDown(self):
        self.tmp.cleanup()

    def test_korean_labels_and_optional_pm_fields(self):
        self.assertEqual(self.specs[0].label, "작업ID")
        self.assertFalse(next(x for x in self.specs if x.key == "assignee").required)

    def test_md_xlsx_md_roundtrip(self):
        md, xlsx, md2 = self.root / "a.md", self.root / "a.xlsx", self.root / "b.md"
        sw.write_md(md, sample_records(), self.specs)
        from_md = sw.read_md(md, self.specs)
        sw.write_xlsx(xlsx, from_md, self.specs)
        sw.write_md(md2, sw.read_xlsx(xlsx, self.specs), self.specs)
        final = sw.read_md(md2, self.specs)
        self.assertEqual(final, from_md)
        self.assertEqual(final[0]["assignee"], "")
        self.assertEqual(final[1]["estimated_effort"], 2.5)
        self.assertEqual(final[1]["parent_id"], "RQ-0042")
        self.assertIn('V["완료기준/테스트"]', md2.read_text(encoding="utf-8"))

    def test_xlsx_md_xlsx_preserves_rows(self):
        x1, md, x2 = self.root / "a.xlsx", self.root / "a.md", self.root / "b.xlsx"
        sw.write_xlsx(x1, sample_records(), self.specs)
        sw.write_md(md, sw.read_xlsx(x1, self.specs), self.specs)
        sw.write_xlsx(x2, sw.read_md(md, self.specs), self.specs)
        self.assertEqual(sw.read_xlsx(x1, self.specs), sw.read_xlsx(x2, self.specs))

    def test_edit_from_current_view_bumps_revision(self):
        current = sample_records()[0]
        canonical = {"schema_version": 1, "items": {"RQ-0042": dict(current)}, "conflicts": []}
        incoming = dict(current); incoming["name"] = "휴가 취소 후 근태 즉시 반영"
        original_now = sw.now; sw.now = lambda: "2026-09-01T10:00:00+09:00"
        try: conflicts = sw.merge(canonical, [incoming], self.specs, "md")
        finally: sw.now = original_now
        self.assertEqual(conflicts, [])
        self.assertEqual(canonical["items"]["RQ-0042"]["revision"], 4)
        self.assertEqual(canonical["items"]["RQ-0042"]["updated_at"], "2026-09-01T10:00:00+09:00")

    def test_stale_revision_creates_conflict_without_overwrite(self):
        current = sample_records()[0]; current.update(revision=4, updated_at="2026-09-01T10:00:00+09:00")
        canonical = {"schema_version": 1, "items": {"RQ-0042": dict(current)}, "conflicts": []}
        incoming = dict(current); incoming.update(revision=3, updated_at="2026-09-01T09:00:00+09:00", name="오래된 수정")
        conflicts = sw.merge(canonical, [incoming], self.specs, "xlsx")
        self.assertEqual(conflicts[0]["type"], "SYNC_CONFLICT")
        self.assertEqual(canonical["items"]["RQ-0042"]["name"], "휴가 취소 후 근태 자동 반영")

    def test_sync_conflict_is_non_blocking_by_default(self):
        md, xlsx = self.root / "work.md", self.root / "work.xlsx"
        canonical_path, conflicts_path = self.root / "canonical.json", self.root / "conflicts.jsonl"
        sw.write_md(md, sample_records(), self.specs)
        args = ["sync", "--source", "md", "--config", str(self.config), "--md", str(md), "--xlsx", str(xlsx), "--canonical", str(canonical_path), "--conflicts", str(conflicts_path)]
        self.assertEqual(sw.main(args), 0)
        canonical = json.loads(canonical_path.read_text(encoding="utf-8"))
        canonical["items"]["RQ-0042"].update(revision=4, updated_at="2026-09-01T11:00:00+09:00", name="canonical newer")
        canonical_path.write_text(json.dumps(canonical, ensure_ascii=False), encoding="utf-8")
        stale = sw.read_md(md, self.specs); stale[0]["name"] = "stale user edit"; sw.write_md(md, stale, self.specs)
        self.assertEqual(sw.main(args), 0)
        self.assertIn("SYNC_CONFLICT", conflicts_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
