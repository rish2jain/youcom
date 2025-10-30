"""Advanced sentiment classification and entity recognition service."""

import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.sentiment_analysis import SentimentAnalysis
from app.services.you_client import YouComClient
from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class EntityRecognitionResult:
    """Result of entity recognition."""
    name: str
    entity_type: str  # company, product, market
    confidence: float
    context: str
    start_pos: int
    end_pos: int
    metadata: Dict[str, Any]


@dataclass
class SentimentClassificationResult:
    """Result of sentiment classification."""
    sentiment_score: float  # -1.0 to 1.0
    sentiment_label: str    # positive, negative, neutral
    confidence: float       # 0.0 to 1.0
    reasoning: str
    metadata: Dict[str, Any]


class EntityRecognizer:
    """Advanced entity recognition system."""
    
    def __init__(self):
        self.you_client = YouComClient()
        self.company_patterns = self._load_company_patterns()
        self.product_patterns = self._load_product_patterns()
        self.market_patterns = self._load_market_patterns()
        
    def _load_company_patterns(self) -> List[str]:
        """Load company name recognition patterns."""
        return [
            # Standard corporate suffixes
            r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\s+(?:Inc\.?|Corp\.?|LLC|Ltd\.?|Co\.?|Corporation|Company)\b',
            
            # Companies in action contexts
            r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\s+(?:announced|launched|released|acquired|merged|partnered)\b',
            r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\s+(?:reported|posted|revealed|disclosed|stated)\b',
            
            # Executive contexts
            r'\b(?:CEO|CTO|CFO|President|Founder)\s+of\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\b',
            r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\s+(?:CEO|CTO|CFO|President|Founder)\b',
            
            # Stock/financial contexts
            r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\s+\([A-Z]{2,5}\)\b',  # Company (TICKER)
            r'\b([A-Z]{2,5})\s+stock\b',  # TICKER stock
            
            # Possessive forms
            r"\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)'s\s+(?:revenue|profit|earnings|stock|shares)\b",
        ]
    
    def _load_product_patterns(self) -> List[str]:
        """Load product name recognition patterns."""
        return [
            # Product launch contexts
            r'\b(?:product|service|platform|app|software|tool)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\b',
            r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\s+(?:version|v\d+|\d+\.\d+|beta|alpha)\b',
            
            # Technology products
            r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\s+(?:API|SDK|framework|library|database)\b',
            r'\b(?:using|with|via)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\s+(?:technology|platform|service)\b',
            
            # Brand products
            r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\s+(?:brand|line|series|suite)\b',
        ]
    
    def _load_market_patterns(self) -> List[str]:
        """Load market segment recognition patterns."""
        return [
            # Market contexts
            r'\b([a-zA-Z]+(?:\s+[a-zA-Z]+)*)\s+(?:market|industry|sector|segment)\b',
            r'\b(?:in|within|across)\s+the\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)*)\s+(?:market|industry|sector)\b',
            
            # Technology markets
            r'\b([a-zA-Z]+(?:\s+[a-zA-Z]+)*)\s+(?:tech|technology|software|hardware)\s+(?:market|space|industry)\b',
            
            # Business models
            r'\b([a-zA-Z]+(?:\s+[a-zA-Z]+)*)\s+(?:business|model|solution|services)\b',
        ]

    async def recognize_entities(self, text: str) -> List[EntityRecognitionResult]:
        """Recognize entities in text using pattern matching and AI enhancement."""
        entities = []
        
        # Pattern-based recognition
        entities.extend(await self._pattern_based_recognition(text))
        
        # AI-enhanced recognition
        try:
            ai_entities = await self._ai_enhanced_recognition(text)
            entities.extend(ai_entities)
        except Exception as e:
            logger.warning(f"AI entity recognition failed: {str(e)}")
        
        # Deduplicate and merge entities
        entities = self._deduplicate_entities(entities)
        
        # Filter by confidence threshold
        entities = [e for e in entities if e.confidence >= 0.6]
        
        return entities

    async def _pattern_based_recognition(self, text: str) -> List[EntityRecognitionResult]:
        """Recognize entities using regex patterns."""
        entities = []
        
        # Company recognition
        for pattern in self.company_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entity_name = match.group(1).strip()
                if len(entity_name) > 2 and self._is_valid_company_name(entity_name):
                    entities.append(EntityRecognitionResult(
                        name=entity_name,
                        entity_type="company",
                        confidence=0.7,
                        context=self._extract_context(text, match.start(), match.end()),
                        start_pos=match.start(),
                        end_pos=match.end(),
                        metadata={"method": "pattern", "pattern": pattern}
                    ))
        
        # Product recognition
        for pattern in self.product_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entity_name = match.group(1).strip()
                if len(entity_name) > 2 and self._is_valid_product_name(entity_name):
                    entities.append(EntityRecognitionResult(
                        name=entity_name,
                        entity_type="product",
                        confidence=0.6,
                        context=self._extract_context(text, match.start(), match.end()),
                        start_pos=match.start(),
                        end_pos=match.end(),
                        metadata={"method": "pattern", "pattern": pattern}
                    ))
        
        # Market recognition
        for pattern in self.market_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entity_name = match.group(1).strip()
                if len(entity_name) > 2 and self._is_valid_market_name(entity_name):
                    entities.append(EntityRecognitionResult(
                        name=entity_name,
                        entity_type="market",
                        confidence=0.6,
                        context=self._extract_context(text, match.start(), match.end()),
                        start_pos=match.start(),
                        end_pos=match.end(),
                        metadata={"method": "pattern", "pattern": pattern}
                    ))
        
        return entities

    async def _ai_enhanced_recognition(self, text: str) -> List[EntityRecognitionResult]:
        """Recognize entities using You.com Custom Agent."""
        prompt = f"""
        Extract companies, products, and market segments from this business/tech news text.
        Focus on competitive intelligence entities that would be relevant for business analysis.
        
        Return a JSON array with objects containing:
        - name: entity name (properly capitalized)
        - type: "company", "product", or "market"
        - confidence: 0.0-1.0 (how confident you are this is a real entity)
        - reasoning: brief explanation of why this is an entity
        
        Text: {text[:2000]}
        
        Example format:
        [
            {{"name": "Microsoft", "type": "company", "confidence": 0.95, "reasoning": "Well-known technology company"}},
            {{"name": "Azure", "type": "product", "confidence": 0.90, "reasoning": "Microsoft's cloud platform"}},
            {{"name": "cloud computing", "type": "market", "confidence": 0.85, "reasoning": "Technology market segment"}}
        ]
        """
        
        try:
            response = await self.you_client.custom_agent_query(
                query=prompt,
                agent_mode="research"
            )
            
            # Parse JSON response
            entities_data = json.loads(response.get("response", "[]"))
            
            entities = []
            for entity_data in entities_data:
                if isinstance(entity_data, dict) and all(k in entity_data for k in ["name", "type", "confidence"]):
                    # Validate entity type
                    if entity_data["type"] not in ["company", "product", "market"]:
                        continue
                    
                    # Validate confidence
                    confidence = min(1.0, max(0.0, float(entity_data["confidence"])))
                    
                    entities.append(EntityRecognitionResult(
                        name=entity_data["name"],
                        entity_type=entity_data["type"],
                        confidence=confidence,
                        context="",  # AI doesn't provide position info
                        start_pos=-1,
                        end_pos=-1,
                        metadata={
                            "method": "ai",
                            "reasoning": entity_data.get("reasoning", "")
                        }
                    ))
            
            return entities
            
        except Exception as e:
            logger.error(f"AI entity recognition error: {str(e)}")
            return []

    def _is_valid_company_name(self, name: str) -> bool:
        """Validate if a string is likely a company name."""
        # Filter out common false positives
        invalid_names = {
            "the", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by",
            "this", "that", "these", "those", "a", "an", "as", "is", "was", "are", "were",
            "new", "old", "big", "small", "good", "bad", "first", "last", "next", "previous"
        }
        return name.lower() not in invalid_names and not name.isdigit()

    def _is_valid_product_name(self, name: str) -> bool:
        """Validate if a string is likely a product name."""
        # Similar validation for products
        return self._is_valid_company_name(name) and len(name) > 1

    def _is_valid_market_name(self, name: str) -> bool:
        """Validate if a string is likely a market name."""
        # Market names can be more generic
        return len(name) > 2 and not name.isdigit()

    def _extract_context(self, text: str, start: int, end: int, window: int = 50) -> str:
        """Extract context around entity mention."""
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        return text[context_start:context_end].strip()

    def _deduplicate_entities(self, entities: List[EntityRecognitionResult]) -> List[EntityRecognitionResult]:
        """Deduplicate entities, keeping the highest confidence version."""
        entity_map = {}
        
        for entity in entities:
            key = f"{entity.name.lower()}_{entity.entity_type}"
            
            if key not in entity_map or entity.confidence > entity_map[key].confidence:
                entity_map[key] = entity
        
        return list(entity_map.values())


