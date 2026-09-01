#!/usr/bin/env python3
"""P2 tests: real XLSX intake evidence + generic Brownfield control-plane slice."""
from __future__ import annotations

import copy
import sys
import tempfile
import zipfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "sdlc/scripts"
sys.path.insert(0, str(SCRIPTS))

from analyze_java_spring import analyze as analyze_java
from analyze_sql_database import analyze as analyze_sql
from build_command_context import build as build_command_context
from execute_command_runtime import execute
from guard_revision_ownership import guard
from intake_requirements_xlsx import intake
from orchestrate_generic_e2e_status import build as build_e2e
from resolve_artifact_profile import resolve as resolve_profile
from resolve_stage_execution import resolve as resolve_stage
from route_provider_command import build_plan


def load(rel: str):
    return yaml.safe_load((ROOT / rel).read_text(encoding="utf-8")) or {}


def create_tiny_xlsx(path: Path) -> None:
    workbook = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Requirements" sheetId="1" r:id="rId1"/></sheets></workbook>'''
    rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>'''
    sheet = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>
<row r="1"><c r="A1" t="inlineStr"><is><t>No</t></is></c><c r="B1" t="inlineStr"><is><t>업무구분</t></is></c><c r="D1" t="inlineStr"><is><t>요구사항</t></is></c></row>
<row r="2"><c r="B2" t="inlineStr"><is><t>Level1</t></is></c><c r="C2" t="inlineStr"><is><t>Level2</t></is></c><c r="D2" t="inlineStr"><is><t>요구사항 ID</t></is></c><c r="E2" t="inlineStr"><is><t>요구사항명</t></is></c><c r="F2" t="inlineStr"><is><t>요구사항</t></is></c></row>
<row r="3"><c r="A3"><v>1</v></c><c r="B3" t="inlineStr"><is><t>Domain</t></is></c><c r="C3" t="inlineStr"><is><t>Interface</t></is></c><c r="D3" t="inlineStr"><is><t>REQ-GEN-001</t></is></c><c r="E3" t="inlineStr"><is><t>External send</t></is></c><c r="F3" t="inlineStr"><is><t>Send profile data</t></is></c></row>
</sheetData></worksheet>'''
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("xl/workbook.xml", workbook)
        zf.writestr("xl/_rels/workbook.xml.rels", rels)
        zf.writestr("xl/worksheets/sheet1.xml", sheet)


def test_real_workbook_intake_evidence():
    doc = load("sdlc/design/validation/p2-representative-brownfield-slice-v1/requirements-intake-REQ_TM_TE100.yaml")
    root = doc["requirement_intake"]
    assert root["source_row_count"] == 142
    assert root["selected_count"] == 1
    assert root["duplicate_source_requirement_ids"] == []
    rec = root["records"][0]
    assert rec["source_requirement_id"] == "REQ_TM_TE100"
    assert rec["level2"] == "Interface"
    assert rec["truth_state"] == "GIVEN"
    assert root["truth_guards"]["canonical_rq_must_not_be_created_by_intake"] is True


def test_xlsx_adapter_header_detection():
    with tempfile.TemporaryDirectory() as td:
        xlsx = Path(td) / "requirements.xlsx"
        create_tiny_xlsx(xlsx)
        result = intake(xlsx, load("sdlc/config/requirement-intake.yaml"))["requirement_intake"]
        assert result["source"]["header_row"] == 2
        assert result["source_row_count"] == 1
        assert result["records"][0]["source_requirement_id"] == "REQ-GEN-001"
        assert result["records"][0]["requirement_text"] == "Send profile data"


def test_java_sql_adapters_are_observation_only():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "src").mkdir(); (root / "db").mkdir()
        (root / "src/ExampleController.java").write_text(
            '@RestController\n@RequestMapping("/examples")\npublic class ExampleController {\n'
            ' private final ExampleService service;\n @GetMapping("/{id}") public String getExample(String id){return service.get(id);}\n}\n'
            '@Service class ExampleService { @Transactional public String get(String id){return id;} }\n', encoding="utf-8")
        (root / "db/schema.sql").write_text(
            "CREATE TABLE EXAMPLE_ITEM (ID VARCHAR(20));\nCREATE OR REPLACE PROCEDURE LOAD_ITEM AS BEGIN INSERT INTO EXAMPLE_ITEM(ID) VALUES ('1'); END;\nSELECT * FROM EXAMPLE_ITEM;\n",
            encoding="utf-8")
        java = analyze_java(root, ["src/ExampleController.java"])["source_analysis_result"]
        sql = analyze_sql(root, ["db/schema.sql"])["source_analysis_result"]
        assert "spring_route" in java["evidence"][0]["signals"]
        assert java["evidence"][0]["business_truth_confirmed"] is False
        assert {x["kind"] for x in sql["evidence"][0]["objects"]} == {"TABLE", "PROCEDURE"}
        assert sql["evidence"][0]["business_truth_confirmed"] is False


