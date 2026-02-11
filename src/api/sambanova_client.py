"""SambaNova.ai API wrapper (no SDK required).

This is implemented as an OpenAI-compatible HTTP client by default.

Configuration (env vars or Streamlit Secrets):
- SAMBANOVA_API_KEY: API key / token (required)
- SAMBANOVA_BASE_URL: default https://api.sambanova.ai
- SAMBANOVA_MODEL: default "Meta-Llama-3.1-70B-Instruct" (override as needed)
- SAMBANOVA_EXTRA_HEADERS_JSON: optional JSON object of extra headers
  (useful if your account requires project/org headers)

Secrets keys supported:
- SAMBANOVA_API_KEY
- sambanova.api_key
- sambanova.base_url
- sambanova.model
- sambanova.extra_headers_json
"""

from __future__ import annotations

import json
import os
from typing import Optional

import requests


def _get_secret(name: str) -> Optional[str]:
    try:
        import streamlit as st  # type: ignore

        return st.secrets.get(name)
    except Exception:
        return None


def _get_api_key(explicit_key: Optional[str] = None) -> str:
    api_key = explicit_key or os.getenv("SAMBANOVA_API_KEY") or _get_secret("SAMBANOVA_API_KEY")
    if not api_key:
        try:
            import streamlit as st  # type: ignore

            api_key = st.secrets.get("sambanova", {}).get("api_key")
        except Exception:
            api_key = None

    if not api_key:
        raise RuntimeError(
            "SambaNova API key not configured. Set SAMBANOVA_API_KEY (env var) or add it to Streamlit Secrets."
        )
    return api_key.strip() if isinstance(api_key, str) else api_key


def _get_base_url() -> str:
    return (
        os.getenv("SAMBANOVA_BASE_URL")
        or _get_secret("SAMBANOVA_BASE_URL")
        or _get_secret("sambanova_base_url")
        or "https://api.sambanova.ai"
    )


def _get_model() -> str:
    return (
        os.getenv("SAMBANOVA_MODEL")
        or _get_secret("SAMBANOVA_MODEL")
        or _get_secret("sambanova_model")
        or "Meta-Llama-3.1-70B-Instruct"
    )


def _get_extra_headers() -> dict[str, str]:
    raw = (
        os.getenv("SAMBANOVA_EXTRA_HEADERS_JSON")
        or _get_secret("SAMBANOVA_EXTRA_HEADERS_JSON")
        or _get_secret("sambanova_extra_headers_json")
    )

    if not raw:
        try:
            import streamlit as st  # type: ignore

            raw = st.secrets.get("sambanova", {}).get("extra_headers_json")
        except Exception:
            raw = None

    if not raw:
        return {}

    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return {str(k): str(v) for k, v in data.items()}
    except Exception:
        return {}

    return {}


def chat_complete(
    messages: list[dict[str, str]],
    *,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.4,
    max_tokens: int = 600,
) -> str:
    """Call SambaNova using an OpenAI-compatible chat completions request."""
    api_key = _get_api_key(api_key)
    model = model or _get_model()

    base_url = _get_base_url().rstrip("/")
    url = base_url + "/v1/chat/completions"

    headers: dict[str, str] = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    headers.update(_get_extra_headers())

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
    except Exception as e:  # pragma: no cover
        raise RuntimeError(f"Failed to reach SambaNova API: {e}") from e

    if r.status_code >= 400:
        try:
            msg = r.json().get("error", {}).get("message") or r.text
        except Exception:
            msg = r.text
        raise RuntimeError(f"SambaNova API error ({r.status_code}): {msg}")

    try:
        data = r.json()
        return (data["choices"][0]["message"]["content"] or "").strip()
    except Exception as e:
        raise RuntimeError(f"Unexpected SambaNova response format: {e}") from e
