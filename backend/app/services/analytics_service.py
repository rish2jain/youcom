"""Predictive analytics service for competitive intelligence"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
import statistics
import json

from app.models.impact_card import ImpactCard
from app.models.company_research import CompanyResearch
from app.models.api_call_log import ApiCallLog

logger = logging.getLogger(__name__)


class PredictiveAnalyticsService:
    """Service for generating predictive insights and trends"""

    @staticmethod
    async def analyze_competitor_trends(
        competitor_name: str,
        days_back: int = 30,
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """Analyze trends for a specific competitor"""
        
        if not db:
            return {"status": "error", "error": "Database session required"}

        try:
            # Get historical impact cards
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
            
            impact_cards_query = await db.execute(
                select(ImpactCard).where(
                    and_(
                        ImpactCard.competitor_name == competitor_name,
                        ImpactCard.created_at >= cutoff_date
                    )
                ).order_by(ImpactCard.created_at)
            )
            impact_cards = impact_cards_query.scalars().all()

            if len(impact_cards) < 2:
                return {
                    "status": "success",
                    "competitor": competitor_name,
                    "trend": "insufficient_data",
                    "message": "Need at least 2 data points for trend analysis"
                }

            # Calculate trend metrics
            risk_scores = [card.risk_score for card in impact_cards]
            confidence_scores = [card.confidence_score for card in impact_cards]
            
            # Risk score trend
            risk_trend = "stable"
            if len(risk_scores) >= 3:
                recent_avg = statistics.mean(risk_scores[-3:])
                older_avg = statistics.mean(risk_scores[:-3]) if len(risk_scores) > 3 else risk_scores[0]
                
                if recent_avg > older_avg + 10:
                    risk_trend = "increasing"
                elif recent_avg < older_avg - 10:
                    risk_trend = "decreasing"

            # Activity frequency
            activity_frequency = len(impact_cards) / days_back * 7  # Per week

            # Confidence trend
            confidence_trend = statistics.mean(confidence_scores) if confidence_scores else 0

            return {
                "status": "success",
                "competitor": competitor_name,
                "analysis_period_days": days_back,
                "total_activities": len(impact_cards),
                "activity_frequency_per_week": round(activity_frequency, 2),
                "risk_trend": risk_trend,
                "average_risk_score": round(statistics.mean(risk_scores), 1),
                "latest_risk_score": risk_scores[-1],
                "average_confidence": round(confidence_trend, 1),
                "prediction": PredictiveAnalyticsService._generate_prediction(
                    risk_trend, activity_frequency, statistics.mean(risk_scores)
                )
            }

        except Exception as e:
            logger.error(f"❌ Competitor trend analysis failed: {str(e)}")
            return {"status": "error", "error": str(e)}

    @staticmethod
    async def market_landscape_analysis(
        days_back: int = 30,
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """Analyze overall market landscape and competitive activity"""
        
        if not db:
            return {"status": "error", "error": "Database session required"}

        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
            
            # Get all impact cards in period
            impact_cards_query = await db.execute(
                select(ImpactCard).where(
                    ImpactCard.created_at >= cutoff_date
                )
            )
            impact_cards = impact_cards_query.scalars().all()

            if not impact_cards:
                return {
                    "status": "success",
                    "message": "No competitive activity in the specified period"
                }

            # Competitor activity analysis
            competitor_activity = {}
            risk_levels = {"critical": 0, "high": 0, "medium": 0, "low": 0}
            
            for card in impact_cards:
                competitor = card.competitor_name
                if competitor not in competitor_activity:
                    competitor_activity[competitor] = {
                        "count": 0,
                        "avg_risk": 0,
                        "risk_scores": []
                    }
                
                competitor_activity[competitor]["count"] += 1
                competitor_activity[competitor]["risk_scores"].append(card.risk_score)
                
                # Count risk levels
                risk_level = card.risk_level.lower()
                if risk_level in risk_levels:
                    risk_levels[risk_level] += 1

            # Calculate averages
            for competitor, data in competitor_activity.items():
                data["avg_risk"] = round(statistics.mean(data["risk_scores"]), 1)

            # Sort by activity level
            top_competitors = sorted(
                competitor_activity.items(),
                key=lambda x: (x[1]["count"], x[1]["avg_risk"]),
                reverse=True
            )[:5]

            # Market insights
            total_activities = len(impact_cards)
            avg_market_risk = round(statistics.mean([card.risk_score for card in impact_cards]), 1)
            
            market_temperature = "cool"
            if avg_market_risk > 70:
                market_temperature = "hot"
            elif avg_market_risk > 50:
                market_temperature = "warm"

            return {
                "status": "success",
                "analysis_period_days": days_back,
                "market_overview": {
                    "total_competitive_activities": total_activities,
                    "average_market_risk": avg_market_risk,
                    "market_temperature": market_temperature,
                    "unique_competitors": len(competitor_activity)
                },
                "risk_distribution": risk_levels,
                "top_competitors": [
                    {
                        "name": name,
                        "activity_count": data["count"],
                        "average_risk_score": data["avg_risk"]
                    }
                    for name, data in top_competitors
                ],
                "insights": PredictiveAnalyticsService._generate_market_insights(
                    market_temperature, total_activities, len(competitor_activity)
                )
            }

        except Exception as e:
            logger.error(f"❌ Market landscape analysis failed: {str(e)}")
            return {"status": "error", "error": str(e)}

    @staticmethod
    async def api_usage_predictions(
        days_back: int = 30,
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """Predict API usage patterns and costs"""
        
        if not db:
            return {"status": "error", "error": "Database session required"}

        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
            
            # Get API call logs
            api_logs_query = await db.execute(
                select(ApiCallLog).where(
                    ApiCallLog.created_at >= cutoff_date
                )
            )
            api_logs = api_logs_query.scalars().all()

            if not api_logs:
                return {
                    "status": "success",
                    "message": "No API usage data available"
                }

            # Analyze by API type
            api_usage = {}
            daily_usage = {}
            
            for log in api_logs:
                api_type = log.api_type
                date_key = log.created_at.date().isoformat()
                
                if api_type not in api_usage:
                    api_usage[api_type] = {"count": 0, "success": 0, "failure": 0}
                
                if date_key not in daily_usage:
                    daily_usage[date_key] = 0
                
                api_usage[api_type]["count"] += 1
                daily_usage[date_key] += 1
                
                if log.status_code and 200 <= log.status_code < 300:
                    api_usage[api_type]["success"] += 1
                else:
                    api_usage[api_type]["failure"] += 1

            # Calculate trends and predictions
            daily_counts = list(daily_usage.values())
            avg_daily_usage = statistics.mean(daily_counts) if daily_counts else 0
            
            # Simple linear trend
            if len(daily_counts) >= 7:
                recent_week = statistics.mean(daily_counts[-7:])
                older_week = statistics.mean(daily_counts[-14:-7]) if len(daily_counts) >= 14 else daily_counts[0]
                growth_rate = (recent_week - older_week) / older_week if older_week > 0 else 0
            else:
                growth_rate = 0

            # Predict next 30 days
            predicted_daily_usage = avg_daily_usage * (1 + growth_rate)
            predicted_monthly_usage = predicted_daily_usage * 30

            return {
                "status": "success",
                "analysis_period_days": days_back,
                "current_usage": {
                    "total_api_calls": len(api_logs),
                    "average_daily_calls": round(avg_daily_usage, 1),
                    "api_breakdown": api_usage
                },
                "trends": {
                    "growth_rate_percent": round(growth_rate * 100, 2),
                    "trend_direction": "increasing" if growth_rate > 0.05 else "decreasing" if growth_rate < -0.05 else "stable"
                },
                "predictions": {
                    "predicted_daily_usage": round(predicted_daily_usage, 1),
                    "predicted_monthly_usage": round(predicted_monthly_usage, 0),
                    "estimated_monthly_cost": round(predicted_monthly_usage * 0.01, 2)  # Assuming $0.01 per call
                }
            }

        except Exception as e:
            logger.error(f"❌ API usage prediction failed: {str(e)}")
            return {"status": "error", "error": str(e)}

    @staticmethod
    def _generate_prediction(risk_trend: str, activity_frequency: float, avg_risk: float) -> str:
        """Generate a prediction based on trend analysis"""
        
        if risk_trend == "increasing" and activity_frequency > 2:
            return "High competitive pressure expected. Consider defensive strategies."
        elif risk_trend == "increasing":
            return "Moderate competitive pressure building. Monitor closely."
        elif risk_trend == "decreasing":
            return "Competitive pressure decreasing. Opportunity for offensive moves."
        elif activity_frequency > 3:
            return "High competitor activity but stable risk. Maintain vigilance."
        elif avg_risk > 70:
            return "High-risk competitor. Immediate attention recommended."
        else:
            return "Stable competitive environment. Continue monitoring."

    @staticmethod
    def _generate_market_insights(temperature: str, activities: int, competitors: int) -> List[str]:
        """Generate market insights based on analysis"""
        
        insights = []
        
        if temperature == "hot":
            insights.append("Market is highly competitive with significant activity.")
            insights.append("Consider accelerating product development and marketing efforts.")
        elif temperature == "warm":
            insights.append("Moderate competitive activity detected.")
            insights.append("Good time for strategic positioning and differentiation.")
        else:
            insights.append("Market appears relatively calm.")
            insights.append("Opportunity for proactive competitive moves.")
        
        if activities > 50:
            insights.append("High volume of competitive intelligence suggests active market.")
        
        if competitors > 10:
            insights.append("Fragmented competitive landscape with many players.")
        elif competitors < 3:
            insights.append("Concentrated market with few key competitors.")
        
        return insights


def get_analytics_service() -> PredictiveAnalyticsService:
    """Factory function to create analytics service instance"""
    return PredictiveAnalyticsService()