def test_revision_ownership_guard_allow_and_deny():
    allow = {"change_execution": {
        "change_id": "CHG-1", "agent_id": "agent-a", "expected_revision": "abc", "current_revision": "abc",
        "agent_branch": "agent/RQ-1/TASK-1/agent-a", "parent_change_branch": "change/RQ-1/update",
        "ownership": {"requested_paths": ["src/a.py"], "owned_paths": ["src/**"], "shared_paths": ["docs/**"], "active_claims": []},
    }}
    result = guard(allow)["revision_ownership_guard"]
    assert result["decision"] == "ALLOW" and result["guard_proof_ref"]
    deny = copy.deepcopy(allow)
    deny["change_execution"]["current_revision"] = "def"
    deny["change_execution"]["ownership"]["active_claims"] = [{"agent_id": "agent-b", "paths": ["src/a.py"]}]
    result = guard(deny)["revision_ownership_guard"]
    assert result["decision"] == "DENY"
    assert {x["code"] for x in result["blockers"]} >= {"REVISION_MISMATCH", "ACTIVE_OWNERSHIP_CONFLICT"}


def test_representative_brownfield_control_plane_stops_at_real_source_boundary():
    stage_pack = load("sdlc/design/validation/p2-representative-brownfield-slice-v1/representative-slice-stage-pack.yaml")
    artifact_plan = resolve_profile(load("sdlc/config/artifact-profiles.yaml"), {"artifacts": {"profile": "LITE"}})
    execution_plan = resolve_stage(load("sdlc/config/stage-routing.yaml"), stage_pack, artifact_plan)
    plan = execution_plan["stage_execution"]
    assert "source.snapshot.read" in plan["required_capabilities"]
    assert "source.search" in plan["required_capabilities"]
    assert plan["read_only_progress_allowed"] is True

    context = build_command_context(stage_pack, execution_plan, "/work")
    registry = load("sdlc/config/provider-registry.example.yaml")
    runtime_plan, errors = build_plan(registry, context)
    assert errors == []
    opens = runtime_plan["runtime_plan"]["open_items"]
    blocking = [x for x in opens if x.get("blocks_action") is True]
    optional = [x for x in opens if x.get("blocks_action") is False]
    assert {x["capability"] for x in blocking} == {"source.snapshot.read", "source.search"}
    assert any(x["capability"] == "source.object.read" for x in optional)
    result = execute(registry, context)["command_runtime_result"]
    assert result["state"] == "ACTION_REQUIRED"
    assert result["invocations"] == []


def test_source_write_requires_revision_guard_proof():
    pack = load("sdlc/design/validation/p2-representative-brownfield-slice-v1/representative-slice-stage-pack.yaml")
    pack = copy.deepcopy(pack)
    pack["stage_input_pack"]["metadata"]["stage"] = "DEVELOPMENT"
    pack["stage_input_pack"]["execution"]["requested_actions"] = ["source.write"]
    pack["stage_input_pack"]["execution"]["write_proofs"] = {"source.write": {
        "expected_revision": "abc", "idempotency_key": "idem-1", "permission_proof_ref": "perm-1"}}
    execution_plan = resolve_stage(load("sdlc/config/stage-routing.yaml"), pack)
    context = build_command_context(pack, execution_plan, "/work")
    assert any(x.get("type") == "REVISION_OWNERSHIP_GUARD_REQUIRED" for x in context["human_actions"])
    pack["stage_input_pack"]["execution"]["revision_guard"] = {"decision": "ALLOW", "guard_proof_ref": "GUARD:CHG-1:abc"}
    context = build_command_context(pack, execution_plan, "/work")
    assert not any(x.get("type") == "REVISION_OWNERSHIP_GUARD_REQUIRED" for x in context["human_actions"])


def test_generic_e2e_status_and_release_gate():
    ledger = load("sdlc/design/validation/p2-representative-brownfield-slice-v1/representative-slice-e2e-ledger.yaml")
    status = build_e2e(ledger)["e2e_check_status"]
    assert status["overall"]["state"] == "ACTION_REQUIRED"
    assert status["overall"]["release_ready"] is False
    ready = {"e2e_execution_ledger": {
        "subject": {"target_id": "RQ-1"},
        "stages": [{"stage": "INTAKE", "state": "COMPLETE", "required_for_release": True}, {"stage": "VERIFY", "state": "COMPLETE", "required_for_release": True}],
        "blockers": [],
        "verification": {"state": "VERIFIED_PASS", "production_verified": True},
    }}
    status = build_e2e(ready)["e2e_check_status"]
    assert status["overall"]["state"] == "READY_FOR_RELEASE"
    assert status["overall"]["release_ready"] is True


def main():
    tests = [
        test_real_workbook_intake_evidence,
        test_xlsx_adapter_header_detection,
        test_java_sql_adapters_are_observation_only,
        test_revision_ownership_guard_allow_and_deny,
        test_representative_brownfield_control_plane_stops_at_real_source_boundary,
        test_source_write_requires_revision_guard_proof,
        test_generic_e2e_status_and_release_gate,
    ]
    for test in tests:
        test(); print(f"PASS {test.__name__}")
    print(f"PASS p2 representative slice tests={len(tests)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
