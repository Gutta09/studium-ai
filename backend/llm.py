"""
Shared LLM access for all agents.

One Groq client, one JSON-mode chat helper, one place to handle provider
errors. Agents stay pure prompt + validation logic.
"""

import json
import logging
import os

from dotenv import load_dotenv
from groq import Groq, GroqError

load_dotenv()

logger = logging.getLogger("studium.llm")

MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


class LLMError(Exception):
    """Raised when the LLM call fails or returns unusable output."""


def chat_json(system: str, user: str, temperature: float = 0.0) -> dict:
    """Call the model in JSON mode and return the parsed object."""
    try:
        response = _client.chat.completions.create(
            model=MODEL,
            temperature=temperature,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
    except GroqError as e:
        logger.error("LLM call failed: %s", e)
        raise LLMError(f"LLM provider error: {e.__class__.__name__}") from e

    content = response.choices[0].message.content
    try:
        return json.loads(content)
    except (json.JSONDecodeError, TypeError) as e:
        logger.error("LLM returned non-JSON output: %.200s", content)
        raise LLMError("LLM returned malformed JSON") from e
