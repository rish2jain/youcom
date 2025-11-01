"""Comment API endpoints for threaded discussions"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func, desc, or_
from typing import List, Optional, Dict, Any
from datetime import datetime
import re

from app.database import get_db
from app.models.comment import Comment
from app.models.comment_notification import CommentNotification, ConflictDetection
from app.models.user import User
from app.models.impact_card import ImpactCard
from app.models.shared_watchlist import SharedWatchlist
from app.models.company_research import CompanyResearch
from app.schemas.comment import (
    CommentCreate, CommentUpdate, CommentResponse, CommentWithUser,
    CommentThread, CommentStats, BulkCommentOperation, CommentNotification as CommentNotificationSchema,
    MentionUser, CommentMentions
)

router = APIRouter(prefix="/comments", tags=["comments"])


# Mock authentication dependency - replace with actual auth
async def get_current_user(db: Session = Depends(get_db)) -> User:
    """Mock user for development - replace with actual authentication"""
    user = db.query(User).first()
    if not user:
        # Create a default user for development
        user = User(
            email="dev@example.com",
            username="dev_user",
            full_name="Development User",
            hashed_password="dev_password"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def detect_mentions(content: str, db: Session) -> List[MentionUser]:
    """Extract user mentions from comment content"""
    # Find @username patterns
    mention_pattern = r'@(\w+)'
    mentioned_usernames = re.findall(mention_pattern, content)
    
    if not mentioned_usernames:
        return []
    
    # Get users by username
    users = db.query(User).filter(User.username.in_(mentioned_usernames)).all()
    
    return [
        MentionUser(
            user_id=user.id,
            username=user.username,
            display_name=user.full_name or user.username
        )
        for user in users
    ]


def detect_conflicts(comment: Comment, db: Session) -> List[ConflictDetection]:
    """Detect potential conflicts with existing comments"""
    conflicts = []
    
    # Get other comments in the same context
    query = db.query(Comment).filter(Comment.id != comment.id)
    
    if comment.impact_card_id:
        query = query.filter(Comment.impact_card_id == comment.impact_card_id)
        context_type = "impact_card"
        context_id = comment.impact_card_id
    elif comment.shared_watchlist_id:
        query = query.filter(Comment.shared_watchlist_id == comment.shared_watchlist_id)
        context_type = "shared_watchlist"
        context_id = comment.shared_watchlist_id
    elif comment.company_research_id:
        query = query.filter(Comment.company_research_id == comment.company_research_id)
        context_type = "company_research"
        context_id = comment.company_research_id
    else:
        return conflicts
    
    other_comments = query.all()
    
    # Simple conflict detection based on keywords
    conflict_keywords = {
        'interpretation': ['disagree', 'wrong', 'incorrect', 'not right', 'different view'],
        'priority': ['not important', 'low priority', 'high priority', 'urgent', 'critical'],
        'action': ['should not', 'bad idea', 'better approach', 'alternative']
    }
    
    comment_lower = comment.content.lower()
    
    for other_comment in other_comments:
        other_lower = other_comment.content.lower()
        
        for conflict_type, keywords in conflict_keywords.items():
            # Check if current comment contains conflict indicators
            has_conflict_indicator = any(keyword in comment_lower for keyword in keywords)
            
            if has_conflict_indicator:
                # Simple scoring based on keyword presence
                confidence = min(80, len([k for k in keywords if k in comment_lower]) * 20)
                
                conflict = ConflictDetection(
                    context_type=context_type,
                    context_id=context_id,
                    comment_1_id=other_comment.id,
                    comment_2_id=comment.id,
                    conflict_type=conflict_type,
                    confidence_score=confidence,
                    description=f"Potential {conflict_type} conflict detected"
                )
                conflicts.append(conflict)
    
    return conflicts


async def create_notifications(comment: Comment, mentions: List[MentionUser], db: Session):
    """Create notifications for comment activities"""
    notifications = []
    
    # Determine context
    if comment.impact_card_id:
        context_type = "impact_card"
        context_id = comment.impact_card_id
    elif comment.shared_watchlist_id:
        context_type = "shared_watchlist"
        context_id = comment.shared_watchlist_id
    elif comment.company_research_id:
        context_type = "company_research"
        context_id = comment.company_research_id
    else:
        return
    
    # Notify mentioned users
    for mention in mentions:
        if mention.user_id != comment.user_id:  # Don't notify self
            notification = CommentNotification(
                recipient_id=mention.user_id,
                comment_id=comment.id,
                notification_type="mention",
                context_type=context_type,
                context_id=context_id
            )
            notifications.append(notification)
    
    # Notify parent comment author for replies
    if comment.parent_comment_id:
        parent_comment = db.query(Comment).filter(Comment.id == comment.parent_comment_id).first()
        if parent_comment and parent_comment.user_id != comment.user_id:
            notification = CommentNotification(
                recipient_id=parent_comment.user_id,
                comment_id=comment.id,
                notification_type="reply",
                context_type=context_type,
                context_id=context_id
            )
            notifications.append(notification)
    
    # Add notifications to database
    for notification in notifications:
        db.add(notification)


@router.post("/", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    impact_card_id: Optional[int] = None,
    shared_watchlist_id: Optional[int] = None,
    company_research_id: Optional[int] = None,
    comment_data: CommentCreate = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new comment"""
    if not any([impact_card_id, shared_watchlist_id, company_research_id]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must specify one of: impact_card_id, shared_watchlist_id, or company_research_id"
        )
    
    # Verify the target entity exists
    if impact_card_id:
        entity = db.query(ImpactCard).filter(ImpactCard.id == impact_card_id).first()
        if not entity:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Impact card not found")
    elif shared_watchlist_id:
        entity = db.query(SharedWatchlist).filter(SharedWatchlist.id == shared_watchlist_id).first()
        if not entity:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shared watchlist not found")
    elif company_research_id:
        entity = db.query(CompanyResearch).filter(CompanyResearch.id == company_research_id).first()
        if not entity:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company research not found")
    
    # Verify parent comment exists if specified
    if comment_data.parent_comment_id:
        parent = db.query(Comment).filter(Comment.id == comment_data.parent_comment_id).first()
        if not parent:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent comment not found")
    
    # Detect mentions
    mentions = detect_mentions(comment_data.content, db)
    
    # Create comment
    comment = Comment(
        user_id=current_user.id,
        impact_card_id=impact_card_id,
        shared_watchlist_id=shared_watchlist_id,
        company_research_id=company_research_id,
        content=comment_data.content,
        annotations=comment_data.annotations,
        parent_comment_id=comment_data.parent_comment_id
    )
    
    db.add(comment)
    db.commit()
    db.refresh(comment)
    
    # Create notifications
    await create_notifications(comment, mentions, db)
    
    # Detect conflicts
    conflicts = detect_conflicts(comment, db)
    for conflict in conflicts:
        db.add(conflict)
    
    db.commit()
    
    return comment


