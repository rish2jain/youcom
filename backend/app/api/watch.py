from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from typing import List
from app.database import get_db
from app.models.watch import WatchItem
from app.schemas.watch import WatchItemCreate, WatchItemUpdate, WatchItem as WatchItemSchema, WatchItemList

router = APIRouter(prefix="/watch", tags=["watchlist"])

@router.post("/", response_model=WatchItemSchema, status_code=status.HTTP_201_CREATED)
async def create_watch_item(
    watch_item: WatchItemCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new watchlist item"""
    db_watch_item = WatchItem(**watch_item.model_dump())
    db.add(db_watch_item)
    await db.commit()
    await db.refresh(db_watch_item)
    return db_watch_item

@router.get("/", response_model=WatchItemList)
async def get_watch_items(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """Get all watchlist items"""
    query = select(WatchItem)
    
    if active_only:
        query = query.where(WatchItem.is_active == True)
    
    query = query.offset(skip).limit(limit).order_by(WatchItem.created_at.desc())
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    # Get total count
    count_query = select(WatchItem)
    if active_only:
        count_query = count_query.where(WatchItem.is_active == True)
    
    count_result = await db.execute(count_query)
    total = len(count_result.scalars().all())
    
    return WatchItemList(items=items, total=total)

@router.get("/{watch_id}", response_model=WatchItemSchema)
async def get_watch_item(
    watch_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific watchlist item"""
    result = await db.execute(select(WatchItem).where(WatchItem.id == watch_id))
    watch_item = result.scalar_one_or_none()
    
    if not watch_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watch item not found"
        )
    
    return watch_item

@router.put("/{watch_id}", response_model=WatchItemSchema)
async def update_watch_item(
    watch_id: int,
    watch_update: WatchItemUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a watchlist item"""
    # Check if item exists
    result = await db.execute(select(WatchItem).where(WatchItem.id == watch_id))
    watch_item = result.scalar_one_or_none()
    
    if not watch_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watch item not found"
        )
    
    # Update fields
    update_data = watch_update.model_dump(exclude_unset=True)
    if update_data:
        await db.execute(
            update(WatchItem)
            .where(WatchItem.id == watch_id)
            .values(**update_data)
        )
        await db.commit()
        await db.refresh(watch_item)
    
    return watch_item

@router.delete("/{watch_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_watch_item(
    watch_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a watchlist item"""
    result = await db.execute(select(WatchItem).where(WatchItem.id == watch_id))
    watch_item = result.scalar_one_or_none()
    
    if not watch_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watch item not found"
        )
    
    await db.execute(delete(WatchItem).where(WatchItem.id == watch_id))
    await db.commit()

@router.post("/{watch_id}/activate", response_model=WatchItemSchema)
async def activate_watch_item(
    watch_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Activate a watchlist item"""
    result = await db.execute(select(WatchItem).where(WatchItem.id == watch_id))
    watch_item = result.scalar_one_or_none()
    
    if not watch_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watch item not found"
        )
    
    await db.execute(
        update(WatchItem)
        .where(WatchItem.id == watch_id)
        .values(is_active=True)
    )
    await db.commit()
    await db.refresh(watch_item)
    
    return watch_item

@router.post("/{watch_id}/deactivate", response_model=WatchItemSchema)
async def deactivate_watch_item(
    watch_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Deactivate a watchlist item"""
    result = await db.execute(select(WatchItem).where(WatchItem.id == watch_id))
    watch_item = result.scalar_one_or_none()
    
    if not watch_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watch item not found"
        )
    
    await db.execute(
        update(WatchItem)
        .where(WatchItem.id == watch_id)
        .values(is_active=False)
    )
    await db.commit()
    await db.refresh(watch_item)
    
    return watch_item