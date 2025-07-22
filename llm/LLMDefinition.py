"""
LLM model configuration and instantiation for the Capstone project.

Responsibilities:
- Loads OpenAI API key from environment
- Instantiates multiple ChatOpenAI models (GPT-4.1, GPT-4, etc.)
- Exposes the default LLM instance for use throughout the codebase
"""

import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")

# GPT-4.1 model with moderate temperature (default for most agent flows)
llm_41 = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    model="gpt-4.1",
    temperature=0.3,
)

# GPT-4 model with zero temperature (for deterministic outputs)
llm_40 = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    model="gpt-4",
    temperature=0,
)

# GPT-4.1 model with moderate temperature (alternative instance)
llm_4o = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    model="gpt-4.1",
    temperature=0.3,
)

# Default LLM used throughout the codebase
LLM = llm_41
