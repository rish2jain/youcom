"""
Industry Template Management API

This module provides FastAPI endpoints for template discovery, selection, application,
customization, and usage analytics for the Industry Template System.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any

from app.database import get_db
from app.services.auth_service import get_current_user
from app.services.industry_template_service import IndustryTemplateService, TemplateStatus
from app.services.template_engine import TemplateEngine, TemplateApplicationResult
from app.services.industry_data_provider import IndustryDataProvider
from app.schemas.industry_template import (
    IndustryTemplateCreate, IndustryTemplateUpdate, IndustryTemplateResponse,
    IndustryTemplateMetadata, TemplateApplicationCreate, TemplateApplicationUpdate,
    TemplateApplicationResponse, TemplateRating, TemplateSearchRequest,
    TemplateFilter, TemplateStatistics, IndustryList, TemplateConfigValidation,
    BulkTemplateOperation, TemplateExport, TemplateStatus as TemplateStatusSchema
)

router = APIRouter(prefix="/api/industry-templates", tags=["Industry Templates"])


@router.post("/", response_model=IndustryTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    template: IndustryTemplateCreate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new industry template."""
    try:
        template_service = IndustryTemplateService(db)
        
        # Check if template with same name and industry already exists
        existing_template = await template_service.get_template_by_name(
            template.name, template.industry_sector
        )
        if existing_template:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Template '{template.name}' already exists for industry '{template.industry_sector}'"
            )
        
        # Create the template
        template_id = await template_service.create_template(
            name=template.name,
            industry_sector=template.industry_sector,
            template_config=template.template_config,
            description=template.description,
            default_competitors=template.default_competitors,
            default_keywords=template.default_keywords,
            risk_categories=template.risk_categories,
            kpi_metrics=template.kpi_metrics,
            created_by=current_user.id
        )
        
        # Return the created template
        created_template = await template_service.get_template(template_id)
        return IndustryTemplateResponse.from_orm(created_template)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create template: {str(e)}"
        )


@router.get("/", response_model=List[IndustryTemplateMetadata])
async def list_templates(
    industry_sector: Optional[str] = Query(None, description="Filter by industry sector"),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of templates to return"),
    offset: int = Query(0, ge=0, description="Number of templates to skip"),
    db: AsyncSession = Depends(get_db)
):
    """List available industry templates with optional filtering."""
    try:
        template_service = IndustryTemplateService(db)
        templates = await template_service.list_templates(
            industry_sector=industry_sector,
            is_active=is_active,
            limit=limit,
            offset=offset
        )
        return templates
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list templates: {str(e)}"
        )


@router.get("/industries", response_model=IndustryList)
async def get_available_industries(db: AsyncSession = Depends(get_db)):
    """Get list of available industry sectors."""
    try:
        template_service = IndustryTemplateService(db)
        industries = await template_service.get_industries()
        return IndustryList(industries=industries)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get industries: {str(e)}"
        )


@router.get("/popular", response_model=List[IndustryTemplateMetadata])
async def get_popular_templates(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of templates to return"),
    db: AsyncSession = Depends(get_db)
):
    """Get most popular templates by usage and rating."""
    try:
        template_service = IndustryTemplateService(db)
        templates = await template_service.get_popular_templates(limit=limit)
        return templates
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get popular templates: {str(e)}"
        )


@router.post("/search", response_model=List[IndustryTemplateMetadata])
async def search_templates(
    search_request: TemplateSearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """Search templates by name or description."""
    try:
        template_service = IndustryTemplateService(db)
        templates = await template_service.search_templates(
            query=search_request.query,
            industry_sector=search_request.industry_sector,
            limit=search_request.limit
        )
        return templates
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search templates: {str(e)}"
        )


@router.get("/{template_id}", response_model=IndustryTemplateResponse)
async def get_template(
    template_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific template by ID."""
    try:
        template_service = IndustryTemplateService(db)
        template = await template_service.get_template(template_id)
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template with ID {template_id} not found"
            )
        
        return IndustryTemplateResponse.from_orm(template)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get template: {str(e)}"
        )


@router.put("/{template_id}", response_model=IndustryTemplateResponse)
async def update_template(
    template_id: int,
    template_update: IndustryTemplateUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing template."""
    try:
        template_service = IndustryTemplateService(db)
        
        success = await template_service.update_template(
            template_id=template_id,
            name=template_update.name,
            description=template_update.description,
            template_config=template_update.template_config,
            default_competitors=template_update.default_competitors,
            default_keywords=template_update.default_keywords,
            risk_categories=template_update.risk_categories,
            kpi_metrics=template_update.kpi_metrics,
            is_active=template_update.is_active
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template with ID {template_id} not found"
            )
        
        # Return updated template
        updated_template = await template_service.get_template(template_id)
        return IndustryTemplateResponse.from_orm(updated_template)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update template: {str(e)}"
        )


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a template (soft delete)."""
    try:
        template_service = IndustryTemplateService(db)
        success = await template_service.delete_template(template_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template with ID {template_id} not found"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete template: {str(e)}"
        )


@router.get("/{template_id}/preview")
async def get_template_preview(
    template_id: int,
    customizations: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get a preview of what will be applied when using a template."""
    try:
        template_engine = TemplateEngine(db)
        preview = await template_engine.get_template_preview(
            template_id=template_id,
            customizations=customizations
        )
        return preview
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate template preview: {str(e)}"
        )


