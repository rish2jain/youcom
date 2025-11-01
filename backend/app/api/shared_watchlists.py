"""Shared watchlist API endpoints for collaborative monitoring"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func, desc
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models.shared_watchlist import SharedWatchlist, watchlist_assignments
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember, WorkspaceRole
from app.models.watch import WatchItem
from app.models.comment import Comment
from app.schemas.shared_watchlist import (
    SharedWatchlistCreate, SharedWatchlistUpdate, SharedWatchlistResponse,
    SharedWatchlistWithDetails, WatchlistAssignment, WatchlistAssignmentResponse,
    SharedWatchlistStats, WatchlistPermissionCheck, BulkWatchlistOperation
)

router = APIRouter(prefix="/shared-watchlists", tags=["shared-watchlists"])


from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
from app.config import settings

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current user from JWT token"""
    try:
        # Decode JWT token
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )
        
        # Extract user identifier
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Validate and normalize user_id type
        try:
            user_id_int = int(user_id)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user from database
        user = db.query(User).filter(User.id == user_id_int).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
        
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def check_workspace_permission(
    workspace_id: int,
    user: User,
    db: Session,
    required_role: WorkspaceRole = WorkspaceRole.MEMBER
) -> WorkspaceMember:
    """Check if user has required permission in workspace"""
    member = db.query(WorkspaceMember).filter(
        and_(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user.id
        )
    ).first()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this workspace"
        )

    # Role hierarchy check
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


def check_watchlist_permission(
    watchlist: SharedWatchlist,
    user: User,
    db: Session
) -> WatchlistPermissionCheck:
    """Check user permissions for a specific watchlist"""
    # Check workspace membership
    member = db.query(WorkspaceMember).filter(
        and_(
            WorkspaceMember.workspace_id == watchlist.workspace_id,
            WorkspaceMember.user_id == user.id
        )
    ).first()

    if not member:
        return WatchlistPermissionCheck(
            can_view=False, can_edit=False, can_delete=False,
            can_assign_users=False, is_creator=False, workspace_role="none"
        )

    is_creator = watchlist.created_by == user.id
    is_admin_or_owner = member.role in [WorkspaceRole.ADMIN, WorkspaceRole.OWNER]

    # Check if user is assigned to watchlist
    is_assigned = db.query(watchlist_assignments).filter(
        and_(
            watchlist_assignments.c.shared_watchlist_id == watchlist.id,
            watchlist_assignments.c.user_id == user.id
        )
    ).first() is not None

    can_view = watchlist.is_public or is_creator or is_assigned or is_admin_or_owner
    can_edit = is_creator or is_admin_or_owner
    can_delete = is_creator or member.role == WorkspaceRole.OWNER
    can_assign_users = is_creator or is_admin_or_owner

    return WatchlistPermissionCheck(
        can_view=can_view,
        can_edit=can_edit,
        can_delete=can_delete,
        can_assign_users=can_assign_users,
        is_creator=is_creator,
        workspace_role=member.role.value
    )


