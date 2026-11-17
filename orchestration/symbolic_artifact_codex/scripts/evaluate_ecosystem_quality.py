#!/usr/bin/env python3
"""Deterministic, fail-closed M03-QA1 ecosystem quality evaluator."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

AXIS_NAMES = (
    "Q1_IDENTITY",
    "Q2_EVIDENCE",
    "Q3_BOUNDARY",
    "Q4_AUTHORITY",
    "Q5_NEGATIVE_PATH",
    "Q6_REPLAY",
    "Q7_OBSERVABILITY",
    "Q8_SPECIALIZATION",
)
CRITICAL_AXES = frozenset(a for a in AXIS_NAMES if a != "Q7_OBSERVABILITY")
VALID_AXIS_STATUS = frozenset({"PASS", "HOLD", "RED"})
EXPECTED_ECOSYSTEM_IDS = tuple(f"ECO-{i:02d}" for i in range(1, 9))
SCORE = {"PASS": 1.0, "HOLD": 0.5, "RED": 0.0}
PASS_SCORE_THRESHOLD = 0.85


class IntegrityError(RuntimeError):
    """Raised when a registry violates a frozen fail-closed invariant."""


def load_json_yaml(path: str | Path) -> dict[str, Any]:
    """Load a JSON-subset YAML 1.2 document using only the stdlib."""
    with Path(path).open("r", encoding="utf-8") as f:
        obj = json.load(f)
    if not isinstance(obj, dict):
        raise IntegrityError(f"registry root must be an object: {path}")
    return obj


def _validate_axes(owner_id: str, axes: dict[str, Any]) -> None:
    if set(axes) != set(AXIS_NAMES):
        missing = sorted(set(AXIS_NAMES) - set(axes))
        extra = sorted(set(axes) - set(AXIS_NAMES))
        raise IntegrityError(f"{owner_id}: invalid axis set missing={missing} extra={extra}")
    for name in AXIS_NAMES:
        axis = axes[name]
        expected_critical = name in CRITICAL_AXES
        if bool(axis.get("critical")) != expected_critical:
            raise IntegrityError(f"{owner_id}:{name}: critical flag mismatch")
        status = axis.get("status")
        if status not in VALID_AXIS_STATUS:
            raise IntegrityError(f"{owner_id}:{name}: invalid status {status!r}")
        evidence_refs = axis.get("evidence_refs")
        if status == "PASS" and (not isinstance(evidence_refs, list) or not any(str(x).strip() for x in evidence_refs)):
            raise IntegrityError(f"{owner_id}:{name}: PASS requires evidence_refs")


def _validate_common(obj: dict[str, Any], kind: str) -> None:
    obj_id = str(obj.get("id", "")).strip()
    if not obj_id:
        raise IntegrityError(f"{kind}: missing id")
    if not str(obj.get("owner", "")).strip():
        raise IntegrityError(f"{obj_id}: missing accountable owner")
    if not str(obj.get("stop_condition", "")).strip() or not str(obj.get("rollback", "")).strip():
        raise IntegrityError(f"{obj_id}: stop_condition and rollback are required")
    if obj.get("receipt_required") is not True:
        raise IntegrityError(f"{obj_id}: receipt_required must be true")
    policy = obj.get("boundary_policy") or {}
    if policy.get("observation_immutable") is not True:
        raise IntegrityError(f"{obj_id}: observation must remain immutable")
    if policy.get("confidence_grants_authority") is not False:
        raise IntegrityError(f"{obj_id}: confidence cannot grant authority")
    parent_invariants = obj.get("parent_invariants")
    if not isinstance(parent_invariants, list) or not parent_invariants:
        raise IntegrityError(f"{obj_id}: parent_invariants required")
    _validate_axes(obj_id, obj.get("axes") or {})


def validate_bundle(bundle: dict[str, Any]) -> None:
    ecosystems = bundle.get("ecosystems")
    specializations = bundle.get("specializations")
    if not isinstance(ecosystems, list) or len(ecosystems) != 8:
        raise IntegrityError("ecosystem registry must contain exactly 8 ecosystems")
    ecosystem_ids = tuple(sorted(str(x.get("id", "")) for x in ecosystems))
    if ecosystem_ids != EXPECTED_ECOSYSTEM_IDS:
        raise IntegrityError(f"ecosystem IDs must be exactly {EXPECTED_ECOSYSTEM_IDS}")

    for eco in ecosystems:
        _validate_common(eco, "ecosystem")

    if not isinstance(specializations, list) or len(specializations) != 8:
        raise IntegrityError("specialization registry must contain exactly 8 specializations")

    seen_specialization_ids: set[str] = set()
    per_ecosystem: dict[str, int] = {eid: 0 for eid in EXPECTED_ECOSYSTEM_IDS}
    ecosystem_by_id = {e["id"]: e for e in ecosystems}
    for spec in specializations:
        _validate_common(spec, "specialization")
        spec_id = str(spec["id"])
        if spec_id in seen_specialization_ids:
            raise IntegrityError(f"duplicate specialization id: {spec_id}")
        seen_specialization_ids.add(spec_id)
        eco_id = spec.get("ecosystem_id")
        if eco_id not in ecosystem_by_id:
            raise IntegrityError(f"{spec_id}: unknown ecosystem_id {eco_id!r}")
        per_ecosystem[eco_id] += 1
        if spec.get("inherits_parent_pass") is not False:
            raise IntegrityError(f"{spec_id}: child cannot inherit parent PASS")
        if spec.get("agent_self_approval") is not False:
            raise IntegrityError(f"{spec_id}: agent self-approval prohibited")
        if spec.get("artifact_hash_matches") is not True:
            raise IntegrityError(f"{spec_id}: stale or mismatched artifact hash")
        if set(spec.get("preserved_parent_invariants") or []) != set(spec.get("parent_invariants") or []):
            raise IntegrityError(f"{spec_id}: parent invariant weakening detected")
        if set(spec["parent_invariants"]) != set(ecosystem_by_id[eco_id]["parent_invariants"]):
            raise IntegrityError(f"{spec_id}: parent invariant binding differs from ecosystem")
        upstream = spec.get("upstream_gate_status")
        requested = spec.get("requested_decision")
        if requested == "PASS" and upstream != "PASS":
            raise IntegrityError(f"{spec_id}: downstream PASS blocked by upstream {upstream!r}")

    if any(count != 1 for count in per_ecosystem.values()):
        raise IntegrityError(f"exactly one specialization required per ecosystem: {per_ecosystem}")


def _entity_result(obj: dict[str, Any]) -> dict[str, Any]:
    critical_statuses = [obj["axes"][name]["status"] for name in CRITICAL_AXES]
    if "RED" in critical_statuses:
        decision = "REDESIGN"
    elif "HOLD" in critical_statuses:
        decision = "HOLD"
    else:
        score = sum(SCORE[obj["axes"][name]["status"]] for name in AXIS_NAMES) / len(AXIS_NAMES)
        decision = "PASS" if score >= PASS_SCORE_THRESHOLD else "HOLD"
    score = sum(SCORE[obj["axes"][name]["status"]] for name in AXIS_NAMES) / len(AXIS_NAMES)
    return {
        "id": obj["id"],
        "decision": decision,
        "score": round(score, 6),
        "critical_holds": sorted(name for name in CRITICAL_AXES if obj["axes"][name]["status"] == "HOLD"),
        "critical_reds": sorted(name for name in CRITICAL_AXES if obj["axes"][name]["status"] == "RED"),
    }


def canonical_digest(report: dict[str, Any]) -> str:
    core = dict(report)
    core.pop("decision_digest", None)
    encoded = json.dumps(core, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def evaluate_bundle(bundle: dict[str, Any], external_gates: dict[str, Any] | None = None) -> dict[str, Any]:
    validate_bundle(bundle)
    external_gates = dict(external_gates or {})
    ecosystem_results = [_entity_result(x) for x in sorted(bundle["ecosystems"], key=lambda x: x["id"])]
    specialization_results = [_entity_result(x) for x in sorted(bundle["specializations"], key=lambda x: x["id"])]
    all_results = ecosystem_results + specialization_results
    if any(x["decision"] == "REDESIGN" for x in all_results):
        decision = "REDESIGN"
    elif any(x["decision"] == "HOLD" for x in all_results):
        decision = "HOLD"
    else:
        decision = "PASS"

    report = {
        "schema_version": str(bundle.get("schema_version", "0.1")),
        "decision": decision,
        "ecosystems": ecosystem_results,
        "specializations": specialization_results,
        "external_gates": {"github_fat_status": str(external_gates.get("github_fat_status", "HOLD"))},
        "human_review_required": True,
        "m04_default": "LOCKED",
    }
    report["decision_digest"] = canonical_digest(report)
    return report


def _validate_human_review(report: dict[str, Any], human_review: dict[str, Any] | None) -> bool:
    if not human_review:
        return False
    if human_review.get("reviewer_kind") != "human":
        raise IntegrityError("human review cannot be supplied by an agent")
    if human_review.get("independent") is not True:
        raise IntegrityError("human reviewer must be independent")
    if human_review.get("approved") is not True:
        return False
    if human_review.get("decision_digest") != report.get("decision_digest"):
        raise IntegrityError("human review digest does not match decision digest")
    return True


def m04_unlock_allowed(
    report: dict[str, Any],
    external_gates: dict[str, Any],
    human_review: dict[str, Any] | None,
) -> bool:
    if report.get("decision") != "PASS":
        return False
    if external_gates.get("github_fat_status") != "PASS":
        return False
    return _validate_human_review(report, human_review)


def load_bundle(ecosystems_path: str | Path, specializations_path: str | Path) -> dict[str, Any]:
    eco_doc = load_json_yaml(ecosystems_path)
    spec_doc = load_json_yaml(specializations_path)
    return {
        "schema_version": eco_doc.get("schema_version", spec_doc.get("schema_version", "0.1")),
        "ecosystems": eco_doc.get("ecosystems", []),
        "specializations": spec_doc.get("specializations", []),
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--ecosystems", required=True)
    parser.add_argument("--specializations", required=True)
    parser.add_argument("--github-fat-status", default="HOLD", choices=["PASS", "HOLD", "REDESIGN"])
    parser.add_argument("--output")
    args = parser.parse_args()
    report = evaluate_bundle(load_bundle(args.ecosystems, args.specializations), {"github_fat_status": args.github_fat_status})
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
