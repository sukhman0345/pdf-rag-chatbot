import os
from groq import Groq
from app.core.config import GROQ_API_KEY, LLM_MODEL, LLM_TEMPERATURE

def get_groq_client():
    api_key = GROQ_API_KEY or os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is not set. Please add it to your .env file.")
    return Groq(api_key=api_key)


def generate_response(prompt: str, system_prompt: str = None) -> str:
    """
    Generate response using Groq API.
    """
    client = get_groq_client()

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    chat_completion = client.chat.completions.create(
        messages=messages,
        model=LLM_MODEL,
        temperature=LLM_TEMPERATURE,
    )

    return chat_completion.choices[0].message.content
