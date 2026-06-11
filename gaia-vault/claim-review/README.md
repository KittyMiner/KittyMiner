# Gaia Vault Claim Review Registry Patch

**Patch run:** `GV-CLAIM-REVIEW-SOURCE-SCAN-PATCH-001`  
**Template:** `GAIA-VAULT-CLAIM-REVIEW-TEMPLATE-001`  
**Status:** active retroactive source-registry gate  
**Date:** 2026-06-11

This directory installs the Gaia Vault claim-review fields and validation rules for YAML, JSON, Markdown, spreadsheet-derived, and derived-node records.

## Required fields

Every previous and future Gaia/GUC node should expose these fields either directly, in YAML frontmatter, in a sidecar claim-review record, or in the Notion/Gaia Governance Gates registry:

- `node_id`
- `title`
- `version`
- `source_assets`
- `claim_type`
- `evidence_layer`
- `evidence_level`
- `validation_status`
- `blocked_claims`
- `permitted_uses`
- `review_required`
- `public_release_status`
- `promotion_requirements`
- `audit_trail`
- `next_actions`

## Restricted claim defaults

| Claim class | Default status |
|---|---|
| `physical_law_claims` | `blocked_pending_validation` |
| `energy_claims` | `blocked_pending_validation` |
| `resonance_causality_claims` | `blocked_pending_validation` |
| `propulsion_field_claims` | `blocked_pending_validation` |
| `hidden_constant_encoding_claims` | `blocked_pending_validation` |
| `medical_safety_compliance_certification_claims` | `blocked_pending_qualified_review` |
| `investment_or_performance_claims` | `blocked_pending_evidence_and_legal_review` |

## Permitted before validation

Unvalidated assets may be used for symbolic mapping, education, hypothesis generation, internal reference, and simulation seeding only when assumptions are explicit.

## Promotion requirements

Claims require provenance, accepted-science comparison where applicable, explicit equations or mechanisms, dimensional checks, reproducible computation or simulation, calibrated measurement for physical claims, controls/null models, uncertainty analysis, safety review, and independent or qualified review before public physical, medical, investment, energy, resonance, propulsion, or field claims.

## Scan outcome

- Notion: `Gaia Governance Gates` schema was patched with the required fields and 23 known previous Gaia/GUC entries were inserted/backfilled.
- GitHub: the current writable installation exposed `KittyMiner/KittyMiner`; no existing Gaia Vault source files were found there, so this directory adds the registry patch and validator without overwriting profile README content.
- File library: Gaia Vault YAML/JSON/Markdown/spreadsheet artifacts were identified and exported into the claim-review manifest, but uploaded File Library objects are references and cannot be mutated in place by this GitHub patch.

## Files

- `claim_review_template.yaml` — canonical schema and gate defaults.
- `backfill_manifest_summary.json` — compact source-registry patch manifest.
- `source_registry_scan_report.md` — scan and patch report.
- `scripts/gaia_claim_review_validator.py` — repository validator for claim-review fields.
