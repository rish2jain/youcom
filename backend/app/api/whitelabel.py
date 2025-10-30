"""
White-label Solutions API

API endpoints for custom branding, on-premise deployment,
and enterprise white-label configurations.
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import logging

from app.database import get_db
from app.models.whitelabel import (
    WhiteLabelCustomer, BrandingConfiguration, DeploymentConfiguration,
    CustomIntegration, WhiteLabelUsage, SupportTicket
)
from app.services.whitelabel_service import WhiteLabelService
from app.services.auth_service import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/whitelabel", tags=["whitelabel"])

def verify_customer_access(customer_id: int, current_user: User, db: Session) -> WhiteLabelCustomer:
    """Verify user has access to customer and return customer object"""
    customer = db.query(WhiteLabelCustomer).filter(WhiteLabelCustomer.id == customer_id).first()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Check authorization - admin or customer owner
    is_admin = getattr(current_user, 'is_admin', False)
    if not is_admin and customer.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return customer


def get_whitelabel_service(db: Session = Depends(get_db)) -> WhiteLabelService:
    """Get white-label service instance"""
    return WhiteLabelService(db)


@router.post("/customers", response_model=Dict[str, Any])
async def create_whitelabel_customer(
    customer_data: Dict[str, Any],
    whitelabel_service: WhiteLabelService = Depends(get_whitelabel_service),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new white-label customer"""
    try:
        # Check if user has permission to create customers (admin only for now)
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required to create customers")
        
        # Validate required fields
        required_fields = [
            "customer_name", "customer_domain", "contact_email", 
            "contact_name", "monthly_fee", "contract_start_date", "contract_end_date"
        ]
        
        for field in required_fields:
            if field not in customer_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Convert date strings to datetime objects
        if isinstance(customer_data["contract_start_date"], str):
            customer_data["contract_start_date"] = datetime.fromisoformat(
                customer_data["contract_start_date"].replace("Z", "+00:00")
            )
        
        if isinstance(customer_data["contract_end_date"], str):
            customer_data["contract_end_date"] = datetime.fromisoformat(
                customer_data["contract_end_date"].replace("Z", "+00:00")
            )
        
        customer = await whitelabel_service.create_whitelabel_customer(customer_data)
        
        return {
            "id": customer.id,
            "customer_name": customer.customer_name,
            "customer_domain": customer.customer_domain,
            "subscription_tier": customer.subscription_tier,
            "deployment_type": customer.deployment_type,
            "status": customer.status,
            "created_at": customer.created_at.isoformat()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating white-label customer: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/customers", response_model=List[Dict[str, Any]])
async def list_whitelabel_customers(
    status: Optional[str] = Query(None),
    deployment_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List white-label customers"""
    try:
        query = db.query(WhiteLabelCustomer)
        
        # Scope results to current user - admin sees all, others see only their own
        is_admin = getattr(current_user, 'is_admin', False)
        if not is_admin:
            query = query.filter(WhiteLabelCustomer.owner_id == current_user.id)
        
        if status:
            query = query.filter(WhiteLabelCustomer.status == status)
        
        if deployment_type:
            query = query.filter(WhiteLabelCustomer.deployment_type == deployment_type)
        
        customers = query.order_by(WhiteLabelCustomer.created_at.desc())\
                        .offset(offset)\
                        .limit(limit)\
                        .all()
        
        return [
            {
                "id": customer.id,
                "customer_name": customer.customer_name,
                "customer_domain": customer.customer_domain,
                "subscription_tier": customer.subscription_tier,
                "deployment_type": customer.deployment_type,
                "status": customer.status,
                "monthly_fee": customer.monthly_fee,
                "max_users": customer.max_users,
                "created_at": customer.created_at.isoformat(),
                "contract_end_date": customer.contract_end_date.isoformat()
            }
            for customer in customers
        ]
        
    except Exception as e:
        logger.error(f"Error listing customers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/customers/{customer_id}", response_model=Dict[str, Any])
async def get_whitelabel_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific white-label customer"""
    try:
        # Verify access and get customer
        customer = verify_customer_access(customer_id, current_user, db)
        
        # Get related configurations
        branding = db.query(BrandingConfiguration).filter(
            BrandingConfiguration.customer_id == customer_id
        ).first()
        
        deployment = db.query(DeploymentConfiguration).filter(
            DeploymentConfiguration.customer_id == customer_id
        ).first()
        
        return {
            "id": customer.id,
            "customer_name": customer.customer_name,
            "customer_domain": customer.customer_domain,
            "contact_email": customer.contact_email,
            "contact_name": customer.contact_name,
            "subscription_tier": customer.subscription_tier,
            "deployment_type": customer.deployment_type,
            "status": customer.status,
            "monthly_fee": customer.monthly_fee,
            "max_users": customer.max_users,
            "max_api_calls_per_month": customer.max_api_calls_per_month,
            "features_enabled": customer.features_enabled,
            "support_level": customer.support_level,
            "contract_start_date": customer.contract_start_date.isoformat(),
            "contract_end_date": customer.contract_end_date.isoformat(),
            "created_at": customer.created_at.isoformat(),
            "branding": {
                "brand_name": branding.brand_name if branding else None,
                "primary_color": branding.primary_color if branding else None,
                "logo_url": branding.logo_url if branding else None,
                "status": branding.status if branding else None
            } if branding else None,
            "deployment": {
                "deployment_name": deployment.deployment_name if deployment else None,
                "deployment_status": deployment.deployment_status if deployment else None,
                "deployed_at": deployment.deployed_at.isoformat() if deployment and deployment.deployed_at else None,
                "health_check_url": deployment.health_check_url if deployment else None
            } if deployment else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting customer: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/customers/{customer_id}/branding", response_model=Dict[str, Any])
async def configure_customer_branding(
    customer_id: int,
    branding_data: Dict[str, Any],
    whitelabel_service: WhiteLabelService = Depends(get_whitelabel_service),
    current_user = Depends(get_current_user)
):
    """Configure custom branding for customer"""
    try:
        branding = await whitelabel_service.configure_branding(customer_id, branding_data)
        
        return {
            "id": branding.id,
            "customer_id": branding.customer_id,
            "brand_name": branding.brand_name,
            "brand_tagline": branding.brand_tagline,
            "primary_color": branding.primary_color,
            "secondary_color": branding.secondary_color,
            "accent_color": branding.accent_color,
            "logo_url": branding.logo_url,
            "custom_domain": branding.custom_domain,
            "status": branding.status,
            "version": branding.version,
            "updated_at": branding.updated_at.isoformat()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error configuring branding: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/customers/{customer_id}/branding", response_model=Dict[str, Any])
async def get_customer_branding(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get customer branding configuration"""
    try:
        branding = db.query(BrandingConfiguration).filter(
            BrandingConfiguration.customer_id == customer_id
        ).first()
        
        if not branding:
            raise HTTPException(status_code=404, detail="Branding configuration not found")
        
        return {
            "id": branding.id,
            "customer_id": branding.customer_id,
            "brand_name": branding.brand_name,
            "brand_tagline": branding.brand_tagline,
            "primary_color": branding.primary_color,
            "secondary_color": branding.secondary_color,
            "accent_color": branding.accent_color,
            "background_color": branding.background_color,
            "text_color": branding.text_color,
            "primary_font": branding.primary_font,
            "secondary_font": branding.secondary_font,
            "logo_url": branding.logo_url,
            "logo_dark_url": branding.logo_dark_url,
            "favicon_url": branding.favicon_url,
            "custom_domain": branding.custom_domain,
            "custom_css": branding.custom_css,
            "status": branding.status,
            "version": branding.version,
            "created_at": branding.created_at.isoformat(),
            "updated_at": branding.updated_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting branding: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/customers/{customer_id}/deploy", response_model=Dict[str, Any])
async def deploy_customer_instance(
    customer_id: int,
    background_tasks: BackgroundTasks,
    deployment_config: Optional[Dict[str, Any]] = None,
    whitelabel_service: WhiteLabelService = Depends(get_whitelabel_service),
    current_user = Depends(get_current_user)
):
    """Deploy customer instance"""
    try:
        # Start deployment in background
        background_tasks.add_task(
            whitelabel_service.deploy_customer_instance,
            customer_id,
            deployment_config
        )
        
        return {
            "message": "Deployment started",
            "customer_id": customer_id,
            "status": "in_progress",
            "started_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error starting deployment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/customers/{customer_id}/deployment", response_model=Dict[str, Any])
async def get_deployment_status(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get deployment status for customer"""
    try:
        deployment = db.query(DeploymentConfiguration).filter(
            DeploymentConfiguration.customer_id == customer_id
        ).first()
        
        if not deployment:
            raise HTTPException(status_code=404, detail="Deployment configuration not found")
        
        return {
            "id": deployment.id,
            "customer_id": deployment.customer_id,
            "deployment_name": deployment.deployment_name,
            "deployment_type": deployment.deployment_type,
            "deployment_status": deployment.deployment_status,
            "environment": deployment.environment,
            "deployed_version": deployment.deployed_version,
            "health_check_url": deployment.health_check_url,
            "uptime_percentage": deployment.uptime_percentage,
            "created_at": deployment.created_at.isoformat(),
            "deployed_at": deployment.deployed_at.isoformat() if deployment.deployed_at else None,
            "last_health_check": deployment.last_health_check.isoformat() if deployment.last_health_check else None,
            "deployment_notes": deployment.deployment_notes
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting deployment status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/customers/{customer_id}/deployment-package")
async def generate_deployment_package(
    customer_id: int,
    whitelabel_service: WhiteLabelService = Depends(get_whitelabel_service),
    current_user = Depends(get_current_user)
):
    """Generate deployment package for on-premise installation"""
    try:
        package_info = await whitelabel_service.generate_deployment_package(customer_id)
        
        return {
            "package_generated": True,
            "package_size": package_info["package_size"],
            "generated_at": package_info["generated_at"],
            "customer_domain": package_info["customer_domain"],
            "deployment_type": package_info["deployment_type"],
            "download_url": f"/api/whitelabel/customers/{customer_id}/download-package"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating deployment package: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/customers/{customer_id}/download-package")
async def download_deployment_package(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download deployment package"""
    import re
    
    try:
        # Verify customer access
        customer = verify_customer_access(customer_id, current_user, db)
        
        # Sanitize and validate customer domain
        domain = customer.customer_domain
        if not re.match(r'^[a-zA-Z0-9.-]+$', domain) or '..' in domain or '/' in domain:
            logger.error(f"Invalid customer domain for download: {domain}")
            raise HTTPException(status_code=400, detail="Invalid customer domain")
        
        # Get configurable base directory
        base_dir = os.getenv("DEPLOYMENT_PACKAGE_DIR", "/tmp/deployment_packages")
        package_path = os.path.join(base_dir, f"{domain}.tar.gz")
        
        # Verify the resolved path is within base directory
        abs_package_path = os.path.abspath(package_path)
        abs_base_dir = os.path.abspath(base_dir)
        if not abs_package_path.startswith(abs_base_dir):
            logger.error(f"Path traversal attempt: {package_path}")
            raise HTTPException(status_code=400, detail="Invalid package path")
        
        if not os.path.exists(package_path):
            raise HTTPException(status_code=404, detail="Deployment package not found")
        
        return FileResponse(
            package_path,
            media_type="application/gzip",
            filename=f"{domain}-deployment.tar.gz"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading package: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/customers/{customer_id}/health", response_model=Dict[str, Any])
async def check_deployment_health(
    customer_id: int,
    whitelabel_service: WhiteLabelService = Depends(get_whitelabel_service),
    current_user = Depends(get_current_user)
):
    """Check health of customer deployment"""
    try:
        health_status = await whitelabel_service.monitor_deployment_health(customer_id)
        return health_status
        
    except Exception as e:
        logger.error(f"Error checking deployment health: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/customers/{customer_id}/usage", response_model=Dict[str, Any])
async def get_customer_usage(
    customer_id: int,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    whitelabel_service: WhiteLabelService = Depends(get_whitelabel_service),
    current_user = Depends(get_current_user)
):
    """Get usage statistics for customer"""
    try:
        # Parse dates if provided
        start_dt = None
        end_dt = None
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
        
        usage_data = await whitelabel_service.get_customer_usage(
            customer_id, start_dt, end_dt
        )
        
        return usage_data
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting customer usage: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/customers/{customer_id}/logo")
async def upload_customer_logo(
    customer_id: int,
    logo_file: UploadFile = File(...),
    logo_type: str = Query("primary"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload customer logo"""
    import aiofiles
    import magic
    from app.config import settings
    
    try:
        # Verify customer access
        customer = verify_customer_access(customer_id, current_user, db)
        
        # Enforce file size limit (5MB)
        MAX_UPLOAD_BYTES = 5 * 1024 * 1024
        content = await logo_file.read()
        if len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=400, detail="File too large (max 5MB)")
        
        # Validate file content using magic bytes
        file_type = magic.from_buffer(content, mime=True)
        allowed_types = ["image/png", "image/jpeg", "image/svg+xml", "image/x-icon"]
        if file_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type detected: {file_type}. Allowed: {', '.join(allowed_types)}"
            )
        
        # Get configurable upload directory
        base_upload_dir = os.getenv("UPLOAD_BASE_DIR", "/tmp/uploads")
        upload_dir = os.path.join(base_upload_dir, "logos", str(customer_id))
        
        # Verify path is within base directory (prevent path traversal)
        abs_upload_dir = os.path.abspath(upload_dir)
        abs_base_dir = os.path.abspath(base_upload_dir)
        if not abs_upload_dir.startswith(abs_base_dir):
            raise HTTPException(status_code=400, detail="Invalid upload path")
        
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate safe filename (don't trust user input)
        file_extension = file_type.split("/")[-1]
        if file_extension == "svg+xml":
            file_extension = "svg"
        filename = f"{logo_type}_logo.{file_extension}"
        file_path = os.path.join(upload_dir, filename)
        
        # Write file asynchronously
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)
        
        # Update branding configuration
        branding = db.query(BrandingConfiguration).filter(
            BrandingConfiguration.customer_id == customer_id
        ).first()
        
        if not branding:
            raise HTTPException(status_code=404, detail="Branding configuration not found")
        
        # Update logo URL based on type
        logo_url = f"/uploads/logos/{customer_id}/{filename}"
        
        if logo_type == "primary":
            branding.logo_url = logo_url
        elif logo_type == "dark":
            branding.logo_dark_url = logo_url
        elif logo_type == "favicon":
            branding.favicon_url = logo_url
        
        branding.updated_at = datetime.utcnow()
        db.commit()
        
        return {
            "message": f"{logo_type.title()} logo uploaded successfully",
            "logo_url": logo_url,
            "file_size": len(content),
            "uploaded_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading logo: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/customers/{customer_id}/analytics", response_model=Dict[str, Any])
async def get_customer_analytics(
    customer_id: int,
    period: str = Query("30d"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get analytics for customer"""
    try:
        # Calculate date range
        now = datetime.utcnow()
        if period == "7d":
            start_date = now - timedelta(days=7)
        elif period == "30d":
            start_date = now - timedelta(days=30)
        elif period == "90d":
            start_date = now - timedelta(days=90)
        else:  # 1y
            start_date = now - timedelta(days=365)
        
        # Get analytics data (simplified - would be more complex in production)
        customer = db.query(WhiteLabelCustomer).filter(
            WhiteLabelCustomer.id == customer_id
        ).first()
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Mock analytics data
        analytics = {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": now.isoformat(),
                "period": period
            },
            "user_metrics": {
                "total_users": customer.max_users,
                "active_users": int(customer.max_users * 0.7),
                "new_users": int(customer.max_users * 0.1),
                "user_retention_rate": 0.85
            },
            "usage_metrics": {
                "api_calls": int(customer.max_api_calls_per_month * 0.6),
                "page_views": int(customer.max_api_calls_per_month * 2.5),
                "session_duration_minutes": 24.5,
                "feature_adoption_rate": 0.78
            },
            "performance_metrics": {
                "average_response_time_ms": 245,
                "uptime_percentage": 99.8,
                "error_rate": 0.02,
                "customer_satisfaction": 4.6
            },
            "business_metrics": {
                "monthly_revenue": customer.monthly_fee,
                "cost_per_user": customer.monthly_fee / max(customer.max_users, 1),
                "support_tickets": 3,
                "feature_requests": 7
            }
        }
        
        return analytics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting customer analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/customers/{customer_id}/support-ticket", response_model=Dict[str, Any])
async def create_support_ticket(
    customer_id: int,
    ticket_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create support ticket for customer"""
    try:
        # Validate required fields
        required_fields = ["title", "description", "priority", "category", "reporter_name", "reporter_email"]
        for field in required_fields:
            if field not in ticket_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Generate ticket number
        ticket_count = db.query(SupportTicket).filter(
            SupportTicket.customer_id == customer_id
        ).count()
        ticket_number = f"WL-{customer_id}-{ticket_count + 1:04d}"
        
        # Create ticket
        ticket = SupportTicket(
            customer_id=customer_id,
            ticket_number=ticket_number,
            title=ticket_data["title"],
            description=ticket_data["description"],
            priority=ticket_data["priority"],
            category=ticket_data["category"],
            severity=ticket_data.get("severity", "minor"),
            reporter_name=ticket_data["reporter_name"],
            reporter_email=ticket_data["reporter_email"]
        )
        
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        
        return {
            "id": ticket.id,
            "ticket_number": ticket.ticket_number,
            "title": ticket.title,
            "priority": ticket.priority,
            "category": ticket.category,
            "status": ticket.status,
            "created_at": ticket.created_at.isoformat(),
            "message": "Support ticket created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating support ticket: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/deployment-templates", response_model=Dict[str, Any])
async def get_deployment_templates(
    current_user = Depends(get_current_user)
):
    """Get available deployment templates"""
    try:
        templates = {
            "cloud_hosted": {
                "name": "Cloud Hosted",
                "description": "Fully managed cloud deployment",
                "features": [
                    "Auto-scaling infrastructure",
                    "Automated backups",
                    "24/7 monitoring",
                    "SSL certificates included",
                    "CDN integration"
                ],
                "pricing": {
                    "setup_fee": 0,
                    "monthly_base": 299,
                    "per_user": 15
                },
                "deployment_time": "1-2 hours"
            },
            "on_premise": {
                "name": "On-Premise",
                "description": "Customer-managed infrastructure",
                "features": [
                    "Full data control",
                    "Custom security policies",
                    "Integration flexibility",
                    "Deployment package provided",
                    "Installation support"
                ],
                "pricing": {
                    "setup_fee": 5000,
                    "monthly_base": 999,
                    "per_user": 25
                },
                "deployment_time": "1-2 weeks"
            },
            "air_gapped": {
                "name": "Air-Gapped",
                "description": "Isolated network deployment",
                "features": [
                    "Complete network isolation",
                    "Offline operation capability",
                    "Enhanced security",
                    "Custom deployment package",
                    "Dedicated support"
                ],
                "pricing": {
                    "setup_fee": 15000,
                    "monthly_base": 2499,
                    "per_user": 50
                },
                "deployment_time": "2-4 weeks"
            }
        }
        
        return templates
        
    except Exception as e:
        logger.error(f"Error getting deployment templates: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))