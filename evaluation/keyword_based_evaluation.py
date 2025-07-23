from typing import List, Dict
import numpy as np
from keybert import KeyBERT
from sentence_transformers import SentenceTransformer
import json
import os
from datetime import datetime


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


def evaluate_keyword_based_relevance(user_prompt: str, recommended_papers: List[Dict], top_k: int = 10):
    """
    Evaluate recommended papers using keyword-based relevance scoring and print results.

    Args:
        user_prompt (str): The user query or description of interest.
        recommended_papers (List[Dict]): List of papers with 'title' and 'abstract' keys.
        top_k (int): Number of top relevant papers to return.
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

    # Sort results by semantic score
    sorted_results = sorted(results, key=lambda x: x["semantic_score"], reverse=True)[:top_k]
    sorted_papers = [paper for paper, _ in
                     sorted(zip(paper_data, results), key=lambda x: x[1]["semantic_score"], reverse=True)[:top_k]]

    # Calculate average scores
    avg_jaccard = sum(res['jaccard_score'] for res in results) / len(results) if results else 0
    avg_precision = sum(res['precision_score'] for res in results) / len(results) if results else 0
    avg_recall = sum(res['recall_score'] for res in results) / len(results) if results else 0
    avg_f1 = sum(res['f1_score'] for res in results) / len(results) if results else 0
    avg_semantic = sum(res['semantic_score'] for res in results) / len(results) if results else 0

    # Prepare data for saving
    evaluation_data = {
        "timestamp": datetime.now().isoformat(),
        "user_prompt": user_prompt,
        "prompt_keywords": prompt_keywords,
        "summary": {
            "total_papers": len(recommended_papers),
            "evaluated_papers": len(results),
            "top_k": top_k,
            "average_scores": {
                "jaccard_score": round(avg_jaccard, 3),
                "precision_score": round(avg_precision, 3),
                "recall_score": round(avg_recall, 3),
                "f1_score": round(avg_f1, 3),
                "semantic_score": round(avg_semantic, 3)
            }
        },
        "papers": []
    }

    # Add individual paper results
    for i, (paper, res) in enumerate(zip(sorted_papers, sorted_results), 1):
        paper_result = {
            "rank": i,
            "title": res['title'],
            "abstract": res['abstract'],
            "scores": {
                "jaccard_score": res['jaccard_score'],
                "precision_score": res['precision_score'],
                "recall_score": res['recall_score'],
                "f1_score": res['f1_score'],
                "semantic_score": res['semantic_score']
            },
            "keywords": {
                "paper_keywords": paper_keywords_dict.get(paper['id'], []),
                "matched_keywords": keybert_matches.get(paper['id'], [])
            }
        }
        evaluation_data["papers"].append(paper_result)

    # Save to file
    evaluation_dir = "evaluation_results"
    if not os.path.exists(evaluation_dir):
        os.makedirs(evaluation_dir)

    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"keyword_evaluation_{timestamp_str}.json"
    filepath = os.path.join(evaluation_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(evaluation_data, f, indent=2, ensure_ascii=False)

    # Print summary
    print(f"Keyword-Based Evaluation Results saved to: {filepath}")
    print(f"User Prompt: {user_prompt}")
    print(f"Total Papers: {len(recommended_papers)}")
    print(f"Evaluated Papers: {len(results)}")
    print("AVERAGE SCORES ACROSS ALL PAPERS:")
    print(f"Average Jaccard Score: {avg_jaccard:.3f}")
    print(f"Average Precision: {avg_precision:.3f}")
    print(f"Average Recall: {avg_recall:.3f}")
    print(f"Average F1 Score: {avg_f1:.3f}")
    print(f"Average Semantic Score: {avg_semantic:.3f}")
