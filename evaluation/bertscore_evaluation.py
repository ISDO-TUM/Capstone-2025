from typing import List, Dict
from bert_score import score
import math


def compute_bertscore_similarity(user_prompt: str, paper_texts: List[str], model_type: str = "bert-base-uncased"):
    """
    Compute BERTScore similarity between user prompt and paper texts.
    Returns precision, recall, and F1 scores.
    """
    P, R, F1 = score(
        paper_texts, [user_prompt] * len(paper_texts),
        model_type=model_type,
        lang="en",
        verbose=False
    )
    return P.numpy().tolist(), R.numpy().tolist(), F1.numpy().tolist()


def precision_at_k(ranked_papers: List[Dict], bertscore_scores: Dict[str, float], k: int) -> float:
    """
    Compute Precision@k using BERTScore F1 as relevance labels.
    """
    if k == 0:
        return 0.0

    relevance_threshold = 0.5
    relevant_count = 0

    for paper in ranked_papers[:k]:
        title = paper['title']
        bertscore_f1 = bertscore_scores.get(title, 0.0)
        if bertscore_f1 > relevance_threshold:
            relevant_count += 1

    return relevant_count / k


def recall_at_k(ranked_papers: List[Dict], bertscore_scores: Dict[str, float], k: int) -> float:
    """
    Compute Recall@k using BERTScore F1 as relevance labels.
    """
    relevance_threshold = 0.5

    # Count total relevant papers
    total_relevant = sum(1 for score in bertscore_scores.values() if score > relevance_threshold)

    if total_relevant == 0:
        return 0.0

    relevant_retrieved = 0
    for paper in ranked_papers[:k]:
        title = paper['title']
        bertscore_f1 = bertscore_scores.get(title, 0.0)
        if bertscore_f1 > relevance_threshold:
            relevant_retrieved += 1

    recall = relevant_retrieved / total_relevant
    return min(recall, 1.0)  # Ensure recall never exceeds 1.0


def dcg_at_k(ranked_papers: List[Dict], bertscore_scores: Dict[str, float], k: int) -> float:
    """
    Compute DCG@k using BERTScore F1 as relevance scores.
    """
    dcg = 0.0
    for i, paper in enumerate(ranked_papers[:k]):
        title = paper['title']
        relevance = bertscore_scores.get(title, 0.0)
        dcg += relevance / math.log2(i + 2)  # log2(i+2) because i starts at 0
    return dcg


def idcg_at_k(bertscore_scores: Dict[str, float], k: int) -> float:
    """
    Compute IDCG@k (ideal DCG) by sorting papers by BERTScore F1 in descending order.
    """
    sorted_scores = sorted(bertscore_scores.values(), reverse=True)

    idcg = 0.0
    for i, relevance in enumerate(sorted_scores[:k]):
        idcg += relevance / math.log2(i + 2)
    return idcg


def ndcg_at_k(ranked_papers: List[Dict], bertscore_scores: Dict[str, float], k: int) -> float:
    """
    Compute nDCG@k using BERTScore F1 as relevance scores.
    """
    dcg = dcg_at_k(ranked_papers, bertscore_scores, k)
    idcg = idcg_at_k(bertscore_scores, k)

    if idcg == 0:
        return 0.0

    ndcg = dcg / idcg
    return min(ndcg, 1.0)  # Ensure NDCG never exceeds 1.0


def evaluate_ranking_performance(ranked_papers: List[Dict], bertscore_scores: Dict[str, float],
                                 k_values: List[int] = [1, 3, 5, 10]) -> Dict[str, float]:
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

            results[f'precision@{k}'] = round(precision, 3)
            results[f'recall@{k}'] = round(recall, 3)
            results[f'ndcg@{k}'] = round(ndcg, 3)

    return results


def evaluate_bertscore_relevance(user_prompt: str, recommended_papers: List[Dict]) -> tuple[List[Dict], Dict[str, float]]:
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
    bertscore_precisions, bertscore_recalls, bertscore_f1s = compute_bertscore_similarity(user_prompt, paper_texts)

    # Create results with BERTScore scores
    results = []
    bertscore_scores_dict = {}

    for i, (p, r, f1) in enumerate(zip(bertscore_precisions, bertscore_recalls, bertscore_f1s)):
        title = recommended_papers[i]["title"]
        bertscore_scores_dict[title] = f1

        results.append({
            "title": title,
            "abstract": recommended_papers[i]["abstract"],
            "bertscore_precision": round(float(p), 3),
            "bertscore_recall": round(float(r), 3),
            "bertscore_f1": round(float(f1), 3)
        })

    # Sort results by BERTScore F1 (descending)
    sorted_results = sorted(results, key=lambda x: x["bertscore_f1"], reverse=True)

    return sorted_results, bertscore_scores_dict


