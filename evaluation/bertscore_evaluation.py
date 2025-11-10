from typing import List, Dict
from bert_score import score
import math
import json
import os
from datetime import datetime


def compute_bertscore_similarity(
    user_prompt: str, paper_texts: List[str], model_type: str = "bert-base-uncased"
):
    """
    Compute BERTScore similarity between user prompt and paper texts.
    Returns precision, recall, and F1 scores.
    """
    P, R, F1 = score(
        paper_texts,
        [user_prompt] * len(paper_texts),
        model_type=model_type,
        lang="en",
        verbose=False,
    )
    return P.numpy().tolist(), R.numpy().tolist(), F1.numpy().tolist()


def precision_at_k(
    ranked_papers: List[Dict], bertscore_scores: Dict[str, float], k: int
) -> float:
    """
    Compute Precision@k using BERTScore F1 as relevance labels.
    """
    if k == 0:
        return 0.0

    relevance_threshold = 0.5
    relevant_count = 0

    for paper in ranked_papers[:k]:
        title = paper["title"]
        bertscore_f1 = bertscore_scores.get(title, 0.0)
        if bertscore_f1 > relevance_threshold:
            relevant_count += 1

    return relevant_count / k


def recall_at_k(
    ranked_papers: List[Dict], bertscore_scores: Dict[str, float], k: int
) -> float:
    """
    Compute Recall@k using BERTScore F1 as relevance labels.
    """
    relevance_threshold = 0.5

    # Count total relevant papers
    total_relevant = sum(
        1 for score in bertscore_scores.values() if score > relevance_threshold
    )

    if total_relevant == 0:
        return 0.0

    relevant_retrieved = 0
    for paper in ranked_papers[:k]:
        title = paper["title"]
        bertscore_f1 = bertscore_scores.get(title, 0.0)
        if bertscore_f1 > relevance_threshold:
            relevant_retrieved += 1

    recall = relevant_retrieved / total_relevant
    return min(recall, 1.0)  # Ensure recall never exceeds 1.0


def dcg_at_k(
    ranked_papers: List[Dict], bertscore_scores: Dict[str, float], k: int
) -> float:
    """
    Compute dcg@k using BERTScore F1 as relevance labels.
    """
    dcg = 0.0
    for i, paper in enumerate(ranked_papers[:k]):
        title = paper["title"]
        rel = bertscore_scores.get(title, 0.0)
        gain = 2**rel - 1
        discount = math.log2(i + 2)
        dcg += gain / discount
    return dcg


def idcg_at_k(bertscore_scores: Dict[str, float], k: int) -> float:
    """
    Compute idcg@k using BERTScore F1 as relevance labels.
    """
    sorted_rels = sorted(bertscore_scores.values(), reverse=True)
    idcg = 0.0
    for i, rel in enumerate(sorted_rels[:k]):
        gain = 2**rel - 1
        discount = math.log2(i + 2)
        idcg += gain / discount
    return idcg


def ndcg_at_k(
    ranked_papers: List[Dict], bertscore_scores: Dict[str, float], k: int
) -> float:
    """
    Compute ndcg@k using BERTScore F1 as relevance labels.
    """
    dcg = dcg_at_k(ranked_papers, bertscore_scores, k)
    idcg = idcg_at_k(bertscore_scores, k)
    ndcg = dcg / idcg if idcg != 0 else 0.0
    return min(ndcg, 1.0)


def evaluate_ranking_performance(
    ranked_papers: List[Dict],
    bertscore_scores: Dict[str, float],
    k_values: List[int] = [1, 3, 5, 10],
) -> Dict[str, float]:
    """
    Evaluate ranking performance using BERTScore as ground truth.

    Args:
        ranked_papers: List of papers in ranked order
        bertscore_scores: Dict mapping paper titles to BERTScore F1 scores
        k_values: List of k values to evaluate

    Returns:
        Dict containing evaluation metrics for each k
    """
    results = {}

    for k in k_values:
        if k <= len(ranked_papers):
            precision = precision_at_k(ranked_papers, bertscore_scores, k)
            recall = recall_at_k(ranked_papers, bertscore_scores, k)
            ndcg = ndcg_at_k(ranked_papers, bertscore_scores, k)

            results[f"precision@{k}"] = round(precision, 3)
            results[f"recall@{k}"] = round(recall, 3)
            results[f"ndcg@{k}"] = round(ndcg, 3)

    return results


