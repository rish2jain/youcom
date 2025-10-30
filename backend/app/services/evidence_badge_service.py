"""
Service for managing evidence badges and confidence scoring.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.evidence_badge import EvidenceBadge, SourceEvidence
from ..models.impact_card import ImpactCard
from ..schemas.evidence_badge import (
    EvidenceBadgeCreate, 
    SourceEvidenceCreate, 
    EvidenceBadgeResponse,
    ConfidenceMetrics
)

logger = logging.getLogger(__name__)

class EvidenceBadgeService:
    """Service for managing evidence badges and confidence scoring."""
    
    # Source tier definitions
    TIER_DEFINITIONS = {
        1: {"name": "Authoritative", "sources": ["WSJ", "Reuters", "Bloomberg", "Financial Times"]},
        2: {"name": "Reputable", "sources": ["TechCrunch", "VentureBeat", "The Information"]},
        3: {"name": "Community", "sources": ["Hacker News", "Reddit", "Medium"]},
        4: {"name": "Unverified", "sources": ["Blogs", "Twitter", "Press Releases"]}
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_evidence_badge(
        self,
        entity_type: str,
        entity_id: int,
        sources: List[Dict[str, Any]],
        confidence_override: Optional[float] = None
    ) -> EvidenceBadge:
        """Create an evidence badge with confidence and source analysis."""
        
        # Analyze sources
        source_analysis = self._analyze_sources(sources)
        
        # Calculate confidence
        confidence = confidence_override or await self._calculate_confidence(source_analysis, sources)
        
        # Create badge
        badge_data = EvidenceBadgeCreate(
            entity_type=entity_type,
            entity_id=entity_id,
            confidence_percentage=confidence,
            total_sources=len(sources),
            tier_1_sources=source_analysis["tier_counts"][1],
            tier_2_sources=source_analysis["tier_counts"][2],
            tier_3_sources=source_analysis["tier_counts"][3],
            tier_4_sources=source_analysis["tier_counts"][4],
            freshness_score=source_analysis["freshness_score"],
            oldest_source_hours=source_analysis["oldest_hours"],
            newest_source_hours=source_analysis["newest_hours"],
            average_source_age_hours=source_analysis["average_age_hours"],
            cross_validation_score=source_analysis["cross_validation_score"],
            bias_detection_score=source_analysis["bias_score"],
            fact_check_score=source_analysis["fact_check_score"],
            top_sources=source_analysis["top_sources"]
        )
        
        badge = EvidenceBadge(**badge_data.dict())
        
        # Set computed display properties
        badge.confidence_level = self._get_confidence_level(confidence)
        badge.badge_color = self._get_badge_color(confidence, source_analysis)
        badge.badge_icon = self._get_badge_icon(confidence, source_analysis)
        badge.display_text = self._get_display_text(confidence, len(sources))
        
        self.db.add(badge)
        self.db.flush()  # Get the ID
        
        # Add detailed source evidence
        for source_data in sources:
            source_evidence = SourceEvidence(
                badge_id=badge.id,
                source_name=source_data.get("name", "Unknown"),
                source_url=source_data.get("url", ""),
                source_tier=self._classify_source_tier(source_data.get("name", "")),
                title=source_data.get("title"),
                excerpt=source_data.get("excerpt"),
                publish_date=self._parse_publish_date(source_data.get("publish_date")),
                relevance_score=source_data.get("relevance_score"),
                credibility_score=source_data.get("credibility_score"),
                sentiment_score=source_data.get("sentiment_score"),
                you_api_source=source_data.get("you_api_source")
            )
            self.db.add(source_evidence)
        
        self.db.commit()
        self.db.refresh(badge)
        
        logger.info(f"Created evidence badge for {entity_type}:{entity_id} with {confidence:.1f}% confidence")
        return badge
    
    def get_evidence_badge(
        self, 
        entity_type: str, 
        entity_id: int
    ) -> Optional[EvidenceBadge]:
        """Get evidence badge for an entity."""
        return self.db.query(EvidenceBadge).filter(
            and_(
                EvidenceBadge.entity_type == entity_type,
                EvidenceBadge.entity_id == entity_id
            )
        ).first()
    
    async def get_expanded_evidence(
        self, 
        entity_type: str, 
        entity_id: int
    ) -> Optional[EvidenceBadgeResponse]:
        """Get evidence badge with expanded source details."""
        badge = self.get_evidence_badge(entity_type, entity_id)
        if not badge:
            return None
        
        # Get top 3 sources for expansion
        top_sources = self.db.query(SourceEvidence).filter(
            SourceEvidence.badge_id == badge.id
        ).order_by(
            SourceEvidence.source_tier.asc(),
            SourceEvidence.relevance_score.desc()
        ).limit(3).all()
        
        # Generate quality breakdown
        quality_breakdown = {
            "confidence_breakdown": {
                "source_quality": badge.weighted_source_score * 100,
                "freshness": badge.freshness_score * 100,
                "cross_validation": (badge.cross_validation_score or 0.5) * 100,
                "fact_checking": (badge.fact_check_score or 0.5) * 100
            },
            "source_distribution": {
                f"tier_{i}": getattr(badge, f"tier_{i}_sources") 
                for i in range(1, 5)
            },
            "freshness_details": {
                "newest_hours": badge.newest_source_hours,
                "oldest_hours": badge.oldest_source_hours,
                "average_hours": badge.average_source_age_hours
            }
        }
        
        # Generate recommendations
        recommendations = await self._generate_evidence_recommendations(badge)
        
        return EvidenceBadgeResponse(
            badge=badge,
            top_sources_expanded=top_sources,
            quality_breakdown=quality_breakdown,
            recommendations=recommendations
        )
    
    async def get_confidence_metrics(
        self, 
        entity_type: str, 
        entity_id: int
    ) -> Optional[ConfidenceMetrics]:
        """Get simplified confidence metrics for display."""
        badge = self.get_evidence_badge(entity_type, entity_id)
        if not badge:
            return None
        
        # Tier breakdown
        tier_breakdown = {
            "tier_1": badge.tier_1_sources,
            "tier_2": badge.tier_2_sources,
            "tier_3": badge.tier_3_sources,
            "tier_4": badge.tier_4_sources
        }
        
        # Freshness indicator
        freshness_indicator = self._get_freshness_indicator(badge.freshness_score)
        
        # Quality indicators
        quality_indicators = []
        if badge.tier_1_sources > 0:
            quality_indicators.append("Authoritative sources")
        if badge.cross_validation_score and badge.cross_validation_score > 0.8:
            quality_indicators.append("Cross-validated")
        if badge.freshness_score > 0.8:
            quality_indicators.append("Very fresh")
        if badge.fact_check_score and badge.fact_check_score > 0.8:
            quality_indicators.append("Fact-checked")
        
        return ConfidenceMetrics(
            overall_confidence=badge.confidence_percentage,
            confidence_level=badge.confidence_level,
            source_count=badge.total_sources,
            tier_breakdown=tier_breakdown,
            freshness_indicator=freshness_indicator,
            quality_indicators=quality_indicators
        )
    
    def _analyze_sources(self, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze source quality and characteristics."""
        if not sources:
            return {
                "tier_counts": {1: 0, 2: 0, 3: 0, 4: 0},
                "freshness_score": 0.0,
                "oldest_hours": None,
                "newest_hours": None,
                "average_age_hours": None,
                "cross_validation_score": 0.0,
                "bias_score": 0.5,
                "fact_check_score": 0.5,
                "top_sources": []
            }
        
        # Classify sources by tier
        tier_counts = {1: 0, 2: 0, 3: 0, 4: 0}
        source_ages = []
        
        for source in sources:
            tier = self._classify_source_tier(source.get("name", ""))
            tier_counts[tier] += 1
            
            # Calculate source age
            publish_date = self._parse_publish_date(source.get("publish_date"))
            if publish_date:
                age_hours = (datetime.now(timezone.utc) - publish_date).total_seconds() / 3600
                source_ages.append(age_hours)
        
        # Calculate freshness metrics
        if source_ages:
            oldest_hours = max(source_ages)
            newest_hours = min(source_ages)
            average_age_hours = sum(source_ages) / len(source_ages)
            
            # Freshness score: newer is better, exponential decay
            freshness_score = sum(
                max(0, 1 - (age / 168))  # 168 hours = 1 week
                for age in source_ages
            ) / len(source_ages)
        else:
            oldest_hours = newest_hours = average_age_hours = None
            freshness_score = 0.5  # Default for unknown
        
        # Cross-validation score (simplified)
        cross_validation_score = min(1.0, len(sources) / 3) * 0.8  # More sources = better validation
        
        # Select top sources
        top_sources = sorted(
            sources,
            key=lambda s: (
                self._classify_source_tier(s.get("name", "")),  # Lower tier number = higher quality
                -(s.get("relevance_score", 0.5))  # Higher relevance first
            )
        )[:3]
        
        return {
            "tier_counts": tier_counts,
            "freshness_score": max(0.0, min(1.0, freshness_score)),
            "oldest_hours": oldest_hours,
            "newest_hours": newest_hours,
            "average_age_hours": average_age_hours,
            "cross_validation_score": cross_validation_score,
            "bias_score": 0.3,  # Simplified bias detection
            "fact_check_score": 0.7,  # Simplified fact checking
            "top_sources": [
                {
                    "name": s.get("name"),
                    "url": s.get("url"),
                    "title": s.get("title"),
                    "tier": self._classify_source_tier(s.get("name", ""))
                }
                for s in top_sources
            ]
        }
    
    async def _calculate_confidence(
        self, 
        source_analysis: Dict[str, Any], 
        sources: List[Dict[str, Any]]
    ) -> float:
        """Calculate overall confidence score."""
        if not sources:
            return 0.0
        
        # Base confidence from source quality
        tier_weights = {1: 1.0, 2: 0.8, 3: 0.6, 4: 0.3}
        weighted_quality = sum(
            source_analysis["tier_counts"][tier] * weight
            for tier, weight in tier_weights.items()
        ) / len(sources)
        
        # Freshness bonus
        freshness_bonus = source_analysis["freshness_score"] * 0.2
        
        # Cross-validation bonus
        validation_bonus = source_analysis["cross_validation_score"] * 0.1
        
        # Source count bonus (diminishing returns)
        count_bonus = min(0.2, len(sources) / 10 * 0.2)
        
        # Calculate final confidence
        confidence = (weighted_quality * 0.6 + freshness_bonus + validation_bonus + count_bonus) * 100
        
        return max(0.0, min(100.0, confidence))
    
    def _classify_source_tier(self, source_name: str) -> int:
        """Classify source into tier based on name."""
        source_lower = source_name.lower()
        
        # Tier 1: Authoritative
        tier_1_keywords = ["wsj", "wall street journal", "reuters", "bloomberg", "financial times", "ft.com"]
        if any(keyword in source_lower for keyword in tier_1_keywords):
            return 1
        
        # Tier 2: Reputable
        tier_2_keywords = ["techcrunch", "venturebeat", "the information", "axios", "forbes"]
        if any(keyword in source_lower for keyword in tier_2_keywords):
            return 2
        
        # Tier 3: Community
        tier_3_keywords = ["hacker news", "reddit", "medium", "ycombinator"]
        if any(keyword in source_lower for keyword in tier_3_keywords):
            return 3
        
        # Tier 4: Default (unverified)
        return 4
    
    def _parse_publish_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse publish date string to datetime."""
        import logging
        
        if not date_str:
            return None
        
        try:
            # Try common formats
            for fmt in ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"]:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            # If parsing fails, log warning and return None
            logging.warning(f"Failed to parse date string: {date_str}")
            return None
        except Exception as e:
            logging.warning(f"Exception parsing date string '{date_str}': {str(e)}")
            return None
    
    def _get_confidence_level(self, confidence: float) -> str:
        """Get confidence level string."""
        if confidence >= 85:
            return "very_high"
        elif confidence >= 70:
            return "high"
        elif confidence >= 50:
            return "medium"
        else:
            return "low"
    
    def _get_badge_color(self, confidence: float, source_analysis: Dict[str, Any]) -> str:
        """Get badge color based on confidence and source quality."""
        if confidence >= 85 and source_analysis["tier_counts"][1] > 0:
            return "green"
        elif confidence >= 70:
            return "blue"
        elif confidence >= 50:
            return "yellow"
        else:
            return "red"
    
    def _get_badge_icon(self, confidence: float, source_analysis: Dict[str, Any]) -> str:
        """Get badge icon based on confidence and source quality."""
        if confidence >= 85:
            return "shield-check"
        elif confidence >= 70:
            return "check-circle"
        elif confidence >= 50:
            return "info-circle"
        else:
            return "alert-triangle"
    
    def _get_display_text(self, confidence: float, source_count: int) -> str:
        """Get display text for badge."""
        confidence_text = f"{confidence:.0f}% confident"
        source_text = f"{source_count} source{'s' if source_count != 1 else ''}"
        return f"{confidence_text} • {source_text}"
    
    def _get_freshness_indicator(self, freshness_score: float) -> str:
        """Get freshness indicator string."""
        if freshness_score >= 0.8:
            return "very_fresh"
        elif freshness_score >= 0.6:
            return "fresh"
        elif freshness_score >= 0.3:
            return "stale"
        else:
            return "very_stale"
    
    async def _generate_evidence_recommendations(self, badge: EvidenceBadge) -> List[str]:
        """Generate recommendations based on evidence quality."""
        recommendations = []
        
        # Confidence-based recommendations
        if badge.confidence_percentage < 50:
            recommendations.append("Low confidence - seek additional sources before acting")
        elif badge.confidence_percentage < 70:
            recommendations.append("Moderate confidence - validate with stakeholders")
        
        # Source quality recommendations
        if badge.tier_1_sources == 0 and badge.total_sources > 0:
            recommendations.append("No authoritative sources - consider seeking tier-1 validation")
        
        if badge.tier_4_sources > badge.tier_1_sources + badge.tier_2_sources:
            recommendations.append("Mostly unverified sources - treat insights as preliminary")
        
        # Freshness recommendations
        if badge.freshness_score < 0.3:
            recommendations.append("Sources are stale - check for more recent developments")
        
        # Cross-validation recommendations
        if badge.cross_validation_score and badge.cross_validation_score < 0.5:
            recommendations.append("Limited cross-validation - seek corroborating evidence")
        
        # Default positive recommendations
        if not recommendations:
            if badge.confidence_percentage >= 85:
                recommendations.append("High confidence - suitable for strategic decisions")
            else:
                recommendations.append("Good evidence quality - proceed with normal validation")
        
        return recommendations[:3]  # Limit to top 3