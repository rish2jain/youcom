"""
Compliance API Endpoints - Week 2 Implementation
GDPR, SOC 2, and enterprise compliance features.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.database import get_db
from app.services.gdpr_service import gdpr_service, GDPRError
from app.services.soc2_service import soc2_service, AuditEventType, SecurityControlStatus
from app.services.teams_service import TeamsService
from app.services.auth_service import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/compliance", tags=["Compliance"])

# Request/Response Models
class DataExportRequest(BaseModel):
    export_type: str = Field(default="complete", description="Type of export: complete, partial")
    categories: Optional[List[str]] = Field(default=None, description="Data categories to export")

class DataDeletionRequest(BaseModel):
    deletion_type: str = Field(default="complete", description="Type of deletion: complete, anonymize")
    verification_token: Optional[str] = Field(default=None, description="Verification token")

class ConsentUpdateRequest(BaseModel):
    marketing: bool = Field(default=False, description="Marketing communications consent")
    analytics: bool = Field(default=True, description="Analytics and performance consent")
    integrations: bool = Field(default=True, description="Third-party integrations consent")

class SecurityControlUpdateRequest(BaseModel):
    status: str = Field(..., description="Control status: compliant, non_compliant, needs_review")
    implementation_details: Optional[str] = Field(default=None, description="Implementation details")
    evidence_location: Optional[str] = Field(default=None, description="Evidence location")
    compliance_notes: Optional[str] = Field(default=None, description="Compliance notes")

class AuditTrailRequest(BaseModel):
    start_date: Optional[datetime] = Field(default=None, description="Start date for audit trail")
    end_date: Optional[datetime] = Field(default=None, description="End date for audit trail")
    event_type: Optional[str] = Field(default=None, description="Filter by event type")
    user_id: Optional[str] = Field(default=None, description="Filter by user ID")
    resource_type: Optional[str] = Field(default=None, description="Filter by resource type")
    limit: int = Field(default=1000, le=10000, description="Maximum number of results")

class TeamsIntegrationRequest(BaseModel):
    webhook_url: str = Field(..., description="Teams webhook URL")
    channel_name: str = Field(default="General", description="Teams channel name")

# GDPR Endpoints
@router.post("/gdpr/export")
async def request_data_export(
    request: DataExportRequest,
    current_user: User = Depends(get_current_user)
):
    """Request personal data export (GDPR Article 15)"""
    logger.info(f"📤 GDPR data export requested by {current_user.email}")
    
    try:
        export_request = await gdpr_service.request_data_export(
            user_id=str(current_user.id),
            export_type=request.export_type,
            categories=request.categories
        )
        
        return {
            "request_id": export_request.id,
            "status": export_request.status,
            "export_type": export_request.request_type,
            "created_at": export_request.created_at.isoformat(),
            "expires_at": export_request.expires_at.isoformat(),
            "message": "Data export request created. You will be notified when ready."
        }
        
    except GDPRError as e:
        logger.error(f"❌ GDPR export request failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ GDPR export error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create export request")

@router.get("/gdpr/export/{request_id}/status")
async def get_export_status(
    request_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get status of data export request"""
    logger.info(f"📊 Export status requested for {request_id}")
    
    try:
        status = await gdpr_service.get_export_status(request_id)
        return status
        
    except GDPRError as e:
        logger.error(f"❌ Export status failed: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/gdpr/export/{request_id}/download")
async def download_data_export(
    request_id: str,
    current_user: User = Depends(get_current_user)
):
    """Download personal data export"""
    logger.info(f"⬇️ Data export download requested for {request_id}")
    
    try:
        # In production, this would retrieve the actual export file
        # For demo, return a sample response
        export_data = {
            "message": "This would be your complete data export",
            "request_id": request_id,
            "user_id": str(current_user.id),
            "generated_at": datetime.utcnow().isoformat()
        }
        
        import json
        json_data = json.dumps(export_data, indent=2)
        
        return StreamingResponse(
            BytesIO(json_data.encode()),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=data_export_{request_id}.json"}
        )
        
    except Exception as e:
        logger.error(f"❌ Export download failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to download export")

@router.post("/gdpr/deletion")
async def request_data_deletion(
    request: DataDeletionRequest,
    current_user: User = Depends(get_current_user)
):
    """Request personal data deletion (GDPR Article 17)"""
    logger.info(f"🗑️ GDPR data deletion requested by {current_user.email}")
    
    try:
        deletion_request = await gdpr_service.request_data_deletion(
            user_id=str(current_user.id),
            deletion_type=request.deletion_type,
            verification_token=request.verification_token
        )
        
        return {
            "request_id": deletion_request.id,
            "status": deletion_request.status,
            "deletion_type": deletion_request.deletion_type,
            "verification_required": deletion_request.verification_required,
            "created_at": deletion_request.created_at.isoformat(),
            "message": "Data deletion request created. Verification email sent if required."
        }
        
    except GDPRError as e:
        logger.error(f"❌ GDPR deletion request failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/gdpr/deletion/{request_id}/verify")