class SentimentClassifier:
    """Advanced sentiment classification system."""
    
    def __init__(self):
        self.you_client = YouComClient()
        self.positive_indicators = self._load_positive_indicators()
        self.negative_indicators = self._load_negative_indicators()
        
    def _load_positive_indicators(self) -> Dict[str, float]:
        """Load positive sentiment indicators with weights."""
        return {
            # Strong positive
            "excellent": 0.8, "outstanding": 0.8, "exceptional": 0.8, "breakthrough": 0.8,
            "revolutionary": 0.7, "innovative": 0.7, "successful": 0.7, "profitable": 0.7,
            
            # Moderate positive
            "good": 0.5, "positive": 0.5, "growth": 0.5, "increase": 0.5, "gain": 0.5,
            "improvement": 0.5, "progress": 0.5, "advance": 0.5, "win": 0.6, "success": 0.6,
            
            # Business positive
            "launch": 0.4, "expansion": 0.5, "partnership": 0.4, "acquisition": 0.3,
            "investment": 0.4, "funding": 0.5, "revenue": 0.3, "profit": 0.6,
        }
    
    def _load_negative_indicators(self) -> Dict[str, float]:
        """Load negative sentiment indicators with weights."""
        return {
            # Strong negative
            "terrible": -0.8, "awful": -0.8, "disaster": -0.8, "catastrophic": -0.8,
            "failure": -0.7, "crisis": -0.7, "collapse": -0.7, "bankruptcy": -0.8,
            
            # Moderate negative
            "bad": -0.5, "poor": -0.5, "negative": -0.5, "decline": -0.5, "decrease": -0.5,
            "loss": -0.6, "problem": -0.4, "issue": -0.4, "concern": -0.4, "risk": -0.3,
            
            # Business negative
            "layoffs": -0.6, "downsizing": -0.5, "restructuring": -0.3, "lawsuit": -0.5,
            "investigation": -0.4, "penalty": -0.5, "fine": -0.4, "violation": -0.5,
        }

    async def classify_sentiment(self, text: str, entities: List[EntityRecognitionResult]) -> SentimentClassificationResult:
        """Classify sentiment with high confidence scoring."""
        
        # Try AI-based classification first
        try:
            ai_result = await self._ai_sentiment_classification(text, entities)
            if ai_result.confidence >= 0.8:
                return ai_result
        except Exception as e:
            logger.warning(f"AI sentiment classification failed: {str(e)}")
        
        # Fallback to rule-based classification
        rule_result = self._rule_based_sentiment_classification(text, entities)
        
        # Combine results if AI confidence is moderate
        try:
            if 'ai_result' in locals() and ai_result.confidence >= 0.6:
                return self._combine_sentiment_results(ai_result, rule_result)
        except:
            pass
        
        return rule_result

    async def _ai_sentiment_classification(self, text: str, entities: List[EntityRecognitionResult]) -> SentimentClassificationResult:
        """Classify sentiment using You.com Custom Agent."""
        entity_context = ""
        if entities:
            entity_names = [e.name for e in entities[:5]]  # Limit to top 5 entities
            entity_context = f"\nKey entities mentioned: {', '.join(entity_names)}"
        
        prompt = f"""
        Analyze the sentiment of this business/competitive intelligence text.
        Consider the context of competitive analysis and business impact.
        
        Return a JSON object with:
        - score: float between -1.0 (very negative) and 1.0 (very positive)
        - label: "positive", "negative", or "neutral"
        - confidence: float between 0.0 and 1.0 (how confident you are in this analysis)
        - reasoning: brief explanation of the sentiment analysis
        
        Text: {text[:2000]}{entity_context}
        
        Example format:
        {{"score": 0.3, "label": "positive", "confidence": 0.85, "reasoning": "Company announced successful product launch with positive market reception"}}
        """
        
        try:
            response = await self.you_client.custom_agent_query(
                query=prompt,
                agent_mode="research"
            )
            
            # Parse JSON response
            sentiment_data = json.loads(response.get("response", "{}"))
            
            # Validate and normalize response
            score = float(sentiment_data.get("score", 0.0))
            score = max(-1.0, min(1.0, score))  # Clamp to valid range
            
            confidence = float(sentiment_data.get("confidence", 0.5))
            confidence = max(0.0, min(1.0, confidence))  # Clamp to valid range
            
            label = sentiment_data.get("label", "neutral").lower()
            if label not in ["positive", "negative", "neutral"]:
                label = "neutral"
            
            reasoning = sentiment_data.get("reasoning", "AI-based sentiment analysis")
            
            return SentimentClassificationResult(
                sentiment_score=score,
                sentiment_label=label,
                confidence=confidence,
                reasoning=reasoning,
                metadata={"method": "ai", "model": "you.com_custom_agent"}
            )
            
        except Exception as e:
            logger.error(f"AI sentiment classification error: {str(e)}")
            raise

    def _rule_based_sentiment_classification(self, text: str, entities: List[EntityRecognitionResult]) -> SentimentClassificationResult:
        """Rule-based sentiment classification as fallback."""
        text_lower = text.lower()
        
        # Calculate sentiment score based on indicators
        positive_score = 0.0
        negative_score = 0.0
        
        for word, weight in self.positive_indicators.items():
            count = text_lower.count(word)
            positive_score += count * weight
        
        for word, weight in self.negative_indicators.items():
            count = text_lower.count(word)
            negative_score += count * abs(weight)  # Make positive for calculation
        
        # Normalize scores
        total_words = len(text.split())
        if total_words > 0:
            positive_score = min(1.0, positive_score / (total_words * 0.1))
            negative_score = min(1.0, negative_score / (total_words * 0.1))
        
        # Calculate final sentiment
        if positive_score > negative_score:
            final_score = positive_score - (negative_score * 0.5)
            label = "positive"
        elif negative_score > positive_score:
            final_score = -(negative_score - (positive_score * 0.5))
            label = "negative"
        else:
            final_score = 0.0
            label = "neutral"
        
        # Clamp final score
        final_score = max(-1.0, min(1.0, final_score))
        
        # Calculate confidence based on score strength
        confidence = min(0.8, abs(final_score) + 0.3)  # Rule-based max confidence is 0.8
        
        reasoning = f"Rule-based analysis: {len([w for w in self.positive_indicators if w in text_lower])} positive indicators, {len([w for w in self.negative_indicators if w in text_lower])} negative indicators"
        
        return SentimentClassificationResult(
            sentiment_score=final_score,
            sentiment_label=label,
            confidence=confidence,
            reasoning=reasoning,
            metadata={"method": "rule_based", "positive_score": positive_score, "negative_score": negative_score}
        )

    def _combine_sentiment_results(self, ai_result: SentimentClassificationResult, 
                                 rule_result: SentimentClassificationResult) -> SentimentClassificationResult:
        """Combine AI and rule-based results weighted by confidence."""
        ai_weight = ai_result.confidence
        rule_weight = rule_result.confidence * 0.7  # Slightly lower weight for rule-based
        
        total_weight = ai_weight + rule_weight
        
        if total_weight > 0:
            combined_score = (ai_result.sentiment_score * ai_weight + rule_result.sentiment_score * rule_weight) / total_weight
            combined_confidence = min(0.95, (ai_result.confidence + rule_result.confidence) / 2)
        else:
            combined_score = 0.0
            combined_confidence = 0.5
        
        # Determine label from combined score
        if combined_score > 0.1:
            label = "positive"
        elif combined_score < -0.1:
            label = "negative"
        else:
            label = "neutral"
        
        return SentimentClassificationResult(
            sentiment_score=combined_score,
            sentiment_label=label,
            confidence=combined_confidence,
            reasoning=f"Combined analysis: AI ({ai_result.confidence:.2f}) + Rules ({rule_result.confidence:.2f})",
            metadata={
                "method": "combined",
                "ai_result": ai_result.metadata,
                "rule_result": rule_result.metadata
            }
        )


# Global instances - lazy initialization
entity_recognizer = None
sentiment_classifier = None

def get_entity_recognizer():
    global entity_recognizer
    if entity_recognizer is None:
        entity_recognizer = EntityRecognizer()
    return entity_recognizer

def get_sentiment_classifier():
    global sentiment_classifier
    if sentiment_classifier is None:
        sentiment_classifier = SentimentClassifier()
    return sentiment_classifier