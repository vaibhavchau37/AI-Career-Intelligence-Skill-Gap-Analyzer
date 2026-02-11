"""LLM routing utilities.

Provides a single chat_complete() that can use OpenAI or Gemini.
"""

from __future__ import annotations

from typing import Optional


def chat_complete(
    provider: str,
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.4,
    max_tokens: int = 600,
) -> str:
    provider_norm = (provider or "").strip().lower()

    if provider_norm in {"openai", "gpt"}:
        from src.api.openai_client import chat_complete as openai_chat

        return openai_chat(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    if provider_norm in {"gemini", "google"}:
        from src.api.gemini_client import chat_complete as gemini_chat

        return gemini_chat(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    if provider_norm in {"sambanova", "sn"}:
        from src.api.sambanova_client import chat_complete as sn_chat

        return sn_chat(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    raise RuntimeError("Unknown AI provider. Use 'OpenAI', 'Gemini', or 'SambaNova'.")
