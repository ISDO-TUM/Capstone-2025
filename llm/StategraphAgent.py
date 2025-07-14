"""
Stategraph-based agent entrypoint for orchestrating multi-step academic paper search and filtering.
"""

import logging
import json

# from langgraph.graph import StateGraph
# from langchain_core.messages import HumanMessage
from llm.LLMDefinition import LLM
from llm.tools.Tools_aggregator import get_tools

# --- State schema ---
# The state is a dict with the following keys:
# - user_query: str
# - keywords: list[str] (optional)
# - reformulated_query: str (optional)
# - papers_raw: list[dict] (optional)
# - papers_filtered: list[dict] (optional)
# - final_output: dict (optional)

# --- Error handling and logging decorator ---

logger = logging.getLogger("StategraphAgent")
logger.setLevel(logging.INFO)


def node_logger(node_name, input_keys=None, output_keys=None):
    def decorator(func):
        def wrapper(state):
            logger = logging.getLogger("StategraphAgent")
            # Log input state
            if input_keys:
                logger.info(f"[{node_name}] Input: %s", {k: state.get(k) for k in input_keys})
            else:
                logger.info(f"[{node_name}] Input: %s", state)
            try:
                result = func(state)
                # Log output state
                if output_keys:
                    logger.info(f"[{node_name}] Output: %s", {k: result.get(k) for k in output_keys})
                else:
                    logger.info(f"[{node_name}] Output: %s", result)
                return result
            except Exception as e:
                logger.exception(f"[{node_name}] Exception occurred: %s", e)
                state["error"] = str(e)
                return state
        return wrapper
    return decorator

# --- Node: Input Handler ---


@node_logger("input_node", input_keys=["user_query"], output_keys=["user_query", "keywords"])
def input_node(state):
    # Initialize the state with the user query
    user_query = state["user_query"]
    # If the query is a single word or phrase, use it as the initial keyword
    keywords = []
    if user_query and len(user_query.split()) == 1:
        keywords = [user_query]
    return {
        "user_query": user_query,
        "keywords": keywords,
        "reformulated_query": None,
        "papers_raw": [],
        "papers_filtered": [],
        "final_output": None
    }

# --- Out-of-Scope Check Node ---


@node_logger("out_of_scope_check", input_keys=["user_query"], output_keys=["out_of_scope_result"])
def out_of_scope_check_node(state):
    # Get the detect_out_of_scope_query tool
    tools = get_tools()
    detect_out_of_scope_query = None
    for tool in tools:
        if hasattr(tool, 'name') and tool.name == 'detect_out_of_scope_query':
            detect_out_of_scope_query = tool
            break
    if detect_out_of_scope_query is None:
        state["error"] = "detect_out_of_scope_query tool not found"
        return state

    # Call the tool
    result = detect_out_of_scope_query.invoke({"query_description": state["user_query"]})
    state["out_of_scope_result"] = result
    return state

# --- Quality Control Node (QC) ---


