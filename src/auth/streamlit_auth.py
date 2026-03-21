"""
Streamlit Authentication UI
============================

A production-ready, modern authentication interface for Streamlit applications.

Features:
- Beautiful login/signup/forgot password pages
- Session state management
- Remember me functionality
- Responsive design with glassmorphism effects
- Animated transitions and loading states
- Error and success message handling

Usage:
    from src.auth.streamlit_auth import render_auth_page, is_authenticated, logout
    
    if not is_authenticated():
        render_auth_page()
        st.stop()
    
    # User is authenticated, show main app
    user = get_current_user()
    st.write(f"Welcome, {user['name']}!")
"""
from __future__ import annotations

import os
import secrets
import time
from urllib.parse import urlencode
from typing import Any, Dict, Optional

import requests
import streamlit as st

from .auth_database import get_auth_db, AuthDatabase


# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════
_SESSION_USER_KEY = "auth_user"
_SESSION_TOKEN_KEY = "auth_session_token"
_AUTH_PAGE_KEY = "auth_page"  # "login", "signup", "forgot_password", "reset_password"
_RESET_TOKEN_KEY = "reset_token"
_GOOGLE_STATE_KEY = "google_oauth_state"


# ══════════════════════════════════════════════════════════════════════════════
# AUTHENTICATION STATE MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

def is_authenticated() -> bool:
    """Check if user is currently authenticated."""
    # First check session state
    if _SESSION_USER_KEY in st.session_state and st.session_state[_SESSION_USER_KEY]:
        return True
    
    # Check for remember me session token
    session_token = st.session_state.get(_SESSION_TOKEN_KEY)
    if session_token:
        db = get_auth_db()
        user = db.validate_session(session_token)
        if user:
            st.session_state[_SESSION_USER_KEY] = user
            return True
        else:
            # Invalid token, clear it
            st.session_state.pop(_SESSION_TOKEN_KEY, None)
    
    return False


def get_current_user() -> Optional[Dict[str, Any]]:
    """Get the currently authenticated user's data."""
    if is_authenticated():
        return st.session_state.get(_SESSION_USER_KEY)
    return None


def logout():
    """Log out the current user and clear all auth session data."""
    # Invalidate session token if exists
    session_token = st.session_state.get(_SESSION_TOKEN_KEY)
    if session_token:
        db = get_auth_db()
        db.invalidate_session(session_token)
    
    # Clear session state
    st.session_state.pop(_SESSION_USER_KEY, None)
    st.session_state.pop(_SESSION_TOKEN_KEY, None)
    st.session_state.pop(_AUTH_PAGE_KEY, None)
    st.session_state.pop(_RESET_TOKEN_KEY, None)
    
    # Clear any app-specific session data
    keys_to_clear = [
        'resume_data', 'selected_role', 'analysis_results',
        'interview_state', 'roadmap_data'
    ]
    for key in keys_to_clear:
        st.session_state.pop(key, None)


def _set_auth_page(page: str):
    """Set the current authentication page."""
    st.session_state[_AUTH_PAGE_KEY] = page


def _get_auth_page() -> str:
    """Get the current authentication page."""
    return st.session_state.get(_AUTH_PAGE_KEY, "login")


def _get_query_params() -> Dict[str, Any]:
    try:
        raw = dict(st.query_params)
    except Exception:
        raw = st.experimental_get_query_params()

    return {
        key: (value[0] if isinstance(value, list) and value else value)
        for key, value in raw.items()
    }


def _clear_query_params():
    try:
        st.query_params.clear()
    except Exception:
        st.experimental_set_query_params()


def _get_google_oauth_config() -> Optional[Dict[str, str]]:
    client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8501").strip()

    if not client_id or not client_secret:
        return None

    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
    }


def _build_google_auth_url() -> Optional[str]:
    config = _get_google_oauth_config()
    if not config:
        return None

    state = st.session_state.get(_GOOGLE_STATE_KEY)
    if not state:
        state = secrets.token_urlsafe(24)
        st.session_state[_GOOGLE_STATE_KEY] = state

    params = {
        "client_id": config["client_id"],
        "redirect_uri": config["redirect_uri"],
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "online",
        "prompt": "select_account",
        "state": state,
    }

    return "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)


def _handle_google_callback() -> None:
    config = _get_google_oauth_config()
    if not config:
        return

    params = _get_query_params()
    if not params:
        return

    code = params.get("code")
    state = params.get("state")
    error = params.get("error")

    if error:
        _clear_query_params()
        _render_message("Google sign-in was canceled.", "info")
        return

    if not code:
        return

    expected_state = st.session_state.get(_GOOGLE_STATE_KEY)
    if expected_state and state and state != expected_state:
        _clear_query_params()
        _render_message("Google sign-in failed. Please try again.", "error")
        return

    token_response = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": config["client_id"],
            "client_secret": config["client_secret"],
            "redirect_uri": config["redirect_uri"],
            "grant_type": "authorization_code",
        },
        timeout=10,
    )

    if token_response.status_code != 200:
        _clear_query_params()
        _render_message("Google sign-in failed. Please try again.", "error")
        return

    token_payload = token_response.json()
    id_token = token_payload.get("id_token")
    if not id_token:
        _clear_query_params()
        _render_message("Google sign-in failed. Missing ID token.", "error")
        return

    info_response = requests.get(
        "https://oauth2.googleapis.com/tokeninfo",
        params={"id_token": id_token},
        timeout=10,
    )

    if info_response.status_code != 200:
        _clear_query_params()
        _render_message("Google sign-in failed. Please try again.", "error")
        return

    info = info_response.json()
    email = info.get("email", "")
    name = info.get("name") or info.get("given_name") or "User"
    provider_id = info.get("sub", "")
    email_verified = str(info.get("email_verified", "false")).lower() == "true"

    db = get_auth_db()
    result = db.get_or_create_oauth_user(
        email=email,
        name=name,
        provider="google",
        provider_id=provider_id,
        email_verified=email_verified,
    )

    _clear_query_params()

    if result.get("success"):
        st.session_state[_SESSION_USER_KEY] = result["user"]
        st.rerun()
    else:
        _render_message(result.get("message", "Google sign-in failed."), "error")


