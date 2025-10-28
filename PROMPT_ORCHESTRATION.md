# 🧠 Prompt Orchestration & Retrospective Schedule

This markdown document outlines the protocol for multi-domain prompt orchestration, autonomous agent routing, and long-horizon retrospectives for Unit Costing and DfM phases.

---

## ✅ GitHub Issue Template
- **Path**: `.github/ISSUE_TEMPLATE/feature-request.yml`
- **Fields**: Description, Impact, Domain (tagged)

## ✅ Notion Tagging & Prompt Database
- **Location**: Notion → Propulsion Blueprints → Unit Costing → DfM Pass 01
- **Fields**: Prompt, Domain, Agent Scope, Review Cadence, Governance Gate

## 🤖 Autonomous Agent Routing
- Prompt triggers domain-tagged webhook → assigns to agent batch
- Outputs are routed through governance validation and logged

## 🔁 Retrospective Timeline
| Interval | Goal                          | Actions                                   |
|----------|-------------------------------|-------------------------------------------|
| 30 Days | Initial KPI & scope check     | Prune, refine, reroute low-performing     |
| 50 Days | Forking/merging & feedback     | Combine/fork agents, reassign prompts     |
| 90 Days | Full audit + drift detection  | Escalate, retire, upgrade, realign        |

## 🛠️ Ops Tracker
- [x] Branch for issue template created
- [x] Prompt orchestration Notion DB initialized
- [x] Agent trigger webhooks scaffolded
- [ ] Merge PR

> For changes, raise a GitHub issue with label `infra` or `governance`.