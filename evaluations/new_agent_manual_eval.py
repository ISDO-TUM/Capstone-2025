import bibtexparser
from fuzzywuzzy import fuzz

recommended_titles = [
    "Exponential Regret Bounds for Gaussian Process Bandits with Deterministic Observations",
    "Gaussian Process Optimization with Adaptive Sketching: Scalable and No Regret",
    "Time-Varying Gaussian Process Bandit Optimization",
    "Search costs, demand‐side economies, and the incentives to merge under Bertrand competition",
    "Endogenous Quality Choice: Price vs. Quantity Competition",
    "Collusive outcomes in price competition",
    "Artificial Intelligence: Can Seemingly Collusive Outcomes Be Avoided?",
    "Collusive Outcomes via Pricing Algorithms",
    "Revocable pricing can yield collusive outcomes",
    "Approximate Bayesian Inference for Latent Gaussian models by using Integrated Nested Laplace Approximations"
]


with open("bibliography.bib", encoding="utf-8") as bibtex_file:
    bib_database = bibtexparser.load(bibtex_file)

# Extract titles from .bib
bib_titles = [entry["title"].strip('{}').strip() for entry in bib_database.entries if "title" in entry]

# Compare using fuzzy string matching
threshold = 90
matches = []

print("\n📚 Comparing titles:")
for rec_title in recommended_titles:
    matched = False
    for bib_title in bib_titles:
        score = fuzz.token_set_ratio(rec_title.lower(), bib_title.lower())
        if score >= threshold:
            matched = True
            print(f"✅ MATCH ({score}):\n    '{rec_title}'\n    ↔ '{bib_title}'\n")
            break
    if not matched:
        print(f" NO MATCH:\n    '{rec_title}'\n")
    matches.append(matched)

# Calcular precisión
tp = sum(matches)
fp = len(recommended_titles) - tp
precision = tp / (tp + fp) if (tp + fp) > 0 else 0

print(f"🎯 Precision: {precision:.2f} ({tp}/{tp + fp} recomendaciones relevantes)")
