"""Workspace management API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
import logging

from app.database import get_db
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember, WorkspaceRole
from app.models.audit_log import AuditLog, AuditAction
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceUpdate,
    WorkspaceResponse,
    WorkspaceMemberInvite,
    WorkspaceMemberUpdate,
    WorkspaceMemberResponse
)
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/workspaces", tags=["workspaces"])
logger = logging.getLogger(__name__)


async def get_workspace_member(
    workspace_id: int,
    current_user: User,
    db: AsyncSession,
    required_role: WorkspaceRole = None
) -> WorkspaceMember:
    """Helper to get workspace member and check permissions"""
    result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == current_user.id
        )
    )
    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this workspace"
        )

    if required_role:
        role_hierarchy = {
            WorkspaceRole.OWNER: 4,
            WorkspaceRole.ADMIN: 3,
            WorkspaceRole.MEMBER: 2,
            WorkspaceRole.GUEST: 1
        }

        if role_hierarchy.get(member.role, 0) < role_hierarchy.get(required_role, 0):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {required_role.value}"
            )

    return member


@router.post("/", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    workspace_data: WorkspaceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new workspace"""
    try:
        # Check if slug already exists
        result = await db.execute(
            select(Workspace).where(Workspace.slug == workspace_data.slug)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Workspace slug already exists"
            )

        # Create workspace
        workspace = Workspace(
            name=workspace_data.name,
            slug=workspace_data.slug,
            description=workspace_data.description,
            max_members=workspace_data.max_members,
            allow_guest_access=workspace_data.allow_guest_access
        )

        db.add(workspace)
        await db.flush()  # Get workspace ID

        # Add creator as owner
        owner_member = WorkspaceMember(
            workspace_id=workspace.id,
            user_id=current_user.id,
            role=WorkspaceRole.OWNER
        )

        db.add(owner_member)
        await db.commit()
        await db.refresh(workspace)

        # Audit log
        audit_log = AuditLog(
            user_id=current_user.id,
            action=AuditAction.CREATE,
            resource_type="workspace",
            resource_id=workspace.id,
            workspace_id=workspace.id,
            description=f"Created workspace: {workspace.name}",
            success=True
        )
        db.add(audit_log)
        await db.commit()

        logger.info(f"✅ Workspace created: {workspace.name} by {current_user.email}")

        response = WorkspaceResponse.from_orm(workspace)
        response.member_count = 1
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Workspace creation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create workspace"
        )


@router.get("/", response_model=List[WorkspaceResponse])
async def list_workspaces(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List workspaces user is a member of"""
    result = await db.execute(
        select(Workspace)
        .join(WorkspaceMember)
        .where(WorkspaceMember.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .order_by(Workspace.created_at.desc())
    )
    workspaces = result.scalars().all()

    # Get member counts
    response_list = []
    for workspace in workspaces:
        count_result = await db.execute(
            select(func.count(WorkspaceMember.id)).where(
                WorkspaceMember.workspace_id == workspace.id
            )
        )
        member_count = count_result.scalar()

        ws_response = WorkspaceResponse.from_orm(workspace)
        ws_response.member_count = member_count
        response_list.append(ws_response)

    return response_list


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get workspace details"""
    # Verify membership
    await get_workspace_member(workspace_id, current_user, db)

    result = await db.execute(
        select(Workspace).where(Workspace.id == workspace_id)
    )
    workspace = result.scalar_one_or_none()

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )

    # Get member count
    count_result = await db.execute(
        select(func.count(WorkspaceMember.id)).where(
            WorkspaceMember.workspace_id == workspace.id
        )
    )
    member_count = count_result.scalar()

    response = WorkspaceResponse.from_orm(workspace)
    response.member_count = member_count
    return response


@router.put("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: int,
    workspace_update: WorkspaceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update workspace (admin/owner only)"""
    try:
        # Verify admin permission
        await get_workspace_member(workspace_id, current_user, db, WorkspaceRole.ADMIN)

        result = await db.execute(
            select(Workspace).where(Workspace.id == workspace_id)
        )
        workspace = result.scalar_one_or_none()

        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found"
            )

        update_data = workspace_update.dict(exclude_unset=True)
        old_values = {k: getattr(workspace, k) for k in update_data.keys()}

        for field, value in update_data.items():
            setattr(workspace, field, value)

        await db.commit()
        await db.refresh(workspace)

        # Audit log
        audit_log = AuditLog(
            user_id=current_user.id,
            action=AuditAction.UPDATE,
            resource_type="workspace",
            resource_id=workspace.id,
            workspace_id=workspace.id,
            description=f"Updated workspace: {workspace.name}",
            old_values=old_values,
            new_values=update_data,
            success=True
        )
        db.add(audit_log)
        await db.commit()

        logger.info(f"✅ Workspace updated: {workspace.name}")

        response = WorkspaceResponse.from_orm(workspace)
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Workspace update error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update workspace"
        )


@router.delete("/{workspace_id}")
async def delete_workspace(
    workspace_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete workspace (owner only)"""
    try:
        # Verify owner permission
        await get_workspace_member(workspace_id, current_user, db, WorkspaceRole.OWNER)

        result = await db.execute(
            select(Workspace).where(Workspace.id == workspace_id)
        )
        workspace = result.scalar_one_or_none()

        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found"
            )

        # Audit log before deletion
        audit_log = AuditLog(
            user_id=current_user.id,
            action=AuditAction.DELETE,
            resource_type="workspace",
            resource_id=workspace.id,
            workspace_id=workspace.id,
            description=f"Deleted workspace: {workspace.name}",
            success=True
        )
        db.add(audit_log)

        await db.delete(workspace)
        await db.commit()

        logger.info(f"✅ Workspace deleted: {workspace.name}")
        return {"message": "Workspace deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Workspace deletion error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete workspace"
        )


