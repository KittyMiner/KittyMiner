# Horizon Operations

This repository now contains a governance-gated 30/50/90-day execution system.

## Current horizons

- **H1 (30d):** immediate execution through 2026-10-17
- **H2 (50d):** integration through 2026-11-06
- **H3 (90d):** scale and research through 2026-12-16

## Automation

- `.github/workflows/seed-horizons.yml` — reads `data/horizons/*.json` and creates domain/horizon-labeled issues when GitHub Issues are enabled.
- `.github/workflows/agent-runner.yml` — scoped agent dispatch acknowledgment. It explicitly limits authority to analysis/drafting and routes work through evidence → review → approve → merge/deploy gates.
- `.github/workflows/retros.yml` — opens 30/50/90-day retrospective issues from `data/horizons/retros.json`.

## GitHub Projects configuration

Use `ops/project-boards.json` as the canonical specification for the first three Projects:

1. **H1 — 30-Day Execution**
2. **H2 — 50-Day Integration**
3. **H3 — 90-Day Scale & Research**

Recommended common fields: Status, Horizon, Domain, Priority, Risk, Evidence, Gate, Owner, Due, KPI, Dependencies, Repository Path.

## Repository prerequisite

GitHub Issues are currently disabled for this repository. The seeding workflow detects this and exits successfully instead of failing. To populate issue-backed boards, enable Issues for `KittyMiner/KittyMiner`, then manually run **Seed Horizons -> Issues** once.

GitHub Projects creation is not available through the connected GitHub automation interface used to build this repository, so the board definitions are stored as version-controlled configuration rather than silently claiming the Projects were created.
