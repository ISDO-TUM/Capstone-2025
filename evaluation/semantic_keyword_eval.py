from sklearn.metrics.pairwise import cosine_similarity
import matplotlib.pyplot as plt
from llm.Embeddings import embed_keyword_set

# Example hardcoded sets
user_keywords = {"machine learning", "vision", "robotics"}
papers_keywords = [
    {"machine learning", "robotics"},
    {"deep learning", "vision"},
    {"robotics", "control"},
    {"language", "processing"},
    {"vision", "applications"},
    {"machine learning"},
    {"vision", "robot", "control"},
    {"data", "mining"},
    {"reinforcement learning", "games"},
    {"robotics", "optimization"}
]


def evaluate_papers_with_semantics(user_keywords: set, papers_keywords: list[set], sim_threshold=0.6):
    precision_list = []
    recall_list = []
    f1_list = []
    jaccard_list = []
    sim_list = []
    relevant_flags = []
    all_matched_user_keywords = set()

    # Embed user keywords set once
    user_vec = embed_keyword_set(user_keywords)

    for idx, paper_keywords in enumerate(papers_keywords):
        if not paper_keywords:
            precision = 0
            recall = 0
            f1 = 0
            jaccard = 0
            sim = 0
        else:
            matched = user_keywords & paper_keywords
            all_matched_user_keywords |= matched

            precision = len(matched) / len(paper_keywords)
            recall = len(matched) / len(user_keywords)
            f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0
            jaccard = len(matched) / len(user_keywords | paper_keywords)

            # Semantic similarity
            paper_vec = embed_keyword_set(paper_keywords)
            sim = cosine_similarity([user_vec], [paper_vec])[0][0]

        precision_list.append(precision)
        recall_list.append(recall)
        f1_list.append(f1)
        jaccard_list.append(jaccard)
        sim_list.append(sim)
        relevant_flags.append(sim >= sim_threshold)

        print(f"Paper {idx + 1}:")
        print(f"Matched keywords: {matched if paper_keywords else set()}")
        print(f"Precision: {precision:.2f}, Recall: {recall:.2f}, F1: {f1:.2f}, Jaccard: {jaccard:.2f}, Semantic Sim: {sim:.2f}")
        print(f"Semantically relevant (sim >= {sim_threshold}): {sim >= sim_threshold}\n")

    avg_precision = sum(precision_list) / len(precision_list)
    avg_recall = sum(recall_list) / len(recall_list)
    avg_f1 = sum(f1_list) / len(f1_list)
    avg_jaccard = sum(jaccard_list) / len(jaccard_list)
    avg_sim = sum(sim_list) / len(sim_list)
    coverage = len(all_matched_user_keywords) / len(user_keywords) if user_keywords else 0
    relevant_rate = sum(relevant_flags) / len(relevant_flags)

    print(f"=== AVERAGE RESULTS ===")
    print(f"Average Precision: {avg_precision:.2f}")
    print(f"Average Recall: {avg_recall:.2f}")
    print(f"Average F1: {avg_f1:.2f}")
    print(f"Average Jaccard: {avg_jaccard:.2f}")
    print(f"Average Semantic Similarity: {avg_sim:.2f}")
    print(f"Coverage: {coverage:.2f}")
    print(f"Semantic Relevant Rate (sim >= {sim_threshold}): {relevant_rate:.2f}")

    return {
        "avg_precision": avg_precision,
        "avg_recall": avg_recall,
        "avg_f1": avg_f1,
        "avg_jaccard": avg_jaccard,
        "avg_sim": avg_sim,
        "coverage": coverage,
        "semantic_relevant_rate": relevant_rate,
        "f1_list": f1_list,
        "sim_list": sim_list
    }


def plot_metrics(sim_list, f1_list):
    plt.figure(figsize=(10,5))
    plt.plot(sim_list, label="Semantic Similarity", marker='o')
    plt.plot(f1_list, label="F1 score", marker='x')
    plt.xlabel("Paper Index")
    plt.ylabel("Score")
    plt.title("Per-Paper Semantic Similarity and F1 score")
    plt.legend()
    plt.savefig("semantic_eval_plot.png")
    print("Plot saved as semantic_eval_plot.png")


results = evaluate_papers_with_semantics(user_keywords, papers_keywords)
plot_metrics(results["sim_list"], results["f1_list"])