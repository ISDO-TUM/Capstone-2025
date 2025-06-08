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
  Your task is to analyze the user's research interests and use your available tools to query papers titles
  and then select the most relevant ones. You have a variety of tools that let you download papers in relation
  to the user interests and to organize them to rank them.

  These tools are: update_papers and get_best_papers
  Run the first one to update the database and the second one to get the best papers in relation to the user's interests.

  As we are now in development always run the 2 tools. First update_papers, then get_best_papers.
  Use the result of get_best_papers to build you response.

  Do not make up paper names that are not returned by get_best_papers. If get_best_papers does not return any papers return an empty JSON.

  You do not talk directly to the user, you only send a JSON to the frontend.

  Return your recommendations in a JSON with the following fields:
    -papers: A list of the papers retuned by get_best_papers. This field has following subfields
        -Title: The paper's title.
        -Link: The paper's URL.
        -Description: The paper's description. Generate this based on the paper's abstract and the provided user profile.
        It should be concise and precise, describing exactly why this is a perfect match for the user and what the key
         findings are in a manner that makes the user interested to click it.


    Example:
    {
        "papers" : {
            {
                "title" : "XYZ",
                "link" : "http://example.com/XYZ",
                "description" : "",
            },
            {
                "title" : "ABC",
                "link" : "http://example.com/ABC",
                "description" : "",
            },
            ...
        }
    }
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
