"""
JWT Handler — create and verify JSON Web Tokens.

Priority for secret key:
    1. JWT_SECRET_KEY env var
    2. Streamlit secrets (jwt_secret_key)
    3. Hard-coded development fallback (not for production)
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

try:
    import jwt as _jwt
    _HAS_JWT = True
except ImportError:
    _HAS_JWT = False

_DEV_SECRET  = "career_analyzer_jwt_dev_secret_change_in_production_2024"
_ALGORITHM   = "HS256"
_EXPIRE_MINS = 60 * 24  # 24 hours


def _get_secret() -> str:
    key = os.getenv("JWT_SECRET_KEY", "")
    if not key:
        try:
            import streamlit as st
            key = st.secrets.get("JWT_SECRET_KEY", "") or ""
        except Exception:
            pass
    return key or _DEV_SECRET


def create_access_token(data: Dict[str, Any],
                        expires_delta: Optional[timedelta] = None) -> str:
    """Return a signed JWT string encoding *data*."""
    if not _HAS_JWT:
        raise ImportError("PyJWT is not installed. Run: pip install PyJWT")

    payload = data.copy()
    expire  = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=_EXPIRE_MINS)
    )
    payload["exp"] = expire
    payload["iat"] = datetime.now(timezone.utc)
    return _jwt.encode(payload, _get_secret(), algorithm=_ALGORITHM)


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and verify a JWT token.

    Returns the payload dict on success, or None if invalid/expired.
    """
    if not _HAS_JWT:
        return None
    try:
        return _jwt.decode(token, _get_secret(), algorithms=[_ALGORITHM])
    except _jwt.ExpiredSignatureError:
        return None
    except _jwt.InvalidTokenError:
        return None


def verify_token_payload(token: str) -> Optional[Dict[str, Any]]:
    """Alias for decode_access_token — returns payload or None."""
    return decode_access_token(token)
