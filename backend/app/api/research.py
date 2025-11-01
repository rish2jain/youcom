from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from pydantic import BaseModel, EmailStr
import logging
from app.database import get_db
from app.models.company_research import CompanyResearch
from app.schemas.company_research import (
    CompanyResearchCreate,
    CompanyResearch as CompanyResearchSchema,
    CompanyResearchRequest
)
from app.services.you_client import get_you_client, YouComAPIError, YouComOrchestrator
from app.services.pdf_service import pdf_generator
from app.services.email_service import get_email_service
from app.config import settings

router = APIRouter(prefix="/research", tags=["company-research"])
logger = logging.getLogger(__name__)

# Import shared limiter
from app.rate_limiter import limiter

@router.post("/company", response_model=CompanyResearchSchema, status_code=status.HTTP_201_CREATED)
@limiter.limit("15/minute")  # Limit to 15 company research requests per minute per IP
async def research_company(
    request_obj: Request,  # Required for rate limiter
    request: CompanyResearchRequest,
    db: AsyncSession = Depends(get_db),
    you_client: YouComOrchestrator = Depends(get_you_client)
):
    """Research a company using You.com APIs (Individual User Feature)

    Rate limit: 15 requests per minute per IP address
    """
    try:
        # Perform quick company research
        logger.info(f"🏢 Starting company research for {request.company_name}")
        research_data = await you_client.quick_company_research(request.company_name)

        # Generate summary from report (first 150 chars)
        report = research_data.get("research_report", {})
        report_text = ""
        if isinstance(report, dict):
            report_text = report.get("report", "")
        if isinstance(report_text, str) and len(report_text) > 150:
            summary = report_text[:147] + "..."
        else:
            summary = "Comprehensive competitive analysis and market research report"

        # Create database record
        db_research = CompanyResearch(
            company_name=request.company_name,
            search_results=research_data["search_results"],
            research_report=research_data["research_report"],
            status="completed",
            summary=summary,
            confidence_score=85,
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
    try:
        query = select(CompanyResearch)
        
        if company:
            query = query.where(CompanyResearch.company_name.ilike(f"%{company}%"))
        
        query = query.offset(skip).limit(limit).order_by(CompanyResearch.created_at.desc())
        
        result = await db.execute(query)
        items = result.scalars().all()
        
        # Convert SQLAlchemy models to Pydantic models
        return [CompanyResearchSchema.model_validate(item) for item in items]
    except Exception as e:
        logger.error(f"❌ Error fetching company research: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch company research: {str(e)}"
        )

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


# Pydantic model for email sharing
class ShareResearchRequest(BaseModel):
    """Request model for sharing research via email"""
    emails: List[EmailStr]
    subject: str = None
    message: str = None


@router.get("/{research_id}/export", response_class=StreamingResponse)
async def export_research_pdf(
    research_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Export company research as PDF

    Returns a downloadable PDF file with the research report
    """
    try:
        # Get research record
        result = await db.execute(select(CompanyResearch).where(CompanyResearch.id == research_id))
        research = result.scalar_one_or_none()

        if not research:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company research not found"
            )

        # Convert SQLAlchemy model to dict for PDF generation
        research_data = {
            'company_name': research.company_name,
            'search_results': research.search_results,
            'research_report': research.research_report,
            'total_sources': research.total_sources,
            'api_usage': research.api_usage,
            'created_at': research.created_at
        }

        # Generate PDF
        pdf_buffer = pdf_generator.generate_research_report(research_data)

        # Return as streaming response
        filename = f"{research.company_name.replace(' ', '_')}_research_report.pdf"

        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to export research as PDF: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate PDF report"
        )


@router.post("/{research_id}/share", status_code=status.HTTP_200_OK)
async def share_research_email(
    research_id: int,
    share_request: ShareResearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Share company research via email

    Sends the research report as a PDF attachment to the specified email addresses
    """
    try:
        # Get research record
        result = await db.execute(select(CompanyResearch).where(CompanyResearch.id == research_id))
        research = result.scalar_one_or_none()

        if not research:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company research not found"
            )

        # Convert SQLAlchemy model to dict for PDF generation
        research_data = {
            'company_name': research.company_name,
            'search_results': research.search_results,
            'research_report': research.research_report,
            'total_sources': research.total_sources,
            'api_usage': research.api_usage,
            'created_at': research.created_at
        }

        # Generate PDF
        pdf_buffer = pdf_generator.generate_research_report(research_data)

        # Get email service
        email_service = get_email_service(settings)
        if not email_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Email service not configured. Please set SMTP settings."
            )

        # Send email
        success = await email_service.send_research_report(
            to_emails=share_request.emails,
            company_name=research.company_name,
            pdf_buffer=pdf_buffer,
            subject=share_request.subject,
            message=share_request.message
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send email"
            )

        return {
            "message": "Research report shared successfully",
            "recipients": share_request.emails,
            "company_name": research.company_name
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to share research via email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to share research report"
        )
