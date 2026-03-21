"""Mistral AI API wrapper (no SDK required).

Uses the Mistral REST API (OpenAI-compatible schema) with `requests`.
Reads key from env ``MISTRAL_API_KEY`` or Streamlit Secrets, or accepts an
explicit key at call time.

Default model: mistral-small-latest  (low-latency, sufficient for interviews)
Override with env var MISTRAL_MODEL.
"""

from __future__ import annotations

import os
from typing import Optional

import requests

# ── Constants ─────────────────────────────────────────────────────────────────
_BASE_URL    = "https://api.mistral.ai/v1"
_DEFAULT_KEY = "UbMxDfEkugDvgdDhQiT81AphMcJFdLpA"
_MODELS = [
    "mistral-small-latest",
    "mistral-medium-latest",
    "mistral-large-latest",
    "open-mistral-7b",
    "open-mixtral-8x7b",
]


# ── Key resolution ─────────────────────────────────────────────────────────────
def _get_api_key(explicit_key: Optional[str] = None) -> str:
    key = (
        explicit_key
        or os.getenv("MISTRAL_API_KEY")
    )

    if not key:
        try:
            import streamlit as st  # type: ignore
            key = (
                st.secrets.get("MISTRAL_API_KEY")
                or st.secrets.get("mistral_api_key")
                or st.secrets.get("mistral", {}).get("api_key")
                or ""
            )
        except Exception:
            key = ""

    if not key:
        key = _DEFAULT_KEY  # project-bundled fallback

    key = (key or "").strip()
    if not key:
        raise RuntimeError(
            "Mistral API key not configured. "
            "Set MISTRAL_API_KEY env var, add it to Streamlit Secrets, "
            "or pass api_key= explicitly."
        )
    return key


def _get_model() -> str:
    return os.getenv("MISTRAL_MODEL", "mistral-small-latest")


# ── Core completion ────────────────────────────────────────────────────────────
def chat_complete(
    messages: list[dict[str, str]],
    *,
    model: Optional[str] = None,
    temperature: float = 0.4,
    max_tokens: int = 600,
    api_key: Optional[str] = None,
) -> str:
    """Call Mistral /chat/completions and return the assistant reply text."""
    key     = _get_api_key(api_key)
    mdl     = model or _get_model()
    url     = _BASE_URL.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = {
        "model":       mdl,
        "messages":    messages,
        "temperature": temperature,
        "max_tokens":  max_tokens,
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
    except requests.exceptions.Timeout:
        raise RuntimeError("Mistral API request timed out after 60 s.")
    except requests.exceptions.ConnectionError as exc:
        raise RuntimeError(f"Could not connect to Mistral API: {exc}") from exc

    if resp.status_code == 401:
        raise RuntimeError("Mistral API key is invalid or expired (401).")
    if resp.status_code == 429:
        raise RuntimeError("Mistral API rate-limit reached (429). Please retry in a moment.")
    if resp.status_code >= 400:
        try:
            msg = resp.json().get("message") or resp.json().get("error") or resp.text
        except Exception:
            msg = resp.text
        raise RuntimeError(f"Mistral API error ({resp.status_code}): {msg}")

    try:
        data    = resp.json()
        choices = data.get("choices") or []
        if not choices:
            raise ValueError("Empty 'choices' in Mistral response.")
        return choices[0]["message"]["content"]
    except (KeyError, IndexError, ValueError) as exc:
        raise RuntimeError(f"Unexpected Mistral response format: {exc}\n{resp.text[:400]}") from exc


# ── Optional: list available models ───────────────────────────────────────────
def list_models(*, api_key: Optional[str] = None) -> list[str]:
    """Return a list of model IDs available under the given key."""
    key  = _get_api_key(api_key)
    url  = _BASE_URL.rstrip("/") + "/models"
    headers = {"Authorization": f"Bearer {key}", "Accept": "application/json"}
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        return [m["id"] for m in resp.json().get("data", [])]
    except Exception:
        return _MODELS  # return known list on failure
