import os
from groq import Groq
from app.core.config import GROQ_API_KEY, LLM_MODEL, LLM_TEMPERATURE

# Global variable to cache the Groq client
_global_groq_client = None

def get_groq_client():
    global _global_groq_client
    if _global_groq_client is None:
        api_key = GROQ_API_KEY or os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY is not set. Please add it to your .env file.")
        _global_groq_client = Groq(api_key=api_key)
    return _global_groq_client


def generate_response(prompt: str, system_prompt: str = None, history: list = None) -> str:
    """
    Generate response using Groq API, with support for conversation history.
    """
    client = get_groq_client()

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    
    # Append conversation history
    if history:
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": prompt})

    chat_completion = client.chat.completions.create(
        messages=messages,
        model=LLM_MODEL,
        temperature=LLM_TEMPERATURE,
    )

    return chat_completion.choices[0].message.content
