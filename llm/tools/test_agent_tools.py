def main():
    # --- lazy imports inside main so standalone execution works -------------
    from langgraph.prebuilt import create_react_agent
    from langchain_core.messages import HumanMessage
    from llm.tools.Tools_aggregator import get_tools
    from llm.LLMDefinition import LLM
    from llm.util.agent_log_formatter import format_log_message

    # Individual tool names
    from llm.tools.paper_handling_tools import (
        retry_broaden,
        reformulate_query,
        accept,
        detect_out_of_scope_query,
        narrow_query,
        multi_step_reasoning,
        filter_by_user_defined_metrics,
    )

    print("\n========== PHASE 1: DIRECT TOOL TESTING ==========\n")

    # ------------------- sample payloads -----------------------------------
    sample_papers = [            # minimal subset for filter demo
        {
            "id": "W1",
            "title": "Paper A",
            "publication_date": "2023-05-10",
            "cited_by_count": 3,
            "similarity_score": 0.91,
            "journal": "Nature",
        },
        {
            "id": "W2",
            "title": "Paper B",
            "publication_date": "2021-12-01",
            "cited_by_count": 42,
            "similarity_score": 0.76,
            "journal": "arXiv",
        },
    ]

    # ------------------- PHASE-1 input table --------------------------------
    tool_inputs = {
        # ---------------- existing tools -----------------------------------
        "retry_broaden": [
            {"query_description": "My research is about yeast metabolism under moonlight.",
             "keywords": ["yeast", "metabolism", "moonlight"]},
        ],
        "reformulate_query": [
            {"query_description": "biotech bio something cancer cell therapy general stuff",
             "keywords": ["biotech", "cancer", "cell therapy"]},
        ],
        "accept": [
            {"confirmation": "yes"},
        ],
        "detect_out_of_scope_query": [
            {"query_description": "How are you doing today?"},
        ],

        # ---------------- NEW tools ----------------------------------------
        "narrow_query": [
            {"query_description": "Large-scale review of all transformer models in biology",
             "keywords": ["transformer", "biology", "deep learning", "protein folding", "drug discovery"]},
        ],
        "multi_step_reasoning": [
            {"query_description": "LLMs for adverse-event detection and transformer architectures for trial-protocol generation",
             "keywords": ["llm", "adverse events", "pharmacovigilance", "transformer", "clinical trials"]},
        ],
        "filter_by_user_defined_metrics": [
            {
                "papers": sample_papers,
                "filter_spec": {
                    "similarity_score": {"op": ">", "value": 0.8},
                    "publication_date": {"op": ">=", "value": 2022},
                },
            },
            {
                "papers": sample_papers,
                "criteria_nl": "Keep only papers after 2022 with similarity above 0.8",
            },
        ],
    }

    # ------------------- execute each tool ---------------------------------
    for tool_name, input_list in tool_inputs.items():
        print(f"\n🛠️ Tool: {tool_name.upper()}")
        for inputs in input_list:
            print(f"Input: {json.dumps(inputs, indent=2)}")
            if tool_name == "retry_broaden":
                out = retry_broaden.invoke(inputs)
            elif tool_name == "reformulate_query":
                out = reformulate_query.invoke(inputs)
            elif tool_name == "accept":
                out = accept.invoke(inputs)
            elif tool_name == "detect_out_of_scope_query":
                out = detect_out_of_scope_query.invoke(inputs)
            elif tool_name == "narrow_query":
                out = narrow_query.invoke(inputs)
            elif tool_name == "multi_step_reasoning":
                out = multi_step_reasoning.invoke(inputs)
            elif tool_name == "filter_by_user_defined_metrics":
                out = filter_by_user_defined_metrics.invoke(inputs)
            else:
                out = "❌ Unknown tool"
            print("Output:", out)
            print("-" * 70)

    # =================== PHASE 2: agent streaming ==========================
    print("\n========== PHASE 2: AGENT STREAMING TESTING ==========\n")

    tools = get_tools()
    agent = create_react_agent(model=LLM, tools=tools)

    system_prompt = HumanMessage(content="""
    You are a helpful academic-research assistant.

    Available tools
    • retry_broaden                  – widen an over-specific keyword set
    • reformulate_query              – clean up vague or messy wording
    • narrow_query                   – focus an over-broad keyword set
    • multi_step_reasoning           – decompose a multi-topic query into coherent sub-queries
    • filter_by_user_defined_metrics – keep / drop papers by date, citations, similarity, etc.
    • accept                         – confirm the query needs no change
    • detect_out_of_scope_query      – reject greetings or non-research requests

    Decision rules
    1. If the request is clearly not about scientific literature → call `detect_out_of_scope_query`.
    2. Apply exactly **one** QC tool:
        ▸ use `multi_step_reasoning` for long multi-topic queries
        ▸ use `narrow_query` for broad queries
        ▸ use `retry_broaden` for very narrow queries
        ▸ use `reformulate_query` for vague / noisy queries
        ▸ use `accept` if the query is already well-formed.
    3. If the user specifies numerical or metadata constraints,
        invoke `filter_by_user_defined_metrics` on the candidate-paper list.
    4. Return **only** the tool result (JSON), no extra commentary.
    5. If the user gives date / citation / similarity or other numeric
        constraints, FIRST call `get_best_papers`, THEN call
        `filter_by_user_defined_metrics` with the papers you just fetched and
        the same criteria.
    """)

    agent_test_queries = [
        "Large-scale review of all transformer models in biology",                 # → narrow_query
        "LLMs for adverse-event detection and trial-protocol generation",          # → multi_step_reasoning
        "Please show papers after 2022 with >0.8 similarity about protein drugs",  # → filter + maybe reformulate
        "How are you doing today?",                                                # → out_of_scope
    ]

    def stream_agent_reasoning(query: str):
        print(f"\n🔍 Query: {query}\n")
        last_step = None
        for step in agent.stream(
            {"messages": [system_prompt, HumanMessage(content=query)]},
            {"recursion_limit": 8},
            stream_mode="values",
        ):
            log = step["messages"][-1].pretty_repr()
            print(format_log_message(log))
            last_step = step
        print("\n✅ Final Agent Output:\n",
              last_step["messages"][-1].content if last_step else "⚠️  no output")

    for q in agent_test_queries:
        stream_agent_reasoning(q)


if __name__ == "__main__":
    import json   # needed for pretty-printing input payloads
    main()
