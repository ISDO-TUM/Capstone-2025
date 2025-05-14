from dotenv import load_dotenv
import os
from langchain_openai import ChatOpenAI

load_dotenv() #loads variables from .env
API_KEY = os.getenv("OPEN_AI_KEY")
llm_41 = ChatOpenAI(
    api_key = API_KEY,
    model="gpt-4.1",
    temperature=0,
)
LLM = llm_41
