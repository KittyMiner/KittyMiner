# GAIA Prompt Governance Control Plane — Design v0.2

**Date:** 2026-10-24  
**Case:** SCN-PGC-001  
**Scope:** Documentation and bounded, offline development qualification.  
**Repository:** `KittyMiner/KittyMiner` on `design/prompt-governance-control-plane`.  
**Notion system of review:** Gaia Board — Scenario Governance, existing `scenario_packets`, `upgrade_objects`, `expansion_decisions`, and GO/HOLD board.  
**Disposition:** DESIGN_REGISTERED; IMPLEMENTATION_NOT_VERIFIED; PRODUCTION_HOLD.

## Authority contract

Architecture proposes; evidence qualifies; human governance authorizes; execution receipts; independent replay verifies. **PASS is not deployment authority.**

The existing GAIA Vault claim-review contract, `gaia-vault/claim-review/claim_review_template.yaml`, remains authoritative for claim classification, source provenance, review and restricted-claim defaults. This design extends it; it does not replace or silently relax it. The Lane A canonical kernel contract and Nodes.csv/Edges.csv must not be modified by this wave without their separate PR guard.

- Deny-by-default. Unknown policies, missing reviewer attestations, stale authorization, mismatched environment, and missing evidence roots yield HOLD/DENY.
- Agents may classify, simulate, draft, recommend and stop. Human approval is required for consequential external actions, permissions, public claims, spending and production changes.
- Only documentation, versioned schemas, offline deterministic tests and read-only inventory are allowed under this design. No live agent/tool action, scheduled sync, paid service, secrets, repository merge or gate promotion is authorized.
- Every record includes case ID, source record/version, actor type, request digest, policy version, evidence roots, verdict, reason codes, and action scope. Do not put private identity data or secrets into GitHub or Notion.
- A hash by itself is an integrity marker, not proof of custody or a substitute for independently reproduced source bytes.

## System boundary

```text
Input → Compass → Fork Analyzer / ClauseBuilder → Governance Engine
                   ↑ registries: agents, capabilities, policies
Governance Engine → route proposal → HOLD (default)
                ↘ signed human authorization + fresh policy replay
                  → Execution Router → Validation → Evidence Ledger
                                                    ↓
                                        Notion dashboard projection
```

A Notion dashboard is a derived projection and **never** the policy or authorization source. GitHub stores versioned code/policy, but deployed effective policy requires a separately authorized, digest-pinned release. Notion status labels cannot grant rights absent a source approval.

## Modules and exact responsibilities

| ID | Module | Principal output | Gate |
|---|---|---|---|
| PGC-01 | Governance Engine | deterministic `ALLOW/DENY/HOLD/HUMAN_REVIEW_REQUIRED` decision record | unknown/malformed policy denies |
| PGC-02 | Prompt Governance Compass | intent, domain, evidence, privacy, risk classification + uncertainty | classification cannot authorize |
| PGC-03 | Fork Analyzer | bounded branches, null option, falsifiers, assumptions, reversibility | branches not execution |
| PGC-04 | ClauseBuilder | typed constraint clauses with source policy citation | cannot manufacture authority |
| PGC-05 | Agent Manifest Registry | versioned identity, owner, allowed tools, prohibited acts | undeclared agent denied |
| PGC-06 | Capability Registry | versioned capability, env, expiry, evidence and human owner | available ≠ authorized |
| PGC-07 | Execution Router | dry-run routing proposal and explicit preflight rejection | `execute=false` default |
| PGC-08 | Validation Pipeline | schema, policy, negative paths, dry-run replay report | fail closed |
| PGC-09 | Evidence Ledger Adapter | event records with digest and lineage for offline replay | append-only claim unverified until storage proven |
| PGC-10 | Dashboard Synchronization | read-only diff projection and proposed Notion writes | no Notion status-based promotion |

## Data contracts

All contracts are versioned. `decision_id` is unique within a deterministic test run, while `request_digest` is stable for repeated identical inputs.

```json
{
  "schema_version": "0.1",
  "case_id": "SCN-PGC-001",
  "request_digest": "sha256:<hex>",
  "policy_id": "pgc.default-deny",
  "policy_version": "0.1",
  "agent_id": "registered-agent-id",
  "capability_id": "registered-capability-id",
  "environment": "offline",
  "decision": "HOLD",
  "reason_codes": ["APPROVAL_MISSING"],
  "evidence_roots": [],
  "review_required": true,
  "action_authorized": false
}
```

Preserve the distinction among factual claims, modeled predictions, hypotheses, and permissions. The old `Batch:2025-10-24A` label identifies an *unverified proposed/import cohort*, not evidence that issues were actually imported. The earlier `your-org` and `owner/repo-prompts-*` references are placeholders and must never become live destinations.

## Failure modes and negative-path qualification

1. Unknown agent/capability → DENY.
2. Approval exists but mismatched environment, version, scope, expiry, or issuer → HOLD/DENY.
3. Notion says Approved while source authorization absent → HOLD.
4. Stale policy root or wrong proposal ID → reject; effective state root unchanged.
5. Duplicate request or replay → no duplicate consequential action.
6. Missing/corrupt event or digest mismatch → reject cold replay.
7. External routing disabled in offline mode, even if tests pass.
8. Restricted physical/medical/financial/public claim without qualified evidence/review → block public release.

## Notion mapping

- `scenario_packets`: one case `SCN-PGC-001` holding scope and review gate.
- `upgrade_objects`: individually tracked `UPG-PGC-01` through `UPG-PGC-10`; all Draft/Review Required and linked by `Source Scenario Code`.
- `expansion_decisions`: no new advancement disposition before human-signed evidence review.
- GO/HOLD board: no gate changes as a result of roadmap registration.

## Verification and next admissible operation

First qualified slice: PGC-01 + PGC-05/06 schema stubs, deterministic offline tests and fail-closed negative paths; collect reproducible test transcript, dependency manifest, code revision, digest receipt, reviewer-independent cold replay, and an accountable decision. Tests alone do not certify security, deployment, public release, or autonomy.

No API keys, real accounts, protected records, paid tasks, repository merges or live integrations are in scope.
