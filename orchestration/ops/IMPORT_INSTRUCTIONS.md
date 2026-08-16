# Import Instructions

## GitHub
1. Commit `.github/ISSUE_TEMPLATE/*` to the repo.
2. Create labels from `orchestration/README.md`.
3. Seed issues from `orchestration/github/issue_seed.csv`.
4. Build a project board with columns:
   - Backlog
   - Exploring
   - Testing
   - Governance Review
   - Approved
   - Deployed
   - Validated

## Notion
1. Create a database with columns:
   - Name
   - Status
   - Domain
   - Agent Assigned
   - Objective
   - Governance Gate
   - 30d Retro
   - 50d Retro
   - 90d Retro
2. Import `orchestration/notion/notion_horizon_cards.csv`.

## Agents
- Use `orchestration/agents/agent_registry.yaml` as the authority map.
- Route all outputs through `orchestration/governance/governance_gates.yaml`.
