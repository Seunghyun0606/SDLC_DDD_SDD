#!/usr/bin/env python3
"""Self-tests for P0/P1 structural redesign. Uses only generic fixtures."""
from __future__ import annotations

import tempfile
from pathlib import Path
import yaml

from bootstrap_project import bootstrap
from build_command_context import build as build_command_context
from build_reverse_sync_from_signals import build as build_reverse_sync
from collect_bounded_source_evidence import collect as collect_bounded_source
from execute_command_runtime import execute
from resolve_artifact_profile import resolve as resolve_profile
from resolve_stage_execution import resolve as resolve_stage
from route_provider_command import build_plan
from validate_p1_foundation import validate_bootstrap

ROOT = Path(__file__).resolve().parents[2]


def load_actual(rel):
    return yaml.safe_load((ROOT / rel).read_text(encoding="utf-8")) or {}


def registry(source_state="UNCONFIGURED"):
    return {"registry":{"providers":[
        {"provider_id":"router","provider_type":"COMMAND_ROUTER","enabled":True,"provider_state":"AVAILABLE","mode":"READ_ONLY","priority":1,"capabilities":["command.route.work","command.route.change","command.route.check"]},
        {"provider_id":"source","provider_type":"SOURCE","enabled":True,"provider_state":source_state,"mode":"READ_ONLY","priority":1,"capabilities":["source.snapshot.read","source.search","source.object.read","source.diff"]},
    ]}}


def routing():
    return {"stages":{
        "DISCOVERY":{"skill":"brownfield-source-analysis","mode_rules":{"BROWNFIELD":{"required_capabilities":["source.snapshot.read","source.search"],"optional_capabilities":["source.object.read"]}},"output_artifacts":["impact_analysis","stage_input_pack"],"next_stage":"IMPACT","side_effect_actions":[]},
        "DEVELOPMENT":{"skill":"source-change","required_capabilities":[],"optional_capabilities":["source.object.read"],"output_artifacts":["implementation_result","stage_input_pack"],"next_stage":"TEST","side_effect_actions":["source.write"]},
    }}


def pack(stage, open_items=None, requested_actions=None, requested_outputs=None, write_proofs=None):
    return {"stage_input_pack":{
        "metadata":{"pack_id":"PACK-1","project_id":"GENERIC-1","project_mode":"BROWNFIELD","stage":stage,"source_revision":"rev-1","profile":"STANDARD"},
        "target":{"primary_id":"RQ-1","target_type":"RQ","related_ids":{}},
        "open_items":open_items or [],
        "execution":{"requested_actions":requested_actions or [],"requested_outputs":requested_outputs or [],"write_proofs":write_proofs or {}},
    }}


def test_profile():
    cfg={"resolver":{"default_profile":"STANDARD"},"profiles":{"LITE":{"human_artifacts":{"requirement_customer_view":"MUST","impact_analysis":"CONDITIONAL","separate_6w":"OFF"},"internal_capabilities":{"canonical_trace":"MUST"}}},"invariants":["trace"]}
    result=resolve_profile(cfg,{"artifacts":{"profile":"LITE"}})
    assert result["profile"]=="LITE"
    assert "separate_6w" in result["disabled"]
    stage=resolve_stage(routing(),pack("DISCOVERY"),result)["stage_execution"]
    assert "impact_analysis" not in stage["expected_outputs"]
    stage=resolve_stage(routing(),pack("DISCOVERY",requested_outputs=["impact_analysis"]),result)["stage_execution"]
    assert "impact_analysis" in stage["expected_outputs"]


def test_stage_nonblocking_open():
    p=pack("DISCOVERY",[{"open_id":"OPEN-1","blocks_reasoning":False,"blocks_action":False}])
    result=resolve_stage(routing(),p)["stage_execution"]
    assert result["read_only_progress_allowed"] is True
    assert "source.search" in result["required_capabilities"]
    assert result["nonblocking_open_ids"]==["OPEN-1"]


