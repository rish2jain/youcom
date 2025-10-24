"""Authentication and user management API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta
import logging

from app.database import get_db
from app.models.user import User, UserRole
from app.models.audit_log import AuditLog, AuditAction
from app.schemas.auth import (
    UserLogin,
    UserRegister,
    TokenResponse,
    TokenRefresh,
    UserResponse,
    UserCreate,
    UserUpdate,
    PasswordChange,
    SSOLoginRequest
)
from app.services.auth_service import (
    AuthService,
    get_current_user,
    require_admin
)
from app.config import settings

router = APIRouter(prefix="/auth", tags=["authentication"])
logger = logging.getLogger(__name__)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user"""
    try:
        # Check if user already exists
        result = await db.execute(
            select(User).where(
                (User.email == user_data.email) | (User.username == user_data.username)
            )
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email or username already exists"
            )

        # Create new user
        hashed_password = AuthService.get_password_hash(user_data.password)
        new_user = User(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            role=UserRole.ANALYST,  # Default role
            is_active=True
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        # Create audit log
        audit_log = AuditLog(
            user_id=new_user.id,
            action=AuditAction.CREATE,
            resource_type="user",
            resource_id=new_user.id,
            description=f"User registered: {new_user.email}",
            success=True
        )
        db.add(audit_log)
        await db.commit()

        # Generate tokens
        access_token = AuthService.create_access_token(
            data={"sub": new_user.id, "role": new_user.role.value}
        )
        refresh_token = AuthService.create_refresh_token(
            data={"sub": new_user.id}
        )

        logger.info(f"✅ User registered: {new_user.email}")

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60
        )

    except Exception as e:
        logger.error(f"❌ Registration error: {str(e)}")
        raise


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """Login with email and password"""
    try:
        # Find user by email
        result = await db.execute(
            select(User).where(User.email == credentials.email)
        )
        user = result.scalar_one_or_none()

        if not user or not AuthService.verify_password(credentials.password, user.hashed_password):
            # Create failed login audit log
            audit_log = AuditLog(
                action=AuditAction.LOGIN,
                resource_type="user",
                description=f"Failed login attempt for: {credentials.email}",
                success=False,
                error_message="Invalid credentials"
            )
            db.add(audit_log)
            await db.commit()

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )

        # Create successful login audit log
        audit_log = AuditLog(
            user_id=user.id,
            action=AuditAction.LOGIN,
            resource_type="user",
            resource_id=user.id,
            description=f"User logged in: {user.email}",
            success=True
        )
        db.add(audit_log)
        await db.commit()

        # Generate tokens
        access_token = AuthService.create_access_token(
            data={"sub": user.id, "role": user.role.value}
        )
        refresh_token = AuthService.create_refresh_token(
            data={"sub": user.id}
        )

        logger.info(f"✅ User logged in: {user.email}")

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_data: TokenRefresh,
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token using refresh token"""
    try:
        payload = AuthService.decode_token(token_data.refresh_token)

        # Verify it's a refresh token
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )

        user_id = payload.get("sub")

        # Fetch user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        # Generate new tokens
        access_token = AuthService.create_access_token(
            data={"sub": user.id, "role": user.role.value}
        )
        refresh_token = AuthService.create_refresh_token(
            data={"sub": user.id}
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not refresh token"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user information"""
    try:
        update_data = user_update.dict(exclude_unset=True)

        # Users cannot change their own role
        if "role" in update_data:
            del update_data["role"]

        # Check if email/username is already taken
        if "email" in update_data or "username" in update_data:
            query = select(User).where(User.id != current_user.id)
            if "email" in update_data:
                query = query.where(User.email == update_data["email"])
            if "username" in update_data:
                query = query.where(User.username == update_data["username"])

            result = await db.execute(query)
            if result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email or username already in use"
                )

        # Update user
        for field, value in update_data.items():
            setattr(current_user, field, value)

        await db.commit()
        await db.refresh(current_user)

        # Audit log
        audit_log = AuditLog(
            user_id=current_user.id,
            action=AuditAction.UPDATE,
            resource_type="user",
            resource_id=current_user.id,
            description="User updated their profile",
            new_values=update_data,
            success=True
        )
        db.add(audit_log)
        await db.commit()

        logger.info(f"✅ User updated: {current_user.email}")
        return current_user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ User update error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Change user password"""
    try:
        # Verify current password
        if not AuthService.verify_password(password_data.current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect current password"
            )

        # Update password
        current_user.hashed_password = AuthService.get_password_hash(password_data.new_password)
        await db.commit()

        # Audit log
        audit_log = AuditLog(
            user_id=current_user.id,
            action=AuditAction.UPDATE,
            resource_type="user",
            resource_id=current_user.id,
            description="User changed password",
            success=True
        )
        db.add(audit_log)
        await db.commit()

        logger.info(f"✅ Password changed for user: {current_user.email}")
        return {"message": "Password changed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Password change error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )


# Admin-only endpoints
@router.get("/users", response_model=list[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """List all users (admin only)"""
    result = await db.execute(
        select(User).offset(skip).limit(limit).order_by(User.created_at.desc())
    )
    users = result.scalars().all()
    return users


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create a new user (admin only)"""
    try:
        # Check if user exists
        result = await db.execute(
            select(User).where(
                (User.email == user_data.email) | (User.username == user_data.username)
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already exists"
            )

        # Create user
        hashed_password = AuthService.get_password_hash(user_data.password)
        new_user = User(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            role=user_data.role,
            is_active=True
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        # Audit log
        audit_log = AuditLog(
            user_id=current_user.id,
            action=AuditAction.CREATE,
            resource_type="user",
            resource_id=new_user.id,
            description=f"Admin created user: {new_user.email}",
            success=True
        )
        db.add(audit_log)
        await db.commit()

        logger.info(f"✅ Admin {current_user.email} created user: {new_user.email}")
        return new_user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ User creation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update a user (admin only)"""
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        update_data = user_update.dict(exclude_unset=True)
        old_values = {k: getattr(user, k) for k in update_data.keys()}

        for field, value in update_data.items():
            setattr(user, field, value)

        await db.commit()
        await db.refresh(user)

        # Audit log
        audit_log = AuditLog(
            user_id=current_user.id,
            action=AuditAction.UPDATE,
            resource_type="user",
            resource_id=user.id,
            description=f"Admin updated user: {user.email}",
            old_values=old_values,
            new_values=update_data,
            success=True
        )
        db.add(audit_log)
        await db.commit()

        logger.info(f"✅ Admin {current_user.email} updated user: {user.email}")
        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ User update error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete a user (admin only)"""
    try:
        if user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )

        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Audit log before deletion
        audit_log = AuditLog(
            user_id=current_user.id,
            action=AuditAction.DELETE,
            resource_type="user",
            resource_id=user.id,
            description=f"Admin deleted user: {user.email}",
            success=True
        )
        db.add(audit_log)

        await db.delete(user)
        await db.commit()

        logger.info(f"✅ Admin {current_user.email} deleted user: {user.email}")
        return {"message": "User deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ User deletion error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )
