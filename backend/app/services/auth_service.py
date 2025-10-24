"""Authentication service for JWT token management and password hashing"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.config import settings
from app.models.user import User, UserRole
from app.database import get_db

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token scheme
security = HTTPBearer()


class AuthService:
    """Service for authentication and authorization"""

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)

    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)

        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
        return encoded_jwt

    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """Create a JWT refresh token (longer expiration)"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=7)  # 7 days for refresh token
        to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
        return encoded_jwt

    @staticmethod
    def decode_token(token: str) -> Dict[str, Any]:
        """Decode and validate a JWT token"""
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            return payload
        except JWTError as e:
            logger.error(f"JWT decode error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )


# Dependency to get current user from token
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get the current authenticated user from JWT token"""

    token = credentials.credentials

    try:
        payload = AuthService.decode_token(token)
        user_id: int = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Fetch user from database
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    # Update last login
    user.last_login_at = datetime.utcnow()
    await db.commit()

    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def require_role(required_role: UserRole):
    """Dependency factory to require specific role"""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        # Role hierarchy: admin > analyst > viewer
        role_hierarchy = {
            UserRole.ADMIN: 3,
            UserRole.ANALYST: 2,
            UserRole.VIEWER: 1
        }

        user_level = role_hierarchy.get(current_user.role, 0)
        required_level = role_hierarchy.get(required_role, 0)

        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role.value}"
            )

        return current_user

    return role_checker


# Convenience dependencies for common roles
async def require_analyst(current_user: User = Depends(get_current_user)) -> User:
    """Require analyst or higher role"""
    return await require_role(UserRole.ANALYST)(current_user)


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require admin role"""
    return await require_role(UserRole.ADMIN)(current_user)


# SSO authentication helpers
class SSOService:
    """Service for SSO authentication"""

    @staticmethod
    async def authenticate_with_google(token: str, db: AsyncSession) -> User:
        """Authenticate user with Google SSO"""
        # In production, verify token with Google API
        # For now, this is a placeholder
        raise NotImplementedError("Google SSO not yet implemented")

    @staticmethod
    async def authenticate_with_okta(token: str, db: AsyncSession) -> User:
        """Authenticate user with Okta SSO"""
        raise NotImplementedError("Okta SSO not yet implemented")

    @staticmethod
    async def authenticate_with_azure(token: str, db: AsyncSession) -> User:
        """Authenticate user with Azure AD SSO"""
        raise NotImplementedError("Azure AD SSO not yet implemented")

    @staticmethod
    async def link_sso_account(user: User, provider: str, sso_id: str, db: AsyncSession) -> User:
        """Link an SSO account to existing user"""
        user.sso_provider = provider
        user.sso_id = sso_id
        await db.commit()
        await db.refresh(user)
        return user
