# GAIA Symbolic Artifact Codex — Control Geometry v0.2

## Objective

Consolidate the symbolic-language, artifact-preservation, ontology, scene-graph, annotation, CI-governance, and GitHub issue-orchestration work into one governed vertical architecture.

## Geometric reasoning model

Treat the system as three orthogonal planes joined only through typed, receipted edges:

1. **Evidence plane** — physical artifact → capture/scan → immutable binary/hash → observation/measurement.
2. **Semantic plane** — symbol instance → ontology concept → correspondence/interpretation → scene graph/ritual or contextual structure.
3. **Authority plane** — proposal → validation → review/approval → execution lease → mutation → receipt → replay/audit.

No plane is allowed to silently collapse into another. In particular:

- interpretation never overwrites observation;
- visual similarity never becomes provenance;
- correspondence never becomes historical fact without evidence;
- confidence never becomes authority;
- a generated issue title never becomes canonical identity;
- a successful first execution never authorizes uncontrolled replay.

## Canonical graph

```text
PhysicalArtifact
      │ captured_as
      ▼
   ScanSet ──hash──▶ ImmutableBinary
      │
      ├──observed_as────────▶ Observation
      │
      └──contains───────────▶ SymbolInstance
                                │ references
                                ▼
                           SymbolDefinition
                                │ maps_to
                                ▼
                          Concept/Correspondence
                                │ supported_by
                                ▼
                         Claim / Source Receipt

ReviewedIssueArtifact ──SHA256──▶ ExecutionAttempt
        │ canonical IDs               │
        │                             ├──CREATED
        │                             └──SKIPPED_ALREADY_EXISTS
        ▼                             │
 CanonicalIssueID ◀───────────────────┘
```

## Frozen invariants

- Stable IDs are immutable and never recycled.
- Visual-symbol IDs and concept IDs occupy separate namespaces.
- Variants are additive (`..._01`, `..._02`, `..._03`), never destructive overwrites.
- Unknown/disputed correspondences remain explicit and do not receive guessed values.
- Every scene-graph relation is typed and directional.
- Every nontrivial semantic edge carries provenance/evidence posture.
- Cross-reference failure is fail-closed.
- GitHub issue identity is `issue_id`, not mutable title text.
- Every created GitHub issue embeds `<!-- gaia-canonical-issue-id:<ID> -->`.
- Same canonical ID on replay means SKIP, including closed issues.
- Same title without the expected canonical marker is a collision and must fail closed.
- Duplicate canonical IDs in payload or repository are integrity violations.
- Production creation remains guarded by review artifact hash, protected approval, explicit create/prod confirmation, and CI allow flag.
- Every execution attempt emits a receipt.

## Governance gates

```text
SOURCE GATE
  ↓
RIGHTS / CULTURAL GATE
  ↓
ONTOLOGY GATE
  ├─ correspondence schema
  ├─ cross references
  ├─ scene graph references
  └─ strict symbol-ID lint
  ↓
DATASET / ANNOTATION GATE
  ↓
MODEL / INTERPRETATION GATE
  ↓
REVIEWED ISSUE ARTIFACT GATE
  ↓
PROTECTED EXECUTION GATE
  ↓
RECEIPT + IDEMPOTENT REPLAY FAT
```

## Thread consolidation

This module is the control spine for the previous work on:

- symbol JSON Schema and stable symbol naming;
- `correspondences.yaml` and cross-domain concept mappings;
- scene-graph annotations and ritual/context step extraction;
- expert annotation rules and uncertainty handling;
- ontology CI and strict naming lint;
- artifact preservation metadata, IIIF/capture, damage/restoration context, provenance and rights;
- Notion/GitHub roadmap scaffolding with GOV / SAFE / CUL responsibilities;
- reviewed JSONL generation, checksums, protected production creation, and idempotent replay.

## Current decisive FAT

Exact reviewed artifact:

`issues/reviewed/issues_idempotency_fat.jsonl`

Frozen SHA-256:

`180897cf23cdee4b804642e46b65f784eeb99615116340d3ab8daa8b430ad024`

Expected:

```text
Run 1: CREATED=N, SKIPPED=0
Run 2: CREATED=0, SKIPPED=N
```

The same canonical IDs must resolve to the same GitHub issue identities after both passes, with no duplicates.