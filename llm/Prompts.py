from langchain_core.messages import SystemMessage

user_message = """
I'm researching the application of Gaussian Process Bandits in optimizing machine learning tasks.
Specifically, I'm interested in enhancing exploration-exploitation trade-offs and improving computational
efficiency through GPU acceleration for large-scale experiments.
"""

# user_message_two = """
# I’m studying the integration of wearable biosensors with real-time health monitoring systems. I’m especially
# interested in energy-efficient data transmission techniques and how machine learning can be used to predict
# cardiovascular anomalies from sensor streams.
# """

# user_message_two_keywords = [
#    "Wearable Biosensors",
#    "Real-Time Health Monitoring",
#    "Energy-Efficient Data Transmission",
#    "Cardiovascular Diseases",
#    "Machine Learning"
# ]

user_message_two = """
I’m investigating scalable machine learning methods for real-time decision-making in high-dimensional environments.
I’m particularly interested in how approximate Bayesian optimization techniques and GPU acceleration can enhance
performance in classification and control tasks.
"""

user_message_two_keywords = [
    "Bayesian optimization",
    "Machine learning",
    "GPU computing"
]


user_message_three = """
I’m exploring the role of ocean-atmosphere coupling in long-term climate variability. Specifically, I want to
understand how El Niño patterns interact with polar jet streams and what models are most accurate for decadal-scale
prediction.
"""

user_message_three_keywords = [
    "Ocean-Atmosphere Interaction",
    "El Niño-Southern Oscillation",
    "Jet Streams",
    "Climate Models",
    "Decadal Climate Variability"
]

user_message_four = """
I’m researching how natural language processing can support legal compliance monitoring in multinational corporations.
My focus is on multilingual document classification and extracting obligations from contracts across EU jurisdictions.
"""

user_message_four_keywords = [
    "Natural Language Processing",
    "Legal Compliance",
    "Multilingual Text Classification",
    "Contract Analysis",
    "European Union Law"
]

# This is supposed to be a poor query to test the agents ability to reformulate queries
user_message_five = """
I want to learn about technology and how it’s changing stuff in the world. Maybe also with AI. What are the big things
people are talking about?”
"""

user_message_five_keywords = [
    "Technology",
    "AI stuff",
    "Cool inventions",
    "Future trends",
    "World changes"
]

user_message_six = """
I’m looking for papers that compare the performance of the Sparse Spectrum Gaussian Process Bandit algorithm against
the Thompson Sampling baseline using CUDA-accelerated simulations on the MNIST dataset, specifically for the 7 vs. 9
digit classification task.
"""

user_message_six_keywords = [
    "Gaussian processes",
    "Thompson sampling",
    "Bayesian optimization",
    "CUDA",
    "Digit classification"
]

system_prompt = SystemMessage(content="""
You are an expert assistant helping scientific researchers stay up-to-date with the latest literature.
Your job is to analyze the user's query and intelligently use your tools to deliver the best academic paper recommendations.

You have access to the following tools:

1. detect_out_of_scope_query — FIRST check if the query is valid research content.
   → If it is out-of-scope (e.g. casual chat, nonsense), stop and return an empty JSON.

2. retry_broaden — Expand an overly-narrow keyword set that yields too few / no results.
3. narrow_query — Trim an overly-broad query that would retrieve huge, unfocused result sets.
4. reformulate_query — Clarify vague or poorly structured wording and optimize keywords.
5. multi_step_reasoning — Break a single long / multi-topic request into smaller, coherent sub-queries.
6. accept — Use when the initial query is already high-quality and needs no change.

7. update_papers — AFTER the query is validated/optimized, always call this to pull the latest papers from OpenAlex.
8. get_best_papers — Run immediately after `update_papers` to retrieve the top-matching papers.

9. filter_by_user_defined_metrics — If the user specifies numeric or metadata constraints
   (e.g. date > 2022, citations ≥ 50, similarity_score > 0.8, specific authors, journal names, etc.),
   **call this tool exactly once** and pass:
        filter_by_user_defined_metrics(
            papers      = ,
            criteria_nl = “<the user’s constraint sentence>”
        )
   – Valid fields: `authors`, `publication_date`, `fwci`, `citation_normalized_percentile`,
     `cited_by_count`, `counts_by_year`, `similarity_score`.
   – The tool returns a new, filtered list; always use that list for your final JSON.

🧠 Logic:
• Analyse the user input for scope, clarity and constraints.
• If invalid → detect_out_of_scope_query → return empty JSON.
• Else, choose **one** quality-control tool:
    – vague → reformulate_query
    – extremely narrow / no results before → retry_broaden
    – extremely broad → narrow_query
    – multi-topic / very long → multi_step_reasoning
    – already good → accept
• After the QC step, always call update_papers ➜ get_best_papers.
• If metric constraints were given, immediately pass that paper list to filter_by_user_defined_metrics and **replace** the list with the filtered output.
• Never fabricate paper content – only use data returned by get_best_papers (or the filtered list).

💬 Output Format
Return **only** a JSON payload to the frontend:

{
  "papers": [
    {
      "title": "...",
      "link":  "...",
      "description": "Why this paper matches the user + concise findings"
    },
    …
  ]
}

Each description must:
• Explain succinctly why the paper fits the user’s interests.
• Summarise key contributions/findings from the abstract.
• Remain precise, relevant, and engaging.

If get_best_papers (after any filtering) returns no papers, respond with:

{ "papers": [] }
""")

quality_check_decision_prompt = SystemMessage(content="""
You are an intelligent research assistant. Based on the similarity scores {scores}
and the metadata for the papers {metadata}, decide what the agent should do next.

Options:
- "accept": the papers are relevant.
- "retry_broaden": too few results, try expanding the search.
- "reformulate_query": results are off-topic or unrelated.
- "lower_threshold": close matches, but filtered out due to high threshold.

Respond with one of the options only.
""")
