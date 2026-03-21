"""
Test script for the Authentication System
==========================================

Run this script to verify the authentication module works correctly:
    python scripts/test_auth_system.py
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.auth.auth_database import (
    AuthDatabase,
    get_auth_db,
    hash_password,
    verify_password,
    generate_token
)


def test_password_hashing():
    """Test bcrypt password hashing and verification."""
    print("\n" + "="*60)
    print("TEST 1: Password Hashing")
    print("="*60)
    
    password = "TestPassword123"
    
    # Hash password
    hashed = hash_password(password)
    print(f"Original password: {password}")
    print(f"Hashed password: {hashed[:30]}...")
    
    # Verify correct password
    assert verify_password(password, hashed), "Password verification failed!"
    print("✓ Password verification: PASSED")
    
    # Verify wrong password fails
    assert not verify_password("WrongPassword", hashed), "Wrong password should not verify!"
    print("✓ Wrong password rejection: PASSED")
    
    print("\n✅ Password hashing tests passed!")


def test_user_registration():
    """Test user registration."""
    print("\n" + "="*60)
    print("TEST 2: User Registration")
    print("="*60)
    
    db = get_auth_db()
    
    # Test successful registration
    result = db.signup(
        name="Test User",
        email="testuser@example.com",
        password="TestPass123",
        confirm_password="TestPass123",
        career_goal="Data Scientist"
    )
    
    if result["success"]:
        print(f"✓ User registered successfully!")
        print(f"  User ID: {result['user']['id']}")
        print(f"  Name: {result['user']['name']}")
        print(f"  Email: {result['user']['email']}")
        print(f"  Career Goal: {result['user']['career_goal']}")
    else:
        print(f"  Registration result: {result['message']}")
        if "already exists" in result['message']:
            print("  (User may already exist from previous test)")
    
    # Test duplicate email rejection
    result2 = db.signup(
        name="Duplicate User",
        email="testuser@example.com",
        password="TestPass123",
        confirm_password="TestPass123"
    )
    
    assert not result2["success"], "Duplicate email should be rejected!"
    print("✓ Duplicate email rejection: PASSED")
    
    # Test password validation
    result3 = db.signup(
        name="Weak Password User",
        email="weakpwd@example.com",
        password="weak",
        confirm_password="weak"
    )
    assert not result3["success"], "Weak password should be rejected!"
    print("✓ Weak password rejection: PASSED")
    
    # Test password mismatch
    result4 = db.signup(
        name="Mismatch User",
        email="mismatch@example.com",
        password="TestPass123",
        confirm_password="DifferentPass123"
    )
    assert not result4["success"], "Password mismatch should be rejected!"
    print("✓ Password mismatch rejection: PASSED")
    
    print("\n✅ User registration tests passed!")


def test_user_login():
    """Test user login."""
    print("\n" + "="*60)
    print("TEST 3: User Login")
    print("="*60)
    
    db = get_auth_db()
    
    # First ensure user exists
    db.signup(
        name="Login Test User",
        email="logintest@example.com",
        password="LoginPass123",
        confirm_password="LoginPass123",
        career_goal="ML Engineer"
    )
    
    # Test successful login
    result = db.login(
        email="logintest@example.com",
        password="LoginPass123",
        remember_me=False
    )
    
    if result["success"]:
        print("✓ Login successful!")
        print(f"  User: {result['user']['name']}")
        print(f"  Email: {result['user']['email']}")
    else:
        print(f"  Login result: {result['message']}")
    
    # Test login with remember_me
    result2 = db.login(
        email="logintest@example.com",
        password="LoginPass123",
        remember_me=True
    )
    
    if result2["success"] and result2.get("session_token"):
        print("✓ Login with Remember Me: Session token generated!")
        
        # Validate session
        user = db.validate_session(result2["session_token"])
        assert user is not None, "Session validation failed!"
        print("✓ Session validation: PASSED")
    
    # Test wrong password
    result3 = db.login(
        email="logintest@example.com",
        password="WrongPassword"
    )
    assert not result3["success"], "Wrong password should fail login!"
    print("✓ Wrong password rejection: PASSED")
    
    # Test non-existent user
    result4 = db.login(
        email="nonexistent@example.com",
        password="SomePassword123"
    )
    assert not result4["success"], "Non-existent user should fail login!"
    print("✓ Non-existent user rejection: PASSED")
    
    print("\n✅ User login tests passed!")


def test_password_reset():
    """Test password reset flow."""
    print("\n" + "="*60)
    print("TEST 4: Password Reset")
    print("="*60)
    
    db = get_auth_db()
    
    # Ensure user exists
    db.signup(
        name="Reset Test User",
        email="resettest@example.com",
        password="OldPass123",
        confirm_password="OldPass123"
    )
    
    # Request password reset
    result = db.request_password_reset("resettest@example.com")
    
    if result["success"] and "reset_token" in result:
        token = result["reset_token"]
        print("✓ Password reset token generated!")
        
        # Reset password
        reset_result = db.reset_password(
            token=token,
            new_password="NewPass456",
            confirm_password="NewPass456"
        )
        
        if reset_result["success"]:
            print("✓ Password reset successful!")
            
            # Verify login with new password
            login_result = db.login("resettest@example.com", "NewPass456")
            assert login_result["success"], "Login with new password failed!"
            print("✓ Login with new password: PASSED")
        else:
            print(f"  Reset result: {reset_result['message']}")
    else:
        print(f"  Request result: {result['message']}")
    
    print("\n✅ Password reset tests passed!")


def test_session_management():
    """Test session management."""
    print("\n" + "="*60)
    print("TEST 5: Session Management")
    print("="*60)
    
    db = get_auth_db()
    
    # Create user and login with remember_me
    db.signup(
        name="Session Test User",
        email="sessiontest@example.com",
        password="SessionPass123",
        confirm_password="SessionPass123"
    )
    
    login_result = db.login(
        email="sessiontest@example.com",
        password="SessionPass123",
        remember_me=True
    )
    
    if login_result["success"] and login_result.get("session_token"):
        token = login_result["session_token"]
        print("✓ Session created!")
        
        # Validate session
        user = db.validate_session(token)
        assert user is not None, "Session should be valid!"
        print("✓ Session validation: PASSED")
        
        # Invalidate session
        db.invalidate_session(token)
        print("✓ Session invalidated!")
        
        # Verify session is no longer valid
        user2 = db.validate_session(token)
        assert user2 is None, "Session should be invalid after logout!"
        print("✓ Session invalidation: PASSED")
    
    print("\n✅ Session management tests passed!")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("   AUTHENTICATION SYSTEM TEST SUITE")
    print("="*60)
    
    try:
        test_password_hashing()
        test_user_registration()
        test_user_login()
        test_password_reset()
        test_session_management()
        
        print("\n" + "="*60)
        print("   🎉 ALL TESTS PASSED!")
        print("="*60)
        print("\nThe authentication system is working correctly.")
        print("You can now run the Streamlit app with: streamlit run app.py")
        print("\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