@router.post("/", response_model=SharedWatchlistResponse, status_code=status.HTTP_201_CREATED)
async def create_shared_watchlist(
    workspace_id: int,
    watchlist_data: SharedWatchlistCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new shared watchlist"""
    # Check workspace permission
    check_workspace_permission(workspace_id, current_user, db, WorkspaceRole.MEMBER)

    # Verify watch item exists and user has access
    watch_item = db.query(WatchItem).filter(WatchItem.id == watchlist_data.watch_item_id).first()
    if not watch_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watch item not found"
        )

    # Create shared watchlist
    shared_watchlist = SharedWatchlist(
        workspace_id=workspace_id,
        name=watchlist_data.name,
        description=watchlist_data.description,
        watch_item_id=watchlist_data.watch_item_id,
        created_by=current_user.id,
        is_public=watchlist_data.is_public
    )

    db.add(shared_watchlist)
    db.commit()
    db.refresh(shared_watchlist)

    # Automatically assign creator to the watchlist
    db.execute(
        watchlist_assignments.insert().values(
            shared_watchlist_id=shared_watchlist.id,
            user_id=current_user.id
        )
    )
    db.commit()

    return shared_watchlist


@router.get("/workspace/{workspace_id}", response_model=List[SharedWatchlistWithDetails])
async def list_workspace_watchlists(
    workspace_id: int,
    include_inactive: bool = Query(False, description="Include inactive watchlists"),
    only_assigned: bool = Query(False, description="Only show watchlists assigned to current user"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List shared watchlists in a workspace"""
    # Check workspace permission
    member = check_workspace_permission(workspace_id, current_user, db, WorkspaceRole.GUEST)

    query = db.query(SharedWatchlist).options(
        joinedload(SharedWatchlist.watch_item),
        joinedload(SharedWatchlist.assigned_users)
    ).filter(SharedWatchlist.workspace_id == workspace_id)

    # Filter by active status
    if not include_inactive:
        query = query.filter(SharedWatchlist.is_active == True)

    # Filter by assignment
    if only_assigned:
        query = query.join(watchlist_assignments).filter(
            watchlist_assignments.c.user_id == current_user.id
        )

    watchlists = query.order_by(desc(SharedWatchlist.created_at)).all()

    # Build response with details
    result = []
    for watchlist in watchlists:
        # Check if user can view this watchlist
        permissions = check_watchlist_permission(watchlist, current_user, db)
        if not permissions.can_view:
            continue

        # Get creator info
        creator = db.query(User).filter(User.id == watchlist.created_by).first()
        
        # Get assignment and comment counts
        assigned_count = db.query(func.count(watchlist_assignments.c.user_id)).filter(
            watchlist_assignments.c.shared_watchlist_id == watchlist.id
        ).scalar()
        
        comments_count = db.query(func.count(Comment.id)).filter(
            Comment.shared_watchlist_id == watchlist.id
        ).scalar()

        watchlist_detail = SharedWatchlistWithDetails(
            **watchlist.__dict__,
            creator_name=creator.full_name or creator.username if creator else "Unknown",
            creator_email=creator.email if creator else "unknown@example.com",
            watch_item_name=watchlist.watch_item.name if watchlist.watch_item else "Unknown",
            watch_item_query=watchlist.watch_item.query if watchlist.watch_item else "",
            assigned_users_count=assigned_count,
            comments_count=comments_count
        )
        result.append(watchlist_detail)

    return result


@router.get("/{watchlist_id}", response_model=SharedWatchlistWithDetails)
async def get_shared_watchlist(
    watchlist_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific shared watchlist"""
    watchlist = db.query(SharedWatchlist).options(
        joinedload(SharedWatchlist.watch_item)
    ).filter(SharedWatchlist.id == watchlist_id).first()

    if not watchlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shared watchlist not found"
        )

    # Check permissions
    permissions = check_watchlist_permission(watchlist, current_user, db)
    if not permissions.can_view:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this watchlist"
        )

    # Get additional details
    creator = db.query(User).filter(User.id == watchlist.created_by).first()
    assigned_count = db.query(func.count(watchlist_assignments.c.user_id)).filter(
        watchlist_assignments.c.shared_watchlist_id == watchlist.id
    ).scalar()
    comments_count = db.query(func.count(Comment.id)).filter(
        Comment.shared_watchlist_id == watchlist.id
    ).scalar()

    return SharedWatchlistWithDetails(
        **watchlist.__dict__,
        creator_name=creator.full_name or creator.username if creator else "Unknown",
        creator_email=creator.email if creator else "unknown@example.com",
        watch_item_name=watchlist.watch_item.name if watchlist.watch_item else "Unknown",
        watch_item_query=watchlist.watch_item.query if watchlist.watch_item else "",
        assigned_users_count=assigned_count,
        comments_count=comments_count
    )


@router.put("/{watchlist_id}", response_model=SharedWatchlistResponse)
async def update_shared_watchlist(
    watchlist_id: int,
    watchlist_update: SharedWatchlistUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a shared watchlist"""
    watchlist = db.query(SharedWatchlist).filter(SharedWatchlist.id == watchlist_id).first()

    if not watchlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shared watchlist not found"
        )

    # Check permissions
    permissions = check_watchlist_permission(watchlist, current_user, db)
    if not permissions.can_edit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to edit this watchlist"
        )

    # Update fields
    update_data = watchlist_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(watchlist, field, value)

    watchlist.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(watchlist)

    return watchlist


