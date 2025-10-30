"""
Service for managing insight timelines and delta analysis.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from dateutil import parser as date_parser

from ..models.insight_timeline import InsightTimeline, DeltaHighlight, TrendSparkline
from ..models.impact_card import ImpactCard
from ..schemas.insight_timeline import (
    InsightTimelineCreate, 
    DeltaHighlightCreate, 
    TrendSparklineCreate,
    InsightDeltaResponse
)

logger = logging.getLogger(__name__)

class InsightTimelineService:
    """Service for managing insight timelines and delta analysis."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_timeline_entry(
        self, 
        timeline_data: InsightTimelineCreate,
        highlights: Optional[List[DeltaHighlightCreate]] = None
    ) -> InsightTimeline:
        """Create a new timeline entry with optional highlights."""
        
        # Calculate risk score delta if previous score exists
        risk_score_delta = None
        if timeline_data.previous_risk_score is not None:
            risk_score_delta = timeline_data.current_risk_score - timeline_data.previous_risk_score
        
        # Create timeline entry
        timeline = InsightTimeline(
            impact_card_id=timeline_data.impact_card_id,
            company_name=timeline_data.company_name,
            current_risk_score=timeline_data.current_risk_score,
            previous_risk_score=timeline_data.previous_risk_score,
            risk_score_delta=risk_score_delta,
            new_stories_count=timeline_data.new_stories_count,
            updated_stories_count=timeline_data.updated_stories_count,
            new_evidence_count=timeline_data.new_evidence_count,
            key_changes=timeline_data.key_changes,
            fresh_insights=timeline_data.fresh_insights,
            trend_shifts=timeline_data.trend_shifts,
            previous_analysis_date=timeline_data.previous_analysis_date,
            analysis_version=timeline_data.analysis_version,
            confidence_score=timeline_data.confidence_score
        )
        
        self.db.add(timeline)
        self.db.flush()  # Get the ID
        
        # Add highlights if provided
        if highlights:
            for highlight_data in highlights:
                highlight = DeltaHighlight(
                    timeline_id=timeline.id,
                    **highlight_data.dict()
                )
                self.db.add(highlight)
        
        self.db.commit()
        self.db.refresh(timeline)
        
        logger.info(f"Created timeline entry for {timeline_data.company_name} with {len(highlights or [])} highlights")
        return timeline
    
    async def get_latest_timeline(self, company_name: str) -> Optional[InsightTimeline]:
        """Get the most recent timeline entry for a company."""
        return self.db.query(InsightTimeline).filter(
            InsightTimeline.company_name == company_name
        ).order_by(desc(InsightTimeline.created_at)).first()
    
    async def get_timeline_history(
        self, 
        company_name: str, 
        limit: int = 10
    ) -> List[InsightTimeline]:
        """Get timeline history for a company."""
        return self.db.query(InsightTimeline).filter(
            InsightTimeline.company_name == company_name
        ).order_by(desc(InsightTimeline.created_at)).limit(limit).all()
    
    async def analyze_delta_since_last_run(
        self, 
        company_name: str, 
        impact_card_id: int
    ) -> InsightDeltaResponse:
        """Analyze changes since the last analysis run."""
        
        # Get the current impact card
        from ..models.impact_card import ImpactCard
        current_impact_card = self.db.query(ImpactCard).filter(ImpactCard.id == impact_card_id).first()
        if not current_impact_card:
            raise ValueError(f"Impact card {impact_card_id} not found")
        
        # Get the previous timeline entry
        previous_timeline = await self.get_latest_timeline(company_name)
        
        # Calculate deltas
        delta_analysis = await self._calculate_deltas(
            company_name, 
            current_impact_card, 
            previous_timeline
        )
        
        # Create new timeline entry
        timeline_data = InsightTimelineCreate(
            impact_card_id=current_impact_card.id,
            company_name=company_name,
            current_risk_score=current_impact_card.risk_score,
            previous_risk_score=previous_timeline.current_risk_score if previous_timeline else None,
            previous_analysis_date=previous_timeline.created_at if previous_timeline else None,
            new_stories_count=delta_analysis["new_stories_count"],
            updated_stories_count=delta_analysis["updated_stories_count"],
            new_evidence_count=delta_analysis["new_evidence_count"],
            key_changes=delta_analysis["key_changes"],
            fresh_insights=delta_analysis["fresh_insights"],
            trend_shifts=delta_analysis["trend_shifts"],
            confidence_score=delta_analysis["confidence_score"]
        )
        
        # Create highlights
        highlights = await self._generate_delta_highlights(delta_analysis, previous_timeline)
        
        # Save timeline entry
        timeline = await self.create_timeline_entry(timeline_data, highlights)
        
        # Update sparkline data and create timeline entry in transaction
        try:
            timeline = await self.create_timeline_entry(timeline_data, highlights)
            sparkline = await self._update_sparkline_data(company_name, current_impact_card.risk_score)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create timeline entry and update sparkline: {str(e)}")
            raise
        
        # Generate summary and recommendations
        summary = await self._generate_delta_summary(timeline, previous_timeline)
        recommendations = await self._generate_delta_recommendations(timeline, delta_analysis)
        
        return InsightDeltaResponse(
            timeline=timeline,
            sparkline_data=sparkline,
            summary=summary,
            recommendations=recommendations
        )
    
    async def _calculate_deltas(
        self, 
        company_name: str, 
        current_card: ImpactCard, 
        previous_timeline: Optional[InsightTimeline]
    ) -> Dict[str, Any]:
        """Calculate deltas between current and previous analysis."""
        
        if not previous_timeline:
            return {
                "new_stories_count": len(current_card.sources or []),
                "updated_stories_count": 0,
                "new_evidence_count": len(current_card.sources or []),
                "key_changes": ["Initial analysis - no previous data"],
                "fresh_insights": current_card.key_insights or [],
                "trend_shifts": [],
                "confidence_score": 0.8  # Default for first analysis
            }
        
        # Simulate delta calculation (in real implementation, this would compare actual data)
        time_since_last = datetime.utcnow() - previous_timeline.created_at
        hours_since = time_since_last.total_seconds() / 3600
        
        # Estimate new content based on time elapsed
        estimated_new_stories = max(0, int(hours_since / 6))  # ~4 stories per day
        estimated_updates = max(0, int(hours_since / 12))     # ~2 updates per day
        
        key_changes = []
        if previous_timeline.current_risk_score != current_card.risk_score:
            delta = current_card.risk_score - previous_timeline.current_risk_score
            direction = "increased" if delta > 0 else "decreased"
            key_changes.append(f"Risk score {direction} by {abs(delta):.1f} points")
        
        if estimated_new_stories > 0:
            key_changes.append(f"{estimated_new_stories} new stories detected")
        
        if estimated_updates > 0:
            key_changes.append(f"{estimated_updates} existing stories updated")
        
        return {
            "new_stories_count": estimated_new_stories,
            "updated_stories_count": estimated_updates,
            "new_evidence_count": estimated_new_stories,
            "key_changes": key_changes or ["No significant changes detected"],
            "fresh_insights": current_card.key_insights or [],
            "trend_shifts": self._detect_trend_shifts(previous_timeline, current_card),
            "confidence_score": min(0.9, 0.6 + (hours_since / 24) * 0.1)  # Higher confidence with more time
        }
    
    def _detect_trend_shifts(
        self, 
        previous_timeline: InsightTimeline, 
        current_card: ImpactCard
    ) -> List[str]:
        """Detect trend shifts between analyses."""
        shifts = []
        
        # Risk score trend
        if previous_timeline.risk_score_delta is not None:
            current_delta = current_card.risk_score - previous_timeline.current_risk_score
            
            if previous_timeline.risk_score_delta > 0 and current_delta < 0:
                shifts.append("Risk trend reversed from increasing to decreasing")
            elif previous_timeline.risk_score_delta < 0 and current_delta > 0:
                shifts.append("Risk trend reversed from decreasing to increasing")
            elif abs(current_delta) > abs(previous_timeline.risk_score_delta) * 1.5:
                direction = "acceleration" if current_delta > 0 else "deceleration"
                shifts.append(f"Risk trend showing {direction}")
        
        return shifts
    
    async def _generate_delta_highlights(
        self, 
        delta_analysis: Dict[str, Any], 
        previous_timeline: Optional[InsightTimeline]
    ) -> List[DeltaHighlightCreate]:
        """Generate highlight objects for the delta analysis."""
        highlights = []
        
        # New stories highlight
        if delta_analysis["new_stories_count"] > 0:
            highlights.append(DeltaHighlightCreate(
                highlight_type="new_story",
                title=f"{delta_analysis['new_stories_count']} new stories detected",
                description="Fresh competitive intelligence since your last analysis",
                importance_score=min(1.0, delta_analysis["new_stories_count"] / 10),
                freshness_hours=1,  # Assume very fresh
                badge_type="new",
                badge_color="green"
            ))
        
        # Risk score change highlight
        if previous_timeline and previous_timeline.current_risk_score:
            risk_delta = delta_analysis.get("risk_score_delta", 0)
            if abs(risk_delta) > 5:  # Significant change
                direction = "increased" if risk_delta > 0 else "decreased"
                color = "red" if risk_delta > 0 else "green"
                highlights.append(DeltaHighlightCreate(
                    highlight_type="risk_change",
                    title=f"Risk score {direction} by {abs(risk_delta):.1f} points",
                    description=f"Competitive risk level has {direction} since last analysis",
                    importance_score=min(1.0, abs(risk_delta) / 20),
                    freshness_hours=0,  # Current analysis
                    badge_type="alert" if abs(risk_delta) > 10 else "updated",
                    badge_color=color
                ))
        
        # Trend shifts highlight
        if delta_analysis["trend_shifts"]:
            for shift in delta_analysis["trend_shifts"]:
                highlights.append(DeltaHighlightCreate(
                    highlight_type="trend_shift",
                    title="Trend shift detected",
                    description=shift,
                    importance_score=0.8,
                    freshness_hours=0,
                    badge_type="trending",
                    badge_color="blue"
                ))
        
        return highlights
    
    async def _update_sparkline_data(
        self, 
        company_name: str, 
        current_risk_score: float
    ) -> TrendSparkline:
        """Update or create sparkline trend data."""
        
        # Get existing sparkline or create new one
        sparkline = self.db.query(TrendSparkline).filter(
            and_(
                TrendSparkline.company_name == company_name,
                TrendSparkline.metric_type == "risk_score",
                TrendSparkline.time_range == "30d"
            )
        ).first()
        
        current_time = datetime.now(timezone.utc)
        new_data_point = {
            "timestamp": current_time.isoformat(),
            "value": current_risk_score
        }
        
        if sparkline:
            # Update existing sparkline
            data_points = sparkline.data_points or []
            data_points.append(new_data_point)
            
            # Keep only last 30 days of data
            cutoff_date = current_time - timedelta(days=30)
            filtered_points = []
            for point in data_points:
                try:
                    point_time = date_parser.parse(point["timestamp"])
                    if point_time.tzinfo is None:
                        point_time = point_time.replace(tzinfo=timezone.utc)
                    if point_time > cutoff_date:
                        filtered_points.append(point)
                except (ValueError, KeyError) as e:
                    logger.warning(f"Skipping malformed timestamp in sparkline data: {point.get('timestamp', 'missing')}: {str(e)}")
                    continue
            data_points = filtered_points
            
            sparkline.data_points = data_points
            sparkline.last_updated = current_time
            
            # Calculate trend
            if len(data_points) >= 2:
                recent_values = [point["value"] for point in data_points[-7:]]  # Last week
                older_values = [point["value"] for point in data_points[-14:-7]]  # Week before
                
                if older_values:
                    recent_avg = sum(recent_values) / len(recent_values)
                    older_avg = sum(older_values) / len(older_values)
                    
                    if recent_avg > older_avg * 1.1:
                        sparkline.trend_direction = "up"
                        sparkline.trend_strength = min(1.0, (recent_avg - older_avg) / older_avg)
                    elif recent_avg < older_avg * 0.9:
                        sparkline.trend_direction = "down"
                        sparkline.trend_strength = min(1.0, (older_avg - recent_avg) / older_avg)
                    else:
                        sparkline.trend_direction = "stable"
                        sparkline.trend_strength = 0.1
        else:
            # Create new sparkline
            sparkline_data = TrendSparklineCreate(
                company_name=company_name,
                metric_type="risk_score",
                data_points=[new_data_point],
                time_range="30d",
                trend_direction="stable",
                trend_strength=0.1
            )
            
            sparkline = TrendSparkline(**sparkline_data.dict())
            self.db.add(sparkline)
        
        self.db.commit()
        self.db.refresh(sparkline)
        
        return sparkline
    
    async def _generate_delta_summary(
        self, 
        timeline: InsightTimeline, 
        previous_timeline: Optional[InsightTimeline]
    ) -> Dict[str, Any]:
        """Generate a summary of the delta analysis."""
        
        if not previous_timeline:
            return {
                "status": "initial_analysis",
                "message": "This is your first analysis for this company",
                "time_since_last": None,
                "key_metrics": {
                    "risk_score": timeline.current_risk_score,
                    "new_stories": timeline.new_stories_count,
                    "evidence_count": timeline.new_evidence_count
                }
            }
        
        time_since = timeline.created_at - previous_timeline.created_at
        hours_since = time_since.total_seconds() / 3600
        
        # Determine status based on changes
        status = "no_changes"
        if timeline.risk_score_delta and abs(timeline.risk_score_delta) > 10:
            status = "significant_changes"
        elif timeline.new_stories_count > 0 or timeline.updated_stories_count > 0:
            status = "minor_changes"
        
        return {
            "status": status,
            "message": f"Analysis updated after {hours_since:.1f} hours",
            "time_since_last": {
                "hours": hours_since,
                "formatted": f"{int(hours_since)}h {int((hours_since % 1) * 60)}m ago"
            },
            "key_metrics": {
                "risk_score": timeline.current_risk_score,
                "risk_score_change": timeline.risk_score_delta,
                "new_stories": timeline.new_stories_count,
                "updated_stories": timeline.updated_stories_count,
                "evidence_count": timeline.new_evidence_count
            }
        }
    
    async def _generate_delta_recommendations(
        self, 
        timeline: InsightTimeline, 
        delta_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on delta analysis."""
        recommendations = []
        
        # Risk score based recommendations
        if timeline.risk_score_delta:
            if timeline.risk_score_delta > 15:
                recommendations.append("High risk increase detected - consider immediate strategic response")
                recommendations.append("Review new competitive threats and update defensive strategies")
            elif timeline.risk_score_delta > 5:
                recommendations.append("Moderate risk increase - monitor closely and prepare contingency plans")
            elif timeline.risk_score_delta < -10:
                recommendations.append("Risk level decreased significantly - opportunity to advance initiatives")
        
        # New content recommendations
        if timeline.new_stories_count > 5:
            recommendations.append("High volume of new intelligence - prioritize review of top-impact stories")
        elif timeline.new_stories_count > 0:
            recommendations.append("New competitive intelligence available - review fresh insights")
        
        # Trend-based recommendations
        if delta_analysis["trend_shifts"]:
            recommendations.append("Trend shifts detected - reassess strategic assumptions and forecasts")
        
        # Default recommendations if none generated
        if not recommendations:
            recommendations.extend([
                "Continue monitoring competitive landscape",
                "Review insights for strategic planning opportunities",
                "Share findings with relevant stakeholders"
            ])
        
        return recommendations[:5]  # Limit to top 5 recommendations