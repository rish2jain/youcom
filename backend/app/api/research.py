from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import logging
from app.database import get_db
from app.models.company_research import CompanyResearch
from app.schemas.company_research import (
    CompanyResearchCreate,
    CompanyResearch as CompanyResearchSchema,
    CompanyResearchRequest
)
from app.services.you_client import get_you_client, YouComAPIError, YouComOrchestrator

router = APIRouter(prefix="/research", tags=["company-research"])
logger = logging.getLogger(__name__)

@router.post("/company", response_model=CompanyResearchSchema, status_code=status.HTTP_201_CREATED)
async def research_company(
    request: CompanyResearchRequest,
    db: AsyncSession = Depends(get_db),
    you_client: YouComOrchestrator = Depends(get_you_client)
):
    """Research a company using You.com APIs (Individual User Feature)"""
    try:
        # Perform quick company research
        logger.info(f"🏢 Starting company research for {request.company_name}")
        research_data = await you_client.quick_company_research(request.company_name)
        
        # Create database record
        db_research = CompanyResearch(
            company_name=request.company_name,
            search_results=research_data["search_results"],
            research_report=research_data["research_report"],
            total_sources=research_data["total_sources"],
            api_usage=research_data["api_usage"]
        )
        
        db.add(db_research)
        await db.commit()
        await db.refresh(db_research)
        
        logger.info(f"✅ Company research completed for {request.company_name}")
        return db_research
        
    except YouComAPIError as e:
        logger.error(f"❌ You.com API error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"You.com API error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"❌ Unexpected error researching company: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to research company"
        )

@router.get("/", response_model=List[CompanyResearchSchema])
async def get_company_research(
    skip: int = 0,
    limit: int = 100,
    company: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Get all company research records"""
    query = select(CompanyResearch)
    
    if company:
        query = query.where(CompanyResearch.company_name.ilike(f"%{company}%"))
    
    query = query.offset(skip).limit(limit).order_by(CompanyResearch.created_at.desc())
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    return items

@router.get("/{research_id}", response_model=CompanyResearchSchema)
async def get_company_research_by_id(
    research_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific company research record"""
    result = await db.execute(select(CompanyResearch).where(CompanyResearch.id == research_id))
    research = result.scalar_one_or_none()
    
    if not research:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company research not found"
        )
    
    return research

@router.get("/company/{company_name}", response_model=List[CompanyResearchSchema])
async def get_research_by_company_name(
    company_name: str,
    db: AsyncSession = Depends(get_db)
):
    """Get all research records for a specific company"""
    result = await db.execute(
        select(CompanyResearch)
        .where(CompanyResearch.company_name.ilike(f"%{company_name}%"))
        .order_by(CompanyResearch.created_at.desc())
    )
    items = result.scalars().all()
    
    return items