# ══════════════════════════════════════════════════════════════════════════════
# CSS STYLES FOR AUTHENTICATION UI
# ══════════════════════════════════════════════════════════════════════════════

AUTH_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* ═══════════════════════════════════════════════════
   HIDE STREAMLIT DEFAULTS ON AUTH PAGE
═══════════════════════════════════════════════════ */
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stHeader"] { display: none !important; }

/* ═══════════════════════════════════════════════════
   ANIMATED BACKGROUND
═══════════════════════════════════════════════════ */
[data-testid="stAppViewContainer"] {
    background: #050608 !important;
}

[data-testid="stAppViewContainer"]::before {
    content: "";
    position: fixed;
    inset: 0;
    z-index: 0;
    pointer-events: none;
    background: 
        radial-gradient(ellipse 80% 50% at 20% -20%, rgba(99, 102, 241, 0.15) 0%, transparent 50%),
        radial-gradient(ellipse 60% 40% at 80% 0%, rgba(6, 182, 212, 0.1) 0%, transparent 50%),
        radial-gradient(ellipse 50% 30% at 50% 100%, rgba(139, 92, 246, 0.08) 0%, transparent 50%);
    animation: aurora 15s ease-in-out infinite alternate;
}

@keyframes aurora {
    0% { opacity: 1; transform: scale(1) rotate(0deg); }
    50% { opacity: 0.8; }
    100% { opacity: 1; transform: scale(1.1) rotate(2deg); }
}

/* Floating orbs animation */
.auth-bg-orb {
    position: fixed;
    border-radius: 50%;
    filter: blur(60px);
    opacity: 0.4;
    animation: float 20s ease-in-out infinite;
    z-index: 0;
    pointer-events: none;
}

.auth-bg-orb-1 {
    width: 400px; height: 400px;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    top: -100px; left: -100px;
    animation-delay: 0s;
}

