"""
Groq API client — reusable functions for all agents.

The project continues to use the Groq API.
Only the model ID has been updated because the previous
Groq model IDs are no longer available.
"""

import os

from groq import Groq
from dotenv import load_dotenv


# Load variables from .env
load_dotenv()


# ---------------------------------------------------------------------------
# Groq model configuration
# ---------------------------------------------------------------------------

DEFAULT_MODEL = "openai/gpt-oss-20b"

STREAMING_MODEL = "openai/gpt-oss-20b"


# ---------------------------------------------------------------------------
# Groq client
# ---------------------------------------------------------------------------

_client = None


def get_client() -> Groq:
    """
    Create and return the Groq API client.

    The API key is loaded from:
        GROQ_API_KEY

    The key should be stored in the project's .env file.
    """

    global _client

    if _client is None:

        api_key = os.environ.get("GROQ_API_KEY")

        if not api_key:

            raise ValueError(
                "GROQ_API_KEY not found.\n\n"
                "Please make sure your .env file contains:\n"
                "GROQ_API_KEY=your_groq_api_key"
            )

        _client = Groq(
            api_key=api_key
        )

    return _client


# ---------------------------------------------------------------------------
# Normal Groq request
# ---------------------------------------------------------------------------

def call_groq(
    system_prompt: str,
    user_prompt: str,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.1,
    max_tokens: int = 2048,
) -> str:
    """
    Send a normal request to Groq.

    Returns:
        Complete response as a string.
    """

    client = get_client()

    response = client.chat.completions.create(

        model=model,

        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],

        temperature=temperature,

        max_tokens=max_tokens,
    )

    return response.choices[0].message.content.strip()


# ---------------------------------------------------------------------------
# Streaming Groq request
# ---------------------------------------------------------------------------

def stream_groq(
    system_prompt: str,
    user_prompt: str,
    model: str = STREAMING_MODEL,
    temperature: float = 0.3,
    max_tokens: int = 1024,
):
    """
    Send a streaming request to Groq.

    Yields response text chunks as they arrive.
    """

    client = get_client()

    stream = client.chat.completions.create(

        model=model,

        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],

        temperature=temperature,

        max_tokens=max_tokens,

        stream=True,
    )

    for chunk in stream:

        if not chunk.choices:
            continue

        delta = chunk.choices[0].delta.content

        if delta:
            yield delta