# Workspace Members Management
@router.get("/{workspace_id}/members", response_model=List[WorkspaceMemberResponse])
async def list_workspace_members(
    workspace_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List workspace members"""
    # Verify membership
    await get_workspace_member(workspace_id, current_user, db)

    result = await db.execute(
        select(WorkspaceMember, User)
        .join(User, WorkspaceMember.user_id == User.id)
        .where(WorkspaceMember.workspace_id == workspace_id)
        .order_by(WorkspaceMember.joined_at.desc())
    )

    members_data = result.all()
    members_response = []

    for member, user in members_data:
        member_response = WorkspaceMemberResponse.from_orm(member)
        member_response.user_email = user.email
        member_response.user_username = user.username
        member_response.user_full_name = user.full_name
        members_response.append(member_response)

    return members_response


@router.post("/{workspace_id}/members", response_model=WorkspaceMemberResponse, status_code=status.HTTP_201_CREATED)
async def invite_workspace_member(
    workspace_id: int,
    invite_data: WorkspaceMemberInvite,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Invite member to workspace (admin/owner only)"""
    try:
        # Verify admin permission
        await get_workspace_member(workspace_id, current_user, db, WorkspaceRole.ADMIN)

        # Check if user exists
        user_result = await db.execute(
            select(User).where(User.id == invite_data.user_id)
        )
        user = user_result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Check if already a member
        existing_result = await db.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == invite_data.user_id
            )
        )
        if existing_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a member"
            )

        # Create membership
        new_member = WorkspaceMember(
            workspace_id=workspace_id,
            user_id=invite_data.user_id,
            role=invite_data.role,
            invited_by=current_user.id
        )

        db.add(new_member)
        await db.commit()
        await db.refresh(new_member)

        # Audit log
        audit_log = AuditLog(
            user_id=current_user.id,
            action=AuditAction.CREATE,
            resource_type="workspace_member",
            resource_id=new_member.id,
            workspace_id=workspace_id,
            description=f"Invited {user.email} to workspace",
            success=True
        )
        db.add(audit_log)
        await db.commit()

        logger.info(f"✅ User {user.email} invited to workspace {workspace_id}")

        response = WorkspaceMemberResponse.from_orm(new_member)
        response.user_email = user.email
        response.user_username = user.username
        response.user_full_name = user.full_name
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Member invite error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to invite member"
        )


@router.put("/{workspace_id}/members/{member_id}", response_model=WorkspaceMemberResponse)
async def update_workspace_member(
    workspace_id: int,
    member_id: int,
    member_update: WorkspaceMemberUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update workspace member role (admin/owner only)"""
    try:
        # Verify admin permission
        await get_workspace_member(workspace_id, current_user, db, WorkspaceRole.ADMIN)

        result = await db.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.id == member_id,
                WorkspaceMember.workspace_id == workspace_id
            )
        )
        member = result.scalar_one_or_none()

        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found"
            )

        old_role = member.role
        member.role = member_update.role

        await db.commit()
        await db.refresh(member)

        # Audit log
        audit_log = AuditLog(
            user_id=current_user.id,
            action=AuditAction.PERMISSION_CHANGE,
            resource_type="workspace_member",
            resource_id=member.id,
            workspace_id=workspace_id,
            description=f"Changed member role from {old_role.value} to {member_update.role.value}",
            old_values={"role": old_role.value},
            new_values={"role": member_update.role.value},
            success=True
        )
        db.add(audit_log)
        await db.commit()

        logger.info(f"✅ Workspace member role updated")
        return WorkspaceMemberResponse.from_orm(member)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Member update error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update member"
        )


@router.delete("/{workspace_id}/members/{member_id}")
async def remove_workspace_member(
    workspace_id: int,
    member_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove member from workspace (admin/owner only)"""
    try:
        # Verify admin permission
        await get_workspace_member(workspace_id, current_user, db, WorkspaceRole.ADMIN)

        result = await db.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.id == member_id,
                WorkspaceMember.workspace_id == workspace_id
            )
        )
        member = result.scalar_one_or_none()

        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found"
            )

        # Cannot remove owner
        if member.role == WorkspaceRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove workspace owner"
            )

        # Audit log before deletion
        audit_log = AuditLog(
            user_id=current_user.id,
            action=AuditAction.DELETE,
            resource_type="workspace_member",
            resource_id=member.id,
            workspace_id=workspace_id,
            description=f"Removed member from workspace",
            success=True
        )
        db.add(audit_log)

        await db.delete(member)
        await db.commit()

        logger.info(f"✅ Workspace member removed")
        return {"message": "Member removed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Member removal error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove member"
        )
