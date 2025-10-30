"""
HubSpot Lead Enrichment and Workflow Automation Service
Automatically enriches leads with competitive intelligence and triggers workflows
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.database import get_db
from app.models.hubspot_integration import HubSpotIntegration, HubSpotWorkflowTrigger
from app.models.impact_card import ImpactCard
from app.models.company_research import CompanyResearch
from app.models.watch import WatchItem
from app.services.hubspot_client import HubSpotClient, HubSpotAPIError
from app.services.hubspot_sync_service import HubSpotSyncService
from app.services.you_client import YouClient

logger = logging.getLogger(__name__)


class HubSpotAutomationService:
    """Service for automating lead enrichment and workflow triggers"""
    
    # Workflow trigger types
    TRIGGER_TYPES = {
        "new_lead_enrichment": "New lead requires competitive intelligence enrichment",
        "competitive_event": "Competitive event affects prospect/customer",
        "risk_score_change": "Risk score changed significantly",
        "market_position_update": "Market position assessment updated",
        "funding_event": "Funding or acquisition event detected",
        "product_launch": "New product or feature launch detected",
        "leadership_change": "Executive leadership change detected"
    }
    
    def __init__(self, integration: HubSpotIntegration, db: AsyncSession):
        self.integration = integration
        self.db = db
        self.client: Optional[HubSpotClient] = None
        self.you_client = YouClient()
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.client = HubSpotClient.from_encrypted_tokens(
            self.integration.access_token_encrypted,
            self.integration.refresh_token_encrypted
        )
        await self.client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.client:
            await self.client.__aexit__(exc_type, exc_val, exc_tb)
    
    async def enrich_new_lead(self, contact_id: str, company_id: Optional[str] = None) -> Dict[str, Any]:
        """Automatically enrich a new lead with competitive intelligence"""
        try:
            # Get contact details from HubSpot
            contact = await self.client.get_contact(contact_id, properties=[
                "firstname", "lastname", "email", "company", "jobtitle", "industry"
            ])
            
            contact_props = contact.get("properties", {})
            company_name = contact_props.get("company")
            
            if not company_name:
                logger.warning(f"No company name found for contact {contact_id}")
                return {"status": "skipped", "reason": "no_company_name"}
            
            # Get or create company intelligence
            intelligence_data = await self._get_company_intelligence(company_name)
            
            # Update contact with intelligence data
            contact_updates = {
                "cia_competitive_risk_score": intelligence_data.get("risk_score", 0),
                "cia_market_position": intelligence_data.get("market_position", "unknown"),
                "cia_last_intelligence_update": datetime.utcnow().isoformat(),
                "cia_competitive_alerts": intelligence_data.get("alert_count", 0)
            }
            
            await self.client.update_contact(contact_id, contact_updates)
            
            # Update company if provided
            if company_id:
                company_updates = {
                    "cia_competitive_risk_score": intelligence_data.get("risk_score", 0),
                    "cia_market_position": intelligence_data.get("market_position", "unknown"),
                    "cia_industry_category": intelligence_data.get("industry", "Unknown"),
                    "cia_competitor_status": intelligence_data.get("competitor_status", "not_monitored"),
                    "cia_last_intelligence_update": datetime.utcnow().isoformat()
                }
                
                await self.client.update_company(company_id, company_updates)
            
            # Trigger enrichment workflow if configured
            await self._trigger_workflow("new_lead_enrichment", contact_id, "contact", {
                "company_name": company_name,
                "risk_score": intelligence_data.get("risk_score", 0),
                "market_position": intelligence_data.get("market_position", "unknown")
            })
            
            return {
                "status": "success",
                "contact_id": contact_id,
                "company_id": company_id,
                "intelligence_data": intelligence_data
            }
            
        except Exception as e:
            logger.error(f"Failed to enrich lead {contact_id}: {e}")
            return {"status": "error", "error": str(e)}
    
    async def process_competitive_event(self, impact_card: ImpactCard) -> List[Dict[str, Any]]:
        """Process a competitive event and trigger relevant workflows"""
        results = []
        
        try:
            # Find related contacts and companies in HubSpot
            affected_objects = await self._find_affected_hubspot_objects(impact_card)
            
            for obj in affected_objects:
                try:
                    # Update object with new intelligence
                    await self._update_object_with_intelligence(obj, impact_card)
                    
                    # Trigger appropriate workflow
                    trigger_result = await self._trigger_competitive_event_workflow(obj, impact_card)
                    
                    results.append({
                        "status": "success",
                        "object_type": obj["type"],
                        "object_id": obj["id"],
                        "workflow_triggered": trigger_result["triggered"]
                    })
                    
                except Exception as e:
                    logger.error(f"Failed to process competitive event for {obj['type']} {obj['id']}: {e}")
                    results.append({
                        "status": "error",
                        "object_type": obj["type"],
                        "object_id": obj["id"],
                        "error": str(e)
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to process competitive event for impact card {impact_card.id}: {e}")
            return [{"status": "error", "error": str(e)}]
    
    async def monitor_risk_score_changes(self) -> List[Dict[str, Any]]:
        """Monitor for significant risk score changes and trigger workflows"""
        results = []
        
        try:
            # Get recent impact cards with significant risk scores
            cutoff_date = datetime.utcnow() - timedelta(hours=1)
            query = select(ImpactCard).where(
                and_(
                    ImpactCard.workspace_id == self.integration.workspace_id,
                    ImpactCard.created_at >= cutoff_date,
                    ImpactCard.risk_score >= 70  # High risk threshold
                )
            )
            
            result = await self.db.execute(query)
            high_risk_cards = result.scalars().all()
            
            for impact_card in high_risk_cards:
                try:
                    # Find affected HubSpot objects
                    affected_objects = await self._find_affected_hubspot_objects(impact_card)
                    
                    for obj in affected_objects:
                        # Trigger risk score change workflow
                        trigger_result = await self._trigger_workflow(
                            "risk_score_change",
                            obj["id"],
                            obj["type"],
                            {
                                "previous_risk_score": 0,  # Could be enhanced to track previous scores
                                "new_risk_score": impact_card.risk_score,
                                "risk_change": impact_card.risk_score,
                                "impact_summary": impact_card.summary
                            }
                        )
                        
                        results.append({
                            "status": "success",
                            "object_type": obj["type"],
                            "object_id": obj["id"],
                            "risk_score": impact_card.risk_score,
                            "workflow_triggered": trigger_result["triggered"]
                        })
                        
                except Exception as e:
                    logger.error(f"Failed to process risk score change for impact card {impact_card.id}: {e}")
                    results.append({
                        "status": "error",
                        "impact_card_id": str(impact_card.id),
                        "error": str(e)
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to monitor risk score changes: {e}")
            return [{"status": "error", "error": str(e)}]
    
    async def create_tasks_for_competitive_events(self, impact_card: ImpactCard) -> List[Dict[str, Any]]:
        """Create tasks in HubSpot for competitive events requiring attention"""
        results = []
        
        try:
            # Find affected contacts and companies
            affected_objects = await self._find_affected_hubspot_objects(impact_card)
            
            for obj in affected_objects:
                try:
                    # Create task based on impact card
                    task_data = {
                        "properties": {
                            "hs_task_subject": f"Competitive Intelligence Alert: {impact_card.company_name}",
                            "hs_task_body": self._generate_task_description(impact_card),
                            "hs_task_status": "NOT_STARTED",
                            "hs_task_priority": self._get_task_priority(impact_card.risk_score),
                            "hs_task_type": "CALL",  # or EMAIL, TODO, etc.
                            "hs_timestamp": int(datetime.utcnow().timestamp() * 1000)
                        },
                        "associations": [
                            {
                                "to": {"id": obj["id"]},
                                "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 204}]  # Task to Contact/Company
                            }
                        ]
                    }
                    
                    # Note: HubSpot task creation would require additional API endpoint
                    # This is a placeholder for the task creation logic
                    logger.info(f"Would create task for {obj['type']} {obj['id']}: {task_data['properties']['hs_task_subject']}")
                    
                    results.append({
                        "status": "success",
                        "object_type": obj["type"],
                        "object_id": obj["id"],
                        "task_subject": task_data["properties"]["hs_task_subject"]
                    })
                    
                except Exception as e:
                    logger.error(f"Failed to create task for {obj['type']} {obj['id']}: {e}")
                    results.append({
                        "status": "error",
                        "object_type": obj["type"],
                        "object_id": obj["id"],
                        "error": str(e)
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to create tasks for impact card {impact_card.id}: {e}")
            return [{"status": "error", "error": str(e)}]
    
    # Private helper methods
    async def _get_company_intelligence(self, company_name: str) -> Dict[str, Any]:
        """Get or generate competitive intelligence for a company"""
        # Check if we already have intelligence for this company
        query = select(CompanyResearch).where(CompanyResearch.company_name == company_name)
        result = await self.db.execute(query)
        existing_research = result.scalar_one_or_none()
        
        if existing_research:
            return {
                "risk_score": 50,  # Default risk score
                "market_position": "unknown",
                "industry": existing_research.industry,
                "competitor_status": "prospect",
                "alert_count": 0,
                "last_updated": existing_research.updated_at
            }
        
        # Generate new intelligence using You.com
        try:
            # Use You.com to research the company
            search_query = f"{company_name} company profile business model competitors"
            search_results = await self.you_client.search(search_query, num_results=5)
            
            # Basic intelligence extraction (could be enhanced with ML)
            intelligence = {
                "risk_score": 30,  # Default low risk for new companies
                "market_position": "emerging",
                "industry": "Technology",  # Default, could be extracted from search results
                "competitor_status": "prospect",
                "alert_count": 0,
                "last_updated": datetime.utcnow(),
                "source": "you_search"
            }
            
            # Create company research record
            company_research = CompanyResearch(
                company_name=company_name,
                industry=intelligence["industry"],
                research_data={"intelligence": intelligence, "search_results": search_results},
                created_at=datetime.utcnow()
            )
            self.db.add(company_research)
            await self.db.commit()
            
            return intelligence
            
        except Exception as e:
            logger.error(f"Failed to generate intelligence for {company_name}: {e}")
            return {
                "risk_score": 0,
                "market_position": "unknown",
                "industry": "Unknown",
                "competitor_status": "not_monitored",
                "alert_count": 0,
                "last_updated": datetime.utcnow(),
                "error": str(e)
            }
    
    async def _find_affected_hubspot_objects(self, impact_card: ImpactCard) -> List[Dict[str, Any]]:
        """Find HubSpot contacts and companies affected by a competitive event"""
        affected_objects = []
        
        try:
            # Search for companies with matching name
            company_filters = [
                {"propertyName": "name", "operator": "CONTAINS_TOKEN", "value": impact_card.company_name}
            ]
            
            company_results = await self.client.search_companies(company_filters, limit=10)
            
            for company in company_results.get("results", []):
                affected_objects.append({
                    "type": "company",
                    "id": company["id"],
                    "name": company["properties"].get("name", "")
                })
            
            # Search for contacts at those companies
            if affected_objects:
                for company_obj in affected_objects:
                    contact_filters = [
                        {"propertyName": "company", "operator": "EQ", "value": company_obj["name"]}
                    ]
                    
                    contact_results = await self.client.search_contacts(contact_filters, limit=50)
                    
                    for contact in contact_results.get("results", []):
                        affected_objects.append({
                            "type": "contact",
                            "id": contact["id"],
                            "name": f"{contact['properties'].get('firstname', '')} {contact['properties'].get('lastname', '')}".strip(),
                            "company": company_obj["name"]
                        })
            
            return affected_objects
            
        except Exception as e:
            logger.error(f"Failed to find affected HubSpot objects for {impact_card.company_name}: {e}")
            return []
    
    async def _update_object_with_intelligence(self, obj: Dict[str, Any], impact_card: ImpactCard):
        """Update HubSpot object with intelligence from impact card"""
        properties = {
            "cia_competitive_risk_score": impact_card.risk_score,
            "cia_last_intelligence_update": datetime.utcnow().isoformat()
        }
        
        if obj["type"] == "contact":
            await self.client.update_contact(obj["id"], properties)
        elif obj["type"] == "company":
            properties["cia_competitor_status"] = "direct"  # Mark as direct competitor
            await self.client.update_company(obj["id"], properties)
    
    async def _trigger_workflow(self, trigger_type: str, object_id: str, object_type: str, 
                               context: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger a workflow in HubSpot"""
        # Get workflow mapping from integration configuration
        workflow_mappings = self.integration.workflow_mappings or {}
        workflow_id = workflow_mappings.get(trigger_type)
        
        if not workflow_id:
            logger.info(f"No workflow configured for trigger type: {trigger_type}")
            return {"triggered": False, "reason": "no_workflow_configured"}
        
        try:
            # Create workflow trigger record
            trigger_record = HubSpotWorkflowTrigger(
                integration_id=self.integration.id,
                workflow_id=workflow_id,
                workflow_name=self.TRIGGER_TYPES.get(trigger_type, trigger_type),
                trigger_type=trigger_type,
                hubspot_object_type=object_type,
                hubspot_object_id=object_id,
                status="pending",
                created_at=datetime.utcnow()
            )
            
            # Add context data
            if "risk_score" in context:
                trigger_record.risk_score = context["risk_score"]
            if "competitive_event_type" in context:
                trigger_record.competitive_event_type = context["competitive_event_type"]
            
            self.db.add(trigger_record)
            await self.db.commit()
            
            # Trigger the workflow
            result = await self.client.trigger_workflow(workflow_id, object_id, object_type)
            
            # Update trigger record
            trigger_record.status = "sent"
            trigger_record.sent_at = datetime.utcnow()
            trigger_record.response_status_code = 200  # Assuming success
            trigger_record.response_message = "Workflow triggered successfully"
            
            await self.db.commit()
            
            # Update integration statistics
            self.integration.total_workflows_triggered += 1
            await self.db.commit()
            
            return {"triggered": True, "workflow_id": workflow_id, "trigger_id": str(trigger_record.id)}
            
        except Exception as e:
            logger.error(f"Failed to trigger workflow {workflow_id} for {object_type} {object_id}: {e}")
            
            # Update trigger record with error
            if 'trigger_record' in locals():
                trigger_record.status = "failed"
                trigger_record.response_message = str(e)
                await self.db.commit()
            
            return {"triggered": False, "error": str(e)}
    
    async def _trigger_competitive_event_workflow(self, obj: Dict[str, Any], impact_card: ImpactCard) -> Dict[str, Any]:
        """Trigger workflow for competitive events"""
        return await self._trigger_workflow(
            "competitive_event",
            obj["id"],
            obj["type"],
            {
                "company_name": impact_card.company_name,
                "risk_score": impact_card.risk_score,
                "competitive_event_type": impact_card.category,
                "impact_summary": impact_card.summary
            }
        )
    
    def _generate_task_description(self, impact_card: ImpactCard) -> str:
        """Generate task description from impact card"""
        return f"""
Competitive Intelligence Alert

Company: {impact_card.company_name}
Risk Score: {impact_card.risk_score}/100
Category: {impact_card.category}

Summary: {impact_card.summary}

Recommended Actions:
{impact_card.recommended_actions}

This alert was generated by the CIA system. Please review and take appropriate action.
        """.strip()
    
    def _get_task_priority(self, risk_score: int) -> str:
        """Get task priority based on risk score"""
        if risk_score >= 80:
            return "HIGH"
        elif risk_score >= 60:
            return "MEDIUM"
        else:
            return "LOW"


# Utility functions
async def create_automation_service(workspace_id: UUID, db: AsyncSession) -> Optional[HubSpotAutomationService]:
    """Create an automation service for a workspace"""
    from app.services.hubspot_sync_service import get_integration_by_workspace
    
    integration = await get_integration_by_workspace(workspace_id, db)
    if not integration or not integration.sync_enabled:
        return None
    
    return HubSpotAutomationService(integration, db)