@router.post("/{template_id}/validate-compatibility")
async def validate_template_compatibility(
    template_id: int,
    workspace_id: str = Query(..., description="Workspace ID to validate against"),
    db: AsyncSession = Depends(get_db)
):
    """Validate if a template is compatible with a workspace."""
    try:
        template_engine = TemplateEngine(db)
        compatibility = await template_engine.validate_template_compatibility(
            template_id=template_id,
            workspace_id=workspace_id
        )
        return compatibility
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate template compatibility: {str(e)}"
        )


@router.post("/{template_id}/apply", status_code=status.HTTP_201_CREATED)
async def apply_template(
    template_id: int,
    application: TemplateApplicationCreate,
    current_user = Depends(get_current_user),
    auto_populate_competitors: bool = Query(True, description="Automatically populate competitors"),
    db: AsyncSession = Depends(get_db)
):
    """Apply a template to a workspace."""
    try:
        template_engine = TemplateEngine(db)
        
        # Apply the template
        summary = await template_engine.apply_template(
            template_id=template_id,
            workspace_id=application.workspace_id,
            user_id=current_user.id,
            customizations=application.customizations,
            auto_populate_competitors=auto_populate_competitors
        )
        
        return {
            "result": summary.result.value,
            "summary": {
                "watchlist_items_created": summary.watchlist_items_created,
                "competitors_added": summary.competitors_added,
                "keywords_configured": summary.keywords_configured,
                "notifications_configured": summary.notifications_configured
            },
            "errors": summary.errors,
            "warnings": summary.warnings
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply template: {str(e)}"
        )


@router.get("/{template_id}/statistics", response_model=TemplateStatistics)
async def get_template_statistics(
    template_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get usage statistics for a template."""
    try:
        template_service = IndustryTemplateService(db)
        stats = await template_service.get_template_statistics(template_id)
        
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template with ID {template_id} not found"
            )
        
        return TemplateStatistics(**stats)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get template statistics: {str(e)}"
        )


# Template Application Management Endpoints

@router.get("/applications/workspace/{workspace_id}", response_model=List[TemplateApplicationResponse])
async def get_workspace_template_applications(
    workspace_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get all template applications for a workspace."""
    try:
        template_service = IndustryTemplateService(db)
        applications = await template_service.get_workspace_templates(workspace_id)
        return [TemplateApplicationResponse(**app.__dict__) for app in applications]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workspace template applications: {str(e)}"
        )


