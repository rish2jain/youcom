"""
GDPR Compliance Service - Week 2 Implementation
Data protection, privacy rights, and compliance features.
"""

import json
import logging
import zipfile
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from io import BytesIO
import uuid

from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.impact_card import ImpactCard
from app.models.company_research import CompanyResearch
from app.models.integration import IntegrationInstallation, IntegrationUsageLog

logger = logging.getLogger(__name__)

class GDPRError(Exception):
    """GDPR compliance error"""
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message)
        self.error_code = error_code

class DataExportRequest:
    """Data export request tracking"""
    def __init__(self, user_id: str, request_type: str):
        self.id = str(uuid.uuid4())
        self.user_id = user_id
        self.request_type = request_type
        self.status = "pending"
        self.created_at = datetime.utcnow()
        self.completed_at = None
        self.download_url = None
        self.expires_at = datetime.utcnow() + timedelta(days=30)

class DataDeletionRequest:
    """Data deletion request tracking"""
    def __init__(self, user_id: str, deletion_type: str):
        self.id = str(uuid.uuid4())
        self.user_id = user_id
        self.deletion_type = deletion_type
        self.status = "pending"
        self.created_at = datetime.utcnow()
        self.completed_at = None
        self.verification_required = True

class GDPRService:
    """GDPR compliance service"""
    
    def __init__(self):
        self.export_requests = {}  # In production, use database
        self.deletion_requests = {}  # In production, use database
        
        # Data retention policies (in days)
        self.retention_policies = {
            "impact_cards": 365 * 2,  # 2 years
            "company_research": 365 * 2,  # 2 years
            "usage_logs": 365 * 1,  # 1 year
            "api_logs": 90,  # 3 months
            "user_sessions": 30,  # 30 days
        }
        
        # Personal data categories
        self.personal_data_categories = {
            "identity": ["email", "full_name", "sso_id"],
            "usage": ["api_calls", "login_history", "preferences"],
            "content": ["impact_cards", "research_reports", "watchlists"],
            "integrations": ["installations", "configurations", "usage_logs"]
        }
    
    async def request_data_export(
        self,
        user_id: str,
        export_type: str = "complete",
        categories: Optional[List[str]] = None
    ) -> DataExportRequest:
        """Request user data export (GDPR Article 15)"""
        logger.info(f"📤 Data export requested by user {user_id}")
        
        try:
            # Create export request
            request = DataExportRequest(user_id, export_type)
            self.export_requests[request.id] = request
            
            # Start export process asynchronously
            import asyncio
            asyncio.create_task(self._process_data_export(request, categories))
            
            logger.info(f"✅ Data export request created: {request.id}")
            return request
        
        except Exception as e:
            logger.error(f"❌ Data export request failed: {str(e)}")
            raise GDPRError(f"Failed to create export request: {str(e)}")
    
    async def request_data_deletion(
        self,
        user_id: str,
        deletion_type: str = "complete",
        verification_token: Optional[str] = None
    ) -> DataDeletionRequest:
        """Request user data deletion (GDPR Article 17)"""
        logger.info(f"🗑️ Data deletion requested by user {user_id}")
        
        try:
            # Create deletion request
            request = DataDeletionRequest(user_id, deletion_type)
            self.deletion_requests[request.id] = request
            
            # If verification token provided, verify immediately
            if verification_token:
                await self._verify_deletion_request(request.id, verification_token)
            else:
                # Send verification email
                await self._send_deletion_verification_email(user_id, request.id)
            
            logger.info(f"✅ Data deletion request created: {request.id}")
            return request
        
        except Exception as e:
            logger.error(f"❌ Data deletion request failed: {str(e)}")
            raise GDPRError(f"Failed to create deletion request: {str(e)}")
    
    async def get_user_data_summary(self, user_id: str) -> Dict[str, Any]:
        """Get summary of user's personal data"""
        logger.info(f"📊 Data summary requested for user {user_id}")
        
        try:
            async with AsyncSessionLocal() as session:
                # Get user data
                user_result = await session.execute(
                    select(User).where(User.id == user_id)
                )
                user = user_result.scalar_one_or_none()
                
                if not user:
                    raise GDPRError("User not found")
                
                # Count various data types
                impact_cards_result = await session.execute(
                    select(ImpactCard).where(ImpactCard.user_id == user_id)
                )
                impact_cards_count = len(impact_cards_result.scalars().all())
                
                research_result = await session.execute(
                    select(CompanyResearch).where(CompanyResearch.user_id == user_id)
                )
                research_count = len(research_result.scalars().all())
                
                integrations_result = await session.execute(
                    select(IntegrationInstallation).where(IntegrationInstallation.user_id == user_id)
                )
                integrations_count = len(integrations_result.scalars().all())
                
                # Calculate data age
                account_age = (datetime.utcnow() - user.created_at).days if user.created_at else 0
                
                return {
                    "user_id": str(user_id),
                    "account_created": user.created_at.isoformat() if user.created_at else None,
                    "account_age_days": account_age,
                    "data_summary": {
                        "identity_data": {
                            "email": bool(user.email),
                            "full_name": bool(user.full_name),
                            "sso_provider": bool(user.sso_provider)
                        },
                        "content_data": {
                            "impact_cards": impact_cards_count,
                            "research_reports": research_count,
                            "integrations": integrations_count
                        }
                    },
                    "retention_policies": self.retention_policies,
                    "rights_available": [
                        "data_export",
                        "data_deletion",
                        "data_portability",
                        "rectification",
                        "restriction_of_processing"
                    ]
                }
        
        except Exception as e:
            logger.error(f"❌ Data summary failed: {str(e)}")
            raise GDPRError(f"Failed to get data summary: {str(e)}")
    
    async def update_consent_preferences(
        self,
        user_id: str,
        consent_data: Dict[str, bool]
    ) -> Dict[str, Any]:
        """Update user consent preferences"""
        logger.info(f"✅ Consent preferences updated for user {user_id}")
        
        try:
            async with AsyncSessionLocal() as session:
                # Update user consent preferences
                await session.execute(
                    update(User)
                    .where(User.id == user_id)
                    .values(
                        consent_marketing=consent_data.get("marketing", False),
                        consent_analytics=consent_data.get("analytics", False),
                        consent_integrations=consent_data.get("integrations", False),
                        updated_at=datetime.utcnow()
                    )
                )
                await session.commit()
                
                return {
                    "status": "updated",
                    "user_id": str(user_id),
                    "consent_preferences": consent_data,
                    "updated_at": datetime.utcnow().isoformat()
                }
        
        except Exception as e:
            logger.error(f"❌ Consent update failed: {str(e)}")
            raise GDPRError(f"Failed to update consent: {str(e)}")
    
    async def get_processing_activities(self, user_id: str) -> List[Dict[str, Any]]:
        """Get list of data processing activities for user"""
        logger.info(f"📋 Processing activities requested for user {user_id}")
        
        try:
            # Define processing activities
            activities = [
                {
                    "activity": "Competitive Intelligence Analysis",
                    "purpose": "Provide competitive intelligence services",
                    "legal_basis": "Legitimate Interest",
                    "data_categories": ["usage_data", "content_data"],
                    "retention_period": "2 years",
                    "third_parties": ["You.com APIs"]
                },
                {
                    "activity": "User Account Management",
                    "purpose": "Manage user accounts and authentication",
                    "legal_basis": "Contract Performance",
                    "data_categories": ["identity_data", "authentication_data"],
                    "retention_period": "Account lifetime + 30 days",
                    "third_parties": ["SSO Providers (Google, Azure, Okta)"]
                },
                {
                    "activity": "Service Analytics",
                    "purpose": "Improve service performance and user experience",
                    "legal_basis": "Legitimate Interest",
                    "data_categories": ["usage_data", "performance_data"],
                    "retention_period": "1 year",
                    "third_parties": ["None"]
                },
                {
                    "activity": "Integration Services",
                    "purpose": "Provide third-party integrations",
                    "legal_basis": "Consent",
                    "data_categories": ["integration_data", "usage_data"],
                    "retention_period": "Until consent withdrawn",
                    "third_parties": ["Integration Partners"]
                }
            ]
            
            return activities
        
        except Exception as e:
            logger.error(f"❌ Processing activities failed: {str(e)}")
            raise GDPRError(f"Failed to get processing activities: {str(e)}")
    
    async def verify_deletion_request(
        self,
        request_id: str,
        verification_token: str
    ) -> Dict[str, Any]:
        """Verify and process data deletion request"""
        logger.info(f"🔐 Verifying deletion request {request_id}")
        
        try:
            request = self.deletion_requests.get(request_id)
            if not request:
                raise GDPRError("Deletion request not found")
            
            # Verify token (simplified - in production, use secure tokens)
            if verification_token != f"verify_{request_id}":
                raise GDPRError("Invalid verification token")
            
            # Process deletion
            await self._process_data_deletion(request)
            
            return {
                "status": "verified_and_processed",
                "request_id": request_id,
                "completed_at": request.completed_at.isoformat()
            }
        
        except Exception as e:
            logger.error(f"❌ Deletion verification failed: {str(e)}")
            raise GDPRError(f"Failed to verify deletion: {str(e)}")
    
    async def get_export_status(self, request_id: str) -> Dict[str, Any]:
        """Get status of data export request"""
        request = self.export_requests.get(request_id)
        if not request:
            raise GDPRError("Export request not found")
        
        return {
            "request_id": request_id,
            "status": request.status,
            "created_at": request.created_at.isoformat(),
            "completed_at": request.completed_at.isoformat() if request.completed_at else None,
            "download_url": request.download_url,
            "expires_at": request.expires_at.isoformat()
        }
    
    async def get_deletion_status(self, request_id: str) -> Dict[str, Any]:
        """Get status of data deletion request"""
        request = self.deletion_requests.get(request_id)
        if not request:
            raise GDPRError("Deletion request not found")
        
        return {
            "request_id": request_id,
            "status": request.status,
            "created_at": request.created_at.isoformat(),
            "completed_at": request.completed_at.isoformat() if request.completed_at else None,
            "verification_required": request.verification_required
        }
    
    async def cleanup_expired_data(self) -> Dict[str, Any]:
        """Clean up expired data based on retention policies"""
        logger.info("🧹 Starting expired data cleanup")
        
        try:
            cleanup_results = {}
            
            async with AsyncSessionLocal() as session:
                # Clean up old impact cards
                impact_cutoff = datetime.utcnow() - timedelta(days=self.retention_policies["impact_cards"])
                impact_result = await session.execute(
                    delete(ImpactCard).where(ImpactCard.created_at < impact_cutoff)
                )
                cleanup_results["impact_cards"] = impact_result.rowcount
                
                # Clean up old research reports
                research_cutoff = datetime.utcnow() - timedelta(days=self.retention_policies["company_research"])
                research_result = await session.execute(
                    delete(CompanyResearch).where(CompanyResearch.created_at < research_cutoff)
                )
                cleanup_results["research_reports"] = research_result.rowcount
                
                # Clean up old usage logs
                usage_cutoff = datetime.utcnow() - timedelta(days=self.retention_policies["usage_logs"])
                usage_result = await session.execute(
                    delete(IntegrationUsageLog).where(IntegrationUsageLog.created_at < usage_cutoff)
                )
                cleanup_results["usage_logs"] = usage_result.rowcount
                
                await session.commit()
            
            logger.info(f"✅ Data cleanup completed: {cleanup_results}")
            return {
                "status": "completed",
                "cleanup_results": cleanup_results,
                "cleaned_at": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"❌ Data cleanup failed: {str(e)}")
            raise GDPRError(f"Failed to cleanup expired data: {str(e)}")
    
    # Private methods
    async def _process_data_export(
        self,
        request: DataExportRequest,
        categories: Optional[List[str]] = None
    ):
        """Process data export request"""
        try:
            request.status = "processing"
            
            # Collect user data
            user_data = await self._collect_user_data(request.user_id, categories)
            
            # Create export file
            export_file = await self._create_export_file(user_data)
            
            # Store export file (in production, use cloud storage)
            request.download_url = f"/api/gdpr/exports/{request.id}/download"
            request.status = "completed"
            request.completed_at = datetime.utcnow()
            
            logger.info(f"✅ Data export completed: {request.id}")
        
        except Exception as e:
            request.status = "failed"
            logger.error(f"❌ Data export failed: {str(e)}")
    
    async def _process_data_deletion(self, request: DataDeletionRequest):
        """Process data deletion request"""
        try:
            request.status = "processing"
            
            async with AsyncSessionLocal() as session:
                user_id = request.user_id
                
                # Delete user's impact cards
                await session.execute(
                    delete(ImpactCard).where(ImpactCard.user_id == user_id)
                )
                
                # Delete user's research reports
                await session.execute(
                    delete(CompanyResearch).where(CompanyResearch.user_id == user_id)
                )
                
                # Delete user's integrations
                await session.execute(
                    delete(IntegrationInstallation).where(IntegrationInstallation.user_id == user_id)
                )
                
                # Anonymize or delete user record
                if request.deletion_type == "complete":
                    await session.execute(
                        delete(User).where(User.id == user_id)
                    )
                else:
                    # Anonymize user data
                    await session.execute(
                        update(User)
                        .where(User.id == user_id)
                        .values(
                            email=f"deleted_{user_id}@example.com",
                            full_name="Deleted User",
                            sso_id=None,
                            sso_provider=None,
                            is_active=False
                        )
                    )
                
                await session.commit()
            
            request.status = "completed"
            request.completed_at = datetime.utcnow()
            
            logger.info(f"✅ Data deletion completed: {request.id}")
        
        except Exception as e:
            request.status = "failed"
            logger.error(f"❌ Data deletion failed: {str(e)}")
    
    async def _collect_user_data(
        self,
        user_id: str,
        categories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Collect all user data for export"""
        
        async with AsyncSessionLocal() as session:
            # Get user data
            user_result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = user_result.scalar_one_or_none()
            
            if not user:
                raise GDPRError("User not found")
            
            # Collect data by category
            data = {
                "export_info": {
                    "user_id": str(user_id),
                    "export_date": datetime.utcnow().isoformat(),
                    "categories": categories or ["all"]
                },
                "identity_data": {
                    "email": user.email,
                    "full_name": user.full_name,
                    "sso_provider": user.sso_provider,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "last_login": user.last_login.isoformat() if user.last_login else None
                }
            }
            
            # Get impact cards
            impact_cards_result = await session.execute(
                select(ImpactCard).where(ImpactCard.user_id == user_id)
            )
            impact_cards = impact_cards_result.scalars().all()
            data["impact_cards"] = [
                {
                    "id": str(card.id),
                    "competitor_name": card.competitor_name,
                    "risk_score": card.risk_score,
                    "created_at": card.created_at.isoformat() if card.created_at else None
                }
                for card in impact_cards
            ]
            
            # Get research reports
            research_result = await session.execute(
                select(CompanyResearch).where(CompanyResearch.user_id == user_id)
            )
            research_reports = research_result.scalars().all()
            data["research_reports"] = [
                {
                    "id": str(report.id),
                    "company_name": report.company_name,
                    "total_sources": report.total_sources,
                    "created_at": report.created_at.isoformat() if report.created_at else None
                }
                for report in research_reports
            ]
            
            # Get integrations
            integrations_result = await session.execute(
                select(IntegrationInstallation).where(IntegrationInstallation.user_id == user_id)
            )
            integrations = integrations_result.scalars().all()
            data["integrations"] = [
                {
                    "id": str(integration.id),
                    "integration_id": str(integration.integration_id),
                    "installed_at": integration.installed_at.isoformat() if integration.installed_at else None,
                    "usage_count": integration.usage_count
                }
                for integration in integrations
            ]
            
            return data
    
    async def _create_export_file(self, user_data: Dict[str, Any]) -> BytesIO:
        """Create export file (JSON + ZIP)"""
        
        # Create JSON file
        json_data = json.dumps(user_data, indent=2, ensure_ascii=False)
        
        # Create ZIP file
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr("user_data.json", json_data)
            zip_file.writestr("README.txt", self._create_export_readme())
        
        zip_buffer.seek(0)
        return zip_buffer
    
    def _create_export_readme(self) -> str:
        """Create README for data export"""
        return """
Enterprise CIA - Personal Data Export

This archive contains all your personal data stored in Enterprise CIA.

Files included:
- user_data.json: Complete data export in JSON format

Data categories:
- Identity data: Email, name, authentication information
- Impact cards: Competitive intelligence reports you've generated
- Research reports: Company research reports you've created
- Integrations: Third-party integrations you've installed

For questions about this export or your data rights, contact:
privacy@enterprisecia.com

Generated: {date}
        """.format(date=datetime.utcnow().isoformat())
    
    async def _send_deletion_verification_email(self, user_id: str, request_id: str):
        """Send deletion verification email"""
        # In production, implement actual email sending
        logger.info(f"📧 Deletion verification email sent for request {request_id}")
        
        # For demo, just log the verification token
        verification_token = f"verify_{request_id}"
        logger.info(f"🔐 Verification token: {verification_token}")
    
    async def _verify_deletion_request(self, request_id: str, verification_token: str):
        """Verify deletion request with token"""
        request = self.deletion_requests.get(request_id)
        if not request:
            raise GDPRError("Deletion request not found")
        
        # Verify token
        if verification_token == f"verify_{request_id}":
            request.verification_required = False
            await self._process_data_deletion(request)
        else:
            raise GDPRError("Invalid verification token")

# Global GDPR service instance
gdpr_service = GDPRService()