"""
Industry Template Repository Service

This service manages industry-specific templates for competitive intelligence configuration,
providing CRUD operations, template application, and customization capabilities.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func, update
from sqlalchemy.orm import selectinload

from app.models.industry_template import IndustryTemplate, TemplateApplication
from app.config import settings

logger = logging.getLogger(__name__)


class TemplateStatus(str, Enum):
    """Status of a template application."""
    ACTIVE = "active"
    MODIFIED = "modified"
    ARCHIVED = "archived"


@dataclass
class TemplateMetadata:
    """Metadata for an industry template."""
    id: int
    name: str
    industry_sector: str
    description: str
    usage_count: int
    rating: float
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]


@dataclass
class TemplateApplicationInfo:
    """Information about a template application."""
    id: int
    template_id: int
    workspace_id: str
    user_id: str
    status: str
    applied_at: datetime
    rating: Optional[float]
    feedback: Optional[str]
    template_name: str
    industry_sector: str


class IndustryTemplateService:
    """Service for managing industry templates and their applications."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_template(
        self,
        name: str,
        industry_sector: str,
        template_config: Dict[str, Any],
        description: str = "",
        default_competitors: Optional[List[str]] = None,
        default_keywords: Optional[List[str]] = None,
        risk_categories: Optional[List[str]] = None,
        kpi_metrics: Optional[List[str]] = None,
        created_by: Optional[str] = None
    ) -> int:
        """Create a new industry template."""
        try:
            template = IndustryTemplate(
                name=name,
                industry_sector=industry_sector,
                description=description,
                template_config=template_config,
                default_competitors=default_competitors or [],
                default_keywords=default_keywords or [],
                risk_categories=risk_categories or [],
                kpi_metrics=kpi_metrics or [],
                created_by=created_by
            )
            
            self.db.add(template)
            await self.db.commit()
            await self.db.refresh(template)
            
            logger.info(f"Created template '{name}' for industry '{industry_sector}' with ID {template.id}")
            return template.id
            
        except Exception as e:
            logger.error(f"Failed to create template: {e}")
            await self.db.rollback()
            raise
    
    async def get_template(self, template_id: int) -> Optional[IndustryTemplate]:
        """Get a template by ID."""
        result = await self.db.execute(
            select(IndustryTemplate).where(IndustryTemplate.id == template_id)
        )
        return result.scalar_one_or_none()
    
    async def get_template_by_name(self, name: str, industry_sector: str) -> Optional[IndustryTemplate]:
        """Get a template by name and industry sector."""
        result = await self.db.execute(
            select(IndustryTemplate).where(
                and_(
                    IndustryTemplate.name == name,
                    IndustryTemplate.industry_sector == industry_sector
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def list_templates(
        self,
        industry_sector: Optional[str] = None,
        is_active: bool = True,
        limit: int = 50,
        offset: int = 0
    ) -> List[TemplateMetadata]:
        """List available templates with optional filtering."""
        query = select(IndustryTemplate)
        
        if industry_sector:
            query = query.where(IndustryTemplate.industry_sector == industry_sector)
        
        if is_active is not None:
            query = query.where(IndustryTemplate.is_active == is_active)
        
        query = query.order_by(desc(IndustryTemplate.rating), desc(IndustryTemplate.usage_count))
        query = query.limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        templates = result.scalars().all()
        
        return [
            TemplateMetadata(
                id=template.id,
                name=template.name,
                industry_sector=template.industry_sector,
                description=template.description,
                usage_count=template.usage_count,
                rating=template.rating,
                is_active=template.is_active,
                created_at=template.created_at,
                updated_at=template.updated_at,
                created_by=template.created_by
            )
            for template in templates
        ]
    
    async def get_industries(self) -> List[str]:
        """Get list of available industry sectors."""
        result = await self.db.execute(
            select(IndustryTemplate.industry_sector)
            .where(IndustryTemplate.is_active == True)
            .distinct()
            .order_by(IndustryTemplate.industry_sector)
        )
        return [row[0] for row in result.fetchall()]
    
    async def update_template(
        self,
        template_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        template_config: Optional[Dict[str, Any]] = None,
        default_competitors: Optional[List[str]] = None,
        default_keywords: Optional[List[str]] = None,
        risk_categories: Optional[List[str]] = None,
        kpi_metrics: Optional[List[str]] = None,
        is_active: Optional[bool] = None
    ) -> bool:
        """Update an existing template."""
        try:
            template = await self.get_template(template_id)
            if not template:
                return False
            
            # Update fields if provided
            if name is not None:
                template.name = name
            if description is not None:
                template.description = description
            if template_config is not None:
                template.template_config = template_config
            if default_competitors is not None:
                template.default_competitors = default_competitors
            if default_keywords is not None:
                template.default_keywords = default_keywords
            if risk_categories is not None:
                template.risk_categories = risk_categories
            if kpi_metrics is not None:
                template.kpi_metrics = kpi_metrics
            if is_active is not None:
                template.is_active = is_active
            
            template.updated_at = datetime.utcnow()
            
            await self.db.commit()
            logger.info(f"Updated template {template_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update template {template_id}: {e}")
            await self.db.rollback()
            return False
    
    async def delete_template(self, template_id: int) -> bool:
        """Delete a template (soft delete by setting is_active=False)."""
        try:
            result = await self.db.execute(
                update(IndustryTemplate)
                .where(IndustryTemplate.id == template_id)
                .values(is_active=False, updated_at=datetime.utcnow())
            )
            
            if result.rowcount > 0:
                await self.db.commit()
                logger.info(f"Deleted template {template_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete template {template_id}: {e}")
            await self.db.rollback()
            return False
    
    async def apply_template(
        self,
        template_id: int,
        workspace_id: str,
        user_id: str,
        customizations: Optional[Dict[str, Any]] = None
    ) -> int:
        """Apply a template to a workspace."""
        try:
            # Check if template exists and is active
            template = await self.get_template(template_id)
            if not template or not template.is_active:
                raise ValueError(f"Template {template_id} not found or inactive")
            
            # Check if template is already applied to this workspace
            existing_result = await self.db.execute(
                select(TemplateApplication).where(
                    and_(
                        TemplateApplication.template_id == template_id,
                        TemplateApplication.workspace_id == workspace_id,
                        TemplateApplication.status == TemplateStatus.ACTIVE.value
                    )
                )
            )
            
            existing_application = existing_result.scalar_one_or_none()
            if existing_application:
                # Update existing application
                existing_application.customizations = customizations or {}
                existing_application.applied_at = datetime.utcnow()
                application_id = existing_application.id
            else:
                # Create new application
                application = TemplateApplication(
                    template_id=template_id,
                    workspace_id=workspace_id,
                    user_id=user_id,
                    customizations=customizations or {},
                    status=TemplateStatus.ACTIVE.value
                )
                
                self.db.add(application)
                await self.db.flush()  # Get the ID
                application_id = application.id
            
            # Increment usage count atomically
            await self.db.execute(
                update(IndustryTemplate)
                .where(IndustryTemplate.id == template_id)
                .values(usage_count=IndustryTemplate.usage_count + 1)
            )
            
            await self.db.commit()
            logger.info(f"Applied template {template_id} to workspace {workspace_id}")
            return application_id
            
        except Exception as e:
            logger.error(f"Failed to apply template {template_id} to workspace {workspace_id}: {e}")
            await self.db.rollback()
            raise
    
    async def get_workspace_templates(self, workspace_id: str) -> List[TemplateApplicationInfo]:
        """Get all template applications for a workspace."""
        result = await self.db.execute(
            select(TemplateApplication, IndustryTemplate.name, IndustryTemplate.industry_sector)
            .join(IndustryTemplate, TemplateApplication.template_id == IndustryTemplate.id)
            .where(TemplateApplication.workspace_id == workspace_id)
            .order_by(desc(TemplateApplication.applied_at))
        )
        
        applications = []
        for app, template_name, industry_sector in result.fetchall():
            applications.append(TemplateApplicationInfo(
                id=app.id,
                template_id=app.template_id,
                workspace_id=app.workspace_id,
                user_id=app.user_id,
                status=app.status,
                applied_at=app.applied_at,
                rating=app.rating,
                feedback=app.feedback,
                template_name=template_name,
                industry_sector=industry_sector
            ))
        
        return applications
    
    async def update_template_application(
        self,
        application_id: int,
        customizations: Optional[Dict[str, Any]] = None,
        status: Optional[TemplateStatus] = None,
        rating: Optional[float] = None,
        feedback: Optional[str] = None
    ) -> bool:
        """Update a template application."""
        try:
            result = await self.db.execute(
                select(TemplateApplication).where(TemplateApplication.id == application_id)
            )
            application = result.scalar_one_or_none()
            
            if not application:
                return False
            
            # Update fields if provided
            if customizations is not None:
                application.customizations = customizations
                application.status = TemplateStatus.MODIFIED.value
            if status is not None:
                application.status = status.value
            if rating is not None:
                application.rating = rating
            if feedback is not None:
                application.feedback = feedback
            
            await self.db.commit()
            logger.info(f"Updated template application {application_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update template application {application_id}: {e}")
            await self.db.rollback()
            return False
    
    async def rate_template(
        self,
        template_id: int,
        application_id: int,
        rating: float,
        feedback: Optional[str] = None
    ) -> bool:
        """Rate a template and update overall template rating."""
        try:
            if not (0.0 <= rating <= 5.0):
                raise ValueError("Rating must be between 0.0 and 5.0")
            
            # Update application rating
            await self.update_template_application(
                application_id=application_id,
                rating=rating,
                feedback=feedback
            )
            
            # Recalculate template average rating
            result = await self.db.execute(
                select(func.avg(TemplateApplication.rating), func.count(TemplateApplication.rating))
                .where(
                    and_(
                        TemplateApplication.template_id == template_id,
                        TemplateApplication.rating.isnot(None)
                    )
                )
            )
            
            avg_rating, rating_count = result.first()
            
            if avg_rating is not None:
                await self.db.execute(
                    update(IndustryTemplate)
                    .where(IndustryTemplate.id == template_id)
                    .values(rating=float(avg_rating))
                )
            
            await self.db.commit()
            logger.info(f"Updated rating for template {template_id}: {avg_rating} ({rating_count} ratings)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rate template {template_id}: {e}")
            await self.db.rollback()
            return False
    
    async def get_template_statistics(self, template_id: int) -> Dict[str, Any]:
        """Get usage statistics for a template."""
        template = await self.get_template(template_id)
        if not template:
            return {}
        
        # Application statistics
        app_result = await self.db.execute(
            select(
                TemplateApplication.status,
                func.count(TemplateApplication.id)
            )
            .where(TemplateApplication.template_id == template_id)
            .group_by(TemplateApplication.status)
        )
        
        status_counts = dict(app_result.fetchall())
        
        # Rating statistics
        rating_result = await self.db.execute(
            select(
                func.avg(TemplateApplication.rating),
                func.count(TemplateApplication.rating),
                func.min(TemplateApplication.rating),
                func.max(TemplateApplication.rating)
            )
            .where(
                and_(
                    TemplateApplication.template_id == template_id,
                    TemplateApplication.rating.isnot(None)
                )
            )
        )
        
        avg_rating, rating_count, min_rating, max_rating = rating_result.first()
        
        return {
            "template_id": template_id,
            "name": template.name,
            "industry_sector": template.industry_sector,
            "total_usage": template.usage_count,
            "status_counts": status_counts,
            "rating_stats": {
                "average": float(avg_rating) if avg_rating else 0.0,
                "count": rating_count or 0,
                "min": float(min_rating) if min_rating else 0.0,
                "max": float(max_rating) if max_rating else 0.0
            },
            "created_at": template.created_at,
            "updated_at": template.updated_at
        }
    
    async def search_templates(
        self,
        query: str,
        industry_sector: Optional[str] = None,
        limit: int = 20
    ) -> List[TemplateMetadata]:
        """Search templates by name or description."""
        search_query = select(IndustryTemplate).where(IndustryTemplate.is_active == True)
        
        # Add text search
        search_pattern = f"%{query.lower()}%"
        search_query = search_query.where(
            func.lower(IndustryTemplate.name).like(search_pattern) |
            func.lower(IndustryTemplate.description).like(search_pattern)
        )
        
        # Add industry filter
        if industry_sector:
            search_query = search_query.where(IndustryTemplate.industry_sector == industry_sector)
        
        search_query = search_query.order_by(
            desc(IndustryTemplate.rating),
            desc(IndustryTemplate.usage_count)
        ).limit(limit)
        
        result = await self.db.execute(search_query)
        templates = result.scalars().all()
        
        return [
            TemplateMetadata(
                id=template.id,
                name=template.name,
                industry_sector=template.industry_sector,
                description=template.description,
                usage_count=template.usage_count,
                rating=template.rating,
                is_active=template.is_active,
                created_at=template.created_at,
                updated_at=template.updated_at,
                created_by=template.created_by
            )
            for template in templates
        ]
    
    async def get_popular_templates(self, limit: int = 10) -> List[TemplateMetadata]:
        """Get most popular templates by usage and rating."""
        result = await self.db.execute(
            select(IndustryTemplate)
            .where(IndustryTemplate.is_active == True)
            .order_by(
                desc(IndustryTemplate.rating),
                desc(IndustryTemplate.usage_count),
                desc(IndustryTemplate.created_at)
            )
            .limit(limit)
        )
        
        templates = result.scalars().all()
        
        return [
            TemplateMetadata(
                id=template.id,
                name=template.name,
                industry_sector=template.industry_sector,
                description=template.description,
                usage_count=template.usage_count,
                rating=template.rating,
                is_active=template.is_active,
                created_at=template.created_at,
                updated_at=template.updated_at,
                created_by=template.created_by
            )
            for template in templates
        ]
    
    async def cleanup_old_applications(self, days: int = 365) -> int:
        """Clean up old archived template applications."""
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        result = await self.db.execute(
            select(TemplateApplication)
            .where(
                and_(
                    TemplateApplication.status == TemplateStatus.ARCHIVED.value,
                    TemplateApplication.applied_at < cutoff_date
                )
            )
        )
        
        applications_to_delete = result.scalars().all()
        cleanup_count = 0
        
        for application in applications_to_delete:
            await self.db.delete(application)
            cleanup_count += 1
        
        await self.db.commit()
        logger.info(f"Cleaned up {cleanup_count} old template applications")
        
        return cleanup_count