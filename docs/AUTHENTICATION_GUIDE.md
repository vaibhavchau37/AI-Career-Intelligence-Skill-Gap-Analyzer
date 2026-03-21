# Authentication System Documentation

## Overview

The AI Career Intelligence & Skill Gap Analyzer includes a production-ready authentication system with the following features:

- **Secure password hashing** using bcrypt with auto-generated salts
- **Session management** with "Remember Me" functionality
- **Password reset** flow with time-limited tokens
- **Modern UI** with glassmorphism effects and smooth animations
- **SQLite database** for user storage (no external database required)

## Features

### 1. User Registration (Signup)

Users can create an account with:

- Full Name
- Email Address (unique, validated)
- Password (strong password requirements)
- Career Goal (optional, selectable from predefined list)

**Password Requirements:**

- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number

### 2. User Login

- Email and password authentication
- "Remember Me" option for persistent sessions (30 days)
- Session tokens stored in SQLite for validation

### 3. Password Reset

- Request reset via email
- Time-limited reset tokens (24 hours)
- Automatic session invalidation on password change

### 4. Session Management

- Secure session tokens for "Remember Me"
- Session validation on page load
- Logout functionality (invalidates current session)
- "Logout Everywhere" capability (invalidates all sessions)

## Technical Architecture

### Files Structure

```
src/auth/
├── __init__.py           # Package exports
├── auth_database.py      # SQLite database with bcrypt
├── streamlit_auth.py     # Streamlit UI components
├── jwt_handler.py        # JWT token handling (for API)
├── user_store.py         # Legacy user store
└── auth_router.py        # FastAPI routes
```

### Database Schema

```sql
-- Users table
CREATE TABLE users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    email         TEXT UNIQUE NOT NULL,
    password      TEXT NOT NULL,      -- bcrypt hash
    career_goal   TEXT DEFAULT '',
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login    TIMESTAMP,
    is_active     INTEGER DEFAULT 1,
    email_verified INTEGER DEFAULT 0
);

-- Password reset tokens
CREATE TABLE password_reset (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL,
    token         TEXT UNIQUE NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at    TIMESTAMP NOT NULL,
    used          INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Sessions for Remember Me
CREATE TABLE sessions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL,
    session_token TEXT UNIQUE NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at    TIMESTAMP NOT NULL,
    device_info   TEXT DEFAULT '',
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

## Usage

### Basic Integration

```python
from src.auth.streamlit_auth import (
    render_auth_page,
    is_authenticated,
    get_current_user,
    logout
)

# Check authentication at app start
if not is_authenticated():
    render_auth_page()
    st.stop()

# Access current user
user = get_current_user()
st.write(f"Welcome, {user['name']}!")

# Logout button
if st.button("Logout"):
    logout()
    st.rerun()
```

### Database Operations

```python
from src.auth.auth_database import get_auth_db

db = get_auth_db()

# Register a new user
result = db.signup(
    name="John Doe",
    email="john@example.com",
    password="SecurePass123",
    confirm_password="SecurePass123",
    career_goal="Data Scientist"
)

# Login
result = db.login(
    email="john@example.com",
    password="SecurePass123",
    remember_me=True
)

# Password reset
reset_result = db.request_password_reset("john@example.com")
if reset_result["success"]:
    token = reset_result["reset_token"]
    db.reset_password(token, "NewPass456", "NewPass456")
```

## Security Considerations

### Password Hashing

- Uses **bcrypt** with 12 rounds (configurable)
- Automatic salt generation per password
- Timing-safe password comparison

### Session Security

- Cryptographically secure random tokens (48 bytes)
- Session expiry (30 days for "Remember Me")
- Automatic cleanup of expired sessions

### Input Validation

- Email format validation
- Password strength requirements
- Duplicate email prevention
- SQL injection prevention (parameterized queries)

## Configuration

### Environment Variables

| Variable         | Description                      | Default                  |
| ---------------- | -------------------------------- | ------------------------ |
| `JWT_SECRET_KEY` | Secret key for JWT tokens        | Auto-generated dev key   |
| `AUTH_SALT`      | Salt for legacy password hashing | (deprecated, use bcrypt) |

### Database Location

Default: `data/users.db`

Can be customized:

```python
from src.auth.auth_database import AuthDatabase

db = AuthDatabase(db_path="custom/path/auth.db")
```

## API Reference

### AuthDatabase Class

| Method                                                         | Description             |
| -------------------------------------------------------------- | ----------------------- |
| `signup(name, email, password, confirm_password, career_goal)` | Register new user       |
| `login(email, password, remember_me)`                          | Authenticate user       |
| `validate_session(session_token)`                              | Validate session token  |
| `invalidate_session(session_token)`                            | Logout (single session) |
| `invalidate_all_sessions(user_id)`                             | Logout everywhere       |
| `request_password_reset(email)`                                | Get reset token         |
| `reset_password(token, new_password, confirm_password)`        | Reset password          |
| `get_user_by_id(user_id)`                                      | Get user profile        |
| `update_profile(user_id, name, career_goal)`                   | Update profile          |
| `change_password(user_id, current, new, confirm)`              | Change password         |

### Streamlit Auth Functions

| Function                  | Description                |
| ------------------------- | -------------------------- |
| `render_auth_page()`      | Render login/signup UI     |
| `is_authenticated()`      | Check if user is logged in |
| `get_current_user()`      | Get current user data      |
| `logout()`                | Log out current user       |
| `render_user_menu()`      | Render user profile menu   |
| `render_welcome_header()` | Render welcome message     |

## Testing

Run the test suite:

```bash
python scripts/test_auth_system.py
```

Expected output:

```
============================================================
   AUTHENTICATION SYSTEM TEST SUITE
============================================================

✅ Password hashing tests passed!
✅ User registration tests passed!
✅ User login tests passed!
✅ Password reset tests passed!
✅ Session management tests passed!

============================================================
   🎉 ALL TESTS PASSED!
============================================================
```

## Troubleshooting

### Common Issues

1. **"bcrypt not installed"**

   ```bash
   pip install bcrypt
   ```

2. **"database is locked"**
   - Ensure only one connection is active at a time
   - The code handles this automatically

3. **Session not persisting**
   - Check that "Remember Me" is checked
   - Session tokens expire after 30 days

### Resetting the Database

To clear all users and start fresh:

```python
import os
os.remove("data/users.db")
```

Or manually delete the `data/users.db` file.

## Career Goals List

Predefined career goals available in signup:

- AI Engineer
- Data Scientist
- Machine Learning Engineer
- Software Developer
- Full Stack Developer
- Backend Developer
- Frontend Developer
- DevOps Engineer
- Cloud Architect
- Data Engineer
- Business Analyst
- Product Manager
- Cybersecurity Analyst
- Mobile App Developer
- Web Developer
- Other

---

_Last updated: March 2026_
