"""
Enhanced SQLite-backed Authentication Database
==============================================

A production-ready authentication database module with:
- bcrypt password hashing
- Career goal tracking
- Password reset tokens
- Session management
- Remember me functionality

Tables:
  users          — Core user data with secure password storage
  password_reset — Time-limited password reset tokens
  sessions       — Persistent login sessions
"""
from __future__ import annotations

import os
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# bcrypt for secure password hashing
try:
    import bcrypt
    _HAS_BCRYPT = True
except ImportError:
    _HAS_BCRYPT = False


# ── Configuration ──────────────────────────────────────────────────────────
_DEFAULT_DB = Path(__file__).parent.parent.parent / "data" / "users.db"
_RESET_TOKEN_EXPIRY_HOURS = 24
_SESSION_EXPIRY_DAYS = 30


# ── Password Hashing with bcrypt ───────────────────────────────────────────
def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt with automatic salt generation.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string (bcrypt format)
    """
    if not _HAS_BCRYPT:
        raise ImportError(
            "bcrypt is not installed. Run: pip install bcrypt"
        )
    # Generate salt and hash password
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a password against its bcrypt hash.
    
    Args:
        password: Plain text password to verify
        hashed: Stored bcrypt hash
        
    Returns:
        True if password matches, False otherwise
    """
    if not _HAS_BCRYPT:
        return False
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False


# ── Token Generation ───────────────────────────────────────────────────────
def generate_token(length: int = 32) -> str:
    """Generate a secure random token for password reset or sessions."""
    return secrets.token_urlsafe(length)


# ── Auth Database Class ────────────────────────────────────────────────────
class AuthDatabase:
    """
    Production-ready SQLite authentication database.
    
    Features:
    - bcrypt password hashing
    - Email uniqueness enforcement
    - Career goal tracking
    - Password reset tokens
    - Remember me sessions
    """

    def __init__(self, db_path: str | Path = _DEFAULT_DB):
        """
        Initialize the auth database.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_tables()

    # ── Database Connection ────────────────────────────────────────────────
    
    @contextmanager
    def _conn(self):
        """Context manager for database connections with auto-commit."""
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_tables(self):
        """Initialize all required database tables."""
        with self._conn() as conn:
            # Main users table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    name          TEXT NOT NULL,
                    email         TEXT UNIQUE NOT NULL,
                    password      TEXT NOT NULL,
                    auth_provider TEXT DEFAULT 'local',
                    provider_id   TEXT DEFAULT '',
                    career_goal   TEXT DEFAULT '',
                    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login    TIMESTAMP,
                    is_active     INTEGER DEFAULT 1,
                    email_verified INTEGER DEFAULT 0
                )
            """)
            
            # Migrate existing tables: Add missing columns
            self._migrate_users_table(conn)
            
            # Password reset tokens table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS password_reset (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id       INTEGER NOT NULL,
                    token         TEXT UNIQUE NOT NULL,
                    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at    TIMESTAMP NOT NULL,
                    used          INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # Sessions table for "Remember Me" functionality
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id       INTEGER NOT NULL,
                    session_token TEXT UNIQUE NOT NULL,
                    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at    TIMESTAMP NOT NULL,
                    device_info   TEXT DEFAULT '',
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(session_token)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_reset_token ON password_reset(token)")

    def _migrate_users_table(self, conn):
        """Add missing columns to users table for backwards compatibility."""
        # Get current columns
        cursor = conn.execute("PRAGMA table_info(users)")
        columns = {row[1] for row in cursor.fetchall()}
        
        # Add missing columns with defaults
        migrations = [
            ("is_active", "INTEGER DEFAULT 1"),
            ("email_verified", "INTEGER DEFAULT 0"),
            ("career_goal", "TEXT DEFAULT ''"),
            ("last_login", "TIMESTAMP"),
            ("auth_provider", "TEXT DEFAULT 'local'"),
            ("provider_id", "TEXT DEFAULT ''"),
        ]
        
        for col_name, col_def in migrations:
            if col_name not in columns:
                try:
                    conn.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}")
                except Exception:
                    pass  # Column might already exist

    # ── User Registration ──────────────────────────────────────────────────

    def signup(
        self,
        name: str,
        email: str,
        password: str,
        confirm_password: str,
        career_goal: str = ""
    ) -> Dict[str, Any]:
        """
        Register a new user account.
        
        Args:
            name: User's full name
            email: User's email address (must be unique)
            password: Plain text password (min 8 characters)
            confirm_password: Password confirmation (must match)
            career_goal: Optional career goal (e.g., "Data Scientist")
            
        Returns:
            Dict with 'success' bool and 'message' or 'user' data
        """
        # Input validation
        name = name.strip()
        email = email.strip().lower()
        career_goal = career_goal.strip()
        
        # Validate name
        if len(name) < 2:
            return {"success": False, "message": "Name must be at least 2 characters."}
        
        # Validate email format
        if not self._is_valid_email(email):
            return {"success": False, "message": "Please enter a valid email address."}
        
        # Validate password strength
        if len(password) < 8:
            return {"success": False, "message": "Password must be at least 8 characters."}
        
        if not any(c.isupper() for c in password):
            return {"success": False, "message": "Password must contain at least one uppercase letter."}
        
        if not any(c.islower() for c in password):
            return {"success": False, "message": "Password must contain at least one lowercase letter."}
        
        if not any(c.isdigit() for c in password):
            return {"success": False, "message": "Password must contain at least one number."}
        
        # Confirm password match
        if password != confirm_password:
            return {"success": False, "message": "Passwords do not match."}
        
        # Check if email already exists
        if self._email_exists(email):
            return {"success": False, "message": "An account with this email already exists."}
        
        # Hash password with bcrypt
        try:
            password_hash = hash_password(password)
        except ImportError as e:
            return {"success": False, "message": str(e)}
        
        # Insert user into database
        try:
            with self._conn() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO users (name, email, password, career_goal)
                    VALUES (?, ?, ?, ?)
                    """,
                    (name, email, password_hash, career_goal)
                )
                user_id = cursor.lastrowid
                
            return {
                "success": True,
                "message": "Account created successfully! Please log in.",
                "user": {
                    "id": user_id,
                    "name": name,
                    "email": email,
                    "career_goal": career_goal
                }
            }
        except sqlite3.IntegrityError:
            return {"success": False, "message": "An account with this email already exists."}
        except Exception as e:
            return {"success": False, "message": f"Registration failed: {str(e)}"}

    # ── User Login ─────────────────────────────────────────────────────────

    def login(
        self,
        email: str,
        password: str,
        remember_me: bool = False
    ) -> Dict[str, Any]:
        """
        Authenticate a user with email and password.
        
        Args:
            email: User's email address
            password: Plain text password
            remember_me: Whether to create a persistent session
            
        Returns:
            Dict with 'success' bool and user data or error message
        """
        email = email.strip().lower()
        
        if not email or not password:
            return {"success": False, "message": "Please enter both email and password."}
        
        # First, find and validate the user
        user_data = None
        with self._conn() as conn:
            # Find user by email
            user = conn.execute(
                "SELECT * FROM users WHERE email = ? AND is_active = 1",
                (email,)
            ).fetchone()
            
            if not user:
                return {"success": False, "message": "Invalid email or password."}
            
            # Verify password
            if not verify_password(password, user["password"]):
                return {"success": False, "message": "Invalid email or password."}
            
            # Update last login timestamp
            conn.execute(
                "UPDATE users SET last_login = ? WHERE id = ?",
                (datetime.now(timezone.utc).isoformat(), user["id"])
            )
            
            # Store user data for return
            user_data = {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "career_goal": user["career_goal"] or "",
                "created_at": user["created_at"]
            }
        
        # Create session token if remember_me is enabled (separate connection)
        session_token = None
        if remember_me and user_data:
            session_token = self._create_session(user_data["id"])
        
        return {
            "success": True,
            "message": "Login successful!",
            "user": user_data,
            "session_token": session_token
        }

    def get_or_create_oauth_user(
        self,
        email: str,
        name: str,
        provider: str,
        provider_id: str,
        email_verified: bool = False
    ) -> Dict[str, Any]:
        """
        Get or create a user authenticated via an OAuth provider.
        """
        email = email.strip().lower()
        name = name.strip() or "User"

        if not self._is_valid_email(email):
            return {"success": False, "message": "Invalid email from provider."}

        with self._conn() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE email = ? AND is_active = 1",
                (email,)
            ).fetchone()

            if user:
                conn.execute(
                    """
                    UPDATE users
                    SET auth_provider = ?, provider_id = ?, email_verified = ?, last_login = ?
                    WHERE id = ?
                    """,
                    (
                        provider,
                        provider_id or user["provider_id"],
                        1 if email_verified else user["email_verified"],
                        datetime.now(timezone.utc).isoformat(),
                        user["id"],
                    ),
                )

                return {
                    "success": True,
                    "message": "Login successful!",
                    "user": {
                        "id": user["id"],
                        "name": user["name"],
                        "email": user["email"],
                        "career_goal": user["career_goal"] or "",
                        "created_at": user["created_at"],
                    },
                }

        try:
            password_hash = hash_password(generate_token(16))
        except ImportError as e:
            return {"success": False, "message": str(e)}

        with self._conn() as conn:
            cursor = conn.execute(
                """
                INSERT INTO users (name, email, password, career_goal, auth_provider, provider_id, email_verified)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    name,
                    email,
                    password_hash,
                    "",
                    provider,
                    provider_id,
                    1 if email_verified else 0,
                ),
            )
            user_id = cursor.lastrowid

        return {
            "success": True,
            "message": "Login successful!",
            "user": {
                "id": user_id,
                "name": name,
                "email": email,
                "career_goal": "",
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        }

    # ── Session Management ─────────────────────────────────────────────────

    def _create_session(self, user_id: int, device_info: str = "") -> str:
        """Create a new session for remember me functionality."""
        token = generate_token(48)
        expires_at = datetime.now(timezone.utc) + timedelta(days=_SESSION_EXPIRY_DAYS)
        
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO sessions (user_id, session_token, expires_at, device_info)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, token, expires_at.isoformat(), device_info)
            )
        return token

    def validate_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """
        Validate a session token and return user data if valid.
        
        Args:
            session_token: The session token to validate
            
        Returns:
            User data dict if valid, None if invalid/expired
        """
        if not session_token:
            return None
            
        with self._conn() as conn:
            session = conn.execute(
                """
                SELECT s.*, u.id, u.name, u.email, u.career_goal, u.created_at
                FROM sessions s
                JOIN users u ON s.user_id = u.id
                WHERE s.session_token = ?
                  AND s.expires_at > datetime('now')
                  AND u.is_active = 1
                """,
                (session_token,)
            ).fetchone()
            
            if session:
                return {
                    "id": session["id"],
                    "name": session["name"],
                    "email": session["email"],
                    "career_goal": session["career_goal"] or "",
                    "created_at": session["created_at"]
                }
        return None

    def invalidate_session(self, session_token: str) -> bool:
        """Invalidate/delete a session token (logout)."""
        with self._conn() as conn:
            conn.execute(
                "DELETE FROM sessions WHERE session_token = ?",
                (session_token,)
            )
        return True

    def invalidate_all_sessions(self, user_id: int) -> bool:
        """Invalidate all sessions for a user (logout everywhere)."""
        with self._conn() as conn:
            conn.execute(
                "DELETE FROM sessions WHERE user_id = ?",
                (user_id,)
            )
        return True

    # ── Password Reset ─────────────────────────────────────────────────────

    def request_password_reset(self, email: str) -> Dict[str, Any]:
        """
        Request a password reset token.
        
        Args:
            email: User's email address
            
        Returns:
            Dict with success status and reset token (for demo) or message
        """
        email = email.strip().lower()
        
        if not self._is_valid_email(email):
            return {"success": False, "message": "Please enter a valid email address."}
        
        with self._conn() as conn:
            user = conn.execute(
                "SELECT id, name FROM users WHERE email = ? AND is_active = 1",
                (email,)
            ).fetchone()
            
            if not user:
                # Don't reveal if email exists for security
                return {
                    "success": True,
                    "message": "If an account exists with this email, you will receive a password reset link."
                }
            
            # Generate reset token
            token = generate_token(32)
            expires_at = datetime.now(timezone.utc) + timedelta(hours=_RESET_TOKEN_EXPIRY_HOURS)
            
            # Delete any existing reset tokens for this user
            conn.execute(
                "DELETE FROM password_reset WHERE user_id = ?",
                (user["id"],)
            )
            
            # Create new reset token
            conn.execute(
                """
                INSERT INTO password_reset (user_id, token, expires_at)
                VALUES (?, ?, ?)
                """,
                (user["id"], token, expires_at.isoformat())
            )
            
            return {
                "success": True,
                "message": "Password reset instructions have been sent to your email.",
                "reset_token": token,  # In production, send via email
                "user_name": user["name"]
            }

    def reset_password(
        self,
        token: str,
        new_password: str,
        confirm_password: str
    ) -> Dict[str, Any]:
        """
        Reset password using a valid reset token.
        
        Args:
            token: Password reset token
            new_password: New password
            confirm_password: Password confirmation
            
        Returns:
            Dict with success status and message
        """
        # Validate new password
        if len(new_password) < 8:
            return {"success": False, "message": "Password must be at least 8 characters."}
        
        if not any(c.isupper() for c in new_password):
            return {"success": False, "message": "Password must contain at least one uppercase letter."}
        
        if not any(c.islower() for c in new_password):
            return {"success": False, "message": "Password must contain at least one lowercase letter."}
        
        if not any(c.isdigit() for c in new_password):
            return {"success": False, "message": "Password must contain at least one number."}
        
        if new_password != confirm_password:
            return {"success": False, "message": "Passwords do not match."}
        
        with self._conn() as conn:
            # Find valid reset token
            reset = conn.execute(
                """
                SELECT * FROM password_reset
                WHERE token = ?
                  AND used = 0
                  AND expires_at > datetime('now')
                """,
                (token,)
            ).fetchone()
            
            if not reset:
                return {"success": False, "message": "Invalid or expired reset link. Please request a new one."}
            
            # Hash new password
            try:
                password_hash = hash_password(new_password)
            except ImportError as e:
                return {"success": False, "message": str(e)}
            
            # Update password
            conn.execute(
                "UPDATE users SET password = ? WHERE id = ?",
                (password_hash, reset["user_id"])
            )
            
            # Mark token as used
            conn.execute(
                "UPDATE password_reset SET used = 1 WHERE id = ?",
                (reset["id"],)
            )
            
            # Store user_id to invalidate sessions after connection closes
            user_id_to_invalidate = reset["user_id"]
        
        # Invalidate all sessions for security (outside connection context)
        self.invalidate_all_sessions(user_id_to_invalidate)
        
        return {
            "success": True,
            "message": "Password reset successfully! You can now log in with your new password."
        }

    # ── User Profile ───────────────────────────────────────────────────────

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user data by ID."""
        with self._conn() as conn:
            user = conn.execute(
                """
                SELECT id, name, email, career_goal, created_at, last_login
                FROM users WHERE id = ? AND is_active = 1
                """,
                (user_id,)
            ).fetchone()
            
            if user:
                return dict(user)
        return None

    def update_profile(
        self,
        user_id: int,
        name: str = None,
        career_goal: str = None
    ) -> Dict[str, Any]:
        """Update user profile information."""
        updates = []
        params = []
        
        if name is not None:
            name = name.strip()
            if len(name) < 2:
                return {"success": False, "message": "Name must be at least 2 characters."}
            updates.append("name = ?")
            params.append(name)
        
        if career_goal is not None:
            updates.append("career_goal = ?")
            params.append(career_goal.strip())
        
        if not updates:
            return {"success": False, "message": "No changes to update."}
        
        params.append(user_id)
        
        with self._conn() as conn:
            conn.execute(
                f"UPDATE users SET {', '.join(updates)} WHERE id = ?",
                params
            )
        
        return {"success": True, "message": "Profile updated successfully!"}

    def change_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str,
        confirm_password: str
    ) -> Dict[str, Any]:
        """Change user password (requires current password)."""
        with self._conn() as conn:
            user = conn.execute(
                "SELECT password FROM users WHERE id = ?",
                (user_id,)
            ).fetchone()
            
            if not user:
                return {"success": False, "message": "User not found."}
            
            # Verify current password
            if not verify_password(current_password, user["password"]):
                return {"success": False, "message": "Current password is incorrect."}
        
        # Use reset_password validation logic (without token check)
        if len(new_password) < 8:
            return {"success": False, "message": "Password must be at least 8 characters."}
        
        if new_password != confirm_password:
            return {"success": False, "message": "New passwords do not match."}
        
        try:
            password_hash = hash_password(new_password)
        except ImportError as e:
            return {"success": False, "message": str(e)}
        
        with self._conn() as conn:
            conn.execute(
                "UPDATE users SET password = ? WHERE id = ?",
                (password_hash, user_id)
            )
        
        return {"success": True, "message": "Password changed successfully!"}

    # ── Utility Methods ────────────────────────────────────────────────────

    def _is_valid_email(self, email: str) -> bool:
        """Basic email validation."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def _email_exists(self, email: str) -> bool:
        """Check if email already exists in database."""
        with self._conn() as conn:
            result = conn.execute(
                "SELECT 1 FROM users WHERE email = ?",
                (email,)
            ).fetchone()
            return result is not None

    def get_career_goals(self) -> List[str]:
        """Get predefined list of career goals for selection."""
        return [
            "AI Engineer",
            "Data Scientist",
            "Machine Learning Engineer",
            "Software Developer",
            "Full Stack Developer",
            "Backend Developer",
            "Frontend Developer",
            "DevOps Engineer",
            "Cloud Architect",
            "Data Engineer",
            "Business Analyst",
            "Product Manager",
            "Cybersecurity Analyst",
            "Mobile App Developer",
            "Web Developer",
            "Other"
        ]

    def cleanup_expired_tokens(self):
        """Clean up expired reset tokens and sessions."""
        with self._conn() as conn:
            conn.execute(
                "DELETE FROM password_reset WHERE expires_at < datetime('now')"
            )
            conn.execute(
                "DELETE FROM sessions WHERE expires_at < datetime('now')"
            )


# ── Module-level convenience instance ──────────────────────────────────────
_db_instance: Optional[AuthDatabase] = None


def get_auth_db() -> AuthDatabase:
    """Get or create the singleton AuthDatabase instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = AuthDatabase()
    return _db_instance
