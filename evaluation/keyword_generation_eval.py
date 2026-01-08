import asyncio
import os
import sys

import pandas as pd

# Set CHROMA_HOST to localhost for local execution
os.environ["CHROMA_HOST"] = "localhost"

# Setup paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pydantic_graph import GraphRunContext

from llm.LLMDefinition import set_default_llm, get_available_models
from llm.nodes.input import Input
from llm.nodes.out_of_scope_check import OutOfScopeCheck
from llm.nodes.quality_control import QualityControl
from llm.state import AgentState
from llm_pydantic.tooling.tooling_mock import AgentDeps
from paper_handling.paper_handler import fetch_works_multiple_queries

# --- Configuration ---
NUMBER_OF_PAPERS_TO_TEST = 50
MODELS_TO_TEST = get_available_models()
SEARCH_RESULTS_TO_CHECK_LIST = [25, 50, 100]
RESULTS_FILENAME = "keyword_generation_results.txt"


def _run_node_sync(node, state: AgentState, deps: AgentDeps) -> AgentState:
    """Helper to run a single async node synchronously for scripts/tests."""

    ctx = GraphRunContext(state=state, deps=deps)
    asyncio.run(node.run(ctx))
    return ctx.state


def input_node(state: AgentState, deps: AgentDeps) -> AgentState:
    return _run_node_sync(Input(user_message=state.user_query), state, deps)


def out_of_scope_check_node(state: AgentState, deps: AgentDeps) -> AgentState:
    return _run_node_sync(OutOfScopeCheck(), state, deps)


def quality_control_node(state: AgentState, deps: AgentDeps) -> AgentState:
    return _run_node_sync(QualityControl(), state, deps)


def get_papers_from_csv(num_papers):
    """
    Reads the paper_pairs.csv file and returns a list of unique papers.
    Args:
        num_papers (int): The number of papers to retrieve.
    Returns:
        list: A list of unique papers.
    """
    df = pd.read_csv("evaluation/data/paper_pairs.csv")

    papers = {}
    for _, row in df.iterrows():
        # Add first paper
        paper1_id = row["openalexid_first"]
        if paper1_id not in papers:
            papers[paper1_id] = {
                "id": paper1_id,
                "title": row["title_first"],
                "abstract": row["abstract_first"],
            }
        # Add second paper
        paper2_id = row["openalexid_second"]
        if paper2_id not in papers:
            papers[paper2_id] = {
                "id": paper2_id,
                "title": row["title_second"],
                "abstract": row["abstract_second"],
            }

    unique_papers = list(papers.values())
    return unique_papers[:num_papers]


def run_single_evaluation_run(paper, model_name, search_results_count) -> tuple:
    """
    Performs a single round-trip evaluation run.
    Args:
        paper (dict): The paper to evaluate.
        model_name (str): The name of the model to use.
        search_results_count (int): The number of search results to return.
    Returns a tuple: (status, found).
    - ("SUCCESS", True) if the run was valid and paper was found.
    - ("SUCCESS", False) if the run was valid and paper was not found.
    - ("ERROR", None) if the run was invalid due to an error.
    """
    try:
        set_default_llm(model_name)

        paper_id = paper["id"]
        paper_title = paper.get("title", "Unknown Title")
        paper_abstract = paper.get("abstract", "")

        # Construct query text from title and abstract
        query_text = f"Title: {paper_title}. Abstract: {paper_abstract}"

    except Exception as e:
        print(f"ERROR: An error occurred in setting up the paper: {e}")
        return "ERROR", None

    try:
        deps = AgentDeps()
        state = AgentState(user_query=query_text)
        state = input_node(state, deps)
        state = out_of_scope_check_node(state, deps)
        state = quality_control_node(state, deps)

        if state.error:
            print(
                f"WARNING: Keyword generation pipeline returned an error: {state.error}"
            )
            return "ERROR", None

        generated_keywords = state.keywords or []
        if not generated_keywords:
            print(
                "WARNING: Keyword generation resulted in an empty list. Aborting run."
            )
            return "ERROR", None

    except Exception as e:
        print(f"ERROR: An error occurred in Step 2 (generating keywords): {e}")
        return "ERROR", None

    try:
        search_results, status = fetch_works_multiple_queries(
            queries=generated_keywords, per_page=search_results_count
        )
        if status != "SUCCESS" and not search_results:
            print(
                "WARNING: Search with generated keywords failed or returned no results."
            )
            return "ERROR", None

    except Exception as e:
        print(f"ERROR: An error occurred in Step 3 (searching with keywords): {e}")
        return "ERROR", None

    found = False
    for result_paper in search_results:
        if result_paper.get("id") == paper_id:
            found = True
            break

    return "SUCCESS", found


def main():
    """Main function to orchestrate the evaluation."""
    print("Starting evaluation...")

    papers = get_papers_from_csv(NUMBER_OF_PAPERS_TO_TEST)
    if not papers:
        print("No papers found in the CSV. Aborting.")
        return

    results = {}

    for model in MODELS_TO_TEST:
        for search_count in SEARCH_RESULTS_TO_CHECK_LIST:
            print(f"\n--- Testing Model: {model}, Search Results: {search_count} ---")

            success_count = 0
            valid_runs = 0

            for i, paper in enumerate(papers):
                print(f"\n--- Running Evaluation: {i + 1}/{len(papers)} ---")
                try:
                    status, was_found = run_single_evaluation_run(
                        paper, model, search_count
                    )
                    if status == "SUCCESS":
                        valid_runs += 1
                        if was_found:
                            success_count += 1
                            print("Result: SUCCESS - The initial paper was found.")
                        else:
                            print("Result: FAILURE - The initial paper was NOT found.")
                    else:
                        print(
                            "Result: ERROR - The run was invalid and will be skipped."
                        )
                except Exception as e:
                    print(f"ERROR: A critical error occurred during run {i + 1}: {e}")

            results[(model, search_count)] = (success_count, valid_runs)

    print("\n--- Evaluation Complete ---")
    print("\n--- Results Summary ---")

    with open(RESULTS_FILENAME, "w") as f:
        f.write("--- Evaluation Complete ---\n")
        f.write("--- Results Summary ---\n")
        for (model, search_count), (success, total) in results.items():
            if total > 0:
                success_rate = (success / total) * 100
                f.write(
                    f"Model: {model}, Search Results: {search_count} -> Success Rate: {success}/{total} ({success_rate:.2f}%)\n"
                )
            else:
                f.write(
                    f"Model: {model}, Search Results: {search_count} -> No valid runs.\n"
                )

    print(f"Results saved to {RESULTS_FILENAME}")


if __name__ == "__main__":
    main()
