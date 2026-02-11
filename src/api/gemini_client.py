"""Gemini API wrapper (no SDK required).

Uses Google Generative Language REST API with `requests`.
Reads key from env `GOOGLE_GEMINI_API_KEY` or Streamlit Secrets.

This keeps the app working on Streamlit Cloud without extra dependencies.
"""

from __future__ import annotations

import os
from typing import Optional
from urllib.parse import quote

import requests


def _get_api_key(explicit_key: Optional[str] = None) -> str:
    api_key = explicit_key or os.getenv("GOOGLE_GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        try:
            import streamlit as st  # type: ignore

            api_key = (
                st.secrets.get("GOOGLE_GEMINI_API_KEY")
                or st.secrets.get("GEMINI_API_KEY")
                or st.secrets.get("gemini", {}).get("api_key")
                or st.secrets.get("google_gemini_api_key")
            )
        except Exception:
            api_key = None

    if isinstance(api_key, str):
        api_key = api_key.strip()

    if not api_key:
        raise RuntimeError(
            "Gemini API key not configured. Set GOOGLE_GEMINI_API_KEY (env var) or add it to Streamlit Secrets."
        )
    return api_key


def _get_model() -> str:
    # Common fast default; can be overridden.
    # Note: availability varies by account/API version; we auto-fallback if needed.
    return os.getenv("GEMINI_MODEL", "gemini-1.5-flash")


def _normalize_model_id(model: str) -> str:
    """Accept either 'gemini-...' or 'models/gemini-...' and return the ID part."""
    m = (model or "").strip()
    if m.startswith("models/"):
        return m[len("models/") :]
    return m


def list_models(*, api_key: Optional[str] = None) -> list[dict]:
    """List available Gemini models and their supported methods."""
    api_key = _get_api_key(api_key)
    base_url = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com")
    url = base_url.rstrip("/") + "/v1beta/models?key=" + quote(api_key)

    r = requests.get(url, timeout=60)
    if r.status_code >= 400:
        try:
            msg = r.json().get("error", {}).get("message") or r.text
        except Exception:
            msg = r.text
        raise RuntimeError(f"Gemini ListModels error ({r.status_code}): {msg}")

    try:
        data = r.json()
        models = data.get("models", [])
        return models if isinstance(models, list) else []
    except Exception as e:
        raise RuntimeError(f"Unexpected Gemini ListModels response format: {e}") from e


def _pick_fallback_model(models: list[dict]) -> Optional[str]:
    """Pick a model that supports generateContent."""
    candidates: list[str] = []
    for m in models:
        if not isinstance(m, dict):
            continue
        name = m.get("name")
        methods = m.get("supportedGenerationMethods")
        if not isinstance(name, str):
            continue
        if isinstance(methods, list) and "generateContent" in methods:
            candidates.append(_normalize_model_id(name))

    if not candidates:
        return None

    # Prefer lightweight/fast models when available.
    preferred_prefixes = [
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-1.0-pro",
    ]
    for pref in preferred_prefixes:
        for c in candidates:
            if c.startswith(pref):
                return c
    return candidates[0]


def chat_complete(
    messages: list[dict[str, str]],
    *,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.4,
    max_tokens: int = 600,
) -> str:
    """Generate a single assistant response from chat-style messages."""
    api_key = _get_api_key(api_key)
    model = _normalize_model_id(model or _get_model())

    # Convert messages to a single prompt (simple + robust).
    lines: list[str] = []
    for m in messages:
        role = (m.get("role") or "user").upper()
        content = m.get("content") or ""
        lines.append(f"{role}: {content}")
    prompt = "\n\n".join(lines)

    base_url = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com")
    def _make_url(model_id: str) -> str:
        return (
            base_url.rstrip("/")
            + "/v1beta/models/"
            + quote(_normalize_model_id(model_id))
            + ":generateContent?key="
            + quote(api_key)
        )

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}],
            }
        ],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        },
    }

    url = _make_url(model)

    def _post(u: str) -> requests.Response:
        try:
            return requests.post(u, json=payload, timeout=60)
        except Exception as e:  # pragma: no cover
            raise RuntimeError(f"Failed to reach Gemini API: {e}") from e

    r = _post(url)

    if r.status_code == 404:
        # Auto-fallback when a model isn't available for this key/API version.
        try:
            msg = r.json().get("error", {}).get("message") or r.text
        except Exception:
            msg = r.text
        if "models/" in msg or "Call ListModels" in msg or "not found" in msg.lower():
            models = list_models(api_key=api_key)
            fallback = _pick_fallback_model(models)
            if fallback and fallback != model:
                r = _post(_make_url(fallback))
                model = fallback

    if r.status_code >= 400:
        try:
            msg = r.json().get("error", {}).get("message") or r.text
        except Exception:
            msg = r.text
        raise RuntimeError(f"Gemini API error ({r.status_code}): {msg}")

    try:
        data = r.json()
        return (
            data["candidates"][0]["content"]["parts"][0]["text"]
        ).strip()
    except Exception as e:
        raise RuntimeError(f"Unexpected Gemini response format: {e}") from e
