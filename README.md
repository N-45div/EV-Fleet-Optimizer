# EV Fleet Charge Optimizer (ASI Alliance)

![tag:innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)
![tag:hackathon](https://img.shields.io/badge/hackathon-5F43F1)

An ASI Alliance–native agent system that optimizes EV fleet charging schedules to minimize cost and peak load while meeting operational constraints. Built with Fetch.ai uAgents, ASI:One Chat Protocol, and a MeTTa-style Grid Knowledge Graph.

## Problem Statement
- Utility prices spike when EV depots charge simultaneously, and fleet operators juggle price volatility, charger constraints, and service-level commitments manually.
- Dispatchers need a conversational assistant that can reason over chargers, depots, and schedules, simulate what-if scenarios, and surface explainable KPIs before locking a plan.

## Solution Overview
- **EV-Optimizer Orchestrator (uAgents)** — ASI:One-compatible agent that ingests fleet telemetry, grid constraints, and price curves, then produces explainable schedules via greedy + MILP backends.
- **Grid Knowledge Layer (CSV ↔ MeTTa)** — Structured knowledge about depots, site peaks, chargers, and overrides, with optional Hyperon/MeTTa reasoning when `USE_METTA=true`.
- **Optimization Engine** — Greedy heuristic for fast responses and OR-Tools MILP for optimal per-charger assignments under blackout/limit constraints.
- **Frontend Web UI (Flask + Vanilla JS)** — Dashboard mirroring chat capabilities with status, optimizer controls, KPI previews, and what-if configuration.
- **Agentverse Readiness** — Chat protocol manifest, innovation lab badge, and mailbox hooks so the orchestrator can be registered and discovered on Agentverse / ASI:One.

## End-User Value
- **Cost & Peak Control** — Quantifies savings vs. peak flattening KPIs so fleet managers can decide on the fly.
- **Operational Confidence** — Transparent previews, per-vehicle explanations, and remaining charge gaps for dispatch planning.
- **What-If Simulation** — Instant toggling of site peak caps or blackout windows before committing to a plan.
- **Seamless UX** — Conversational interface for quick commands plus a browser dashboard for richer visual review.

## Features
- ASI:One–compatible Chat Orchestrator Agent (discoverable on Agentverse)
- Conversational UX with intents: help, optimize, preview, explain, compare, status, runtime defaults
- Dual optimization backends: greedy heuristic (speed) and OR-Tools MILP (optimal per-charger)
- Grid-KG (CSV + optional MeTTa) for depots, chargers, constraints; runtime what‑ifs (site peak overrides, blackout windows)
- Synthetic telemetry & price feeds (swap with live sources via services layer)
- KPIs & explanations: total cost, peak kW, SLA on-time %, top decisions, vehicle drill-downs
- Frontend dashboard mirroring chat capabilities with REST API bridge

## Quickstart
1. Python 3.11
2. Create venv and install deps:
   ```bash
   python -m venv .venv
   . .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Copy env template and edit values (paste your ASI:One key):
   ```bash
   cp .env.example .env
   # edit .env: ASI_ONE_API_KEY=...
   ```
4. Start the Orchestrator (mailbox mode):
   ```bash
   set -a && source .env && set +a
   python agents/orchestrator_agent.py
   ```


## Frontend Web UI

We ship a simple Flask frontend (backend-for-frontend) that calls the agent’s REST API.

1) Ensure the agent is running on port 8000 (mailbox enabled is fine)
2) Install deps (Flask, requests) are in requirements.txt
3) Run the UI on port 5000

```bash
pip install -r requirements.txt
# in one terminal
set -a && source .env && set +a
python agents/orchestrator_agent.py
# in another terminal
export AGENT_URL=http://127.0.0.1:8000
python frontend/app.py  # opens http://127.0.0.1:5000
```

Endpoints used:
- POST /optimize, POST /compare, GET /status, POST /whatif/site_peak, POST /whatif/blackout

## Agentverse / ASI:One
- The Orchestrator publishes the ASI:One Chat Protocol manifest and connects via mailbox.
- Create the mailbox using the Inspector link printed on startup (Agentverse UI).
- Docs: Overview — https://docs.agentverse.ai/documentation/getting-started/overview
- Hosted agents and ASI compatibility — https://docs.agentverse.ai/documentation/advanced-usages/asi-one-compatible-agent

## Chat Commands
- `help` — show commands
- `optimize 24h|12h [cost|peak]` — run optimization
- `preview [10 vehicles 24h]` — compact schedule table
- `explain [v5]` — top decisions or vehicle details
- `compare cost vs peak [48h]` — KPI comparison
- `status` — defaults and last-run
- `set default objective peak|cost`
- `set default horizon 24h`
- `set backend milp|greedy` — choose optimizer backend
- `set site peak D1 40kW` — runtime site-peak override
- `blackout D2 18-22h` — block depot-hour allocations
- `clear blackouts [D1]`, `clear peak [D1]`

## Environment Flags
- `ASI_ONE_API_KEY` — Agentverse key (mailbox, chat)
- `USE_MAILBOX=true` — enable mailbox transport
- `OBJECTIVE_DEFAULT=cost|peak`
- `AGENT_PORT=8000`, `PUBLIC_ENDPOINT=` (if you expose publicly)
- `BACKEND=greedy|milp`
- `USE_METTA=true|false`
- `PRIVATE_MODE=true|false`

## Repository Structure
- `agents/` — uAgents (orchestrator and optional sub-agents)
- `services/` — local services for telemetry, prices, KG, optimizer
- `kg/` — MeTTa-style KG seed
- `data/` — synthetic datasets
- `tests/` — unit and e2e tests
- `docs/` — architecture and demo notes

## Submission Notes
- Include your Orchestrator agent name and address here once registered on Agentverse.
- Include 3–5 min demo video link.

## Security
- `.env` is git-ignored. Never commit your API keys.

## Roadmap / Upcoming Enhancements
- **MeTTa Deepening** — Publish `kg/metta_rules.metta` with richer charger/depot logic, expose MeTTa-backed insights in chat/UI.
- **Frontend Polish** — Rebuild UI with Framer Motion-powered interactions, KPI charts, and Agentverse deep links.
- **Telemetry Integrations** — Swap synthetic feeds with real data sources (OCPP, utility APIs) configurable via `.env`.
- **Automated Testing** — Pytest coverage for optimizers, REST endpoints, and regression scenarios.

## Deployment (always-on)

You can deploy without Docker using a user-level systemd service. This keeps the agent alive across restarts and reboots.

1) Create the unit file (adjust the path if your repo is elsewhere):

```ini
# ~/.config/systemd/user/ev-optimizer.service
[Unit]
Description=EV Fleet Charge Optimizer (uAgents)
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/divij/fetch-agent
EnvironmentFile=/home/divij/fetch-agent/.env
ExecStart=/home/divij/fetch-agent/.venv/bin/python /home/divij/fetch-agent/agents/orchestrator_agent.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
```

2) Enable and start (user services):

```bash
systemctl --user daemon-reload
systemctl --user enable --now ev-optimizer.service
systemctl --user status ev-optimizer.service -n 50 --no-pager
# Logs
journalctl --user -u ev-optimizer.service -f
```

3) Optional: keep running after logout (may require admin policy):

```bash
loginctl enable-linger "$USER"
```

### Docker (alternative)

```bash
docker build -t ev-optimizer .
docker run -p 8000:8000 --env-file .env ev-optimizer
# If exposing publicly, set PUBLIC_ENDPOINT in .env
```

