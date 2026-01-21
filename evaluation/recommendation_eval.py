import asyncio
import os
import sys
import pandas as pd
from sklearn.metrics import precision_score, recall_score, accuracy_score
import numpy as np
import uuid
import json
import concurrent.futures

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
from llm.tools.tooling_mock import AgentDeps
from paper_handling.paper_handler import fetch_works_multiple_queries
from llm.Embeddings import embed_paper_text
from chroma_db.chroma_vector_db import CHROMA_HOST, CHROMA_PORT

import chromadb

# --- Configuration ---
MODELS_TO_TEST = ["gpt-5-nano"]
SEARCH_RESULTS_TO_CHECK_LIST = [100]
EVALUATION_DATASET = "evaluation/data/paper_pairs.csv"
RESULTS_FILENAME = "recommendation_evaluation_results.txt"
RESULTS_JSONL_FILENAME = "recommendation_evaluation_results.jsonl"
EVAL_SET_SIZE = 100
MAX_WORKERS = 5


async def _embed_texts(texts: list[str]) -> list[list[float]]:
    return await asyncio.gather(*(embed_paper_text(text) for text in texts))


def _run_node_sync(node, state: AgentState, deps: AgentDeps) -> AgentState:
    """Run a single async node synchronously for evaluation scripts."""

    ctx = GraphRunContext(state=state, deps=deps)
    asyncio.run(node.run(ctx))
    return ctx.state


def input_node(state: AgentState, deps: AgentDeps) -> AgentState:
    return _run_node_sync(Input(user_message=state.user_query), state, deps)


def out_of_scope_check_node(state: AgentState, deps: AgentDeps) -> AgentState:
    return _run_node_sync(OutOfScopeCheck(), state, deps)


def quality_control_node(state: AgentState, deps: AgentDeps) -> AgentState:
    return _run_node_sync(QualityControl(), state, deps)


def calculate_mrr(ranks):
    """Calculates the Mean Reciprocal Rank."""
    if not ranks:
        return 0.0
    reciprocal_ranks = [1.0 / rank for rank in ranks if rank > 0]
    if not reciprocal_ranks:
        return 0.0
    return np.mean(reciprocal_ranks)


def run_full_pipeline_evaluation(row, model_name, search_results_count) -> tuple:
    """
    Performs a single round-trip evaluation of the full recommendation pipeline.
    """
    try:
        set_default_llm(model_name)

        paper2_title = row["title_second"]
        paper2_abstract = row["abstract_second"]
        paper1_id = row["openalexid_first"]

        query_text = f"Title: {paper2_title}. Abstract: {paper2_abstract}"

    except Exception as e:
        print(f"ERROR setting up paper: {e}")
        return "ERROR", None, None

    # 1. Keyword Generation using the correct agent flow
    try:
        deps = AgentDeps()
        state = AgentState(user_query=query_text)
        state = input_node(state, deps)
        state = out_of_scope_check_node(state, deps)
        state = quality_control_node(state, deps)

        if state.error:
            print(f"WARNING: Keyword pipeline error: {state.error}")
            return "ERROR", None, None

        generated_keywords = state.keywords or []
        if not generated_keywords:
            print("WARNING: No keywords generated. Aborting run.")
            return "ERROR", None, None
    except Exception as e:
        print(f"ERROR in keyword generation: {e}")
        return "ERROR", None, None

    # 2. Fetch Candidate Papers
    try:
        candidate_papers, status = fetch_works_multiple_queries(
            queries=generated_keywords, per_page=search_results_count
        )
        if not candidate_papers:
            print("WARNING: Keyword search failed or returned no results.")
            return "ERROR", None, None

        # De-duplicate candidate papers based on their ID
        unique_papers = {}
        for paper in candidate_papers:
            paper_id = paper.get("id")
            if paper_id and paper_id not in unique_papers:
                unique_papers[paper_id] = paper
        candidate_papers = list(unique_papers.values())

    except Exception as e:
        print(f"ERROR fetching and de-duplicating candidate papers: {e}")
        return "ERROR", None, None

    # 3. Embeddings and In-Memory ChromaDB evaluation
    temp_collection_name = f"eval_{uuid.uuid4().hex}"
    chroma_client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
    prediction = 0
    rank = 0

    try:
        temp_collection = chroma_client.create_collection(name=temp_collection_name)

        paper_texts = [
            f"{p.get('title', '')} {p.get('abstract', '')}" for p in candidate_papers
        ]
        if not paper_texts:
            print("WARNING: No paper texts to embed. Aborting run.")
            return "ERROR", None, None

        embeddings = asyncio.run(_embed_texts(paper_texts))
        paper_ids = [p.get("id") for p in candidate_papers]

        valid_indices = [
            i
            for i, pid in enumerate(paper_ids)
            if pid is not None and embeddings[i] is not None
        ]
        if not valid_indices:
            print(
                "WARNING: No valid papers after filtering for IDs and embeddings. Aborting run."
            )
            return "ERROR", None, None

        temp_collection.add(
            ids=[paper_ids[i] for i in valid_indices],
            embeddings=[embeddings[i] for i in valid_indices],
            documents=[paper_texts[i] for i in valid_indices],
        )

        query_embedding = asyncio.run(embed_paper_text(query_text))
        if query_embedding is None:
            print("WARNING: Could not generate embedding for query. Aborting run.")
            return "ERROR", None, None

        results = temp_collection.query(
            query_embeddings=[query_embedding],
            n_results=search_results_count,
            include=["documents"],
        )

        ranked_ids = results.get("ids", [[]])[0]
        if paper1_id in ranked_ids:
            rank = ranked_ids.index(paper1_id) + 1
            prediction = 1

        return "SUCCESS", prediction, rank

    except Exception as e:
        print(f"ERROR during ChromaDB interaction/embedding generation: {e}")
        return "ERROR", None, None
    finally:
        try:
            client_for_cleanup = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
            if temp_collection_name in [
                c.name for c in client_for_cleanup.list_collections()
            ]:
                client_for_cleanup.delete_collection(name=temp_collection_name)
        except Exception as e:
            print(f"ERROR during cleanup of temporary ChromaDB collection: {e}")


