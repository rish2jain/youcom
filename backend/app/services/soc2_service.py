"""
SOC 2 Compliance Service - Week 2 Implementation
Security controls, audit trails, and compliance monitoring.
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from enum import Enum
import uuid
import hashlib

from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.database import Base, AsyncSessionLocal
from app.config import settings
from app.models.audit_log import AuditLog, AuditAction

logger = logging.getLogger(__name__)

class AuditEventType(Enum):
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    DATA_DELETION = "data_deletion"
    SYSTEM_CONFIGURATION = "system_configuration"
    SECURITY_EVENT = "security_event"
    API_ACCESS = "api_access"
    INTEGRATION_ACCESS = "integration_access"
    ADMIN_ACTION = "admin_action"

class SecurityControlStatus(Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    NEEDS_REVIEW = "needs_review"
    NOT_APPLICABLE = "not_applicable"

class SOC2AuditLog(Base):
    """Immutable audit log entries for SOC 2 compliance"""
    __tablename__ = "soc2_audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(50), nullable=False)
    user_id = Column(UUID(as_uuid=True))
    resource_type = Column(String(100))
    resource_id = Column(String(255))
    action = Column(String(100), nullable=False)
    details = Column(JSONB)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    success = Column(Boolean, default=True)
    risk_level = Column(String(20), default="low")
    
    # Immutability controls
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    checksum = Column(String(64))  # SHA-256 hash for integrity
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Generate checksum for integrity verification
        self.checksum = self._generate_checksum()
    
    def _generate_checksum(self) -> str:
        """Generate SHA-256 checksum for audit log integrity"""
        data = {
            "event_type": self.event_type,
            "user_id": str(self.user_id) if self.user_id else None,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "action": self.action,
            "details": self.details,
            "ip_address": self.ip_address,
            "success": self.success,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
        
        json_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode()).hexdigest()

class SecurityControl(Base):
    """SOC 2 security controls tracking"""
    __tablename__ = "security_controls"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    control_id = Column(String(50), unique=True, nullable=False)
    control_name = Column(String(255), nullable=False)
    control_description = Column(Text)
    soc2_category = Column(String(50))  # Security, Availability, Processing Integrity, etc.
    status = Column(String(50), default=SecurityControlStatus.NEEDS_REVIEW.value)
    
    # Implementation details
    implementation_details = Column(Text)
    evidence_location = Column(String(500))
    responsible_party = Column(String(255))
    review_frequency = Column(String(50))  # daily, weekly, monthly, quarterly, annually
    
    # Compliance tracking
    last_reviewed_at = Column(DateTime)
    last_tested_at = Column(DateTime)
    next_review_due = Column(DateTime)
    compliance_notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class SOC2Service:
    """SOC 2 compliance service"""
    
    def __init__(self):
        self.trust_service_criteria = {
            "security": "Information and systems are protected against unauthorized access",
            "availability": "Information and systems are available for operation and use",
            "processing_integrity": "System processing is complete, valid, accurate, timely, and authorized",
            "confidentiality": "Information designated as confidential is protected",
            "privacy": "Personal information is collected, used, retained, disclosed, and disposed of in conformity with commitments"
        }
        
        # Initialize security controls
        self.security_controls = self._initialize_security_controls()
    
    async def log_audit_event(
        self,
        event_type: AuditEventType,
        action: str,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        risk_level: str = "low"
    ) -> str:
        """Log audit event for SOC 2 compliance"""
        
        try:
            async with AsyncSessionLocal() as session:
                audit_entry = SOC2AuditLog(
                    event_type=event_type.value,
                    user_id=user_id,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    action=action,
                    details=details or {},
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=success,
                    risk_level=risk_level
                )
                
                session.add(audit_entry)
                await session.commit()
                await session.refresh(audit_entry)
                
                logger.info(f"📝 Audit event logged: {event_type.value} - {action}")
                return str(audit_entry.id)
        
        except Exception as e:
            logger.error(f"❌ Failed to log audit event: {str(e)}")
            # Don't raise exception to avoid breaking main functionality
            return ""
    
    async def get_audit_trail(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_type: Optional[str] = None,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Get audit trail for compliance reporting"""
        
        try:
            async with AsyncSessionLocal() as session:
                query = select(SOC2AuditLog)
                
                # Apply filters
                conditions = []
                if start_date:
                    conditions.append(SOC2AuditLog.created_at >= start_date)
                if end_date:
                    conditions.append(SOC2AuditLog.created_at <= end_date)
                if event_type:
                    conditions.append(SOC2AuditLog.event_type == event_type)
                if user_id:
                    conditions.append(SOC2AuditLog.user_id == user_id)
                if resource_type:
                    conditions.append(SOC2AuditLog.resource_type == resource_type)
                
                if conditions:
                    query = query.where(and_(*conditions))
                
                query = query.order_by(SOC2AuditLog.created_at.desc()).limit(limit)
                
                result = await session.execute(query)
                audit_logs = result.scalars().all()
                
                return [
                    {
                        "id": str(log.id),
                        "event_type": log.event_type,
                        "user_id": str(log.user_id) if log.user_id else None,
                        "resource_type": log.resource_type,
                        "resource_id": log.resource_id,
                        "action": log.action,
                        "details": log.details,
                        "ip_address": log.ip_address,
                        "success": log.success,
                        "risk_level": log.risk_level,
                        "created_at": log.created_at.isoformat(),
                        "checksum": log.checksum
                    }
                    for log in audit_logs
                ]
        
        except Exception as e:
            logger.error(f"❌ Failed to get audit trail: {str(e)}")
            return []
    
    async def verify_audit_integrity(
        self,
        audit_log_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Verify integrity of audit logs"""
        
        try:
            async with AsyncSessionLocal() as session:
                if audit_log_ids:
                    query = select(SOC2AuditLog).where(SOC2AuditLog.id.in_(audit_log_ids))
                else:
                    # Verify recent logs (last 1000)
                    query = select(SOC2AuditLog).order_by(SOC2AuditLog.created_at.desc()).limit(1000)
                
                result = await session.execute(query)
                audit_logs = result.scalars().all()
                
                verification_results = {
                    "total_logs": len(audit_logs),
                    "verified_logs": 0,
                    "corrupted_logs": 0,
                    "corrupted_log_ids": []
                }
                
                for log in audit_logs:
                    # Recalculate checksum
                    expected_checksum = log._generate_checksum()
                    
                    if log.checksum == expected_checksum:
                        verification_results["verified_logs"] += 1
                    else:
                        verification_results["corrupted_logs"] += 1
                        verification_results["corrupted_log_ids"].append(str(log.id))
                
                verification_results["integrity_percentage"] = (
                    verification_results["verified_logs"] / verification_results["total_logs"] * 100
                    if verification_results["total_logs"] > 0 else 100
                )
                
                return verification_results
        
        except Exception as e:
            logger.error(f"❌ Failed to verify audit integrity: {str(e)}")
            return {"error": str(e)}
    
    async def get_security_controls_status(self) -> Dict[str, Any]:
        """Get status of all security controls"""
        
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(select(SecurityControl))
                controls = result.scalars().all()
                
                status_summary = {
                    "total_controls": len(controls),
                    "compliant": 0,
                    "non_compliant": 0,
                    "needs_review": 0,
                    "not_applicable": 0,
                    "overdue_reviews": 0
                }
                
                control_details = []
                now = datetime.now(timezone.utc)
                
                for control in controls:
                    status_summary[control.status] += 1
                    
                    if control.next_review_due and control.next_review_due < now:
                        status_summary["overdue_reviews"] += 1
                    
                    control_details.append({
                        "control_id": control.control_id,
                        "control_name": control.control_name,
                        "soc2_category": control.soc2_category,
                        "status": control.status,
                        "last_reviewed_at": control.last_reviewed_at.isoformat() if control.last_reviewed_at else None,
                        "next_review_due": control.next_review_due.isoformat() if control.next_review_due else None,
                        "responsible_party": control.responsible_party,
                        "overdue": control.next_review_due < now if control.next_review_due else False
                    })
                
                compliance_percentage = (
                    status_summary["compliant"] / status_summary["total_controls"] * 100
                    if status_summary["total_controls"] > 0 else 0
                )
                
                return {
                    "summary": status_summary,
                    "compliance_percentage": compliance_percentage,
                    "controls": control_details,
                    "generated_at": now.isoformat()
                }
        
        except Exception as e:
            logger.error(f"❌ Failed to get security controls status: {str(e)}")
            return {"error": str(e)}
    
    async def update_security_control(
        self,
        control_id: str,
        status: SecurityControlStatus,
        implementation_details: Optional[str] = None,
        evidence_location: Optional[str] = None,
        compliance_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update security control status"""
        
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(SecurityControl).where(SecurityControl.control_id == control_id)
                )
                control = result.scalar_one_or_none()
                
                if not control:
                    raise ValueError(f"Security control {control_id} not found")
                
                # Update control
                control.status = status.value
                control.last_reviewed_at = datetime.now(timezone.utc)
                
                if implementation_details:
                    control.implementation_details = implementation_details
                if evidence_location:
                    control.evidence_location = evidence_location
                if compliance_notes:
                    control.compliance_notes = compliance_notes
                
                # Calculate next review date
                if control.review_frequency == "daily":
                    control.next_review_due = datetime.utcnow() + timedelta(days=1)
                elif control.review_frequency == "weekly":
                    control.next_review_due = datetime.utcnow() + timedelta(weeks=1)
                elif control.review_frequency == "monthly":
                    control.next_review_due = datetime.utcnow() + timedelta(days=30)
                elif control.review_frequency == "quarterly":
                    control.next_review_due = datetime.utcnow() + timedelta(days=90)
                elif control.review_frequency == "annually":
                    control.next_review_due = datetime.utcnow() + timedelta(days=365)
                
                await session.commit()
                
                # Log audit event
                await self.log_audit_event(
                    AuditEventType.SYSTEM_CONFIGURATION,
                    f"Updated security control {control_id}",
                    resource_type="security_control",
                    resource_id=control_id,
                    details={
                        "old_status": control.status,
                        "new_status": status.value,
                        "implementation_details": implementation_details,
                        "evidence_location": evidence_location
                    }
                )
                
                return {
                    "control_id": control_id,
                    "status": status.value,
                    "updated_at": datetime.utcnow().isoformat(),
                    "next_review_due": control.next_review_due.isoformat() if control.next_review_due else None
                }
        
        except Exception as e:
            logger.error(f"❌ Failed to update security control: {str(e)}")
            raise
    
    async def generate_compliance_report(
        self,
        report_type: str = "full",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Generate SOC 2 compliance report"""
        
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=90)  # Last 90 days
            if not end_date:
                end_date = datetime.utcnow()
            
            # Get security controls status
            controls_status = await self.get_security_controls_status()
            
            # Get audit trail summary
            audit_trail = await self.get_audit_trail(start_date, end_date, limit=10000)
            
            # Analyze audit events
            event_summary = {}
            risk_summary = {"low": 0, "medium": 0, "high": 0, "critical": 0}
            
            for event in audit_trail:
                event_type = event["event_type"]
                event_summary[event_type] = event_summary.get(event_type, 0) + 1
                
                risk_level = event.get("risk_level", "low")
                risk_summary[risk_level] = risk_summary.get(risk_level, 0) + 1
            
            # Verify audit integrity
            integrity_check = await self.verify_audit_integrity()
            
            report = {
                "report_info": {
                    "report_type": report_type,
                    "period_start": start_date.isoformat(),
                    "period_end": end_date.isoformat(),
                    "generated_at": datetime.utcnow().isoformat(),
                    "generated_by": "SOC2Service"
                },
                "executive_summary": {
                    "compliance_percentage": controls_status.get("compliance_percentage", 0),
                    "total_controls": controls_status.get("summary", {}).get("total_controls", 0),
                    "compliant_controls": controls_status.get("summary", {}).get("compliant", 0),
                    "non_compliant_controls": controls_status.get("summary", {}).get("non_compliant", 0),
                    "overdue_reviews": controls_status.get("summary", {}).get("overdue_reviews", 0),
                    "total_audit_events": len(audit_trail),
                    "audit_integrity": integrity_check.get("integrity_percentage", 0)
                },
                "security_controls": controls_status,
                "audit_summary": {
                    "total_events": len(audit_trail),
                    "event_types": event_summary,
                    "risk_levels": risk_summary,
                    "integrity_check": integrity_check
                },
                "trust_service_criteria": self.trust_service_criteria,
                "recommendations": self._generate_compliance_recommendations(controls_status, audit_trail)
            }
            
            return report
        
        except Exception as e:
            logger.error(f"❌ Failed to generate compliance report: {str(e)}")
            return {"error": str(e)}
    
    async def schedule_control_review(
        self,
        control_id: str,
        reviewer: str,
        review_date: datetime
    ) -> Dict[str, Any]:
        """Schedule security control review"""
        
        try:
            # Log audit event
            await self.log_audit_event(
                AuditEventType.ADMIN_ACTION,
                f"Scheduled review for security control {control_id}",
                resource_type="security_control",
                resource_id=control_id,
                details={
                    "reviewer": reviewer,
                    "scheduled_date": review_date.isoformat()
                }
            )
            
            return {
                "control_id": control_id,
                "reviewer": reviewer,
                "review_date": review_date.isoformat(),
                "status": "scheduled"
            }
        
        except Exception as e:
            logger.error(f"❌ Failed to schedule control review: {str(e)}")
            raise
    
    def _initialize_security_controls(self) -> List[Dict[str, Any]]:
        """Initialize standard SOC 2 security controls"""
        
        return [
            {
                "control_id": "CC1.1",
                "control_name": "Control Environment - Integrity and Ethical Values",
                "soc2_category": "security",
                "description": "The entity demonstrates a commitment to integrity and ethical values",
                "review_frequency": "annually"
            },
            {
                "control_id": "CC2.1",
                "control_name": "Communication and Information - Internal Communication",
                "soc2_category": "security",
                "description": "The entity obtains or generates and uses relevant, quality information",
                "review_frequency": "quarterly"
            },
            {
                "control_id": "CC3.1",
                "control_name": "Risk Assessment - Objectives",
                "soc2_category": "security",
                "description": "The entity specifies objectives with sufficient clarity",
                "review_frequency": "annually"
            },
            {
                "control_id": "CC6.1",
                "control_name": "Logical and Physical Access Controls - Access",
                "soc2_category": "security",
                "description": "The entity implements logical access security software",
                "review_frequency": "monthly"
            },
            {
                "control_id": "CC6.2",
                "control_name": "Logical and Physical Access Controls - Authentication",
                "soc2_category": "security",
                "description": "Prior to issuing system credentials, the entity registers users",
                "review_frequency": "monthly"
            },
            {
                "control_id": "CC7.1",
                "control_name": "System Operations - Data Backup",
                "soc2_category": "availability",
                "description": "The entity maintains data backup and recovery procedures",
                "review_frequency": "monthly"
            },
            {
                "control_id": "CC8.1",
                "control_name": "Change Management - Authorization",
                "soc2_category": "processing_integrity",
                "description": "The entity authorizes, designs, develops, configures, documents, tests, approves, and implements changes",
                "review_frequency": "quarterly"
            }
        ]
    
    def _generate_compliance_recommendations(
        self,
        controls_status: Dict[str, Any],
        audit_trail: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate compliance recommendations"""
        
        recommendations = []
        
        # Check compliance percentage
        compliance_pct = controls_status.get("compliance_percentage", 0)
        if compliance_pct < 90:
            recommendations.append("Improve overall compliance percentage to above 90%")
        
        # Check overdue reviews
        overdue_reviews = controls_status.get("summary", {}).get("overdue_reviews", 0)
        if overdue_reviews > 0:
            recommendations.append(f"Complete {overdue_reviews} overdue security control reviews")
        
        # Check non-compliant controls
        non_compliant = controls_status.get("summary", {}).get("non_compliant", 0)
        if non_compliant > 0:
            recommendations.append(f"Address {non_compliant} non-compliant security controls")
        
        # Check audit trail volume
        if len(audit_trail) < 100:
            recommendations.append("Increase audit logging coverage for better compliance visibility")
        
        # Check for high-risk events
        high_risk_events = sum(1 for event in audit_trail if event.get("risk_level") in ["high", "critical"])
        if high_risk_events > 0:
            recommendations.append(f"Review and address {high_risk_events} high-risk security events")
        
        if not recommendations:
            recommendations.append("All security controls are compliant - maintain current practices")
        
        return recommendations

# Global SOC 2 service instance
soc2_service = SOC2Service()