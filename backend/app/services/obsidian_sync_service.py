"""
Obsidian Note Synchronization and Update Management Service
"""

import asyncio
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, update
from sqlalchemy.orm import selectinload

from app.models.obsidian_integration import (
    ObsidianIntegration, ObsidianSyncLog, ObsidianNoteMapping, ObsidianNoteTemplate
)
from app.models.impact_card import ImpactCard
from app.models.company_research import CompanyResearch
from app.services.obsidian_client import ObsidianClient, ObsidianVaultError, ObsidianConnectionError
from app.services.obsidian_template_service import ObsidianTemplateService
from app.services.obsidian_markdown_service import MarkdownGenerator


class ObsidianSyncService:
    """Service for synchronizing content with Obsidian vaults"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.template_service = ObsidianTemplateService(db)
        self.markdown_generator = MarkdownGenerator()
    
    async def sync_integration(self, integration_id: str, sync_type: str = "incremental_sync") -> Dict[str, Any]:
        """Perform synchronization for an integration"""
        
        # Get integration details
        result = await self.db.execute(
            select(ObsidianIntegration)
            .options(selectinload(ObsidianIntegration.note_mappings))
            .where(ObsidianIntegration.id == integration_id)
        )
        integration = result.scalar_one_or_none()
        
        if not integration:
            raise ValueError(f"Integration not found: {integration_id}")
        
        if not integration.sync_enabled:
            return {"status": "skipped", "reason": "Sync disabled"}
        
        # Create sync log
        sync_log = ObsidianSyncLog(
            integration_id=integration_id,
            sync_type=sync_type,
            operation="sync",
            status="running",
            started_at=datetime.now(timezone.utc)
        )
        self.db.add(sync_log)
        await self.db.commit()
        
        try:
            # Initialize Obsidian client
            async with ObsidianClient.from_encrypted_credentials(
                vault_path=integration.vault_path,
                api_endpoint=integration.api_endpoint,
                encrypted_api_key=integration.api_key_encrypted,
                api_port=integration.api_port or 27123
            ) as client:
                
                # Perform health check
                health = await client.health_check()
                if health["overall_status"] != "healthy":
                    raise ObsidianConnectionError(f"Vault health check failed: {health['errors']}")
                
                sync_results = {
                    "notes_processed": 0,
                    "notes_created": 0,
                    "notes_updated": 0,
                    "backlinks_created": 0,
                    "errors": []
                }
                
                # Sync different content types
                if sync_type == "full_sync":
                    # Full sync: process all content
                    await self._sync_impact_cards(integration, client, sync_results)
                    await self._sync_company_profiles(integration, client, sync_results)
                    await self._create_index_notes(integration, client, sync_results)
                else:
                    # Incremental sync: only process updated content
                    await self._sync_updated_content(integration, client, sync_results)
                
                # Update integration status
                integration.last_sync_at = datetime.now(timezone.utc)
                integration.last_successful_sync_at = datetime.now(timezone.utc)
                integration.sync_status = "active"
                integration.consecutive_failures = 0
                integration.last_error_message = None
                
                # Update usage statistics
                integration.total_notes_created += sync_results["notes_created"]
                integration.total_notes_updated += sync_results["notes_updated"]
                integration.total_backlinks_created += sync_results["backlinks_created"]
                
                # Complete sync log
                sync_log.status = "success" if not sync_results["errors"] else "partial_success"
                sync_log.completed_at = datetime.now(timezone.utc)
                sync_log.duration_seconds = int((sync_log.completed_at - sync_log.started_at).total_seconds())
                sync_log.notes_processed = sync_results["notes_processed"]
                sync_log.notes_created = sync_results["notes_created"]
                sync_log.notes_updated = sync_results["notes_updated"]
                sync_log.backlinks_created = sync_results["backlinks_created"]
                
                if sync_results["errors"]:
                    sync_log.error_details = {"errors": sync_results["errors"]}
                
                await self.db.commit()
                
                return {
                    "status": "success",
                    "sync_log_id": str(sync_log.id),
                    **sync_results
                }
        
        except Exception as e:
            # Handle sync failure
            integration.consecutive_failures = (integration.consecutive_failures or 0) + 1
            integration.last_error_message = str(e)
            integration.sync_status = "error"
            
            sync_log.status = "failure"
            sync_log.completed_at = datetime.now(timezone.utc)
            sync_log.duration_seconds = int((sync_log.completed_at - sync_log.started_at).total_seconds())
            sync_log.error_message = str(e)
            
            await self.db.commit()
            
            return {
                "status": "failure",
                "error": str(e),
                "sync_log_id": str(sync_log.id)
            }
    
    async def _sync_impact_cards(self, integration: ObsidianIntegration, 
                               client: ObsidianClient, sync_results: Dict[str, Any]):
        """Sync impact cards to Obsidian"""
        
        # Get recent impact cards (last 30 days or all if full sync)
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
        
        result = await self.db.execute(
            select(ImpactCard)
            .where(ImpactCard.created_at >= cutoff_date)
            .order_by(ImpactCard.created_at.desc())
        )
        impact_cards = result.scalars().all()
        
        for impact_card in impact_cards:
            try:
                await self._sync_single_impact_card(integration, client, impact_card, sync_results)
                sync_results["notes_processed"] += 1
            except Exception as e:
                sync_results["errors"].append(f"Failed to sync impact card {impact_card.id}: {str(e)}")
    
    async def _sync_single_impact_card(self, integration: ObsidianIntegration,
                                     client: ObsidianClient, impact_card: ImpactCard,
                                     sync_results: Dict[str, Any]):
        """Sync a single impact card"""
        
        content_id = str(impact_card.id)
        
        # Check if note mapping exists
        result = await self.db.execute(
            select(ObsidianNoteMapping)
            .where(
                and_(
                    ObsidianNoteMapping.integration_id == integration.id,
                    ObsidianNoteMapping.content_type == "impact_card",
                    ObsidianNoteMapping.content_id == content_id
                )
            )
        )
        note_mapping = result.scalar_one_or_none()
        
        # Prepare impact card data
        impact_data = {
            "title": impact_card.title,
            "company_name": impact_card.company_name,
            "severity": impact_card.severity,
            "category": impact_card.category,
            "risk_score": impact_card.risk_score,
            "confidence": impact_card.confidence,
            "summary": impact_card.summary,
            "impact_analysis": impact_card.impact_analysis,
            "recommended_actions": impact_card.recommended_actions or [],
            "evidence": getattr(impact_card, 'evidence', [])
        }
        
        # Generate note content using template
        template = await self.template_service.get_template(integration.id, "impact_card")
        if template:
            note_content = await self.template_service.apply_template(template, impact_data)
        else:
            # Fallback to markdown generator
            note_data = self.markdown_generator.generate_impact_card_note(
                impact_card, 
                include_metadata=integration.include_metadata,
                include_backlinks=integration.enable_backlinks
            )
            note_content = note_data["content"]
        
        # Generate backlinks if enabled
        if integration.enable_backlinks:
            backlinks = await self.template_service.generate_backlinks_for_content("impact_card", impact_data)
            note_content = await self.template_service.create_backlinks_in_content(
                note_content, backlinks, integration.backlink_format
            )
        
        # Determine note path
        folder_template = integration.company_folder_template or "Companies/{company_name}"
        folder_path = folder_template.format(company_name=impact_card.company_name)
        note_filename = f"{impact_card.company_name}_{impact_card.title}".replace(" ", "_")
        note_path = f"{folder_path}/{note_filename}"
        
        # Calculate content hash
        content_hash = hashlib.sha256(note_content.encode('utf-8')).hexdigest()
        
        if note_mapping:
            # Check if content has changed
            if note_mapping.note_hash != content_hash:
                # Update existing note
                await client.update_note(note_mapping.note_path, note_content)
                
                # Update mapping
                note_mapping.note_hash = content_hash
                note_mapping.last_updated_in_obsidian_at = datetime.now(timezone.utc)
                note_mapping.last_synced_at = datetime.now(timezone.utc)
                note_mapping.sync_version += 1
                note_mapping.needs_update = False
                
                sync_results["notes_updated"] += 1
        else:
            # Create new note
            await client.create_note(note_path, note_content)
            
            # Create note mapping
            note_mapping = ObsidianNoteMapping(
                integration_id=integration.id,
                content_type="impact_card",
                content_id=content_id,
                content_title=impact_card.title,
                note_path=note_path,
                note_filename=f"{note_filename}.md",
                note_folder=folder_path,
                note_hash=content_hash,
                created_in_obsidian_at=datetime.now(timezone.utc),
                last_synced_at=datetime.now(timezone.utc),
                sync_version=1
            )
            self.db.add(note_mapping)
            
            sync_results["notes_created"] += 1
        
        # Update backlinks in mapping if enabled
        if integration.enable_backlinks:
            backlinks_to = await self.template_service.extract_backlinks_from_content(note_content)
            await self.template_service.update_note_mapping_backlinks(
                note_mapping, backlinks_to, []
            )
            sync_results["backlinks_created"] += len(backlinks_to)
    
    async def _sync_company_profiles(self, integration: ObsidianIntegration,
                                   client: ObsidianClient, sync_results: Dict[str, Any]):
        """Sync company profiles to Obsidian"""
        
        # Get recent company research
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
        
        result = await self.db.execute(
            select(CompanyResearch)
            .where(CompanyResearch.updated_at >= cutoff_date)
            .order_by(CompanyResearch.updated_at.desc())
        )
        company_profiles = result.scalars().all()
        
        for profile in company_profiles:
            try:
                await self._sync_single_company_profile(integration, client, profile, sync_results)
                sync_results["notes_processed"] += 1
            except Exception as e:
                sync_results["errors"].append(f"Failed to sync company profile {profile.id}: {str(e)}")
    
    async def _sync_single_company_profile(self, integration: ObsidianIntegration,
                                         client: ObsidianClient, profile: CompanyResearch,
                                         sync_results: Dict[str, Any]):
        """Sync a single company profile"""
        
        content_id = str(profile.id)
        
        # Check if note mapping exists
        result = await self.db.execute(
            select(ObsidianNoteMapping)
            .where(
                and_(
                    ObsidianNoteMapping.integration_id == integration.id,
                    ObsidianNoteMapping.content_type == "company_profile",
                    ObsidianNoteMapping.content_id == content_id
                )
            )
        )
        note_mapping = result.scalar_one_or_none()
        
        # Generate note content using template
        template = await self.template_service.get_template(integration.id, "company_profile")
        if template:
            profile_data = {
                "company_name": profile.company_name,
                "industry": profile.industry,
                "founded_year": profile.founded_year,
                "employee_count": profile.employee_count,
                "headquarters": profile.headquarters,
                "website": profile.website,
                "description": profile.description,
                "products": profile.products or [],
                "key_people": profile.key_people or [],
                "competitive_position": profile.competitive_position
            }
            note_content = await self.template_service.apply_template(template, profile_data)
        else:
            # Fallback to markdown generator
            note_data = self.markdown_generator.generate_company_profile_note(
                profile,
                include_metadata=integration.include_metadata,
                include_backlinks=integration.enable_backlinks
            )
            note_content = note_data["content"]
        
        # Generate backlinks if enabled
        if integration.enable_backlinks:
            backlinks = await self.template_service.generate_backlinks_for_content("company_profile", profile_data)
            note_content = await self.template_service.create_backlinks_in_content(
                note_content, backlinks, integration.backlink_format
            )
        
        # Determine note path
        folder_template = integration.company_folder_template or "Companies/{company_name}"
        folder_path = folder_template.format(company_name=profile.company_name)
        note_filename = f"{profile.company_name}_Profile".replace(" ", "_")
        note_path = f"{folder_path}/{note_filename}"
        
        # Calculate content hash
        content_hash = hashlib.sha256(note_content.encode('utf-8')).hexdigest()
        
        if note_mapping:
            # Check if content has changed
            if note_mapping.note_hash != content_hash:
                # Update existing note
                await client.update_note(note_mapping.note_path, note_content)
                
                # Update mapping
                note_mapping.note_hash = content_hash
                note_mapping.last_updated_in_obsidian_at = datetime.now(timezone.utc)
                note_mapping.last_synced_at = datetime.now(timezone.utc)
                note_mapping.sync_version += 1
                note_mapping.needs_update = False
                
                sync_results["notes_updated"] += 1
        else:
            # Create new note
            await client.create_note(note_path, note_content)
            
            # Create note mapping
            note_mapping = ObsidianNoteMapping(
                integration_id=integration.id,
                content_type="company_profile",
                content_id=content_id,
                content_title=f"{profile.company_name} Profile",
                note_path=note_path,
                note_filename=f"{note_filename}.md",
                note_folder=folder_path,
                note_hash=content_hash,
                created_in_obsidian_at=datetime.now(timezone.utc),
                last_synced_at=datetime.now(timezone.utc),
                sync_version=1
            )
            self.db.add(note_mapping)
            
            sync_results["notes_created"] += 1
        
        # Update backlinks in mapping if enabled
        if integration.enable_backlinks:
            backlinks_to = await self.template_service.extract_backlinks_from_content(note_content)
            await self.template_service.update_note_mapping_backlinks(
                note_mapping, backlinks_to, []
            )
            sync_results["backlinks_created"] += len(backlinks_to)
    
    async def _sync_updated_content(self, integration: ObsidianIntegration,
                                  client: ObsidianClient, sync_results: Dict[str, Any]):
        """Sync only content that has been updated since last sync"""
        
        last_sync = integration.last_successful_sync_at or datetime.now(timezone.utc) - timedelta(days=1)
        
        # Find notes that need updates
        result = await self.db.execute(
            select(ObsidianNoteMapping)
            .where(
                and_(
                    ObsidianNoteMapping.integration_id == integration.id,
                    ObsidianNoteMapping.needs_update == True
                )
            )
        )
        mappings_to_update = result.scalars().all()
        
        for mapping in mappings_to_update:
            try:
                if mapping.content_type == "impact_card":
                    # Get the impact card
                    result = await self.db.execute(
                        select(ImpactCard).where(ImpactCard.id == int(mapping.content_id))
                    )
                    impact_card = result.scalar_one_or_none()
                    if impact_card:
                        await self._sync_single_impact_card(integration, client, impact_card, sync_results)
                
                elif mapping.content_type == "company_profile":
                    # Get the company profile
                    result = await self.db.execute(
                        select(CompanyResearch).where(CompanyResearch.id == int(mapping.content_id))
                    )
                    profile = result.scalar_one_or_none()
                    if profile:
                        await self._sync_single_company_profile(integration, client, profile, sync_results)
                
                sync_results["notes_processed"] += 1
                
            except Exception as e:
                sync_results["errors"].append(f"Failed to update note {mapping.note_path}: {str(e)}")
    
    async def _create_index_notes(self, integration: ObsidianIntegration,
                                client: ObsidianClient, sync_results: Dict[str, Any]):
        """Create index notes for better organization"""
        
        if not integration.auto_create_index:
            return
        
        try:
            # Create main index
            await self._create_main_index(integration, client)
            
            # Create company index
            await self._create_company_index(integration, client)
            
            # Create category indices
            await self._create_category_indices(integration, client)
            
            sync_results["notes_created"] += 3  # Approximate
            
        except Exception as e:
            sync_results["errors"].append(f"Failed to create index notes: {str(e)}")
    
    async def _create_main_index(self, integration: ObsidianIntegration, client: ObsidianClient):
        """Create main competitive intelligence index"""
        
        # Get all note mappings
        result = await self.db.execute(
            select(ObsidianNoteMapping)
            .where(
                and_(
                    ObsidianNoteMapping.integration_id == integration.id,
                    ObsidianNoteMapping.is_active == True
                )
            )
            .order_by(ObsidianNoteMapping.created_in_obsidian_at.desc())
        )
        mappings = result.scalars().all()
        
        # Group by content type
        content_groups = {}
        for mapping in mappings:
            if mapping.content_type not in content_groups:
                content_groups[mapping.content_type] = []
            content_groups[mapping.content_type].append(mapping)
        
        # Generate index content
        index_content = f"""# Competitive Intelligence Index

*Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}*

## Overview

This vault contains {len(mappings)} competitive intelligence notes organized by type and company.

"""
        
        for content_type, items in content_groups.items():
            index_content += f"## {content_type.replace('_', ' ').title()} ({len(items)} notes)\n\n"
            
            for item in items[:10]:  # Limit to 10 most recent
                if integration.backlink_format == "wikilink":
                    link = f"- [[{item.note_path}|{item.content_title}]]"
                else:
                    link = f"- [{item.content_title}]({item.note_path}.md)"
                index_content += f"{link}\n"
            
            if len(items) > 10:
                index_content += f"- ... and {len(items) - 10} more\n"
            
            index_content += "\n"
        
        # Create or update index note
        index_path = f"{integration.base_folder}/Index"
        await client.create_note(index_path, index_content, overwrite=True)
    
    async def _create_company_index(self, integration: ObsidianIntegration, client: ObsidianClient):
        """Create company-specific index"""
        
        # Get company mappings
        result = await self.db.execute(
            select(ObsidianNoteMapping)
            .where(
                and_(
                    ObsidianNoteMapping.integration_id == integration.id,
                    ObsidianNoteMapping.is_active == True
                )
            )
        )
        mappings = result.scalars().all()
        
        # Group by company (extract from note folder)
        company_groups = {}
        for mapping in mappings:
            # Extract company name from folder path
            if mapping.note_folder and "Companies/" in mapping.note_folder:
                company_name = mapping.note_folder.split("Companies/")[1].split("/")[0]
                if company_name not in company_groups:
                    company_groups[company_name] = []
                company_groups[company_name].append(mapping)
        
        # Create index for each company with multiple notes
        for company_name, items in company_groups.items():
            if len(items) > 1:  # Only create index if multiple notes exist
                index_content = f"""# {company_name} - Competitive Intelligence

*Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}*

## Notes ({len(items)})

"""
                
                for item in items:
                    if integration.backlink_format == "wikilink":
                        link = f"- [[{item.note_path}|{item.content_title}]]"
                    else:
                        link = f"- [{item.content_title}]({item.note_path}.md)"
                    index_content += f"{link}\n"
                
                # Create company index
                index_path = f"Companies/{company_name}/Index"
                await client.create_note(index_path, index_content, overwrite=True)
    
    async def _create_category_indices(self, integration: ObsidianIntegration, client: ObsidianClient):
        """Create category-based indices"""
        
        # Get impact card mappings
        result = await self.db.execute(
            select(ObsidianNoteMapping)
            .where(
                and_(
                    ObsidianNoteMapping.integration_id == integration.id,
                    ObsidianNoteMapping.content_type == "impact_card",
                    ObsidianNoteMapping.is_active == True
                )
            )
        )
        mappings = result.scalars().all()
        
        # Get corresponding impact cards to extract categories
        content_ids = [mapping.content_id for mapping in mappings]
        result = await self.db.execute(
            select(ImpactCard).where(ImpactCard.id.in_(content_ids))
        )
        impact_cards = result.scalars().all()
        
        # Group by category
        category_groups = {}
        for impact_card in impact_cards:
            category = impact_card.category
            if category not in category_groups:
                category_groups[category] = []
            
            # Find corresponding mapping
            mapping = next((m for m in mappings if m.content_id == str(impact_card.id)), None)
            if mapping:
                category_groups[category].append({
                    "mapping": mapping,
                    "impact_card": impact_card
                })
        
        # Create index for each category
        for category, items in category_groups.items():
            if len(items) > 1:  # Only create index if multiple items exist
                index_content = f"""# {category} - Impact Analysis

*Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}*

## Impact Cards ({len(items)})

"""
                
                # Sort by risk score (highest first)
                items.sort(key=lambda x: x["impact_card"].risk_score, reverse=True)
                
                for item in items:
                    mapping = item["mapping"]
                    impact_card = item["impact_card"]
                    
                    if integration.backlink_format == "wikilink":
                        link = f"- [[{mapping.note_path}|{mapping.content_title}]] (Risk: {impact_card.risk_score}/100)"
                    else:
                        link = f"- [{mapping.content_title}]({mapping.note_path}.md) (Risk: {impact_card.risk_score}/100)"
                    index_content += f"{link}\n"
                
                # Create category index
                index_path = f"Impact Cards/{category}/Index"
                await client.create_note(index_path, index_content, overwrite=True)
    
    async def mark_content_for_update(self, integration_id: str, content_type: str, content_id: str):
        """Mark content as needing update in Obsidian"""
        
        result = await self.db.execute(
            select(ObsidianNoteMapping)
            .where(
                and_(
                    ObsidianNoteMapping.integration_id == integration_id,
                    ObsidianNoteMapping.content_type == content_type,
                    ObsidianNoteMapping.content_id == content_id
                )
            )
        )
        mapping = result.scalar_one_or_none()
        
        if mapping:
            mapping.needs_update = True
            await self.db.commit()
    
    async def get_sync_status(self, integration_id: str) -> Dict[str, Any]:
        """Get synchronization status for an integration"""
        
        # Get integration
        result = await self.db.execute(
            select(ObsidianIntegration).where(ObsidianIntegration.id == integration_id)
        )
        integration = result.scalar_one_or_none()
        
        if not integration:
            return {"error": "Integration not found"}
        
        # Get recent sync logs
        result = await self.db.execute(
            select(ObsidianSyncLog)
            .where(ObsidianSyncLog.integration_id == integration_id)
            .order_by(ObsidianSyncLog.started_at.desc())
            .limit(10)
        )
        recent_logs = result.scalars().all()
        
        # Get note mappings count
        result = await self.db.execute(
            select(ObsidianNoteMapping)
            .where(
                and_(
                    ObsidianNoteMapping.integration_id == integration_id,
                    ObsidianNoteMapping.is_active == True
                )
            )
        )
        active_mappings = result.scalars().all()
        
        # Count notes needing update
        pending_updates = len([m for m in active_mappings if m.needs_update])
        
        return {
            "integration_id": integration_id,
            "sync_enabled": integration.sync_enabled,
            "sync_status": integration.sync_status,
            "last_sync_at": integration.last_sync_at.isoformat() if integration.last_sync_at else None,
            "last_successful_sync_at": integration.last_successful_sync_at.isoformat() if integration.last_successful_sync_at else None,
            "consecutive_failures": integration.consecutive_failures,
            "last_error_message": integration.last_error_message,
            "total_notes": len(active_mappings),
            "pending_updates": pending_updates,
            "usage_stats": {
                "total_notes_created": integration.total_notes_created,
                "total_notes_updated": integration.total_notes_updated,
                "total_backlinks_created": integration.total_backlinks_created
            },
            "recent_sync_logs": [
                {
                    "id": str(log.id),
                    "sync_type": log.sync_type,
                    "status": log.status,
                    "started_at": log.started_at.isoformat(),
                    "completed_at": log.completed_at.isoformat() if log.completed_at else None,
                    "duration_seconds": log.duration_seconds,
                    "notes_processed": log.notes_processed,
                    "notes_created": log.notes_created,
                    "notes_updated": log.notes_updated,
                    "error_message": log.error_message
                }
                for log in recent_logs
            ]
        }
    
    async def schedule_auto_sync(self, integration_id: str):
        """Schedule automatic synchronization for an integration"""
        
        result = await self.db.execute(
            select(ObsidianIntegration).where(ObsidianIntegration.id == integration_id)
        )
        integration = result.scalar_one_or_none()
        
        if not integration or not integration.auto_sync:
            return
        
        # Check if enough time has passed since last sync
        if integration.last_sync_at:
            time_since_sync = datetime.now(timezone.utc) - integration.last_sync_at
            sync_interval = timedelta(minutes=integration.sync_frequency_minutes or 15)
            
            if time_since_sync < sync_interval:
                return  # Too soon to sync again
        
        # Perform incremental sync
        try:
            await self.sync_integration(integration_id, "incremental_sync")
        except Exception as e:
            # Log error but don't raise - this is a background operation
            print(f"Auto-sync failed for integration {integration_id}: {str(e)}")