"""
Industry Data Provider Service

This service maintains up-to-date industry information, implements competitor discovery
and ranking algorithms, and manages industry-specific keywords and risk categories.
"""

import logging
import asyncio
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json
import hashlib

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func, text

from app.services.you_client import YouComOrchestrator
from app.config import settings

logger = logging.getLogger(__name__)


class IndustryCategory(str, Enum):
    """Industry categories for classification."""
    SAAS = "SaaS"
    FINTECH = "FinTech"
    HEALTHTECH = "HealthTech"
    ECOMMERCE = "E-commerce"
    MANUFACTURING = "Manufacturing"
    ENERGY = "Energy"
    MEDIA = "Media"
    CONSULTING = "Consulting"
    AUTOMOTIVE = "Automotive"
    RETAIL = "Retail"
    REAL_ESTATE = "Real Estate"
    EDUCATION = "Education"


class CompetitorRankingFactor(str, Enum):
    """Factors used for competitor ranking."""
    MARKET_CAP = "market_cap"
    REVENUE = "revenue"
    EMPLOYEE_COUNT = "employee_count"
    FUNDING_AMOUNT = "funding_amount"
    NEWS_MENTIONS = "news_mentions"
    SOCIAL_PRESENCE = "social_presence"
    MARKET_SHARE = "market_share"


@dataclass
class CompetitorProfile:
    """Comprehensive competitor profile."""
    name: str
    industry: str
    description: str
    website: Optional[str]
    founded_year: Optional[int]
    headquarters: Optional[str]
    employee_count: Optional[int]
    market_cap: Optional[float]
    revenue: Optional[float]
    funding_amount: Optional[float]
    last_funding_round: Optional[str]
    key_products: List[str]
    target_markets: List[str]
    competitive_advantages: List[str]
    recent_news: List[Dict[str, Any]]
    social_metrics: Dict[str, int]
    risk_factors: List[str]
    confidence_score: float
    last_updated: datetime


@dataclass
class IndustryInsights:
    """Industry-level insights and trends."""
    industry: str
    market_size: Optional[float]
    growth_rate: Optional[float]
    key_trends: List[str]
    major_players: List[str]
    emerging_companies: List[str]
    risk_factors: List[str]
    opportunities: List[str]
    regulatory_environment: List[str]
    technology_trends: List[str]
    last_updated: datetime


@dataclass
class KeywordSet:
    """Industry-specific keyword set."""
    industry: str
    primary_keywords: List[str]
    secondary_keywords: List[str]
    negative_keywords: List[str]
    trending_keywords: List[str]
    seasonal_keywords: Dict[str, List[str]]
    confidence_scores: Dict[str, float]
    last_updated: datetime