.auth-bg-orb-2 {
    width: 300px; height: 300px;
    background: linear-gradient(135deg, #06b6d4, #0ea5e9);
    bottom: -50px; right: -50px;
    animation-delay: -7s;
}

.auth-bg-orb-3 {
    width: 200px; height: 200px;
    background: linear-gradient(135deg, #10b981, #059669);
    top: 50%; right: 10%;
    animation-delay: -14s;
}

@keyframes float {
    0%, 100% { transform: translate(0, 0) scale(1); }
    25% { transform: translate(30px, -30px) scale(1.05); }
    50% { transform: translate(-20px, 20px) scale(0.95); }
    75% { transform: translate(20px, 30px) scale(1.02); }
}

@keyframes card-3d-float {
    0%, 100% { transform: perspective(1400px) rotateX(1.4deg) rotateY(-1.4deg) translateY(0px); }
    50% { transform: perspective(1400px) rotateX(-1.2deg) rotateY(1.4deg) translateY(-8px); }
}

@keyframes symbol-3d-orbit {
    0%, 100% { transform: translateY(0px) rotateZ(0deg) scale(1); }
    50% { transform: translateY(-6px) rotateZ(2deg) scale(1.03); }
}

@keyframes holo-scan {
    0% { transform: translateX(-120%); opacity: 0; }
    30% { opacity: 0.45; }
    65% { opacity: 0.22; }
    100% { transform: translateX(120%); opacity: 0; }
}

@keyframes neon-breathe {
    0%, 100% { box-shadow: 0 0 0 1px rgba(14, 165, 233, 0.2), 0 0 18px rgba(14, 165, 233, 0.16); }
    50% { box-shadow: 0 0 0 1px rgba(14, 165, 233, 0.35), 0 0 30px rgba(14, 165, 233, 0.28); }
}

/* ═══════════════════════════════════════════════════
   AUTH CONTAINER & CARD
═══════════════════════════════════════════════════ */
.auth-wrapper {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    z-index: 1;
    padding: 40px 20px;
}

.auth-container {
    width: 100%;
    max-width: 440px;
    margin: 28px auto 40px auto;
    display: flex;
    flex-direction: column;
    align-items: center;
    perspective: 1400px;
}

.auth-card {
    width: 100%;
    background: rgba(15, 15, 20, 0.6);
    backdrop-filter: blur(40px) saturate(150%);
    -webkit-backdrop-filter: blur(40px) saturate(150%);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 22px;
    padding: 40px 36px 44px 36px;
    box-shadow: 
        0 0 0 1px rgba(255, 255, 255, 0.03),
        0 25px 50px -12px rgba(0, 0, 0, 0.8),
        0 0 100px rgba(99, 102, 241, 0.1),
        inset 0 1px 0 rgba(255, 255, 255, 0.04);
    position: relative;
    overflow: hidden;
    transform-style: preserve-3d;
    animation: card-3d-float 8.5s ease-in-out infinite;
    transition: transform 0.35s ease, box-shadow 0.35s ease;
}

.auth-card:hover {
    transform: perspective(1400px) rotateX(0.5deg) rotateY(-0.5deg) translateY(-4px) scale(1.005);
    box-shadow:
        0 0 0 1px rgba(255, 255, 255, 0.05),
        0 35px 60px -18px rgba(0, 0, 0, 0.85),
        0 0 130px rgba(99, 102, 241, 0.16),
        inset 0 1px 0 rgba(255, 255, 255, 0.06);
}

/* Top gradient line */
.auth-card::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(90deg, 
        transparent 0%, 
        #6366f1 20%, 
        #06b6d4 50%, 
        #10b981 80%, 
        transparent 100%);
    opacity: 0.8;
}

/* Subtle glow effect */
.auth-card::after {
    content: "";
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(
        ellipse at center,
        rgba(99, 102, 241, 0.03) 0%,
        transparent 70%
    );
    pointer-events: none;
}

/* ═══════════════════════════════════════════════════
   LOGO SECTION
═══════════════════════════════════════════════════ */
.auth-logo {
    text-align: center;
    margin-bottom: 24px;
    position: relative;
    z-index: 1;
    max-width: 860px;
    margin-left: auto;
    margin-right: auto;
}

.auth-hover-brand {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 14px;
    width: 100%;
    transform-style: preserve-3d;
}

.auth-hover-symbol {
    order: -1;
    width: 88px;
    height: 88px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: radial-gradient(circle at 30% 30%, rgba(34, 211, 238, 0.22), rgba(59, 130, 246, 0.2) 55%, rgba(2, 6, 23, 0.2) 100%);
    border: 2px solid rgba(34, 211, 238, 0.8);
    box-shadow:
        0 0 0 5px rgba(14, 165, 233, 0.14),
        0 0 22px rgba(56, 189, 248, 0.35);
    transition: transform 0.25s ease, box-shadow 0.25s ease;
    animation: symbol-3d-orbit 4.2s ease-in-out infinite;
    position: relative;
}

.auth-hover-symbol::after {
    content: "";
    position: absolute;
    inset: -14px;
    border-radius: 50%;
    border: 1px solid rgba(34, 211, 238, 0.35);
    transform: translateZ(0);
    animation: neon-breathe 3.4s ease-in-out infinite;
    pointer-events: none;
}

.auth-hover-symbol svg {
    width: 40px;
    height: 40px;
    opacity: 0.95;
}

.auth-hover-title-bar {
    display: none !important;
}

.auth-brand-name-pill {
    width: 100%;
    max-width: 840px;
    min-height: 74px;
    border-radius: 28px;
    border: 1px solid rgba(148, 163, 184, 0.18);
    background: linear-gradient(120deg, rgba(15, 23, 42, 0.72), rgba(17, 24, 39, 0.6));
    box-shadow:
        inset 0 1px 0 rgba(148, 163, 184, 0.15),
        0 0 0 1px rgba(30, 41, 59, 0.45),
        0 14px 40px rgba(2, 6, 23, 0.45);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 14px 26px;
    position: relative;
    overflow: hidden;
    transition: border-color 0.25s ease, box-shadow 0.25s ease;
    transform: translateZ(0);
    transform-style: preserve-3d;
}

/* Force strict order: symbol first, name pill second */
.auth-hover-brand > .auth-hover-symbol {
    order: 1 !important;
}

.auth-hover-brand > .auth-brand-name-pill {
    order: 2 !important;
    display: flex !important;
}

.auth-brand-name-pill::before {
    content: "";
    position: absolute;
    inset: 0;
    pointer-events: none;
    background: linear-gradient(90deg, rgba(37, 99, 235, 0) 0%, rgba(34, 211, 238, 0.2) 50%, rgba(37, 99, 235, 0) 100%);
    opacity: 0;
    transition: opacity 0.25s ease;
}

.auth-brand-name-pill::after {
    content: "";
    position: absolute;
    top: 0;
    bottom: 0;
    width: 34%;
    background: linear-gradient(90deg, rgba(34, 211, 238, 0), rgba(34, 211, 238, 0.25), rgba(34, 211, 238, 0));
    filter: blur(0.6px);
    animation: holo-scan 5.2s linear infinite;
    pointer-events: none;
}

.auth-brand-name-pill:hover {
    border-color: rgba(34, 211, 238, 0.42);
    box-shadow:
        inset 0 1px 0 rgba(186, 230, 253, 0.24),
        0 0 0 1px rgba(14, 165, 233, 0.35),
        0 0 26px rgba(14, 165, 233, 0.22),
        0 14px 40px rgba(2, 6, 23, 0.45);
}

.auth-brand-name-pill:hover::before {
    opacity: 1;
}

.auth-hover-title {
    display: block;
    margin: 0;
    text-align: center;
    font-size: 1.26rem;
    line-height: 1.3;
    letter-spacing: 0.4px;
    color: #e2e8f0 !important;
    background: none !important;
    -webkit-text-fill-color: #e2e8f0 !important;
    font-weight: 700;
    position: relative;
    z-index: 1;
    text-shadow: 0 0 16px rgba(56, 189, 248, 0.24);
}

.auth-hover-brand:hover .auth-hover-symbol {
    transform: translateY(-4px) scale(1.05) rotateZ(2deg);
    box-shadow:
        0 0 0 5px rgba(14, 165, 233, 0.2),
        0 0 28px rgba(34, 211, 238, 0.4);
}

.logo-icon-wrapper {
    width: 72px;
    height: 72px;
    margin: 0 auto 16px auto;
    position: relative;
    animation: logo-float 4s ease-in-out infinite;
}

.logo-icon-wrapper::before {
    content: "";
    position: absolute;
    inset: -10px;
    background: radial-gradient(circle, rgba(99, 102, 241, 0.3) 0%, transparent 70%);
    border-radius: 50%;
    animation: logo-glow 3s ease-in-out infinite;
}

.auth-logo-svg {
    width: 100%;
    height: 100%;
    filter: drop-shadow(0 0 25px rgba(99, 102, 241, 0.4));
}

@keyframes logo-float {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-5px); }
}

@keyframes logo-glow {
    0%, 100% { opacity: 0.5; transform: scale(1); }
    50% { opacity: 0.8; transform: scale(1.1); }
}

.auth-logo h1 {
    font-family: 'Inter', sans-serif;
    font-size: 1.55rem;
    font-weight: 800;
    margin: 0;
    background: linear-gradient(135deg, #ffffff 0%, #e0e7ff 40%, #a5b4fc 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.4px;
    text-shadow: 0 0 32px rgba(99, 102, 241, 0.28);
}

.brand-tagline {
    display: inline-block;
    margin-top: 8px;
    padding: 5px 14px;
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(6, 182, 212, 0.1) 100%);
    border: 1px solid rgba(99, 102, 241, 0.2);
    border-radius: 18px;
    color: rgba(165, 180, 252, 0.9);
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.8px;
    text-transform: uppercase;
}

.auth-logo p:not(.brand-tagline) {
    color: rgba(255, 255, 255, 0.4);
    font-size: 0.85rem;
    margin-top: 6px;
    font-weight: 400;
    letter-spacing: 0.5px;
}

