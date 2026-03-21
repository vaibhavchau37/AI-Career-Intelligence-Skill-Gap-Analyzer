"""
FastAPI auth router — /auth/register, /auth/login, /auth/me, /auth/verify.

Mount this in backend.py:
    app.include_router(auth_router, prefix="/auth", tags=["auth"])
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from .jwt_handler import create_access_token, decode_access_token
from .user_store  import UserStore
from .models      import (
    RegisterRequest, LoginRequest, TokenResponse,
    UserProfile, MessageResponse, ChangePasswordRequest,
)

auth_router = APIRouter()
_store      = UserStore()
_oauth2     = OAuth2PasswordBearer(tokenUrl="/auth/token")


# ── Dependency: resolve current user from Bearer token ────────────────────

def _get_current_user(token: str = Depends(_oauth2)) -> dict:
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = _store.get_user_by_id(payload.get("user_id"))
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user


# ── Endpoints ──────────────────────────────────────────────────────────────

@auth_router.post("/register", response_model=TokenResponse, status_code=201)
def register(req: RegisterRequest):
    """Register a new account and return a JWT token immediately."""
    result = _store.register(
        username=req.username,
        email=req.email,
        password=req.password,
        full_name=req.full_name or "",
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    user = _store.get_user_by_id(result["user_id"])
    token = create_access_token({
        "user_id":  user["id"],
        "username": user["username"],
        "email":    user["email"],
    })
    return TokenResponse(
        access_token=token,
        user_id=user["id"],
        username=user["username"],
        email=user["email"],
        full_name=user["full_name"] or "",
    )


@auth_router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest):
    """Login and return a JWT token."""
    result = _store.login(req.username, req.password)
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result["message"],
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token({
        "user_id":  result["user_id"],
        "username": result["username"],
        "email":    result["email"],
    })
    return TokenResponse(
        access_token=token,
        user_id=result["user_id"],
        username=result["username"],
        email=result["email"],
        full_name=result["full_name"],
    )


@auth_router.post("/token", response_model=TokenResponse)
def oauth2_login(form: OAuth2PasswordRequestForm = Depends()):
    """OAuth2-compatible login endpoint (username + password form)."""
    return login(LoginRequest(username=form.username, password=form.password))


@auth_router.get("/me", response_model=UserProfile)
def me(user: dict = Depends(_get_current_user)):
    """Return the currently authenticated user's profile."""
    return UserProfile(
        user_id=user["id"],
        username=user["username"],
        email=user["email"],
        full_name=user["full_name"] or "",
        created_at=user.get("created_at"),
        last_login=user.get("last_login"),
    )


@auth_router.get("/verify")
def verify_token(user: dict = Depends(_get_current_user)):
    """Verify a JWT token is still valid (returns {valid: true} or 401)."""
    return {"valid": True, "username": user["username"], "user_id": user["id"]}


@auth_router.post("/change-password", response_model=MessageResponse)
def change_password(req: ChangePasswordRequest,
                    user: dict = Depends(_get_current_user)):
    """Change the current user's password."""
    result = _store.change_password(
        user_id=user["id"],
        old_password=req.old_password,
        new_password=req.new_password,
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return MessageResponse(success=True, message="Password updated successfully.")
