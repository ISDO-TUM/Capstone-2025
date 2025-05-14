from langchain_openai import ChatOpenAI

API_KEY = ""
llm_41 = ChatOpenAI(
    api_key=API_KEY,
    model="gpt-4.1",
    temperature=0,
)
LLM = llm_41