/* ═══════════════════════════════════════════════════
   TITLES
═══════════════════════════════════════════════════ */
.auth-title {
    font-family: 'Inter', sans-serif;
    font-size: 1.45rem;
    font-weight: 700;
    color: #f8fafc;
    text-align: center;
    margin-bottom: 8px;
    letter-spacing: -0.2px;
    position: relative;
    z-index: 1;
}

.auth-subtitle {
    color: rgba(255, 255, 255, 0.52);
    font-size: 0.86rem;
    text-align: center;
    margin: 0 auto 22px auto;
    max-width: 320px;
    font-weight: 400;
    position: relative;
    z-index: 1;
    line-height: 1.5;
}

.auth-subtitle strong {
    color: #a5b4fc;
    font-weight: 600;
}

/* Divider between logo and form */
.auth-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
    margin: 0 0 22px 0;
}

/* ═══════════════════════════════════════════════════
   FORM INPUTS - Enhanced Styling
═══════════════════════════════════════════════════ */
[data-testid="stForm"] {
    position: relative;
    z-index: 1;
}

/* ═══════════════════════════════════════════════════
   OAUTH BUTTONS
═══════════════════════════════════════════════════ */
.oauth-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    width: 100%;
    padding: 14px 16px;
    border-radius: 14px;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.12);
    color: #e2e8f0;
    text-decoration: none;
    font-size: 0.92rem;
    font-weight: 600;
    margin-bottom: 14px;
    transition: all 0.2s ease;
}

.oauth-btn:hover {
    border-color: rgba(255, 255, 255, 0.2);
    background: rgba(255, 255, 255, 0.06);
    transform: translateY(-1px);
}

.oauth-btn span {
    display: inline-flex;
    width: 18px;
    height: 18px;
}

.oauth-divider {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 10px 0 18px 0;
    color: rgba(255, 255, 255, 0.4);
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.oauth-divider::before,
.oauth-divider::after {
    content: "";
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.12), transparent);
}

/* Input container */
[data-testid="stTextInput"] {
    margin-bottom: 20px !important;
}

/* Input labels */
[data-testid="stTextInput"] > label,
[data-testid="stSelectbox"] > label {
    color: rgba(255, 255, 255, 0.6) !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.3px !important;
    margin-bottom: 8px !important;
}

/* Input fields */
[data-testid="stTextInput"] > div > div > input {
    background: rgba(255, 255, 255, 0.03) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 14px !important;
    color: #f1f5f9 !important;
    padding: 16px 18px !important;
    font-size: 0.95rem !important;
    font-weight: 400 !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    height: auto !important;
    box-shadow: 0 10px 28px rgba(2, 6, 23, 0.2) inset, 0 4px 12px rgba(2, 6, 23, 0.22) !important;
}

[data-testid="stTextInput"] > div > div > input::placeholder {
    color: rgba(255, 255, 255, 0.25) !important;
}

[data-testid="stTextInput"] > div > div > input:hover {
    border-color: rgba(255, 255, 255, 0.15) !important;
    background: rgba(255, 255, 255, 0.04) !important;
    transform: translateY(-1px);
}

[data-testid="stTextInput"] > div > div > input:focus {
    border-color: rgba(99, 102, 241, 0.5) !important;
    background: rgba(99, 102, 241, 0.03) !important;
    box-shadow: 
        0 0 0 4px rgba(99, 102, 241, 0.1),
        0 0 20px rgba(99, 102, 241, 0.1) !important;
    outline: none !important;
}

/* Password visibility toggle */
[data-testid="stTextInput"] button {
    color: rgba(255, 255, 255, 0.4) !important;
}

[data-testid="stTextInput"] button:hover {
    color: rgba(255, 255, 255, 0.7) !important;
}

/* Selectbox styling */
[data-testid="stSelectbox"] > div > div {
    background: rgba(255, 255, 255, 0.03) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 14px !important;
}

[data-testid="stSelectbox"] > div > div > div {
    color: #f1f5f9 !important;
    padding: 12px 16px !important;
}

/* ═══════════════════════════════════════════════════
   PRIMARY BUTTON (Sign In / Create Account)
═══════════════════════════════════════════════════ */
[data-testid="stForm"] .stButton > button,
.primary-btn .stButton > button {
    width: 100%;
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 16px 28px !important;
    font-size: 0.95rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.3px !important;
    cursor: pointer !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 
        0 4px 15px rgba(99, 102, 241, 0.4),
        0 0 0 1px rgba(255, 255, 255, 0.1) inset !important;
    position: relative;
    overflow: hidden;
    transform-style: preserve-3d;
}

[data-testid="stForm"] .stButton > button::before {
    content: "";
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
    transition: left 0.5s;
}

[data-testid="stForm"] .stButton > button:hover {
    transform: translateY(-3px) scale(1.01) !important;
    box-shadow: 
        0 8px 25px rgba(99, 102, 241, 0.5),
        0 0 0 1px rgba(255, 255, 255, 0.15) inset !important;
}

[data-testid="stForm"] .stButton > button:hover::before {
    left: 100%;
}

[data-testid="stForm"] .stButton > button:active {
    transform: translateY(0) scale(0.98) !important;
}

/* ═══════════════════════════════════════════════════
   LINK BUTTONS (Forgot Password, Create Account, Back)
═══════════════════════════════════════════════════ */
.link-btn .stButton > button {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    color: #818cf8 !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    padding: 8px 4px !important;
    text-decoration: none !important;
    transition: all 0.2s ease !important;
}

.link-btn .stButton > button:hover {
    background: transparent !important;
    color: #a5b4fc !important;
    text-decoration: underline !important;
    transform: none !important;
    box-shadow: none !important;
}

/* Secondary text link style */
.text-link-btn .stButton > button {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    color: rgba(255, 255, 255, 0.5) !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    padding: 4px 0 !important;
}

.text-link-btn .stButton > button:hover {
    background: transparent !important;
    color: #818cf8 !important;
    transform: none !important;
    box-shadow: none !important;
}