@router.delete("/{watchlist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shared_watchlist(
    watchlist_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a shared watchlist"""
    watchlist = db.query(SharedWatchlist).filter(SharedWatchlist.id == watchlist_id).first()

    if not watchlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shared watchlist not found"
        )

    # Check permissions
    permissions = check_watchlist_permission(watchlist, current_user, db)
    if not permissions.can_delete:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this watchlist"
        )

    db.delete(watchlist)
    db.commit()


@router.post("/{watchlist_id}/assign", response_model=List[WatchlistAssignmentResponse])
async def assign_users_to_watchlist(
    watchlist_id: int,
    assignment: WatchlistAssignment,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Assign users to a shared watchlist"""
    watchlist = db.query(SharedWatchlist).filter(SharedWatchlist.id == watchlist_id).first()

    if not watchlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shared watchlist not found"
        )

    # Check permissions
    permissions = check_watchlist_permission(watchlist, current_user, db)
    if not permissions.can_assign_users:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to assign users to this watchlist"
        )

    # Verify all users are workspace members
    workspace_members = db.query(WorkspaceMember.user_id).filter(
        and_(
            WorkspaceMember.workspace_id == watchlist.workspace_id,
            WorkspaceMember.user_id.in_(assignment.user_ids)
        )
    ).all()

    valid_user_ids = [member.user_id for member in workspace_members]
    invalid_user_ids = set(assignment.user_ids) - set(valid_user_ids)

    if invalid_user_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Users not in workspace: {list(invalid_user_ids)}"
        )

    # Remove existing assignments for these users
    db.execute(
        watchlist_assignments.delete().where(
            and_(
                watchlist_assignments.c.shared_watchlist_id == watchlist_id,
                watchlist_assignments.c.user_id.in_(assignment.user_ids)
            )
        )
    )

    # Add new assignments
    assignments_data = [
        {"shared_watchlist_id": watchlist_id, "user_id": user_id}
        for user_id in assignment.user_ids
    ]

    db.execute(watchlist_assignments.insert(), assignments_data)
    db.commit()

    # Return assignment responses
    result = []
    for user_id in assignment.user_ids:
        result.append(WatchlistAssignmentResponse(
            shared_watchlist_id=watchlist_id,
            user_id=user_id,
            assigned_at=datetime.utcnow()
        ))

    return result


@router.delete("/{watchlist_id}/assign/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unassign_user_from_watchlist(
    watchlist_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove user assignment from watchlist"""
    watchlist = db.query(SharedWatchlist).filter(SharedWatchlist.id == watchlist_id).first()

    if not watchlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shared watchlist not found"
        )

    # Check permissions (users can unassign themselves)
    permissions = check_watchlist_permission(watchlist, current_user, db)
    if not permissions.can_assign_users and user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to unassign users from this watchlist"
        )

    # Remove assignment
    result = db.execute(
        watchlist_assignments.delete().where(
            and_(
                watchlist_assignments.c.shared_watchlist_id == watchlist_id,
                watchlist_assignments.c.user_id == user_id
            )
        )
    )

    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User assignment not found"
        )

    db.commit()


@router.get("/{watchlist_id}/assignments", response_model=List[WatchlistAssignmentResponse])
async def list_watchlist_assignments(
    watchlist_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List users assigned to a watchlist"""
    watchlist = db.query(SharedWatchlist).filter(SharedWatchlist.id == watchlist_id).first()

    if not watchlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shared watchlist not found"
        )

    # Check permissions
    permissions = check_watchlist_permission(watchlist, current_user, db)
    if not permissions.can_view:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this watchlist"
        )

    # Get assignments
    assignments = db.query(watchlist_assignments).filter(
        watchlist_assignments.c.shared_watchlist_id == watchlist_id
    ).all()

    return [
        WatchlistAssignmentResponse(
            shared_watchlist_id=assignment.shared_watchlist_id,
            user_id=assignment.user_id,
            assigned_at=assignment.assigned_at
        )
        for assignment in assignments
    ]


