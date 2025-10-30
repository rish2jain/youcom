"""
HubSpot Data Synchronization Service
Handles bidirectional sync between CIA and HubSpot CRM
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.database import get_db
from app.models.hubspot_integration import (
    HubSpotIntegration, HubSpotSyncLog, HubSpotCustomProperty
)
from app.models.impact_card import ImpactCard
from app.models.company_research import CompanyResearch
from app.models.watch import WatchItem
from app.services.hubspot_client import HubSpotClient, HubSpotAPIError, HubSpotAuthError
from app.services.encryption_service import encryption_service

logger = logging.getLogger(__name__)


class HubSpotSyncConflictError(Exception):
    """Raised when there's a conflict during synchronization"""
    pass


class HubSpotSyncService:
    """Service for synchronizing data between CIA and HubSpot"""
    
    # Default custom properties to create in HubSpot
    DEFAULT_CONTACT_PROPERTIES = [
        {
            "name": "cia_competitive_risk_score",
            "label": "CIA Competitive Risk Score",
            "description": "Risk score from CIA competitive intelligence (0-100)",
            "type": "number",
            "fieldType": "number"
        },
        {
            "name": "cia_market_position",
            "label": "CIA Market Position",
            "description": "Market position assessment from CIA",
            "type": "enumeration",
            "fieldType": "select",
            "options": [
                {"label": "Market Leader", "value": "leader"},
                {"label": "Strong Competitor", "value": "strong"},
                {"label": "Emerging Player", "value": "emerging"},
                {"label": "Niche Player", "value": "niche"},
                {"label": "Unknown", "value": "unknown"}
            ]
        },
        {
            "name": "cia_last_intelligence_update",
            "label": "CIA Last Intelligence Update",
            "description": "Last time competitive intelligence was updated",
            "type": "datetime",
            "fieldType": "date"
        },
        {
            "name": "cia_competitive_alerts",
            "label": "CIA Competitive Alerts",
            "description": "Number of active competitive alerts",
            "type": "number",
            "fieldType": "number"
        }
    ]
    
    DEFAULT_COMPANY_PROPERTIES = [
        {
            "name": "cia_competitive_risk_score",
            "label": "CIA Competitive Risk Score",
            "description": "Risk score from CIA competitive intelligence (0-100)",
            "type": "number",
            "fieldType": "number"
        },
        {
            "name": "cia_market_position",
            "label": "CIA Market Position",
            "description": "Market position assessment from CIA",
            "type": "enumeration",
            "fieldType": "select",
            "options": [
                {"label": "Market Leader", "value": "leader"},
                {"label": "Strong Competitor", "value": "strong"},
                {"label": "Emerging Player", "value": "emerging"},
                {"label": "Niche Player", "value": "niche"},
                {"label": "Unknown", "value": "unknown"}
            ]
        },
        {
            "name": "cia_industry_category",
            "label": "CIA Industry Category",
            "description": "Industry category from CIA analysis",
            "type": "string",
            "fieldType": "text"
        },
        {
            "name": "cia_competitor_status",
            "label": "CIA Competitor Status",
            "description": "Whether this company is being monitored as a competitor",
            "type": "enumeration",
            "fieldType": "select",
            "options": [
                {"label": "Direct Competitor", "value": "direct"},
                {"label": "Indirect Competitor", "value": "indirect"},
                {"label": "Partner", "value": "partner"},
                {"label": "Prospect", "value": "prospect"},
                {"label": "Not Monitored", "value": "not_monitored"}
            ]
        },
        {
            "name": "cia_last_intelligence_update",
            "label": "CIA Last Intelligence Update",
            "description": "Last time competitive intelligence was updated",
            "type": "datetime",
            "fieldType": "date"
        }
    ]
    
    def __init__(self, integration: HubSpotIntegration, db: AsyncSession):
        self.integration = integration
        self.db = db
        self.client: Optional[HubSpotClient] = None
    
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
    
    async def setup_custom_properties(self) -> Dict[str, List[str]]:
        """Create custom properties in HubSpot for CIA data"""
        created_properties = {"contacts": [], "companies": []}
        
        try:
            # Get existing properties
            existing_contact_props = await self.client.get_contact_properties()
            existing_company_props = await self.client.get_company_properties()
            
            existing_contact_names = {prop["name"] for prop in existing_contact_props.get("results", [])}
            existing_company_names = {prop["name"] for prop in existing_company_props.get("results", [])}
            
            # Create contact properties
            for prop_config in self.DEFAULT_CONTACT_PROPERTIES:
                if prop_config["name"] not in existing_contact_names:
                    try:
                        await self.client.create_contact_property(prop_config)
                        created_properties["contacts"].append(prop_config["name"])
                        logger.info(f"Created contact property: {prop_config['name']}")
                    except HubSpotAPIError as e:
                        logger.error(f"Failed to create contact property {prop_config['name']}: {e}")
            
            # Create company properties
            for prop_config in self.DEFAULT_COMPANY_PROPERTIES:
                if prop_config["name"] not in existing_company_names:
                    try:
                        await self.client.create_company_property(prop_config)
                        created_properties["companies"].append(prop_config["name"])
                        logger.info(f"Created company property: {prop_config['name']}")
                    except HubSpotAPIError as e:
                        logger.error(f"Failed to create company property {prop_config['name']}: {e}")
            
            # Update integration record
            all_created = created_properties["contacts"] + created_properties["companies"]
            if all_created:
                current_props = self.integration.custom_properties_created or []
                self.integration.custom_properties_created = list(set(current_props + all_created))
                await self.db.commit()
            
            return created_properties
            
        except Exception as e:
            logger.error(f"Error setting up custom properties: {e}")
            raise
    
    async def sync_to_hubspot(self, sync_type: str = "incremental") -> HubSpotSyncLog:
        """Sync CIA data to HubSpot"""
        sync_log = HubSpotSyncLog(
            integration_id=self.integration.id,
            sync_type=sync_type,
            direction="to_hubspot",
            status="running",
            started_at=datetime.utcnow()
        )
        self.db.add(sync_log)
        await self.db.commit()
        
        try:
            records_processed = 0
            records_successful = 0
            records_failed = 0
            
            # Determine sync window
            if sync_type == "full_sync":
                since_date = None
            else:
                since_date = self.integration.last_successful_sync_at or (datetime.utcnow() - timedelta(days=7))
            
            # Sync companies from watch items
            watch_items = await self._get_watch_items_to_sync(since_date)
            for watch_item in watch_items:
                try:
                    await self._sync_watch_item_to_hubspot(watch_item)
                    records_successful += 1
                except Exception as e:
                    logger.error(f"Failed to sync watch item {watch_item.id}: {e}")
                    records_failed += 1
                records_processed += 1
            
            # Sync impact cards as activities/notes
            impact_cards = await self._get_impact_cards_to_sync(since_date)
            for impact_card in impact_cards:
                try:
                    await self._sync_impact_card_to_hubspot(impact_card)
                    records_successful += 1
                except Exception as e:
                    logger.error(f"Failed to sync impact card {impact_card.id}: {e}")
                    records_failed += 1
                records_processed += 1
            
            # Update sync log
            sync_log.status = "success" if records_failed == 0 else "partial_success"
            sync_log.records_processed = records_processed
            sync_log.records_successful = records_successful
            sync_log.records_failed = records_failed
            sync_log.completed_at = datetime.utcnow()
            sync_log.duration_seconds = int((sync_log.completed_at - sync_log.started_at).total_seconds())
            
            # Update integration
            if records_successful > 0:
                self.integration.last_successful_sync_at = datetime.utcnow()
                self.integration.total_companies_synced += len(watch_items)
                self.integration.consecutive_failures = 0
            
            self.integration.last_sync_at = datetime.utcnow()
            
            await self.db.commit()
            return sync_log
            
        except Exception as e:
            sync_log.status = "failure"
            sync_log.error_message = str(e)
            sync_log.completed_at = datetime.utcnow()
            sync_log.duration_seconds = int((sync_log.completed_at - sync_log.started_at).total_seconds())
            
            self.integration.consecutive_failures += 1
            self.integration.last_error_message = str(e)
            
            await self.db.commit()
            raise
    
    async def sync_from_hubspot(self, sync_type: str = "incremental") -> HubSpotSyncLog:
        """Sync data from HubSpot to CIA"""
        sync_log = HubSpotSyncLog(
            integration_id=self.integration.id,
            sync_type=sync_type,
            direction="from_hubspot",
            status="running",
            started_at=datetime.utcnow()
        )
        self.db.add(sync_log)
        await self.db.commit()
        
        try:
            records_processed = 0
            records_successful = 0
            records_failed = 0
            
            # Sync companies from HubSpot
            companies = await self._get_hubspot_companies_to_sync()
            for company in companies:
                try:
                    await self._sync_hubspot_company_to_cia(company)
                    records_successful += 1
                except Exception as e:
                    logger.error(f"Failed to sync HubSpot company {company.get('id')}: {e}")
                    records_failed += 1
                records_processed += 1
            
            # Update sync log
            sync_log.status = "success" if records_failed == 0 else "partial_success"
            sync_log.records_processed = records_processed
            sync_log.records_successful = records_successful
            sync_log.records_failed = records_failed
            sync_log.completed_at = datetime.utcnow()
            sync_log.duration_seconds = int((sync_log.completed_at - sync_log.started_at).total_seconds())
            
            # Update integration
            if records_successful > 0:
                self.integration.last_successful_sync_at = datetime.utcnow()
                self.integration.consecutive_failures = 0
            
            self.integration.last_sync_at = datetime.utcnow()
            
            await self.db.commit()
            return sync_log
            
        except Exception as e:
            sync_log.status = "failure"
            sync_log.error_message = str(e)
            sync_log.completed_at = datetime.utcnow()
            sync_log.duration_seconds = int((sync_log.completed_at - sync_log.started_at).total_seconds())
            
            self.integration.consecutive_failures += 1
            self.integration.last_error_message = str(e)
            
            await self.db.commit()
            raise
    
    async def bidirectional_sync(self, sync_type: str = "incremental") -> Tuple[HubSpotSyncLog, HubSpotSyncLog]:
        """Perform bidirectional synchronization"""
        # First sync CIA data to HubSpot
        to_hubspot_log = await self.sync_to_hubspot(sync_type)
        
        # Then sync HubSpot data to CIA
        from_hubspot_log = await self.sync_from_hubspot(sync_type)
        
        return to_hubspot_log, from_hubspot_log
    
    async def resolve_conflict(self, cia_data: Dict[str, Any], hubspot_data: Dict[str, Any], 
                              conflict_resolution: str = "cia_wins") -> Dict[str, Any]:
        """Resolve data conflicts between CIA and HubSpot"""
        if conflict_resolution == "cia_wins":
            return cia_data
        elif conflict_resolution == "hubspot_wins":
            return hubspot_data
        elif conflict_resolution == "most_recent":
            cia_updated = cia_data.get("updated_at", datetime.min)
            hubspot_updated = hubspot_data.get("updated_at", datetime.min)
            return cia_data if cia_updated > hubspot_updated else hubspot_data
        else:
            # Manual resolution required
            raise HubSpotSyncConflictError(f"Manual conflict resolution required for {conflict_resolution}")
    
    # Private helper methods
    async def _get_watch_items_to_sync(self, since_date: Optional[datetime]) -> List[WatchItem]:
        """Get watch items that need to be synced to HubSpot"""
        query = select(WatchItem).where(WatchItem.workspace_id == self.integration.workspace_id)
        
        if since_date:
            query = query.where(
                or_(
                    WatchItem.created_at >= since_date,
                    WatchItem.updated_at >= since_date
                )
            )
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def _get_impact_cards_to_sync(self, since_date: Optional[datetime]) -> List[ImpactCard]:
        """Get impact cards that need to be synced to HubSpot"""
        query = select(ImpactCard).where(ImpactCard.workspace_id == self.integration.workspace_id)
        
        if since_date:
            query = query.where(
                or_(
                    ImpactCard.created_at >= since_date,
                    ImpactCard.updated_at >= since_date
                )
            )
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def _sync_watch_item_to_hubspot(self, watch_item: WatchItem):
        """Sync a watch item to HubSpot as a company"""
        # Search for existing company
        search_filters = [
            {"propertyName": "name", "operator": "EQ", "value": watch_item.company_name}
        ]
        
        search_result = await self.client.search_companies(search_filters)
        
        # Prepare company properties
        properties = {
            "name": watch_item.company_name,
            "cia_competitor_status": "direct" if watch_item.is_competitor else "prospect",
            "cia_industry_category": watch_item.industry or "Unknown",
            "cia_last_intelligence_update": datetime.utcnow().isoformat()
        }
        
        if search_result.get("results"):
            # Update existing company
            company_id = search_result["results"][0]["id"]
            await self.client.update_company(company_id, properties)
        else:
            # Create new company
            await self.client.create_company(properties)
    
    async def _sync_impact_card_to_hubspot(self, impact_card: ImpactCard):
        """Sync an impact card to HubSpot as a note or activity"""
        # Find related company in HubSpot
        search_filters = [
            {"propertyName": "name", "operator": "EQ", "value": impact_card.company_name}
        ]
        
        search_result = await self.client.search_companies(search_filters)
        
        if search_result.get("results"):
            company_id = search_result["results"][0]["id"]
            
            # Update company with latest risk score
            properties = {
                "cia_competitive_risk_score": impact_card.risk_score,
                "cia_last_intelligence_update": datetime.utcnow().isoformat(),
                "cia_competitive_alerts": 1  # Increment alert count
            }
            
            await self.client.update_company(company_id, properties)
    
    async def _get_hubspot_companies_to_sync(self) -> List[Dict[str, Any]]:
        """Get companies from HubSpot that should be synced to CIA"""
        properties = [
            "name", "domain", "industry", "city", "state", "country",
            "cia_competitor_status", "cia_competitive_risk_score"
        ]
        
        companies = []
        after = None
        
        while True:
            result = await self.client.get_companies(limit=100, after=after, properties=properties)
            companies.extend(result.get("results", []))
            
            paging = result.get("paging", {})
            if not paging.get("next"):
                break
            
            after = paging["next"]["after"]
        
        return companies
    
    async def _sync_hubspot_company_to_cia(self, hubspot_company: Dict[str, Any]):
        """Sync a HubSpot company to CIA as a watch item"""
        properties = hubspot_company.get("properties", {})
        company_name = properties.get("name")
        
        if not company_name:
            return
        
        # Check if watch item already exists
        query = select(WatchItem).where(
            and_(
                WatchItem.workspace_id == self.integration.workspace_id,
                WatchItem.company_name == company_name
            )
        )
        result = await self.db.execute(query)
        existing_watch_item = result.scalar_one_or_none()
        
        if not existing_watch_item:
            # Create new watch item
            watch_item = WatchItem(
                workspace_id=self.integration.workspace_id,
                company_name=company_name,
                industry=properties.get("industry"),
                is_competitor=properties.get("cia_competitor_status") in ["direct", "indirect"],
                created_at=datetime.utcnow()
            )
            self.db.add(watch_item)


# Utility functions for external use
async def get_integration_by_workspace(workspace_id: UUID, db: AsyncSession) -> Optional[HubSpotIntegration]:
    """Get HubSpot integration for a workspace"""
    query = select(HubSpotIntegration).where(HubSpotIntegration.workspace_id == workspace_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_sync_service(workspace_id: UUID, db: AsyncSession) -> Optional[HubSpotSyncService]:
    """Create a sync service for a workspace"""
    integration = await get_integration_by_workspace(workspace_id, db)
    if not integration or not integration.sync_enabled:
        return None
    
    return HubSpotSyncService(integration, db)