import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).parents[1]
MODULE_PATH = ROOT / "scripts" / "evaluate_ecosystem_quality.py"
spec = importlib.util.spec_from_file_location("evaluate_ecosystem_quality", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

IntegrityError = module.IntegrityError
evaluate_bundle = module.evaluate_bundle
canonical_digest = module.canonical_digest
m04_unlock_allowed = module.m04_unlock_allowed
validate_bundle = module.validate_bundle

AXES = [
    "Q1_IDENTITY", "Q2_EVIDENCE", "Q3_BOUNDARY", "Q4_AUTHORITY",
    "Q5_NEGATIVE_PATH", "Q6_REPLAY", "Q7_OBSERVABILITY", "Q8_SPECIALIZATION",
]
CRITICAL = {a: a != "Q7_OBSERVABILITY" for a in AXES}


def axes(status="PASS"):
    return {
        a: {"critical": CRITICAL[a], "status": status, "evidence_refs": [f"evidence:{a}"]}
        for a in AXES
    }


def ecosystem(i):
    return {
        "id": f"ECO-{i:02d}",
        "name": f"Ecosystem {i}",
        "owner": f"OWNER-{i}",
        "maturity": "L3_TESTED",
        "parent_invariants": ["identity_immutable", "authority_human_accountable"],
        "boundary_policy": {"observation_immutable": True, "confidence_grants_authority": False},
        "stop_condition": "critical gate failure",
        "rollback": "restore prior qualified state",
        "receipt_required": True,
        "axes": axes(),
    }


def specialization(i):
    return {
        "id": f"SPEC-{i:02d}",
        "ecosystem_id": f"ECO-{i:02d}",
        "owner": f"SPEC-OWNER-{i}",
        "parent_invariants": ["identity_immutable", "authority_human_accountable"],
        "preserved_parent_invariants": ["identity_immutable", "authority_human_accountable"],
        "inherits_parent_pass": False,
        "agent_self_approval": False,
        "boundary_policy": {"observation_immutable": True, "confidence_grants_authority": False},
        "artifact_hash_matches": True,
        "stop_condition": "critical gate failure",
        "rollback": "restore prior qualified state",
        "receipt_required": True,
        "upstream_gate_status": "PASS",
        "requested_decision": "PASS",
        "axes": axes(),
    }


def valid_bundle():
    return {
        "schema_version": "0.1",
        "ecosystems": [ecosystem(i) for i in range(1, 9)],
        "specializations": [specialization(i) for i in range(1, 9)],
    }


class ContractAndDecisionTests(unittest.TestCase):
    def test_complete_bundle_passes_technical_gate(self):
        report = evaluate_bundle(valid_bundle(), {"github_fat_status": "PASS"})
        self.assertEqual(report["decision"], "PASS")
        self.assertEqual(len(report["ecosystems"]), 8)
        self.assertEqual(len(report["specializations"]), 8)

    def test_critical_red_forces_redesign(self):
        bundle = valid_bundle()
        bundle["ecosystems"][0]["axes"]["Q1_IDENTITY"]["status"] = "RED"
        report = evaluate_bundle(bundle, {"github_fat_status": "PASS"})
        self.assertEqual(report["decision"], "REDESIGN")

    def test_m04_requires_human_review_and_github_fat_pass(self):
        report = evaluate_bundle(valid_bundle(), {"github_fat_status": "PASS"})
        self.assertFalse(m04_unlock_allowed(report, {"github_fat_status": "HOLD"}, None))
        self.assertFalse(m04_unlock_allowed(report, {"github_fat_status": "PASS"}, None))
        review = {
            "reviewer_id": "human-1", "reviewer_kind": "human", "independent": True,
            "approved": True, "decision_digest": report["decision_digest"],
        }
        self.assertTrue(m04_unlock_allowed(report, {"github_fat_status": "PASS"}, review))

    def test_cold_reconstruction_identical(self):
        bundle = valid_bundle()
        one = evaluate_bundle(copy.deepcopy(bundle), {"github_fat_status": "PASS"})
        two = evaluate_bundle(copy.deepcopy(bundle), {"github_fat_status": "PASS"})
        self.assertEqual(one, two)
        self.assertEqual(canonical_digest(one), canonical_digest(two))


class FrozenNegativePathTests(unittest.TestCase):
    def test_neg_01_missing_accountable_owner(self):
        b = valid_bundle(); b["ecosystems"][0]["owner"] = ""
        with self.assertRaises(IntegrityError): validate_bundle(b)

    def test_neg_02_missing_evidence_reference(self):
        b = valid_bundle(); b["ecosystems"][0]["axes"]["Q1_IDENTITY"]["evidence_refs"] = []
        with self.assertRaises(IntegrityError): validate_bundle(b)

    def test_neg_03_critical_hold_cannot_be_masked_by_score(self):
        b = valid_bundle(); b["ecosystems"][0]["axes"]["Q6_REPLAY"]["status"] = "HOLD"
        r = evaluate_bundle(b, {"github_fat_status": "PASS"})
        self.assertEqual(r["decision"], "HOLD")

    def test_neg_04_child_cannot_inherit_parent_pass(self):
        b = valid_bundle(); b["specializations"][0]["inherits_parent_pass"] = True
        with self.assertRaises(IntegrityError): validate_bundle(b)

    def test_neg_05_agent_self_approval_rejected(self):
        b = valid_bundle(); b["specializations"][0]["agent_self_approval"] = True
        with self.assertRaises(IntegrityError): validate_bundle(b)

    def test_neg_06_interpretation_cannot_overwrite_observation(self):
        b = valid_bundle(); b["ecosystems"][0]["boundary_policy"]["observation_immutable"] = False
        with self.assertRaises(IntegrityError): validate_bundle(b)

    def test_neg_07_confidence_cannot_grant_authority(self):
        b = valid_bundle(); b["ecosystems"][0]["boundary_policy"]["confidence_grants_authority"] = True
        with self.assertRaises(IntegrityError): validate_bundle(b)

    def test_neg_08_hash_mismatch_rejected(self):
        b = valid_bundle(); b["specializations"][0]["artifact_hash_matches"] = False
        with self.assertRaises(IntegrityError): validate_bundle(b)

    def test_neg_09_missing_stop_or_rollback_rejected(self):
        b = valid_bundle(); b["ecosystems"][0]["rollback"] = ""
        with self.assertRaises(IntegrityError): validate_bundle(b)

    def test_neg_10_upstream_hold_blocks_downstream_pass(self):
        b = valid_bundle(); b["specializations"][0]["upstream_gate_status"] = "HOLD"
        with self.assertRaises(IntegrityError): validate_bundle(b)

    def test_neg_11_parent_invariant_weakening_rejected(self):
        b = valid_bundle(); b["specializations"][0]["preserved_parent_invariants"] = ["identity_immutable"]
        with self.assertRaises(IntegrityError): validate_bundle(b)

    def test_neg_12_receipt_omission_rejected(self):
        b = valid_bundle(); b["specializations"][0]["receipt_required"] = False
        with self.assertRaises(IntegrityError): validate_bundle(b)


class RegistryFileTests(unittest.TestCase):
    def test_real_registry_is_complete_and_valid(self):
        bundle = module.load_bundle(
            ROOT / "quality" / "ecosystem_registry.yaml",
            ROOT / "quality" / "specialization_registry.yaml",
        )
        validate_bundle(bundle)
        self.assertEqual([e["id"] for e in bundle["ecosystems"]], [f"ECO-{i:02d}" for i in range(1, 9)])
        self.assertEqual(len(bundle["specializations"]), 8)
        for entity in bundle["ecosystems"] + bundle["specializations"]:
            self.assertEqual(set(entity["axes"]), set(AXES))

    def test_real_baseline_is_hold_and_m04_locked(self):
        bundle = module.load_bundle(
            ROOT / "quality" / "ecosystem_registry.yaml",
            ROOT / "quality" / "specialization_registry.yaml",
        )
        baseline = module.load_json_yaml(ROOT / "quality" / "baseline_2026-09-14.yaml")
        one = evaluate_bundle(bundle, baseline["external_gates"])
        two = evaluate_bundle(copy.deepcopy(bundle), baseline["external_gates"])
        self.assertEqual(one, two)
        self.assertEqual(one["decision"], "HOLD")
        self.assertFalse(m04_unlock_allowed(one, baseline["external_gates"], baseline.get("human_review")))


class ReceiptAndProgressTests(unittest.TestCase):
    def test_quality_receipt_covers_frozen_acceptance_contract(self):
        receipt = module.load_json_yaml(ROOT / "issues" / "receipts" / "M03-QA1_quality_decision.json")
        acceptance = receipt["acceptance"]
        self.assertTrue(acceptance["ecosystem_registry_complete"])
        self.assertTrue(acceptance["eight_quality_axes_bound"])
        self.assertTrue(acceptance["critical_axes_fail_closed"])
        self.assertEqual(acceptance["negative_paths_passed"], 12)
        self.assertEqual(acceptance["negative_paths_failed"], 0)
        self.assertTrue(acceptance["specialization_parent_invariants_preserved"])
        self.assertTrue(acceptance["cold_reconstruction_identical"])
        self.assertTrue(acceptance["receipt_generated"])
        self.assertEqual(receipt["human_review"]["status"], "PENDING")
        self.assertEqual(receipt["existing_github_fat"]["status"], "HOLD")
        self.assertEqual(receipt["M04"]["state"], "LOCKED")
        self.assertEqual(receipt["technical_report"]["decision_digest"], "b976fd874019cea7d4abaec9a7750859801f3cc44a0a4414cebecd49197e3eab")

    def test_progress_register_keeps_human_review_and_m04_on_hold(self):
        progress = module.load_json_yaml(ROOT / "plans" / "M03-QA1_progress_register.yaml")
        by_id = {x["task_id"]: x for x in progress["tasks"]}
        self.assertEqual(by_id["QA1-A6"]["status"], "HOLD_PENDING_HUMAN_REVIEW")
        self.assertEqual(progress["M04"]["state"], "LOCKED")


if __name__ == "__main__":
    unittest.main()
