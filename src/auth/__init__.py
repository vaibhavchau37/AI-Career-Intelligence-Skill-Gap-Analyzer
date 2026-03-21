"""
Auth Package — Complete Authentication System
=============================================

This package provides:
- JWT token handling for API authentication
- SQLite-backed user storage
- bcrypt password hashing
- Streamlit authentication UI
- Session management with "Remember Me"
- Password reset functionality
"""
from .jwt_handler import create_access_token, decode_access_token, verify_token_payload
from .user_store import UserStore
from .auth_database import (
    AuthDatabase,
    get_auth_db,
    hash_password,
    verify_password,
    generate_token
)
from .streamlit_auth import (
    render_auth_page,
    is_authenticated,
    get_current_user,
    logout,
    render_user_menu,
    render_welcome_header
)

__all__ = [
    # JWT handling
    "create_access_token",
    "decode_access_token", 
    "verify_token_payload",
    # User store (legacy)
    "UserStore",
    # Auth database (new)
    "AuthDatabase",
    "get_auth_db",
    "hash_password",
    "verify_password",
    "generate_token",
    # Streamlit auth UI
    "render_auth_page",
    "is_authenticated",
    "get_current_user",
    "logout",
    "render_user_menu",
    "render_welcome_header",
]
