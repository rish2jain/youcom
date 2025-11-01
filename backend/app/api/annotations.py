"""Annotation API endpoints for collaborative features"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models.annotation import Annotation
from app.models.user import User
from app.models.impact_card import ImpactCard
from app.schemas.annotation import (
    AnnotationCreate, AnnotationUpdate, AnnotationResponse, 
    AnnotationWithUser, AnnotationStats, BulkAnnotationOperation
)

router = APIRouter(prefix="/annotations", tags=["annotations"])


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


@router.post("/", response_model=AnnotationResponse, status_code=status.HTTP_201_CREATED)
async def create_annotation(
    impact_card_id: int,
    annotation: AnnotationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new annotation on an Impact Card"""
    # Verify impact card exists
    impact_card = db.query(ImpactCard).filter(ImpactCard.id == impact_card_id).first()
    if not impact_card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Impact card not found"
        )

    # Create annotation
    db_annotation = Annotation(
        user_id=current_user.id,
        impact_card_id=impact_card_id,
        content=annotation.content,
        annotation_type=annotation.annotation_type,
        position=annotation.position.dict() if annotation.position else None,
        target_element=annotation.target_element,
        target_text=annotation.target_text
    )
    
    db.add(db_annotation)
    db.commit()
    db.refresh(db_annotation)
    
    return db_annotation


@router.get("/impact-card/{impact_card_id}", response_model=List[AnnotationWithUser])
async def get_annotations_for_impact_card(
    impact_card_id: int,
    annotation_type: Optional[str] = None,
    include_resolved: bool = True,
    db: Session = Depends(get_db)
):
    """Get all annotations for a specific Impact Card"""
    query = db.query(Annotation).options(
        joinedload(Annotation.user),
        joinedload(Annotation.resolver)
    ).filter(Annotation.impact_card_id == impact_card_id)
    
    if annotation_type:
        query = query.filter(Annotation.annotation_type == annotation_type)
    
    if not include_resolved:
        query = query.filter(Annotation.is_resolved == 0)
    
    annotations = query.order_by(Annotation.created_at.desc()).all()
    
    # Transform to include user information
    result = []
    for annotation in annotations:
        annotation_dict = {
            **annotation.__dict__,
            "user_name": annotation.user.full_name or annotation.user.username,
            "user_email": annotation.user.email,
            "resolver_name": annotation.resolver.full_name if annotation.resolver else None
        }
        result.append(annotation_dict)
    
    return result


@router.get("/{annotation_id}", response_model=AnnotationWithUser)
async def get_annotation(
    annotation_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific annotation by ID"""
    annotation = db.query(Annotation).options(
        joinedload(Annotation.user),
        joinedload(Annotation.resolver)
    ).filter(Annotation.id == annotation_id).first()
    
    if not annotation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Annotation not found"
        )
    
    return {
        **annotation.__dict__,
        "user_name": annotation.user.full_name or annotation.user.username,
        "user_email": annotation.user.email,
        "resolver_name": annotation.resolver.full_name if annotation.resolver else None
    }


@router.put("/{annotation_id}", response_model=AnnotationResponse)
async def update_annotation(
    annotation_id: int,
    annotation_update: AnnotationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an annotation"""
    annotation = db.query(Annotation).filter(Annotation.id == annotation_id).first()
    
    if not annotation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Annotation not found"
        )
    
    # Only allow the creator or admin to update
    if annotation.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this annotation"
        )
    
    # Update fields
    update_data = annotation_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == "position" and value:
            setattr(annotation, field, value.dict() if hasattr(value, 'dict') else value)
        elif field == "is_resolved" and value == 1:
            setattr(annotation, field, value)
            annotation.resolved_by = current_user.id
            annotation.resolved_at = datetime.utcnow()
        elif field == "is_resolved" and value == 0:
            setattr(annotation, field, value)
            annotation.resolved_by = None
            annotation.resolved_at = None
        else:
            setattr(annotation, field, value)
    
    annotation.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(annotation)
    
    return annotation


@router.delete("/{annotation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_annotation(
    annotation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an annotation"""
    annotation = db.query(Annotation).filter(Annotation.id == annotation_id).first()
    
    if not annotation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Annotation not found"
        )
    
    # Only allow the creator or admin to delete
    if annotation.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this annotation"
        )
    
    db.delete(annotation)
    db.commit()


@router.get("/impact-card/{impact_card_id}/stats", response_model=AnnotationStats)
async def get_annotation_stats(
    impact_card_id: int,
    db: Session = Depends(get_db)
):
    """Get annotation statistics for an Impact Card"""
    # Total count
    total = db.query(func.count(Annotation.id)).filter(
        Annotation.impact_card_id == impact_card_id
    ).scalar()
    
    # Count by type
    type_counts = db.query(
        Annotation.annotation_type,
        func.count(Annotation.id)
    ).filter(
        Annotation.impact_card_id == impact_card_id
    ).group_by(Annotation.annotation_type).all()
    
    by_type = {type_name: count for type_name, count in type_counts}
    
    # Resolved vs pending
    resolved = db.query(func.count(Annotation.id)).filter(
        and_(
            Annotation.impact_card_id == impact_card_id,
            Annotation.is_resolved == 1
        )
    ).scalar()
    
    # Count by user
    user_counts = db.query(
        User.username,
        func.count(Annotation.id)
    ).join(Annotation).filter(
        Annotation.impact_card_id == impact_card_id
    ).group_by(User.username).all()
    
    by_user = {username: count for username, count in user_counts}
    
    return AnnotationStats(
        total_annotations=total,
        by_type=by_type,
        resolved_count=resolved,
        pending_count=total - resolved,
        by_user=by_user
    )


@router.post("/bulk-operation", status_code=status.HTTP_200_OK)
async def bulk_annotation_operation(
    operation: BulkAnnotationOperation,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Perform bulk operations on annotations"""
    annotations = db.query(Annotation).filter(
        Annotation.id.in_(operation.annotation_ids)
    ).all()
    
    if not annotations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No annotations found with provided IDs"
        )
    
    # Check permissions - only allow operations on own annotations or if admin
    for annotation in annotations:
        if annotation.user_id != current_user.id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not authorized to modify annotation {annotation.id}"
            )
    
    # Perform operation
    if operation.operation == "resolve":
        for annotation in annotations:
            annotation.is_resolved = 1
            annotation.resolved_by = operation.resolved_by or current_user.id
            annotation.resolved_at = datetime.utcnow()
    elif operation.operation == "unresolve":
        for annotation in annotations:
            annotation.is_resolved = 0
            annotation.resolved_by = None
            annotation.resolved_at = None
    elif operation.operation == "delete":
        for annotation in annotations:
            db.delete(annotation)
    
    db.commit()
    
    return {"message": f"Successfully performed {operation.operation} on {len(annotations)} annotations"}