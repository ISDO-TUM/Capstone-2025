from typing import List, Dict
from llama_index.core.schema import TextNode
from llama_index.retrievers.bm25 import BM25Retriever
from dotenv import load_dotenv
import Stemmer
import json
import os
from datetime import datetime

load_dotenv()


def evaluate_bm25_lexical_matching(
    user_prompt: str, recommended_papers: List[Dict], top_k: int = 10
):
    """
    Evaluate recommended papers using BM25 lexical matching via LlamaIndex and save results.

    Args:
        user_prompt (str): The user query or description of interest.
        recommended_papers (List[Dict]): List of papers with 'title' and 'abstract' keys.
        top_k (int): Number of top relevant papers to return.
    """
    # Prepare nodes
    nodes = []
    for paper in recommended_papers:
        title = paper.get("title", "")
        abstract = paper.get("abstract", "")
        content = f"{title}\n\n{abstract}".strip()
        if content:  # only add if not empty
            node = TextNode(
                text=content, metadata={"title": title, "abstract": abstract}
            )
            nodes.append(node)

    # BM25 Retriever
    bm25_retriever = BM25Retriever.from_defaults(
        nodes=nodes,
        similarity_top_k=len(nodes),
        stemmer=Stemmer.Stemmer("english"),
        language="english",
    )
    bm25_results = {
        node.node.node_id: node.score for node in bm25_retriever.retrieve(user_prompt)
    }

    # Prepare results
    results = []
    for node in nodes:
        kid = node.node_id
        bm25_score = bm25_results.get(kid, 0.0) or 0.0

        results.append(
            {
                "title": node.metadata["title"],
                "abstract": node.metadata["abstract"],
                "bm25_score": round(float(bm25_score), 3),
            }
        )

    # Sort results by BM25 score
    sorted_results = sorted(results, key=lambda x: x["bm25_score"], reverse=True)[
        :top_k
    ]

    # Calculate average score
    avg_bm25 = (
        sum(res["bm25_score"] for res in results) / len(results) if results else 0
    )

    # Prepare data for saving
    evaluation_data = {
        "timestamp": datetime.now().isoformat(),
        "user_prompt": user_prompt,
        "summary": {
            "total_papers": len(recommended_papers),
            "evaluated_papers": len(results),
            "top_k": top_k,
            "average_scores": {"bm25_score": round(avg_bm25, 3)},
        },
        "papers": [],
    }

    # Add individual paper results
    for i, res in enumerate(sorted_results, 1):
        paper_result = {
            "rank": i,
            "title": res["title"],
            "abstract": res["abstract"],
            "scores": {"bm25_score": res["bm25_score"]},
        }
        evaluation_data["papers"].append(paper_result)

    # Save to file
    evaluation_dir = "evaluation_results"
    if not os.path.exists(evaluation_dir):
        os.makedirs(evaluation_dir)

    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"bm25_evaluation_{timestamp_str}.json"
    filepath = os.path.join(evaluation_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(evaluation_data, f, indent=2, ensure_ascii=False)

    # Print summary
    print(f"BM25 Lexical Matching Results saved to: {filepath}")
    print(f"User Prompt: {user_prompt}")
    print(f"Total Papers: {len(recommended_papers)}")
    print(f"Evaluated Papers: {len(results)}")
    print("AVERAGE SCORES ACROSS ALL PAPERS:")
    print(f"Average BM25 Score: {avg_bm25:.3f}")