def test_action_guard_and_write_proof():
    item={"open_id":"OPEN-WRITE","blocks_reasoning":False,"blocks_action":True,"action_scopes":["source.write"]}
    result=resolve_stage(routing(),pack("DEVELOPMENT",[item],["source.write"]))["stage_execution"]
    assert "source.write" in result["required_capabilities"]
    action=[x for x in result["side_effect_actions"] if x["action"]=="source.write"][0]
    assert action["state"]=="GUARDED"

    clear_pack=pack("DEVELOPMENT",requested_actions=["source.write"])
    clear_plan=resolve_stage(routing(),clear_pack)
    context=build_command_context(clear_pack,clear_plan,"/work")
    missing=[x for x in context["human_actions"] if x.get("type")=="WRITE_PROOF_REQUIRED"]
    assert len(missing)==3
    assert context["write_intent"] is True


def test_optional_provider_missing_is_partial():
    context={"command":"/work","command_id":"CMD-1","requested_capabilities":["source.search"],"required_capabilities":[],"human_actions":[]}
    plan,errors=build_plan(registry(),context)
    assert not errors
    runtime=plan["runtime_plan"]
    assert runtime["status"]=="PARTIAL"
    assert runtime["executable"] is True
    assert runtime["open_items"][0]["blocks_action"] is False
    result=execute(registry(),context)["command_runtime_result"]
    assert result["state"]=="PARTIAL"


def test_required_provider_missing_blocks_action():
    context={"command":"/work","command_id":"CMD-2","requested_capabilities":["source.search"],"required_capabilities":["source.search"],"human_actions":[]}
    plan,errors=build_plan(registry(),context)
    assert not errors
    runtime=plan["runtime_plan"]
    assert runtime["status"]=="ACTION_REQUIRED"
    assert runtime["open_items"][0]["blocks_action"] is True
    result=execute(registry(),context)["command_runtime_result"]
    assert result["state"]=="ACTION_REQUIRED"


def bootstrap_config():
    return {"bootstrap":{"scan_policy":{"max_depth":2},"brownfield_markers":{"source_directories":["src"],"build_files":["pom.xml"]},"document_candidates":["README.md"],"data_candidates":["db"]},"greenfield_decisions":["development_language","framework"]}


def test_bootstrap_modes_and_p1_compatibility():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        profile={"project":{"name":"generic","mode":"AUTO"},"artifacts":{"profile":"LITE"}}
        doc=bootstrap(root,profile,registry(),bootstrap_config())
        result=doc["project_bootstrap"]
        assert result["resolved_mode"]=="GREENFIELD"
        assert all(x["state"]=="OPEN" for x in result["technology_decisions"])
        assert validate_bootstrap(doc)==[]
        (root/"pom.xml").write_text("<project/>",encoding="utf-8")
        doc=bootstrap(root,profile,registry(),bootstrap_config())
        result=doc["project_bootstrap"]
        assert result["resolved_mode"]=="BROWNFIELD"
        assert result["entry_gate"]["first_work_allowed"] is True
        assert result["entry_gate"]["source_claim_allowed"] is False
        assert validate_bootstrap(doc)==[]


def test_bounded_source_collection():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        (root/"src").mkdir()
        (root/"src"/"service.py").write_text("def run():\n    return 1\n",encoding="utf-8")
        target={"source_target":{"target_id":"RQ-CAND-1","target_type":"RQ_CANDIDATE","direct_paths":["src/service.py"],"explicit_relations":[]}}
        result=collect_bounded_source(root,"rev-1",target)["source_discovery_result"]
        assert result["artifacts"][0]["path"]=="src/service.py"
        assert result["artifacts"][0]["file_hash"]
        assert result["constraints"]["source_behavior_is_not_business_truth"] is True
        assert result["metadata"]["language_specific_parsing"] is False