/* ═══════════════════════════════════════════════════
   CHECKBOX STYLING
═══════════════════════════════════════════════════ */
[data-testid="stCheckbox"] {
    margin: 4px 0 !important;
}

[data-testid="stCheckbox"] > label {
    color: rgba(255, 255, 255, 0.6) !important;
    font-size: 0.85rem !important;
    font-weight: 400 !important;
}

[data-testid="stCheckbox"] > label > span:first-child {
    background: rgba(255, 255, 255, 0.05) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 6px !important;
}

[data-testid="stCheckbox"] > label > span:first-child[data-checked="true"] {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    border-color: transparent !important;
}

/* ═══════════════════════════════════════════════════
   MESSAGES (Success, Error, Info)
═══════════════════════════════════════════════════ */
.auth-message {
    padding: 14px 18px;
    border-radius: 14px;
    margin-bottom: 24px;
    font-size: 0.85rem;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 12px;
    position: relative;
    z-index: 1;
    animation: message-in 0.3s ease-out;
}

@keyframes message-in {
    from { opacity: 0; transform: translateY(-10px); }
    to { opacity: 1; transform: translateY(0); }
}

.auth-message-success {
    background: rgba(16, 185, 129, 0.1);
    border: 1px solid rgba(16, 185, 129, 0.2);
    color: #34d399;
}

.auth-message-error {
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.2);
    color: #f87171;
}

.auth-message-info {
    background: rgba(99, 102, 241, 0.1);
    border: 1px solid rgba(99, 102, 241, 0.2);
    color: #a5b4fc;
}

/* ═══════════════════════════════════════════════════
   DIVIDERS & TOGGLES
═══════════════════════════════════════════════════ */
.auth-divider {
    display: flex;
    align-items: center;
    margin: 28px 0;
    position: relative;
    z-index: 1;
}

.auth-divider::before,
.auth-divider::after {
    content: "";
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
}

.auth-divider span {
    padding: 0 16px;
    color: rgba(255, 255, 255, 0.3);
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    font-weight: 500;
}

.auth-toggle {
    text-align: center;
    margin-top: 28px;
    padding-top: 24px;
    border-top: 1px solid rgba(255, 255, 255, 0.06);
    position: relative;
    z-index: 1;
}

.auth-toggle p {
    color: rgba(255, 255, 255, 0.4);
    font-size: 0.85rem;
    margin: 0 0 8px 0;
    font-weight: 400;
}

/* ═══════════════════════════════════════════════════
   FORGOT PASSWORD ROW
═══════════════════════════════════════════════════ */
.forgot-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin: -8px 0 24px 0;
    position: relative;
    z-index: 1;
}

.forgot-link {
    color: rgba(255, 255, 255, 0.4);
    font-size: 0.8rem;
    text-decoration: none;
    transition: color 0.2s;
    cursor: pointer;
    font-weight: 500;
}

.forgot-link:hover {
    color: #818cf8;
}

/* ═══════════════════════════════════════════════════
   PASSWORD REQUIREMENTS
═══════════════════════════════════════════════════ */
.password-hint {
    font-size: 0.75rem;
    color: rgba(255, 255, 255, 0.35);
    margin: -12px 0 20px 0;
    padding-left: 2px;
}

/* ═══════════════════════════════════════════════════
   RESPONSIVE ADJUSTMENTS
═══════════════════════════════════════════════════ */
@media (max-width: 480px) {
    .auth-card {
        padding: 36px 24px;
        border-radius: 20px;
    }
    
    .auth-logo-icon {
        font-size: 2.8rem;
    }
    
    .auth-logo h1 {
        font-size: 1.4rem;
    }
    
    .auth-title {
        font-size: 1.5rem;
    }
}

@media (prefers-reduced-motion: reduce) {
    .auth-bg-orb,
    .auth-card,
    .auth-hover-symbol,
    .auth-hover-title-bar::after {
        animation: none !important;
    }
}

/* ═══════════════════════════════════════════════════
   SPINNER OVERRIDE
═══════════════════════════════════════════════════ */
[data-testid="stSpinner"] {
    position: relative;
    z-index: 1;
}

[data-testid="stSpinner"] > div {
    border-color: #6366f1 !important;
    border-right-color: transparent !important;
}
</style>
"""


# ══════════════════════════════════════════════════════════════════════════════
# AUTHENTICATION FORMS
# ══════════════════════════════════════════════════════════════════════════════

def _render_logo():
    """Render the application logo and title."""
    st.markdown("""
    <div class="auth-logo">
        <div class="auth-hover-brand">
            <div class="auth-hover-symbol">
                <svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                    <defs>
                        <linearGradient id="hoverSymbolGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" style="stop-color:#38bdf8"/>
                            <stop offset="100%" style="stop-color:#22d3ee"/>
                        </linearGradient>
                    </defs>
                    <path d="M32 14L39 27H25L32 14Z" fill="url(#hoverSymbolGrad)"/>
                    <circle cx="24" cy="33" r="4" fill="url(#hoverSymbolGrad)" opacity="0.9"/>
                    <circle cx="40" cy="33" r="4" fill="url(#hoverSymbolGrad)" opacity="0.9"/>
                    <circle cx="32" cy="39" r="6" fill="url(#hoverSymbolGrad)" opacity="0.95"/>
                    <path d="M24 50C24 45.5817 27.5817 42 32 42C36.4183 42 40 45.5817 40 50" stroke="url(#hoverSymbolGrad)" stroke-width="3" stroke-linecap="round"/>
                </svg>
            </div>
            <div class="auth-brand-name-pill">
                <div class="auth-hover-title">AI Career Intelligence &amp; Skill Gap Analyzer</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_message(message: str, message_type: str = "info"):
    """Render a styled message (success, error, or info)."""
    icons = {
        "success": "✓",
        "error": "✕",
        "info": "ℹ"
    }
    icon = icons.get(message_type, "ℹ")
    st.markdown(f"""
    <div class="auth-message auth-message-{message_type}">
        <span>{icon}</span>
        <span>{message}</span>
    </div>
    """, unsafe_allow_html=True)


