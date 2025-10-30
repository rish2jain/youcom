"""
Obsidian Note Template System and Backlink Management Service
"""

import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Set, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.models.obsidian_integration import (
    ObsidianIntegration, ObsidianNoteTemplate, ObsidianNoteMapping
)
from app.services.obsidian_markdown_service import MarkdownGenerator


class ObsidianTemplateService:
    """Service for managing Obsidian note templates and backlinks"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.markdown_generator = MarkdownGenerator()
    
    # Template Management
    async def create_default_templates(self, integration_id: str) -> List[ObsidianNoteTemplate]:
        """Create default note templates for an integration"""
        
        default_templates = [
            {
                "template_name": "Company Profile",
                "template_type": "company_profile",
                "description": "Template for company research profiles",
                "template_content": self._get_company_profile_template(),
                "frontmatter_template": self._get_company_profile_frontmatter(),
                "variables": ["company_name", "industry", "founded_year", "employee_count", "headquarters", "website", "description", "products", "key_people"],
                "required_fields": ["company_name"],
                "default_tags": ["competitive_intelligence", "company_profile"],
                "is_default": True
            },
            {
                "template_name": "Impact Card",
                "template_type": "impact_card",
                "description": "Template for competitive intelligence impact cards",
                "template_content": self._get_impact_card_template(),
                "frontmatter_template": self._get_impact_card_frontmatter(),
                "variables": ["title", "company_name", "severity", "category", "risk_score", "confidence", "summary", "impact_analysis", "recommended_actions", "evidence"],
                "required_fields": ["title", "company_name", "severity"],
                "default_tags": ["competitive_intelligence", "impact_card"],
                "is_default": True
            },
            {
                "template_name": "Market Analysis",
                "template_type": "market_analysis",
                "description": "Template for market and industry analysis",
                "template_content": self._get_market_analysis_template(),
                "frontmatter_template": self._get_market_analysis_frontmatter(),
                "variables": ["industry", "overview", "key_players", "trends", "opportunities", "threats"],
                "required_fields": ["industry"],
                "default_tags": ["competitive_intelligence", "market_analysis"],
                "is_default": True
            },
            {
                "template_name": "Trend Report",
                "template_type": "trend_report",
                "description": "Template for trend analysis reports",
                "template_content": self._get_trend_report_template(),
                "frontmatter_template": self._get_trend_report_frontmatter(),
                "variables": ["title", "category", "timeframe", "summary", "trends", "implications", "recommendations"],
                "required_fields": ["title", "category"],
                "default_tags": ["competitive_intelligence", "trend_report"],
                "is_default": True
            }
        ]
        
        created_templates = []
        for template_data in default_templates:
            template = ObsidianNoteTemplate(
                integration_id=integration_id,
                **template_data
            )
            self.db.add(template)
            created_templates.append(template)
        
        await self.db.commit()
        return created_templates
    
    async def get_template(self, integration_id: str, template_type: str) -> Optional[ObsidianNoteTemplate]:
        """Get a template by type for an integration"""
        result = await self.db.execute(
            select(ObsidianNoteTemplate)
            .where(
                and_(
                    ObsidianNoteTemplate.integration_id == integration_id,
                    ObsidianNoteTemplate.template_type == template_type,
                    ObsidianNoteTemplate.is_active == True
                )
            )
            .order_by(ObsidianNoteTemplate.is_default.desc(), ObsidianNoteTemplate.created_at.desc())
        )
        return result.scalar_one_or_none()
    
    async def get_all_templates(self, integration_id: str) -> List[ObsidianNoteTemplate]:
        """Get all templates for an integration"""
        result = await self.db.execute(
            select(ObsidianNoteTemplate)
            .where(
                and_(
                    ObsidianNoteTemplate.integration_id == integration_id,
                    ObsidianNoteTemplate.is_active == True
                )
            )
            .order_by(ObsidianNoteTemplate.template_type, ObsidianNoteTemplate.is_default.desc())
        )
        return result.scalars().all()
    
    async def apply_template(self, template: ObsidianNoteTemplate, data: Dict[str, Any]) -> str:
        """Apply data to a template to generate note content"""
        content = template.template_content
        
        # Replace template variables
        for variable in template.variables:
            placeholder = f"{{{{{variable}}}}}"
            value = data.get(variable, "")
            
            # Handle different data types
            if isinstance(value, list):
                if variable in ["recommended_actions", "trends", "opportunities", "threats", "implications", "recommendations"]:
                    # Format as bullet list
                    value = "\n".join([f"- {item}" for item in value])
                elif variable == "key_people":
                    # Format key people
                    formatted_people = []
                    for person in value:
                        if isinstance(person, dict):
                            name = person.get('name', 'Unknown')
                            role = person.get('role', 'Unknown Role')
                            formatted_people.append(f"- **{name}** - {role}")
                        else:
                            formatted_people.append(f"- {person}")
                    value = "\n".join(formatted_people)
                elif variable == "products":
                    # Format products list
                    value = "\n".join([f"- {product}" for product in value])
                else:
                    # Default list formatting
                    value = ", ".join(str(item) for item in value)
            elif isinstance(value, dict):
                # Handle dictionary values (like evidence)
                if variable == "evidence":
                    formatted_evidence = []
                    for i, evidence in enumerate(value.get('sources', []), 1):
                        formatted_evidence.append(f"### Source {i}")
                        if 'title' in evidence:
                            formatted_evidence.append(f"**Title**: {evidence['title']}")
                        if 'url' in evidence:
                            formatted_evidence.append(f"**URL**: {evidence['url']}")
                        if 'snippet' in evidence:
                            formatted_evidence.append(f"**Excerpt**: {evidence['snippet']}")
                        formatted_evidence.append("")
                    value = "\n".join(formatted_evidence)
                else:
                    value = str(value)
            else:
                value = str(value) if value is not None else ""
            
            content = content.replace(placeholder, value)
        
        # Add frontmatter if template has it
        if template.frontmatter_template:
            frontmatter = self._apply_frontmatter_template(template.frontmatter_template, data, template.default_tags)
            content = f"{frontmatter}\n\n{content}"
        
        # Update template usage count
        template.usage_count = (template.usage_count or 0) + 1
        await self.db.commit()
        
        return content
    
    def _apply_frontmatter_template(self, frontmatter_template: str, data: Dict[str, Any], default_tags: List[str]) -> str:
        """Apply data to frontmatter template"""
        frontmatter = frontmatter_template
        
        # Replace variables in frontmatter
        for key, value in data.items():
            placeholder = f"{{{{{key}}}}}"
            if isinstance(value, (list, dict)):
                # Skip complex types in frontmatter
                continue
            frontmatter = frontmatter.replace(placeholder, str(value) if value is not None else "")
        
        # Add default tags
        if default_tags:
            tags_section = "tags:\n" + "\n".join([f"  - {tag}" for tag in default_tags])
            frontmatter = frontmatter.replace("{{default_tags}}", tags_section)
        
        # Add current timestamp
        frontmatter = frontmatter.replace("{{current_date}}", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
        frontmatter = frontmatter.replace("{{current_datetime}}", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"))
        
        return frontmatter
    
    # Backlink Management
    async def extract_backlinks_from_content(self, content: str) -> List[str]:
        """Extract all backlinks from note content"""
        # Extract wikilinks [[Note Name]]
        wikilinks = re.findall(r'\[\[([^\]|]+)(?:\|[^\]]*)?\]\]', content)
        
        # Extract markdown links [text](note.md)
        markdown_links = re.findall(r'\[([^\]]+)\]\(([^)]+\.md)\)', content)
        markdown_note_names = [link[1].replace('.md', '') for link in markdown_links]
        
        # Combine and deduplicate
        all_links = list(set(wikilinks + markdown_note_names))
        
        return all_links
    
    async def generate_backlinks_for_content(self, content_type: str, content_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate relevant backlinks for content based on its type and data"""
        backlinks = []
        
        if content_type == "impact_card":
            company_name = content_data.get("company_name")
            category = content_data.get("category")
            
            if company_name:
                backlinks.append({
                    "text": f"{company_name} Profile",
                    "target": f"Companies/{company_name}/{company_name}_Profile",
                    "type": "company_profile"
                })
            
            if category:
                backlinks.append({
                    "text": f"{category} Analysis",
                    "target": f"Market Analysis/{category}/{category}_Analysis",
                    "type": "market_analysis"
                })
                
                backlinks.append({
                    "text": f"{category} Trends",
                    "target": f"Trends/{category}/{category}_Trends",
                    "type": "trend_report"
                })
        
        elif content_type == "company_profile":
            company_name = content_data.get("company_name")
            industry = content_data.get("industry")
            
            if industry:
                backlinks.append({
                    "text": f"{industry} Industry Analysis",
                    "target": f"Market Analysis/{industry}/{industry}_Industry_Analysis",
                    "type": "market_analysis"
                })
                
                backlinks.append({
                    "text": f"{industry} Competitive Landscape",
                    "target": f"Market Analysis/{industry}/{industry}_Competitive_Landscape",
                    "type": "market_analysis"
                })
            
            # Link to related impact cards
            if company_name:
                backlinks.append({
                    "text": f"{company_name} Impact Cards",
                    "target": f"Impact Cards/{company_name}/Index",
                    "type": "index"
                })
        
        elif content_type == "market_analysis":
            industry = content_data.get("industry")
            key_players = content_data.get("key_players", [])
            
            # Link to company profiles of key players
            for player in key_players[:5]:  # Limit to top 5
                player_name = player.get('name', player) if isinstance(player, dict) else player
                backlinks.append({
                    "text": f"{player_name} Profile",
                    "target": f"Companies/{player_name}/{player_name}_Profile",
                    "type": "company_profile"
                })
            
            if industry:
                backlinks.append({
                    "text": f"{industry} Trends",
                    "target": f"Trends/{industry}/{industry}_Trends",
                    "type": "trend_report"
                })
        
        elif content_type == "trend_report":
            category = content_data.get("category")
            
            if category:
                backlinks.append({
                    "text": f"{category} Market Analysis",
                    "target": f"Market Analysis/{category}/{category}_Market_Analysis",
                    "type": "market_analysis"
                })
                
                backlinks.append({
                    "text": f"{category} Overview",
                    "target": f"Market Analysis/{category}/{category}_Overview",
                    "type": "market_analysis"
                })
        
        return backlinks
    
    async def create_backlinks_in_content(self, content: str, backlinks: List[Dict[str, str]], 
                                        link_format: str = "wikilink") -> str:
        """Add backlinks to content"""
        if not backlinks:
            return content
        
        # Check if content already has a "Related" section
        if "## Related" in content:
            # Find the Related section and add links there
            lines = content.split('\n')
            related_index = -1
            
            for i, line in enumerate(lines):
                if line.strip() == "## Related":
                    related_index = i
                    break
            
            if related_index != -1:
                # Find the end of the Related section
                end_index = len(lines)
                for i in range(related_index + 1, len(lines)):
                    if lines[i].startswith('##') and not lines[i].startswith('###'):
                        end_index = i
                        break
                
                # Add new backlinks
                new_links = []
                for backlink in backlinks:
                    if link_format == "wikilink":
                        link_text = f"- [[{backlink['target']}|{backlink['text']}]]"
                    else:
                        link_text = f"- [{backlink['text']}]({backlink['target']}.md)"
                    
                    # Check if link already exists
                    link_exists = any(backlink['text'] in line for line in lines[related_index:end_index])
                    if not link_exists:
                        new_links.append(link_text)
                
                # Insert new links before the end of the Related section
                if new_links:
                    lines[end_index:end_index] = new_links
                
                return '\n'.join(lines)
        
        # If no Related section exists, add one at the end
        related_section = ["", "## Related"]
        for backlink in backlinks:
            if link_format == "wikilink":
                link_text = f"- [[{backlink['target']}|{backlink['text']}]]"
            else:
                link_text = f"- [{backlink['text']}]({backlink['target']}.md)"
            related_section.append(link_text)
        
        return content + '\n'.join(related_section)
    
    async def update_note_mapping_backlinks(self, mapping: ObsidianNoteMapping, 
                                          backlinks_to: List[str], backlinks_from: List[str]):
        """Update backlink information in note mapping"""
        mapping.backlinks_to = backlinks_to
        mapping.backlinks_from = backlinks_from
        await self.db.commit()
    
    async def find_related_notes(self, integration_id: str, content_type: str, 
                               keywords: List[str]) -> List[ObsidianNoteMapping]:
        """Find related notes based on content type and keywords"""
        # Build search conditions
        conditions = [ObsidianNoteMapping.integration_id == integration_id]
        
        # Search in content title and note filename
        keyword_conditions = []
        for keyword in keywords:
            keyword_conditions.extend([
                ObsidianNoteMapping.content_title.ilike(f"%{keyword}%"),
                ObsidianNoteMapping.note_filename.ilike(f"%{keyword}%")
            ])
        
        if keyword_conditions:
            conditions.append(or_(*keyword_conditions))
        
        result = await self.db.execute(
            select(ObsidianNoteMapping)
            .where(and_(*conditions))
            .where(ObsidianNoteMapping.is_active == True)
            .limit(10)  # Limit results
        )
        
        return result.scalars().all()
    
    # Tag Hierarchy Management
    async def create_tag_hierarchy(self, integration_id: str) -> Dict[str, Any]:
        """Create a hierarchical tag system for competitive intelligence"""
        hierarchy = {
            "competitive_intelligence": {
                "description": "Root tag for all competitive intelligence content",
                "children": {
                    "impact_card": {
                        "description": "Impact cards and competitive events",
                        "children": {
                            "severity_critical": {"description": "Critical severity impact cards"},
                            "severity_high": {"description": "High severity impact cards"},
                            "severity_medium": {"description": "Medium severity impact cards"},
                            "severity_low": {"description": "Low severity impact cards"}
                        }
                    },
                    "company_profile": {
                        "description": "Company research and profiles",
                        "children": {
                            "public_company": {"description": "Publicly traded companies"},
                            "private_company": {"description": "Private companies"},
                            "startup": {"description": "Startup companies"},
                            "enterprise": {"description": "Enterprise companies"}
                        }
                    },
                    "market_analysis": {
                        "description": "Market and industry analysis",
                        "children": {
                            "industry_overview": {"description": "Industry overview and landscape"},
                            "competitive_landscape": {"description": "Competitive positioning"},
                            "market_trends": {"description": "Market trend analysis"},
                            "market_opportunity": {"description": "Market opportunities"}
                        }
                    },
                    "trend_report": {
                        "description": "Trend analysis and reports",
                        "children": {
                            "technology_trends": {"description": "Technology and innovation trends"},
                            "market_trends": {"description": "Market and business trends"},
                            "regulatory_trends": {"description": "Regulatory and compliance trends"},
                            "consumer_trends": {"description": "Consumer behavior trends"}
                        }
                    }
                }
            },
            "industry": {
                "description": "Industry-specific tags",
                "children": {
                    "saas": {"description": "Software as a Service"},
                    "fintech": {"description": "Financial Technology"},
                    "healthtech": {"description": "Healthcare Technology"},
                    "ecommerce": {"description": "E-commerce and Retail"},
                    "manufacturing": {"description": "Manufacturing and Industrial"},
                    "energy": {"description": "Energy and Utilities"},
                    "media": {"description": "Media and Entertainment"},
                    "consulting": {"description": "Consulting and Professional Services"}
                }
            },
            "priority": {
                "description": "Priority and urgency tags",
                "children": {
                    "urgent": {"description": "Requires immediate attention"},
                    "high_priority": {"description": "High priority items"},
                    "medium_priority": {"description": "Medium priority items"},
                    "low_priority": {"description": "Low priority items"},
                    "monitoring": {"description": "Items under monitoring"}
                }
            }
        }
        
        # Update integration with tag hierarchy
        result = await self.db.execute(
            select(ObsidianIntegration).where(ObsidianIntegration.id == integration_id)
        )
        integration = result.scalar_one_or_none()
        
        if integration:
            integration.tag_hierarchy = hierarchy
            await self.db.commit()
        
        return hierarchy
    
    async def get_tags_for_content(self, content_type: str, content_data: Dict[str, Any]) -> List[str]:
        """Generate appropriate tags for content based on type and data"""
        tags = ["competitive_intelligence", content_type]
        
        # Add content-specific tags
        if content_type == "impact_card":
            severity = content_data.get("severity", "").lower()
            if severity:
                tags.append(f"severity_{severity}")
            
            category = content_data.get("category", "").lower().replace(" ", "_")
            if category:
                tags.append(category)
            
            company_name = content_data.get("company_name", "").lower().replace(" ", "_")
            if company_name:
                tags.append(company_name)
        
        elif content_type == "company_profile":
            industry = content_data.get("industry", "").lower().replace(" ", "_")
            if industry:
                tags.extend(["industry", industry])
            
            company_name = content_data.get("company_name", "").lower().replace(" ", "_")
            if company_name:
                tags.append(company_name)
        
        elif content_type == "market_analysis":
            industry = content_data.get("industry", "").lower().replace(" ", "_")
            if industry:
                tags.extend(["industry", industry, "market_trends"])
        
        elif content_type == "trend_report":
            category = content_data.get("category", "").lower().replace(" ", "_")
            if category:
                tags.extend([category, "market_trends"])
        
        return list(set(tags))  # Remove duplicates
    
    # Template Content Definitions
    def _get_company_profile_template(self) -> str:
        return """# {{company_name}} Profile

## Overview

{{description}}

## Key Information

- **Industry**: {{industry}}
- **Founded**: {{founded_year}}
- **Employees**: {{employee_count}}
- **Headquarters**: {{headquarters}}
- **Website**: {{website}}

## Products & Services

{{products}}

## Key People

{{key_people}}

## Competitive Position

{{competitive_position}}

## Recent Developments

{{recent_news}}

## Tags

{{default_tags}}

## Related

- Industry Analysis: [[{{industry}} Industry Analysis]]
- Competitive Landscape: [[{{industry}} Competitive Landscape]]
"""
    
    def _get_company_profile_frontmatter(self) -> str:
        return """---
type: company_profile
company: {{company_name}}
industry: {{industry}}
founded: {{founded_year}}
employees: {{employee_count}}
created: {{current_datetime}}
{{default_tags}}
---"""
    
    def _get_impact_card_template(self) -> str:
        return """# {{title}}

## Summary

{{summary}}

## Key Details

- **Company**: [[{{company_name}} Profile|{{company_name}}]]
- **Severity**: {{severity}}
- **Category**: {{category}}
- **Risk Score**: {{risk_score}}/100
- **Confidence**: {{confidence}}
- **Detected**: {{current_datetime}}

## Impact Analysis

{{impact_analysis}}

## Recommended Actions

{{recommended_actions}}

## Evidence

{{evidence}}

## Tags

{{default_tags}}

## Related

- Company Profile: [[{{company_name}} Profile]]
- Market Analysis: [[{{category}} Analysis]]
"""
    
    def _get_impact_card_frontmatter(self) -> str:
        return """---
type: impact_card
company: {{company_name}}
severity: {{severity}}
category: {{category}}
risk_score: {{risk_score}}
confidence: {{confidence}}
created: {{current_datetime}}
{{default_tags}}
---"""
    
    def _get_market_analysis_template(self) -> str:
        return """# {{industry}} Market Analysis

## Market Overview

{{overview}}

## Key Players

{{key_players}}

## Market Trends

{{trends}}

## Opportunities

{{opportunities}}

## Threats

{{threats}}

## Tags

{{default_tags}}

## Related

- Industry Overview: [[{{industry}} Overview]]
"""
    
    def _get_market_analysis_frontmatter(self) -> str:
        return """---
type: market_analysis
industry: {{industry}}
created: {{current_datetime}}
{{default_tags}}
---"""
    
    def _get_trend_report_template(self) -> str:
        return """# {{title}}

## Executive Summary

{{summary}}

## Key Trends

{{trends}}

## Strategic Implications

{{implications}}

## Recommendations

{{recommendations}}

## Tags

{{default_tags}}

## Related

- Category Analysis: [[{{category}} Analysis]]
- Market Overview: [[{{category}} Market Overview]]
"""
    
    def _get_trend_report_frontmatter(self) -> str:
        return """---
type: trend_report
category: {{category}}
timeframe: {{timeframe}}
created: {{current_datetime}}
{{default_tags}}
---"""