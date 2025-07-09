import sys
import os
import json
import re
from llm.Agent import trigger_agent
from sklearn.metrics import precision_score, recall_score, f1_score
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def normalize_title(title):
    """Lowercase, strip, and remove punctuation for better matching."""
    return re.sub(r'[^\w\s]', '', title.lower().strip())


def load_titles_from_bib(bib_file_path):
    with open(bib_file_path, encoding='utf-8') as bibtex_file:
        parser = BibTexParser()
        parser.customization = convert_to_unicode
        bib_database = parser.parse_file(bibtex_file)
        titles = [normalize_title(entry.get("title", "")) for entry in bib_database.entries]
        return titles


def evaluate_agent(prompt, relevant_titles):
    print("⌛ Triggering agent...")
    try:
        response = trigger_agent(prompt)
        print("✅ Agent triggered.")
        response_content = response["messages"][-1].content
    except Exception as e:
        print("❌ Error accessing agent response content:", e)
        return 0, 0, 0

    print("🧾 Raw agent response:")
    print(response_content)

    try:
        papers_json = json.loads(response_content)
        predicted_titles = [normalize_title(p["title"]) for p in papers_json["papers"]]
    except Exception as e:
        print("❌ Error parsing agent response:", e)
        return 0, 0, 0

    print("\n✅ Predicted titles:")
    for t in predicted_titles:
        print("-", t)

    print("\n📚 Relevant titles:")
    for t in relevant_titles:
        print("-", t)

    all_titles = set(predicted_titles + relevant_titles)
    y_true = [1 if title in relevant_titles else 0 for title in all_titles]
    y_pred = [1 if title in predicted_titles else 0 for title in all_titles]

    print("\n🧪 y_true:", y_true)
    print("🧪 y_pred:", y_pred)

    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)

    return precision, recall, f1


if __name__ == "__main__":
    print("✅ Script running...\n")

    # === ⬇️ Aditi Evaluation (Prompt + Bib file) ===
    # prompt = """We explore the dynamics of algorithmic pricing in competitive markets, driven by concerns
    # about the potential of pricing algorithms to unintentionally promote collusive behavior among
    # firms. We focus on Gaussian Process (GP) Bandit algorithms operating within a continuous
    # action space in a Bertrand economy. We implement a Bayesian optimization framework for
    # each agent, allowing them to set prices and receive rewards based on a demand function.
    # The reward function is modeled using a GP, which utilizes previous action-reward pairs to
    # make predictions about potential actions. To enhance computational efficiency, we introduce
    # three Memory Loss strategies. GP-based predictions are utilized by acquisition functions that
    # optimize price selection by balancing the exploration-exploitation trade-off, employing one
    # of four key algorithms: GP-UCB, GP-EI, GP-PI, and GP-TS. Our findings suggest that GP
    # Bandits generally lead to non-collusive outcomes when the GP posterior distribution remains
    # smooth and stable. However, in certain market conditions, where the GP is unstable, the
    # use of a GP Bandit algorithm can result in collusive outcomes, influenced by the choice of
    # kernel and hyperparameters. The interaction between the demand function and GP kernels
    # influences whether algorithms promote competitive or moderately collusive behaviors. Within
    # the GP Bandit framework, the choice of acquisition functions is crucial; GP-UCB encourages
    # competitive pricing, while exploratory functions like GP-EI and GP-PI may lead to collusive
    # pricing without necessarily increasing profits. Additionally, strategies that selectively forget
    # older data points offer substantial computational efficiency and reasonable approximations,
    # proving beneficial for large-scale implementations. These results highlight the importance of
    # careful design and tuning of algorithmic pricing strategies to reduce the risk of collusion."""
    # bib_path = "bibliography.bib"

    # === ⬇️ DDoS Evaluation (Prompt + Bib file) ===
    prompt = """This project investigates methods for detecting and mitigating volumetric Distributed Denial of Service (DDoS) attacks in high-speed networks.
    It explores traffic monitoring techniques that can operate at line rate without relying on packet sampling using machine learning approaches for DDoS detection.
    The approach involves integrating hardware-based solutions, such as TCAM switches, into Software-Defined Networking (SDN) environments to enable fast and scalable packet analysis.
    The objective is to identify efficient, real-time, machine learning based DDoS detection mechanisms that are adaptable to evolving multi-vector attack strategies while maintaining minimal network disruption.
    Other goal is to compare these new DDoS detection approaches against old ones."""
    bib_path = "BA.bib"

    print("\n📝 Prompt sent to agent")
    print(prompt)

    relevant_titles = load_titles_from_bib(bib_path)
    print("\n📚 Loaded", len(relevant_titles), "relevant titles")

    precision, recall, f1 = evaluate_agent(prompt, relevant_titles)

    print(f"\n📌 Precision: {precision:.2f}")
    print(f"📌 Recall:    {recall:.2f}")
    print(f"📌 F1 Score:  {f1:.2f}")
