from langchain_groq import ChatGroq
from app.config import settings

def get_llm(temperature: float = 0):
    return ChatGroq(
        model=settings.GROQ_MODEL,
        api_key=settings.GROQ_API_KEY,
        temperature=temperature,
        max_retries=2,
    )
