from typing import List, Dict, Any
from llama_index.core.schema import TextNode
from llama_index.retrievers.bm25 import BM25Retriever
from dotenv import load_dotenv
import Stemmer

load_dotenv()


def evaluate_bm25_lexical_matching(user_prompt: str, recommended_papers: List[Dict], top_k: int = 10) -> Any:
    """
    Evaluate recommended papers using BM25 lexical matching via LlamaIndex.

    Args:
        user_prompt (str): The user query or description of interest.
        recommended_papers (List[Dict]): List of papers with 'title' and 'abstract' keys.
        top_k (int): Number of top relevant papers to return.

    Returns:
        Tuple containing:
        - List[Dict]: A list of papers with BM25 scores
        - List[TextNode]: Sorted nodes
        - Dict: BM25 scores dictionary
    """

    # Prepare nodes
    nodes = []
    for paper in recommended_papers:
        title = paper.get("title", "")
        abstract = paper.get("abstract", "")
        content = f"{title}\n\n{abstract}".strip()
        if content:  # only add if not empty
            node = TextNode(text=content, metadata={"title": title, "abstract": abstract})
            nodes.append(node)

    # BM25 Retriever
    bm25_retriever = BM25Retriever.from_defaults(
        nodes=nodes,
        similarity_top_k=len(nodes),
        stemmer=Stemmer.Stemmer("english"),
        language="english"
    )
    bm25_results = {node.node.node_id: node.score for node in bm25_retriever.retrieve(user_prompt)}

    # Prepare results
    results = []
    for node in nodes:
        kid = node.node_id
        bm25_score = bm25_results.get(kid, 0.0) or 0.0

        results.append({
            "title": node.metadata["title"],
            "abstract": node.metadata["abstract"],
            "bm25_score": round(float(bm25_score), 3)
        })

    # Return sorted results
    sorted_results = sorted(results, key=lambda x: x["bm25_score"], reverse=True)[:top_k]
    sorted_nodes = [node for node, _ in
                    sorted(zip(nodes, results), key=lambda x: x[1]["bm25_score"], reverse=True)[:top_k]]

    return sorted_results, sorted_nodes, bm25_results


# Example usage
if __name__ == "__main__":
    # Set random seeds for reproducibility
    import numpy as np

    np.random.seed(42)

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

    results, result_nodes, bm25_scores = evaluate_bm25_lexical_matching(user_prompt, recommended_papers)

    print("BM25 Lexical Matching Results:")
    for i, (node, res) in enumerate(zip(result_nodes, results), 1):
        print(f"{i}. {res['title']}")
        print(f"BM25 Score: {res['bm25_score']}")