class IndustryDataProvider:
    """Service for providing comprehensive industry data and competitor intelligence."""
    
    def __init__(self, db: AsyncSession, you_client: Optional[YouComOrchestrator] = None):
        self.db = db
        self.you_client = you_client or YouComOrchestrator()
        self.cache_ttl = timedelta(hours=24)  # Cache industry data for 24 hours
        self.competitor_cache_ttl = timedelta(hours=6)  # Competitor data refreshed more frequently
        
        # Industry-specific data cache
        self._industry_cache: Dict[str, IndustryInsights] = {}
        self._competitor_cache: Dict[str, List[CompetitorProfile]] = {}
        self._keyword_cache: Dict[str, KeywordSet] = {}
        
        # Last update timestamps
        self._last_industry_update: Dict[str, datetime] = {}
        self._last_competitor_update: Dict[str, datetime] = {}
        self._last_keyword_update: Dict[str, datetime] = {}
    
    async def get_industry_insights(self, industry: str, force_refresh: bool = False) -> IndustryInsights:
        """Get comprehensive insights for a specific industry."""
        try:
            # Check cache first
            if not force_refresh and self._is_cache_valid(industry, self._last_industry_update):
                cached_insights = self._industry_cache.get(industry)
                if cached_insights:
                    return cached_insights
            
            # Fetch fresh industry data
            insights = await self._fetch_industry_insights(industry)
            
            # Update cache
            self._industry_cache[industry] = insights
            self._last_industry_update[industry] = datetime.now(timezone.utc)
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to get industry insights for {industry}: {e}")
            # Return cached data if available, otherwise empty insights
            return self._industry_cache.get(industry, self._create_empty_insights(industry))
    
    async def discover_competitors(
        self,
        industry: str,
        company_name: Optional[str] = None,
        limit: int = 20,
        ranking_factors: Optional[List[CompetitorRankingFactor]] = None
    ) -> List[CompetitorProfile]:
        """Discover and rank competitors for a specific industry or company."""
        try:
            cache_key = f"{industry}_{company_name or 'general'}"
            
            # Check cache
            if self._is_cache_valid(cache_key, self._last_competitor_update, self.competitor_cache_ttl):
                cached_competitors = self._competitor_cache.get(cache_key)
                if cached_competitors:
                    return cached_competitors[:limit]
            
            # Fetch competitors
            competitors = await self._fetch_competitors(industry, company_name)
            
            # Rank competitors
            ranking_factors = ranking_factors or [
                CompetitorRankingFactor.MARKET_CAP,
                CompetitorRankingFactor.REVENUE,
                CompetitorRankingFactor.NEWS_MENTIONS
            ]
            
            ranked_competitors = await self._rank_competitors(competitors, ranking_factors)
            
            # Update cache
            self._competitor_cache[cache_key] = ranked_competitors
            self._last_competitor_update[cache_key] = datetime.now(timezone.utc)
            
            return ranked_competitors[:limit]
            
        except Exception as e:
            logger.error(f"Failed to discover competitors for {industry}: {e}")
            return []
    
    async def get_industry_keywords(
        self,
        industry: str,
        include_trending: bool = True,
        force_refresh: bool = False
    ) -> KeywordSet:
        """Get industry-specific keywords for monitoring."""
        try:
            # Check cache
            if not force_refresh and self._is_cache_valid(industry, self._last_keyword_update):
                cached_keywords = self._keyword_cache.get(industry)
                if cached_keywords:
                    return cached_keywords
            
            # Fetch keywords
            keyword_set = await self._fetch_industry_keywords(industry, include_trending)
            
            # Update cache
            self._keyword_cache[industry] = keyword_set
            self._last_keyword_update[industry] = datetime.now(timezone.utc)
            
            return keyword_set
            
        except Exception as e:
            logger.error(f"Failed to get keywords for {industry}: {e}")
            return self._create_empty_keyword_set(industry)
    
    async def get_risk_categories(self, industry: str) -> List[Dict[str, Any]]:
        """Get industry-specific risk categories and their definitions."""
        risk_categories = {
            IndustryCategory.SAAS: [
                {
                    "category": "Product Risk",
                    "description": "Risks related to product development, feature gaps, and technical issues",
                    "keywords": ["outage", "bug", "security breach", "data loss", "downtime"],
                    "severity_indicators": ["critical", "major", "widespread", "affecting users"]
                },
                {
                    "category": "Competitive Risk",
                    "description": "Risks from competitor actions, new entrants, and market positioning",
                    "keywords": ["competitor launch", "price war", "market share", "new feature"],
                    "severity_indicators": ["major competitor", "significant", "disruptive", "game-changing"]
                },
                {
                    "category": "Regulatory Risk",
                    "description": "Risks from regulatory changes, compliance issues, and legal challenges",
                    "keywords": ["regulation", "compliance", "privacy", "GDPR", "lawsuit"],
                    "severity_indicators": ["regulatory action", "fine", "investigation", "violation"]
                },
                {
                    "category": "Financial Risk",
                    "description": "Risks related to funding, revenue, and financial performance",
                    "keywords": ["funding", "revenue", "losses", "layoffs", "bankruptcy"],
                    "severity_indicators": ["significant", "major", "substantial", "concerning"]
                }
            ],
            IndustryCategory.FINTECH: [
                {
                    "category": "Regulatory Risk",
                    "description": "Financial regulations, compliance requirements, and regulatory changes",
                    "keywords": ["regulation", "compliance", "SEC", "CFPB", "banking rules"],
                    "severity_indicators": ["regulatory action", "fine", "investigation", "non-compliance"]
                },
                {
                    "category": "Security Risk",
                    "description": "Cybersecurity threats, data breaches, and fraud risks",
                    "keywords": ["security breach", "fraud", "cyberattack", "data theft", "hacking"],
                    "severity_indicators": ["major breach", "widespread", "customer data", "financial loss"]
                },
                {
                    "category": "Market Risk",
                    "description": "Market volatility, economic conditions, and competitive pressures",
                    "keywords": ["market volatility", "economic downturn", "competition", "market share"],
                    "severity_indicators": ["significant impact", "major shift", "substantial", "concerning"]
                },
                {
                    "category": "Technology Risk",
                    "description": "Technology failures, system outages, and technical debt",
                    "keywords": ["system failure", "outage", "technical issues", "platform problems"],
                    "severity_indicators": ["critical", "widespread", "affecting transactions", "major impact"]
                }
            ],
            IndustryCategory.HEALTHTECH: [
                {
                    "category": "Regulatory Risk",
                    "description": "FDA approvals, healthcare regulations, and compliance requirements",
                    "keywords": ["FDA", "clinical trial", "regulatory approval", "compliance", "healthcare regulation"],
                    "severity_indicators": ["FDA warning", "trial failure", "regulatory rejection", "compliance issue"]
                },
                {
                    "category": "Clinical Risk",
                    "description": "Clinical trial outcomes, safety issues, and efficacy concerns",
                    "keywords": ["clinical trial", "safety", "efficacy", "adverse events", "patient outcomes"],
                    "severity_indicators": ["trial failure", "safety concern", "adverse events", "efficacy issues"]
                },
                {
                    "category": "Privacy Risk",
                    "description": "Patient data privacy, HIPAA compliance, and data security",
                    "keywords": ["HIPAA", "patient data", "privacy breach", "data security", "PHI"],
                    "severity_indicators": ["data breach", "privacy violation", "HIPAA violation", "patient data exposed"]
                },
                {
                    "category": "Market Access Risk",
                    "description": "Market access, reimbursement, and adoption challenges",
                    "keywords": ["reimbursement", "market access", "adoption", "payer coverage", "healthcare system"],
                    "severity_indicators": ["reimbursement denial", "access restrictions", "adoption challenges", "payer rejection"]
                }
            ]
        }
        
        industry_enum = IndustryCategory(industry) if industry in [e.value for e in IndustryCategory] else None
        return risk_categories.get(industry_enum, self._get_generic_risk_categories())
    
    async def _fetch_industry_insights(self, industry: str) -> IndustryInsights:
        """Fetch comprehensive industry insights using You.com APIs."""
        try:
            # Validate and sanitize industry input
            if not industry or not isinstance(industry, str):
                raise ValueError("Industry parameter must be a non-empty string")
            
            # Sanitize input: trim whitespace, limit length, restrict characters
            industry = industry.strip()
            if len(industry) > 100:
                raise ValueError("Industry name too long (max 100 characters)")
            
            # Allow letters, numbers, spaces, hyphens, ampersands, apostrophes, commas, parentheses, and periods
            if not re.match(r'^[a-zA-Z0-9\s\-&\'",().]+$', industry):
                raise ValueError("Industry name contains invalid characters")
            
            # Use You.com Search API to get industry information
            search_query = f"{industry} industry analysis market size trends 2024"
            # Truncate search query to safe length
            search_query = search_query[:200]
            search_results = await self.you_client.search(search_query, num_results=10)
            
            # Use Custom Agents API for structured analysis
            # Escape industry name for safe inclusion in prompt
            safe_industry = json.dumps(industry)[1:-1]  # Remove quotes from JSON encoding
            analysis_prompt = f"""
            Analyze the {safe_industry} industry and provide structured insights including:
            1. Market size and growth rate
            2. Key trends and developments
            3. Major players and market leaders
            4. Emerging companies to watch
            5. Risk factors and challenges
            6. Opportunities and growth areas
            7. Regulatory environment
            8. Technology trends
            
            Based on the following search results: {json.dumps(search_results[:5])}
            """
            # Truncate prompt to safe length
            analysis_prompt = analysis_prompt[:2000]
            
            structured_analysis = await self.you_client.custom_agent_query(
                query=analysis_prompt,
                agent_type="research_analyst"
            )
            
            # Parse the structured analysis
            insights = self._parse_industry_analysis(industry, structured_analysis)
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to fetch industry insights for {industry}: {e}")
            return self._create_empty_insights(industry)
    
    async def _fetch_competitors(
        self,
        industry: str,
        company_name: Optional[str] = None
    ) -> List[CompetitorProfile]:
        """Fetch competitor information using You.com APIs."""
        try:
            competitors = []
            
            # Search for competitors
            if company_name:
                search_query = f"{company_name} competitors {industry} companies similar"
            else:
                search_query = f"top {industry} companies market leaders startups"
            
            search_results = await self.you_client.search(search_query, num_results=20)
            
            # Extract company names from search results
            company_names = await self._extract_company_names(search_results, industry)
            
            # Get detailed information for each company
            for name in company_names[:15]:  # Limit to avoid API rate limits
                try:
                    competitor_profile = await self._fetch_competitor_profile(name, industry)
                    if competitor_profile:
                        competitors.append(competitor_profile)
                except Exception as e:
                    logger.warning(f"Failed to fetch profile for {name}: {e}")
                    continue
            
            return competitors
            
        except Exception as e:
            logger.error(f"Failed to fetch competitors: {e}")
            return []
    
    async def _fetch_competitor_profile(self, company_name: str, industry: str) -> Optional[CompetitorProfile]:
        """Fetch detailed profile for a specific competitor."""
        try:
            # Search for company information
            search_query = f"{company_name} company profile funding revenue employees"
            search_results = await self.you_client.search(search_query, num_results=5)
            
            # Use Custom Agents API for structured extraction
            extraction_prompt = f"""
            Extract structured information about {company_name} from the search results:
            1. Company description and business model
            2. Founded year and headquarters location
            3. Employee count and market cap (if public)
            4. Revenue and funding information
            5. Key products and services
            6. Target markets and customer segments
            7. Recent news and developments
            8. Competitive advantages
            
            Search results: {json.dumps(search_results)}
            """
            
            structured_data = await self.you_client.custom_agent_query(
                query=extraction_prompt,
                agent_type="data_extractor"
            )
            
            # Parse the structured data into CompetitorProfile
            profile = self._parse_competitor_data(company_name, industry, structured_data)
            
            return profile
            
        except Exception as e:
            logger.error(f"Failed to fetch competitor profile for {company_name}: {e}")
            return None
    
    async def _fetch_industry_keywords(self, industry: str, include_trending: bool) -> KeywordSet:
        """Fetch industry-specific keywords for monitoring."""
        try:
            # Base keywords for different industries
            base_keywords = await self._get_base_keywords(industry)
            
            # Get trending keywords if requested
            trending_keywords = []
            if include_trending:
                trending_keywords = await self._get_trending_keywords(industry)
            
            # Calculate confidence scores
            confidence_scores = {}
            for keyword in base_keywords["primary"] + base_keywords["secondary"]:
                confidence_scores[keyword] = await self._calculate_keyword_confidence(keyword, industry)
            
            keyword_set = KeywordSet(
                industry=industry,
                primary_keywords=base_keywords["primary"],
                secondary_keywords=base_keywords["secondary"],
                negative_keywords=base_keywords["negative"],
                trending_keywords=trending_keywords,
                seasonal_keywords=base_keywords.get("seasonal", {}),
                confidence_scores=confidence_scores,
                last_updated=datetime.now(timezone.utc)
            )
            
            return keyword_set
            
        except Exception as e:
            logger.error(f"Failed to fetch keywords for {industry}: {e}")
            return self._create_empty_keyword_set(industry)
    
    async def _get_base_keywords(self, industry: str) -> Dict[str, Any]:
        """Get base keywords for an industry."""
        industry_keywords = {
            IndustryCategory.SAAS: {
                "primary": ["SaaS", "software", "cloud", "subscription", "platform", "API", "integration"],
                "secondary": ["enterprise", "B2B", "automation", "workflow", "analytics", "dashboard", "CRM"],
                "negative": ["hardware", "physical", "retail", "manufacturing"],
                "seasonal": {
                    "Q4": ["budget", "planning", "renewal", "contract"],
                    "Q1": ["implementation", "onboarding", "training"]
                }
            },
            IndustryCategory.FINTECH: {
                "primary": ["fintech", "payments", "banking", "financial", "cryptocurrency", "blockchain", "lending"],
                "secondary": ["digital wallet", "mobile banking", "robo-advisor", "insurtech", "regtech", "compliance"],
                "negative": ["traditional banking", "brick and mortar", "cash only"],
                "seasonal": {
                    "tax season": ["tax", "filing", "accounting", "bookkeeping"],
                    "year-end": ["financial planning", "investment", "portfolio"]
                }
            },
            IndustryCategory.HEALTHTECH: {
                "primary": ["healthtech", "telemedicine", "digital health", "medical device", "healthcare", "biotech"],
                "secondary": ["EHR", "patient portal", "clinical trial", "FDA approval", "medical AI", "diagnostics"],
                "negative": ["traditional medicine", "non-digital", "paper-based"],
                "seasonal": {
                    "flu season": ["telehealth", "remote consultation", "symptom checker"],
                    "open enrollment": ["health insurance", "benefits", "coverage"]
                }
            }
        }
        
        industry_enum = IndustryCategory(industry) if industry in [e.value for e in IndustryCategory] else None
        return industry_keywords.get(industry_enum, {
            "primary": [industry.lower()],
            "secondary": ["technology", "innovation", "digital"],
            "negative": ["unrelated", "irrelevant"],
            "seasonal": {}
        })
    
    async def _get_trending_keywords(self, industry: str) -> List[str]:
        """Get trending keywords for an industry using You.com Search API."""
        try:
            # Search for trending topics in the industry
            search_query = f"trending {industry} topics 2024 latest developments"
            search_results = await self.you_client.search(search_query, num_results=10)
            
            # Extract trending terms from search results
            trending_terms = []
            for result in search_results:
                title = result.get("title", "")
                description = result.get("description", "")
                
                # Simple keyword extraction (in production, use NLP)
                text = f"{title} {description}".lower()
                words = text.split()
                
                # Filter for relevant trending terms
                for word in words:
                    if (len(word) > 3 and 
                        word not in ["the", "and", "for", "with", "this", "that"] and
                        word not in trending_terms):
                        trending_terms.append(word)
            
            return trending_terms[:10]  # Return top 10 trending terms
            
        except Exception as e:
            logger.error(f"Failed to get trending keywords for {industry}: {e}")
            return []
    
    async def _calculate_keyword_confidence(self, keyword: str, industry: str) -> float:
        """Calculate confidence score for a keyword's relevance to an industry."""
        try:
            # Search for the keyword in context of the industry
            search_query = f"{keyword} {industry}"
            search_results = await self.you_client.search(search_query, num_results=5)
            
            # Simple confidence calculation based on result count and relevance
            if len(search_results) >= 5:
                return 0.9
            elif len(search_results) >= 3:
                return 0.7
            elif len(search_results) >= 1:
                return 0.5
            else:
                return 0.2
                
        except Exception as e:
            logger.warning(f"Failed to calculate confidence for keyword {keyword}: {e}")
            return 0.5  # Default confidence
    
    async def _rank_competitors(
        self,
        competitors: List[CompetitorProfile],
        ranking_factors: List[CompetitorRankingFactor]
    ) -> List[CompetitorProfile]:
        """Rank competitors based on specified factors."""
        try:
            def calculate_score(competitor: CompetitorProfile) -> float:
                score = 0.0
                factor_count = 0
                
                for factor in ranking_factors:
                    if factor == CompetitorRankingFactor.MARKET_CAP and competitor.market_cap:
                        score += min(competitor.market_cap / 1000000000, 10) * 0.3  # Normalize to 0-10, weight 0.3
                        factor_count += 1
                    elif factor == CompetitorRankingFactor.REVENUE and competitor.revenue:
                        score += min(competitor.revenue / 1000000000, 10) * 0.25  # Normalize to 0-10, weight 0.25
                        factor_count += 1
                    elif factor == CompetitorRankingFactor.EMPLOYEE_COUNT and competitor.employee_count:
                        score += min(competitor.employee_count / 10000, 10) * 0.15  # Normalize to 0-10, weight 0.15
                        factor_count += 1
                    elif factor == CompetitorRankingFactor.FUNDING_AMOUNT and competitor.funding_amount:
                        score += min(competitor.funding_amount / 1000000000, 10) * 0.2  # Normalize to 0-10, weight 0.2
                        factor_count += 1
                    elif factor == CompetitorRankingFactor.NEWS_MENTIONS:
                        news_score = len(competitor.recent_news) * 0.5  # 0.5 points per news item
                        score += min(news_score, 5) * 0.1  # Max 5 points, weight 0.1
                        factor_count += 1
                
                # Add confidence score
                score += competitor.confidence_score * 0.1
                
                return score / max(factor_count, 1)  # Average score
            
            # Calculate scores and sort
            scored_competitors = [(competitor, calculate_score(competitor)) for competitor in competitors]
            scored_competitors.sort(key=lambda x: x[1], reverse=True)
            
            return [competitor for competitor, score in scored_competitors]
            
        except Exception as e:
            logger.error(f"Failed to rank competitors: {e}")
            return competitors
    
    def _is_cache_valid(
        self,
        key: str,
        last_update_dict: Dict[str, datetime],
        ttl: Optional[timedelta] = None
    ) -> bool:
        """Check if cached data is still valid."""
        ttl = ttl or self.cache_ttl
        last_update = last_update_dict.get(key)
        if not last_update:
            return False
        return datetime.now(timezone.utc) - last_update < ttl
    
    def _create_empty_insights(self, industry: str) -> IndustryInsights:
        """Create empty industry insights structure."""
        return IndustryInsights(
            industry=industry,
            market_size=None,
            growth_rate=None,
            key_trends=[],
            major_players=[],
            emerging_companies=[],
            risk_factors=[],
            opportunities=[],
            regulatory_environment=[],
            technology_trends=[],
            last_updated=datetime.now(timezone.utc)
        )
    
    def _create_empty_keyword_set(self, industry: str) -> KeywordSet:
        """Create empty keyword set structure."""
        return KeywordSet(
            industry=industry,
            primary_keywords=[],
            secondary_keywords=[],
            negative_keywords=[],
            trending_keywords=[],
            seasonal_keywords={},
            confidence_scores={},
            last_updated=datetime.now(timezone.utc)
        )
    
    def _get_generic_risk_categories(self) -> List[Dict[str, Any]]:
        """Get generic risk categories for unknown industries."""
        return [
            {
                "category": "Competitive Risk",
                "description": "Risks from competitor actions and market changes",
                "keywords": ["competitor", "competition", "market share", "new entrant"],
                "severity_indicators": ["major", "significant", "disruptive", "threatening"]
            },
            {
                "category": "Operational Risk",
                "description": "Risks related to business operations and processes",
                "keywords": ["operational", "process", "efficiency", "disruption"],
                "severity_indicators": ["critical", "major", "widespread", "significant impact"]
            },
            {
                "category": "Financial Risk",
                "description": "Risks related to financial performance and funding",
                "keywords": ["financial", "revenue", "funding", "losses", "cash flow"],
                "severity_indicators": ["substantial", "significant", "concerning", "major"]
            },
            {
                "category": "Regulatory Risk",
                "description": "Risks from regulatory changes and compliance issues",
                "keywords": ["regulatory", "compliance", "legal", "regulation", "policy"],
                "severity_indicators": ["regulatory action", "violation", "investigation", "fine"]
            }
        ]
    
    async def _extract_company_names(self, search_results: List[Dict], industry: str) -> List[str]:
        """Extract company names from search results."""
        company_names = []
        
        for result in search_results:
            title = result.get("title", "")
            description = result.get("description", "")
            
            # Simple company name extraction (in production, use NLP)
            text = f"{title} {description}"
            
            # Look for patterns like "Company Name Inc.", "Company Name Corp", etc.
            patterns = [
                r'\b([A-Z][a-zA-Z\s]+(?:Inc|Corp|LLC|Ltd|Co)\.?)\b',
                r'\b([A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+)*)\s+(?:announced|launched|released|reported)',
                r'\b([A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+)*)\s+(?:CEO|founder|company)'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    if match not in company_names and len(match) > 2:
                        company_names.append(match.strip())
        
        return company_names[:20]  # Return top 20 potential company names
    
    def _parse_industry_analysis(self, industry: str, analysis_text: str) -> IndustryInsights:
        """Parse structured industry analysis from You.com Custom Agents response."""
        # This is a simplified parser - in production, use proper NLP
        try:
            insights = IndustryInsights(
                industry=industry,
                market_size=None,
                growth_rate=None,
                key_trends=[],
                major_players=[],
                emerging_companies=[],
                risk_factors=[],
                opportunities=[],
                regulatory_environment=[],
                technology_trends=[],
                last_updated=datetime.now(timezone.utc)
            )
            
            # Extract information using simple text parsing
            lines = analysis_text.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Identify sections
                if 'market size' in line.lower():
                    current_section = 'market_size'
                elif 'growth rate' in line.lower():
                    current_section = 'growth_rate'
                elif 'trends' in line.lower():
                    current_section = 'trends'
                elif 'major players' in line.lower():
                    current_section = 'players'
                elif 'emerging' in line.lower():
                    current_section = 'emerging'
                elif 'risk' in line.lower():
                    current_section = 'risks'
                elif 'opportunit' in line.lower():
                    current_section = 'opportunities'
                elif 'regulat' in line.lower():
                    current_section = 'regulatory'
                elif 'technology' in line.lower():
                    current_section = 'technology'
                
                # Extract data based on current section
                if current_section == 'trends' and line.startswith('-'):
                    insights.key_trends.append(line[1:].strip())
                elif current_section == 'players' and line.startswith('-'):
                    insights.major_players.append(line[1:].strip())
                elif current_section == 'emerging' and line.startswith('-'):
                    insights.emerging_companies.append(line[1:].strip())
                elif current_section == 'risks' and line.startswith('-'):
                    insights.risk_factors.append(line[1:].strip())
                elif current_section == 'opportunities' and line.startswith('-'):
                    insights.opportunities.append(line[1:].strip())
                elif current_section == 'regulatory' and line.startswith('-'):
                    insights.regulatory_environment.append(line[1:].strip())
                elif current_section == 'technology' and line.startswith('-'):
                    insights.technology_trends.append(line[1:].strip())
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to parse industry analysis: {e}")
            return self._create_empty_insights(industry)
    
    def _parse_competitor_data(self, company_name: str, industry: str, data_text: str) -> CompetitorProfile:
        """Parse competitor data from You.com Custom Agents response."""
        # Simplified parser - in production, use proper NLP and structured extraction
        try:
            profile = CompetitorProfile(
                name=company_name,
                industry=industry,
                description="",
                website=None,
                founded_year=None,
                headquarters=None,
                employee_count=None,
                market_cap=None,
                revenue=None,
                funding_amount=None,
                last_funding_round=None,
                key_products=[],
                target_markets=[],
                competitive_advantages=[],
                recent_news=[],
                social_metrics={},
                risk_factors=[],
                confidence_score=0.7,  # Default confidence
                last_updated=datetime.now(timezone.utc)
            )
            
            # Extract basic information using simple text parsing
            lines = data_text.split('\n')
            for line in lines:
                line = line.strip().lower()
                
                if 'founded' in line and 'year' in line:
                    # Extract year
                    year_match = re.search(r'\b(19|20)\d{2}\b', line)
                    if year_match:
                        profile.founded_year = int(year_match.group())
                
                elif 'employee' in line:
                    # Extract employee count
                    num_match = re.search(r'\b(\d{1,3}(?:,\d{3})*)\b', line)
                    if num_match:
                        profile.employee_count = int(num_match.group().replace(',', ''))
                
                elif 'description' in line or 'business' in line:
                    profile.description = line
            
            return profile
            
        except Exception as e:
            logger.error(f"Failed to parse competitor data for {company_name}: {e}")
            return CompetitorProfile(
                name=company_name,
                industry=industry,
                description=f"{company_name} is a company in the {industry} industry.",
                website=None,
                founded_year=None,
                headquarters=None,
                employee_count=None,
                market_cap=None,
                revenue=None,
                funding_amount=None,
                last_funding_round=None,
                key_products=[],
                target_markets=[],
                competitive_advantages=[],
                recent_news=[],
                social_metrics={},
                risk_factors=[],
                confidence_score=0.5,
                last_updated=datetime.now(timezone.utc)
            )
    
    async def refresh_all_industry_data(self) -> Dict[str, bool]:
        """Refresh all cached industry data."""
        results = {}
        
        for industry in IndustryCategory:
            try:
                await self.get_industry_insights(industry.value, force_refresh=True)
                await self.discover_competitors(industry.value, limit=20)
                await self.get_industry_keywords(industry.value, force_refresh=True)
                results[industry.value] = True
                logger.info(f"Successfully refreshed data for {industry.value}")
            except Exception as e:
                logger.error(f"Failed to refresh data for {industry.value}: {e}")
                results[industry.value] = False
        
        return results
    
    async def get_industry_statistics(self) -> Dict[str, Any]:
        """Get statistics about cached industry data."""
        return {
            "cached_industries": len(self._industry_cache),
            "cached_competitor_sets": len(self._competitor_cache),
            "cached_keyword_sets": len(self._keyword_cache),
            "last_updates": {
                "industries": dict(self._last_industry_update),
                "competitors": dict(self._last_competitor_update),
                "keywords": dict(self._last_keyword_update)
            },
            "cache_ttl_hours": self.cache_ttl.total_seconds() / 3600,
            "competitor_cache_ttl_hours": self.competitor_cache_ttl.total_seconds() / 3600
        }