import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "sdlc/scripts/validate_empirical_pilot_evidence.py"
SPEC = importlib.util.spec_from_file_location("empirical_pilot_evidence", SCRIPT)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MOD)
PILOT_ROOT = ROOT / "sdlc/validation/pilots"


def load_example(name: str) -> dict:
    return json.loads((PILOT_ROOT / name).read_text(encoding="utf-8"))


class EmpiricalPilotEvidenceTest(unittest.TestCase):
    def test_all_pilot_templates_are_explicit_not_run(self):
        for name in [
            "external-agent-tailoring-pilot.example.json",
            "human-first-use-pilot.example.json",
            "brownfield-reconciliation-pilot.example.json",
        ]:
            with self.subTest(name=name):
                result = MOD.validate(load_example(name))
                self.assertEqual("NOT_RUN", result["verdict"])
                self.assertFalse(result["empirical_pass"])

    def test_unobserved_pilot_cannot_claim_pass(self):
        data = load_example("external-agent-tailoring-pilot.example.json")
        data["claims"]["external_agent_empirical_pass"] = True
        result = MOD.validate(data)
        self.assertEqual("FAIL_OVERCLAIMED_PASS", result["verdict"])
        self.assertIn("UNOBSERVED_PILOT_CANNOT_CLAIM_PASS", result["errors"])

    def test_external_agent_observed_three_profiles_can_pass_with_identity_and_human_review(self):
        data = load_example("external-agent-tailoring-pilot.example.json")
        data.update({
            "execution_status": "OBSERVED",
            "observed_at": "2026-09-07T10:00:00+09:00",
            "observer": "pilot-observer-01",
        })
        data["provider"]["provider_id"] = "observed-provider-01"
        data["provider"]["identity_evidence"] = ["session:agent-run-001", "observer-log:pilot-001"]
        for row in data["profile_runs"]:
            row["artifact_paths"] = [f"docs/pilot/{row['profile_id']}/artifact.md"]
            row["semantic_review"] = {
                "reviewer": "semantic-reviewer-01",
                "meaning_preserved": True,
                "unsupported_business_fact_count": 0,
                "material_omission_count": 0,
                "notes": "관찰 Pilot 기준 충족",
            }
        data["claims"]["external_agent_empirical_pass"] = True
        result = MOD.validate(data)
        self.assertEqual("PASS_OBSERVED_EMPIRICAL_PILOT", result["verdict"])
        self.assertTrue(result["empirical_pass"])
        self.assertFalse(result["production_ready_claimed"])

    def test_external_agent_label_without_identity_evidence_is_not_empirical_pass(self):
        data = load_example("external-agent-tailoring-pilot.example.json")
        data.update({
            "execution_status": "OBSERVED",
            "observed_at": "2026-09-07T10:00:00+09:00",
            "observer": "pilot-observer-01",
        })
        data["claims"]["external_agent_empirical_pass"] = True
        result = MOD.validate(data)
        self.assertEqual("FAIL_OVERCLAIMED_PASS", result["verdict"])
        self.assertIn("MISSING_PROVIDER_IDENTITY_EVIDENCE", result["errors"])
        self.assertFalse(result["empirical_pass"])

    def test_human_first_use_requires_observed_participants_and_zero_critical_blockers(self):
        data = load_example("human-first-use-pilot.example.json")
        data.update({
            "execution_status": "OBSERVED",
            "observed_at": "2026-09-07T11:00:00+09:00",
            "observer": "human-pilot-observer",
            "participants": [
                {
                    "participant_id": "P01",
                    "role": "업무분석",
                    "started_from_start_here": True,
                    "completed_without_framework_designer": True,
                    "critical_blocker_count": 0,
                    "review_burden_rating_1_to_5": 2,
                },
                {
                    "participant_id": "P02",
                    "role": "설계/개발",
                    "started_from_start_here": True,
                    "completed_without_framework_designer": True,
                    "critical_blocker_count": 0,
                    "review_burden_rating_1_to_5": 3,
                },
                {
                    "participant_id": "P03",
                    "role": "PM",
                    "started_from_start_here": True,
                    "completed_without_framework_designer": True,
                    "critical_blocker_count": 0,
                    "review_burden_rating_1_to_5": 2,
                },
            ],
        })
        passed = MOD.validate(data)
        self.assertEqual("PASS_OBSERVED_EMPIRICAL_PILOT", passed["verdict"])
        self.assertTrue(passed["empirical_pass"])

        failed_data = copy.deepcopy(data)
        failed_data["participants"][1]["critical_blocker_count"] = 1
        failed = MOD.validate(failed_data)
        self.assertEqual("FAIL_OBSERVED_EMPIRICAL_PILOT", failed["verdict"])
        self.assertFalse(failed["empirical_pass"])

    def test_brownfield_source_only_is_insufficient_but_source_plus_confirmed_truth_and_review_can_pass(self):
        data = load_example("brownfield-reconciliation-pilot.example.json")
        data.update({
            "execution_status": "OBSERVED",
            "observed_at": "2026-09-07T12:00:00+09:00",
            "observer": "brownfield-pilot-observer",
            "evidence": [
                {
                    "evidence_class": "CURRENT_SOURCE_DB_CONFIG_RUNTIME_EVIDENCE",
                    "ref": "source:OmsOrderController#list",
                }
            ],
        })
        source_only = MOD.validate(data)
        self.assertEqual("FAIL_INSUFFICIENT_EVIDENCE", source_only["verdict"])
        self.assertIn("MISSING_BROWNFIELD_AUTHORITY_EVIDENCE", source_only["errors"])

        data["evidence"].append({
            "evidence_class": "CONFIRMED_HUMAN_BUSINESS_TRUTH",
            "ref": "decision:BUSINESS-001",
        })
        data["reviewer_decision"] = "Source 관찰은 AS-IS 근거로 유지하고 Business Truth는 자동 수정하지 않는다."
        reconciled = MOD.validate(data)
        self.assertEqual("PASS_OBSERVED_EMPIRICAL_PILOT", reconciled["verdict"])
        self.assertTrue(reconciled["empirical_pass"])
        self.assertFalse(reconciled["production_ready_claimed"])


if __name__ == "__main__":
    unittest.main()