@node_logger("quality_control", input_keys=["user_query", "out_of_scope_result", "keywords"], output_keys=["qc_decision", "qc_tool_result", "keywords", "has_filter_instructions"])
def quality_control_node(state):
    tools = get_tools()
    tool_map = {getattr(tool, 'name', None): tool for tool in tools}
    qc_decision = "accept"  # Default
    qc_tool_result = None
    try:
        result = state.get("out_of_scope_result")
        user_query = state.get("user_query", "")
        keywords = state.get("keywords", [])

        # Extract keywords from out_of_scope_result if available
        if result:
            try:
                parsed = json.loads(result)
                if isinstance(parsed, dict):
                    if parsed.get("status") == "out_of_scope":
                        qc_decision = "out_of_scope"
                        qc_tool_result = result
                        state["qc_decision"] = qc_decision
                        state["qc_tool_result"] = qc_tool_result
                        # Don't return here - let the LLM QC decision process continue
                    elif parsed.get("status") == "valid" and "keywords" in parsed:
                        keywords = parsed["keywords"]
                        state["keywords"] = keywords
            except Exception as e:
                logger.error(f"Error parsing out_of_scope_result: {e}")

        # Update keywords in state
        state["keywords"] = keywords

        # Use LLM to intelligently detect filter instructions
        filter_detection_prompt = f"""
        You are an academic research assistant. Analyze the user query to determine if it contains filter instructions.

        Filter instructions include:
        - Date/time constraints: "after 2020", "before 2018", "published since 2022", "between 2019-2023"
        - Citation constraints: "highly cited", "more than 50 citations", "well-cited papers"
        - Author constraints: "by author X", "from researcher Y", "authored by"
        - Journal/conference constraints: "published in Nature", "from conference X", "in journal Y"
        - Impact constraints: "high impact", "top journals", "prestigious venues"
        - Similarity constraints: "highly relevant", "closely related", "similar to"
        - Specific metrics: "fwci > 5", "citation percentile > 90", "impact factor > 10"

        User query: "{user_query}"

        Respond with ONLY a JSON object:
        {{
        "has_filter_instructions": true/false,
        "reason": "brief explanation of why"
        }}
        """

        try:
            filter_response = LLM.invoke(filter_detection_prompt)
            filter_result = json.loads(filter_response.content) if isinstance(filter_response.content, str) else filter_response.content

            # Handle potential list response
            if isinstance(filter_result, list) and len(filter_result) > 0:
                filter_result = filter_result[0]

            has_filter_instructions = False
            reason = "No reason provided"
            if isinstance(filter_result, dict):
                has_filter_instructions = filter_result.get("has_filter_instructions", False)
                reason = filter_result.get("reason", "No reason provided")

            state["has_filter_instructions"] = has_filter_instructions
            logger.info(f"Filter detection: {has_filter_instructions} - {reason}")

        except Exception as e:
            logger.error(f"Error in filter detection: {e}")
            state["has_filter_instructions"] = False

        # LLM-driven QC decision
        qc_prompt = f"""
        You are an academic research assistant. Given the following user query and keywords, decide which action to take:
        - If the query is valid and specific, respond with 'accept'.
        - If the query is vague, respond with 'reformulate'.
        - If the query is too broad, respond with 'narrow'.
        - If the query is too narrow, respond with 'broaden'.
        - If the query contains multiple topics, respond with 'split'.
        - If the query is not a valid research topic, respond with 'out_of_scope'.

        User query: "{user_query}"
        Keywords: {keywords}

        Respond with a JSON object:
        {{
        "qc_decision": "accept" | "reformulate" | "broaden" | "narrow" | "split" | "out_of_scope",
        "reason": "..."
        }}
        """
        qc_response = LLM.invoke(qc_prompt)
        qc_result = json.loads(qc_response.content) if isinstance(qc_response.content, str) else qc_response.content
        # If qc_result is a list, use the first element if possible
        if isinstance(qc_result, list) and len(qc_result) > 0:
            qc_result = qc_result[0]
        if not isinstance(qc_result, dict):
            qc_result = {}
        qc_decision = qc_result.get("qc_decision", "accept")
        state["qc_decision"] = qc_decision
        state["qc_decision_reason"] = qc_result.get("reason", "")
        # Call the appropriate tool if needed
        if qc_decision == "reformulate":
            tool = tool_map.get("reformulate_query")
            if tool:
                qc_tool_result = tool.invoke({"query_description": user_query, "keywords": keywords})
                try:
                    tool_result = json.loads(qc_tool_result) if isinstance(qc_tool_result, str) else qc_tool_result
                    if "result" in tool_result and "refined_keywords" in tool_result["result"]:
                        state["keywords"] = tool_result["result"]["refined_keywords"]
                except Exception as e:
                    logger.error(f"Error in ...: {e}")
        elif qc_decision == "split":
            tool = tool_map.get("multi_step_reasoning")
            if tool:
                qc_tool_result = tool.invoke({"query_description": user_query})
        elif qc_decision == "broaden":
            tool = tool_map.get("retry_broaden")
            if tool:
                qc_tool_result = tool.invoke({"query_description": user_query, "keywords": keywords})
                try:
                    tool_result = json.loads(qc_tool_result) if isinstance(qc_tool_result, str) else qc_tool_result
                    if "broadened_keywords" in tool_result:
                        state["keywords"] = tool_result["broadened_keywords"]
                except Exception as e:
                    logger.error(f"Error in ...: {e}")
        elif qc_decision == "narrow":
            tool = tool_map.get("narrow_query")
            if tool:
                qc_tool_result = tool.invoke({"query_description": user_query, "keywords": keywords})
                try:
                    tool_result = json.loads(qc_tool_result) if isinstance(qc_tool_result, str) else qc_tool_result
                    if "narrowed_keywords" in tool_result:
                        state["keywords"] = tool_result["narrowed_keywords"]
                except Exception as e:
                    logger.error(f"Error in ...: {e}")
        elif qc_decision == "accept":
            tool = tool_map.get("accept")
            if tool:
                qc_tool_result = tool.invoke({"confirmation": "yes"})
        state["qc_tool_result"] = qc_tool_result
    except Exception as e:
        state["error"] = f"QC node error: {e}"
        qc_decision = "error"
    return state

