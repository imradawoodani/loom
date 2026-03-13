"""
Providers — all models through DigitalOcean Gradient.

One API key. One endpoint. All models.
https://inference.do-ai.run/v1  (OpenAI-compatible)

Covers: Anthropic Claude, OpenAI GPT, Meta Llama, Mistral, and more.
"""
import os
from openai import OpenAI

DO_API_KEY  = os.environ.get("DO_API_KEY", "")
DO_ENDPOINT = "https://inference.do-ai.run/v1"

_client = OpenAI(api_key=DO_API_KEY, base_url=DO_ENDPOINT)


def call(model_spec: dict, system_prompt: str, user_message: str,
         max_tokens: int = 1500) -> tuple[str, int]:
    """
    Call any model through DigitalOcean Gradient.
    Returns (response_text, tokens_used).
    """
    resp = _client.chat.completions.create(
        model=model_spec["model_id"],
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
    )
    text   = resp.choices[0].message.content
    tokens = resp.usage.total_tokens if resp.usage else 800
    return text, tokens


def provider_available(provider: str) -> bool:
    """All providers are available through DO — always True if key is set."""
    return bool(DO_API_KEY)
