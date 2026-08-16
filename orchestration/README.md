# Coordinated Orchestration Scaffold

This bundle seeds domain-based workstreams for:
- GitHub issue board scaffolding
- Notion prompt-card import
- Scoped agent routing
- Governance gates
- 30d / 50d / 90d retrospectives

## Included
- `github/issue_seed.csv` — issue-ready horizon cards with labels
- `.github/ISSUE_TEMPLATE/` — reusable issue templates by domain
- `notion/notion_horizon_cards.csv` — import-ready CSV for Notion
- `agents/agent_registry.yaml` — scoped agents and authority boundaries
- `governance/governance_gates.yaml` — review, merge/fork, and audit logic
- `retros/retrospective_schedule.md` — scheduled checkpoints
- `diagrams/orchestration_flow.mmd` — Mermaid flowchart of agent routing

## Suggested GitHub Labels
- domain:quantum
- domain:security
- domain:terraform
- domain:governance
- domain:ethics
- domain:infrastructure
- domain:monitoring
- status:exploring
- status:testing
- status:deployed
- status:validated
- gate:review
- gate:approved
- gate:fork
- gate:merge

## Suggested Board Columns
- Backlog
- Exploring
- Testing
- Governance Review
- Approved
- Deployed
- Validated