# --- Out-of-Scope Handler Node ---


@node_logger("out_of_scope_handler", input_keys=["user_query", "qc_decision_reason"], output_keys=["out_of_scope_message", "requires_user_input"])
def out_of_scope_handler_node(state):
    """
    Handle out-of-scope queries by providing explanation and requesting new input.
    """
    user_query = state.get("user_query", "")
    qc_decision_reason = state.get("qc_decision_reason", "The query was determined to be out of scope.")

    # Generate explanation for why the query was rejected
    explanation_prompt = f"""
    The user query "{user_query}" was determined to be out of scope for academic paper recommendations.

    Reason: {qc_decision_reason}

    Provide a helpful explanation to the user about why their query is out of scope and suggest how they could rephrase it to get relevant academic paper recommendations.

    Focus on:
    1. Why the current query doesn't work for academic paper search
    2. What types of queries work well (research topics, academic fields, specific technologies)
    3. Examples of better ways to phrase their request

    Keep the explanation friendly and constructive.
    """

    # Generate a short summary explanation
    short_explanation_prompt = f"""
    The user query "{user_query}" was determined to be out of scope for academic paper recommendations.
    Reason: {qc_decision_reason}

    In 1-2 short sentences, summarize for the user why their query is out of scope and what they should do instead. Be concise and direct (e.g., 'Your query is too general. Please specify a research topic or field.').
    """

    try:
        explanation_response = LLM.invoke(explanation_prompt)
        explanation = explanation_response.content if hasattr(explanation_response, 'content') else str(explanation_response)

        short_explanation_response = LLM.invoke(short_explanation_prompt)
        short_explanation = short_explanation_response.content if hasattr(short_explanation_response, 'content') else str(short_explanation_response)

        # Create the out-of-scope message
        out_of_scope_message = {
            "type": "out_of_scope",
            "original_query": user_query,
            "short_explanation": short_explanation,
            "explanation": explanation,
            "suggestion": "Please provide a new query focused on academic research topics, technologies, or fields of study."
        }

        state["out_of_scope_message"] = out_of_scope_message
        state["requires_user_input"] = True

        logger.info(f"Out-of-scope query handled. Original query: '{user_query}'")

    except Exception as e:
        logger.error(f"Error in out_of_scope_handler_node: {e}")
        state["error"] = f"Error handling out-of-scope query: {e}"
        state["out_of_scope_message"] = {
            "type": "out_of_scope",
            "original_query": user_query,
            "short_explanation": "Your query is out of scope. Please specify a research topic or field.",
            "explanation": "The query was determined to be out of scope for academic paper recommendations. Please try a different query focused on research topics or academic fields.",
            "suggestion": "Please provide a new query focused on academic research topics, technologies, or fields of study."
        }
        state["requires_user_input"] = True

    return state


