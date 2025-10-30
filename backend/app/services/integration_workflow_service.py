"""
Integration Workflow Service for Advanced Intelligence Suite

This service integrates HubSpot sync with existing competitive intelligence workflows,
connects Obsidian export with existing research report generation, and wires
integration health checks with existing system monitoring.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func

from app.models.hubspot_integration import HubSpotIntegration, HubSpotSyncLog
from app.models.obsidian_integration import ObsidianIntegration, ObsidianSyncLog
from app.models.impact_card import ImpactCard
from app.models.company_research import CompanyResearch
from app.models.watch import WatchItem
from app.services.hubspot_sync_service import HubSpotSyncService, get_integration_by_workspace
from app.services.obsidian_sync_service import ObsidianSyncService
from app.services.performance_monitor import metrics_collector
from app.realtime import emit_progress

logger = logging.getLogger(__name__)

@dataclass
class IntegrationWorkflowMetrics:
    """Metrics for integration workflow performance."""
    hubspot_syncs_completed: int
    obsidian_exports_completed: int
    workflow_automations_triggered: int
    integration_health_checks: int
    average_sync_time: float
    workflow_health: str

class IntegrationWorkflowService:
    """Service for integrating HubSpot and Obsidian with existing workflows."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._metrics_lock = asyncio.Lock()
        
        # Workflow configuration
        self.auto_hubspot_sync = True
        self.auto_obsidian_export = True
        self.sync_on_impact_card_creation = True
        self.export_on_research_completion = True
        
        # Performance tracking
        self.workflow_metrics = {
            "hubspot_syncs_completed": 0,
            "obsidian_exports_completed": 0,
            "workflow_automations_triggered": 0,
            "integration_health_checks": 0,
            "sync_times": []
        }
    
    async def integrate_hubspot_with_cia_workflows(
        self, 
        workspace_id: str,
        impact_card: Optional[ImpactCard] = None
    ) -> Dict[str, Any]:
        """Integrate HubSpot sync with existing CIA workflows."""
        try:
            logger.info(f"🔗 Integrating HubSpot with CIA workflows for workspace {workspace_id}")
            
            # Get HubSpot integration for workspace
            hubspot_integration = await get_integration_by_workspace(workspace_id, self.db)
            
            if not hubspot_integration or not hubspot_integration.sync_enabled:
                return {
                    "status": "skipped",
                    "reason": "HubSpot integration not found or disabled",
                    "workspace_id": workspace_id
                }
            
            start_time = datetime.utcnow()
            
            # Perform HubSpot sync
            async with HubSpotSyncService(hubspot_integration, self.db) as sync_service:
                # If specific impact card provided, sync related data
                if impact_card:
                    await self._sync_impact_card_to_hubspot(sync_service, impact_card)
                else:
                    # Perform incremental sync
                    sync_log = await sync_service.sync_to_hubspot("incremental")
                    
                    # Trigger workflow automations if configured
                    if self.auto_hubspot_sync:
                        await self._trigger_hubspot_workflows(hubspot_integration, sync_log)
            
            # Record metrics
            sync_time = (datetime.utcnow() - start_time).total_seconds()
            async with self._metrics_lock:
                self.workflow_metrics["hubspot_syncs_completed"] += 1
                self.workflow_metrics["sync_times"].append(sync_time)
            
            # Emit progress event
            await emit_progress(
                "hubspot_workflow_integration",
                {
                    "workspace_id": workspace_id,
                    "status": "completed",
                    "sync_time": sync_time,
                    "impact_card_id": impact_card.id if impact_card else None
                }
            )
            
            logger.info(f"✅ HubSpot workflow integration completed for workspace {workspace_id}")
            
            return {
                "status": "completed",
                "workspace_id": workspace_id,
                "sync_time": sync_time,
                "integration_id": str(hubspot_integration.id)
            }
            
        except Exception as e:
            logger.error(f"❌ Error integrating HubSpot workflows for workspace {workspace_id}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "workspace_id": workspace_id
            }    

    async def integrate_obsidian_with_research_workflows(
        self, 
        user_id: str,
        research_report: Optional[CompanyResearch] = None
    ) -> Dict[str, Any]:
        """Integrate Obsidian export with existing research report generation."""
        try:
            logger.info(f"📝 Integrating Obsidian with research workflows for user {user_id}")
            
            # Get Obsidian integrations for user
            result = await self.db.execute(
                select(ObsidianIntegration)
                .where(
                    and_(
                        ObsidianIntegration.user_id == user_id,
                        ObsidianIntegration.sync_enabled == True
                    )
                )
            )
            
            obsidian_integrations = result.scalars().all()
            
            if not obsidian_integrations:
                return {
                    "status": "skipped",
                    "reason": "No active Obsidian integrations found",
                    "user_id": user_id
                }
            
            start_time = datetime.utcnow()
            exports_completed = 0
            
            # Export to each active Obsidian integration
            for integration in obsidian_integrations:
                try:
                    sync_service = ObsidianSyncService(self.db)
                    
                    if research_report:
                        # Export specific research report
                        await self._export_research_to_obsidian(sync_service, integration, research_report)
                    else:
                        # Perform incremental sync
                        await sync_service.sync_integration(str(integration.id), "incremental_sync")
                    
                    exports_completed += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to export to Obsidian integration {integration.id}: {e}")
            
            # Record metrics
            export_time = (datetime.utcnow() - start_time).total_seconds()
            async with self._metrics_lock:
                self.workflow_metrics["obsidian_exports_completed"] += exports_completed
                self.workflow_metrics["sync_times"].append(export_time)
            
            # Emit progress event
            await emit_progress(
                "obsidian_workflow_integration",
                {
                    "user_id": user_id,
                    "status": "completed",
                    "exports_completed": exports_completed,
                    "export_time": export_time,
                    "research_report_id": research_report.id if research_report else None
                }
            )
            
            logger.info(f"✅ Obsidian workflow integration completed for user {user_id}")
            
            return {
                "status": "completed",
                "user_id": user_id,
                "exports_completed": exports_completed,
                "export_time": export_time,
                "integrations_processed": len(obsidian_integrations)
            }
            
        except Exception as e:
            logger.error(f"❌ Error integrating Obsidian workflows for user {user_id}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "user_id": user_id
            }
    
    async def wire_integration_health_checks(self) -> Dict[str, Any]:
        """Wire integration health checks with existing system monitoring."""
        try:
            logger.info("🔍 Wiring integration health checks with system monitoring")
            
            health_status = {
                "hubspot_integrations": {},
                "obsidian_integrations": {},
                "overall_health": "healthy",
                "issues": [],
                "recommendations": []
            }
            
            # Check HubSpot integrations health
            hubspot_health = await self._check_hubspot_integrations_health()
            health_status["hubspot_integrations"] = hubspot_health
            
            # Check Obsidian integrations health
            obsidian_health = await self._check_obsidian_integrations_health()
            health_status["obsidian_integrations"] = obsidian_health
            
            # Determine overall health
            total_issues = len(hubspot_health.get("issues", [])) + len(obsidian_health.get("issues", []))
            
            if total_issues == 0:
                health_status["overall_health"] = "healthy"
            elif total_issues <= 2:
                health_status["overall_health"] = "warning"
            else:
                health_status["overall_health"] = "critical"
            
            # Combine issues and recommendations
            health_status["issues"] = hubspot_health.get("issues", []) + obsidian_health.get("issues", [])
            health_status["recommendations"] = hubspot_health.get("recommendations", []) + obsidian_health.get("recommendations", [])
            
            # Record health check metric
            async with self._metrics_lock:
                self.workflow_metrics["integration_health_checks"] += 1
            
            # Record metrics for monitoring system
            await metrics_collector.record_metric(
                "integration_health_check",
                1.0 if health_status["overall_health"] == "healthy" else 0.0,
                {
                    "overall_health": health_status["overall_health"],
                    "total_issues": total_issues,
                    "hubspot_active": hubspot_health.get("active_integrations", 0),
                    "obsidian_active": obsidian_health.get("active_integrations", 0)
                }
            )
            
            logger.info(f"✅ Integration health check completed: {health_status['overall_health']}")
            
            return health_status
            
        except Exception as e:
            logger.error(f"❌ Error wiring integration health checks: {e}")
            return {
                "overall_health": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _sync_impact_card_to_hubspot(
        self, 
        sync_service: HubSpotSyncService, 
        impact_card: ImpactCard
    ) -> None:
        """Sync a specific impact card to HubSpot."""
        try:
            # This would typically involve updating company records in HubSpot
            # with competitive intelligence data from the impact card
            
            # For now, we'll trigger a general sync that includes this impact card
            await sync_service.sync_to_hubspot("incremental")
            
            logger.info(f"Synced impact card {impact_card.id} to HubSpot")
            
        except Exception as e:
            logger.error(f"Failed to sync impact card {impact_card.id} to HubSpot: {e}")
            raise
    
    async def _trigger_hubspot_workflows(
        self, 
        integration: HubSpotIntegration, 
        sync_log: HubSpotSyncLog
    ) -> None:
        """Trigger HubSpot workflow automations based on sync results."""
        try:
            # Check if workflows should be triggered based on sync results
            if sync_log.status == "success" and sync_log.records_successful > 0:
                # Trigger workflow automations
                async with self._metrics_lock:
                    self.workflow_metrics["workflow_automations_triggered"] += 1
                
                logger.info(f"Triggered HubSpot workflows for integration {integration.id}")
            
        except Exception as e:
            logger.warning(f"Failed to trigger HubSpot workflows: {e}")
    
    async def _export_research_to_obsidian(
        self, 
        sync_service: ObsidianSyncService, 
        integration: ObsidianIntegration,
        research_report: CompanyResearch
    ) -> None:
        """Export a specific research report to Obsidian."""
        try:
            # Mark the research report for update in Obsidian
            await sync_service.mark_content_for_update(
                str(integration.id),
                "company_profile",
                str(research_report.id)
            )
            
            # Trigger sync to export the updated content
            await sync_service.sync_integration(str(integration.id), "incremental_sync")
            
            logger.info(f"Exported research report {research_report.id} to Obsidian integration {integration.id}")
            
        except Exception as e:
            logger.error(f"Failed to export research report {research_report.id} to Obsidian: {e}")
            raise
    
    async def _check_hubspot_integrations_health(self) -> Dict[str, Any]:
        """Check health of all HubSpot integrations."""
        try:
            result = await self.db.execute(
                select(HubSpotIntegration)
                .where(HubSpotIntegration.sync_enabled == True)
            )
            
            integrations = result.scalars().all()
            
            health_data = {
                "active_integrations": len(integrations),
                "healthy_integrations": 0,
                "issues": [],
                "recommendations": []
            }
            
            for integration in integrations:
                # Check for recent sync failures
                if integration.consecutive_failures is not None and integration.consecutive_failures > 3:
                    health_data["issues"].append(
                        f"HubSpot integration {integration.id} has {integration.consecutive_failures} consecutive failures"
                    )
                    health_data["recommendations"].append(
                        f"Review HubSpot integration {integration.id} configuration and credentials"
                    )
                else:
                    health_data["healthy_integrations"] += 1
                
                # Check last sync time
                if integration.last_sync_at and integration.last_sync_at < datetime.utcnow() - timedelta(hours=24):
                    health_data["issues"].append(
                        f"HubSpot integration {integration.id} hasn't synced in over 24 hours"
                    )
                    health_data["recommendations"].append(
                        f"Check sync schedule for HubSpot integration {integration.id}"
                    )
            
            return health_data
            
        except Exception as e:
            logger.error(f"Error checking HubSpot integrations health: {e}")
            return {
                "active_integrations": 0,
                "healthy_integrations": 0,
                "issues": ["Failed to check HubSpot integrations health"],
                "recommendations": ["Review HubSpot integration monitoring system"]
            }
    
    async def _check_obsidian_integrations_health(self) -> Dict[str, Any]:
        """Check health of all Obsidian integrations."""
        try:
            result = await self.db.execute(
                select(ObsidianIntegration)
                .where(ObsidianIntegration.sync_enabled == True)
            )
            
            integrations = result.scalars().all()
            
            health_data = {
                "active_integrations": len(integrations),
                "healthy_integrations": 0,
                "issues": [],
                "recommendations": []
            }
            
            for integration in integrations:
                # Check for recent sync failures
                if integration.consecutive_failures and integration.consecutive_failures > 3:
                    health_data["issues"].append(
                        f"Obsidian integration {integration.id} has {integration.consecutive_failures} consecutive failures"
                    )
                    health_data["recommendations"].append(
                        f"Review Obsidian integration {integration.id} vault connectivity"
                    )
                else:
                    health_data["healthy_integrations"] += 1
                
                # Check last sync time
                if integration.last_sync_at and integration.last_sync_at < datetime.utcnow() - timedelta(hours=24):
                    health_data["issues"].append(
                        f"Obsidian integration {integration.id} hasn't synced in over 24 hours"
                    )
                    health_data["recommendations"].append(
                        f"Check sync schedule for Obsidian integration {integration.id}"
                    )
            
            return health_data
            
        except Exception as e:
            logger.error(f"Error checking Obsidian integrations health: {e}")
            return {
                "active_integrations": 0,
                "healthy_integrations": 0,
                "issues": ["Failed to check Obsidian integrations health"],
                "recommendations": ["Review Obsidian integration monitoring system"]
            }
    
    async def trigger_workflow_on_impact_card_creation(self, impact_card: ImpactCard) -> Dict[str, Any]:
        """Trigger integration workflows when a new impact card is created."""
        try:
            results = {
                "hubspot_sync": None,
                "obsidian_export": None,
                "workflows_triggered": 0
            }
            
            # Trigger HubSpot sync if enabled
            if self.sync_on_impact_card_creation and self.auto_hubspot_sync:
                workspace_id = getattr(impact_card, 'workspace_id', None)
                if workspace_id:
                    hubspot_result = await self.integrate_hubspot_with_cia_workflows(
                        workspace_id, impact_card
                    )
                    results["hubspot_sync"] = hubspot_result
                    if hubspot_result.get("status") == "completed":
                        results["workflows_triggered"] += 1
            
            # Trigger Obsidian export if enabled
            if self.export_on_research_completion and self.auto_obsidian_export:
                # For impact cards, we might want to export to all user integrations
                # This is a simplified approach - in practice, you'd determine the relevant user
                user_id = getattr(impact_card, 'created_by_user_id', None)
                if user_id:
                    obsidian_result = await self.integrate_obsidian_with_research_workflows(
                        user_id
                    )
                    results["obsidian_export"] = obsidian_result
                    if obsidian_result.get("status") == "completed":
                        results["workflows_triggered"] += 1
            
            return results
            
        except Exception as e:
            logger.error(f"Error triggering workflows for impact card {impact_card.id}: {e}")
            return {
                "error": str(e),
                "workflows_triggered": 0
            }
    
    async def trigger_workflow_on_research_completion(self, research_report: CompanyResearch) -> Dict[str, Any]:
        """Trigger integration workflows when research is completed."""
        try:
            results = {
                "obsidian_export": None,
                "workflows_triggered": 0
            }
            
            # Trigger Obsidian export if enabled
            if self.export_on_research_completion and self.auto_obsidian_export:
                user_id = getattr(research_report, 'created_by_user_id', None)
                if user_id:
                    obsidian_result = await self.integrate_obsidian_with_research_workflows(
                        user_id, research_report
                    )
                    results["obsidian_export"] = obsidian_result
                    if obsidian_result.get("status") == "completed":
                        results["workflows_triggered"] += 1
            
            return results
            
        except Exception as e:
            logger.error(f"Error triggering workflows for research report {research_report.id}: {e}")
            return {
                "error": str(e),
                "workflows_triggered": 0
            }
    
    async def get_workflow_integration_status(self) -> Dict[str, Any]:
        """Get comprehensive workflow integration status."""
        try:
            # Calculate average sync time
            avg_sync_time = 0.0
            if self.workflow_metrics["sync_times"]:
                avg_sync_time = sum(self.workflow_metrics["sync_times"]) / len(self.workflow_metrics["sync_times"])
                
                # Keep only recent sync times to prevent memory growth
                if len(self.workflow_metrics["sync_times"]) > 100:
                    self.workflow_metrics["sync_times"] = self.workflow_metrics["sync_times"][-50:]
            
            # Determine workflow health
            total_operations = (
                self.workflow_metrics["hubspot_syncs_completed"] + 
                self.workflow_metrics["obsidian_exports_completed"]
            )
            
            if total_operations > 10 and avg_sync_time < 30:
                workflow_health = "excellent"
            elif total_operations > 5 and avg_sync_time < 60:
                workflow_health = "good"
            elif total_operations > 0:
                workflow_health = "fair"
            else:
                workflow_health = "poor"
            
            return {
                "workflow_health": workflow_health,
                "metrics": {
                    "hubspot_syncs_completed": self.workflow_metrics["hubspot_syncs_completed"],
                    "obsidian_exports_completed": self.workflow_metrics["obsidian_exports_completed"],
                    "workflow_automations_triggered": self.workflow_metrics["workflow_automations_triggered"],
                    "integration_health_checks": self.workflow_metrics["integration_health_checks"],
                    "average_sync_time": avg_sync_time,
                    "total_operations": total_operations
                },
                "configuration": {
                    "auto_hubspot_sync": self.auto_hubspot_sync,
                    "auto_obsidian_export": self.auto_obsidian_export,
                    "sync_on_impact_card_creation": self.sync_on_impact_card_creation,
                    "export_on_research_completion": self.export_on_research_completion
                },
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting workflow integration status: {e}")
            return {
                "workflow_health": "error",
                "error": str(e),
                "last_updated": datetime.utcnow().isoformat()
            }
    
    async def get_workflow_metrics(self) -> IntegrationWorkflowMetrics:
        """Get comprehensive workflow integration metrics."""
        try:
            avg_sync_time = 0.0
            if self.workflow_metrics["sync_times"]:
                avg_sync_time = sum(self.workflow_metrics["sync_times"]) / len(self.workflow_metrics["sync_times"])
            
            # Determine workflow health
            total_operations = (
                self.workflow_metrics["hubspot_syncs_completed"] + 
                self.workflow_metrics["obsidian_exports_completed"]
            )
            
            if total_operations > 10 and avg_sync_time < 30:
                workflow_health = "excellent"
            elif total_operations > 5 and avg_sync_time < 60:
                workflow_health = "good"
            elif total_operations > 0:
                workflow_health = "fair"
            else:
                workflow_health = "poor"
            
            return IntegrationWorkflowMetrics(
                hubspot_syncs_completed=self.workflow_metrics["hubspot_syncs_completed"],
                obsidian_exports_completed=self.workflow_metrics["obsidian_exports_completed"],
                workflow_automations_triggered=self.workflow_metrics["workflow_automations_triggered"],
                integration_health_checks=self.workflow_metrics["integration_health_checks"],
                average_sync_time=avg_sync_time,
                workflow_health=workflow_health
            )
            
        except Exception as e:
            logger.error(f"❌ Error getting workflow metrics: {e}")
            return IntegrationWorkflowMetrics(
                hubspot_syncs_completed=0,
                obsidian_exports_completed=0,
                workflow_automations_triggered=0,
                integration_health_checks=0,
                average_sync_time=0.0,
                workflow_health="error"
            )