# Example usage
if __name__ == "__main__":
    # Sample user prompt
    user_prompt = "I'm interested in papers on algorithmic pricing using Gaussian Process Bandits, including Bayesian optimization in Bertrand markets, the impact of acquisition functions (e.g., GP-UCB, GP-EI), the role of GP kernels and hyperparameters in shaping market outcomes, and memory loss strategies for computational efficiency."
    recommended_papers = [
        {
            "title": "Contextual Gaussian Process Bandit Optimization",
            "abstract": "How should we design experiments to maximize performance of a complex system, taking into account uncontrollable environmental conditions? How should we select relevant documents (ads) to display, given information about the user? These tasks can be formalized as contextual bandit problems, where at each round, we receive context (about the experimental conditions, the query), and have to choose an action (parameters, documents). The key challenge is to trade off exploration by gathering data for estimating the mean payoff function over the context-action space, and to exploit by choosing an action deemed optimal based on the gathered data. We model the payoff function as a sample from a Gaussian process defined over the joint context-action space, and develop CGP-UCB, an intuitive upper-confidence style algorithm. We show that by mixing and matching kernels for contexts and actions, CGP-UCB can handle a variety of practical applications. We further provide generic tools for deriving regret bounds when using such composite kernel functions. Lastly, we evaluate our algorithm on two case studies, in the context of automated vaccine design and sensor management. We show that context-sensitive optimization outperforms no or naive use of context."
        },
        {
            "title": "Parallelizing exploration-exploitation tradeoffs in Gaussian process bandit optimization",
            "abstract": "How can we take advantage of opportunities for experimental parallelization in exploration-exploitation tradeoffs? In many experimental scenarios, it is often desirable to execute experiments simultaneously or in batches, rather than only performing one at a time. Additionally, observations may be both noisy and expensive. We introduce Gaussian Process Batch Upper Confidence Bound (GP-BUCB), an upper confidence bound-based algorithm, which models the reward function as a sample from a Gaussian process and which can select batches of experiments to run in parallel. We prove a general regret bound for GP-BUCB, as well as the surprising result that for some common kernels, the asymptotic average regret can be made independent of the batch size. The GP-BUCB algorithm is also applicable in the related case of a delay between initiation of an experiment and observation of its results, for which the same regret bounds hold. We also introduce Gaussian Process Adaptive Upper Confidence Bound (GP-AUCB), a variant of GP-BUCB which can exploit parallelism in an adaptive manner. We evaluate GP-BUCB and GP-AUCB on several simulated and real data sets. These experiments show that GP-BUCB and GP-AUCB are competitive with state-of-the-art heuristics."
        },
        {
            "title": "Gaussian Process Optimization in the Bandit Setting: No Regret and Experimental Design",
            "abstract": "Many applications require optimizing an unknown, noisy function that is expensive to evaluate. We formalize this task as a multi-armed bandit problem, where the payoff function is either sampled from a Gaussian process (GP) or has low RKHS norm. We resolve the important open problem of deriving regret bounds for this setting, which imply novel convergence rates for GP optimization. We analyze GP-UCB, an intuitive upper-confidence based algorithm, and bound its cumulative regret in terms of maximal information gain, establishing a novel connection between GP optimization and experimental design. Moreover, by bounding the latter in terms of operator spectra, we obtain explicit sublinear regret bounds for many commonly used covariance functions. In some important cases, our bounds have surprisingly weak dependence on the dimensionality. In our experiments on real sensor data, GP-UCB compares favorably with other heuristical GP optimization approaches."
        },
        {
            "title": "Gaussian Process Optimization in the Bandit Setting: No Regret and Experimental Design",
            "abstract": "This is an alternative version of the previous paper, offering the same in-depth analysis of GP-UCB and its regret bounds. It is highly relevant for understanding the theoretical underpinnings of Gaussian Process Bandits in pricing and market optimization, with a focus on kernel selection and information gain."
        },
        {
            "title": "Practical Bayesian Optimization of Machine Learning Algorithms",
            "abstract": "Machine learning algorithms frequently require careful tuning of model hyperparameters, regularization terms, and optimization parameters. Unfortunately, this tuning is often a \"black art\" that requires expert experience, unwritten rules of thumb, or sometimes brute-force search. Much more appealing is the idea of developing automatic approaches which can optimize the performance of a given learning algorithm to the task at hand. In this work, we consider the automatic tuning problem within the framework of Bayesian optimization, in which a learning algorithm's generalization performance is modeled as a sample from a Gaussian process (GP). The tractable posterior distribution induced by the GP leads to efficient use of the information gathered by previous experiments, enabling optimal choices about what parameters to try next. Here we show how the effects of the Gaussian process prior and the associated inference procedure can have a large impact on the success or failure of Bayesian optimization. We show that thoughtful choices can lead to results that exceed expert-level performance in tuning machine learning algorithms. We also describe new algorithms that take into account the variable cost (duration) of learning experiments and that can leverage the presence of multiple cores for parallel experimentation. We show that these proposed algorithms improve on previous automatic procedures and can reach or surpass human expert-level optimization on a diverse set of contemporary algorithms including latent Dirichlet allocation, structured SVMs and convolutional neural networks."
        },
        {
            "title": "A Tutorial on Bayesian Optimization",
            "abstract": "Bayesian optimization is an approach to optimizing objective functions that take a long time (minutes or hours) to evaluate. It is best-suited for optimization over continuous domains of less than 20 dimensions, and tolerates stochastic noise in function evaluations. It builds a surrogate for the objective and quantifies the uncertainty in that surrogate using a Bayesian machine learning technique, Gaussian process regression, and then uses an acquisition function defined from this surrogate to decide where to sample. In this tutorial, we describe how Bayesian optimization works, including Gaussian process regression and three common acquisition functions: expected improvement, entropy search, and knowledge gradient. We then discuss more advanced techniques, including running multiple function evaluations in parallel, multi-fidelity and multi-information source optimization, expensive-to-evaluate constraints, random environmental conditions, multi-task Bayesian optimization, and the inclusion of derivative information. We conclude with a discussion of Bayesian optimization software and future research directions in the field. Within our tutorial material we provide a generalization of expected improvement to noisy evaluations, beyond the noise-free setting where it is more commonly applied. This generalization is justified by a formal decision-theoretic argument, standing in contrast to previous ad hoc modifications."
        },
        {
            "title": "Information-Theoretic Regret Bounds for Gaussian Process Optimization in the Bandit Setting",
            "abstract": "This paper provides information-theoretic regret bounds for GP optimization in the bandit setting, with explicit analysis of kernel functions and their impact on performance. It is directly relevant to your focus on the influence of GP kernels and hyperparameters in market outcomes and offers theoretical guarantees for GP-UCB."
        },
        {
            "title": "Clustering-Guided Gp-Ucb for Bayesian Optimization",
            "abstract": "This work proposes a clustering-guided method to improve GP-UCB, particularly for objective functions with sharp peaks and valleys. It addresses practical challenges in hyperparameter tuning and helps avoid local optima, which is pertinent to your interest in acquisition functions and efficient exploration in complex market environments."
        },
        {
            "title": "Gaussian Processes for Machine Learning",
            "abstract": "This authoritative book provides a comprehensive introduction to Gaussian Processes, including detailed discussions of kernel functions, model selection, and approximation methods. It is an essential reference for understanding the theoretical and practical aspects of GP kernels and hyperparameters, which are central to your research on market outcomes and algorithmic pricing."
        },
        {
            "title": "Sparse Gaussian Processes using Pseudo-inputs",
            "abstract": "This paper introduces a sparse GP regression model using pseudo-inputs, significantly reducing computational costs. It is highly relevant for your interest in memory loss strategies and computational efficiency, offering practical methods for scaling GP-based optimization in large-scale market applications."
        }
    ]

    # Get BERTScore evaluation results
    results, bertscore_scores = evaluate_bertscore_relevance(user_prompt, recommended_papers)

    print("BERTScore Evaluation Results:")
    print("Papers ranked by BERTScore F1 (title + abstract similarity to user prompt):")
    for i, res in enumerate(results, 1):
        print(f"{i}. {res['title']}")
        print(f"BERTScore F1: {res['bertscore_f1']}")
        print()

    print("Ranking Evaluation Metrics:")
    print("Using BERTScore F1 as ground truth relevance:")
    ranking_metrics = evaluate_ranking_performance(results, bertscore_scores, k_values=[1, 3, 5])
    for metric, value in ranking_metrics.items():
        print(f"{metric}: {value}")
