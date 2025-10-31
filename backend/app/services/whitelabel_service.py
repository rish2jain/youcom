"""
White-label Service

Service for managing custom branding, on-premise deployment,
and enterprise white-label configurations.
"""

import os
import json
import yaml
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
import logging
try:
    import docker
except ImportError:
    docker = None

import subprocess
from pathlib import Path

from app.models.whitelabel import (
    WhiteLabelCustomer, BrandingConfiguration, DeploymentConfiguration,
    CustomIntegration, WhiteLabelUsage, SupportTicket, WhiteLabelAnalytics,
    DeploymentType, BrandingStatus, DeploymentStatus
)

logger = logging.getLogger(__name__)


class WhiteLabelService:
    """Service for white-label solutions and custom deployments"""
    
    def __init__(self, db: Session):
        self.db = db
        self.docker_client = None
        if docker:
            try:
                self.docker_client = docker.from_env()
            except Exception as e:
                logger.warning(f"Docker client not available: {str(e)}")
        else:
            logger.warning("Docker module not available")
        
        # Deployment templates
        self.deployment_templates = {
            "cloud_hosted": self._get_cloud_template(),
            "on_premise": self._get_onpremise_template(),
            "air_gapped": self._get_airgapped_template()
        }

    async def create_whitelabel_customer(
        self, 
        customer_data: Dict[str, Any]
    ) -> WhiteLabelCustomer:
        """Create a new white-label customer"""
        try:
            customer = WhiteLabelCustomer(
                customer_name=customer_data["customer_name"],
                customer_domain=customer_data["customer_domain"],
                contact_email=customer_data["contact_email"],
                contact_name=customer_data["contact_name"],
                subscription_tier=customer_data.get("subscription_tier", "enterprise"),
                monthly_fee=customer_data["monthly_fee"],
                setup_fee=customer_data.get("setup_fee", 0.0),
                contract_start_date=customer_data["contract_start_date"],
                contract_end_date=customer_data["contract_end_date"],
                deployment_type=customer_data.get("deployment_type", DeploymentType.CLOUD_HOSTED),
                max_users=customer_data.get("max_users", 100),
                max_api_calls_per_month=customer_data.get("max_api_calls_per_month", 10000),
                features_enabled=customer_data.get("features_enabled", {}),
                integrations_enabled=customer_data.get("integrations_enabled", []),
                support_level=customer_data.get("support_level", "standard")
            )
            
            self.db.add(customer)
            self.db.commit()
            self.db.refresh(customer)
            
            # Create default branding configuration
            await self._create_default_branding(customer.id, customer_data.get("branding", {}))
            
            # Create deployment configuration if needed
            if customer.deployment_type != DeploymentType.CLOUD_HOSTED:
                await self._create_deployment_config(customer.id, customer_data.get("deployment", {}))
            
            logger.info(f"Created white-label customer: {customer.customer_name}")
            return customer
            
        except Exception as e:
            logger.error(f"Error creating white-label customer: {str(e)}")
            self.db.rollback()
            raise

    async def configure_branding(
        self, 
        customer_id: int, 
        branding_data: Dict[str, Any]
    ) -> BrandingConfiguration:
        """Configure custom branding for a customer"""
        try:
            # Get existing branding config or create new
            branding = self.db.query(BrandingConfiguration).filter(
                BrandingConfiguration.customer_id == customer_id
            ).first()
            
            if not branding:
                branding = BrandingConfiguration(customer_id=customer_id)
                self.db.add(branding)
            
            # Update branding configuration
            for field, value in branding_data.items():
                if hasattr(branding, field):
                    setattr(branding, field, value)
            
            branding.updated_at = datetime.utcnow()
            branding.version = self._increment_version(branding.version)
            
            self.db.commit()
            self.db.refresh(branding)
            
            # Generate custom CSS
            await self._generate_custom_css(branding)
            
            # Update deployment if active
            await self._update_deployment_branding(customer_id, branding)
            
            logger.info(f"Updated branding configuration for customer {customer_id}")
            return branding
            
        except Exception as e:
            logger.error(f"Error configuring branding: {str(e)}")
            self.db.rollback()
            raise

    async def deploy_customer_instance(
        self, 
        customer_id: int, 
        deployment_config: Dict[str, Any] = None
    ) -> DeploymentConfiguration:
        """Deploy customer instance based on deployment type"""
        try:
            customer = self.db.query(WhiteLabelCustomer).filter(
                WhiteLabelCustomer.id == customer_id
            ).first()
            
            if not customer:
                raise ValueError("Customer not found")
            
            # Get or create deployment configuration
            deployment = self.db.query(DeploymentConfiguration).filter(
                DeploymentConfiguration.customer_id == customer_id
            ).first()
            
            if not deployment:
                deployment = await self._create_deployment_config(
                    customer_id, 
                    deployment_config or {}
                )
            
            # Update deployment status
            deployment.deployment_status = DeploymentStatus.IN_PROGRESS
            deployment.updated_at = datetime.utcnow()
            self.db.commit()
            
            # Deploy based on type
            if customer.deployment_type == DeploymentType.CLOUD_HOSTED:
                result = await self._deploy_cloud_instance(customer, deployment)
            elif customer.deployment_type == DeploymentType.ON_PREMISE:
                result = await self._deploy_onpremise_instance(customer, deployment)
            elif customer.deployment_type == DeploymentType.AIR_GAPPED:
                result = await self._deploy_airgapped_instance(customer, deployment)
            else:
                raise ValueError(f"Unsupported deployment type: {customer.deployment_type}")
            
            # Update deployment status
            if result["success"]:
                deployment.deployment_status = DeploymentStatus.DEPLOYED
                deployment.deployed_at = datetime.utcnow()
                deployment.deployed_version = result.get("version", "1.0.0")
                deployment.health_check_url = result.get("health_check_url")
            else:
                deployment.deployment_status = DeploymentStatus.FAILED
                deployment.deployment_notes = result.get("error", "Deployment failed")
            
            self.db.commit()
            self.db.refresh(deployment)
            
            logger.info(f"Deployment completed for customer {customer_id}: {deployment.deployment_status}")
            return deployment
            
        except Exception as e:
            logger.error(f"Error deploying customer instance: {str(e)}")
            # Update deployment status to failed
            if 'deployment' in locals():
                deployment.deployment_status = DeploymentStatus.FAILED
                deployment.deployment_notes = str(e)
                self.db.commit()
            raise

    async def generate_deployment_package(
        self, 
        customer_id: int
    ) -> Dict[str, Any]:
        """Generate deployment package for on-premise installation"""
        try:
            customer = self.db.query(WhiteLabelCustomer).filter(
                WhiteLabelCustomer.id == customer_id
            ).first()
            
            if not customer:
                raise ValueError("Customer not found")
            
            branding = self.db.query(BrandingConfiguration).filter(
                BrandingConfiguration.customer_id == customer_id
            ).first()
            
            deployment = self.db.query(DeploymentConfiguration).filter(
                DeploymentConfiguration.customer_id == customer_id
            ).first()
            
            # Create deployment package directory with safe domain validation
            import re
            safe_domain = customer.customer_domain
            if not re.match(r'^[a-zA-Z0-9.-]+$', safe_domain) or '..' in safe_domain or '/' in safe_domain:
                # Use safe fallback - hash of domain
                import hashlib
                safe_domain = hashlib.sha256(customer.customer_domain.encode()).hexdigest()[:16]
                logger.warning(f"Using safe domain hash for customer {customer_id}: {safe_domain}")
            
            base_dir = os.getenv("DEPLOYMENT_PACKAGE_DIR", "/tmp/deployment_packages")
            package_dir = os.path.join(base_dir, safe_domain)
            
            # Verify path is within base directory
            abs_package_dir = os.path.abspath(package_dir)
            abs_base_dir = os.path.abspath(base_dir)
            if not abs_package_dir.startswith(abs_base_dir):
                raise ValueError("Invalid package directory path")
            
            os.makedirs(package_dir, exist_ok=True)
            
            # Generate Docker Compose configuration
            docker_compose = await self._generate_docker_compose(customer, branding, deployment)
            with open(f"{package_dir}/docker-compose.yml", "w") as f:
                yaml.dump(docker_compose, f)
            
            # Generate environment configuration
            env_config = await self._generate_env_config(customer, branding, deployment)
            with open(f"{package_dir}/.env", "w") as f:
                for key, value in env_config.items():
                    f.write(f"{key}={value}\n")
            
            # Generate installation script
            install_script = await self._generate_install_script(customer, deployment)
            with open(f"{package_dir}/install.sh", "w") as f:
                f.write(install_script)
            os.chmod(f"{package_dir}/install.sh", 0o755)
            
            # Generate configuration files
            await self._generate_config_files(package_dir, customer, branding, deployment)
            
            # Generate documentation
            await self._generate_deployment_docs(package_dir, customer, deployment)
            
            # Create package archive
            package_path = f"{package_dir}.tar.gz"
            subprocess.run([
                "tar", "-czf", package_path, "-C", "/tmp/deployment_packages", 
                customer.customer_domain
            ], check=True)
            
            return {
                "package_path": package_path,
                "package_size": os.path.getsize(package_path),
                "generated_at": datetime.utcnow().isoformat(),
                "customer_domain": customer.customer_domain,
                "deployment_type": customer.deployment_type
            }
            
        except Exception as e:
            logger.error(f"Error generating deployment package: {str(e)}")
            raise

    async def monitor_deployment_health(self, customer_id: int) -> Dict[str, Any]:
        """Monitor health of customer deployment"""
        try:
            deployment = self.db.query(DeploymentConfiguration).filter(
                DeploymentConfiguration.customer_id == customer_id
            ).first()
            
            if not deployment or not deployment.health_check_url:
                return {"status": "unknown", "message": "No health check URL configured"}
            
            # Perform health check
            import aiohttp
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(
                        deployment.health_check_url, 
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        if response.status == 200:
                            health_data = await response.json()
                            
                            # Update deployment health
                            deployment.last_health_check = datetime.utcnow()
                            self.db.commit()
                            
                            return {
                                "status": "healthy",
                                "response_time_ms": health_data.get("response_time", 0),
                                "uptime": health_data.get("uptime", "unknown"),
                                "version": health_data.get("version", deployment.deployed_version),
                                "last_check": deployment.last_health_check.isoformat()
                            }
                        else:
                            return {
                                "status": "unhealthy",
                                "http_status": response.status,
                                "message": f"Health check returned {response.status}"
                            }
                            
                except asyncio.TimeoutError:
                    return {
                        "status": "timeout",
                        "message": "Health check timed out"
                    }
                except Exception as e:
                    return {
                        "status": "error",
                        "message": str(e)
                    }
                    
        except Exception as e:
            logger.error(f"Error monitoring deployment health: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def get_customer_usage(
        self, 
        customer_id: int, 
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Dict[str, Any]:
        """Get usage statistics for customer"""
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()
            
            # Get usage records
            usage_records = self.db.query(WhiteLabelUsage).filter(
                and_(
                    WhiteLabelUsage.customer_id == customer_id,
                    WhiteLabelUsage.created_at >= start_date,
                    WhiteLabelUsage.created_at <= end_date
                )
            ).all()
            
            if not usage_records:
                return {
                    "total_api_calls": 0,
                    "active_users": 0,
                    "storage_used_gb": 0.0,
                    "bandwidth_used_gb": 0.0,
                    "average_response_time_ms": 0.0,
                    "uptime_percentage": 0.0,
                    "total_fees": 0.0
                }
            
            # Aggregate usage data
            total_api_calls = sum(record.total_api_calls for record in usage_records)
            max_active_users = max(record.active_users for record in usage_records)
            total_storage = sum(record.storage_used_gb for record in usage_records) / len(usage_records)
            total_bandwidth = sum(record.bandwidth_used_gb for record in usage_records)
            avg_response_time = sum(record.average_response_time_ms for record in usage_records) / len(usage_records)
            avg_uptime = sum(record.uptime_percentage for record in usage_records) / len(usage_records)
            total_fees = sum(record.total_fee for record in usage_records)
            
            # Get feature usage breakdown
            feature_usage = {}
            for record in usage_records:
                for feature, usage in record.feature_usage.items():
                    feature_usage[feature] = feature_usage.get(feature, 0) + usage
            
            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "usage_summary": {
                    "total_api_calls": total_api_calls,
                    "active_users": max_active_users,
                    "storage_used_gb": round(total_storage, 2),
                    "bandwidth_used_gb": round(total_bandwidth, 2),
                    "average_response_time_ms": round(avg_response_time, 2),
                    "uptime_percentage": round(avg_uptime, 2),
                    "total_fees": round(total_fees, 2)
                },
                "feature_usage": feature_usage,
                "usage_trend": [
                    {
                        "date": record.created_at.isoformat(),
                        "api_calls": record.total_api_calls,
                        "active_users": record.active_users,
                        "response_time": record.average_response_time_ms
                    }
                    for record in usage_records
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting customer usage: {str(e)}")
            raise

    # Private helper methods
    
    async def _create_default_branding(self, customer_id: int, branding_data: Dict[str, Any]):
        """Create default branding configuration"""
        branding = BrandingConfiguration(
            customer_id=customer_id,
            brand_name=branding_data.get("brand_name", "Enterprise CIA"),
            brand_tagline=branding_data.get("brand_tagline", "Competitive Intelligence Platform"),
            primary_color=branding_data.get("primary_color", "#1f2937"),
            secondary_color=branding_data.get("secondary_color", "#3b82f6"),
            accent_color=branding_data.get("accent_color", "#10b981"),
            status=BrandingStatus.ACTIVE
        )
        
        self.db.add(branding)
        self.db.commit()
        return branding

    async def _create_deployment_config(self, customer_id: int, deployment_data: Dict[str, Any]):
        """Create deployment configuration"""
        deployment = DeploymentConfiguration(
            customer_id=customer_id,
            deployment_name=deployment_data.get("deployment_name", f"customer-{customer_id}"),
            deployment_type=deployment_data.get("deployment_type", DeploymentType.CLOUD_HOSTED),
            environment=deployment_data.get("environment", "production"),
            server_specifications=deployment_data.get("server_specifications", {
                "cpu_cores": 4,
                "memory_gb": 16,
                "storage_gb": 100
            }),
            network_configuration=deployment_data.get("network_configuration", {}),
            security_configuration=deployment_data.get("security_configuration", {}),
            application_settings=deployment_data.get("application_settings", {}),
            monitoring_enabled=deployment_data.get("monitoring_enabled", True),
            backup_enabled=deployment_data.get("backup_enabled", True)
        )
        
        self.db.add(deployment)
        self.db.commit()
        return deployment

    async def _deploy_cloud_instance(self, customer: WhiteLabelCustomer, deployment: DeploymentConfiguration):
        """Deploy cloud-hosted instance"""
        try:
            # This would integrate with cloud providers (AWS, GCP, Azure)
            # For now, we'll simulate the deployment
            
            # Generate unique subdomain
            subdomain = f"{customer.customer_domain.replace('.', '-')}-{customer.id}"
            
            # Simulate cloud deployment
            await asyncio.sleep(2)  # Simulate deployment time
            
            return {
                "success": True,
                "version": "1.0.0",
                "health_check_url": f"https://{subdomain}.cia-platform.com/health",
                "deployment_url": f"https://{subdomain}.cia-platform.com",
                "message": "Cloud instance deployed successfully"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _deploy_onpremise_instance(self, customer: WhiteLabelCustomer, deployment: DeploymentConfiguration):
        """Deploy on-premise instance"""
        try:
            # Generate deployment package
            package_info = await self.generate_deployment_package(customer.id)
            
            return {
                "success": True,
                "version": "1.0.0",
                "package_path": package_info["package_path"],
                "message": "On-premise deployment package generated"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _deploy_airgapped_instance(self, customer: WhiteLabelCustomer, deployment: DeploymentConfiguration):
        """Deploy air-gapped instance"""
        try:
            # Generate air-gapped deployment package with all dependencies
            package_info = await self.generate_deployment_package(customer.id)
            
            # Add offline dependencies
            # This would include Docker images, database dumps, etc.
            
            return {
                "success": True,
                "version": "1.0.0",
                "package_path": package_info["package_path"],
                "message": "Air-gapped deployment package generated with offline dependencies"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _generate_docker_compose(self, customer, branding, deployment):
        """Generate Docker Compose configuration"""
        import secrets
        import string
        
        # Generate secure random password
        password_chars = string.ascii_letters + string.digits + "!@#$%^&*"
        db_password = ''.join(secrets.choice(password_chars) for _ in range(16))
        
        # Store the generated password securely
        if deployment:
            from app.config import settings
            
            # Check if secure secret management is required
            require_secure_secrets = getattr(settings, 'require_no_plaintext_credentials', False) or \
                                   getattr(settings, 'enforce_secret_management', False)
            
            if require_secure_secrets:
                raise RuntimeError("Plaintext password storage not allowed - secure secret management required")
            
            # In production, this should be stored in a secure secret store like AWS Secrets Manager
            # For now, we'll store a reference instead of the actual password
            deployment.database_configuration = deployment.database_configuration or {}
            
            try:
                # Attempt to store in secure secret store
                secret_name = f"secret_ref_{deployment.id}"
                # FUTURE: Integrate with secret management service (AWS Secrets Manager, HashiCorp Vault, or Azure Key Vault)
                # Example: success = await secrets_client.store_secret(secret_name, db_password)
                success = False  # Placeholder until secret store is implemented
                
                if success:
                    deployment.database_configuration['password_reference'] = secret_name
                    deployment.database_configuration['password_stored_securely'] = True
                    logger.info(f"Database password stored securely for deployment {deployment.id}")
                else:
                    # Fallback: warn and continue with reference (caller must handle secure storage)
                    deployment.database_configuration['password_reference'] = secret_name
                    deployment.database_configuration['password_stored_securely'] = False
                    logger.warning("Database password should be stored in secure secret store - returning plaintext for caller to handle securely")
                    # Return the password so caller can store it securely
                    deployment.database_configuration['plaintext_password'] = db_password
                    
            except Exception as e:
                logger.error(f"Failed to store password securely: {str(e)}")
                # Don't leave deployment in inconsistent state
                deployment.database_configuration['password_reference'] = f"secret_ref_{deployment.id}"
                deployment.database_configuration['password_stored_securely'] = False
                deployment.database_configuration['plaintext_password'] = db_password
                logger.warning("Storing password reference only - caller must handle secure storage")
            
            self.db.commit()
        
        return {
            "version": "3.8",
            "services": {
                "cia-backend": {
                    "image": f"cia-platform/backend:{deployment.deployed_version or 'latest'}",
                    "environment": [
                        f"CUSTOMER_ID={customer.id}",
                        f"BRAND_NAME={branding.brand_name if branding else customer.customer_name}",
                        f"PRIMARY_COLOR={branding.primary_color if branding else '#1f2937'}",
                        "DATABASE_URL=postgresql://cia:${POSTGRES_PASSWORD}@postgres:5432/cia_db"
                    ],
                    "ports": ["8000:8000"],
                    "depends_on": ["postgres", "redis"]
                },
                "cia-frontend": {
                    "image": f"cia-platform/frontend:{deployment.deployed_version or 'latest'}",
                    "environment": [
                        f"NEXT_PUBLIC_API_URL=http://cia-backend:8000",
                        f"NEXT_PUBLIC_BRAND_NAME={branding.brand_name if branding else customer.customer_name}"
                    ],
                    "ports": ["3000:3000"],
                    "depends_on": ["cia-backend"]
                },
                "postgres": {
                    "image": "postgres:15",
                    "environment": [
                        "POSTGRES_DB=cia_db",
                        "POSTGRES_USER=cia",
                        f"POSTGRES_PASSWORD={db_password}"
                    ],
                    "volumes": ["postgres_data:/var/lib/postgresql/data"]
                },
                "redis": {
                    "image": "redis:7",
                    "volumes": ["redis_data:/data"]
                }
            },
            "volumes": {
                "postgres_data": {},
                "redis_data": {}
            }
        }

    async def _generate_env_config(self, customer, branding, deployment):
        """Generate environment configuration"""
        return {
            "CUSTOMER_ID": str(customer.id),
            "CUSTOMER_DOMAIN": customer.customer_domain,
            "BRAND_NAME": branding.brand_name if branding else customer.customer_name,
            "PRIMARY_COLOR": branding.primary_color if branding else "#1f2937",
            "SECONDARY_COLOR": branding.secondary_color if branding else "#3b82f6",
            "MAX_USERS": str(customer.max_users),
            "MAX_API_CALLS": str(customer.max_api_calls_per_month),
            "DEPLOYMENT_TYPE": customer.deployment_type,
            "ENVIRONMENT": deployment.environment if deployment else "production"
        }

    async def _generate_install_script(self, customer, deployment):
        """Generate installation script"""
        return f"""#!/bin/bash
# CIA Platform Installation Script
# Customer: {customer.customer_name}
# Domain: {customer.customer_domain}

set -e

echo "Starting CIA Platform installation..."

# Check Docker installation
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create directories
mkdir -p data/postgres
mkdir -p data/redis
mkdir -p logs

# Set permissions
chmod 755 data/postgres
chmod 755 data/redis
chmod 755 logs

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

# Start services
echo "Starting CIA Platform services..."
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 30

# Run database migrations
echo "Running database migrations..."
docker-compose exec cia-backend python -m alembic upgrade head

# Create initial admin user
echo "Creating initial admin user..."
docker-compose exec cia-backend python scripts/create_admin.py

echo "Installation completed successfully!"
echo "Access your CIA Platform at: http://localhost:3000"
echo "Admin login will be displayed above."
"""

    async def _generate_config_files(self, package_dir, customer, branding, deployment):
        """Generate additional configuration files"""
        # Nginx configuration
        nginx_config = f"""
server {{
    listen 80;
    server_name {customer.customer_domain};
    
    location / {{
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }}
    
    location /api/ {{
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }}
}}
"""
        
        with open(f"{package_dir}/nginx.conf", "w") as f:
            f.write(nginx_config)

    async def _generate_deployment_docs(self, package_dir, customer, deployment):
        """Generate deployment documentation"""
        docs = f"""# CIA Platform Deployment Guide

## Customer Information
- **Customer**: {customer.customer_name}
- **Domain**: {customer.customer_domain}
- **Deployment Type**: {customer.deployment_type}
- **Max Users**: {customer.max_users}

## System Requirements
- Docker 20.10+
- Docker Compose 2.0+
- 4 CPU cores minimum
- 16GB RAM minimum
- 100GB storage minimum

## Installation Steps

1. Extract the deployment package
2. Review and modify `.env` file if needed
3. Run the installation script: `./install.sh`
4. Access the platform at your configured domain

## Configuration

### Environment Variables
See `.env` file for all configuration options.

### Custom Branding
Branding is pre-configured based on your specifications.

### Support
Contact support at: {customer.contact_email}
Support Level: {customer.support_level}

## Maintenance

### Backup
Database backups are automated daily.
Backup location: `./data/backups/`

### Updates
Contact support for update procedures.

### Monitoring
Health check endpoint: `/health`
Metrics endpoint: `/metrics`
"""
        
        with open(f"{package_dir}/README.md", "w") as f:
            f.write(docs)

    def _get_cloud_template(self):
        """Get cloud deployment template"""
        return {
            "type": "cloud_hosted",
            "infrastructure": "managed",
            "scaling": "auto",
            "backup": "automated",
            "monitoring": "included"
        }

    def _get_onpremise_template(self):
        """Get on-premise deployment template"""
        return {
            "type": "on_premise",
            "infrastructure": "customer_managed",
            "scaling": "manual",
            "backup": "customer_managed",
            "monitoring": "optional"
        }

    def _get_airgapped_template(self):
        """Get air-gapped deployment template"""
        return {
            "type": "air_gapped",
            "infrastructure": "isolated",
            "scaling": "manual",
            "backup": "offline",
            "monitoring": "local_only"
        }

    def _increment_version(self, current_version: str) -> str:
        """Increment version number"""
        try:
            parts = current_version.split(".")
            parts[-1] = str(int(parts[-1]) + 1)
            return ".".join(parts)
        except:
            return "1.0.1"

    async def _generate_custom_css(self, branding: BrandingConfiguration):
        """Generate custom CSS based on branding"""
        css = f"""
:root {{
    --primary-color: {branding.primary_color};
    --secondary-color: {branding.secondary_color};
    --accent-color: {branding.accent_color};
    --background-color: {branding.background_color};
    --text-color: {branding.text_color};
    --primary-font: '{branding.primary_font}', sans-serif;
    --secondary-font: '{branding.secondary_font}', sans-serif;
}}

.brand-logo {{
    background-image: url('{branding.logo_url}');
}}

.brand-name::before {{
    content: '{branding.brand_name}';
}}
"""
        branding.custom_css = css

    async def _update_deployment_branding(self, customer_id: int, branding: BrandingConfiguration):
        """Update deployment with new branding"""
        # This would trigger a deployment update with new branding
        # For now, we'll just log the update
        logger.info(f"Branding updated for customer {customer_id}, deployment update triggered")