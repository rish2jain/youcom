"""
Template Engine Service

This service handles the application of industry-specific templates to workspaces,
including automatic competitor list population and template customization.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func

from app.models.industry_template import IndustryTemplate, TemplateApplication
from app.models.watch import WatchItem
from app.models.workspace import Workspace
from app.services.industry_template_service import IndustryTemplateService, TemplateStatus
from app.config import settings

logger = logging.getLogger(__name__)


class TemplateApplicationResult(str, Enum):
    """Result of template application."""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    ALREADY_APPLIED = "already_applied"


@dataclass
class ApplicationSummary:
    """Summary of template application results."""
    result: TemplateApplicationResult
    watchlist_items_created: int
    competitors_added: int
    keywords_configured: int
    notifications_configured: int
    errors: List[str]
    warnings: List[str]


@dataclass
class CompetitorInfo:
    """Information about a competitor."""
    name: str
    industry: str
    market_cap: Optional[float]
    founded_year: Optional[int]
    description: str
    website: Optional[str]
    confidence_score: float


class TemplateEngine:
    """Service for applying and customizing industry templates."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.template_service = IndustryTemplateService(db)
    
    async def apply_template(
        self,
        template_id: int,
        workspace_id: str,
        user_id: str,
        customizations: Optional[Dict[str, Any]] = None,
        auto_populate_competitors: bool = True
    ) -> ApplicationSummary:
        """Apply an industry template to a workspace."""
        try:
            # Get the template
            template = await self.template_service.get_template(template_id)
            if not template or not template.is_active:
                return ApplicationSummary(
                    result=TemplateApplicationResult.FAILED,
                    watchlist_items_created=0,
                    competitors_added=0,
                    keywords_configured=0,
                    notifications_configured=0,
                    errors=[f"Template {template_id} not found or inactive"],
                    warnings=[]
                )
            
            # Check if workspace exists
            workspace_result = await self.db.execute(
                select(Workspace).where(Workspace.id == workspace_id)
            )
            workspace = workspace_result.scalar_one_or_none()
            if not workspace:
                return ApplicationSummary(
                    result=TemplateApplicationResult.FAILED,
                    watchlist_items_created=0,
                    competitors_added=0,
                    keywords_configured=0,
                    notifications_configured=0,
                    errors=[f"Workspace {workspace_id} not found"],
                    warnings=[]
                )
            
            # Merge template config with customizations
            final_config = self._merge_configurations(
                template.template_config,
                customizations or {}
            )
            
            # Create TemplateApplication record immediately with PENDING status
            application_id = await self.template_service.apply_template(
                template_id=template_id,
                workspace_id=workspace_id,
                user_id=user_id,
                customizations=customizations,
                status="PENDING"
            )
            
            # Initialize summary
            summary = ApplicationSummary(
                result=TemplateApplicationResult.SUCCESS,
                watchlist_items_created=0,
                competitors_added=0,
                keywords_configured=0,
                notifications_configured=0,
                errors=[],
                warnings=[]
            )
            
            # Apply watchlist configuration
            watchlist_result = await self._apply_watchlist_config(
                template, final_config, workspace_id, user_id
            )
            summary.watchlist_items_created = watchlist_result["items_created"]
            summary.errors.extend(watchlist_result["errors"])
            summary.warnings.extend(watchlist_result["warnings"])
            
            # Auto-populate competitors if requested
            if auto_populate_competitors:
                competitor_result = await self._populate_competitors(
                    template, workspace_id, user_id
                )
                summary.competitors_added = competitor_result["competitors_added"]
                summary.errors.extend(competitor_result["errors"])
                summary.warnings.extend(competitor_result["warnings"])
            
            # Configure keywords
            keyword_result = await self._configure_keywords(
                template, final_config, workspace_id
            )
            summary.keywords_configured = keyword_result["keywords_configured"]
            summary.errors.extend(keyword_result["errors"])
            
            # Configure notifications
            notification_result = await self._configure_notifications(
                final_config, workspace_id
            )
            summary.notifications_configured = notification_result["notifications_configured"]
            summary.errors.extend(notification_result["errors"])
            
            # Determine final result
            if summary.errors:
                if (summary.watchlist_items_created > 0 or 
                    summary.competitors_added > 0 or 
                    summary.keywords_configured > 0):
                    summary.result = TemplateApplicationResult.PARTIAL_SUCCESS
                else:
                    summary.result = TemplateApplicationResult.FAILED
            
            # Update TemplateApplication status
            await self.template_service.update_template_application_status(
                application_id, "SUCCESS" if summary.result == TemplateApplicationResult.SUCCESS else "FAILED"
            )
            
            logger.info(f"Applied template {template_id} to workspace {workspace_id} with result: {summary.result}")
            return summary
            
        except Exception as e:
            logger.error(f"Failed to apply template {template_id} to workspace {workspace_id}: {e}")
            
            # Update TemplateApplication status to FAILED if it was created
            if 'application_id' in locals():
                try:
                    await self.template_service.update_template_application_status(application_id, "FAILED")
                except Exception as update_error:
                    logger.error(f"Failed to update template application status: {update_error}")
                    pass  # Don't fail the error handling
            
            return ApplicationSummary(
                result=TemplateApplicationResult.FAILED,
                watchlist_items_created=0,
                competitors_added=0,
                keywords_configured=0,
                notifications_configured=0,
                errors=[f"Template application failed: {str(e)}"],
                warnings=[]
            )
    
    def _merge_configurations(
        self,
        template_config: Dict[str, Any],
        customizations: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge template configuration with user customizations."""
        final_config = template_config.copy()
        
        # Deep merge customizations
        for key, value in customizations.items():
            if key in final_config and isinstance(final_config[key], dict) and isinstance(value, dict):
                final_config[key] = {**final_config[key], **value}
            else:
                final_config[key] = value
        
        return final_config
    
    async def _apply_watchlist_config(
        self,
        template: IndustryTemplate,
        config: Dict[str, Any],
        workspace_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Apply watchlist configuration from template."""
        result = {
            "items_created": 0,
            "errors": [],
            "warnings": []
        }
        
        try:
            watchlist_config = config.get("watchlist_config", {})
            companies = watchlist_config.get("companies", [])
            
            # Add default competitors from template
            if template.default_competitors:
                companies.extend(template.default_competitors)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_companies = []
            for company in companies:
                if company.lower() not in seen:
                    seen.add(company.lower())
                    unique_companies.append(company)
            
            # Create watch items for companies
            for company_name in unique_companies:
                try:
                    # Check if watch item already exists
                    existing_result = await self.db.execute(
                        select(WatchItem).where(
                            and_(
                                WatchItem.workspace_id == workspace_id,
                                func.lower(WatchItem.company_name) == company_name.lower()
                            )
                        )
                    )
                    
                    if existing_result.scalar_one_or_none():
                        result["warnings"].append(f"Watch item for '{company_name}' already exists")
                        continue
                    
                    # Create new watch item
                    watch_item = WatchItem(
                        company_name=company_name,
                        workspace_id=workspace_id,
                        created_by=user_id,
                        is_active=True,
                        keywords=template.default_keywords or [],
                        risk_categories=template.risk_categories or []
                    )
                    
                    self.db.add(watch_item)
                    result["items_created"] += 1
                    
                except Exception as e:
                    result["errors"].append(f"Failed to create watch item for '{company_name}': {str(e)}")
            
            await self.db.commit()
            
        except Exception as e:
            result["errors"].append(f"Failed to apply watchlist configuration: {str(e)}")
            await self.db.rollback()
        
        return result
    
    async def _populate_competitors(
        self,
        template: IndustryTemplate,
        workspace_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Automatically populate competitor list based on industry data."""
        result = {
            "competitors_added": 0,
            "errors": [],
            "warnings": []
        }
        
        try:
            # Get industry-specific competitors
            competitors = await self._discover_industry_competitors(
                template.industry_sector,
                limit=20
            )
            
            for competitor in competitors:
                try:
                    # Check if competitor already exists in watchlist
                    existing_result = await self.db.execute(
                        select(WatchItem).where(
                            and_(
                                WatchItem.workspace_id == workspace_id,
                                func.lower(WatchItem.company_name) == competitor.name.lower()
                            )
                        )
                    )
                    
                    if existing_result.scalar_one_or_none():
                        continue
                    
                    # Create watch item for competitor
                    watch_item = WatchItem(
                        company_name=competitor.name,
                        workspace_id=workspace_id,
                        created_by=user_id,
                        is_active=True,
                        keywords=template.default_keywords or [],
                        risk_categories=template.risk_categories or [],
                        description=competitor.description,
                        website=competitor.website
                    )
                    
                    self.db.add(watch_item)
                    result["competitors_added"] += 1
                    
                except Exception as e:
                    result["errors"].append(f"Failed to add competitor '{competitor.name}': {str(e)}")
            
            await self.db.commit()
            
        except Exception as e:
            result["errors"].append(f"Failed to populate competitors: {str(e)}")
            await self.db.rollback()
        
        return result
    
    async def _discover_industry_competitors(
        self,
        industry_sector: str,
        limit: int = 20
    ) -> List[CompetitorInfo]:
        """Discover competitors for a specific industry sector."""
        # This is a simplified implementation
        # In a real system, this would integrate with external data sources
        # like Crunchbase, PitchBook, or industry databases
        
        industry_competitors = {
            "SaaS": [
                CompetitorInfo("Salesforce", "SaaS", 250000000000, 1999, "Customer relationship management", "https://salesforce.com", 0.95),
                CompetitorInfo("Microsoft", "SaaS", 2800000000000, 1975, "Cloud computing and productivity software", "https://microsoft.com", 0.98),
                CompetitorInfo("Adobe", "SaaS", 240000000000, 1982, "Creative and marketing software", "https://adobe.com", 0.92),
                CompetitorInfo("ServiceNow", "SaaS", 120000000000, 2004, "Digital workflow automation", "https://servicenow.com", 0.88),
                CompetitorInfo("Workday", "SaaS", 60000000000, 2005, "Human capital management", "https://workday.com", 0.85),
            ],
            "FinTech": [
                CompetitorInfo("Stripe", "FinTech", 95000000000, 2010, "Online payment processing", "https://stripe.com", 0.94),
                CompetitorInfo("Square", "FinTech", 45000000000, 2009, "Financial services and payment solutions", "https://squareup.com", 0.91),
                CompetitorInfo("PayPal", "FinTech", 120000000000, 1998, "Digital payments platform", "https://paypal.com", 0.96),
                CompetitorInfo("Plaid", "FinTech", 13000000000, 2013, "Financial data connectivity", "https://plaid.com", 0.87),
                CompetitorInfo("Robinhood", "FinTech", 8000000000, 2013, "Commission-free stock trading", "https://robinhood.com", 0.82),
            ],
            "HealthTech": [
                CompetitorInfo("Teladoc", "HealthTech", 15000000000, 2002, "Telemedicine and virtual healthcare", "https://teladoc.com", 0.89),
                CompetitorInfo("Veracyte", "HealthTech", 3000000000, 2008, "Genomic diagnostics", "https://veracyte.com", 0.84),
                CompetitorInfo("10x Genomics", "HealthTech", 5000000000, 2012, "Life sciences tools", "https://10xgenomics.com", 0.86),
                CompetitorInfo("Moderna", "HealthTech", 60000000000, 2010, "mRNA therapeutics and vaccines", "https://modernatx.com", 0.93),
                CompetitorInfo("Illumina", "HealthTech", 25000000000, 1998, "DNA sequencing and array-based technologies", "https://illumina.com", 0.91),
            ],
            "E-commerce": [
                CompetitorInfo("Amazon", "E-commerce", 1500000000000, 1994, "Online marketplace and cloud services", "https://amazon.com", 0.99),
                CompetitorInfo("Shopify", "E-commerce", 80000000000, 2006, "E-commerce platform", "https://shopify.com", 0.92),
                CompetitorInfo("eBay", "E-commerce", 35000000000, 1995, "Online auction and marketplace", "https://ebay.com", 0.88),
                CompetitorInfo("Etsy", "E-commerce", 12000000000, 2005, "Handmade and vintage goods marketplace", "https://etsy.com", 0.85),
                CompetitorInfo("Wayfair", "E-commerce", 8000000000, 2002, "Home goods e-commerce", "https://wayfair.com", 0.81),
            ]
        }
        
        competitors = industry_competitors.get(industry_sector, [])
        return competitors[:limit]
    
    async def _configure_keywords(
        self,
        template: IndustryTemplate,
        config: Dict[str, Any],
        workspace_id: str
    ) -> Dict[str, Any]:
        """Configure industry-specific keywords for monitoring."""
        result = {
            "keywords_configured": 0,
            "errors": []
        }
        
        try:
            # Get keywords from template and config
            template_keywords = template.default_keywords or []
            config_keywords = config.get("watchlist_config", {}).get("keywords", [])
            
            # Combine and deduplicate keywords
            all_keywords = list(set(template_keywords + config_keywords))
            
            # Update existing watch items with keywords
            watch_items_result = await self.db.execute(
                select(WatchItem).where(WatchItem.workspace_id == workspace_id)
            )
            watch_items = watch_items_result.scalars().all()
            
            # Count unique keywords only once
            unique_keywords = set(all_keywords)
            result["keywords_configured"] = len(unique_keywords)
            
            for watch_item in watch_items:
                # Merge existing keywords with template keywords
                existing_keywords = watch_item.keywords or []
                updated_keywords = list(set(existing_keywords + all_keywords))
                watch_item.keywords = updated_keywords
            
            await self.db.commit()
            
        except Exception as e:
            result["errors"].append(f"Failed to configure keywords: {str(e)}")
            await self.db.rollback()
        
        return result
    
    async def _configure_notifications(
        self,
        config: Dict[str, Any],
        workspace_id: str
    ) -> Dict[str, Any]:
        """Configure notification rules based on template."""
        result = {
            "notifications_configured": 0,
            "errors": []
        }
        
        try:
            notification_config = config.get("notification_rules", {})
            
            # This is a simplified implementation
            # In a real system, this would create NotificationRule records
            # based on the template configuration
            
            triggers = notification_config.get("triggers", [])
            channels = notification_config.get("channels", [])
            frequency = notification_config.get("frequency", "immediate")
            
            # Count configured notifications
            result["notifications_configured"] = len(triggers) * len(channels)
            
            logger.info(f"Configured {result['notifications_configured']} notification rules for workspace {workspace_id}")
            
        except Exception as e:
            result["errors"].append(f"Failed to configure notifications: {str(e)}")
        
        return result
    
    async def customize_template_application(
        self,
        application_id: int,
        customizations: Dict[str, Any],
        user_id: str
    ) -> bool:
        """Customize an existing template application."""
        try:
            # Get the template application
            result = await self.db.execute(
                select(TemplateApplication).where(TemplateApplication.id == application_id)
            )
            application = result.scalar_one_or_none()
            
            if not application:
                logger.error(f"Template application {application_id} not found")
                return False
            
            # Update customizations
            success = await self.template_service.update_template_application(
                application_id=application_id,
                customizations=customizations,
                status=TemplateStatus.MODIFIED
            )
            
            if success:
                # Re-apply template with new customizations
                template = await self.template_service.get_template(application.template_id)
                if template:
                    await self._apply_customizations(
                        template, customizations, application.workspace_id, user_id
                    )
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to customize template application {application_id}: {e}")
            return False
    
    async def _apply_customizations(
        self,
        template: IndustryTemplate,
        customizations: Dict[str, Any],
        workspace_id: str,
        user_id: str
    ) -> None:
        """Apply customizations to an existing template application."""
        try:
            # Handle watchlist customizations
            if "watchlist_config" in customizations:
                watchlist_config = customizations["watchlist_config"]
                
                # Add new companies if specified
                if "additional_companies" in watchlist_config:
                    for company_name in watchlist_config["additional_companies"]:
                        # Check if already exists
                        existing_result = await self.db.execute(
                            select(WatchItem).where(
                                and_(
                                    WatchItem.workspace_id == workspace_id,
                                    func.lower(WatchItem.company_name) == company_name.lower()
                                )
                            )
                        )
                        
                        if not existing_result.scalar_one_or_none():
                            watch_item = WatchItem(
                                company_name=company_name,
                                workspace_id=workspace_id,
                                created_by=user_id,
                                is_active=True,
                                keywords=template.default_keywords or []
                            )
                            self.db.add(watch_item)
                
                # Remove companies if specified
                if "remove_companies" in watchlist_config:
                    for company_name in watchlist_config["remove_companies"]:
                        result = await self.db.execute(
                            select(WatchItem).where(
                                and_(
                                    WatchItem.workspace_id == workspace_id,
                                    func.lower(WatchItem.company_name) == company_name.lower()
                                )
                            )
                        )
                        watch_item = result.scalar_one_or_none()
                        if watch_item:
                            watch_item.is_active = False
            
            await self.db.commit()
            logger.info(f"Applied customizations to workspace {workspace_id}")
            
        except Exception as e:
            logger.error(f"Failed to apply customizations: {e}")
            await self.db.rollback()
    
    async def get_template_preview(
        self,
        template_id: int,
        customizations: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get a preview of what will be applied when using a template."""
        try:
            template = await self.template_service.get_template(template_id)
            if not template:
                return {"error": "Template not found"}
            
            # Merge configurations
            final_config = self._merge_configurations(
                template.template_config,
                customizations or {}
            )
            
            # Get competitor preview
            competitors = await self._discover_industry_competitors(
                template.industry_sector,
                limit=10
            )
            
            preview = {
                "template_name": template.name,
                "industry_sector": template.industry_sector,
                "description": template.description,
                "watchlist_items": {
                    "default_competitors": template.default_competitors or [],
                    "discovered_competitors": [c.name for c in competitors],
                    "total_companies": len(template.default_competitors or []) + len(competitors)
                },
                "keywords": template.default_keywords or [],
                "risk_categories": template.risk_categories or [],
                "kpi_metrics": template.kpi_metrics or [],
                "configuration": final_config
            }
            
            return preview
            
        except Exception as e:
            logger.error(f"Failed to generate template preview: {e}")
            return {"error": f"Failed to generate preview: {str(e)}"}
    
    async def validate_template_compatibility(
        self,
        template_id: int,
        workspace_id: str
    ) -> Dict[str, Any]:
        """Validate if a template is compatible with a workspace."""
        try:
            template = await self.template_service.get_template(template_id)
            if not template:
                return {"compatible": False, "reason": "Template not found"}
            
            # Check existing watch items
            existing_result = await self.db.execute(
                select(func.count(WatchItem.id)).where(WatchItem.workspace_id == workspace_id)
            )
            existing_count = existing_result.scalar()
            
            # Check for conflicts
            conflicts = []
            if existing_count > 0:
                # Check for duplicate companies
                for competitor in template.default_competitors or []:
                    duplicate_result = await self.db.execute(
                        select(WatchItem).where(
                            and_(
                                WatchItem.workspace_id == workspace_id,
                                func.lower(WatchItem.company_name) == competitor.lower()
                            )
                        )
                    )
                    if duplicate_result.scalar_one_or_none():
                        conflicts.append(f"Company '{competitor}' already exists in watchlist")
            
            return {
                "compatible": len(conflicts) == 0,
                "existing_items": existing_count,
                "conflicts": conflicts,
                "recommendations": [
                    "Consider customizing the template to avoid duplicates" if conflicts else "Template can be applied directly"
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to validate template compatibility: {e}")
            return {"compatible": False, "reason": f"Validation failed: {str(e)}"}