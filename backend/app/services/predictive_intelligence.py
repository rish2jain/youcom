"""
Predictive Intelligence Engine - Week 3 Implementation
ML-powered forecasting and predictive analytics for competitive intelligence.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
try:
    import numpy as np
except ImportError:
    np = None
from enum import Enum

logger = logging.getLogger(__name__)

class PredictionType(Enum):
    FUNDING_ROUND = "funding_round"
    PRODUCT_LAUNCH = "product_launch"
    MARKET_EXPANSION = "market_expansion"
    ACQUISITION = "acquisition"
    PARTNERSHIP = "partnership"
    COMPETITIVE_MOVE = "competitive_move"

class ConfidenceLevel(Enum):
    LOW = "low"          # < 60%
    MEDIUM = "medium"    # 60-80%
    HIGH = "high"        # > 80%

@dataclass
class PredictionResult:
    """Result of a predictive analysis"""
    prediction_type: PredictionType
    target_company: str
    prediction: str
    probability: float
    confidence_level: ConfidenceLevel
    time_horizon: str  # e.g., "3_months", "6_months", "1_year"
    supporting_factors: List[str]
    risk_factors: List[str]
    generated_at: datetime = field(default_factory=datetime.utcnow)
    model_version: str = "1.0.0"

class FundingPredictor:
    """Predicts funding rounds and investment activities"""
    
    def __init__(self):
        self.model_version = "1.0.0"
        
        # Funding indicators and weights
        self.funding_indicators = {
            "hiring_surge": 0.25,
            "product_development": 0.20,
            "market_expansion": 0.15,
            "partnership_activity": 0.15,
            "media_coverage": 0.10,
            "executive_changes": 0.10,
            "patent_activity": 0.05
        }
    
    async def predict_funding_round(
        self,
        company: str,
        company_data: Dict[str, Any],
        market_data: Dict[str, Any],
        time_horizon: str = "6_months"
    ) -> PredictionResult:
        """Predict likelihood of funding round"""
        
        # Extract signals from data
        signals = self._extract_funding_signals(company_data, market_data)
        
        # Calculate probability
        probability = self._calculate_funding_probability(signals)
        
        # Determine confidence level
        confidence = self._determine_confidence_level(probability, signals)
        
        # Generate supporting factors
        supporting_factors = self._identify_supporting_factors(signals)
        
        # Identify risk factors
        risk_factors = self._identify_funding_risks(signals, market_data)
        
        return PredictionResult(
            prediction_type=PredictionType.FUNDING_ROUND,
            target_company=company,
            prediction=f"Funding round probability: {probability:.1%}",
            probability=probability,
            confidence_level=confidence,
            time_horizon=time_horizon,
            supporting_factors=supporting_factors,
            risk_factors=risk_factors
        )
    
    def _extract_funding_signals(self, company_data: Dict, market_data: Dict) -> Dict[str, float]:
        """Extract funding-related signals from data"""
        signals = {}
        
        # Hiring surge indicator
        hiring_mentions = self._count_mentions(company_data, ["hiring", "jobs", "team", "employees"])
        signals["hiring_surge"] = min(hiring_mentions / 10, 1.0)  # Normalize to 0-1
        
        # Product development indicator
        product_mentions = self._count_mentions(company_data, ["product", "feature", "launch", "development"])
        signals["product_development"] = min(product_mentions / 15, 1.0)
        
        # Market expansion indicator
        expansion_mentions = self._count_mentions(company_data, ["expansion", "market", "international", "growth"])
        signals["market_expansion"] = min(expansion_mentions / 8, 1.0)
        
        # Partnership activity
        partnership_mentions = self._count_mentions(company_data, ["partnership", "collaboration", "alliance"])
        signals["partnership_activity"] = min(partnership_mentions / 5, 1.0)
        
        # Media coverage
        media_score = company_data.get("media_coverage_score", 0.5)
        signals["media_coverage"] = media_score
        
        # Executive changes
        exec_mentions = self._count_mentions(company_data, ["CEO", "CTO", "executive", "leadership"])
        signals["executive_changes"] = min(exec_mentions / 3, 1.0)
        
        # Patent activity (simplified)
        patent_score = company_data.get("innovation_score", 0.3)
        signals["patent_activity"] = patent_score
        
        return signals
    
    def _calculate_funding_probability(self, signals: Dict[str, float]) -> float:
        """Calculate funding probability based on signals"""
        weighted_score = 0.0
        
        for indicator, weight in self.funding_indicators.items():
            signal_strength = signals.get(indicator, 0.0)
            weighted_score += signal_strength * weight
        
        # Apply sigmoid function for probability
        if np:
            probability = 1 / (1 + np.exp(-5 * (weighted_score - 0.5)))
        else:
            # Fallback without numpy
            import math
            probability = 1 / (1 + math.exp(-5 * (weighted_score - 0.5)))
        
        return probability
    
    def _determine_confidence_level(self, probability: float, signals: Dict[str, float]) -> ConfidenceLevel:
        """Determine confidence level based on probability and signal strength"""
        # Calculate signal consistency
        signal_values = list(signals.values())
        if np and signal_values:
            signal_consistency = 1 - np.std(signal_values)
        elif signal_values:
            # Fallback standard deviation calculation
            mean_val = sum(signal_values) / len(signal_values)
            variance = sum((x - mean_val) ** 2 for x in signal_values) / len(signal_values)
            signal_consistency = 1 - (variance ** 0.5)
        else:
            signal_consistency = 0
        
        # Adjust confidence based on consistency
        if probability > 0.8 and signal_consistency > 0.7:
            return ConfidenceLevel.HIGH
        elif probability > 0.6 and signal_consistency > 0.5:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    def _identify_supporting_factors(self, signals: Dict[str, float]) -> List[str]:
        """Identify key supporting factors for funding prediction"""
        factors = []
        
        # Sort signals by strength
        sorted_signals = sorted(signals.items(), key=lambda x: x[1], reverse=True)
        
        for signal, strength in sorted_signals[:3]:  # Top 3 signals
            if strength > 0.6:
                factor_descriptions = {
                    "hiring_surge": "Significant hiring activity indicates growth preparation",
                    "product_development": "Active product development suggests expansion plans",
                    "market_expansion": "Market expansion signals indicate scaling needs",
                    "partnership_activity": "Partnership activity suggests strategic growth",
                    "media_coverage": "Increased media attention indicates market momentum",
                    "executive_changes": "Leadership changes may indicate growth phase",
                    "patent_activity": "Innovation activity suggests R&D investment"
                }
                factors.append(factor_descriptions.get(signal, f"Strong {signal} indicator"))
        
        return factors
    
    def _identify_funding_risks(self, signals: Dict[str, float], market_data: Dict) -> List[str]:
        """Identify risk factors that might affect funding"""
        risks = []
        
        # Market condition risks
        market_sentiment = market_data.get("market_sentiment", 0.5)
        if market_sentiment < 0.4:
            risks.append("Challenging market conditions may affect investor appetite")
        
        # Competition risks
        competitive_pressure = market_data.get("competitive_pressure", 0.5)
        if competitive_pressure > 0.7:
            risks.append("High competitive pressure may impact valuation")
        
        # Signal consistency risks
        signal_values = list(signals.values())
        if signal_values:
            if np:
                std_dev = np.std(signal_values)
            else:
                mean_val = sum(signal_values) / len(signal_values)
                variance = sum((x - mean_val) ** 2 for x in signal_values) / len(signal_values)
                std_dev = variance ** 0.5
            
            if std_dev > 0.3:
                risks.append("Mixed signals may indicate uncertainty in growth trajectory")
        
        return risks
    
    def _count_mentions(self, data: Dict, keywords: List[str]) -> int:
        """Count mentions of keywords in data"""
        count = 0
        
        # Search in various data fields
        search_fields = ["articles", "news", "content", "description"]
        
        for field in search_fields:
            if field in data:
                field_data = data[field]
                if isinstance(field_data, list):
                    for item in field_data:
                        if isinstance(item, dict):
                            text = " ".join(str(v) for v in item.values()).lower()
                        else:
                            text = str(item).lower()
                        
                        for keyword in keywords:
                            count += text.count(keyword.lower())
                elif isinstance(field_data, str):
                    text = field_data.lower()
                    for keyword in keywords:
                        count += text.count(keyword.lower())
        
        return count

class ProductLaunchPredictor:
    """Predicts product launches and feature releases"""
    
    def __init__(self):
        self.model_version = "1.0.0"
        
        self.launch_indicators = {
            "development_activity": 0.30,
            "hiring_patterns": 0.20,
            "patent_filings": 0.15,
            "beta_testing": 0.15,
            "marketing_activity": 0.10,
            "partnership_announcements": 0.10
        }
    
    async def predict_product_launch(
        self,
        company: str,
        company_data: Dict[str, Any],
        time_horizon: str = "3_months"
    ) -> PredictionResult:
        """Predict likelihood of product launch"""
        
        # Extract product launch signals
        signals = self._extract_launch_signals(company_data)
        
        # Calculate probability
        probability = self._calculate_launch_probability(signals)
        
        # Determine confidence
        confidence = self._determine_launch_confidence(probability, signals)
        
        # Generate insights
        supporting_factors = self._identify_launch_factors(signals)
        risk_factors = self._identify_launch_risks(signals, company_data)
        
        return PredictionResult(
            prediction_type=PredictionType.PRODUCT_LAUNCH,
            target_company=company,
            prediction=f"Product launch probability: {probability:.1%}",
            probability=probability,
            confidence_level=confidence,
            time_horizon=time_horizon,
            supporting_factors=supporting_factors,
            risk_factors=risk_factors
        )
    
    def _extract_launch_signals(self, company_data: Dict) -> Dict[str, float]:
        """Extract product launch signals"""
        signals = {}
        
        # Development activity
        dev_keywords = ["development", "building", "creating", "engineering", "coding"]
        dev_mentions = self._count_keywords(company_data, dev_keywords)
        signals["development_activity"] = min(dev_mentions / 12, 1.0)
        
        # Hiring patterns (technical roles)
        hiring_keywords = ["engineer", "developer", "designer", "product manager"]
        hiring_mentions = self._count_keywords(company_data, hiring_keywords)
        signals["hiring_patterns"] = min(hiring_mentions / 8, 1.0)
        
        # Patent filings
        patent_keywords = ["patent", "intellectual property", "innovation", "technology"]
        patent_mentions = self._count_keywords(company_data, patent_keywords)
        signals["patent_filings"] = min(patent_mentions / 5, 1.0)
        
        # Beta testing
        beta_keywords = ["beta", "testing", "preview", "early access", "pilot"]
        beta_mentions = self._count_keywords(company_data, beta_keywords)
        signals["beta_testing"] = min(beta_mentions / 4, 1.0)
        
        # Marketing activity
        marketing_keywords = ["announcement", "reveal", "unveil", "coming soon"]
        marketing_mentions = self._count_keywords(company_data, marketing_keywords)
        signals["marketing_activity"] = min(marketing_mentions / 6, 1.0)
        
        # Partnership announcements
        partnership_keywords = ["partnership", "integration", "collaboration"]
        partnership_mentions = self._count_keywords(company_data, partnership_keywords)
        signals["partnership_announcements"] = min(partnership_mentions / 3, 1.0)
        
        return signals
    
    def _calculate_launch_probability(self, signals: Dict[str, float]) -> float:
        """Calculate product launch probability"""
        weighted_score = sum(
            signals.get(indicator, 0.0) * weight
            for indicator, weight in self.launch_indicators.items()
        )
        
        # Apply sigmoid transformation
        if np:
            probability = 1 / (1 + np.exp(-4 * (weighted_score - 0.6)))
        else:
            import math
            probability = 1 / (1 + math.exp(-4 * (weighted_score - 0.6)))
        
        return probability
    
    def _determine_launch_confidence(self, probability: float, signals: Dict[str, float]) -> ConfidenceLevel:
        """Determine confidence level for launch prediction"""
        if signals:
            signal_values = list(signals.values())
            if np:
                signal_strength = np.mean(signal_values)
            else:
                signal_strength = sum(signal_values) / len(signal_values)
        else:
            signal_strength = 0
        
        if probability > 0.75 and signal_strength > 0.6:
            return ConfidenceLevel.HIGH
        elif probability > 0.55 and signal_strength > 0.4:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    def _identify_launch_factors(self, signals: Dict[str, float]) -> List[str]:
        """Identify supporting factors for launch prediction"""
        factors = []
        
        factor_descriptions = {
            "development_activity": "High development activity indicates active product work",
            "hiring_patterns": "Technical hiring suggests product development scaling",
            "patent_filings": "Patent activity indicates innovative product features",
            "beta_testing": "Beta testing activity suggests near-term launch",
            "marketing_activity": "Marketing preparation indicates launch readiness",
            "partnership_announcements": "Partnership activity may support product launch"
        }
        
        for signal, strength in signals.items():
            if strength > 0.5:
                factors.append(factor_descriptions.get(signal, f"Strong {signal} signal"))
        
        return factors[:4]  # Top 4 factors
    
    def _identify_launch_risks(self, signals: Dict[str, float], company_data: Dict) -> List[str]:
        """Identify risks that might delay launch"""
        risks = []
        
        # Development risks
        if signals.get("development_activity", 0) < 0.3:
            risks.append("Low development activity may indicate delays")
        
        # Resource risks
        if signals.get("hiring_patterns", 0) > 0.8:
            risks.append("Rapid hiring may indicate resource constraints")
        
        # Market timing risks
        competitive_mentions = self._count_keywords(company_data, ["competitor", "competition", "rival"])
        if competitive_mentions > 10:
            risks.append("High competitive activity may affect launch timing")
        
        return risks
    
    def _count_keywords(self, data: Dict, keywords: List[str]) -> int:
        """Count keyword mentions in data"""
        count = 0
        data_str = json.dumps(data).lower()
        
        for keyword in keywords:
            count += data_str.count(keyword.lower())
        
        return count

class MarketExpansionPredictor:
    """Predicts market expansion and geographic growth"""
    
    def __init__(self):
        self.model_version = "1.0.0"
        
        self.expansion_indicators = {
            "geographic_mentions": 0.25,
            "regulatory_activity": 0.20,
            "local_partnerships": 0.20,
            "hiring_in_target_markets": 0.15,
            "localization_efforts": 0.10,
            "market_research_activity": 0.10
        }
    
    async def predict_market_expansion(
        self,
        company: str,
        company_data: Dict[str, Any],
        target_markets: List[str] = None,
        time_horizon: str = "1_year"
    ) -> PredictionResult:
        """Predict likelihood of market expansion"""
        
        if not target_markets:
            target_markets = ["Europe", "Asia", "Latin America"]
        
        # Extract expansion signals
        signals = self._extract_expansion_signals(company_data, target_markets)
        
        # Calculate probability
        probability = self._calculate_expansion_probability(signals)
        
        # Determine confidence
        confidence = self._determine_expansion_confidence(probability, signals)
        
        # Generate insights
        supporting_factors = self._identify_expansion_factors(signals, target_markets)
        risk_factors = self._identify_expansion_risks(signals, company_data)
        
        return PredictionResult(
            prediction_type=PredictionType.MARKET_EXPANSION,
            target_company=company,
            prediction=f"Market expansion probability: {probability:.1%}",
            probability=probability,
            confidence_level=confidence,
            time_horizon=time_horizon,
            supporting_factors=supporting_factors,
            risk_factors=risk_factors
        )
    
    def _extract_expansion_signals(self, company_data: Dict, target_markets: List[str]) -> Dict[str, float]:
        """Extract market expansion signals"""
        signals = {}
        
        # Geographic mentions
        geo_mentions = 0
        for market in target_markets:
            geo_mentions += self._count_keywords(company_data, [market.lower()])
        signals["geographic_mentions"] = min(geo_mentions / 8, 1.0)
        
        # Regulatory activity
        regulatory_keywords = ["regulation", "compliance", "legal", "licensing"]
        regulatory_mentions = self._count_keywords(company_data, regulatory_keywords)
        signals["regulatory_activity"] = min(regulatory_mentions / 6, 1.0)
        
        # Local partnerships
        partnership_keywords = ["local partner", "regional", "distributor", "reseller"]
        partnership_mentions = self._count_keywords(company_data, partnership_keywords)
        signals["local_partnerships"] = min(partnership_mentions / 4, 1.0)
        
        # Hiring in target markets
        hiring_keywords = ["international", "global", "remote", "distributed"]
        hiring_mentions = self._count_keywords(company_data, hiring_keywords)
        signals["hiring_in_target_markets"] = min(hiring_mentions / 5, 1.0)
        
        # Localization efforts
        localization_keywords = ["localization", "translation", "local", "regional"]
        localization_mentions = self._count_keywords(company_data, localization_keywords)
        signals["localization_efforts"] = min(localization_mentions / 3, 1.0)
        
        # Market research activity
        research_keywords = ["market research", "market analysis", "opportunity"]
        research_mentions = self._count_keywords(company_data, research_keywords)
        signals["market_research_activity"] = min(research_mentions / 4, 1.0)
        
        return signals
    
    def _calculate_expansion_probability(self, signals: Dict[str, float]) -> float:
        """Calculate market expansion probability"""
        weighted_score = sum(
            signals.get(indicator, 0.0) * weight
            for indicator, weight in self.expansion_indicators.items()
        )
        
        # Apply sigmoid transformation
        if np:
            probability = 1 / (1 + np.exp(-3 * (weighted_score - 0.5)))
        else:
            import math
            probability = 1 / (1 + math.exp(-3 * (weighted_score - 0.5)))
        
        return probability
    
    def _determine_expansion_confidence(self, probability: float, signals: Dict[str, float]) -> ConfidenceLevel:
        """Determine confidence level for expansion prediction"""
        signal_count = sum(1 for s in signals.values() if s > 0.3)
        
        if probability > 0.7 and signal_count >= 4:
            return ConfidenceLevel.HIGH
        elif probability > 0.5 and signal_count >= 2:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    def _identify_expansion_factors(self, signals: Dict[str, float], target_markets: List[str]) -> List[str]:
        """Identify supporting factors for expansion prediction"""
        factors = []
        
        if signals.get("geographic_mentions", 0) > 0.5:
            factors.append(f"Increased mentions of target markets: {', '.join(target_markets)}")
        
        if signals.get("regulatory_activity", 0) > 0.4:
            factors.append("Regulatory preparation indicates expansion planning")
        
        if signals.get("local_partnerships", 0) > 0.4:
            factors.append("Local partnership activity suggests market entry strategy")
        
        if signals.get("hiring_in_target_markets", 0) > 0.3:
            factors.append("International hiring indicates expansion preparation")
        
        return factors
    
    def _identify_expansion_risks(self, signals: Dict[str, float], company_data: Dict) -> List[str]:
        """Identify risks for market expansion"""
        risks = []
        
        # Regulatory risks
        if signals.get("regulatory_activity", 0) > 0.7:
            risks.append("High regulatory activity may indicate compliance challenges")
        
        # Resource risks
        total_signal_strength = sum(signals.values())
        if total_signal_strength < 1.5:
            risks.append("Limited expansion signals may indicate resource constraints")
        
        # Competition risks
        competitive_mentions = self._count_keywords(company_data, ["competition", "competitive"])
        if competitive_mentions > 8:
            risks.append("High competitive activity in target markets")
        
        return risks
    
    def _count_keywords(self, data: Dict, keywords: List[str]) -> int:
        """Count keyword mentions in data"""
        count = 0
        data_str = json.dumps(data).lower()
        
        for keyword in keywords:
            count += data_str.count(keyword.lower())
        
        return count

class PredictiveIntelligenceEngine:
    """Main predictive intelligence engine coordinating all predictors"""
    
    def __init__(self):
        self.funding_predictor = FundingPredictor()
        self.product_predictor = ProductLaunchPredictor()
        self.market_predictor = MarketExpansionPredictor()
        
        self.engine_version = "1.0.0"
    
    async def generate_comprehensive_predictions(
        self,
        company: str,
        company_data: Dict[str, Any],
        market_data: Dict[str, Any] = None,
        prediction_types: List[PredictionType] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive predictions for a company"""
        
        if market_data is None:
            market_data = {}
        
        if prediction_types is None:
            prediction_types = [
                PredictionType.FUNDING_ROUND,
                PredictionType.PRODUCT_LAUNCH,
                PredictionType.MARKET_EXPANSION
            ]
        
        predictions = []
        
        # Generate predictions based on requested types
        if PredictionType.FUNDING_ROUND in prediction_types:
            funding_prediction = await self.funding_predictor.predict_funding_round(
                company, company_data, market_data
            )
            predictions.append(funding_prediction)
        
        if PredictionType.PRODUCT_LAUNCH in prediction_types:
            product_prediction = await self.product_predictor.predict_product_launch(
                company, company_data
            )
            predictions.append(product_prediction)
        
        if PredictionType.MARKET_EXPANSION in prediction_types:
            expansion_prediction = await self.market_predictor.predict_market_expansion(
                company, company_data
            )
            predictions.append(expansion_prediction)
        
        # Analyze prediction patterns
        prediction_summary = self._analyze_prediction_patterns(predictions)
        
        return {
            "company": company,
            "generated_at": datetime.utcnow().isoformat(),
            "predictions": [self._prediction_to_dict(p) for p in predictions],
            "prediction_summary": prediction_summary,
            "engine_metadata": {
                "engine_version": self.engine_version,
                "predictors_used": [p.value for p in prediction_types],
                "total_predictions": len(predictions)
            }
        }
    
    def _prediction_to_dict(self, prediction: PredictionResult) -> Dict[str, Any]:
        """Convert prediction result to dictionary"""
        return {
            "prediction_type": prediction.prediction_type.value,
            "target_company": prediction.target_company,
            "prediction": prediction.prediction,
            "probability": prediction.probability,
            "confidence_level": prediction.confidence_level.value,
            "time_horizon": prediction.time_horizon,
            "supporting_factors": prediction.supporting_factors,
            "risk_factors": prediction.risk_factors,
            "generated_at": prediction.generated_at.isoformat(),
            "model_version": prediction.model_version
        }
    
    def _analyze_prediction_patterns(self, predictions: List[PredictionResult]) -> Dict[str, Any]:
        """Analyze patterns across predictions"""
        if not predictions:
            return {}
        
        # Calculate average probability
        probabilities = [p.probability for p in predictions]
        if np:
            avg_probability = np.mean(probabilities)
        else:
            avg_probability = sum(probabilities) / len(probabilities) if probabilities else 0
        
        # Count confidence levels
        confidence_counts = {}
        for pred in predictions:
            level = pred.confidence_level.value
            confidence_counts[level] = confidence_counts.get(level, 0) + 1
        
        # Identify highest probability prediction
        highest_prob_pred = max(predictions, key=lambda p: p.probability)
        
        # Identify common themes in supporting factors
        all_factors = []
        for pred in predictions:
            all_factors.extend(pred.supporting_factors)
        
        # Simple theme identification (would be more sophisticated in production)
        common_themes = []
        if any("hiring" in factor.lower() for factor in all_factors):
            common_themes.append("hiring_activity")
        if any("product" in factor.lower() for factor in all_factors):
            common_themes.append("product_development")
        if any("market" in factor.lower() for factor in all_factors):
            common_themes.append("market_activity")
        
        return {
            "average_probability": avg_probability,
            "confidence_distribution": confidence_counts,
            "highest_probability_prediction": {
                "type": highest_prob_pred.prediction_type.value,
                "probability": highest_prob_pred.probability
            },
            "common_themes": common_themes,
            "overall_activity_level": "high" if avg_probability > 0.6 else "medium" if avg_probability > 0.4 else "low"
        }

# Global predictive intelligence engine
predictive_intelligence = PredictiveIntelligenceEngine()