def test_generic_reverse_sync():
    change={"source_change_evidence":{"change_id":"CHG-1","source_revision_before":"a","source_revision_after":"b","changed_files":[{"path":"src/service.py","signals":["added_or_changed_branch_condition"]}]}}
    graph={"reference_graph":{"nodes":[
        {"node_id":"SRC-1","node_type":"SOURCE","source_ref":"src/service.py","title":"service.py"},
        {"node_id":"PGM-1","node_type":"PGM","title":"Program"},
        {"node_id":"BR-1","node_type":"BR","title":"Rule"},
    ],"edges":[
        {"edge_id":"E-1","from_id":"SRC-1","to_id":"PGM-1","status":"CONFIRMED","truth_state":"CONFIRMED"},
        {"edge_id":"E-2","from_id":"SRC-1","to_id":"BR-1","status":"CONFIRMED","truth_state":"CONFIRMED"},
    ]}}
    classification={"classification_precedence":["BUSINESS_RULE_CANDIDATE","UNKNOWN"],"candidate_signals":{"BUSINESS_RULE_CANDIDATE":["added_or_changed_branch_condition"]}}
    result=build_reverse_sync(change,graph,classification)["reverse_sync_candidate"]
    assert result["semantic_change_class"]=="BUSINESS_RULE_CANDIDATE"
    assert [x["node_id"] for x in result["stale_candidates"]]==["PGM-1"]
    assert [x["node_id"] for x in result["review_candidates"]]==["BR-1"]
    assert result["protected_human_truth"] is True


def test_repository_contract_shapes_and_no_pilot_leak():
    graph_template=load_actual("sdlc/templates/reference-graph.yaml")["reference_graph"]
    assert "nodes" in graph_template and "edges" in graph_template

    open_template=load_actual("sdlc/templates/open-item.yaml")["open_item"]
    for key in ("open_id","blocks_reasoning","blocks_action","action_scopes","required_evidence","escalation"):
        assert key in open_template, key
    assert "blocks_side_effecting_action" not in open_template

    stage_routing=load_actual("sdlc/config/stage-routing.yaml")["stages"]
    test_stage=stage_routing["TEST"]
    assert "test.execute" not in (test_stage.get("required_capabilities") or [])
    assert "test.execute" in (test_stage.get("side_effect_actions") or [])

    profile=load_actual("sdlc/config/project-profile.example.yaml")
    refs=[
        profile["bootstrap"]["runtime_script"],
        profile["artifacts"]["resolver"],
        profile["handoff"]["stage_resolver"],
        profile["handoff"]["command_context_builder"],
        profile["source_discovery"]["inventory_script"],
        profile["source_discovery"]["reverse_sync_script"],
    ]
    for rel in refs:
        assert (ROOT/rel).is_file(), rel

    active_core=[
        "sdlc/config/stage-routing.yaml",
        "sdlc/config/bootstrap-runtime.yaml",
        "sdlc/config/source-discovery.yaml",
        "sdlc/config/source-analyzers.yaml",
        "sdlc/config/reverse-sync-classification.yaml",
        "sdlc/scripts/bootstrap_project.py",
        "sdlc/scripts/discover_source_inventory.py",
        "sdlc/scripts/collect_bounded_source_evidence.py",
        "sdlc/scripts/build_reverse_sync_from_signals.py",
        "sdlc/scripts/route_provider_command.py",
        "sdlc/scripts/execute_command_runtime.py",
    ]
    forbidden=["REQ_TM_TE","RQG-CAND-6BB6D66548","AttendanceClose","ATT-CLOSE","FORCE_CLOSE","TB_ATT_","10분"]
    text="\n".join((ROOT/x).read_text(encoding="utf-8") for x in active_core)
    for token in forbidden:
        assert token not in text, f"pilot token leaked into active core: {token}"


def main():
    tests=[
        test_profile,
        test_stage_nonblocking_open,
        test_action_guard_and_write_proof,
        test_optional_provider_missing_is_partial,
        test_required_provider_missing_blocks_action,
        test_bootstrap_modes_and_p1_compatibility,
        test_bounded_source_collection,
        test_generic_reverse_sync,
        test_repository_contract_shapes_and_no_pilot_leak,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"PASS structural redesign tests={len(tests)}")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