async def verify_data_deletion(
    request_id: str,
    verification_token: str = Query(..., description="Verification token from email"),
    current_user: User = Depends(get_current_user)
):
    """Verify and process data deletion request"""
    logger.info(f"🔐 Deletion verification for request {request_id}")
    
    try:
        result = await gdpr_service.verify_deletion_request(request_id, verification_token)
        return result
        
    except GDPRError as e:
        logger.error(f"❌ Deletion verification failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/gdpr/data-summary")
async def get_data_summary(
    current_user: User = Depends(get_current_user)
):
    """Get summary of user's personal data"""
    logger.info(f"📊 Data summary requested by {current_user.email}")
    
    try:
        summary = await gdpr_service.get_user_data_summary(str(current_user.id))
        return summary
        
    except GDPRError as e:
        logger.error(f"❌ Data summary failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/gdpr/consent")
async def update_consent_preferences(
    request: ConsentUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    """Update user consent preferences"""
    logger.info(f"✅ Consent preferences updated by {current_user.email}")
    
    try:
        consent_data = {
            "marketing": request.marketing,
            "analytics": request.analytics,
            "integrations": request.integrations
        }
        
        result = await gdpr_service.update_consent_preferences(
            str(current_user.id),
            consent_data
        )
        
        return result
        
    except GDPRError as e:
        logger.error(f"❌ Consent update failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/gdpr/processing-activities")
async def get_processing_activities(
    current_user: User = Depends(get_current_user)
):
    """Get list of data processing activities"""
    logger.info(f"📋 Processing activities requested by {current_user.email}")
    
    try:
        activities = await gdpr_service.get_processing_activities(str(current_user.id))
        return {"processing_activities": activities}
        
    except GDPRError as e:
        logger.error(f"❌ Processing activities failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# SOC 2 Endpoints
@router.get("/soc2/audit-trail")
async def get_audit_trail(
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    event_type: Optional[str] = Query(None, description="Event type filter"),
    user_id: Optional[str] = Query(None, description="User ID filter"),
    resource_type: Optional[str] = Query(None, description="Resource type filter"),
    limit: int = Query(1000, le=10000, description="Maximum results"),
    current_user: User = Depends(get_current_user)
):
    """Get audit trail for compliance reporting"""
    logger.info(f"📝 Audit trail requested by {current_user.email}")
    
    # Check admin permissions
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        audit_trail = await soc2_service.get_audit_trail(
            start_date=start_date,
            end_date=end_date,
            event_type=event_type,
            user_id=user_id,
            resource_type=resource_type,
            limit=limit
        )
        
        return {
            "audit_trail": audit_trail,
            "total_events": len(audit_trail),
            "period_start": start_date.isoformat() if start_date else None,
            "period_end": end_date.isoformat() if end_date else None,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Audit trail failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get audit trail")

@router.get("/soc2/security-controls")
async def get_security_controls_status(
    current_user: User = Depends(get_current_user)
):
    """Get status of all security controls"""
    logger.info(f"🔒 Security controls status requested by {current_user.email}")
    
    # Check admin permissions
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        status = await soc2_service.get_security_controls_status()
        return status
        
    except Exception as e:
        logger.error(f"❌ Security controls status failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get security controls status")

@router.put("/soc2/security-controls/{control_id}")
async def update_security_control(
    control_id: str,
    request: SecurityControlUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    """Update security control status"""
    logger.info(f"🔧 Security control update: {control_id} by {current_user.email}")
    
    # Check admin permissions
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Validate status
        try:
            status = SecurityControlStatus(request.status)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Valid values: {[s.value for s in SecurityControlStatus]}"
            )
        
        result = await soc2_service.update_security_control(
            control_id=control_id,
            status=status,
            implementation_details=request.implementation_details,
            evidence_location=request.evidence_location,
            compliance_notes=request.compliance_notes
        )
        
        return result
        
    except ValueError as e:
        logger.error(f"❌ Security control update failed: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Security control update error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update security control")

@router.get("/soc2/compliance-report")
async def generate_compliance_report(
    report_type: str = Query("full", description="Report type: full, summary"),
    start_date: Optional[datetime] = Query(None, description="Report start date"),
    end_date: Optional[datetime] = Query(None, description="Report end date"),
    current_user: User = Depends(get_current_user)
):
    """Generate SOC 2 compliance report"""
    logger.info(f"📊 Compliance report requested by {current_user.email}")
    
    # Check admin permissions
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        report = await soc2_service.generate_compliance_report(
            report_type=report_type,
            start_date=start_date,
            end_date=end_date
        )
        
        return report
        
    except Exception as e:
        logger.error(f"❌ Compliance report failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate compliance report")

@router.post("/soc2/verify-audit-integrity")
async def verify_audit_integrity(
    audit_log_ids: Optional[List[str]] = None,
    current_user: User = Depends(get_current_user)
):
    """Verify integrity of audit logs"""
    logger.info(f"🔍 Audit integrity verification by {current_user.email}")
    
    # Check admin permissions
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        verification_result = await soc2_service.verify_audit_integrity(audit_log_ids)
        return verification_result
        
    except Exception as e:
        logger.error(f"❌ Audit integrity verification failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to verify audit integrity")

# Microsoft Teams Integration Endpoints
@router.post("/integrations/teams/register")
async def register_teams_webhook(
    request: TeamsIntegrationRequest,
    current_user: User = Depends(get_current_user)
):
    """Register Microsoft Teams webhook"""
    logger.info(f"🔗 Teams webhook registration by {current_user.email}")
    
    try:
        teams_service = TeamsService()
        
        # Use user's workspace ID (simplified - in production, get from context)
        workspace_id = str(current_user.id)  # Simplified mapping
        
        result = await teams_service.register_webhook(
            workspace_id=workspace_id,
            webhook_url=request.webhook_url,
            channel_name=request.channel_name
        )
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Teams webhook registration failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to register Teams webhook")

@router.post("/integrations/teams/test")
async def test_teams_integration(
    webhook_url: str = Query(..., description="Teams webhook URL to test"),
    current_user: User = Depends(get_current_user)
):
    """Test Microsoft Teams integration"""
    logger.info(f"🧪 Teams integration test by {current_user.email}")
    
    try:
        teams_service = TeamsService()
        
        # Send test impact card
        test_impact_card = {
            "competitor": "Test Company",
            "risk_score": 75,
            "risk_level": "high",
            "confidence_score": 85,
            "total_sources": 5,
            "generated_at": datetime.utcnow().isoformat(),
            "key_insights": [
                "This is a test impact card",
                "Teams integration is working correctly"
            ],
            "recommended_actions": [
                {"action": "Review test results", "priority": "medium"}
            ]
        }
        
        result = await teams_service.send_impact_card(
            team_id=None,
            channel_id=None,
            impact_card=test_impact_card,
            webhook_url=webhook_url
        )
        
        return {
            "status": "test_successful",
            "message": "Test impact card sent to Teams channel",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"❌ Teams integration test failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Teams integration test failed: {str(e)}")

# Data Retention and Cleanup
@router.post("/gdpr/cleanup-expired-data")
async def cleanup_expired_data(
    current_user: User = Depends(get_current_user)
):
    """Clean up expired data based on retention policies"""
    logger.info(f"🧹 Data cleanup requested by {current_user.email}")
    
    # Check admin permissions
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        result = await gdpr_service.cleanup_expired_data()
        return result
        
    except GDPRError as e:
        logger.error(f"❌ Data cleanup failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# Compliance Dashboard
@router.get("/dashboard")
async def get_compliance_dashboard(
    current_user: User = Depends(get_current_user)
):
    """Get compliance dashboard overview"""
    logger.info(f"📊 Compliance dashboard requested by {current_user.email}")
    
    # Check admin permissions
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Get SOC 2 status
        soc2_status = await soc2_service.get_security_controls_status()
        
        # Get recent audit events
        recent_audit = await soc2_service.get_audit_trail(
            start_date=datetime.utcnow() - timedelta(days=7),
            limit=100
        )
        
        # Get GDPR summary (simplified)
        gdpr_summary = {
            "active_export_requests": len([r for r in gdpr_service.export_requests.values() if r.status == "pending"]),
            "active_deletion_requests": len([r for r in gdpr_service.deletion_requests.values() if r.status == "pending"]),
            "retention_policies": gdpr_service.retention_policies
        }
        
        return {
            "soc2_compliance": {
                "compliance_percentage": soc2_status.get("compliance_percentage", 0),
                "total_controls": soc2_status.get("summary", {}).get("total_controls", 0),
                "overdue_reviews": soc2_status.get("summary", {}).get("overdue_reviews", 0)
            },
            "gdpr_status": gdpr_summary,
            "recent_activity": {
                "audit_events_7_days": len(recent_audit),
                "high_risk_events": len([e for e in recent_audit if e.get("risk_level") in ["high", "critical"]])
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Compliance dashboard failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get compliance dashboard")

# Health check
@router.get("/health")
async def compliance_health_check():
    """Compliance services health check"""
    return {
        "status": "healthy",
        "services": {
            "gdpr": "active",
            "soc2": "active",
            "teams_integration": "active"
        },
        "timestamp": datetime.utcnow().isoformat()
    }