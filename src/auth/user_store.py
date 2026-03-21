"""
SQLite-backed user store — self-contained, no external database required.

Tables:
  users   — id, username, email, hashed_password, full_name, created_at, last_login
"""
from __future__ import annotations

import hashlib
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


_DEFAULT_DB = Path(__file__).parent.parent.parent / "data" / "auth.db"


def _hash_password(password: str) -> str:
    salt = os.getenv("AUTH_SALT", "career_analyzer_salt_2024")
    return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()


class UserStore:
    """Thread-safe SQLite user store."""

    def __init__(self, db_path: str | Path = _DEFAULT_DB):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    # ── Internal ──────────────────────────────────────────────────

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self):
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    username      TEXT UNIQUE NOT NULL,
                    email         TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    full_name     TEXT DEFAULT '',
                    created_at    TEXT DEFAULT (datetime('now')),
                    last_login    TEXT
                )
            """)

    # ── Public API ────────────────────────────────────────────────

    def register(self, username: str, email: str, password: str,
                 full_name: str = "") -> Dict[str, Any]:
        """
        Register a new user.

        Returns:
            {"success": True,  "user_id": int}
            {"success": False, "message": str}
        """
        username  = username.strip()
        email     = email.strip().lower()
        full_name = full_name.strip()

        if len(username) < 3:
            return {"success": False, "message": "Username must be at least 3 characters."}
        if len(password) < 6:
            return {"success": False, "message": "Password must be at least 6 characters."}
        if "@" not in email:
            return {"success": False, "message": "Invalid email address."}

        pw_hash = _hash_password(password)
        try:
            with self._conn() as conn:
                cur = conn.execute(
                    "INSERT INTO users (username, email, password_hash, full_name) "
                    "VALUES (?, ?, ?, ?)",
                    (username, email, pw_hash, full_name),
                )
                return {"success": True, "user_id": cur.lastrowid}
        except sqlite3.IntegrityError as e:
            msg = str(e)
            if "username" in msg:
                return {"success": False, "message": "Username already exists."}
            if "email" in msg:
                return {"success": False, "message": "Email already registered."}
            return {"success": False, "message": "Registration failed."}

    def login(self, username_or_email: str, password: str) -> Dict[str, Any]:
        """
        Authenticate a user by username OR email.

        Returns:
            {"success": True,  "user_id", "username", "email", "full_name"}
            {"success": False, "message": str}
        """
        key     = username_or_email.strip()
        pw_hash = _hash_password(password)
        with self._conn() as conn:
            user = conn.execute(
                "SELECT id, username, email, full_name FROM users "
                "WHERE (username = ? OR email = ?) AND password_hash = ?",
                (key, key.lower(), pw_hash),
            ).fetchone()

            if not user:
                return {"success": False, "message": "Invalid credentials."}

            # Update last_login
            conn.execute(
                "UPDATE users SET last_login = ? WHERE id = ?",
                (datetime.now(timezone.utc).isoformat(), user["id"]),
            )
            return {
                "success":   True,
                "user_id":   user["id"],
                "username":  user["username"],
                "email":     user["email"],
                "full_name": user["full_name"] or "",
            }

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Return user dict or None."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT id, username, email, full_name, created_at, last_login "
                "FROM users WHERE id = ?", (user_id,)
            ).fetchone()
        return dict(row) if row else None

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT id, username, email, full_name, created_at, last_login "
                "FROM users WHERE username = ?", (username,)
            ).fetchone()
        return dict(row) if row else None

    def update_full_name(self, user_id: int, full_name: str) -> bool:
        with self._conn() as conn:
            conn.execute("UPDATE users SET full_name = ? WHERE id = ?",
                         (full_name.strip(), user_id))
        return True

    def change_password(self, user_id: int, old_password: str,
                        new_password: str) -> Dict[str, Any]:
        old_hash = _hash_password(old_password)
        with self._conn() as conn:
            row = conn.execute(
                "SELECT id FROM users WHERE id = ? AND password_hash = ?",
                (user_id, old_hash),
            ).fetchone()
            if not row:
                return {"success": False, "message": "Current password is incorrect."}
            if len(new_password) < 6:
                return {"success": False, "message": "New password must be 6+ characters."}
            conn.execute("UPDATE users SET password_hash = ? WHERE id = ?",
                         (_hash_password(new_password), user_id))
        return {"success": True, "message": "Password updated."}