@router.get("/workspace/{workspace_id}/stats", response_model=SharedWatchlistStats)
async def get_workspace_watchlist_stats(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get watchlist statistics for a workspace"""
    # Check workspace permission
    check_workspace_permission(workspace_id, current_user, db, WorkspaceRole.GUEST)

    # Total watchlists
    total = db.query(func.count(SharedWatchlist.id)).filter(
        SharedWatchlist.workspace_id == workspace_id
    ).scalar()

    # Active watchlists
    active = db.query(func.count(SharedWatchlist.id)).filter(
        and_(
            SharedWatchlist.workspace_id == workspace_id,
            SharedWatchlist.is_active == True
        )
    ).scalar()

    # Public vs private
    public = db.query(func.count(SharedWatchlist.id)).filter(
        and_(
            SharedWatchlist.workspace_id == workspace_id,
            SharedWatchlist.is_public == True
        )
    ).scalar()

    # By creator
    creator_stats = db.query(
        User.username,
        func.count(SharedWatchlist.id)
    ).join(SharedWatchlist, User.id == SharedWatchlist.created_by).filter(
        SharedWatchlist.workspace_id == workspace_id
    ).group_by(User.username).all()

    by_creator = {username: count for username, count in creator_stats}

    # Assignment stats
    assignment_stats = db.query(
        func.count(watchlist_assignments.c.user_id).label('total_assignments'),
        func.count(func.distinct(watchlist_assignments.c.user_id)).label('unique_users')
    ).join(
        SharedWatchlist,
        watchlist_assignments.c.shared_watchlist_id == SharedWatchlist.id
    ).filter(SharedWatchlist.workspace_id == workspace_id).first()

    assignment_data = {
        "total_assignments": assignment_stats.total_assignments or 0,
        "unique_assigned_users": assignment_stats.unique_users or 0
    }

    return SharedWatchlistStats(
        total_watchlists=total,
        active_watchlists=active,
        public_watchlists=public,
        private_watchlists=total - public,
        by_creator=by_creator,
        assignment_stats=assignment_data
    )


@router.post("/bulk-operation", status_code=status.HTTP_200_OK)
async def bulk_watchlist_operation(
    workspace_id: int,
    operation: BulkWatchlistOperation,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Perform bulk operations on watchlists"""
    # Check workspace permission
    check_workspace_permission(workspace_id, current_user, db, WorkspaceRole.ADMIN)

    # Get watchlists
    watchlists = db.query(SharedWatchlist).filter(
        and_(
            SharedWatchlist.id.in_(operation.watchlist_ids),
            SharedWatchlist.workspace_id == workspace_id
        )
    ).all()

    if not watchlists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No watchlists found with provided IDs"
        )

    # Perform operation
    if operation.operation == "activate":
        for watchlist in watchlists:
            watchlist.is_active = True
    elif operation.operation == "deactivate":
        for watchlist in watchlists:
            watchlist.is_active = False
    elif operation.operation == "make_public":
        for watchlist in watchlists:
            watchlist.is_public = True
    elif operation.operation == "make_private":
        for watchlist in watchlists:
            watchlist.is_public = False
    elif operation.operation == "delete":
        for watchlist in watchlists:
            db.delete(watchlist)

    db.commit()

    return {"message": f"Successfully performed {operation.operation} on {len(watchlists)} watchlists"}