def main():
    """Main function to orchestrate the recommendation system evaluation."""
    print("Starting full pipeline recommendation system evaluation...")

    try:
        df = pd.read_csv(EVALUATION_DATASET)
        if EVAL_SET_SIZE > 0:
            df = df.head(EVAL_SET_SIZE)
    except FileNotFoundError:
        print(f"Error: Dataset '{EVALUATION_DATASET}' not found.")
        return

    available_models = get_available_models()
    models_to_run = [m for m in MODELS_TO_TEST if m in available_models]
    if not models_to_run:
        print(
            f"Models {MODELS_TO_TEST} not found in available models: {available_models}."
        )
        return

    # Prepare list of tasks
    tasks = []
    for model in models_to_run:
        for search_count in SEARCH_RESULTS_TO_CHECK_LIST:
            for i, row in df.iterrows():
                tasks.append(
                    {
                        "row": row,
                        "model": model,
                        "search_count": search_count,
                        "index": i,
                    }
                )

    print(f"Running {len(tasks)} evaluations with {MAX_WORKERS} workers...")

    # Ensure the file exists or create it (clear it if starting fresh run)
    # Note: If you want to Append to existing run, remove the 'w' open here.
    # But usually a fresh run implies a fresh file or we might want to keep history.
    # For now, let's just ensure we can append.
    if not os.path.exists(RESULTS_JSONL_FILENAME):
        with open(RESULTS_JSONL_FILENAME, "w") as f:
            pass

    results_list = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all tasks
        future_to_task = {
            executor.submit(
                run_full_pipeline_evaluation,
                task["row"],
                task["model"],
                task["search_count"],
            ): task
            for task in tasks
        }

        for future in concurrent.futures.as_completed(future_to_task):
            task = future_to_task[future]
            try:
                status, prediction, rank = future.result()

                result_entry = {
                    "model": task["model"],
                    "search_count": task["search_count"],
                    "paper_pair_index": task["index"],
                    "ground_truth": int(task["row"]["label"]),
                    "prediction": prediction,
                    "rank": rank,
                    "status": status,
                }

                # Incremental Save
                with open(RESULTS_JSONL_FILENAME, "a") as f:
                    f.write(json.dumps(result_entry) + "\n")

                results_list.append(result_entry)

                if status == "SUCCESS":
                    if prediction == 1:
                        print(
                            f"Task {task['index']} ({task['model']}): Recommended (Rank: {rank})"
                        )
                    else:
                        print(
                            f"Task {task['index']} ({task['model']}): Not Recommended"
                        )
                else:
                    print(f"Task {task['index']} ({task['model']}): ERROR")

            except Exception as e:
                print(f"Task {task['index']} generated an exception: {e}")

    # Calculate and print summary stats
    print("\n--- Evaluation Complete ---")
    print(f"Detailed results saved to {RESULTS_JSONL_FILENAME}")

    # Simple summary calculation from results_list
    # Group by model and search_count
    summary_groups = {}
    for res in results_list:
        if res["status"] != "SUCCESS":
            continue
        key = (res["model"], res["search_count"])
        if key not in summary_groups:
            summary_groups[key] = {"predictions": [], "ground_truths": [], "ranks": []}

        summary_groups[key]["predictions"].append(res["prediction"])
        summary_groups[key]["ground_truths"].append(res["ground_truth"])
        if res["prediction"] == 1:
            summary_groups[key]["ranks"].append(res["rank"])
        else:
            summary_groups[key]["ranks"].append(0)

    print("\n--- Results Summary ---")
    with open(RESULTS_FILENAME, "w") as f:
        f.write("--- Full Recommendation Pipeline Evaluation ---\n\n")
        for (model, search_count), data in summary_groups.items():
            predictions = data["predictions"]
            ground_truths = data["ground_truths"]
            ranks = data["ranks"]

            if not ground_truths:
                continue

            precision = precision_score(ground_truths, predictions, zero_division=0)
            recall = recall_score(ground_truths, predictions, zero_division=0)
            accuracy = accuracy_score(ground_truths, predictions)
            mrr = calculate_mrr(ranks)

            summary_text = (
                f"Model: {model}, Candidate Pool Size: {search_count}\n"
                f"  Valid Runs: {len(ground_truths)}\n"
                f"  Successful Recommendations: {sum(1 for r in ranks if r > 0)}\n"
                f"  Precision: {precision:.4f}\n"
                f"  Recall: {recall:.4f}\n"
                f"  Accuracy: {accuracy:.4f}\n"
                f"  Mean Reciprocal Rank (MRR): {mrr:.4f}\n\n"
            )
            print(summary_text)
            f.write(summary_text)

    print(f"Results summary saved to {RESULTS_FILENAME}")


if __name__ == "__main__":
    main()
