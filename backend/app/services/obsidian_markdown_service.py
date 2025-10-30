"""
Markdown Generation Service for Obsidian Integration
Converts competitive intelligence data to structured markdown format
"""

import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urlparse

from app.models.impact_card import ImpactCard
from app.models.company_research import CompanyResearch
from app.models.watch import WatchItem


class MarkdownGenerator:
    """Generate markdown content for Obsidian notes"""
    
    def __init__(self, style: str = "obsidian"):
        """
        Initialize markdown generator
        
        Args:
            style: Markdown style - 'obsidian', 'standard', or 'github'
        """
        self.style = style
    
    def _sanitize_filename(self, name: str) -> str:
        """Sanitize a string for use as a filename"""
        # Remove or replace invalid characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', name)
        sanitized = re.sub(r'\s+', '_', sanitized)
        sanitized = sanitized.strip('._')
        return sanitized[:200]  # Limit length
    
    def _format_date(self, date: datetime) -> str:
        """Format date for markdown with proper UTC conversion"""
        # Ensure datetime is in UTC
        if date.tzinfo is None:
            # Treat naive datetime as UTC
            date = date.replace(tzinfo=timezone.utc)
        else:
            # Convert to UTC
            date = date.astimezone(timezone.utc)
        
        return date.strftime("%Y-%m-%d %H:%M:%S UTC")
    
    def _create_wikilink(self, text: str, target: Optional[str] = None) -> str:
        """Create a wikilink based on style preference"""
        if self.style == "obsidian":
            if target:
                return f"[[{target}|{text}]]"
            else:
                return f"[[{text}]]"
        else:
            # Use markdown links for other styles
            target = target or self._sanitize_filename(text)
            return f"[{text}]({target}.md)"
    
    def _create_tag(self, tag: str) -> str:
        """Create a tag based on style preference"""
        # Clean tag name
        clean_tag = re.sub(r'[^\w\-_/]', '', tag.replace(' ', '_'))
        return f"#{clean_tag}"
    
    def _create_frontmatter(self, metadata: Dict[str, Any]) -> str:
        """Create YAML frontmatter"""
        lines = ["---"]
        
        for key, value in metadata.items():
            if isinstance(value, list):
                if value:  # Only add non-empty lists
                    lines.append(f"{key}:")
                    for item in value:
                        lines.append(f"  - {item}")
            elif isinstance(value, dict):
                if value:  # Only add non-empty dicts
                    lines.append(f"{key}:")
                    for k, v in value.items():
                        lines.append(f"  {k}: {v}")
            elif value is not None:
                # Escape special YAML characters
                if isinstance(value, str) and any(char in value for char in [':', '"', "'"]):
                    value = f'"{value.replace('"', '\\"')}"'
                lines.append(f"{key}: {value}")
        
        lines.append("---")
        return "\n".join(lines)
    
    def generate_impact_card_note(self, impact_card: ImpactCard, 
                                 include_metadata: bool = True,
                                 include_backlinks: bool = True) -> Dict[str, str]:
        """Generate markdown note for an impact card"""
        
        # Create filename
        title = f"{impact_card.company_name} - {impact_card.title}"
        filename = self._sanitize_filename(title)
        
        # Prepare metadata
        metadata = {}
        if include_metadata:
            metadata = {
                "type": "impact_card",
                "company": impact_card.company_name,
                "severity": impact_card.severity,
                "category": impact_card.category,
                "risk_score": impact_card.risk_score,
                "confidence": impact_card.confidence,
                "created": self._format_date(impact_card.created_at),
                "tags": [
                    "competitive_intelligence",
                    "impact_card",
                    self._sanitize_filename(impact_card.company_name).lower(),
                    impact_card.category.lower().replace(' ', '_'),
                    f"severity_{impact_card.severity.lower()}"
                ]
            }
        
        # Build content
        content_parts = []
        
        # Add frontmatter
        if metadata:
            content_parts.append(self._create_frontmatter(metadata))
            content_parts.append("")
        
        # Title
        content_parts.append(f"# {title}")
        content_parts.append("")
        
        # Summary
        if impact_card.summary:
            content_parts.append("## Summary")
            content_parts.append(impact_card.summary)
            content_parts.append("")
        
        # Key details
        content_parts.append("## Key Details")
        content_parts.append(f"- **Company**: {self._create_wikilink(impact_card.company_name)}")
        content_parts.append(f"- **Severity**: {impact_card.severity}")
        content_parts.append(f"- **Category**: {impact_card.category}")
        content_parts.append(f"- **Risk Score**: {impact_card.risk_score}/100")
        content_parts.append(f"- **Confidence**: {impact_card.confidence:.1%}")
        content_parts.append(f"- **Detected**: {self._format_date(impact_card.created_at)}")
        content_parts.append("")
        
        # Impact analysis
        if impact_card.impact_analysis:
            content_parts.append("## Impact Analysis")
            content_parts.append(impact_card.impact_analysis)
            content_parts.append("")
        
        # Recommended actions
        if impact_card.recommended_actions:
            content_parts.append("## Recommended Actions")
            actions = impact_card.recommended_actions
            if isinstance(actions, list):
                for action in actions:
                    content_parts.append(f"- {action}")
            else:
                content_parts.append(actions)
            content_parts.append("")
        
        # Evidence and sources
        if hasattr(impact_card, 'evidence') and impact_card.evidence:
            content_parts.append("## Evidence")
            for i, evidence in enumerate(impact_card.evidence, 1):
                content_parts.append(f"### Source {i}")
                if 'title' in evidence:
                    content_parts.append(f"**Title**: {evidence['title']}")
                if 'url' in evidence:
                    content_parts.append(f"**URL**: {evidence['url']}")
                if 'snippet' in evidence:
                    content_parts.append(f"**Excerpt**: {evidence['snippet']}")
                if 'credibility' in evidence:
                    content_parts.append(f"**Credibility**: {evidence['credibility']:.1%}")
                content_parts.append("")
        
        # Tags
        if include_metadata and metadata.get('tags'):
            content_parts.append("## Tags")
            tag_line = " ".join([self._create_tag(tag) for tag in metadata['tags']])
            content_parts.append(tag_line)
            content_parts.append("")
        
        # Backlinks section
        if include_backlinks:
            content_parts.append("## Related")
            content_parts.append(f"- Company Profile: {self._create_wikilink(f'{impact_card.company_name} Profile')}")
            content_parts.append(f"- Market Analysis: {self._create_wikilink(f'{impact_card.category} Analysis')}")
            content_parts.append("")
        
        return {
            "filename": filename,
            "content": "\n".join(content_parts),
            "title": title,
            "folder": f"Impact Cards/{impact_card.company_name}"
        }
    
    def generate_company_profile_note(self, company_research: CompanyResearch,
                                    include_metadata: bool = True,
                                    include_backlinks: bool = True) -> Dict[str, str]:
        """Generate markdown note for a company profile"""
        
        # Create filename
        title = f"{company_research.company_name} Profile"
        filename = self._sanitize_filename(title)
        
        # Prepare metadata
        metadata = {}
        if include_metadata:
            metadata = {
                "type": "company_profile",
                "company": company_research.company_name,
                "industry": company_research.industry,
                "founded": company_research.founded_year,
                "employees": company_research.employee_count,
                "created": self._format_date(company_research.created_at),
                "updated": self._format_date(company_research.updated_at),
                "tags": [
                    "competitive_intelligence",
                    "company_profile",
                    self._sanitize_filename(company_research.company_name).lower(),
                    company_research.industry.lower().replace(' ', '_') if company_research.industry else "unknown"
                ]
            }
        
        # Build content
        content_parts = []
        
        # Add frontmatter
        if metadata:
            content_parts.append(self._create_frontmatter(metadata))
            content_parts.append("")
        
        # Title
        content_parts.append(f"# {title}")
        content_parts.append("")
        
        # Overview
        if company_research.description:
            content_parts.append("## Overview")
            content_parts.append(company_research.description)
            content_parts.append("")
        
        # Key Information
        content_parts.append("## Key Information")
        content_parts.append(f"- **Industry**: {company_research.industry or 'Unknown'}")
        if company_research.founded_year:
            content_parts.append(f"- **Founded**: {company_research.founded_year}")
        if company_research.employee_count:
            content_parts.append(f"- **Employees**: {company_research.employee_count:,}")
        if company_research.headquarters:
            content_parts.append(f"- **Headquarters**: {company_research.headquarters}")
        if company_research.website:
            content_parts.append(f"- **Website**: {company_research.website}")
        content_parts.append("")
        
        # Products and services
        if company_research.products:
            content_parts.append("## Products & Services")
            if isinstance(company_research.products, list):
                for product in company_research.products:
                    content_parts.append(f"- {product}")
            else:
                content_parts.append(company_research.products)
            content_parts.append("")
        
        # Key people
        if company_research.key_people:
            content_parts.append("## Key People")
            if isinstance(company_research.key_people, list):
                for person in company_research.key_people:
                    if isinstance(person, dict):
                        name = person.get('name', 'Unknown')
                        role = person.get('role', 'Unknown Role')
                        content_parts.append(f"- **{name}** - {role}")
                    else:
                        content_parts.append(f"- {person}")
            else:
                content_parts.append(company_research.key_people)
            content_parts.append("")
        
        # Recent news and developments
        if hasattr(company_research, 'recent_news') and company_research.recent_news:
            content_parts.append("## Recent Developments")
            for news in company_research.recent_news[:5]:  # Limit to 5 most recent
                content_parts.append(f"- **{news.get('date', 'Unknown date')}**: {news.get('title', 'No title')}")
                if news.get('url'):
                    content_parts.append(f"  - Source: {news['url']}")
            content_parts.append("")
        
        # Competitive positioning
        if company_research.competitive_position:
            content_parts.append("## Competitive Position")
            content_parts.append(company_research.competitive_position)
            content_parts.append("")
        
        # Tags
        if include_metadata and metadata.get('tags'):
            content_parts.append("## Tags")
            tag_line = " ".join([self._create_tag(tag) for tag in metadata['tags']])
            content_parts.append(tag_line)
            content_parts.append("")
        
        # Backlinks section
        if include_backlinks:
            content_parts.append("## Related")
            content_parts.append(f"- Industry Analysis: {self._create_wikilink(f'{company_research.industry} Industry Analysis')}")
            content_parts.append(f"- Competitive Landscape: {self._create_wikilink(f'{company_research.industry} Competitive Landscape')}")
            content_parts.append("")
        
        return {
            "filename": filename,
            "content": "\n".join(content_parts),
            "title": title,
            "folder": f"Companies/{company_research.company_name}"
        }
    
    def generate_market_analysis_note(self, industry: str, analysis_data: Dict[str, Any],
                                    include_metadata: bool = True,
                                    include_backlinks: bool = True) -> Dict[str, str]:
        """Generate markdown note for market analysis"""
        
        # Create filename
        title = f"{industry} Market Analysis"
        filename = self._sanitize_filename(title)
        
        # Prepare metadata
        metadata = {}
        if include_metadata:
            metadata = {
                "type": "market_analysis",
                "industry": industry,
                "created": self._format_date(datetime.now(timezone.utc)),
                "tags": [
                    "competitive_intelligence",
                    "market_analysis",
                    industry.lower().replace(' ', '_')
                ]
            }
        
        # Build content
        content_parts = []
        
        # Add frontmatter
        if metadata:
            content_parts.append(self._create_frontmatter(metadata))
            content_parts.append("")
        
        # Title
        content_parts.append(f"# {title}")
        content_parts.append("")
        
        # Market overview
        if analysis_data.get('overview'):
            content_parts.append("## Market Overview")
            content_parts.append(analysis_data['overview'])
            content_parts.append("")
        
        # Key players
        if analysis_data.get('key_players'):
            content_parts.append("## Key Players")
            for player in analysis_data['key_players']:
                if isinstance(player, dict):
                    name = player.get('name', 'Unknown')
                    market_share = player.get('market_share', 'Unknown')
                    content_parts.append(f"- {self._create_wikilink(f'{name} Profile', name)} - Market Share: {market_share}")
                else:
                    content_parts.append(f"- {self._create_wikilink(f'{player} Profile', player)}")
            content_parts.append("")
        
        # Market trends
        if analysis_data.get('trends'):
            content_parts.append("## Market Trends")
            for trend in analysis_data['trends']:
                content_parts.append(f"- {trend}")
            content_parts.append("")
        
        # Opportunities and threats
        if analysis_data.get('opportunities'):
            content_parts.append("## Opportunities")
            for opportunity in analysis_data['opportunities']:
                content_parts.append(f"- {opportunity}")
            content_parts.append("")
        
        if analysis_data.get('threats'):
            content_parts.append("## Threats")
            for threat in analysis_data['threats']:
                content_parts.append(f"- {threat}")
            content_parts.append("")
        
        # Tags
        if include_metadata and metadata.get('tags'):
            content_parts.append("## Tags")
            tag_line = " ".join([self._create_tag(tag) for tag in metadata['tags']])
            content_parts.append(tag_line)
            content_parts.append("")
        
        # Backlinks section
        if include_backlinks:
            content_parts.append("## Related")
            content_parts.append(f"- Industry Overview: {self._create_wikilink(f'{industry} Overview')}")
            if analysis_data.get('key_players'):
                content_parts.append("- Company Profiles:")
                for player in analysis_data['key_players'][:5]:  # Limit to 5
                    name = player.get('name', player) if isinstance(player, dict) else player
                    content_parts.append(f"  - {self._create_wikilink(f'{name} Profile', name)}")
            content_parts.append("")
        
        return {
            "filename": filename,
            "content": "\n".join(content_parts),
            "title": title,
            "folder": f"Market Analysis/{industry}"
        }
    
    def generate_trend_report_note(self, trend_data: Dict[str, Any],
                                 include_metadata: bool = True,
                                 include_backlinks: bool = True) -> Dict[str, str]:
        """Generate markdown note for trend reports"""
        
        # Create filename
        title = trend_data.get('title', 'Trend Report')
        filename = self._sanitize_filename(title)
        
        # Prepare metadata
        metadata = {}
        if include_metadata:
            metadata = {
                "type": "trend_report",
                "category": trend_data.get('category', 'General'),
                "timeframe": trend_data.get('timeframe', 'Unknown'),
                "created": self._format_date(datetime.now(timezone.utc)),
                "tags": [
                    "competitive_intelligence",
                    "trend_report",
                    trend_data.get('category', 'general').lower().replace(' ', '_')
                ]
            }
        
        # Build content
        content_parts = []
        
        # Add frontmatter
        if metadata:
            content_parts.append(self._create_frontmatter(metadata))
            content_parts.append("")
        
        # Title
        content_parts.append(f"# {title}")
        content_parts.append("")
        
        # Executive summary
        if trend_data.get('summary'):
            content_parts.append("## Executive Summary")
            content_parts.append(trend_data['summary'])
            content_parts.append("")
        
        # Key trends
        if trend_data.get('trends'):
            content_parts.append("## Key Trends")
            for i, trend in enumerate(trend_data['trends'], 1):
                if isinstance(trend, dict):
                    content_parts.append(f"### {i}. {trend.get('name', f'Trend {i}')}")
                    if trend.get('description'):
                        content_parts.append(trend['description'])
                    if trend.get('impact'):
                        content_parts.append(f"**Impact**: {trend['impact']}")
                else:
                    content_parts.append(f"### {i}. {trend}")
                content_parts.append("")
        
        # Implications
        if trend_data.get('implications'):
            content_parts.append("## Strategic Implications")
            for implication in trend_data['implications']:
                content_parts.append(f"- {implication}")
            content_parts.append("")
        
        # Recommendations
        if trend_data.get('recommendations'):
            content_parts.append("## Recommendations")
            for recommendation in trend_data['recommendations']:
                content_parts.append(f"- {recommendation}")
            content_parts.append("")
        
        # Tags
        if include_metadata and metadata.get('tags'):
            content_parts.append("## Tags")
            tag_line = " ".join([self._create_tag(tag) for tag in metadata['tags']])
            content_parts.append(tag_line)
            content_parts.append("")
        
        # Backlinks section
        if include_backlinks:
            content_parts.append("## Related")
            category = trend_data.get('category', 'General')
            content_parts.append(f"- Category Analysis: {self._create_wikilink(f'{category} Analysis')}")
            content_parts.append(f"- Market Overview: {self._create_wikilink(f'{category} Market Overview')}")
            content_parts.append("")
        
        return {
            "filename": filename,
            "content": "\n".join(content_parts),
            "title": title,
            "folder": f"Trends/{trend_data.get('category', 'General')}"
        }
    
    def generate_index_note(self, title: str, items: List[Dict[str, str]],
                          description: str = "") -> Dict[str, str]:
        """Generate an index note that links to other notes"""
        
        filename = self._sanitize_filename(title)
        
        # Build content
        content_parts = []
        
        # Title
        content_parts.append(f"# {title}")
        content_parts.append("")
        
        # Description
        if description:
            content_parts.append(description)
            content_parts.append("")
        
        # Items list
        for item in items:
            name = item.get('name', 'Unknown')
            path = item.get('path', name)
            description = item.get('description', '')
            
            if description:
                content_parts.append(f"- {self._create_wikilink(name, path)} - {description}")
            else:
                content_parts.append(f"- {self._create_wikilink(name, path)}")
        
        content_parts.append("")
        content_parts.append(f"*Last updated: {self._format_date(datetime.now(timezone.utc))}*")
        
        return {
            "filename": filename,
            "content": "\n".join(content_parts),
            "title": title,
            "folder": ""
        }