def _render_login_form():
    """Render the login form."""
    st.markdown('<div class="auth-divider"></div>', unsafe_allow_html=True)
    st.markdown('<h2 class="auth-title">Welcome Back</h2>', unsafe_allow_html=True)
    st.markdown('<p class="auth-subtitle">Sign in to continue your career journey</p>', unsafe_allow_html=True)

    google_auth_url = _build_google_auth_url()
    if google_auth_url:
        st.markdown(
            f"""
            <a class="oauth-btn" href="{google_auth_url}">
                <span>
                    <svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
                        <path fill="#EA4335" d="M24 9.5c3.1 0 5.9 1.1 8.1 3.1l6-6C34.2 2.8 29.4 1 24 1 14.6 1 6.6 6.4 3 14.2l7 5.4C12.1 13.7 17.6 9.5 24 9.5z"/>
                        <path fill="#4285F4" d="M46.1 24.5c0-1.6-.1-2.8-.4-4.2H24v8h12.6c-.8 4.1-3.5 7.6-7.4 9.4l7 5.4c4.1-3.8 6.5-9.3 6.5-15.6z"/>
                        <path fill="#FBBC05" d="M10 28.6c-.8-2.4-.8-4.9 0-7.3l-7-5.4C.8 20.6.8 27.4 3 32.1l7-5.4z"/>
                        <path fill="#34A853" d="M24 47c5.4 0 10.2-1.8 13.6-4.9l-7-5.4c-1.9 1.3-4.4 2.1-6.6 2.1-6.4 0-11.9-4.2-14-10.1l-7 5.4C6.6 41.6 14.6 47 24 47z"/>
                    </svg>
                </span>
                Continue with Google
            </a>
            <div class="oauth-divider">or sign in with email</div>
            """,
            unsafe_allow_html=True,
        )
    
    # Check for any messages
    if "auth_message" in st.session_state:
        msg = st.session_state.pop("auth_message")
        _render_message(msg["text"], msg["type"])
    
    # Login form
    with st.form("login_form", clear_on_submit=False):
        email = st.text_input(
            "📧 Email Address",
            placeholder="Enter your email",
            key="login_email"
        )
        
        password = st.text_input(
            "🔒 Password",
            type="password",
            placeholder="Enter your password",
            key="login_password"
        )
        
        col1, col2 = st.columns([1, 1])
        with col1:
            remember_me = st.checkbox("Remember me", key="login_remember")
        
        submitted = st.form_submit_button("Sign In", use_container_width=True)
        
        if submitted:
            if not email or not password:
                _render_message("Please enter both email and password.", "error")
            else:
                with st.spinner("Signing in..."):
                    db = get_auth_db()
                    result = db.login(email, password, remember_me)
                    
                    if result["success"]:
                        st.session_state[_SESSION_USER_KEY] = result["user"]
                        if result.get("session_token"):
                            st.session_state[_SESSION_TOKEN_KEY] = result["session_token"]
                        st.rerun()
                    else:
                        _render_message(result["message"], "error")
    
    # Forgot password link
    st.markdown('<div class="link-btn">', unsafe_allow_html=True)
    if st.button("Forgot Password?", key="forgot_pwd_btn", type="secondary"):
        _set_auth_page("forgot_password")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Sign up toggle
    st.markdown('<div class="auth-toggle">', unsafe_allow_html=True)
    st.markdown("<p>Don't have an account?</p>", unsafe_allow_html=True)
    st.markdown('<div class="text-link-btn">', unsafe_allow_html=True)
    if st.button("Create Account", key="goto_signup", type="secondary"):
        _set_auth_page("signup")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def _render_signup_form():
    """Render the signup form."""
    st.markdown('<div class="auth-divider"></div>', unsafe_allow_html=True)
    st.markdown('<h2 class="auth-title">Create Your Account</h2>', unsafe_allow_html=True)
    st.markdown('<p class="auth-subtitle">Start your AI-powered career transformation</p>', unsafe_allow_html=True)
    
    # Check for any messages
    if "auth_message" in st.session_state:
        msg = st.session_state.pop("auth_message")
        _render_message(msg["text"], msg["type"])
    
    db = get_auth_db()
    career_goals = [""] + db.get_career_goals()
    
    # Signup form
    with st.form("signup_form", clear_on_submit=False):
        name = st.text_input(
            "👤 Full Name",
            placeholder="Enter your full name",
            key="signup_name"
        )
        
        email = st.text_input(
            "📧 Email Address",
            placeholder="Enter your email",
            key="signup_email"
        )
        
        password = st.text_input(
            "🔒 Password",
            type="password",
            placeholder="Create a strong password",
            key="signup_password",
            help="Min 8 characters with uppercase, lowercase, and number"
        )
        
        confirm_password = st.text_input(
            "🔒 Confirm Password",
            type="password",
            placeholder="Confirm your password",
            key="signup_confirm_password"
        )
        
        career_goal = st.selectbox(
            "🎯 Career Goal (Optional)",
            options=career_goals,
            index=0,
            key="signup_career_goal",
            help="What role are you targeting?"
        )
        
        # Password requirements hint
        st.markdown("""
        <div style="font-size: 0.75rem; color: rgba(255,255,255,0.5); margin: -10px 0 15px 0;">
            Password requirements: 8+ characters, uppercase, lowercase, and number
        </div>
        """, unsafe_allow_html=True)
        
        submitted = st.form_submit_button("Create Account", use_container_width=True)
        
        if submitted:
            with st.spinner("Creating your account..."):
                result = db.signup(
                    name=name,
                    email=email,
                    password=password,
                    confirm_password=confirm_password,
                    career_goal=career_goal if career_goal else ""
                )
                
                if result["success"]:
                    st.session_state["auth_message"] = {
                        "text": result["message"],
                        "type": "success"
                    }
                    _set_auth_page("login")
                    st.rerun()
                else:
                    _render_message(result["message"], "error")
    
    # Login toggle
    st.markdown('<div class="auth-toggle">', unsafe_allow_html=True)
    st.markdown("<p>Already have an account?</p>", unsafe_allow_html=True)
    st.markdown('<div class="text-link-btn">', unsafe_allow_html=True)
    if st.button("Sign In", key="goto_login", type="secondary"):
        _set_auth_page("login")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def _render_forgot_password_form():
    """Render the forgot password form."""
    st.markdown('<div class="auth-divider"></div>', unsafe_allow_html=True)
    st.markdown('<h2 class="auth-title">Reset Password</h2>', unsafe_allow_html=True)
    st.markdown('<p class="auth-subtitle">Enter your email to reset your password</p>', unsafe_allow_html=True)
    
    # Check for any messages
    if "auth_message" in st.session_state:
        msg = st.session_state.pop("auth_message")
        _render_message(msg["text"], msg["type"])
    
    with st.form("forgot_password_form", clear_on_submit=False):
        email = st.text_input(
            "📧 Email Address",
            placeholder="Enter your registered email",
            key="forgot_email"
        )
        
        submitted = st.form_submit_button("Continue", use_container_width=True)
        
        if submitted:
            if not email:
                _render_message("Please enter your email address.", "error")
            else:
                with st.spinner("Verifying email..."):
                    db = get_auth_db()
                    result = db.request_password_reset(email)
                    
                    if result["success"] and "reset_token" in result:
                        # Email exists - store token and go directly to reset form
                        st.session_state[_RESET_TOKEN_KEY] = result["reset_token"]
                        st.session_state["reset_user_email"] = email  # Store email for display
                        _set_auth_page("reset_password")
                        st.rerun()
                    elif result["success"]:
                        # Email doesn't exist but we don't reveal that for security
                        _render_message("If an account exists with this email, you can reset your password.", "info")
                    else:
                        _render_message(result["message"], "error")
    
    # Back to login
    st.markdown('<div class="auth-toggle">', unsafe_allow_html=True)
    st.markdown("<p>Remember your password?</p>", unsafe_allow_html=True)
    st.markdown('<div class="text-link-btn">', unsafe_allow_html=True)
    if st.button("← Back to Sign In", key="back_to_login", type="secondary"):
        _set_auth_page("login")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def _render_reset_password_form():
    """Render the password reset form."""
    st.markdown('<div class="auth-divider"></div>', unsafe_allow_html=True)
    st.markdown('<h2 class="auth-title">Set New Password</h2>', unsafe_allow_html=True)
    
    # Show which email is being reset
    reset_email = st.session_state.get("reset_user_email", "")
    if reset_email:
        st.markdown(f'<p class="auth-subtitle">Create a new password for <strong>{reset_email}</strong></p>', unsafe_allow_html=True)
    else:
        st.markdown('<p class="auth-subtitle">Create a strong new password</p>', unsafe_allow_html=True)
    
    # Check for any messages
    if "auth_message" in st.session_state:
        msg = st.session_state.pop("auth_message")
        _render_message(msg["text"], msg["type"])
    
    reset_token = st.session_state.get(_RESET_TOKEN_KEY)
    
    if not reset_token:
        _render_message("Invalid or expired reset session. Please try again.", "error")
        if st.button("Try Again", key="new_reset_link"):
            _set_auth_page("forgot_password")
            st.rerun()
        return
    
    with st.form("reset_password_form", clear_on_submit=False):
        new_password = st.text_input(
            "🔒 New Password",
            type="password",
            placeholder="Enter new password",
            key="reset_new_password",
            help="Min 8 characters with uppercase, lowercase, and number"
        )
        
        confirm_password = st.text_input(
            "🔒 Confirm New Password",
            type="password",
            placeholder="Confirm new password",
            key="reset_confirm_password"
        )
        
        # Password requirements hint
        st.markdown("""
        <div style="font-size: 0.75rem; color: rgba(255,255,255,0.5); margin: -10px 0 15px 0;">
            Password requirements: 8+ characters, uppercase, lowercase, and number
        </div>
        """, unsafe_allow_html=True)
        
        submitted = st.form_submit_button("Reset Password", use_container_width=True)
        
        if submitted:
            with st.spinner("Resetting password..."):
                db = get_auth_db()
                result = db.reset_password(
                    token=reset_token,
                    new_password=new_password,
                    confirm_password=confirm_password
                )
                
                if result["success"]:
                    st.session_state.pop(_RESET_TOKEN_KEY, None)
                    st.session_state.pop("reset_user_email", None)
                    st.session_state["auth_message"] = {
                        "text": "Password reset successful! Please sign in with your new password.",
                        "type": "success"
                    }
                    _set_auth_page("login")
                    st.rerun()
                else:
                    _render_message(result["message"], "error")
    
    # Back to login
    st.markdown('<div class="auth-toggle" style="margin-top: 10px;">', unsafe_allow_html=True)
    st.markdown('<div class="text-link-btn">', unsafe_allow_html=True)
    if st.button("← Cancel", key="cancel_reset", type="secondary"):
        st.session_state.pop(_RESET_TOKEN_KEY, None)
        st.session_state.pop("reset_user_email", None)
        _set_auth_page("login")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN AUTHENTICATION PAGE RENDERER
