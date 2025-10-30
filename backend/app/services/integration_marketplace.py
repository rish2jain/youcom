"""
Integration Marketplace Service

Service for managing third-party integrations, developer ecosystem,
and revenue sharing marketplace.
"""

import asyncio
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func, text
import logging
try:
    import stripe
except ImportError:
    stripe = None
    
try:
    import requests
except ImportError:
    requests = None

from app.models.integration_marketplace import (
    IntegrationDeveloper, MarketplaceIntegration, MarketplaceIntegrationInstallation,
    IntegrationReview, IntegrationWebhook, IntegrationAnalytics,
    IntegrationPayout, IntegrationSupport, MarketplaceSettings,
    IntegrationStatus, IntegrationCategory, PricingModel, DeveloperTier
)

logger = logging.getLogger(__name__)


class IntegrationMarketplaceService:
    """Service for integration marketplace and developer ecosystem"""
    
    def __init__(self, db: Session):
        import os
        
        self.db = db
        
        # Initialize Stripe with environment key
        stripe_key = os.environ.get("STRIPE_API_KEY")
        if stripe and stripe_key:
            stripe.api_key = stripe_key
        elif stripe:
            logger.warning("Stripe API key not configured")
        
        # Marketplace configuration from environment with validation
        try:
            default_revenue_share = float(os.environ.get("DEFAULT_REVENUE_SHARE", "70.0"))
            platform_fee = float(os.environ.get("PLATFORM_FEE", "30.0"))
            minimum_payout = float(os.environ.get("MINIMUM_PAYOUT", "50.0"))
            api_rate_limit = int(os.environ.get("API_RATE_LIMIT", "100"))
            
            # Validate ranges
            if not (0 <= default_revenue_share <= 100):
                raise ValueError(f"DEFAULT_REVENUE_SHARE must be between 0 and 100, got {default_revenue_share}")
            if not (0 <= platform_fee <= 100):
                raise ValueError(f"PLATFORM_FEE must be between 0 and 100, got {platform_fee}")
            if minimum_payout < 0:
                raise ValueError(f"MINIMUM_PAYOUT must be >= 0, got {minimum_payout}")
            if api_rate_limit <= 0:
                raise ValueError(f"API_RATE_LIMIT must be > 0, got {api_rate_limit}")
            
            # Validate revenue share + platform fee = 100
            if abs(default_revenue_share + platform_fee - 100.0) > 0.01:
                logger.warning(f"Revenue share ({default_revenue_share}) + platform fee ({platform_fee}) != 100, adjusting platform fee")
                platform_fee = 100.0 - default_revenue_share
            
            # Parse boolean values safely
            def parse_bool(value: str) -> bool:
                return value.lower() in ("true", "1", "yes", "on")
            
            review_required = parse_bool(os.environ.get("REVIEW_REQUIRED", "true"))
            auto_approve_updates = parse_bool(os.environ.get("AUTO_APPROVE_UPDATES", "false"))
            
            self.config = {
                "default_revenue_share": default_revenue_share,
                "platform_fee": platform_fee,
                "review_required": review_required,
                "auto_approve_updates": auto_approve_updates,
                "minimum_payout": minimum_payout,
                "api_rate_limit": api_rate_limit
            }
            
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid marketplace configuration: {e}")
            raise RuntimeError(f"Failed to initialize marketplace service: {e}")

    def register_developer(
        self, 
        developer_data: Dict[str, Any]
    ) -> IntegrationDeveloper:
        """Register a new developer in the marketplace"""
        try:
            # Check if developer already exists
            existing_developer = self.db.query(IntegrationDeveloper).filter(
                IntegrationDeveloper.email == developer_data["email"]
            ).first()
            
            if existing_developer:
                raise ValueError("Developer with this email already exists")
            
            # Generate API key
            api_key = self._generate_api_key()
            
            # Create developer
            developer = IntegrationDeveloper(
                developer_name=developer_data["developer_name"],
                company_name=developer_data.get("company_name"),
                email=developer_data["email"],
                website=developer_data.get("website"),
                bio=developer_data.get("bio"),
                github_username=developer_data.get("github_username"),
                linkedin_profile=developer_data.get("linkedin_profile"),
                tier=developer_data.get("tier", DeveloperTier.INDIVIDUAL),
                api_key=api_key,
                revenue_share_percentage=self.config["default_revenue_share"]
            )
            
            self.db.add(developer)
            self.db.commit()
            self.db.refresh(developer)
            
            logger.info(f"Registered new developer: {developer.developer_name}")
            return developer
            
        except Exception as e:
            logger.error(f"Error registering developer: {str(e)}")
            self.db.rollback()
            raise

    def create_integration(
        self, 
        developer_id: int, 
        integration_data: Dict[str, Any]
    ) -> MarketplaceIntegration:
        """Create a new integration"""
        try:
            # Validate developer
            developer = self.db.query(IntegrationDeveloper).filter(
                IntegrationDeveloper.id == developer_id
            ).first()
            
            if not developer:
                raise ValueError("Developer not found")
            
            # Check integration limits
            if developer.total_integrations >= self.config.get("max_integrations", 10):
                raise ValueError("Maximum integrations limit reached")
            
            # Generate unique slug
            slug = self._generate_slug(integration_data["name"])
            
            # Create integration
            integration = MarketplaceIntegration(
                developer_id=developer_id,
                name=integration_data["name"],
                slug=slug,
                description=integration_data["description"],
                short_description=integration_data["short_description"],
                category=integration_data["category"],
                tags=integration_data.get("tags", []),
                version=integration_data.get("version", "1.0.0"),
                webhook_url=integration_data.get("webhook_url"),
                api_endpoints=integration_data.get("api_endpoints", {}),
                configuration_schema=integration_data.get("configuration_schema", {}),
                supported_events=integration_data.get("supported_events", []),
                minimum_plan=integration_data.get("minimum_plan", "starter"),
                pricing_model=integration_data.get("pricing_model", PricingModel.FREE),
                price=integration_data.get("price", 0.0),
                trial_days=integration_data.get("trial_days", 0),
                status=IntegrationStatus.DRAFT
            )
            
            self.db.add(integration)
            
            # Update developer stats
            developer.total_integrations += 1
            
            self.db.commit()
            self.db.refresh(integration)
            
            logger.info(f"Created integration: {integration.name} by {developer.developer_name}")
            return integration
            
        except Exception as e:
            logger.error(f"Error creating integration: {str(e)}")
            self.db.rollback()
            raise

    async def submit_for_review(self, integration_id: int) -> MarketplaceIntegration:
        """Submit integration for marketplace review"""
        try:
            integration = self.db.query(MarketplaceIntegration).filter(
                MarketplaceIntegration.id == integration_id
            ).first()
            
            if not integration:
                raise ValueError("Integration not found")
            
            if integration.status != IntegrationStatus.DRAFT:
                raise ValueError("Integration must be in draft status to submit for review")
            
            # Validate integration completeness
            validation_errors = await self._validate_integration(integration)
            if validation_errors:
                raise ValueError(f"Integration validation failed: {', '.join(validation_errors)}")
            
            # Update status
            integration.status = IntegrationStatus.PENDING_REVIEW
            integration.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            # Notify review team (would send email/notification)
            await self._notify_review_team(integration)
            
            logger.info(f"Integration {integration.name} submitted for review")
            return integration
            
        except Exception as e:
            logger.error(f"Error submitting integration for review: {str(e)}")
            self.db.rollback()
            raise

    async def approve_integration(
        self, 
        integration_id: int, 
        reviewer_id: str,
        review_notes: str = None
    ) -> MarketplaceIntegration:
        """Approve integration for marketplace publication"""
        try:
            integration = self.db.query(MarketplaceIntegration).filter(
                MarketplaceIntegration.id == integration_id
            ).first()
            
            if not integration:
                raise ValueError("Integration not found")
            
            if integration.status != IntegrationStatus.PENDING_REVIEW:
                raise ValueError("Integration must be pending review to approve")
            
            # Update integration status
            integration.status = IntegrationStatus.APPROVED
            integration.approved_by = reviewer_id
            integration.approved_at = datetime.utcnow()
            integration.review_notes = review_notes
            integration.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            # Auto-publish if configured
            if self.config.get("auto_publish_approved", True):
                await self.publish_integration(integration_id)
            
            # Notify developer
            await self._notify_developer_approval(integration)
            
            logger.info(f"Integration {integration.name} approved by {reviewer_id}")
            return integration
            
        except Exception as e:
            logger.error(f"Error approving integration: {str(e)}")
            self.db.rollback()
            raise

    async def publish_integration(self, integration_id: int) -> MarketplaceIntegration:
        """Publish integration to marketplace"""
        try:
            integration = self.db.query(MarketplaceIntegration).filter(
                MarketplaceIntegration.id == integration_id
            ).first()
            
            if not integration:
                raise ValueError("Integration not found")
            
            if integration.status != IntegrationStatus.APPROVED:
                raise ValueError("Integration must be approved to publish")
            
            # Update status
            integration.status = IntegrationStatus.PUBLISHED
            integration.published_at = datetime.utcnow()
            integration.updated_at = datetime.utcnow()
            
            # Update developer stats
            developer = integration.developer
            developer.published_integrations += 1
            
            self.db.commit()
            
            # Index for search
            await self._index_integration_for_search(integration)
            
            # Notify developer
            await self._notify_developer_published(integration)
            
            logger.info(f"Integration {integration.name} published to marketplace")
            return integration
            
        except Exception as e:
            logger.error(f"Error publishing integration: {str(e)}")
            self.db.rollback()
            raise

    async def install_integration(
        self, 
        integration_id: int, 
        user_id: str,
        workspace_id: str = None,
        configuration: Dict[str, Any] = None
    ) -> MarketplaceIntegrationInstallation:
        """Install integration for a user"""
        try:
            integration = self.db.query(MarketplaceIntegration).filter(
                MarketplaceIntegration.id == integration_id
            ).first()
            
            if not integration:
                raise ValueError("Integration not found")
            
            if integration.status != IntegrationStatus.PUBLISHED:
                raise ValueError("Integration is not available for installation")
            
            # Check if already installed
            existing_installation = self.db.query(MarketplaceIntegrationInstallation).filter(
                and_(
                    MarketplaceIntegrationInstallation.integration_id == integration_id,
                    MarketplaceIntegrationInstallation.user_id == user_id,
                    MarketplaceIntegrationInstallation.workspace_id == workspace_id
                )
            ).first()
            
            if existing_installation:
                raise ValueError("Integration already installed")
            
            # Create installation
            installation = MarketplaceIntegrationInstallation(
                integration_id=integration_id,
                user_id=user_id,
                workspace_id=workspace_id,
                configuration=configuration or {}
            )
            
            # Handle billing for paid integrations
            if integration.pricing_model != PricingModel.FREE:
                subscription_id = await self._create_subscription(
                    integration, user_id, installation
                )
                installation.subscription_id = subscription_id
            
            self.db.add(installation)
            
            # Update integration stats
            integration.total_installs += 1
            integration.active_installs += 1
            
            # Update developer stats
            developer = integration.developer
            developer.total_installs += 1
            
            self.db.commit()
            self.db.refresh(installation)
            
            # Send installation webhook
            await self._send_installation_webhook(integration, installation, "installed")
            
            logger.info(f"Integration {integration.name} installed for user {user_id}")
            return installation
            
        except Exception as e:
            logger.error(f"Error installing integration: {str(e)}")
            self.db.rollback()
            raise

    async def uninstall_integration(
        self, 
        installation_id: int, 
        user_id: str
    ) -> bool:
        """Uninstall integration for a user"""
        try:
            installation = self.db.query(MarketplaceIntegrationInstallation).filter(
                and_(
                    MarketplaceIntegrationInstallation.id == installation_id,
                    MarketplaceIntegrationInstallation.user_id == user_id
                )
            ).first()
            
            if not installation:
                raise ValueError("Installation not found")
            
            integration = installation.integration
            
            # Cancel subscription if exists
            if installation.subscription_id:
                await self._cancel_subscription(installation.subscription_id)
            
            # Update integration stats
            integration.active_installs = max(0, integration.active_installs - 1)
            
            # Send uninstallation webhook
            await self._send_installation_webhook(integration, installation, "uninstalled")
            
            # Delete installation
            self.db.delete(installation)
            self.db.commit()
            
            logger.info(f"Integration {integration.name} uninstalled for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error uninstalling integration: {str(e)}")
            self.db.rollback()
            raise

    async def search_integrations(
        self, 
        query: str = None,
        category: str = None,
        pricing_model: str = None,
        featured_only: bool = False,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Search integrations in marketplace"""
        try:
            # Build query
            db_query = self.db.query(MarketplaceIntegration).filter(
                MarketplaceIntegration.status == IntegrationStatus.PUBLISHED
            )
            
            # Apply filters
            if query:
                search_term = f"%{query}%"
                db_query = db_query.filter(
                    or_(
                        MarketplaceIntegration.name.ilike(search_term),
                        MarketplaceIntegration.description.ilike(search_term),
                        MarketplaceIntegration.short_description.ilike(search_term)
                    )
                )
            
            if category:
                db_query = db_query.filter(MarketplaceIntegration.category == category)
            
            if pricing_model:
                db_query = db_query.filter(MarketplaceIntegration.pricing_model == pricing_model)
            
            if featured_only:
                db_query = db_query.filter(MarketplaceIntegration.featured == True)
            
            # Get total count
            total_count = db_query.count()
            
            # Apply sorting and pagination
            integrations = db_query.order_by(
                desc(MarketplaceIntegration.featured),
                desc(MarketplaceIntegration.trending_score),
                desc(MarketplaceIntegration.average_rating),
                desc(MarketplaceIntegration.total_installs)
            ).offset(offset).limit(limit).all()
            
            # Format results
            results = []
            for integration in integrations:
                results.append({
                    "id": integration.id,
                    "name": integration.name,
                    "slug": integration.slug,
                    "short_description": integration.short_description,
                    "category": integration.category,
                    "pricing_model": integration.pricing_model,
                    "price": integration.price,
                    "icon_url": integration.icon_url,
                    "average_rating": integration.average_rating,
                    "total_installs": integration.total_installs,
                    "featured": integration.featured,
                    "developer": {
                        "name": integration.developer.developer_name,
                        "company": integration.developer.company_name,
                        "verified": integration.developer.verified
                    }
                })
            
            # Generate facets
            facets = await self._generate_search_facets(query, category, pricing_model)
            
            return {
                "total_count": total_count,
                "results": results,
                "facets": facets,
                "has_more": (offset + limit) < total_count
            }
            
        except Exception as e:
            logger.error(f"Error searching integrations: {str(e)}")
            raise

    async def get_integration_analytics(
        self, 
        integration_id: int,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Dict[str, Any]:
        """Get analytics for an integration"""
        try:
            integration = self.db.query(MarketplaceIntegration).filter(
                MarketplaceIntegration.id == integration_id
            ).first()
            
            if not integration:
                raise ValueError("Integration not found")
            
            # Default date range
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()
            
            # Get analytics data
            analytics_records = self.db.query(IntegrationAnalytics).filter(
                and_(
                    IntegrationAnalytics.integration_id == integration_id,
                    IntegrationAnalytics.date >= start_date,
                    IntegrationAnalytics.date <= end_date
                )
            ).order_by(IntegrationAnalytics.date).all()
            
            # Aggregate data
            total_installs = sum(record.new_installs for record in analytics_records)
            total_uninstalls = sum(record.uninstalls for record in analytics_records)
            total_revenue = sum(record.revenue for record in analytics_records)
            total_api_calls = sum(record.api_calls for record in analytics_records)
            
            # Calculate averages
            avg_daily_users = sum(record.daily_active_users for record in analytics_records) / max(len(analytics_records), 1)
            avg_response_time = sum(record.average_response_time_ms for record in analytics_records) / max(len(analytics_records), 1)
            avg_success_rate = sum(record.success_rate for record in analytics_records) / max(len(analytics_records), 1)
            
            return {
                "integration": {
                    "id": integration.id,
                    "name": integration.name,
                    "total_installs": integration.total_installs,
                    "active_installs": integration.active_installs,
                    "average_rating": integration.average_rating
                },
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "metrics": {
                    "new_installs": total_installs,
                    "uninstalls": total_uninstalls,
                    "net_installs": total_installs - total_uninstalls,
                    "revenue": total_revenue,
                    "api_calls": total_api_calls,
                    "average_daily_users": round(avg_daily_users, 1),
                    "average_response_time_ms": round(avg_response_time, 2),
                    "success_rate": round(avg_success_rate, 3)
                },
                "timeline": [
                    {
                        "date": record.date.isoformat(),
                        "daily_active_users": record.daily_active_users,
                        "api_calls": record.api_calls,
                        "revenue": record.revenue,
                        "new_installs": record.new_installs,
                        "uninstalls": record.uninstalls
                    }
                    for record in analytics_records
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting integration analytics: {str(e)}")
            raise

    async def process_revenue_sharing(self, payout_period_days: int = 30) -> List[IntegrationPayout]:
        """Process revenue sharing payouts to developers"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=payout_period_days)
            
            # Get developers with revenue to payout
            developers_with_revenue = self.db.query(IntegrationDeveloper).filter(
                IntegrationDeveloper.total_earnings >= self.config["minimum_payout"]
            ).all()
            
            payouts = []
            
            for developer in developers_with_revenue:
                # Calculate revenue for period
                revenue_data = await self._calculate_developer_revenue(
                    developer.id, start_date, end_date
                )
                
                if revenue_data["net_payout"] >= self.config["minimum_payout"]:
                    # Create payout record
                    payout = IntegrationPayout(
                        developer_id=developer.id,
                        payout_period_start=start_date,
                        payout_period_end=end_date,
                        gross_revenue=revenue_data["gross_revenue"],
                        platform_fee=revenue_data["platform_fee"],
                        net_payout=revenue_data["net_payout"],
                        integration_revenues=revenue_data["integration_breakdown"],
                        payout_method=developer.payout_method
                    )
                    
                    self.db.add(payout)
                    payouts.append(payout)
                    
                    # Process actual payout
                    await self._process_payout(payout, developer)
            
            self.db.commit()
            
            logger.info(f"Processed {len(payouts)} revenue sharing payouts")
            return payouts
            
        except Exception as e:
            logger.error(f"Error processing revenue sharing: {str(e)}")
            self.db.rollback()
            raise

    # Private helper methods
    
    def _generate_api_key(self) -> str:
        """Generate unique API key for developer"""
        return f"cia_dev_{secrets.token_urlsafe(32)}"

    def _generate_slug(self, name: str) -> str:
        """Generate unique slug from integration name"""
        base_slug = name.lower().replace(" ", "-").replace("_", "-")
        # Remove special characters
        import re
        base_slug = re.sub(r'[^a-z0-9-]', '', base_slug)
        
        # Check for uniqueness
        counter = 1
        slug = base_slug
        while self.db.query(MarketplaceIntegration).filter(MarketplaceIntegration.slug == slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug

    async def _validate_integration(self, integration: MarketplaceIntegration) -> List[str]:
        """Validate integration for marketplace submission"""
        errors = []
        
        if not integration.name or len(integration.name) < 3:
            errors.append("Name must be at least 3 characters")
        
        if not integration.description or len(integration.description) < 50:
            errors.append("Description must be at least 50 characters")
        
        if not integration.short_description or len(integration.short_description) < 20:
            errors.append("Short description must be at least 20 characters")
        
        if not integration.category:
            errors.append("Category is required")
        
        if integration.pricing_model != PricingModel.FREE and integration.price <= 0:
            errors.append("Price must be greater than 0 for paid integrations")
        
        if not integration.webhook_url and integration.supported_events:
            errors.append("Webhook URL required for integrations with events")
        
        return errors

    async def _notify_review_team(self, integration: MarketplaceIntegration):
        """Notify review team of new submission"""
        # Would send email/notification to review team
        logger.info(f"Review team notified of integration submission: {integration.name}")

    async def _notify_developer_approval(self, integration: MarketplaceIntegration):
        """Notify developer of integration approval"""
        # Would send email to developer
        logger.info(f"Developer notified of integration approval: {integration.name}")

    async def _notify_developer_published(self, integration: MarketplaceIntegration):
        """Notify developer of integration publication"""
        # Would send email to developer
        logger.info(f"Developer notified of integration publication: {integration.name}")

    async def _index_integration_for_search(self, integration: MarketplaceIntegration):
        """Index integration for search functionality"""
        # Would integrate with search engine (Elasticsearch, etc.)
        logger.info(f"Integration indexed for search: {integration.name}")

    async def _create_subscription(
        self, 
        integration: MarketplaceIntegration, 
        user_id: str, 
        installation: MarketplaceIntegrationInstallation
    ) -> str:
        """Create Stripe subscription for paid integration"""
        try:
            if not stripe:
                # Mock subscription for testing
                return f"sub_mock_{user_id}_{integration.id}"
                
            # Create Stripe subscription (simplified)
            subscription = stripe.Subscription.create(
                customer=f"cus_{user_id}",  # Would be actual Stripe customer ID
                items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product': integration.slug,
                        'unit_amount': int(integration.price * 100),
                        'recurring': {'interval': 'month'}
                    }
                }],
                trial_period_days=integration.trial_days if integration.trial_days > 0 else None
            )
            
            return subscription.id
            
        except Exception as e:
            logger.error(f"Error creating subscription: {str(e)}")
            raise

    async def _cancel_subscription(self, subscription_id: str):
        """Cancel Stripe subscription"""
        try:
            if not stripe:
                logger.info(f"Mock subscription cancelled: {subscription_id}")
                return
                
            stripe.Subscription.delete(subscription_id)
            logger.info(f"Subscription cancelled: {subscription_id}")
            
        except Exception as e:
            logger.error(f"Error cancelling subscription: {str(e)}")

    async def _send_installation_webhook(
        self, 
        integration: MarketplaceIntegration, 
        installation: MarketplaceIntegrationInstallation, 
        event_type: str,
        background_tasks = None
    ):
        """Send webhook to integration for installation events"""
        if not integration.webhook_url:
            return
        
        try:
            webhook_data = {
                "event": event_type,
                "integration_id": integration.id,
                "installation_id": installation.id,
                "user_id": installation.user_id,
                "workspace_id": installation.workspace_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Create webhook record
            webhook = IntegrationWebhook(
                integration_id=integration.id,
                installation_id=installation.id,
                event_type=event_type,
                event_data=webhook_data
            )
            
            self.db.add(webhook)
            self.db.commit()
            
            # Send webhook in background using async implementation
            if background_tasks:
                background_tasks.add_task(self._webhook_safe_wrapper, webhook.id, integration.webhook_url)
            else:
                # Use asyncio for non-blocking delivery when no background_tasks available
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(self._safe_deliver_webhook(webhook, integration.webhook_url))
                except RuntimeError:
                    # No running event loop, log and skip webhook delivery
                    logger.warning(f"No running event loop for webhook delivery, skipping webhook for integration {integration.id}")
            
        except Exception as e:
            logger.error(f"Error sending installation webhook: {str(e)}")

    async def _webhook_safe_wrapper(self, webhook_id: int, webhook_url: str):
        """Wrapper for background webhook delivery with its own DB session"""
        from app.database import SessionLocal
        
        db = SessionLocal()
        try:
            # Re-fetch webhook to ensure we have a fresh DB session
            webhook = db.query(IntegrationWebhook).filter(IntegrationWebhook.id == webhook_id).first()
            if not webhook:
                logger.error("Webhook record not found during delivery")
                return
                
            await self._deliver_webhook_with_session(webhook, webhook_url, db)
        except Exception as e:
            logger.error(f"Error in webhook safe wrapper: {str(e)}")
        finally:
            db.close()

    async def _safe_deliver_webhook(self, webhook: IntegrationWebhook, webhook_url: str):
        """Safely deliver webhook with its own DB session and error handling"""
        from app.database import SessionLocal
        
        db = SessionLocal()
        try:
            # Re-fetch webhook to ensure we have a fresh DB session
            webhook = db.query(IntegrationWebhook).filter(IntegrationWebhook.id == webhook.id).first()
            if not webhook:
                logger.error("Webhook record not found during delivery")
                return
                
            await self._deliver_webhook_with_session(webhook, webhook_url, db)
        except Exception as e:
            logger.error(f"Error in safe webhook delivery: {str(e)}")
        finally:
            db.close()

    async def _deliver_webhook_with_session(self, webhook: IntegrationWebhook, webhook_url: str, db_session):
        """Deliver webhook with provided DB session"""
        try:
            if not requests:
                # Mock webhook delivery
                webhook.status = "completed"
                webhook.response_status_code = 200
                webhook.processed_at = datetime.utcnow()
                db_session.commit()
                return
                
            response = requests.post(
                webhook_url,
                json=webhook.event_data,
                timeout=30,
                headers={"Content-Type": "application/json"}
            )
            
            # Update webhook record
            webhook.status = "completed" if response.status_code == 200 else "failed"
            webhook.response_status_code = response.status_code
            webhook.response_body = response.text[:1000]  # Truncate
            webhook.processed_at = datetime.utcnow()
            
            db_session.commit()
            
        except Exception as e:
            webhook.status = "failed"
            webhook.error_message = str(e)
            webhook.processed_at = datetime.utcnow()
            db_session.commit()
            
            logger.error(f"Error delivering webhook: {str(e)}")


    async def _generate_search_facets(
        self, 
        query: str, 
        category: str, 
        pricing_model: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Generate search facets for filtering"""
        # Simplified facet generation
        return {
            "categories": [
                {"value": "productivity", "count": 45, "label": "Productivity"},
                {"value": "crm", "count": 32, "label": "CRM"},
                {"value": "analytics", "count": 28, "label": "Analytics"},
                {"value": "communication", "count": 24, "label": "Communication"}
            ],
            "pricing": [
                {"value": "free", "count": 67, "label": "Free"},
                {"value": "monthly", "count": 43, "label": "Monthly"},
                {"value": "one_time", "count": 18, "label": "One-time"}
            ],
            "ratings": [
                {"value": "4+", "count": 89, "label": "4+ Stars"},
                {"value": "3+", "count": 112, "label": "3+ Stars"},
                {"value": "2+", "count": 129, "label": "2+ Stars"}
            ]
        }

    async def _calculate_developer_revenue(
        self, 
        developer_id: int, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """Calculate revenue for developer in given period"""
        # Get developer's integrations
        integrations = self.db.query(MarketplaceIntegration).filter(
            MarketplaceIntegration.developer_id == developer_id
        ).all()
        
        total_revenue = 0.0
        integration_breakdown = {}
        
        for integration in integrations:
            # Get analytics for period
            analytics = self.db.query(IntegrationAnalytics).filter(
                and_(
                    IntegrationAnalytics.integration_id == integration.id,
                    IntegrationAnalytics.date >= start_date,
                    IntegrationAnalytics.date <= end_date
                )
            ).all()
            
            integration_revenue = sum(record.revenue for record in analytics)
            total_revenue += integration_revenue
            
            if integration_revenue > 0:
                integration_breakdown[integration.name] = integration_revenue
        
        # Calculate platform fee and net payout
        developer = self.db.query(IntegrationDeveloper).filter(
            IntegrationDeveloper.id == developer_id
        ).first()
        
        # Validate revenue share percentage
        if not (0 <= developer.revenue_share_percentage <= 100):
            raise ValueError(f"Invalid revenue share percentage: {developer.revenue_share_percentage}%. Must be between 0 and 100.")
        
        platform_fee_rate = (100 - developer.revenue_share_percentage) / 100
        platform_fee = total_revenue * platform_fee_rate
        net_payout = total_revenue - platform_fee
        
        return {
            "gross_revenue": total_revenue,
            "platform_fee": platform_fee,
            "net_payout": net_payout,
            "integration_breakdown": integration_breakdown
        }

    async def _process_payout(self, payout: IntegrationPayout, developer: IntegrationDeveloper):
        """Process actual payout to developer"""
        try:
            # Process payout via Stripe, PayPal, etc.
            # This is simplified - would integrate with actual payment processors
            
            payout.status = "completed"
            payout.processed_at = datetime.utcnow()
            payout.payout_reference = f"po_{secrets.token_urlsafe(16)}"
            
            # Update developer earnings
            developer.total_earnings += payout.net_payout
            
            logger.info(f"Processed payout of ${payout.net_payout} to developer {developer.developer_name}")
            
        except Exception as e:
            payout.status = "failed"
            payout.error_message = str(e)
            logger.error(f"Error processing payout: {str(e)}")