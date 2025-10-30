from langchain_openai import ChatOpenAI
from config import settings

llm = ChatOpenAI(
    model="gpt-4.1-mini",
    # model="gpt-5-nano", reasoning model
    api_key=settings.OPENAI_API_KEY
   
)

