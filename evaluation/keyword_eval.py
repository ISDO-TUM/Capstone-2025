import re

# Hardcoded user keywords
user_keywords = {"machine", "learning", "vision", "robotics"}

# Hardcoded paper keywords
papers_keywords = [
    {"machine", "learning", "robotics"},
    {"deep", "learning", "vision"},
    {"robotics", "control"},
    {"language", "processing"},
    {"vision", "applications"},
    {"machine", "learning"},
    {"vision", "robot", "control"},
    {"data", "mining"},
    {"reinforcement", "learning", "games"},
    {"robotics", "optimization"},
]


def evaluate_papers(user_keywords: set, papers_keywords: list[set]):
    precision_list = []
    recall_list = []
    f1_list = []
    jaccard_list = []

    all_matched_user_keywords = set()

    for idx, paper_keywords in enumerate(papers_keywords):
        if not paper_keywords:
            precision = 0
            recall = 0
            f1 = 0
            jaccard = 0
        else:
            matched = user_keywords & paper_keywords
            all_matched_user_keywords |= matched

            precision = len(matched) / len(paper_keywords)
            recall = len(matched) / len(user_keywords)
            f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0
            jaccard = len(matched) / len(user_keywords | paper_keywords)

        precision_list.append(precision)
        recall_list.append(recall)
        f1_list.append(f1)
        jaccard_list.append(jaccard)

        print(f"Paper {idx + 1}:")
        print(f"Matched keywords: {matched}")
        print(f"Precision: {precision:.2f}, Recall: {recall:.2f}, F1: {f1:.2f}, Jaccard: {jaccard:.2f}\n")

    avg_precision = sum(precision_list) / len(precision_list)
    avg_recall = sum(recall_list) / len(recall_list)
    avg_f1 = sum(f1_list) / len(f1_list)
    avg_jaccard = sum(jaccard_list) / len(jaccard_list)
    coverage = len(all_matched_user_keywords) / len(user_keywords) if user_keywords else 0

    print(f"=== AVERAGE RESULTS ===")
    print(f"Average Precision: {avg_precision:.2f}")
    print(f"Average Recall: {avg_recall:.2f}")
    print(f"Average F1: {avg_f1:.2f}")
    print(f"Average Jaccard: {avg_jaccard:.2f}")
    print(f"Coverage: {coverage:.2f}")

    return {
        "avg_precision": avg_precision,
        "avg_recall": avg_recall,
        "avg_f1": avg_f1,
        "avg_jaccard": avg_jaccard,
        "coverage": coverage
    }


# Run evaluation
evaluate_papers(user_keywords, papers_keywords)
