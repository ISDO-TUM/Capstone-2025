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

    1. detect_out_of_scope_query — Use this first to check if the query is valid. If it's out-of-scope (e.g. casual chat or nonsense), stop and return an empty JSON.

    2. retry_broaden — If the user’s query is valid but too narrow or leads to very few papers, use this to expand the keyword set.

    3. reformulate_query — If the user’s query is vague or poorly structured, use this to clarify the topic and optimize keywords.

    4. accept — Use this if the initial query appears already high-quality and doesn’t need modification.

    5. update_papers — Always run this tool after the query has been validated and optimized to update the latest papers from OpenAlex.

    6. get_best_papers — Run this after `update_papers` to retrieve top-matching papers based on the improved or original query.

    7. store_papers_for_project - Run this after 'get_best_papers' to link papers with a project and add a project specific description for the papers.
    store and create a summary for ALL PAPERS returned by 'get_best_papers'.

    🧠 Logic:
    - First, analyze the user input for clarity, scope, and quality.
    - If it's invalid or irrelevant, use detect_out_of_scope_query and return an empty JSON.
    - If it’s vague, use reformulate_query.
    - If it’s too narrow or no good results were found previously, use retry_broaden.
    - If it’s already suitable, use accept.
    - Once a valid and optimized query is available, always run update_papers, then get_best_papers and finally store_papers_for_project.
    - Do not fabricate paper content. Only use output from get_best_papers.

    💬 Output Format:
    Summarize your actions in a message
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
