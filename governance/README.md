# GUC Horizon Governance Scaffold

This repository now hosts the operational scaffolding for six execution horizons:

- Security
- Wet-Lab
- Quantum
- Ethics
- Infrastructure
- Governance

## Layout

- `.github/ISSUE_TEMPLATE/` — domain issue intake forms
- `agents/config/` — scoped autonomous agent YAML definitions
- `governance/boards/` — board definitions, routing rules, and governance gates
- `governance/retros/` — 30d / 50d / 90d retrospective templates

## Execution Rules

1. Tag every intake by domain and horizon.
2. Assign only the scoped agent for that domain.
3. Route deliverables through governance validation.
4. Merge, fork, or prune work during retrospectives.
