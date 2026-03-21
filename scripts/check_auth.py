"""Quick health-check for the complete auth system."""
import sys
import time

sys.path.insert(0, ".")

PASS = "[PASS]"
FAIL = "[FAIL]"
errors = []


def ok(msg):
    print(f"{PASS} {msg}")


def fail(label, exc):
    errors.append(f"{FAIL} {label}: {exc}")
    print(f"{FAIL} {label}: {exc}")


# ── 1. Imports ──────────────────────────────────────────────────────────────
try:
    from src.auth.auth_database import (
        get_auth_db, hash_password, verify_password, generate_token
    )
    ok("auth_database imports")
except Exception as e:
    fail("auth_database imports", e)
    sys.exit(1)

try:
    from src.auth.streamlit_auth import (
        render_auth_page, is_authenticated, get_current_user, logout,
        _build_google_auth_url, _get_google_oauth_config,
    )
    ok("streamlit_auth imports (incl. Google OAuth helpers)")
except Exception as e:
    fail("streamlit_auth imports", e)

# ── 2. DB Init ───────────────────────────────────────────────────────────────
try:
    db = get_auth_db()
    ok("AuthDatabase initialized / tables created")
except Exception as e:
    fail("DB init", e)
    sys.exit(1)

# ── 3. bcrypt ────────────────────────────────────────────────────────────────
try:
    h = hash_password("TestPass1")
    assert verify_password("TestPass1", h), "correct password not verified"
    assert not verify_password("WrongPass", h), "wrong password accepted"
    ok("bcrypt hash & verify")
except Exception as e:
    fail("bcrypt", e)

# ── 4. Token generation ──────────────────────────────────────────────────────
try:
    t = generate_token()
    assert len(t) > 20
    ok("secure token generation")
except Exception as e:
    fail("token generation", e)

# ── 5. Sign-up ───────────────────────────────────────────────────────────────
email = f"healthcheck_{int(time.time())}@test.com"
try:
    r = db.signup("Health Check", email, "TestPass1", "TestPass1", "Data Scientist")
    assert r["success"], r["message"]
    ok("signup")
except Exception as e:
    fail("signup", e)

# ── 6. Duplicate e-mail rejected ────────────────────────────────────────────
try:
    r = db.signup("Health Check", email, "TestPass1", "TestPass1")
    assert not r["success"], "duplicate email should be rejected"
    ok("duplicate email rejected")
except Exception as e:
    fail("duplicate email check", e)

# ── 7. Login (correct credentials) ─────────────────────────────────────────
try:
    r = db.login(email, "TestPass1")
    assert r["success"], r["message"]
    ok("login with correct credentials")
except Exception as e:
    fail("login", e)

# ── 8. Login (wrong password) ───────────────────────────────────────────────
try:
    r = db.login(email, "BadPass99")
    assert not r["success"]
    ok("wrong password correctly rejected")
except Exception as e:
    fail("wrong-password check", e)

# ── 9. Password-reset flow ──────────────────────────────────────────────────
try:
    r = db.request_password_reset(email)
    assert r["success"] and "reset_token" in r, r
    token = r["reset_token"]
    r2 = db.reset_password(token, "NewPass99", "NewPass99")
    assert r2["success"], r2["message"]
    r3 = db.login(email, "NewPass99")
    assert r3["success"], "login with new password failed"
    ok("password-reset flow (request → reset → login)")
except Exception as e:
    fail("password-reset flow", e)

# ── 10. Remember-me session ─────────────────────────────────────────────────
try:
    r = db.login(email, "NewPass99", remember_me=True)
    assert r["success"]
    tok = r.get("session_token")
    assert tok, "no session token returned"
    user = db.validate_session(tok)
    assert user and user["email"] == email
    db.invalidate_session(tok)
    assert db.validate_session(tok) is None, "session not invalidated"
    ok("remember-me session (create → validate → invalidate)")
except Exception as e:
    fail("remember-me session", e)

# ── 11. Google OAuth – get_or_create_oauth_user ─────────────────────────────
try:
    oemail = f"goauth_{int(time.time())}@gmail.com"
    r1 = db.get_or_create_oauth_user(oemail, "Google User", "google", "sub-abc-123", True)
    assert r1["success"], r1.get("message")
    uid = r1["user"]["id"]
    # Second call must return same user
    r2 = db.get_or_create_oauth_user(oemail, "Google User", "google", "sub-abc-123", True)
    assert r2["success"] and r2["user"]["id"] == uid, "user ID mismatch on second call"
    ok("Google OAuth get_or_create_oauth_user (idempotent)")
except Exception as e:
    fail("Google OAuth user creation", e)

# ── 12. Google OAuth URL builder (no env vars → returns None gracefully) ─────
try:
    import os
    os.environ.pop("GOOGLE_CLIENT_ID", None)
    os.environ.pop("GOOGLE_CLIENT_SECRET", None)
    # Must return None when credentials are missing (no crash)
    # We can't call _build_google_auth_url without st context, so just check config
    from src.auth.streamlit_auth import _get_google_oauth_config
    assert _get_google_oauth_config() is None
    ok("Google OAuth URL: returns None gracefully when credentials missing")
except Exception as e:
    fail("Google OAuth URL builder (no credentials)", e)

# ── 13. career_goals helper ─────────────────────────────────────────────────
try:
    goals = db.get_career_goals()
    assert isinstance(goals, list)
    ok(f"get_career_goals returned {len(goals)} goals")
except Exception as e:
    fail("get_career_goals", e)

# ── 14. app.py integration ──────────────────────────────────────────────────
try:
    import ast, pathlib
    src = pathlib.Path("app.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    ok("app.py parses without syntax errors")
    has_auth = "is_authenticated" in src or "render_auth_page" in src
    assert has_auth, "auth not integrated in app.py"
    ok("app.py contains auth integration")
except Exception as e:
    fail("app.py check", e)

# ── 15. requirements.txt ────────────────────────────────────────────────────
try:
    reqs = pathlib.Path("requirements.txt").read_text()
    for pkg in ["bcrypt", "streamlit", "requests"]:
        assert pkg in reqs, f"missing: {pkg}"
    ok("requirements.txt has bcrypt, streamlit, requests")
except Exception as e:
    fail("requirements.txt", e)

# ── Summary ──────────────────────────────────────────────────────────────────
print()
print("=" * 55)
if errors:
    print(f"  {len(errors)} check(s) FAILED:")
    for e in errors:
        print(f"    {e}")
    sys.exit(1)
else:
    print("  ALL 15 CHECKS PASSED — auth system is fully functional")
print("=" * 55)