def expand_subqueries_node(state):
    """
    If the QC decision was 'split', extract subqueries and keywords from the multi_step_reasoning tool result.
    """
    qc_tool_result = state.get("qc_tool_result")
    subqueries = []
    if qc_tool_result:
        try:
            parsed = json.loads(qc_tool_result) if isinstance(qc_tool_result, str) else qc_tool_result
            if parsed.get("status") == "success" and "subqueries" in parsed:
                for sub in parsed["subqueries"]:
                    subqueries.append({
                        "description": sub.get("sub_description", ""),
                        "keywords": sub.get("keywords", [])
                    })
        except Exception as e:
            logger.error(f"Error parsing subqueries: {e}")
    state["subqueries"] = subqueries
    logger.info(f"Extracted {len(subqueries)} subqueries from split.")
    return state

# --- Update Papers Node ---


@node_logger("update_papers", input_keys=["user_query", "qc_decision", "qc_tool_result"], output_keys=["update_papers_result"])
def update_papers_node(state):
    tools = get_tools()
    tool_map = {getattr(tool, 'name', None): tool for tool in tools}
    update_papers_tool = tool_map.get("update_papers")
    update_papers_result = None
    all_papers = []
    try:
        # If subqueries exist, process each
        subqueries = state.get("subqueries", [])
        if subqueries:
            update_results = []
            for sub in subqueries:
                keywords = sub.get("keywords", [])
                if update_papers_tool:
                    result = update_papers_tool.invoke({"queries": keywords})
                    update_results.append(result)
                    # Optionally, collect papers from result if available
                    # all_papers.extend(parse_papers_from_result(result))
            update_papers_result = update_results
        else:
            # Fallback: single query as before
            queries = []
            if state.get("qc_decision") == "reformulate" and state.get("qc_tool_result"):
                try:
                    qc_result = json.loads(state["qc_tool_result"])
                    if "result" in qc_result and "refined_keywords" in qc_result["result"]:
                        queries = qc_result["result"]["refined_keywords"]
                    elif "reformulated_description" in qc_result:
                        queries = [qc_result["reformulated_description"]]
                except Exception:
                    queries = [state.get("user_query", "")]
            elif state.get("qc_decision") == "split" and state.get("qc_tool_result"):
                # Should not happen, handled above
                queries = [state.get("user_query", "")]
            else:
                queries = [state.get("user_query", "")]
            if update_papers_tool:
                update_papers_result = update_papers_tool.invoke({"queries": queries})
        state["update_papers_result"] = update_papers_result
        state["all_papers"] = all_papers
    except Exception as e:
        state["error"] = f"Update papers node error: {e}"
    return state

# --- Get Best Papers Node ---


@node_logger("get_best_papers", input_keys=["user_query", "keywords", "has_filter_instructions"], output_keys=["papers_raw"])
def get_best_papers_node(state):
    tools = get_tools()
    tool_map = {getattr(tool, 'name', None): tool for tool in tools}
    get_best_papers_tool = tool_map.get("get_best_papers")
    papers_raw = []
    try:
        # Prefer keywords if available, else use user_query
        user_profile = None
        if state.get("keywords"):
            user_profile = ", ".join(state["keywords"])
        else:
            user_profile = state.get("user_query", "")

        # Determine retrieval count based on filter instructions
        has_filter_instructions = state.get("has_filter_instructions", False)
        retrieval_count = 50 if has_filter_instructions else 10  # More papers if filtering will be applied

        if get_best_papers_tool:
            # Use count parameter based on filter instructions
            papers_raw = get_best_papers_tool.invoke({
                "user_profile": user_profile,
                "count": retrieval_count
            })

            logger.info(f"Retrieved {len(papers_raw)} papers (filter instructions: {has_filter_instructions}, requested: {retrieval_count})")

        state["papers_raw"] = papers_raw
    except Exception as e:
        state["error"] = f"Get best papers node error: {e}"
    return state


