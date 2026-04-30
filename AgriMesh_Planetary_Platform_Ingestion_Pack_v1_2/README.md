# AgriMesh Planetary Platform Ingestion Pack v1.2

Canonical publication package for the AgriMesh planetary platform ingestion layer.

## Publish state

- registry_status: validated_clean
- publish_status: ready_for_ingestion
- validation_result: pass
- ingestion_gate: approved
- approved_for: platform_catalog, search_index, github_repository, ai_retrieval_layer
- next_action: publish_to_repository

## Operating rule

registry.json governs truth. document_index.csv governs discovery.

## Validation command

```bash
python 08_automation/scripts/sync_registry_and_index.py --root .
```

## Package contents

- Board governance materials
- Master Operating Blueprint
- Investor and funding materials
- Legal and contracting materials
- Timeline and KPI materials
- Metadata registry
- Platform ingestion guides
- Validator and index regeneration automation

## Release tag

agrimesh-ingestion-v1.2
