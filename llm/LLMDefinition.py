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
    raise ValueError(
        "OpenAI API key not found. Please set the OPENAI_API_KEY environment variable."
    )

# A dictionary to hold all the instantiated models
_models = {
    "gpt-5.1": ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model="gpt-5.1",
        temperature=0.3,
    ),
    "gpt-5": ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model="gpt-5",
        temperature=0.3,
    ),
    "gpt-5-mini": ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model="gpt-5-mini",
        temperature=0.3,
    ),
    "gpt-5-nano": ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model="gpt-5-nano",
        temperature=0.3,
    ),
}

<<<<<<< HEAD
LLM = llm_41
=======
# Default LLM used throughout the codebase
LLM = _models["gpt-5.1"]


def get_llm(model_name: str):
    """
    Returns an LLM instance by model name.
    Args:
        model_name (str): The name of the model to return.
    Returns:
        ChatOpenAI: The LLM instance.
    """
    return _models.get(model_name)


def set_default_llm(model_name: str):
    """
    Sets the default LLM instance.
    Args:
        model_name (str): The name of the model to set as default.
    """
    global LLM
    llm_instance = get_llm(model_name)
    if llm_instance:
        LLM = llm_instance
    else:
        raise ValueError(f"Model '{model_name}' not found.")


def get_available_models():
    """
    Returns a list of available model names.
    """
    return list(_models.keys())
>>>>>>> e7642dd (Keyword Evaluation - Dataset Generation)