@router.get("/", response_model=List[CommentWithUser])
async def list_comments(
    impact_card_id: Optional[int] = None,
    shared_watchlist_id: Optional[int] = None,
    company_research_id: Optional[int] = None,
    include_replies: bool = Query(True, description="Include reply comments"),
    limit: int = Query(50, le=100, description="Maximum number of comments"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    """List comments for a specific entity"""
    if not any([impact_card_id, shared_watchlist_id, company_research_id]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must specify one of: impact_card_id, shared_watchlist_id, or company_research_id"
        )
    
    query = db.query(Comment).options(joinedload(Comment.user))
    
    # Filter by entity
    if impact_card_id:
        query = query.filter(Comment.impact_card_id == impact_card_id)
    elif shared_watchlist_id:
        query = query.filter(Comment.shared_watchlist_id == shared_watchlist_id)
    elif company_research_id:
        query = query.filter(Comment.company_research_id == company_research_id)
    
    # Filter by reply status
    if not include_replies:
        query = query.filter(Comment.parent_comment_id.is_(None))
    
    comments = query.order_by(desc(Comment.created_at)).offset(offset).limit(limit).all()
    
    # Build response with user info and reply counts
    result = []
    for comment in comments:
        replies_count = db.query(func.count(Comment.id)).filter(
            Comment.parent_comment_id == comment.id
        ).scalar()
        
        comment_with_user = CommentWithUser(
            **comment.__dict__,
            user_name=comment.user.full_name or comment.user.username,
            user_email=comment.user.email,
            replies_count=replies_count
        )
        result.append(comment_with_user)
    
    return result


@router.get("/threads", response_model=List[CommentThread])
async def get_comment_threads(
    impact_card_id: Optional[int] = None,
    shared_watchlist_id: Optional[int] = None,
    company_research_id: Optional[int] = None,
    limit: int = Query(20, le=50, description="Maximum number of threads"),
    db: Session = Depends(get_db)
):
    """Get threaded comments with nested replies"""
    if not any([impact_card_id, shared_watchlist_id, company_research_id]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must specify one of: impact_card_id, shared_watchlist_id, or company_research_id"
        )
    
    # Get top-level comments
    query = db.query(Comment).options(joinedload(Comment.user)).filter(
        Comment.parent_comment_id.is_(None)
    )
    
    if impact_card_id:
        query = query.filter(Comment.impact_card_id == impact_card_id)
    elif shared_watchlist_id:
        query = query.filter(Comment.shared_watchlist_id == shared_watchlist_id)
    elif company_research_id:
        query = query.filter(Comment.company_research_id == company_research_id)
    
    top_level_comments = query.order_by(desc(Comment.created_at)).limit(limit).all()
    
    # Build threaded structure
    def build_thread(comment: Comment) -> CommentThread:
        # Get replies
        replies = db.query(Comment).options(joinedload(Comment.user)).filter(
            Comment.parent_comment_id == comment.id
        ).order_by(Comment.created_at).all()
        
        # Recursively build reply threads
        reply_threads = [build_thread(reply) for reply in replies]
        
        return CommentThread(
            **comment.__dict__,
            user_name=comment.user.full_name or comment.user.username,
            user_email=comment.user.email,
            replies_count=len(replies),
            replies=reply_threads
        )
    
    threads = [build_thread(comment) for comment in top_level_comments]
    return threads


@router.get("/{comment_id}", response_model=CommentWithUser)
async def get_comment(
    comment_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific comment"""
    comment = db.query(Comment).options(joinedload(Comment.user)).filter(
        Comment.id == comment_id
    ).first()
    
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    replies_count = db.query(func.count(Comment.id)).filter(
        Comment.parent_comment_id == comment.id
    ).scalar()
    
    return CommentWithUser(
        **comment.__dict__,
        user_name=comment.user.full_name or comment.user.username,
        user_email=comment.user.email,
        replies_count=replies_count
    )


@router.put("/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: int,
    comment_update: CommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a comment"""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    # Only allow the author or admin to update
    if comment.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this comment"
        )
    
    # Update fields
    update_data = comment_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(comment, field, value)
    
    comment.updated_at = datetime.utcnow()
    comment.is_edited += 1
    
    db.commit()
    db.refresh(comment)
    
    return comment


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a comment"""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    # Only allow the author or admin to delete
    if comment.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this comment"
        )
    
    db.delete(comment)
    db.commit()


@router.get("/stats/summary", response_model=CommentStats)
async def get_comment_stats(
    impact_card_id: Optional[int] = None,
    shared_watchlist_id: Optional[int] = None,
    company_research_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get comment statistics"""
    if not any([impact_card_id, shared_watchlist_id, company_research_id]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must specify one of: impact_card_id, shared_watchlist_id, or company_research_id"
        )
    
    query = db.query(Comment)
    
    if impact_card_id:
        query = query.filter(Comment.impact_card_id == impact_card_id)
    elif shared_watchlist_id:
        query = query.filter(Comment.shared_watchlist_id == shared_watchlist_id)
    elif company_research_id:
        query = query.filter(Comment.company_research_id == company_research_id)
    
    # Total comments
    total = query.count()
    
    # Thread vs reply counts
    threads = query.filter(Comment.parent_comment_id.is_(None)).count()
    replies = total - threads
    
    # By user - build query explicitly with proper filtering
    user_stats_query = db.query(User.username, func.count(Comment.id)).join(Comment)
    
    if impact_card_id:
        user_stats_query = user_stats_query.filter(Comment.impact_card_id == impact_card_id)
    elif shared_watchlist_id:
        user_stats_query = user_stats_query.filter(Comment.shared_watchlist_id == shared_watchlist_id)
    elif company_research_id:
        user_stats_query = user_stats_query.filter(Comment.company_research_id == company_research_id)
    
    user_stats = user_stats_query.group_by(User.username).all()
    
    by_user = {username: count for username, count in user_stats}
    
    # Recent activity
    recent_comments = query.options(joinedload(Comment.user)).order_by(
        desc(Comment.created_at)
    ).limit(5).all()
    
    recent_activity = [
        {
            "comment_id": comment.id,
            "user_name": comment.user.full_name or comment.user.username,
            "content_preview": comment.content[:100] + "..." if len(comment.content) > 100 else comment.content,
            "created_at": comment.created_at.isoformat(),
            "is_reply": comment.parent_comment_id is not None
        }
        for comment in recent_comments
    ]
    
    return CommentStats(
        total_comments=total,
        total_threads=threads,
        total_replies=replies,
        by_user=by_user,
        recent_activity=recent_activity
    )


@router.get("/notifications/", response_model=List[CommentNotificationSchema])
async def get_user_notifications(
    unread_only: bool = Query(False, description="Only show unread notifications"),
    limit: int = Query(20, le=50, description="Maximum number of notifications"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comment notifications for current user"""
    query = db.query(CommentNotification).options(
        joinedload(CommentNotification.comment).joinedload(Comment.user)
    ).filter(CommentNotification.recipient_id == current_user.id)
    
    if unread_only:
        query = query.filter(CommentNotification.is_read == False)
    
    notifications = query.order_by(desc(CommentNotification.created_at)).limit(limit).all()
    
    result = []
    for notification in notifications:
        result.append(CommentNotificationSchema(
            id=notification.id,
            recipient_id=notification.recipient_id,
            comment_id=notification.comment_id,
            notification_type=notification.notification_type,
            is_read=notification.is_read,
            created_at=notification.created_at,
            comment_content=notification.comment.content[:100] + "..." if len(notification.comment.content) > 100 else notification.comment.content,
            author_name=notification.comment.user.full_name or notification.comment.user.username,
            context_type=notification.context_type,
            context_id=notification.context_id
        ))
    
    return result


@router.put("/notifications/{notification_id}/read", status_code=status.HTTP_200_OK)
async def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a notification as read"""
    notification = db.query(CommentNotification).filter(
        and_(
            CommentNotification.id == notification_id,
            CommentNotification.recipient_id == current_user.id
        )
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    notification.is_read = True
    notification.read_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Notification marked as read"}


@router.get("/conflicts/", response_model=List[Dict[str, Any]])
async def get_conflicts(
    impact_card_id: Optional[int] = None,
    shared_watchlist_id: Optional[int] = None,
    company_research_id: Optional[int] = None,
    unresolved_only: bool = Query(True, description="Only show unresolved conflicts"),
    db: Session = Depends(get_db)
):
    """Get detected conflicts in comments"""
    if not any([impact_card_id, shared_watchlist_id, company_research_id]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must specify one of: impact_card_id, shared_watchlist_id, or company_research_id"
        )
    
    query = db.query(ConflictDetection).options(
        joinedload(ConflictDetection.comment_1).joinedload(Comment.user),
        joinedload(ConflictDetection.comment_2).joinedload(Comment.user)
    )
    
    if impact_card_id:
        query = query.filter(
            and_(
                ConflictDetection.context_type == "impact_card",
                ConflictDetection.context_id == impact_card_id
            )
        )
    elif shared_watchlist_id:
        query = query.filter(
            and_(
                ConflictDetection.context_type == "shared_watchlist",
                ConflictDetection.context_id == shared_watchlist_id
            )
        )
    elif company_research_id:
        query = query.filter(
            and_(
                ConflictDetection.context_type == "company_research",
                ConflictDetection.context_id == company_research_id
            )
        )
    
    if unresolved_only:
        query = query.filter(ConflictDetection.is_resolved == False)
    
    conflicts = query.order_by(desc(ConflictDetection.confidence_score)).all()
    
    result = []
    for conflict in conflicts:
        result.append({
            "id": conflict.id,
            "conflict_type": conflict.conflict_type,
            "confidence_score": conflict.confidence_score,
            "description": conflict.description,
            "is_resolved": conflict.is_resolved,
            "detected_at": conflict.detected_at.isoformat(),
            "comment_1": {
                "id": conflict.comment_1.id,
                "content": conflict.comment_1.content,
                "author": conflict.comment_1.user.full_name or conflict.comment_1.user.username
            },
            "comment_2": {
                "id": conflict.comment_2.id,
                "content": conflict.comment_2.content,
                "author": conflict.comment_2.user.full_name or conflict.comment_2.user.username
            }
        })
    
    return result


@router.post("/bulk-operation", status_code=status.HTTP_200_OK)
async def bulk_comment_operation(
    operation: BulkCommentOperation,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Perform bulk operations on comments"""
    comments = db.query(Comment).filter(Comment.id.in_(operation.comment_ids)).all()
    
    if not comments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No comments found with provided IDs"
        )
    
    # Check permissions - only allow operations on own comments or if admin
    for comment in comments:
        if comment.user_id != current_user.id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not authorized to modify comment {comment.id}"
            )
    
    # Perform operation
    if operation.operation == "delete":
        for comment in comments:
            db.delete(comment)
        db.commit()
        return {"message": f"Successfully deleted {len(comments)} comments"}
    elif operation.operation == "hide":
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Hide operation is not implemented yet"
        )
    elif operation.operation == "unhide":
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Unhide operation is not implemented yet"
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown operation: {operation.operation}"
        )