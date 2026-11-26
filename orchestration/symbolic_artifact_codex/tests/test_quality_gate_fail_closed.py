"""Negative tests for the three M03-QA1 quality-gate bypasses.

Each bypass test FAILS against the pre-fix evaluator (the bypass is
demonstrable) and PASSES against the patched evaluator (the bypass is
closed). The positive control passes against both, proving the fixes
do not break the legitimate PASS / M04-unlock path.

Run from the directory containing evaluate_ecosystem_quality.py:
    python -m unittest test_quality_gate_fail_closed -v
"""

import copy
import unittest

from evaluate_ecosystem_quality import (
    AXIS_NAMES,
    CRITICAL_AXES,
    IntegrityError,
    evaluate_bundle,
    m04_unlock_allowed,
)


def _axes(status="PASS", evidence_refs=None):
    return {
        name: {
            "critical": name in CRITICAL_AXES,
            "status": status,
            "evidence_refs": ["README.md"] if evidence_refs is None else evidence_refs,
        }
        for name in AXIS_NAMES
    }


def _entity(entity_id, **overrides):
    obj = {
        "id": entity_id,
        "owner": "accountable-owner",
        "stop_condition": "stop",
        "rollback": "rollback",
        "receipt_required": True,
        "boundary_policy": {
            "observation_immutable": True,
            "confidence_grants_authority": False,
        },
        "parent_invariants": ["INV-1"],
        "axes": _axes(),
    }
    obj.update(overrides)
    return obj


def _bundle(spec_overrides=None, drop_spec_keys=()):
    ecosystems = [_entity(f"ECO-{i:02d}") for i in range(1, 9)]
    specializations = []
    for i in range(1, 9):
        spec = _entity(
            f"SPEC-{i:02d}",
            ecosystem_id=f"ECO-{i:02d}",
            inherits_parent_pass=False,
            agent_self_approval=False,
            artifact_hash_matches=True,
            preserved_parent_invariants=["INV-1"],
            upstream_gate_status="PASS",
            requested_decision="PASS",
        )
        if spec_overrides:
            spec.update(spec_overrides)
        for key in drop_spec_keys:
            spec.pop(key, None)
        specializations.append(spec)
    return {
        "schema_version": "0.1",
        "ecosystems": ecosystems,
        "specializations": specializations,
    }


class TestUpstreamHoldBypass(unittest.TestCase):
    """Bypass 1: upstream HOLD (or omitted request) still validated PASS."""

    def test_upstream_hold_caps_specialization_at_hold(self):
        bundle = _bundle({"upstream_gate_status": "HOLD", "requested_decision": "HOLD"})
        report = evaluate_bundle(bundle, {"github_fat_status": "PASS"})
        self.assertTrue(all(r["decision"] == "HOLD" for r in report["specializations"]))
        self.assertEqual(report["decision"], "HOLD")

    def test_omitted_requested_decision_caps_at_hold(self):
        bundle = _bundle(drop_spec_keys=("requested_decision",))
        report = evaluate_bundle(bundle, {"github_fat_status": "PASS"})
        self.assertTrue(all(r["decision"] == "HOLD" for r in report["specializations"]))
        self.assertEqual(report["decision"], "HOLD")


class TestHumanReviewDigestBypass(unittest.TestCase):
    """Bypass 2: editing the report after approval still unlocked M04."""

    def _hold_report_and_review(self):
        bundle = _bundle()
        bundle["specializations"][0]["axes"]["Q1_IDENTITY"]["status"] = "HOLD"
        report = evaluate_bundle(bundle, {"github_fat_status": "PASS"})
        assert report["decision"] == "HOLD"
        review = {
            "reviewer_kind": "human",
            "independent": True,
            "approved": True,
            "decision_digest": report["decision_digest"],
        }
        return report, review

    def test_tampered_report_cannot_unlock_m04(self):
        report, review = self._hold_report_and_review()
        gates = {"github_fat_status": "PASS"}
        # The untampered HOLD report correctly stays locked.
        self.assertFalse(m04_unlock_allowed(report, gates, review))
        # Flip only the top-level decision; the critical HOLD inside
        # and both stored digest strings are left untouched.
        tampered = copy.deepcopy(report)
        tampered["decision"] = "PASS"
        with self.assertRaises(IntegrityError):
            m04_unlock_allowed(tampered, gates, review)


class TestNullEvidenceBypass(unittest.TestCase):
    """Bypass 3: null / non-string evidence references still passed."""

    def test_null_evidence_refs_rejected(self):
        bundle = _bundle()
        for entity in bundle["ecosystems"] + bundle["specializations"]:
            entity["axes"] = _axes(evidence_refs=[None])
        with self.assertRaises(IntegrityError):
            evaluate_bundle(bundle, {"github_fat_status": "PASS"})

    def test_non_string_evidence_refs_rejected(self):
        bundle = _bundle()
        for entity in bundle["ecosystems"] + bundle["specializations"]:
            entity["axes"] = _axes(evidence_refs=[123])
        with self.assertRaises(IntegrityError):
            evaluate_bundle(bundle, {"github_fat_status": "PASS"})


class TestLegitimatePathStillWorks(unittest.TestCase):
    """Positive control: a genuine PASS bundle still passes and unlocks."""

    def test_pass_bundle_and_matching_review_unlock_m04(self):
        report = evaluate_bundle(_bundle(), {"github_fat_status": "PASS"})
        self.assertEqual(report["decision"], "PASS")
        review = {
            "reviewer_kind": "human",
            "independent": True,
            "approved": True,
            "decision_digest": report["decision_digest"],
        }
        self.assertTrue(
            m04_unlock_allowed(report, {"github_fat_status": "PASS"}, review)
        )


if __name__ == "__main__":
    unittest.main()