# --- Filter Papers Node ---
@node_logger("filter_papers", input_keys=["user_query", "papers_raw", "has_filter_instructions"], output_keys=["papers_filtered"])
def filter_papers_node(state):
    tools = get_tools()
    tool_map = {getattr(tool, 'name', None): tool for tool in tools}
    filter_tool = tool_map.get("filter_papers_by_nl_criteria")
    papers_filtered = []

    try:
        user_query = state.get("user_query", "")
        papers_raw = state.get("papers_raw", [])
        has_filter_instructions = state.get("has_filter_instructions", False)

        if not has_filter_instructions or not papers_raw:
            # No filtering needed or no papers to filter
            papers_filtered = papers_raw
            logger.info(f"No filtering applied. Papers count: {len(papers_filtered)}")
            state["applied_filter_criteria"] = {}
        else:
            # Use the filter_papers_by_nl_criteria tool to get both filtered papers and the filter spec
            filter_extraction_nl = user_query
            if filter_tool:
                filter_result = filter_tool.invoke({
                    "papers": papers_raw,
                    "criteria_nl": filter_extraction_nl
                })
                try:
                    filter_result_parsed = json.loads(filter_result)
                    if filter_result_parsed.get("status") == "success":
                        papers_filtered = filter_result_parsed.get("kept_papers", [])
                        logger.info(f"Applied filter. Kept {len(papers_filtered)} out of {len(papers_raw)} papers")
                        # Store the filter spec (filters) in the state for later use
                        state["applied_filter_criteria"] = filter_result_parsed.get("filters", {})
                    else:
                        logger.warning(f"Filter failed: {filter_result_parsed.get('message', 'Unknown error')}")
                        papers_filtered = papers_raw
                        state["applied_filter_criteria"] = {}
                except Exception as e:
                    logger.error(f"Error parsing filter result: {e}")
                    papers_filtered = papers_raw
                    state["applied_filter_criteria"] = {}
            else:
                logger.warning("Filter tool not found")
                papers_filtered = papers_raw
                state["applied_filter_criteria"] = {}

        state["papers_filtered"] = papers_filtered

    except Exception as e:
        state["error"] = f"Filter papers node error: {e}"
        state["papers_filtered"] = state.get("papers_raw", [])
        state["applied_filter_criteria"] = {}

    return state

# --- Smart No-Results Handler Node ---


@node_logger("no_results_handler", input_keys=["user_query", "papers_raw", "papers_filtered"], output_keys=["no_results_message"])
def no_results_handler_node(state):
    """
    If no papers are found after filtering, generate a smart explanation using the LLM.
    Finds the closest value for each filterable metric (year, citations, impact factor, etc.) using the find_closest_paper_metrics tool.
    """
    user_query = state.get("user_query", "")
    papers_raw = state.get("papers_raw", [])
    # papers_filtered is used implicitly - we know it's empty when this node is called
    filter_criteria_json = state.get("applied_filter_criteria", {})

    # Use the tool to get closest values and directions
    tools = get_tools()
    tool_map = {getattr(tool, 'name', None): tool for tool in tools}
    closest_tool = tool_map.get("find_closest_paper_metrics")
    closest_values = {}
    if closest_tool:
        try:
            closest_result = closest_tool.invoke({
                "papers": papers_raw,
                "filter_spec": filter_criteria_json
            })
            closest_values = json.loads(closest_result)
        except Exception:
            closest_values = {}

    # Compose a prompt for the LLM
    smart_explanation_prompt = f"""
    The user searched for academic papers with the following query:
    "{user_query}"
    After applying all filters, no papers were found.
    The filter criteria were: {json.dumps(filter_criteria_json)}
    The detailed analysis of available values: {json.dumps(closest_values)}

    IMPORTANT: Use the EXACT values provided above in your explanation. Do not make up generic values.

    Please explain to the user in a friendly, concise way:
    1. That no papers matched their combined filters (this is not an error)
    2. For each filter individually:
       - State the best available value for that metric
       - Whether any papers would match that filter alone
       - If papers would match individually, mention this as a potential adjustment
    3. Suggest specific adjustments based on the actual values:
       - If individual filters would work, suggest trying them separately
       - If values are close to thresholds, suggest lowering them slightly
       - If best available values are much better than thresholds, highlight this

    Be specific and use the actual numbers from the analysis data.
    """
    try:
        llm_response = LLM.invoke(smart_explanation_prompt)
        explanation = llm_response.content if hasattr(llm_response, 'content') else str(llm_response)
        state["no_results_message"] = {
            "type": "no_results",
            "explanation": explanation,
            "closest_values": closest_values,
            "filter_criteria": filter_criteria_json
        }
    except Exception:
        state["no_results_message"] = {
            "type": "no_results",
            "explanation": "No papers matched your filter. Please try broadening your search.",
            "closest_values": closest_values,
            "filter_criteria": filter_criteria_json
        }
    return state


