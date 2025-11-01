"""Predictive Intelligence service for competitor pattern analysis and predictions."""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
import numpy as np
from collections import defaultdict, Counter

from app.models.predictive_intelligence import CompetitorPattern, PredictedEvent, PatternEvent
from app.models.impact_card import ImpactCard
# from app.services.you_client import YouClient

logger = logging.getLogger(__name__)


class PredictiveIntelligenceEngine:
    """Engine for analyzing competitor patterns and generating predictions."""
    
    def __init__(self, db: Session, you_client = None):
        self.db = db
        self.you_client = you_client  # Optional You.com client for future enhancements
        
        # Pattern analysis configuration
        self.min_pattern_frequency = 2  # Minimum occurrences to consider a pattern
        self.pattern_confidence_threshold = 0.6  # Minimum confidence for valid patterns
        self.prediction_horizon_days = 90  # How far ahead to predict
        
        # Event type mappings for pattern recognition
        self.event_type_keywords = {
            "product_launch": ["launch", "release", "announce", "unveil", "introduce"],
            "pricing_change": ["price", "pricing", "cost", "discount", "premium"],
            "partnership": ["partner", "collaboration", "alliance", "joint", "merger"],
            "funding": ["funding", "investment", "raise", "series", "valuation"],
            "expansion": ["expand", "growth", "market", "international", "new region"],
            "acquisition": ["acquire", "acquisition", "buy", "purchase", "takeover"],
            "leadership": ["ceo", "cto", "hire", "appointment", "leadership", "executive"]
        }
    
    def analyze_competitor_patterns(self, competitor_name: str) -> List[CompetitorPattern]:
        """Analyze historical data to identify competitor behavior patterns."""
        logger.info(f"Analyzing patterns for competitor: {competitor_name}")
        
        # Get historical impact cards for this competitor
        impact_cards = self.db.query(ImpactCard).filter(
            ImpactCard.competitor_name == competitor_name
        ).order_by(ImpactCard.created_at).all()
        
        if len(impact_cards) < self.min_pattern_frequency:
            logger.info(f"Insufficient data for pattern analysis: {len(impact_cards)} cards")
            return []
        
        # Group events by type and analyze patterns
        patterns = []
        event_groups = self._group_events_by_type(impact_cards)
        
        for event_type, events in event_groups.items():
            if len(events) >= self.min_pattern_frequency:
                pattern = self._analyze_event_sequence(competitor_name, event_type, events)
                if pattern and pattern.confidence >= self.pattern_confidence_threshold:
                    patterns.append(pattern)
        
        # Save patterns to database
        for pattern in patterns:
            existing_pattern = self.db.query(CompetitorPattern).filter(
                and_(
                    CompetitorPattern.competitor_name == competitor_name,
                    CompetitorPattern.pattern_type == pattern.pattern_type
                )
            ).first()
            
            if existing_pattern:
                # Update existing pattern
                existing_pattern.sequence = pattern.sequence
                existing_pattern.frequency = pattern.frequency
                existing_pattern.confidence = pattern.confidence
                existing_pattern.last_observed = pattern.last_observed
                existing_pattern.updated_at = datetime.utcnow()
            else:
                # Create new pattern
                self.db.add(pattern)
        
        self.db.commit()
        logger.info(f"Identified {len(patterns)} patterns for {competitor_name}")
        return patterns
    
    def _group_events_by_type(self, impact_cards: List[ImpactCard]) -> Dict[str, List[ImpactCard]]:
        """Group impact cards by event type based on content analysis."""
        event_groups = defaultdict(list)
        
        for card in impact_cards:
            event_type = self._classify_event_type(card)
            event_groups[event_type].append(card)
        
        return dict(event_groups)
    
    def _classify_event_type(self, impact_card: ImpactCard) -> str:
        """Classify an impact card into an event type based on content."""
        # Analyze key insights and recommended actions for keywords
        content_text = ""
        
        if impact_card.key_insights:
            content_text += " ".join(impact_card.key_insights)
        
        if impact_card.recommended_actions:
            for action in impact_card.recommended_actions:
                if isinstance(action, dict) and "description" in action:
                    content_text += " " + action["description"]
        
        content_text = content_text.lower()
        
        # Score each event type based on keyword matches
        type_scores = {}
        for event_type, keywords in self.event_type_keywords.items():
            score = sum(1 for keyword in keywords if keyword in content_text)
            if score > 0:
                type_scores[event_type] = score
        
        # Return the highest scoring type, or "general" if no matches
        if type_scores:
            return max(type_scores.items(), key=lambda x: x[1])[0]
        else:
            return "general"
    
    def _analyze_event_sequence(self, competitor_name: str, event_type: str, events: List[ImpactCard]) -> Optional[CompetitorPattern]:
        """Analyze a sequence of events to identify patterns."""
        if len(events) < 2:
            return None
        
        # Sort events by date
        events.sort(key=lambda x: x.created_at)
        
        # Calculate intervals between events
        intervals = []
        for i in range(1, len(events)):
            interval = (events[i].created_at - events[i-1].created_at).days
            intervals.append(interval)
        
        # Calculate pattern characteristics
        avg_interval = np.mean(intervals) if intervals else 0
        interval_std = np.std(intervals) if len(intervals) > 1 else 0
        
        # Calculate confidence based on consistency of intervals
        confidence = max(0.0, 1.0 - (interval_std / max(avg_interval, 1)))
        confidence = min(confidence, 1.0)
        
        # Create pattern sequence
        sequence = []
        for event in events:
            sequence.append({
                "date": event.created_at.isoformat(),
                "risk_score": event.risk_score,
                "key_insights": event.key_insights[:2] if event.key_insights else [],
                "impact_areas": event.impact_areas[:3] if event.impact_areas else []
            })
        
        # Identify contributing factors
        contributing_factors = self._identify_contributing_factors(events)
        
        # Create pattern object
        pattern = CompetitorPattern(
            competitor_name=competitor_name,
            pattern_type=event_type,
            sequence=sequence,
            frequency=len(events),
            confidence=confidence,
            average_duration=int(avg_interval),
            typical_intervals=intervals,
            first_observed=events[0].created_at,
            last_observed=events[-1].created_at,
            contributing_factors=contributing_factors,
            success_indicators=self._identify_success_indicators(events)
        )
        
        return pattern
    
    def _identify_contributing_factors(self, events: List[ImpactCard]) -> List[str]:
        """Identify common factors that contribute to this pattern."""
        factors = []
        
        # Analyze impact areas across events
        all_impact_areas = []
        for event in events:
            if event.impact_areas:
                all_impact_areas.extend(event.impact_areas)
        
        # Find most common impact areas
        if all_impact_areas:
            impact_counter = Counter(all_impact_areas)
            common_impacts = [area for area, count in impact_counter.most_common(3)]
            factors.extend(common_impacts)
        
        # Analyze risk score patterns
        risk_scores = [event.risk_score for event in events]
        avg_risk = np.mean(risk_scores)
        
        if avg_risk > 80:
            factors.append("high_risk_events")
        elif avg_risk > 60:
            factors.append("medium_risk_events")
        
        return factors[:5]  # Limit to top 5 factors
    
    def _identify_success_indicators(self, events: List[ImpactCard]) -> List[str]:
        """Identify indicators of pattern success."""
        indicators = []
        
        # Analyze trend in risk scores
        risk_scores = [event.risk_score for event in events]
        if len(risk_scores) > 1:
            risk_trend = np.polyfit(range(len(risk_scores)), risk_scores, 1)[0]
            if risk_trend > 5:
                indicators.append("increasing_risk_trend")
            elif risk_trend < -5:
                indicators.append("decreasing_risk_trend")
        
        # Analyze confidence scores
        confidence_scores = [event.confidence_score for event in events]
        avg_confidence = np.mean(confidence_scores)
        
        if avg_confidence > 80:
            indicators.append("high_confidence_pattern")
        
        return indicators
    
    def generate_predictions(self, competitor_name: str) -> List[PredictedEvent]:
        """Generate predictions based on identified patterns."""
        logger.info(f"Generating predictions for competitor: {competitor_name}")
        
        # Get active patterns for this competitor
        patterns = self.db.query(CompetitorPattern).filter(
            and_(
                CompetitorPattern.competitor_name == competitor_name,
                CompetitorPattern.is_active == True
            )
        ).all()
        
        predictions = []
        
        for pattern in patterns:
            prediction = self._generate_pattern_prediction(pattern)
            if prediction:
                predictions.append(prediction)
        
        # Save predictions to database
        for prediction in predictions:
            # Check if similar prediction already exists
            existing = self.db.query(PredictedEvent).filter(
                and_(
                    PredictedEvent.competitor_name == competitor_name,
                    PredictedEvent.event_type == prediction.event_type,
                    PredictedEvent.status == "pending"
                )
            ).first()
            
            if not existing:
                self.db.add(prediction)
        
        self.db.commit()
        logger.info(f"Generated {len(predictions)} predictions for {competitor_name}")
        return predictions
    
    def _generate_pattern_prediction(self, pattern: CompetitorPattern) -> Optional[PredictedEvent]:
        """Generate a prediction based on a specific pattern."""
        if not pattern.sequence or pattern.frequency < 2:
            return None
        
        # Calculate time since last occurrence
        time_since_last = (datetime.utcnow() - pattern.last_observed).days
        
        # Estimate next occurrence based on average interval
        if pattern.average_duration and pattern.average_duration > 0:
            days_until_next = max(0, pattern.average_duration - time_since_last)
            predicted_date = datetime.utcnow() + timedelta(days=days_until_next)
            
            # Calculate probability based on pattern consistency and timing
            timing_factor = min(1.0, time_since_last / pattern.average_duration)
            probability = pattern.confidence * timing_factor
            
            # Adjust probability based on pattern frequency
            frequency_factor = min(1.0, pattern.frequency / 5.0)  # Normalize to max 5 occurrences
            probability *= (0.5 + 0.5 * frequency_factor)
            
            # Generate timeframe description
            if days_until_next <= 7:
                timeframe = "within 1 week"
            elif days_until_next <= 30:
                timeframe = "within 1 month"
            elif days_until_next <= 90:
                timeframe = "within 3 months"
            else:
                timeframe = "beyond 3 months"
            
            # Generate reasoning
            reasoning = [
                f"Pattern observed {pattern.frequency} times with {pattern.confidence:.1%} consistency",
                f"Average interval between occurrences: {pattern.average_duration} days",
                f"Last occurrence: {time_since_last} days ago",
                f"Contributing factors: {', '.join(pattern.contributing_factors[:3])}"
            ]
            
            # Create prediction
            prediction = PredictedEvent(
                pattern_id=pattern.id,
                competitor_name=pattern.competitor_name,
                event_type=pattern.pattern_type,
                description=self._generate_prediction_description(pattern),
                probability=min(probability, 1.0),
                confidence=pattern.confidence,
                predicted_date=predicted_date,
                timeframe=timeframe,
                earliest_date=predicted_date - timedelta(days=7),
                latest_date=predicted_date + timedelta(days=14),
                reasoning=reasoning,
                trigger_events=self._identify_trigger_events(pattern),
                supporting_evidence=pattern.sequence[-2:],  # Last 2 occurrences as evidence
                expires_at=datetime.utcnow() + timedelta(days=self.prediction_horizon_days)
            )
            
            return prediction
        
        return None
    
    def _generate_prediction_description(self, pattern: CompetitorPattern) -> str:
        """Generate a human-readable description for the prediction."""
        event_type_descriptions = {
            "product_launch": f"{pattern.competitor_name} is likely to announce a new product or feature",
            "pricing_change": f"{pattern.competitor_name} may adjust their pricing strategy",
            "partnership": f"{pattern.competitor_name} could announce a new partnership or collaboration",
            "funding": f"{pattern.competitor_name} might raise additional funding",
            "expansion": f"{pattern.competitor_name} may expand into new markets or regions",
            "acquisition": f"{pattern.competitor_name} could make an acquisition",
            "leadership": f"{pattern.competitor_name} may announce leadership changes"
        }
        
        return event_type_descriptions.get(
            pattern.pattern_type,
            f"{pattern.competitor_name} may engage in {pattern.pattern_type} activity"
        )
    
    def _identify_trigger_events(self, pattern: CompetitorPattern) -> List[str]:
        """Identify events that typically trigger this pattern."""
        triggers = []
        
        # Analyze contributing factors to identify triggers
        if pattern.contributing_factors:
            for factor in pattern.contributing_factors[:3]:
                if "high_risk" in factor:
                    triggers.append("Increased competitive pressure")
                elif "market" in factor.lower():
                    triggers.append("Market dynamics change")
                elif "product" in factor.lower():
                    triggers.append("Product development cycle")
        
        # Add pattern-specific triggers
        pattern_triggers = {
            "product_launch": ["Development completion", "Market opportunity"],
            "pricing_change": ["Competitive pressure", "Market positioning"],
            "partnership": ["Strategic alignment", "Market expansion needs"],
            "funding": ["Growth requirements", "Market opportunity"],
            "expansion": ["Market saturation", "Growth strategy"],
            "acquisition": ["Strategic gaps", "Market consolidation"],
            "leadership": ["Growth phase", "Strategic changes"]
        }
        
        if pattern.pattern_type in pattern_triggers:
            triggers.extend(pattern_triggers[pattern.pattern_type])
        
        return triggers[:5]  # Limit to top 5 triggers
    
    def validate_prediction(self, prediction_id: int, actual_outcome: str, accuracy_score: float) -> bool:
        """Validate a prediction with actual outcome."""
        prediction = self.db.query(PredictedEvent).filter(
            PredictedEvent.id == prediction_id
        ).first()
        
        if not prediction:
            return False
        
        prediction.actual_outcome = actual_outcome
        prediction.accuracy_score = accuracy_score
        prediction.validation_date = datetime.utcnow()
        prediction.status = "validated" if accuracy_score > 0.5 else "invalidated"
        
        self.db.commit()
        logger.info(f"Validated prediction {prediction_id} with accuracy {accuracy_score}")
        return True
    
    def get_active_predictions(self, competitor_name: str = None) -> List[PredictedEvent]:
        """Get active predictions, optionally filtered by competitor."""
        query = self.db.query(PredictedEvent).filter(
            PredictedEvent.status == "pending",
            PredictedEvent.expires_at > datetime.utcnow()
        )
        
        if competitor_name:
            query = query.filter(PredictedEvent.competitor_name == competitor_name)
        
        return query.order_by(desc(PredictedEvent.probability)).all()
    
    def get_pattern_accuracy_metrics(self) -> Dict[str, Any]:
        """Get accuracy metrics for pattern predictions."""
        validated_predictions = self.db.query(PredictedEvent).filter(
            PredictedEvent.status.in_(["validated", "invalidated"]),
            PredictedEvent.accuracy_score.isnot(None)
        ).all()
        
        if not validated_predictions:
            return {"total_predictions": 0, "accuracy": 0.0}
        
        total_predictions = len(validated_predictions)
        accurate_predictions = sum(1 for p in validated_predictions if p.accuracy_score > 0.5)
        overall_accuracy = accurate_predictions / total_predictions
        
        # Accuracy by event type
        type_accuracy = defaultdict(list)
        for prediction in validated_predictions:
            type_accuracy[prediction.event_type].append(prediction.accuracy_score)
        
        type_metrics = {}
        for event_type, scores in type_accuracy.items():
            type_metrics[event_type] = {
                "count": len(scores),
                "accuracy": np.mean(scores),
                "confidence": np.mean([p.confidence for p in validated_predictions if p.event_type == event_type])
            }
        
        return {
            "total_predictions": total_predictions,
            "accurate_predictions": accurate_predictions,
            "overall_accuracy": overall_accuracy,
            "type_metrics": type_metrics
        }