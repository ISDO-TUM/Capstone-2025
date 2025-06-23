import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
# API_KEY = "" Use this in case you weren't able to set the api key as an environment variable
llm_41 = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    model="gpt-4.1",
    temperature=0,
)

llm_40 = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    model="gpt-4",
    temperature=0,
)

llm_4o = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    model="gpt-4.1",
    temperature=0.3,
)
LLM = llm_41