def run_stategraph_agent(user_query: str):
    """
    Run the complete Stategraph agent workflow and return the final results.

    Args:
        user_query (str): The user's research query

    Returns:
        dict: Final state with papers and results
    """
    # Initialize state
    state = {"user_query": user_query}

    # Run the complete workflow
    state = input_node(state)
    state = out_of_scope_check_node(state)

    # Extract keywords from out_of_scope_result if available
    out_of_scope_result = state.get("out_of_scope_result")
    if out_of_scope_result:
        try:
            parsed = json.loads(out_of_scope_result)
            if parsed.get("status") == "valid" and "keywords" in parsed:
                state["keywords"] = parsed["keywords"]
        except Exception:
            logger.error("Error parsing out_of_scope_result")

    state = quality_control_node(state)
    # Branch: if split, expand subqueries before updating papers
    if state.get("qc_decision") == "split":
        state = expand_subqueries_node(state)
    state = update_papers_node(state)
    state = get_best_papers_node(state)
    state = filter_papers_node(state)

    return state


def trigger_stategraph_agent_show_thoughts(user_message: str):
    """
    A generator that yields each step of the Stategraph agent's thought process.
    This replaces the old React agent's trigger_agent_show_thoughts function.
    """
    try:
        # Initialize state
        state = {"user_query": user_message}

        # Step 1: Input node
        yield {"thought": "Processing user input...", "is_final": False, "final_content": None}
        state = input_node(state)

        # Step 2: Out-of-scope check
        yield {"thought": "Checking if query is within scope...", "is_final": False, "final_content": None}
        state = out_of_scope_check_node(state)

        # Extract keywords from out_of_scope_result if available
        out_of_scope_result = state.get("out_of_scope_result")
        if out_of_scope_result:
            try:
                parsed = json.loads(out_of_scope_result)
                if parsed.get("status") == "valid" and "keywords" in parsed:
                    state["keywords"] = parsed["keywords"]
                    yield {"thought": f"Extracted keywords: {state['keywords']}", "is_final": False, "final_content": None}
            except Exception as e:
                logger.error(f"Error parsing out_of_scope_result: {e}")

        # Step 3: Quality control
        yield {"thought": "Performing quality control and filter detection...", "is_final": False, "final_content": None}
        state = quality_control_node(state)

        # Check if query is out of scope
        qc_decision = state.get("qc_decision", "accept")
        if qc_decision == "out_of_scope":
            yield {"thought": "Query determined to be out of scope. Generating explanation...", "is_final": False, "final_content": None}
            state = out_of_scope_handler_node(state)

            # Return out-of-scope message
            out_of_scope_message = state.get("out_of_scope_message", {})
            yield {
                "thought": "Query rejected as out of scope. Please provide a new query.",
                "is_final": True,
                "final_content": json.dumps({
                    "type": "out_of_scope",
                    "message": out_of_scope_message,
                    "requires_user_input": True
                })
            }
            return

        # If split, expand subqueries
        if qc_decision == "split":
            yield {"thought": "Splitting query into subqueries...", "is_final": False, "final_content": None}
            state = expand_subqueries_node(state)

        # Step 4: Update papers
        yield {"thought": "Updating paper database with latest research...", "is_final": False, "final_content": None}
        state = update_papers_node(state)

        # Step 5: Get best papers
        yield {"thought": "Retrieving most relevant papers...", "is_final": False, "final_content": None}
        state = get_best_papers_node(state)

        # Step 6: Filter papers
        yield {"thought": "Applying filters to refine results...", "is_final": False, "final_content": None}
        state = filter_papers_node(state)

        # Check for no results
        if not state.get("papers_filtered"):
            yield {"thought": "No papers found after filtering. Generating smart no-results explanation...", "is_final": False, "final_content": None}
            state = no_results_handler_node(state)
            no_results_message = state.get("no_results_message", {})
            yield {
                "thought": "No papers found. Please try broadening your search or adjusting your filter.",
                "is_final": True,
                "final_content": json.dumps({
                    "type": "no_results",
                    "message": no_results_message,
                    "requires_user_input": True
                })
            }
            return

        # Prepare final response
        papers_filtered = state.get("papers_filtered", [])
        final_recommendations = []

        for paper in papers_filtered:
            final_recommendations.append({
                "title": paper.get("title", "N/A"),
                "link": paper.get("landing_page_url", paper.get("pdf_url", "N/A")),
                "description": f"Relevant paper on {paper.get('title', 'this topic')} with {paper.get('cited_by_count', 0)} citations."
            })

        final_response = {"papers": final_recommendations}

        yield {"thought": "Finalizing recommendations...", "is_final": True, "final_content": json.dumps(final_response)}

    except Exception as e:
        logger.error(f"Error in Stategraph agent: {e}")
        yield {"thought": f"An error occurred: {str(e)}", "is_final": True, "final_content": None}