@router.put("/applications/{application_id}", response_model=TemplateApplicationResponse)
async def update_template_application(
    application_id: int,
    application_update: TemplateApplicationUpdate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a template application."""
    try:
        template_service = IndustryTemplateService(db)
        
        # If customizations are being updated, use template engine
        if application_update.customizations is not None:
            template_engine = TemplateEngine(db)
            success = await template_engine.customize_template_application(
                application_id=application_id,
                customizations=application_update.customizations,
                user_id=current_user.id
            )
        else:
            success = await template_service.update_template_application(
                application_id=application_id,
                status=application_update.status,
                rating=application_update.rating,
                feedback=application_update.feedback
            )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template application with ID {application_id} not found"
            )
        
        # Return updated application info
        updated_application = await template_service.get_template_application(application_id)
        if not updated_application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template application with ID {application_id} not found after update"
            )
        return TemplateApplicationResponse.from_orm(updated_application)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update template application: {str(e)}"
        )


@router.post("/applications/{application_id}/rate", status_code=status.HTTP_200_OK)
async def rate_template_application(
    application_id: int,
    rating: TemplateRating,
    db: AsyncSession = Depends(get_db)
):
    """Rate a template application."""
    try:
        template_service = IndustryTemplateService(db)
        
        # Get the application to find the template ID
        from app.models.industry_template import TemplateApplication
        from sqlalchemy import select
        
        result = await db.execute(
            select(TemplateApplication).where(TemplateApplication.id == application_id)
        )
        application = result.scalar_one_or_none()
        
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template application with ID {application_id} not found"
            )
        
        success = await template_service.rate_template(
            template_id=application.template_id,
            application_id=application_id,
            rating=rating.rating,
            feedback=rating.feedback
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to rate template"
            )
        
        return {"message": "Template rated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rate template: {str(e)}"
        )


# Industry Data Endpoints

@router.get("/industry-data/{industry}/insights")
async def get_industry_insights(
    industry: str,
    force_refresh: bool = Query(False, description="Force refresh of cached data"),
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive insights for a specific industry."""
    try:
        data_provider = IndustryDataProvider(db)
        insights = await data_provider.get_industry_insights(
            industry=industry,
            force_refresh=force_refresh
        )
        
        # Convert dataclass to dict for JSON serialization
        return {
            "industry": insights.industry,
            "market_size": insights.market_size,
            "growth_rate": insights.growth_rate,
            "key_trends": insights.key_trends,
            "major_players": insights.major_players,
            "emerging_companies": insights.emerging_companies,
            "risk_factors": insights.risk_factors,
            "opportunities": insights.opportunities,
            "regulatory_environment": insights.regulatory_environment,
            "technology_trends": insights.technology_trends,
            "last_updated": insights.last_updated.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get industry insights: {str(e)}"
        )


@router.get("/industry-data/{industry}/competitors")
async def discover_industry_competitors(
    industry: str,
    company_name: Optional[str] = Query(None, description="Specific company to find competitors for"),
    limit: int = Query(20, ge=1, le=50, description="Maximum number of competitors to return"),
    db: AsyncSession = Depends(get_db)
):
    """Discover competitors for a specific industry or company."""
    try:
        data_provider = IndustryDataProvider(db)
        competitors = await data_provider.discover_competitors(
            industry=industry,
            company_name=company_name,
            limit=limit
        )
        
        # Convert competitor profiles to dict for JSON serialization
        return [
            {
                "name": comp.name,
                "industry": comp.industry,
                "description": comp.description,
                "website": comp.website,
                "founded_year": comp.founded_year,
                "headquarters": comp.headquarters,
                "employee_count": comp.employee_count,
                "market_cap": comp.market_cap,
                "revenue": comp.revenue,
                "funding_amount": comp.funding_amount,
                "key_products": comp.key_products,
                "target_markets": comp.target_markets,
                "competitive_advantages": comp.competitive_advantages,
                "confidence_score": comp.confidence_score,
                "last_updated": comp.last_updated.isoformat()
            }
            for comp in competitors
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to discover competitors: {str(e)}"
        )


@router.get("/industry-data/{industry}/keywords")
async def get_industry_keywords(
    industry: str,
    include_trending: bool = Query(True, description="Include trending keywords"),
    force_refresh: bool = Query(False, description="Force refresh of cached data"),
    db: AsyncSession = Depends(get_db)
):
    """Get industry-specific keywords for monitoring."""
    try:
        data_provider = IndustryDataProvider(db)
        keyword_set = await data_provider.get_industry_keywords(
            industry=industry,
            include_trending=include_trending,
            force_refresh=force_refresh
        )
        
        # Convert keyword set to dict for JSON serialization
        return {
            "industry": keyword_set.industry,
            "primary_keywords": keyword_set.primary_keywords,
            "secondary_keywords": keyword_set.secondary_keywords,
            "negative_keywords": keyword_set.negative_keywords,
            "trending_keywords": keyword_set.trending_keywords,
            "seasonal_keywords": keyword_set.seasonal_keywords,
            "confidence_scores": keyword_set.confidence_scores,
            "last_updated": keyword_set.last_updated.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get industry keywords: {str(e)}"
        )


@router.get("/industry-data/{industry}/risk-categories")
async def get_industry_risk_categories(
    industry: str,
    db: AsyncSession = Depends(get_db)
):
    """Get industry-specific risk categories."""
    try:
        data_provider = IndustryDataProvider(db)
        risk_categories = await data_provider.get_risk_categories(industry)
        return {"industry": industry, "risk_categories": risk_categories}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get risk categories: {str(e)}"
        )


# Bulk Operations and Utilities

@router.post("/bulk-operation")
async def perform_bulk_template_operation(
    operation: BulkTemplateOperation,
    db: AsyncSession = Depends(get_db)
):
    """Perform bulk operations on multiple templates."""
    try:
        template_service = IndustryTemplateService(db)
        results = {}
        
        for template_id in operation.template_ids:
            try:
                if operation.operation == "activate":
                    success = await template_service.update_template(template_id, is_active=True)
                elif operation.operation == "deactivate":
                    success = await template_service.update_template(template_id, is_active=False)
                elif operation.operation == "delete":
                    success = await template_service.delete_template(template_id)
                else:
                    success = False
                
                results[template_id] = {"success": success}
                
            except Exception as e:
                results[template_id] = {"success": False, "error": str(e)}
        
        return {"operation": operation.operation, "results": results}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform bulk operation: {str(e)}"
        )


@router.post("/validate-config", status_code=status.HTTP_200_OK)
async def validate_template_config(
    config: TemplateConfigValidation
):
    """Validate a template configuration structure."""
    try:
        # The validation is handled by Pydantic in the schema
        return {"valid": True, "message": "Template configuration is valid"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid template configuration: {str(e)}"
        )


@router.post("/cleanup")
async def cleanup_old_template_applications(
    days: int = Query(365, ge=30, le=3650, description="Age threshold in days"),
    db: AsyncSession = Depends(get_db)
):
    """Clean up old archived template applications."""
    try:
        template_service = IndustryTemplateService(db)
        cleanup_count = await template_service.cleanup_old_applications(days=days)
        
        return {
            "message": f"Cleaned up {cleanup_count} old template applications",
            "cleanup_count": cleanup_count,
            "age_threshold_days": days
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup old applications: {str(e)}"
        )