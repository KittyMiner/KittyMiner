# M03-QA1 Cross-Ecosystem Quality Gate Design

## Status

Approved design contract for `GAIA_SYMBOLIC_ARTIFACT_CODEX_M03-QA1_cross_ecosystem_quality_specialization_qualification_gate_v0.1`.

This is an M03 extension. It does not authorize M04.

## Objective

Add a deterministic, fail-closed quality evaluator that classifies the eight Symbolic Artifact Codex ecosystems and their first deeper specializations without allowing aggregate scores, model confidence, or parent status to hide a critical failure.

## Frozen acceptance contract

```yaml
M03_QA1_acceptance:
  ecosystem_registry_complete: true
  eight_quality_axes_bound: true
  critical_axes_fail_closed: true
  negative_paths_passed: 12
  negative_paths_failed: 0
  specialization_parent_invariants_preserved: true
  cold_reconstruction_identical: true
  receipt_generated: true
  human_review: required

  existing_github_fat:
    required_for_M04_unlock: PASS

  M04:
    default: LOCKED
```

## Quality axes

Every ecosystem and specialization binds all eight axes:

1. `Q1_IDENTITY` — canonical identity is immutable and non-recycled.
2. `Q2_EVIDENCE` — claims reconstruct to explicit evidence.
3. `Q3_BOUNDARY` — evidence, semantics, and authority remain separated.
4. `Q4_AUTHORITY` — accountable human authority remains explicit.
5. `Q5_NEGATIVE_PATH` — bypass and failure paths are tested.
6. `Q6_REPLAY` — state and decisions reconstruct deterministically.
7. `Q7_OBSERVABILITY` — status, blockers, receipts, and drift are visible.
8. `Q8_SPECIALIZATION` — child specialization adds qualification without weakening parent invariants.

`Q1` through `Q6` and `Q8` are critical. `Q7` is non-critical but still required.

## Decision semantics

Axis states are `PASS`, `HOLD`, or `RED`.

- Any critical `RED` => `REDESIGN`.
- Else any critical `HOLD` => `HOLD`.
- Else if the weighted informational score is below `0.85` => `HOLD`.
- Else => `PASS`.

The score is diagnostic only. It can never override a critical `HOLD` or `RED`.

## Registry model

The ecosystem registry contains exactly `ECO-01` through `ECO-08`. Each entry includes owner, maturity, parent invariants, boundary policy, rollback/stop controls, receipt policy, and all eight quality axes with evidence references.

The specialization registry contains one first specialization per ecosystem:

- `PROVENANCE-LINEAGE`
- `ONTOLOGY-XREF`
- `SCENE-GRAPH-INTEGRITY`
- `EPISTEMIC-CONTAINMENT`
- `AUTHORITY-LEASE`
- `ISSUE-IDEMPOTENCY`
- `CONSERVATION-LINEAGE`
- `CULTURAL-RIGHTS`

Each specialization independently binds all eight axes and explicitly lists the parent invariants it preserves. Parent PASS cannot be inherited as child PASS.

## Required negative paths

The evaluator must fail closed or downgrade the decision for all twelve cases:

1. missing accountable owner;
2. missing evidence reference for a PASS axis;
3. critical HOLD masked by a high aggregate score;
4. child specialization attempting to inherit parent PASS without its own axis evidence;
5. agent self-approval;
6. interpretation permitted to overwrite observation;
7. confidence permitted to grant authority;
8. stale or mismatched artifact hash;
9. missing stop condition or rollback control;
10. downstream PASS requested while an upstream gate is HOLD;
11. child specialization weakens a parent invariant;
12. receipt disabled or omitted after an attempt.

## Determinism and cold reconstruction

Evaluation is a pure function of canonical registry bytes plus explicit external gate inputs. Reports contain no timestamps or nondeterministic ordering in the hashed decision core. Two evaluations of identical inputs must produce the same canonical report digest.

## Human review and M04 lock

Technical qualification may establish that the evaluator and fixtures satisfy this contract, but the overall M03-QA1 decision remains `HOLD_PENDING_HUMAN_REVIEW` until an accountable human review object is supplied.

M04 remains locked unless all of the following are true:

- M03-QA1 technical decision is `PASS`;
- human review is present, independent of the executing agent, and approves the exact decision digest;
- the pre-existing GitHub idempotency FAT is `PASS`;
- no critical ecosystem or specialization axis is `HOLD` or `RED`.

The existing reviewed JSONL FAT artifact, its SHA-256, and canonical issue IDs are immutable inputs and are out of scope for modification in this build.

## Outputs

The build creates:

- `quality/quality_contract.schema.json`
- `quality/ecosystem_registry.yaml`
- `quality/specialization_registry.yaml`
- `quality/baseline_2026-09-14.yaml`
- `scripts/evaluate_ecosystem_quality.py`
- `tests/test_ecosystem_quality.py`
- `plans/M03-QA1_progress_register.yaml`
- `issues/receipts/M03-QA1_quality_decision.json`

All `.yaml` registry files use the JSON subset of YAML 1.2 so the evaluator can parse them with Python's standard library and introduce no new runtime dependency.
