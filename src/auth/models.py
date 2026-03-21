"""
Pydantic models for the Auth API.
"""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator


class RegisterRequest(BaseModel):
    username:  str
    email:     EmailStr
    password:  str
    full_name: Optional[str] = ""

    @field_validator("username")
    @classmethod
    def username_min_length(cls, v: str) -> str:
        if len(v.strip()) < 3:
            raise ValueError("Username must be at least 3 characters.")
        return v.strip()

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters.")
        return v


class LoginRequest(BaseModel):
    username: str   # accepts username OR email
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    user_id:      int
    username:     str
    email:        str
    full_name:    str


class UserProfile(BaseModel):
    user_id:    int
    username:   str
    email:      str
    full_name:  str
    created_at: Optional[str] = None
    last_login: Optional[str] = None


class MessageResponse(BaseModel):
    success: bool
    message: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
