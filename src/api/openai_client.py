"""OpenAI Chat API wrapper.

This project treats OpenAI usage as optional.
- Uses `OPENAI_API_KEY` from environment.
- Supports OpenAI Python SDK v1.x.

All functions raise RuntimeError with a clear message when unavailable.
"""

from __future__ import annotations

import os
from typing import Any, Optional

import requests


def _get_api_key(explicit_key: Optional[str] = None) -> str:
    api_key = explicit_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        # Optional: Streamlit Cloud secrets support
        try:
            import streamlit as st  # type: ignore

            api_key = (
                st.secrets.get("OPENAI_API_KEY")
                or st.secrets.get("openai", {}).get("api_key")
                or st.secrets.get("openai_api_key")
            )
        except Exception:
            api_key = None
    if not api_key:
        raise RuntimeError(
            "OpenAI API key not configured. Set OPENAI_API_KEY (env var) or add it to Streamlit Secrets."
        )
    return api_key.strip() if isinstance(api_key, str) else api_key


def _get_model() -> str:
    return os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def chat_complete(
    messages: list[dict[str, str]],
    *,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.4,
    max_tokens: int = 600,
) -> str:
    """Call OpenAI chat completions API and return assistant text."""
    api_key = _get_api_key(api_key)
    model = model or _get_model()

    # Prefer OpenAI SDK v1.x if installed; otherwise fall back to HTTPS.
    try:
        from openai import OpenAI  # type: ignore

        client = OpenAI(api_key=api_key)
        resp: Any = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return (resp.choices[0].message.content or "").strip()
    except ImportError:
        pass
    except Exception as e:
        # If SDK is installed but failed (auth, quota, etc.), surface the real error.
        raise RuntimeError(str(e)) from e

    # HTTPS fallback (no SDK needed)
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")
    url = base_url.rstrip("/") + "/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
    except Exception as e:  # pragma: no cover
        raise RuntimeError(f"Failed to reach OpenAI API: {e}") from e

    if r.status_code >= 400:
        # Try to extract structured API errors
        try:
            err = r.json().get("error", {})
            msg = err.get("message") or r.text
        except Exception:
            msg = r.text
        raise RuntimeError(f"OpenAI API error ({r.status_code}): {msg}")

    try:
        data = r.json()
        return (data["choices"][0]["message"]["content"] or "").strip()
    except Exception as e:
        raise RuntimeError(f"Unexpected OpenAI response format: {e}") from e