def _evaluate_bertscore_relevance_core(
    user_prompt: str, recommended_papers: List[Dict]
) -> tuple[List[Dict], Dict[str, float]]:
    """
    Evaluate recommended papers using BERTScore similarity.
    Args:
        user_prompt: The user query or description of interest
        recommended_papers: List of papers with 'title' and 'abstract' keys
    Returns:
        Tuple containing:
        - List[Dict]: Papers with BERTScore scores, sorted by BERTScore F1
        - Dict: BERTScore F1 scores dictionary for ranking evaluation
    """
    # Prepare paper texts (title + abstract)
    paper_texts = [f"{p['title']}. {p['abstract']}" for p in recommended_papers]
    # Compute BERTScore similarity
    bertscore_precisions, bertscore_recalls, bertscore_f1s = (
        compute_bertscore_similarity(user_prompt, paper_texts)
    )
    # Create results with BERTScore scores
    results = []
    bertscore_scores_dict = {}
    for i, (p, r, f1) in enumerate(
        zip(bertscore_precisions, bertscore_recalls, bertscore_f1s)
    ):
        title = recommended_papers[i]["title"]
        bertscore_scores_dict[title] = f1
        results.append(
            {
                "title": title,
                "abstract": recommended_papers[i]["abstract"],
                "bertscore_precision": round(float(p), 3),
                "bertscore_recall": round(float(r), 3),
                "bertscore_f1": round(float(f1), 3),
            }
        )
    # Sort results by BERTScore F1 (descending)
    sorted_results = sorted(results, key=lambda x: x["bertscore_f1"], reverse=True)
    return sorted_results, bertscore_scores_dict


def evaluate_bertscore_relevance(
    user_prompt: str, recommended_papers: List[Dict], top_k: int = 10
):
    """
    Evaluate recommended papers using BERTScore similarity and save results.
    Args:
        user_prompt (str): The user query or description of interest.
        recommended_papers (List[Dict]): List of papers with 'title' and 'abstract' keys.
        top_k (int): Number of top relevant papers to return.
    """
    import logging

    logger = logging.getLogger(__name__)
    try:
        # Get BERTScore evaluation results
        results, bertscore_scores = _evaluate_bertscore_relevance_core(
            user_prompt, recommended_papers
        )
        # Get top-k results
        top_k_results = results[:top_k]
        # Calculate ranking metrics
        ranking_metrics = evaluate_ranking_performance(
            recommended_papers, bertscore_scores, k_values=[1, 3, 5, 10]
        )
        # Calculate average scores
        avg_precision = (
            sum(res["bertscore_precision"] for res in results) / len(results)
            if results
            else 0
        )
        avg_recall = (
            sum(res["bertscore_recall"] for res in results) / len(results)
            if results
            else 0
        )
        avg_f1 = (
            sum(res["bertscore_f1"] for res in results) / len(results) if results else 0
        )
        # Prepare data for saving
        evaluation_data = {
            "timestamp": datetime.now().isoformat(),
            "user_prompt": user_prompt,
            "summary": {
                "total_papers": len(recommended_papers),
                "evaluated_papers": len(results),
                "top_k": top_k,
                "average_scores": {
                    "bertscore_precision": round(avg_precision, 3),
                    "bertscore_recall": round(avg_recall, 3),
                    "bertscore_f1": round(avg_f1, 3),
                },
                "ranking_metrics": ranking_metrics,
            },
            "papers": [],
        }
        # Add individual paper results
        for i, res in enumerate(top_k_results, 1):
            paper_result = {
                "rank": i,
                "title": res["title"],
                "abstract": res["abstract"],
                "scores": {
                    "bertscore_precision": res["bertscore_precision"],
                    "bertscore_recall": res["bertscore_recall"],
                    "bertscore_f1": res["bertscore_f1"],
                },
            }
            evaluation_data["papers"].append(paper_result)
        # Save to file
        evaluation_dir = "evaluation_results"
        if not os.path.exists(evaluation_dir):
            os.makedirs(evaluation_dir)
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bertscore_evaluation_{timestamp_str}.json"
        filepath = os.path.join(evaluation_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(evaluation_data, f, indent=2, ensure_ascii=False)
        # Print summary
        print(f"BERTScore Evaluation Results saved to: {filepath}")
        print(f"User Prompt: {user_prompt}")
        print(f"Total Papers: {len(recommended_papers)}")
        print(f"Evaluated Papers: {len(results)}")
        print("AVERAGE SCORES ACROSS ALL PAPERS:")
        print(f"Average BERTScore Precision: {avg_precision:.3f}")
        print(f"Average BERTScore Recall: {avg_recall:.3f}")
        print(f"Average BERTScore F1: {avg_f1:.3f}")
        print("\nRANKING METRICS (using BERTScore F1 as ground truth):")
        for metric, value in ranking_metrics.items():
            print(f"{metric}: {value}")
    except Exception as e:
        logger.error(f"BERTScore evaluation failed: {e}", exc_info=True)
        raise
