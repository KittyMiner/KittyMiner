# GAIA Prompt Governance — Ten-Module Implementation Plan v0.2

> **For agentic workers:** Implement one independently reviewable slice at a time; use fresh test/review cycles. Never infer a gate promotion from a code test.

**Date:** 2026-10-24  
**Case:** SCN-PGC-001  
**Goal:** Build offline-first, governed prompt analysis and routing proposals in the single `KittyMiner/KittyMiner` repository, projected into existing Notion Gaia Board records without production execution.  
**Architecture:** Typed Python contracts and a deterministic policy decision layer; analysis modules produce proposals; registries define capabilities; a fail-closed router cannot execute without separately verified human authorization. Evidence is captured locally before Notion read-only reconciliation.  
**Tech:** Python 3.11+, stdlib `dataclasses`, `json`, `hashlib`, `unittest` initially (no runtime network dependency); optional adapters remain disabled.

## Global constraints

- Work only in a reviewed feature branch under `governance/prompt_governance/`, `tests/prompt_governance/`, and `docs/superpowers/`.
- Preserve existing `gaia-vault/claim-review/` contract; do not change `Nodes.csv`, `Edges.csv`, Lane A canonical kernel, live policies, approvals, Notion authority, or `main` outside a human-reviewed merge.
- Default `execute=False`; no external network, cloud, email, money movement, medical action, production agent routing, or policy grant.
- Stable case ID: `SCN-PGC-001`; module IDs: `UPG-PGC-01` … `UPG-PGC-10`.
- Per module: write negative-path test, run it to fail, implement minimum code, run targeted test, run full offline test suite, capture exit code and revision SHA, request human review.
- If a test cannot be executed, record `NOT_RUN`, never PASS. No external action may be authorized by a local PASS.

## File boundaries

```text
governance/prompt_governance/
    __init__.py
    contracts.py          # typed request, decision, evidence and classification objects
    engine.py             # deterministic policy evaluation
    compass.py            # classification only
    forks.py              # alternative proposals
    clauses.py            # typed constraints
    agents.py             # manifest validation
    capabilities.py       # capability validation
    router.py             # offline route proposal, no execution
    validation.py         # negative paths and aggregate receipts
    ledger.py             # local JSONL hash-linked event prototype
    notion_projection.py  # read-only diff builder
tests/prompt_governance/
    test_engine.py
    test_compass.py
    test_forks.py
    test_clauses.py
    test_agents.py
    test_capabilities.py
    test_router.py
    test_validation.py
    test_ledger.py
    test_notion_projection.py
```

## Task 1 — Typed contracts and default-deny engine (UPG-PGC-01)

- [ ] Create `contracts.py`: immutable `Decision` dataclass with `schema_version`, `case_id`, `request_digest`, `policy_version`, `verdict`, `reason_codes`, `evidence_roots`, `action_authorized`.
- [ ] In `test_engine.py`, write `test_unknown_policy_denies` asserting `evaluate({"policy_id":"missing"}, {})` gives `DENY` and `action_authorized is False`; run `python3 -m unittest discover -s tests/prompt_governance -p 'test_engine.py' -v` and observe failure.
- [ ] Create `engine.py` with `evaluate(request: dict, registry: dict) -> Decision` where missing policy, missing authority, stale effective root, and invalid input all fail closed.
- [ ] Add tests: same inputs yield same fields except per-run audit timestamp; conflicting grants yield DENY; `HUMAN_REVIEW_REQUIRED` never implies `action_authorized=True`.
- [ ] Run target + entire suite; record `NOT_RUN` if unavailable; commit candidate for code review.

## Task 2 — Agent manifest registry (UPG-PGC-05)

- [ ] Add `agents.py`: `validate_agent(manifest: dict) -> tuple[bool,list[str]]`; require stable ID, version, accountable owner, permitted tools, prohibited actions, environment, expiry/revocation reference.
- [ ] Add `test_agents.py`: missing owner, undeclared tool, revoked agent and expired manifest all reject; run `python3 -m unittest discover -s tests/prompt_governance -p 'test_agents.py' -v`.
- [ ] Reject claims of identity verification from a username or unsigned file alone; validate test cases, then review.