if __name__ == "__main__":
    # Example usage (stepwise test)
    queries = [
        "I am looking for papers in the field of machine learning in healthcare published after 2018.",  # accept
        # "Hello world",  # out_of_scope
        # "Biology",  # reformulate (too short/vague)
        # "Deep learning for genomics and climate change adaptation",  # split (multi-topic)
        # "Quantum entanglement in nitrogen-vacancy centers at 4K in diamond nanostructures",  # broaden (very narrow)
        # "Recent advances in science and technology"  # narrow (too broad)
    ]
    for user_query in queries:
        print(f"\n=== Testing query: '{user_query}' ===")
        # Step 1: Input node
        state = {"user_query": user_query}
        state = input_node(state)
        print("After input_node:", state)
        # Step 2: Out-of-scope check node
        state = out_of_scope_check_node(state)
        print("After out_of_scope_check_node:", state)
        out_of_scope_result = state.get("out_of_scope_result")
        if out_of_scope_result:
            try:
                parsed = json.loads(out_of_scope_result)
                if parsed.get("status") == "valid" and "keywords" in parsed:
                    state["keywords"] = parsed["keywords"]
            except Exception:
                # Optionally log or handle parsing errors
                logger.error("Error parsing out_of_scope_result")
                pass
        print("After out_of_scope_check_node:", state)
        # Step 3: Quality control node
        state = quality_control_node(state)
        print("After quality_control_node:", state)
        # Step 4: Update papers node
        state = update_papers_node(state)
        print("After update_papers_node:", state)
        # Step 5: Get best papers node
        state = get_best_papers_node(state)
        print("After get_best_papers_node:", state)
        # Step 6: Filter papers node
        state = filter_papers_node(state)
        print("After filter_papers_node:", state)
