# EV Fleet Optimizer Architecture (Dark)

```mermaid
%%{init: {'theme': 'base', 'logLevel': 'fatal', 'background': '#060606', 'themeVariables': { 'primaryColor': '#101010', 'primaryTextColor': '#ffffff', 'primaryBorderColor': '#3a3a3a', 'secondaryColor': '#161616', 'secondaryTextColor': '#ffffff', 'tertiaryColor': '#101010', 'tertiaryTextColor': '#ffffff', 'edgeLabelBackground': '#101010', 'lineColor': '#f5f5f5', 'textColor': '#ffffff' }}}%%
flowchart TD
  user[User on ASI:One / Agentverse] -->|Chat| chat(ASI:One Chat Protocol)
  chat --> mailbox[Agentverse Mailbox]
  mailbox --> orch[Orchestrator Agent (uAgents)]

  subgraph Services
    tel[Telemetry Service]
    price[Price Service]
    kg[Grid-KG Service\n(CSV + optional MeTTa)]
    eval[Evaluation Service]
    fmt[Formatting Service]
  end

  subgraph Optimizers
    greedy[Greedy Heuristic]
    milp[OR-Tools MILP]
  end

  orch -->|get fleet state| tel
  orch -->|get price curve| price
  orch -->|constraints| kg
  orch -->|objective & horizon| greedy
  orch -->|objective & horizon| milp
  greedy --> sched[Schedule]
  milp --> sched

  sched --> eval --> KPIs[KPIs]
  sched --> fmt --> summary[Summary + Preview]
  KPIs --> fmt

  fmt --> orch -->|ChatMessage| mailbox --> user
```
