# Pydantic Graph Agent (prototype)

This directory now hosts a minimal reproduction of the legacy `llm/StategraphAgent`
workflow using [`pydantic-graph`](https://ai.pydantic.dev/graph/).

```python
from llm_pydantic.agent import run_agent_sync

result = run_agent_sync("nuclear fusion control algorithms project ID: demo-42")
print(result)
```

For testing use `Pydantic Agent` configuration in launch.json.

Notes:
- All tools are mocked via `llm_pydantic.tooling.MockToolbelt` so the graph can
  be exercised in isolation.
- Nodes live in `llm_pydantic/nodes/` and each one maps to the steps described in
  `llm/StategraphAgent.py` (input parsing, scope check, QC, retrieval, filtering,
  storage).
- This intentionally **does not** call real LLMs yet; the goal is to validate the
  graph wiring before swapping in production dependencies.
- Need a Mermaid diagram? Call `generate_mermaid_diagram(save_path="agent.mmd")`
  from `llm_pydantic.agent` and open the saved file in
  [mermaid.live](https://mermaid.live) or embed it into docs.
- For quick demos run `python llm_pydantic/agent_cli.py`; it mirrors the legacy
  CLI but uses the mocked toolchain.
- To export the diagram from the terminal, run
  `python llm_pydantic/graph_cli.py --output agent.mmd`.

## State Graph

````mermaid
---
title: graph
---
stateDiagram-v2
  direction LR
  [*] --> InputNode
  InputNode --> ScopeCheckNode
  ScopeCheckNode --> QualityControlNode
  ScopeCheckNode --> OutOfScopeNode
  QualityControlNode --> RetrievePapersNode
  QualityControlNode --> OutOfScopeNode
  RetrievePapersNode --> FilterPapersNode
  FilterPapersNode --> StorePapersNode
  FilterPapersNode --> NoResultsNode
  StorePapersNode --> [*]
  NoResultsNode --> [*]
  OutOfScopeNode --> [*]
````

  ## State Model

  ````mermaid
  ---
  title: AgentState
  ---
  classDiagram
    class AgentState {
      string user_query
      string project_id
      list~string~ keywords
      string qc_decision
      string qc_reason
      bool has_filter_instructions
      string out_of_scope_message
      list~dict~ papers_raw
      list~dict~ papers_filtered
      bool requires_user_input
      string no_results_summary
      dict final_payload
    }

    class AgentOutput {
      string status
      dict detail
    }

  ````
