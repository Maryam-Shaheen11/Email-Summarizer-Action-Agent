import os
from crewai import LLM

MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

def get_llm():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not configured.")
    return LLM(
        model=f"groq/{MODEL}",
        api_key=api_key,
        temperature=0.1,
    )
