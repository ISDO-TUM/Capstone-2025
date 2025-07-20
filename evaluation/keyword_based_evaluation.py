from typing import List, Dict, Any
import numpy as np
from keybert import KeyBERT
from sentence_transformers import SentenceTransformer


def cosine_similarity(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


# KeyBERT setup for domain-specific keyword extraction
kw_model = KeyBERT(model='allenai/scibert_scivocab_uncased')


def extract_keywords_keybert(text, top_n=10, stopwords=None):
    keywords = kw_model.extract_keywords(
        text,
        keyphrase_ngram_range=(1, 3),
        stop_words=stopwords or 'english',
        use_maxsum=True,
        top_n=top_n
    )
    return [kw for kw, score in keywords]


def keyword_coverage(prompt_keywords, paper_keywords):
    prompt_set = set(kw.lower() for kw in prompt_keywords)
    paper_set = set(kw.lower() for kw in paper_keywords)
    overlap = prompt_set & paper_set
    return len(overlap) / max(len(prompt_set), 1), list(overlap)


def jaccard_similarity(prompt_keywords, paper_keywords):
    prompt_set = set(kw.lower() for kw in prompt_keywords)
    paper_set = set(kw.lower() for kw in paper_keywords)
    intersection = prompt_set & paper_set
    union = prompt_set | paper_set
    return len(intersection) / max(len(union), 1)


def precision_recall_f1(prompt_keywords, paper_keywords):
    prompt_set = set(kw.lower() for kw in prompt_keywords)
    paper_set = set(kw.lower() for kw in paper_keywords)
    intersection = prompt_set & paper_set

    precision = len(intersection) / max(len(paper_set), 1)
    recall = len(intersection) / max(len(prompt_set), 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-8)

    return precision, recall, f1


def evaluate_keyword_based_relevance(user_prompt: str, recommended_papers: List[Dict], top_k: int = 10) -> Any:
    """
    Evaluate recommended papers using keyword-based relevance scoring.

    Args:
        user_prompt (str): The user query or description of interest.
        recommended_papers (List[Dict]): List of papers with 'title' and 'abstract' keys.
        top_k (int): Number of top relevant papers to return.

    Returns:
        Tuple containing:
        - List[Dict]: A list of papers with keyword-based scores
        - List[Dict]: Sorted papers
        - List[str]: Prompt keywords
        - Dict: Paper keywords dictionary
        - Dict: KeyBERT matches
    """
    # Prepare paper data
    paper_data = []
    paper_texts = []
    for i, paper in enumerate(recommended_papers):
        title = paper.get("title", "")
        abstract = paper.get("abstract", "")
        content = f"{title}\n\n{abstract}".strip()
        if content:
            paper_data.append({
                "id": f"paper_{i}",
                "title": title,
                "abstract": abstract,
                "content": content
            })
            paper_texts.append(content)

    prompt_keywords = extract_keywords_keybert(user_prompt, top_n=10)
    keybert_matches = {}
    paper_keywords_dict = {}
    jaccard_scores = {}
    precision_scores = {}
    recall_scores = {}
    f1_scores = {}

    for paper, text in zip(paper_data, paper_texts):
        paper_keywords = extract_keywords_keybert(text, top_n=10)
        paper_keywords_dict[paper["id"]] = paper_keywords

        # KeyBERT coverage for matches only
        _, overlap = keyword_coverage(prompt_keywords, paper_keywords)
        keybert_matches[paper["id"]] = overlap

        # Jaccard similarity
        jaccard_scores[paper["id"]] = jaccard_similarity(prompt_keywords, paper_keywords)

        # Precision, Recall, F1
        precision, recall, f1 = precision_recall_f1(prompt_keywords, paper_keywords)
        precision_scores[paper["id"]] = precision
        recall_scores[paper["id"]] = recall
        f1_scores[paper["id"]] = f1

    # Semantic similarity using sentence transformers
    model = SentenceTransformer("allenai-specter")
    prompt_embedding = model.encode(user_prompt, convert_to_numpy=True)
    paper_embeddings = model.encode(paper_texts, convert_to_numpy=True)
    semantic_scores = {}
    for paper, emb in zip(paper_data, paper_embeddings):
        semantic_scores[paper["id"]] = cosine_similarity(prompt_embedding, emb)

    # Combine results
    results = []
    for paper in paper_data:
        kid = paper["id"]
        jaccard_score = jaccard_scores.get(kid, 0.0) or 0.0
        precision_score = precision_scores.get(kid, 0.0) or 0.0
        recall_score = recall_scores.get(kid, 0.0) or 0.0
        f1_score = f1_scores.get(kid, 0.0) or 0.0
        semantic_score = semantic_scores.get(kid, 0.0) or 0.0

        results.append({
            "title": paper["title"],
            "abstract": paper["abstract"],
            "jaccard_score": round(float(jaccard_score), 3),
            "precision_score": round(float(precision_score), 3),
            "recall_score": round(float(recall_score), 3),
            "f1_score": round(float(f1_score), 3),
            "semantic_score": round(float(semantic_score), 3)
        })

    # Return sorted results and keyword info (by semantic score)
    sorted_results = sorted(results, key=lambda x: x["semantic_score"], reverse=True)[:top_k]
    sorted_papers = [paper for paper, _ in
                     sorted(zip(paper_data, results), key=lambda x: x[1]["semantic_score"], reverse=True)[:top_k]]

    return sorted_results, sorted_papers, prompt_keywords, paper_keywords_dict, keybert_matches


# Example usage
if __name__ == "__main__":

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

    results, sorted_papers, prompt_keywords, paper_keywords_dict, keybert_matches = evaluate_keyword_based_relevance(
        user_prompt, recommended_papers)

    print("Keyword-Based Evaluation Results:")
    for i, (paper, res) in enumerate(zip(sorted_papers, results), 1):
        print(f"{i}. {res['title']}")
        print(f"Jaccard Score: {res['jaccard_score']}")
        print(f"Precision: {res['precision_score']}")
        print(f"Recall: {res['recall_score']}")
        print(f"F1 Score: {res['f1_score']}")
        print(f"Semantic Score: {res['semantic_score']}")
        print(f"Prompt Keywords: {prompt_keywords}")
        print(f"Paper Keywords: {paper_keywords_dict.get(paper['id'], [])}")
        print(f"Matched Keywords: {keybert_matches.get(paper['id'], [])}\n")
