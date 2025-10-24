"""Pydantic schemas for authentication and user management"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
from app.models.user import UserRole


# Authentication schemas
class UserLogin(BaseModel):
    """User login request"""
    email: EmailStr
    password: str


class UserRegister(BaseModel):
    """User registration request"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None

    @validator('username')
    def username_alphanumeric(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username must be alphanumeric (underscores and hyphens allowed)')
        return v


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenRefresh(BaseModel):
    """Token refresh request"""
    refresh_token: str


# User schemas
class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    username: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Create user schema"""
    password: str
    role: UserRole = UserRole.ANALYST


class UserUpdate(BaseModel):
    """Update user schema"""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """User response schema"""
    id: int
    role: UserRole
    is_active: bool
    is_verified: bool
    sso_provider: Optional[str]
    created_at: datetime
    last_login_at: Optional[datetime]

    class Config:
        from_attributes = True


class PasswordChange(BaseModel):
    """Password change request"""
    current_password: str
    new_password: str = Field(..., min_length=8)


class PasswordReset(BaseModel):
    """Password reset request"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation"""
    token: str
    new_password: str = Field(..., min_length=8)


# SSO schemas
class SSOLoginRequest(BaseModel):
    """SSO login request"""
    provider: str  # google, okta, azure
    token: str  # SSO provider token


class SSOLinkRequest(BaseModel):
    """Link SSO account request"""
    provider: str
    sso_id: str
