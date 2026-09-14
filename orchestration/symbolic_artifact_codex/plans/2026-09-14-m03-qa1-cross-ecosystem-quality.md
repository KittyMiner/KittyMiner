# M03-QA1 Cross-Ecosystem Quality Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic fail-closed quality evaluator for eight ecosystems and eight first specializations while keeping M04 locked until human review and the existing GitHub FAT both pass.

**Architecture:** Use JSON-subset YAML registries plus a pure Python standard-library evaluator. Separate contract validation from decision derivation, hash only deterministic report content, and keep the pre-existing GitHub FAT as an external gate input rather than modifying it.

**Tech Stack:** Python 3 standard library, `unittest`, JSON Schema as a contract artifact, JSON-compatible YAML 1.2 registry files.

**Spec:** `orchestration/symbolic_artifact_codex/docs/M03-QA1-cross-ecosystem-quality-design.md`

## Global Constraints

- Exactly eight ecosystems: `ECO-01` through `ECO-08`.
- Exactly eight quality axes: `Q1_IDENTITY` through `Q8_SPECIALIZATION`.
- Critical axes: Q1-Q6 and Q8.
- Any critical RED => REDESIGN.
- Any critical HOLD => HOLD.
- Numeric score never overrides a critical HOLD/RED.
- Exactly twelve frozen negative-path fixtures must pass.
- No specialization may inherit parent PASS without independent evidence.
- Cold replay of identical inputs must produce an identical decision digest.
- Human review is mandatory before overall M03-QA1 PASS.
- Existing GitHub FAT must equal PASS before M04 unlock.
- M04 defaults LOCKED.
- Do not modify the sealed GitHub FAT JSONL, its SHA-256, or canonical IDs.

---

### Task 1: Freeze quality contract and registries

**Files:**
- Create: `quality/quality_contract.schema.json`
- Create: `quality/ecosystem_registry.yaml`
- Create: `quality/specialization_registry.yaml`
- Create: `quality/baseline_2026-09-14.yaml`

**Interfaces:**
- Consumes: approved M03-QA1 design contract.
- Produces: registry objects parsed with `json.load()` and consumed by `evaluate_bundle()`.

- [ ] **Step 1: Add registry-shape tests**

Tests assert exactly 8 ecosystems, exactly 8 specializations, all eight axes on every object, and Q1-Q6/Q8 marked critical.

- [ ] **Step 2: Run tests and verify RED**

Run:
`python -m unittest orchestration.symbolic_artifact_codex.tests.test_ecosystem_quality -v`

Expected: failure because registry/evaluator artifacts do not yet exist.

- [ ] **Step 3: Add minimal contract and registry files**

Populate current evidence posture honestly: design-only ecosystems retain HOLD axes; ECO-06 records the implemented/tested idempotency planner but live FAT remains HOLD.

- [ ] **Step 4: Re-run registry tests**

Expected: registry-shape tests PASS while evaluator-behavior tests remain RED until Task 2.

### Task 2: Implement deterministic evaluator

**Files:**
- Create: `scripts/evaluate_ecosystem_quality.py`
- Modify: `tests/test_ecosystem_quality.py`

**Interfaces:**
- Produces: `load_json_yaml(path) -> dict`, `validate_bundle(bundle) -> None`, `evaluate_bundle(bundle, external_gates) -> dict`, `canonical_digest(report) -> str`, `m04_unlock_allowed(report, external_gates, human_review) -> bool`.

- [ ] **Step 1: Write failing decision tests**

Required cases:
- all critical PASS and score >= .85 => PASS;
- critical HOLD => HOLD even if every other axis PASS;
- critical RED => REDESIGN;
- M04 false when GitHub FAT != PASS;
- M04 false when human review missing.

- [ ] **Step 2: Run tests and verify RED**

Expected failure: evaluator functions absent.

- [ ] **Step 3: Implement minimal pure evaluator**

Use deterministic key sorting and no timestamps in the decision core. Treat score as diagnostic only.

- [ ] **Step 4: Run tests and verify GREEN**

Expected: decision tests PASS.

### Task 3: Freeze and execute 12 negative paths

**Files:**
- Modify: `tests/test_ecosystem_quality.py`

**Interfaces:**
- Consumes: evaluator functions from Task 2.
- Produces: exactly 12 named negative-path qualification tests.

- [ ] **Step 1: Add all 12 tests from the design spec**

Each test mutates one otherwise valid fixture and asserts `IntegrityError`, HOLD, or REDESIGN according to the contract.

- [ ] **Step 2: Run tests and verify any uncovered behavior fails**

Run the full module with `-v` and confirm each negative fixture executes independently.

- [ ] **Step 3: Add only the minimal evaluator validation needed**

No additional policy surface beyond the frozen twelve fixtures.

- [ ] **Step 4: Run full suite**

Required: 12/12 negative paths pass and 0 fail.

### Task 4: Prove cold reconstruction and parent-invariant preservation

**Files:**
- Modify: `tests/test_ecosystem_quality.py`

**Interfaces:**
- Consumes: canonical report generator.
- Produces: deterministic digest and specialization invariant checks.

- [ ] **Step 1: Add cold replay test**

Evaluate deep-copied identical inputs twice and assert exact report equality plus identical SHA-256 digest.

- [ ] **Step 2: Add parent-invariant preservation test**

For every specialization assert `set(preserved_parent_invariants) == set(parent_invariants)`.

- [ ] **Step 3: Run full suite**

Expected: deterministic equality and invariant preservation PASS.

### Task 5: Generate progress register and decision receipt

**Files:**
- Create: `plans/M03-QA1_progress_register.yaml`
- Create: `issues/receipts/M03-QA1_quality_decision.json`

**Interfaces:**
- Consumes: fresh test results and baseline evaluation.
- Produces: auditable qualification state.

- [ ] **Step 1: Evaluate committed baseline twice**

Record technical evaluator status, ecosystem HOLDs, specialization HOLDs, and identical decision digest.

- [ ] **Step 2: Record acceptance coverage**

Receipt must include booleans for registry completeness, eight-axis binding, fail-closed critical axes, 12/12 negative paths, parent-invariant preservation, cold replay equality, receipt creation, human-review status, GitHub FAT status, and M04 lock.

- [ ] **Step 3: Set overall disposition conservatively**

Use `HOLD_PENDING_HUMAN_REVIEW_AND_GITHUB_FAT` unless both external gates are actually PASS. Do not self-approve.

### Task 6: Final verification and integration proposal

**Files:**
- Verify all files above.

- [ ] **Step 1: Run complete unit-test command**

`python -m unittest discover -s orchestration/symbolic_artifact_codex/tests -p 'test_*.py' -v`

Required: zero failures/errors.

- [ ] **Step 2: Re-read receipt against approved acceptance contract**

Required: every acceptance field is explicitly represented and M04 remains LOCKED.

- [ ] **Step 3: Compare child branch to parent branch**

Confirm no sealed FAT artifact path changed.

- [ ] **Step 4: Open a draft PR to the existing M03 branch**

Base: `gaia/symbolic-codex-idempotency-fat-v0.2`.
Head: `gaia/m03-qa1-cross-ecosystem-quality-v0.1`.
The PR must state technical test results and remaining HOLD blockers without claiming M04 readiness.