# ══════════════════════════════════════════════════════════════════════════════

def render_auth_page():
    """
    Render the complete authentication page with login/signup/forgot password.
    
    This function handles all authentication UI and should be called when
    the user is not authenticated.
    """
    # Inject CSS
    st.markdown(AUTH_CSS, unsafe_allow_html=True)

    # Handle Google OAuth callback if present
    _handle_google_callback()
    
    # Add animated background orbs
    st.markdown("""
    <div class="auth-bg-orb auth-bg-orb-1"></div>
    <div class="auth-bg-orb auth-bg-orb-2"></div>
    <div class="auth-bg-orb auth-bg-orb-3"></div>
    """, unsafe_allow_html=True)
    
    # Add body class for auth page
    st.markdown('<div class="auth-page">', unsafe_allow_html=True)
    
    # Determine current auth page early so we can apply page-specific visual tuning
    current_page = _get_auth_page()

    # Center the auth card
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if current_page == "login":
            st.markdown(
                """
                <style>
                /* Login-only premium cinematic pass */
                .auth-card {
                    animation: card-3d-float 15s ease-in-out infinite;
                }

                .auth-card::after {
                    background: radial-gradient(ellipse at center, rgba(34, 211, 238, 0.05) 0%, transparent 74%);
                }

                .auth-hover-symbol {
                    animation: symbol-3d-orbit 7.5s ease-in-out infinite;
                }

                .auth-brand-name-pill::after {
                    animation: holo-scan 11.5s linear infinite;
                    opacity: 0.32;
                }

                .auth-hover-title {
                    font-size: 1.32rem;
                    letter-spacing: 0.45px;
                    text-shadow: 0 0 20px rgba(56, 189, 248, 0.2);
                }

                .auth-title {
                    font-size: 3rem;
                    font-weight: 800;
                    letter-spacing: -0.5px;
                    margin-bottom: 10px;
                    text-shadow: 0 8px 28px rgba(2, 6, 23, 0.5);
                }

                .auth-subtitle {
                    font-size: 0.95rem;
                    color: rgba(226, 232, 240, 0.66);
                    margin: 0 auto 26px auto;
                }

                [data-testid="stTextInput"] > div > div > input {
                    border-radius: 15px !important;
                    border-color: rgba(148, 163, 184, 0.22) !important;
                    background: linear-gradient(135deg, rgba(30, 41, 59, 0.55), rgba(30, 41, 59, 0.35)) !important;
                    box-shadow: 0 12px 30px rgba(2, 6, 23, 0.24) inset, 0 8px 24px rgba(2, 6, 23, 0.28) !important;
                    transition: transform 0.45s cubic-bezier(0.22, 1, 0.36, 1), box-shadow 0.45s cubic-bezier(0.22, 1, 0.36, 1), border-color 0.35s ease !important;
                }

                [data-testid="stTextInput"] > div > div > input:hover {
                    transform: translateY(-2px) !important;
                    border-color: rgba(56, 189, 248, 0.3) !important;
                    box-shadow: 0 14px 30px rgba(2, 6, 23, 0.24) inset, 0 12px 30px rgba(8, 47, 73, 0.26) !important;
                }

                [data-testid="stForm"] .stButton > button {
                    background: linear-gradient(135deg, #111d34 0%, #1c2a4e 100%) !important;
                    border: 1px solid rgba(56, 189, 248, 0.2) !important;
                    transition: transform 0.45s cubic-bezier(0.22, 1, 0.36, 1), box-shadow 0.45s cubic-bezier(0.22, 1, 0.36, 1) !important;
                }

                [data-testid="stForm"] .stButton > button:hover {
                    transform: translateY(-4px) scale(1.01) !important;
                    box-shadow: 0 16px 35px rgba(8, 47, 73, 0.38), 0 0 0 1px rgba(125, 211, 252, 0.28) inset !important;
                }

                .link-btn .stButton > button,
                .text-link-btn .stButton > button {
                    transition: all 0.38s ease !important;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )

        st.markdown('<div class="auth-container">', unsafe_allow_html=True)
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        
        # Render logo
        _render_logo()
        
        # Render appropriate form based on current page
        if current_page == "signup":
            _render_signup_form()
        elif current_page == "forgot_password":
            _render_forgot_password_form()
        elif current_page == "reset_password":
            _render_reset_password_form()
        else:  # Default to login
            _render_login_form()
        
        st.markdown('</div>', unsafe_allow_html=True)  # Close auth-card
        st.markdown('</div>', unsafe_allow_html=True)  # Close auth-container
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close auth-page


# ══════════════════════════════════════════════════════════════════════════════
# USER PROFILE WIDGET
# ══════════════════════════════════════════════════════════════════════════════

def render_user_menu():
    """
    Render a user profile menu in the sidebar or header.
    Shows user info and logout button.
    """
    user = get_current_user()
    if not user:
        return
    
    st.markdown(f"""
    <div style="
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 20px;
    ">
        <div style="display: flex; align-items: center; gap: 12px;">
            <div style="
                width: 40px;
                height: 40px;
                background: linear-gradient(135deg, #6366f1, #818cf8);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.1rem;
                font-weight: 700;
                color: white;
            ">{user['name'][0].upper()}</div>
            <div>
                <div style="font-weight: 600; color: #f1f5f9; font-size: 0.9rem;">
                    {user['name']}
                </div>
                <div style="color: rgba(255,255,255,0.5); font-size: 0.75rem;">
                    {user['email']}
                </div>
            </div>
        </div>
        {f'''<div style="
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px solid rgba(255,255,255,0.08);
        ">
            <span style="
                background: rgba(99,102,241,0.15);
                color: #a5b4fc;
                padding: 4px 10px;
                border-radius: 20px;
                font-size: 0.7rem;
                font-weight: 600;
            ">🎯 {user["career_goal"]}</span>
        </div>''' if user.get('career_goal') else ''}
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚪 Logout", key="logout_btn", use_container_width=True):
        logout()
        st.rerun()


def render_welcome_header():
    """Render a welcome header for authenticated users."""
    user = get_current_user()
    if not user:
        return
    
    # Get time-based greeting
    from datetime import datetime
    hour = datetime.now().hour
    if hour < 12:
        greeting = "Good morning"
    elif hour < 17:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, rgba(99,102,241,0.1), rgba(6,182,212,0.05));
        border: 1px solid rgba(99,102,241,0.2);
        border-radius: 16px;
        padding: 24px 28px;
        margin-bottom: 24px;
    ">
        <div style="font-size: 0.85rem; color: rgba(255,255,255,0.5); margin-bottom: 4px;">
            {greeting},
        </div>
        <div style="font-size: 1.5rem; font-weight: 700; color: #f1f5f9;">
            Welcome back, {user['name'].split()[0]}! 👋
        </div>
        <div style="font-size: 0.85rem; color: rgba(255,255,255,0.6); margin-top: 8px;">
            Ready to continue your career journey?
            {f" Your goal: <strong>{user['career_goal']}</strong>" if user.get('career_goal') else ""}
        </div>
    </div>
    """, unsafe_allow_html=True)
