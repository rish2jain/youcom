"""
Learning Service - AI-powered analysis of alert outcomes to improve monitoring.
Implements the core learning loop logic for competitive intelligence.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, desc, select, bindparam

from ..models.learning import AlertOutcome, LearningInsight, MonitoringAdjustment
from ..models.watch import WatchItem
from ..schemas.learning import LearningInsightResponse, MonitoringRecommendation, ApplyInsightRequest

class LearningService:
    """
    Service for analyzing user feedback and generating insights to improve monitoring.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def generate_insights(self, competitor: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Generate AI-powered insights based on alert outcomes.
        """
        insights = []
        
        # Get recent outcomes for analysis
        query = select(AlertOutcome).where(
            AlertOutcome.created_at >= datetime.utcnow() - timedelta(days=30)
        )
        
        if competitor:
            # Escape wildcard characters and use parameterized query
            safe_competitor = competitor.replace('%', '\\%').replace('_', '\\_')
            query = query.where(AlertOutcome.competitor_name.ilike(bindparam('competitor')))
            result = await self.db.execute(query, {'competitor': f"%{safe_competitor}%"})
        else:
            result = await self.db.execute(query)
        outcomes = result.scalars().all()
        
        if len(outcomes) < 5:  # Need minimum data for insights
            return insights
            
        # Analyze by competitor
        competitor_analysis = self._analyze_by_competitor(outcomes)
        
        for comp_name, analysis in competitor_analysis.items():
            # Generate threshold adjustment insights
            threshold_insight = self._generate_threshold_insight(comp_name, analysis)
            if threshold_insight:
                insights.append(threshold_insight)
                
            # Generate keyword optimization insights
            keyword_insight = self._generate_keyword_insight(comp_name, analysis)
            if keyword_insight:
                insights.append(keyword_insight)
                
            # Generate timing insights
            timing_insight = self._generate_timing_insight(comp_name, analysis)
            if timing_insight:
                insights.append(timing_insight)
        
        return insights
    
    def _analyze_by_competitor(self, outcomes: List[AlertOutcome]) -> Dict[str, Dict[str, Any]]:
        """
        Analyze outcomes grouped by competitor.
        """
        analysis = {}
        
        for outcome in outcomes:
            comp = outcome.competitor_name
            if comp not in analysis:
                analysis[comp] = {
                    'total': 0,
                    'helpful': 0,
                    'acted_upon': 0,
                    'dismissed': 0,
                    'false_positive': 0,
                    'avg_confidence': 0,
                    'avg_processing_time': 0,
                    'outcomes': []
                }
            
            data = analysis[comp]
            data['total'] += 1
            data['outcomes'].append(outcome)
            
            if outcome.outcome_quality == 'helpful':
                data['helpful'] += 1
            elif outcome.outcome_quality == 'false_positive':
                data['false_positive'] += 1
                
            if outcome.action_taken == 'acted_upon':
                data['acted_upon'] += 1
            elif outcome.action_taken == 'dismissed':
                data['dismissed'] += 1
                
            if outcome.confidence_score:
                data['avg_confidence'] += outcome.confidence_score
            if outcome.processing_time:
                data['avg_processing_time'] += outcome.processing_time
        
        # Calculate averages
        for comp, data in analysis.items():
            if data['total'] > 0:
                data['helpful_rate'] = data['helpful'] / data['total']
                data['action_rate'] = data['acted_upon'] / data['total']
                data['false_positive_rate'] = data['false_positive'] / data['total']
                data['dismiss_rate'] = data['dismissed'] / data['total']
                data['avg_confidence'] /= data['total']
                data['avg_processing_time'] /= data['total']
        
        return analysis
    
    async def _generate_threshold_insight(self, competitor: str, analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Generate insight about risk threshold adjustments.
        """
        false_positive_rate = analysis.get('false_positive_rate', 0)
        dismiss_rate = analysis.get('dismiss_rate', 0)
        
        # Get current threshold from watch item
        # Escape wildcard characters and use parameterized query
        safe_competitor = competitor.replace('%', '\\%').replace('_', '\\_')
        query = select(WatchItem).where(WatchItem.competitor_name.ilike(bindparam('competitor')))
        result = await self.db.execute(query, {'competitor': f"%{safe_competitor}%"})
        watch_item = result.scalar_one_or_none()
        
        if not watch_item:
            return None
            
        current_threshold = watch_item.risk_threshold
        
        # Too many false positives or dismissals - increase threshold
        if false_positive_rate > 0.3 or dismiss_rate > 0.4:
            suggested_threshold = min(current_threshold + 10, 90)
            confidence = min(0.8, false_positive_rate + dismiss_rate)
            
            return {
                'type': 'threshold_adjustment',
                'competitor': competitor,
                'current_value': current_threshold,
                'suggested_value': suggested_threshold,
                'confidence': confidence,
                'reason': f'High false positive rate ({false_positive_rate:.1%}) and dismiss rate ({dismiss_rate:.1%}) suggest threshold is too low',
                'potential_impact': f'Could reduce noise by {(false_positive_rate + dismiss_rate) * 50:.0f}% while maintaining signal quality'
            }
        
        # Too few alerts but high action rate - decrease threshold
        elif analysis['total'] < 3 and analysis.get('action_rate', 0) > 0.7:
            suggested_threshold = max(current_threshold - 5, 30)
            confidence = 0.6
            
            return {
                'type': 'threshold_adjustment',
                'competitor': competitor,
                'current_value': current_threshold,
                'suggested_value': suggested_threshold,
                'confidence': confidence,
                'reason': f'Low alert volume ({analysis["total"]}) but high action rate ({analysis.get("action_rate", 0):.1%}) suggests missing signals',
                'potential_impact': 'Could increase early detection by 20-30% with minimal noise increase'
            }
        
        return None
    
    def _generate_keyword_insight(self, competitor: str, analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Generate insight about keyword optimization.
        """
        # Analyze feedback for keyword-related issues
        feedback_texts = [
            outcome.user_feedback for outcome in analysis['outcomes'] 
            if outcome.user_feedback and 'keyword' in outcome.user_feedback.lower()
        ]
        
        if len(feedback_texts) >= 2:
            return {
                'type': 'keyword_optimization',
                'competitor': competitor,
                'current_value': len(feedback_texts),  # Number of keyword-related issues
                'suggested_value': 0,  # Target: zero keyword issues
                'confidence': 0.7,
                'reason': f'Multiple users mentioned keyword issues in feedback ({len(feedback_texts)} instances)',
                'potential_impact': 'Improved keyword targeting could increase relevance by 25-40%'
            }
        
        return None
    
    def _generate_timing_insight(self, competitor: str, analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Generate insight about monitoring timing optimization.
        """
        avg_processing_time = analysis.get('avg_processing_time', 0)
        
        # If processing time is consistently high, suggest optimization
        if avg_processing_time > 300:  # 5 minutes
            return {
                'type': 'timing_improvement',
                'competitor': competitor,
                'current_value': avg_processing_time,
                'suggested_value': 120,  # Target: 2 minutes
                'confidence': 0.8,
                'reason': f'Average processing time ({avg_processing_time:.0f}s) exceeds target (<120s)',
                'potential_impact': 'Faster processing could improve user satisfaction and enable real-time responses'
            }
        
        return None
    
    async def apply_insight(self, insight_request: ApplyInsightRequest) -> Dict[str, Any]:
        """
        Apply a learning insight to update monitoring configuration.
        """
        changes = {}
        
        if insight_request.type == 'threshold_adjustment':
            changes = await self._apply_threshold_adjustment(insight_request)
        elif insight_request.type == 'keyword_optimization':
            changes = await self._apply_keyword_optimization(insight_request)
        elif insight_request.type == 'timing_improvement':
            changes = await self._apply_timing_improvement(insight_request)
        
        # Record the adjustment
        adjustment = MonitoringAdjustment(
            competitor_name=insight_request.competitor,
            adjustment_type=insight_request.type,
            old_value=insight_request.current_value,
            new_value=insight_request.suggested_value,
            created_at=datetime.utcnow()
        )
        
        self.db.add(adjustment)
        await self.db.commit()
        
        return changes
    
    async def _apply_threshold_adjustment(self, insight: ApplyInsightRequest) -> Dict[str, Any]:
        """
        Apply threshold adjustment to watch item.
        """
        # Escape wildcard characters and use parameterized query
        safe_competitor = insight.competitor.replace('%', '\\%').replace('_', '\\_')
        query = select(WatchItem).where(WatchItem.competitor_name.ilike(bindparam('competitor')))
        result = await self.db.execute(query, {'competitor': f"%{safe_competitor}%"})
        watch_item = result.scalar_one_or_none()
        
        if watch_item:
            old_threshold = watch_item.risk_threshold
            try:
                # Validate suggested_value is present and within acceptable bounds
                if not insight.suggested_value:
                    raise ValueError("suggested_value is required")
                new_threshold = int(insight.suggested_value)
                if not (0 <= new_threshold <= 100):
                    raise ValueError("suggested_value must be between 0 and 100")
                
                watch_item.risk_threshold = new_threshold
                watch_item.updated_at = datetime.utcnow()
                await self.db.commit()
            except (ValueError, TypeError) as e:
                await self.db.rollback()
                logger.error(f"Invalid suggested_value for risk threshold: {e}")
                raise HTTPException(status_code=400, detail=f"Invalid suggested_value: {str(e)}")
            except Exception as e:
                await self.db.rollback()
                logger.error(f"Database error updating risk threshold: {e}")
                raise HTTPException(status_code=500, detail="Failed to update risk threshold")
            
            return {
                'watch_item_id': watch_item.id,
                'old_threshold': old_threshold,
                'new_threshold': watch_item.risk_threshold,
                'change': watch_item.risk_threshold - old_threshold
            }
        
        return {}
    
    async def _apply_keyword_optimization(self, insight: ApplyInsightRequest) -> Dict[str, Any]:
        """
        Apply keyword optimization (placeholder for future ML-based keyword suggestions).
        """
        # This would integrate with NLP analysis of successful vs failed alerts
        # For now, return placeholder
        return {
            'message': 'Keyword optimization queued for ML analysis',
            'competitor': insight.competitor
        }
    
    async def _apply_timing_improvement(self, insight: ApplyInsightRequest) -> Dict[str, Any]:
        """
        Apply timing improvements (adjust check frequency).
        """
        # Escape wildcard characters and use parameterized query
        safe_competitor = insight.competitor.replace('%', '\\%').replace('_', '\\_')
        query = select(WatchItem).where(WatchItem.competitor_name.ilike(bindparam('competitor')))
        result = await self.db.execute(query, {'competitor': f"%{safe_competitor}%"})
        watch_item = result.scalar_one_or_none()
        
        if watch_item:
            old_frequency = watch_item.check_frequency
            # Increase frequency for faster detection
            watch_item.check_frequency = max(5, old_frequency - 5)  # Check more frequently
            watch_item.updated_at = datetime.utcnow()
            await self.db.commit()
            
            return {
                'watch_item_id': watch_item.id,
                'old_frequency': old_frequency,
                'new_frequency': watch_item.check_frequency,
                'improvement': old_frequency - watch_item.check_frequency
            }
        
        return {}
    
    async def get_recommendations(self, competitor: Optional[str] = None) -> List[MonitoringRecommendation]:
        """
        Get AI-powered recommendations for improving monitoring effectiveness.
        """
        recommendations = []
        
        # Analyze recent performance
        query = select(AlertOutcome).where(
            AlertOutcome.created_at >= datetime.utcnow() - timedelta(days=14)
        )
        
        if competitor:
            # Escape wildcard characters and use parameterized query
            safe_competitor = competitor.replace('%', '\\%').replace('_', '\\_')
            query = query.where(AlertOutcome.competitor_name.ilike(bindparam('competitor')))
            result = await self.db.execute(query, {'competitor': f"%{safe_competitor}%"})
        else:
            result = await self.db.execute(query)
        outcomes = result.scalars().all()
        
        if len(outcomes) == 0:
            return recommendations
        
        # Calculate key metrics
        total = len(outcomes)
        helpful = sum(1 for o in outcomes if o.outcome_quality == 'helpful')
        false_positives = sum(1 for o in outcomes if o.outcome_quality == 'false_positive')
        acted_upon = sum(1 for o in outcomes if o.action_taken == 'acted_upon')
        
        helpful_rate = helpful / total
        false_positive_rate = false_positives / total
        action_rate = acted_upon / total
        
        # Generate recommendations based on performance
        if false_positive_rate > 0.25:
            recommendations.append(MonitoringRecommendation(
                type="threshold_adjustment",
                priority="high",
                title="Reduce False Positive Rate",
                description=f"Current false positive rate is {false_positive_rate:.1%}, above the 25% threshold",
                expected_improvement="Reduce noise by 30-50% while maintaining signal quality",
                implementation_effort="low",
                confidence=0.85
            ))
        
        if action_rate < 0.3:
            recommendations.append(MonitoringRecommendation(
                type="relevance_improvement",
                priority="medium",
                title="Improve Alert Relevance",
                description=f"Only {action_rate:.1%} of alerts result in action, suggesting low relevance",
                expected_improvement="Increase actionable alerts by 40-60%",
                implementation_effort="medium",
                confidence=0.75
            ))
        
        if helpful_rate > 0.8 and total < 5:
            recommendations.append(MonitoringRecommendation(
                type="sensitivity_increase",
                priority="medium",
                title="Increase Monitoring Sensitivity",
                description=f"High quality ({helpful_rate:.1%}) but low volume ({total} alerts) suggests missing signals",
                expected_improvement="Increase early detection by 25-35%",
                implementation_effort="low",
                confidence=0.7
            ))
        
        return recommendations
    
    async def generate_insights_async(self, competitor: str):
        """
        Asynchronously generate insights for a specific competitor.
        This can be called after recording outcomes to update insights.
        """
        # This would typically be handled by a background task queue (Celery)
        # For now, we'll just trigger insight generation
        await asyncio.sleep(0.1)  # Simulate async processing
        insights = await self.generate_insights(competitor)
        
        # Store insights in database
        for insight_data in insights:
            insight = LearningInsight(
                competitor_name=insight_data['competitor'],
                insight_type=insight_data['type'],
                current_value=insight_data['current_value'],
                suggested_value=insight_data['suggested_value'],
                confidence=insight_data['confidence'],
                reason=insight_data['reason'],
                potential_impact=insight_data['potential_impact'],
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=7)  # Insights expire after a week
            )
            self.db.add(insight)
        
        await self.db.commit()
        return insights