## Task 3 — Capability registry (UPG-PGC-06)

- [ ] Add `capabilities.py`: `validate_capability(requested_id, environment, registry) -> tuple[bool,list[str]]`.
- [ ] Add `test_capabilities.py`: absent, environment mismatch, expired grant, conflicting policies and unreviewed capability all reject; run relevant `unittest`.
- [ ] Keep capability available vs capability authorized separate; review receipt.

## Task 4 — Compass classification (UPG-PGC-02)

- [ ] Add `compass.py`: `classify(prompt: str) -> dict` returning domain, intent, sensitivity, claimed authority, uncertainty and `authorization=None`.
- [ ] Add `test_compass.py`: ambiguity returns uncertainty; adversarial "ignore gates" cannot authorize; empty prompt returns unknown; evaluate fixture stability.
- [ ] Run targeted `unittest`; preserve classification as advisory output.

## Task 5 — Fork analyzer (UPG-PGC-03)

- [ ] Add `forks.py`: `enumerate_forks(goal: str, options: list[dict]) -> list[dict]` including null/do-nothing option and falsifiers.
- [ ] Add `test_forks.py`: missing evidence produces HOLD branch; all options include reversibility and source; no branch auto-executes.
- [ ] Verify deterministic ordering and negative paths.

## Task 6 — ClauseBuilder (UPG-PGC-04)

- [ ] Add `clauses.py`: `build_clause(source_policy: dict, proposed_rule: dict) -> dict` retaining source version and permitted bounds.
- [ ] Add `test_clauses.py`: generated clause cannot widen allowed tools, environments or expiry; source mismatch rejects.
- [ ] Run tests and examine reviewer traceability.

## Task 7 — Execution router proposal (UPG-PGC-07)

- [ ] Add `router.py`: `route(request: dict, decision: Decision, execute: bool=False) -> dict`; return route proposal only, explicit `executed=False` always in this phase.
- [ ] Add `test_router.py`: execute=True raises `PermissionError`; Notion-approved alone cannot route; unknown tool/replay denial fails closed.
- [ ] Do not implement live adapter binding in this phase.

## Task 8 — Validation pipeline (UPG-PGC-08)

- [ ] Add `validation.py`: `qualify(run_results: list[dict]) -> dict` rejecting missing/corrupt proofs; include source commit and test transcript digest.
- [ ] Add `test_validation.py`: a green exit code with missing evidence yields HOLD; failed negative path yields HOLD; cold replay mismatch yields HOLD.
- [ ] Execute full `python3 -m unittest discover -s tests/prompt_governance -p 'test_*.py' -v`, store exact output and return code.

## Task 9 — Evidence Ledger prototype (UPG-PGC-09)

- [ ] Add `ledger.py`: `append_record(path, event) -> str` computing canonical event digest and previous-record reference, and `replay(path) -> dict` verifying linkage.
- [ ] Add `test_ledger.py`: mutation/deletion/reordering rejected; duplicate request IDs rejected; failures leave prior ledger unchanged.
- [ ] Explicitly label JSONL local storage as *tamper-evident prototype*, not immutable custody or independent attestation.

## Task 10 — Dashboard diff only (UPG-PGC-10)

- [ ] Add `notion_projection.py`: `propose_changes(canonical: list[dict], observed: list[dict]) -> list[dict]`; output diff without sending requests.
- [ ] Add `test_notion_projection.py`: duplicate canonical IDs rejected; Notion "Approved" cannot update code authority; missing links yield drift/HOLD.
- [ ] Use existing `scenario_packets`, `upgrade_objects`, `expansion_decisions` fields; no database creation or write adapter in phase 1.

## Review packets and gates

Each task's receipt needs a commit SHA, code diff, test command and full stdout/stderr, exit code, negative paths, source digests, environment, owner and independent reviewer assessment. Tests are not independent review. **A0.1E1 EXIT:** reviewer cold-replay and a named human authorization; until then `IMPLEMENTATION_QUALIFICATION_HOLD`.

The old `Batch:2025-10-24A` and `owner/repo-prompts-*` strings are historical/example configuration, not evidence of GitHub Projects or existing issues. No mass import, label mutation, or project linking is part of this plan.
