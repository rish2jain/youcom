"""
Explainability Engine - Provides transparent reasoning chains for all AI insights
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from urllib.parse import urlparse
import re

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.explainability import ReasoningStep, SourceCredibilityAnalysis, UncertaintyDetection
from app.models.impact_card import ImpactCard
from app.schemas.explainability import (
    ReasoningStepCreate, SourceCredibilityAnalysisCreate, UncertaintyDetectionCreate,
    EnhancedExplainability, ExplainabilityVisualization, HumanValidationRequest
)

logger = logging.getLogger(__name__)

class ExplainabilityEngine:
    """
    Core explainability engine that generates transparent reasoning chains
    for all AI-generated insights and risk scores.
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        
        # Tier definitions for source credibility
        self.tier_domains = {
            "tier1": {
                "domains": {
                    "nytimes.com", "wsj.com", "bloomberg.com", "reuters.com", 
                    "ft.com", "forbes.com", "techcrunch.com"
                },
                "score_range": (0.85, 1.0),
                "description": "Authoritative sources with high editorial standards"
            },
            "tier2": {
                "domains": {
                    "venturebeat.com", "theinformation.com", "axios.com", 
                    "businessinsider.com", "cnbc.com"
                },
                "score_range": (0.65, 0.84),
                "description": "Reputable sources with good editorial standards"
            },
            "tier3": {
                "domains": set(),  # Everything else
                "score_range": (0.20, 0.64),
                "description": "Community and unverified sources"
            }
        }
        
        # Confidence thresholds for uncertainty detection
        self.confidence_thresholds = {
            "critical": 0.3,  # Below this requires immediate human validation
            "high": 0.5,      # High uncertainty, recommend validation
            "medium": 0.7,    # Medium uncertainty, flag for review
            "low": 0.85       # Low uncertainty, acceptable
        }
        
        # Factor weights for risk score calculation
        self.default_factor_weights = {
            "product_impact": 0.25,
            "market_impact": 0.20,
            "competitive_threat": 0.20,
            "regulatory_impact": 0.15,
            "brand_impact": 0.10,
            "financial_impact": 0.10
        }

    async def generate_reasoning_chain(
        self, 
        impact_card_id: int,
        analysis_data: Dict[str, Any],
        source_data: Dict[str, Any]
    ) -> List[ReasoningStep]:
        """
        Generate a complete reasoning chain for risk score calculation.
        
        Args:
            impact_card_id: ID of the impact card
            analysis_data: Analysis results from You.com APIs
            source_data: Source quality and credibility data
            
        Returns:
            List of reasoning steps explaining the risk score calculation
        """
        logger.info(f"🔍 Generating reasoning chain for impact card {impact_card_id}")
        
        reasoning_steps = []
        step_order = 1
        
        # Step 1: Source Quality Assessment
        source_step = await self._create_source_assessment_step(
            impact_card_id, step_order, source_data
        )
        reasoning_steps.append(source_step)
        step_order += 1
        
        # Step 2: Impact Area Analysis
        impact_areas = analysis_data.get("impact_areas", [])
        for area in impact_areas:
            area_step = await self._create_impact_area_step(
                impact_card_id, step_order, area, source_data
            )
            reasoning_steps.append(area_step)
            step_order += 1
        
        # Step 3: Risk Score Calculation
        risk_step = await self._create_risk_calculation_step(
            impact_card_id, step_order, analysis_data, reasoning_steps
        )
        reasoning_steps.append(risk_step)
        step_order += 1
        
        # Step 4: Confidence Assessment
        confidence_step = await self._create_confidence_assessment_step(
            impact_card_id, step_order, analysis_data, source_data
        )
        reasoning_steps.append(confidence_step)
        
        # Save all reasoning steps to database
        for step in reasoning_steps:
            self.db.add(step)
        
        await self.db.commit()
        logger.info(f"✅ Generated {len(reasoning_steps)} reasoning steps")
        
        return reasoning_steps

    async def _create_source_assessment_step(
        self, 
        impact_card_id: int, 
        step_order: int, 
        source_data: Dict[str, Any]
    ) -> ReasoningStep:
        """Create reasoning step for source quality assessment"""
        
        source_quality = source_data.get("source_quality", {})
        total_sources = source_quality.get("total", 0)
        quality_score = source_quality.get("score", 0.0)
        tier_breakdown = source_quality.get("tiers", {})
        
        # Calculate factor weight based on source quality
        factor_weight = min(0.3, quality_score * 0.3)  # Max 30% weight for sources
        
        # Build evidence from top sources
        evidence_sources = []
        for source in source_quality.get("top_sources", [])[:3]:
            evidence_sources.append({
                "title": source.get("title", "Unknown"),
                "url": source.get("url", ""),
                "tier": source.get("tier", "tier3"),
                "weight": source.get("weight", 0.5)
            })
        
        # Generate reasoning text
        tier1_count = tier_breakdown.get("tier1", 0)
        tier2_count = tier_breakdown.get("tier2", 0)
        tier3_count = tier_breakdown.get("tier3", 0)
        
        reasoning_text = (
            f"Source quality assessment based on {total_sources} sources: "
            f"{tier1_count} tier-1 (authoritative), {tier2_count} tier-2 (reputable), "
            f"{tier3_count} tier-3 (community). Overall quality score: {quality_score:.2f}. "
            f"Higher quality sources increase confidence in the analysis."
        )
        
        # Detect uncertainty flags
        uncertainty_flags = []
        if quality_score < 0.5:
            uncertainty_flags.append("low_source_quality")
        if tier1_count == 0:
            uncertainty_flags.append("no_authoritative_sources")
        if total_sources < 3:
            uncertainty_flags.append("insufficient_sources")
        
        return ReasoningStep(
            impact_card_id=impact_card_id,
            step_order=step_order,
            step_type="source_assessment",
            step_name="Source Quality Assessment",
            factor_name="Source Credibility",
            factor_weight=factor_weight,
            factor_contribution=quality_score * factor_weight * 100,
            evidence_sources=evidence_sources,
            reasoning_text=reasoning_text,
            confidence_level=quality_score,
            uncertainty_flags=uncertainty_flags,
            conflicting_evidence=[]
        )

    async def _create_impact_area_step(
        self, 
        impact_card_id: int, 
        step_order: int, 
        impact_area: Dict[str, Any],
        source_data: Dict[str, Any]
    ) -> ReasoningStep:
        """Create reasoning step for individual impact area analysis"""
        
        area_name = impact_area.get("area", "Unknown Impact")
        impact_score = impact_area.get("impact_score", 50)
        description = impact_area.get("description", "No description available")
        
        # Determine factor weight based on impact area type
        area_type = area_name.lower()
        factor_weight = self.default_factor_weights.get(
            area_type.replace(" ", "_"), 0.15
        )
        
        # Calculate contribution to risk score
        factor_contribution = (impact_score / 100.0) * factor_weight * 100
        
        # Build evidence from sources related to this impact area
        evidence_sources = []
        top_sources = source_data.get("source_quality", {}).get("top_sources", [])
        for source in top_sources[:2]:  # Top 2 sources per impact area
            if self._is_source_relevant_to_area(source, area_name):
                evidence_sources.append({
                    "title": source.get("title", "Unknown"),
                    "url": source.get("url", ""),
                    "relevance": "high",
                    "tier": source.get("tier", "tier3")
                })
        
        # Generate reasoning text
        reasoning_text = (
            f"Impact area '{area_name}' analysis: {description}. "
            f"Impact score: {impact_score}/100. Factor weight: {factor_weight:.2f}. "
            f"This contributes {factor_contribution:.1f} points to the overall risk score."
        )
        
        # Detect uncertainty flags
        uncertainty_flags = []
        if impact_score > 80 and len(evidence_sources) < 2:
            uncertainty_flags.append("high_impact_insufficient_evidence")
        if not description or len(description) < 20:
            uncertainty_flags.append("insufficient_analysis_detail")
        
        # Calculate confidence based on evidence quality
        confidence_level = min(0.9, len(evidence_sources) * 0.3 + 0.4)
        
        return ReasoningStep(
            impact_card_id=impact_card_id,
            step_order=step_order,
            step_type="impact_analysis",
            step_name=f"Impact Analysis: {area_name}",
            factor_name=area_name,
            factor_weight=factor_weight,
            factor_contribution=factor_contribution,
            evidence_sources=evidence_sources,
            reasoning_text=reasoning_text,
            confidence_level=confidence_level,
            uncertainty_flags=uncertainty_flags,
            conflicting_evidence=[]
        )

    async def _create_risk_calculation_step(
        self, 
        impact_card_id: int, 
        step_order: int, 
        analysis_data: Dict[str, Any],
        previous_steps: List[ReasoningStep]
    ) -> ReasoningStep:
        """Create reasoning step for final risk score calculation"""
        
        risk_score = analysis_data.get("risk_score", 50)
        risk_level = analysis_data.get("risk_level", "medium")
        
        # Calculate total contribution from all factors
        total_contribution = sum(step.factor_contribution for step in previous_steps)
        
        # Build evidence from all previous steps
        evidence_sources = []
        for step in previous_steps:
            if step.evidence_sources:
                evidence_sources.extend(step.evidence_sources[:1])  # One source per step
        
        # Generate reasoning text
        reasoning_text = (
            f"Final risk score calculation: {risk_score}/100 ({risk_level} risk). "
            f"Calculated from {len(previous_steps)} contributing factors with "
            f"total weighted contribution of {total_contribution:.1f} points. "
            f"Risk level determined by score thresholds: "
            f"0-30 (low), 31-60 (medium), 61-80 (high), 81-100 (critical)."
        )
        
        # Detect uncertainty flags
        uncertainty_flags = []
        if previous_steps:
            avg_confidence = sum(step.confidence_level for step in previous_steps) / len(previous_steps)
        else:
            avg_confidence = 0.0
        if avg_confidence < 0.6:
            uncertainty_flags.append("low_average_confidence")
        if abs(total_contribution - risk_score) > 20:
            uncertainty_flags.append("calculation_discrepancy")
        
        return ReasoningStep(
            impact_card_id=impact_card_id,
            step_order=step_order,
            step_type="risk_calculation",
            step_name="Final Risk Score Calculation",
            factor_name="Overall Risk Assessment",
            factor_weight=1.0,  # Final calculation gets full weight
            factor_contribution=risk_score,
            evidence_sources=evidence_sources,
            reasoning_text=reasoning_text,
            confidence_level=avg_confidence,
            uncertainty_flags=uncertainty_flags,
            conflicting_evidence=[]
        )

    async def _create_confidence_assessment_step(
        self, 
        impact_card_id: int, 
        step_order: int, 
        analysis_data: Dict[str, Any],
        source_data: Dict[str, Any]
    ) -> ReasoningStep:
        """Create reasoning step for confidence assessment"""
        
        confidence_score = analysis_data.get("confidence_score", 70)
        source_quality_score = source_data.get("source_quality", {}).get("score", 0.5)
        
        # Calculate confidence factors
        data_quality_factor = source_quality_score
        analysis_depth_factor = min(1.0, len(analysis_data.get("impact_areas", [])) / 3.0)
        source_diversity_factor = min(1.0, source_data.get("source_quality", {}).get("total", 0) / 5.0)
        
        overall_confidence = (data_quality_factor + analysis_depth_factor + source_diversity_factor) / 3.0
        
        # Build evidence
        evidence_sources = [{
            "factor": "Data Quality",
            "score": f"{data_quality_factor:.2f}",
            "description": f"Based on {source_data.get('source_quality', {}).get('total', 0)} sources"
        }, {
            "factor": "Analysis Depth", 
            "score": f"{analysis_depth_factor:.2f}",
            "description": f"Based on {len(analysis_data.get('impact_areas', []))} impact areas"
        }, {
            "factor": "Source Diversity",
            "score": f"{source_diversity_factor:.2f}",
            "description": "Based on source variety and coverage"
        }]
        
        # Generate reasoning text
        reasoning_text = (
            f"Confidence assessment: {confidence_score}/100. "
            f"Calculated from data quality ({data_quality_factor:.2f}), "
            f"analysis depth ({analysis_depth_factor:.2f}), and "
            f"source diversity ({source_diversity_factor:.2f}). "
            f"Overall confidence: {overall_confidence:.2f}."
        )
        
        # Detect uncertainty flags
        uncertainty_flags = []
        if overall_confidence < 0.5:
            uncertainty_flags.append("low_overall_confidence")
        if confidence_score < 60:
            uncertainty_flags.append("low_model_confidence")
        
        return ReasoningStep(
            impact_card_id=impact_card_id,
            step_order=step_order,
            step_type="confidence_assessment",
            step_name="Confidence Assessment",
            factor_name="Analysis Confidence",
            factor_weight=0.0,  # Confidence doesn't contribute to risk score
            factor_contribution=0.0,
            evidence_sources=evidence_sources,
            reasoning_text=reasoning_text,
            confidence_level=overall_confidence,
            uncertainty_flags=uncertainty_flags,
            conflicting_evidence=[]
        )

    def _is_source_relevant_to_area(self, source: Dict[str, Any], area_name: str) -> bool:
        """Check if a source is relevant to a specific impact area"""
        title = source.get("title", "").lower()
        area_keywords = area_name.lower().split()
        
        # Simple keyword matching - could be enhanced with NLP
        for keyword in area_keywords:
            if keyword in title:
                return True
        return False

    async def analyze_source_quality(
        self, 
        impact_card_id: int,
        source_data: Dict[str, Any]
    ) -> List[SourceCredibilityAnalysis]:
        """
        Perform detailed source quality analysis for all sources.
        
        Args:
            impact_card_id: ID of the impact card
            source_data: Raw source data from You.com APIs
            
        Returns:
            List of source credibility analyses
        """
        logger.info(f"🔍 Analyzing source quality for impact card {impact_card_id}")
        
        analyses = []
        source_quality = source_data.get("source_quality", {})
        
        for source in source_quality.get("top_sources", []):
            analysis = await self._analyze_individual_source(impact_card_id, source)
            analyses.append(analysis)
        
        # Detect conflicts between sources
        await self._detect_source_conflicts(analyses)
        
        # Save all analyses to database
        for analysis in analyses:
            self.db.add(analysis)
        
        await self.db.commit()
        logger.info(f"✅ Analyzed {len(analyses)} sources")
        
        return analyses

    async def _analyze_individual_source(
        self, 
        impact_card_id: int, 
        source: Dict[str, Any]
    ) -> SourceCredibilityAnalysis:
        """Analyze credibility of an individual source"""
        
        url = source.get("url", "")
        title = source.get("title", "")
        source_type = source.get("type", "unknown")
        tier = source.get("tier", "tier3")
        
        # Parse domain for analysis
        domain = urlparse(url).netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        
        # Calculate credibility scores
        authority_score = self._calculate_authority_score(domain, tier)
        recency_score = self._calculate_recency_score(source)
        relevance_score = self._calculate_relevance_score(source)
        
        # Overall credibility score
        credibility_score = (authority_score + recency_score + relevance_score) / 3.0
        
        # Determine validation method
        validation_method = f"Domain tier analysis + {source_type} source validation"
        
        # Generate quality and warning flags
        quality_flags = []
        warning_flags = []
        
        if tier == "tier1":
            quality_flags.append("authoritative_source")
        if domain.endswith(".gov") or domain.endswith(".edu"):
            quality_flags.append("official_source")
        if credibility_score > 0.8:
            quality_flags.append("high_credibility")
        
        if credibility_score < 0.5:
            warning_flags.append("low_credibility")
        if not title or len(title) < 10:
            warning_flags.append("insufficient_metadata")
        if source_type == "unknown":
            warning_flags.append("unknown_source_type")
        
        return SourceCredibilityAnalysis(
            impact_card_id=impact_card_id,
            source_url=url,
            source_title=title,
            source_type=source_type,
            tier_level=tier,
            credibility_score=credibility_score,
            authority_score=authority_score,
            recency_score=recency_score,
            relevance_score=relevance_score,
            validation_method=validation_method,
            quality_flags=quality_flags,
            warning_flags=warning_flags,
            conflicts_with=[],
            conflict_severity="none"
        )

    def _calculate_authority_score(self, domain: str, tier: str) -> float:
        """Calculate authority score based on domain and tier"""
        tier_scores = {
            "tier1": 0.9,
            "tier2": 0.7,
            "tier3": 0.4
        }
        
        base_score = tier_scores.get(tier, 0.3)
        
        # Bonus for specific high-authority domains
        if domain in {"reuters.com", "bloomberg.com", "wsj.com"}:
            base_score = min(1.0, base_score + 0.1)
        
        return base_score

    def _calculate_recency_score(self, source: Dict[str, Any]) -> float:
        """Calculate recency score (placeholder - would need timestamp data)"""
        # In a real implementation, this would analyze publication date
        # For now, return a default score
        return 0.8

    def _calculate_relevance_score(self, source: Dict[str, Any]) -> float:
        """Calculate relevance score based on title and content"""
        title = source.get("title", "").lower()
        
        # Simple relevance scoring based on business keywords
        business_keywords = [
            "launch", "product", "funding", "acquisition", "partnership",
            "revenue", "growth", "market", "competition", "strategy"
        ]
        
        relevance_count = sum(1 for keyword in business_keywords if keyword in title)
        return min(1.0, relevance_count / 3.0 + 0.3)

    async def _detect_source_conflicts(self, analyses: List[SourceCredibilityAnalysis]) -> None:
        """Detect conflicts between sources"""
        # Simple conflict detection based on domain similarity and credibility differences
        for i, analysis1 in enumerate(analyses):
            for j, analysis2 in enumerate(analyses[i+1:], i+1):
                if self._sources_conflict(analysis1, analysis2):
                    analyses[i].conflicts_with.append(j)
                    analyses[j].conflicts_with.append(i)
                    
                    # Determine conflict severity
                    credibility_diff = abs(analysis1.credibility_score - analysis2.credibility_score)
                    if credibility_diff > 0.5:
                        analyses[i].conflict_severity = "major"
                        analyses[j].conflict_severity = "major"
                    else:
                        analyses[i].conflict_severity = "minor"
                        analyses[j].conflict_severity = "minor"

    def _sources_conflict(self, analysis1: SourceCredibilityAnalysis, analysis2: SourceCredibilityAnalysis) -> bool:
        """Determine if two sources conflict with each other"""
        # Simple conflict detection - could be enhanced with content analysis
        domain1 = urlparse(analysis1.source_url).netloc.lower()
        domain2 = urlparse(analysis2.source_url).netloc.lower()
        
        # Same domain but different tiers might indicate conflict
        if domain1 == domain2 and analysis1.tier_level != analysis2.tier_level:
            return True
        
        # Large credibility score differences might indicate conflict
        if abs(analysis1.credibility_score - analysis2.credibility_score) > 0.6:
            return True
        
        return False

    async def detect_uncertainty(
        self, 
        impact_card_id: int,
        analysis_data: Dict[str, Any],
        reasoning_steps: List[ReasoningStep],
        source_analyses: List[SourceCredibilityAnalysis]
    ) -> List[UncertaintyDetection]:
        """
        Detect uncertainty in the analysis and recommend human validation.
        
        Args:
            impact_card_id: ID of the impact card
            analysis_data: Analysis results
            reasoning_steps: Generated reasoning steps
            source_analyses: Source credibility analyses
            
        Returns:
            List of uncertainty detections
        """
        logger.info(f"🔍 Detecting uncertainty for impact card {impact_card_id}")
        
        detections = []
        
        # Check overall confidence levels
        if reasoning_steps:
            avg_confidence = sum(step.confidence_level for step in reasoning_steps) / len(reasoning_steps)
        else:
            avg_confidence = 0.0
        if avg_confidence < self.confidence_thresholds["critical"]:
            detections.append(await self._create_uncertainty_detection(
                impact_card_id, "low_confidence", "critical", avg_confidence,
                ["risk_score", "impact_areas", "recommended_actions"],
                f"Average confidence ({avg_confidence:.2f}) is below critical threshold",
                True, ["immediate_human_review", "additional_data_collection"], "urgent"
            ))
        elif avg_confidence < self.confidence_thresholds["high"]:
            detections.append(await self._create_uncertainty_detection(
                impact_card_id, "medium_confidence", "high", avg_confidence,
                ["risk_score", "recommended_actions"],
                f"Average confidence ({avg_confidence:.2f}) indicates high uncertainty",
                True, ["human_review", "source_verification"], "high"
            ))
        
        # Check for conflicting sources
        conflicting_sources = [s for s in source_analyses if s.conflict_severity in ["major", "critical"]]
        if conflicting_sources:
            detections.append(await self._create_uncertainty_detection(
                impact_card_id, "conflicting_evidence", "medium", 0.5,
                ["source_quality", "credibility_score"],
                f"Found {len(conflicting_sources)} sources with conflicting information",
                True, ["source_reconciliation", "expert_review"], "medium"
            ))
        
        # Check for insufficient data
        total_sources = len(source_analyses)
        if total_sources < 3:
            detections.append(await self._create_uncertainty_detection(
                impact_card_id, "insufficient_data", "medium", 0.4,
                ["risk_score", "confidence_score"],
                f"Only {total_sources} sources available for analysis",
                False, ["additional_data_collection", "broader_search"], "medium"
            ))
        
        # Check for high-impact areas with low evidence
        for step in reasoning_steps:
            if (step.step_type == "impact_analysis" and 
                step.factor_contribution > 20 and 
                len(step.evidence_sources) < 2):
                detections.append(await self._create_uncertainty_detection(
                    impact_card_id, "high_impact_low_evidence", "high", step.confidence_level,
                    [step.factor_name],
                    f"High-impact factor '{step.factor_name}' has insufficient supporting evidence",
                    True, ["targeted_research", "expert_consultation"], "high"
                ))
        
        # Save all detections to database
        for detection in detections:
            self.db.add(detection)
        
        await self.db.commit()
        logger.info(f"✅ Detected {len(detections)} uncertainty issues")
        
        return detections

    async def _create_uncertainty_detection(
        self,
        impact_card_id: int,
        uncertainty_type: str,
        uncertainty_level: str,
        confidence_threshold: float,
        affected_components: List[str],
        description: str,
        human_validation_required: bool,
        recommended_actions: List[str],
        validation_priority: str
    ) -> UncertaintyDetection:
        """Create an uncertainty detection record"""
        
        return UncertaintyDetection(
            impact_card_id=impact_card_id,
            uncertainty_type=uncertainty_type,
            uncertainty_level=uncertainty_level,
            confidence_threshold=confidence_threshold,
            affected_components=affected_components,
            uncertainty_description=description,
            human_validation_required=human_validation_required,
            recommended_actions=recommended_actions,
            validation_priority=validation_priority,
            is_resolved=False,
            resolution_method=None,
            resolved_by=None,
            resolved_at=None
        )

    async def build_enhanced_explainability(
        self, 
        impact_card_id: int
    ) -> EnhancedExplainability:
        """
        Build complete enhanced explainability for an impact card.
        
        Args:
            impact_card_id: ID of the impact card
            
        Returns:
            Enhanced explainability with all components
        """
        logger.info(f"🔍 Building enhanced explainability for impact card {impact_card_id}")
        
        # Fetch all explainability components from database
        reasoning_steps_result = await self.db.execute(
            select(ReasoningStep).where(ReasoningStep.impact_card_id == impact_card_id)
            .order_by(ReasoningStep.step_order)
        )
        reasoning_steps = reasoning_steps_result.scalars().all()
        
        source_analyses_result = await self.db.execute(
            select(SourceCredibilityAnalysis).where(SourceCredibilityAnalysis.impact_card_id == impact_card_id)
        )
        source_analyses = source_analyses_result.scalars().all()
        
        uncertainty_detections_result = await self.db.execute(
            select(UncertaintyDetection).where(UncertaintyDetection.impact_card_id == impact_card_id)
        )
        uncertainty_detections = uncertainty_detections_result.scalars().all()
        
        # Calculate summary metrics
        overall_confidence = sum(step.confidence_level for step in reasoning_steps) / len(reasoning_steps) if reasoning_steps else 0.0
        source_quality_score = sum(analysis.credibility_score for analysis in source_analyses) / len(source_analyses) if source_analyses else 0.0
        
        # Determine overall uncertainty level
        uncertainty_level = "low"
        if any(d.uncertainty_level == "critical" for d in uncertainty_detections):
            uncertainty_level = "critical"
        elif any(d.uncertainty_level == "high" for d in uncertainty_detections):
            uncertainty_level = "high"
        elif any(d.uncertainty_level == "medium" for d in uncertainty_detections):
            uncertainty_level = "medium"
        
        # Check if human validation is recommended
        human_validation_recommended = any(d.human_validation_required for d in uncertainty_detections)
        
        return EnhancedExplainability(
            reasoning_chain=reasoning_steps,
            source_analyses=source_analyses,
            uncertainty_detections=uncertainty_detections,
            overall_confidence=overall_confidence,
            source_quality_score=source_quality_score,
            uncertainty_level=uncertainty_level,
            human_validation_recommended=human_validation_recommended
        )

    async def create_visualization_data(
        self, 
        impact_card_id: int
    ) -> ExplainabilityVisualization:
        """
        Create visualization data for explainability dashboard.
        
        Args:
            impact_card_id: ID of the impact card
            
        Returns:
            Visualization data structure
        """
        # Fetch reasoning steps
        reasoning_steps_result = await self.db.execute(
            select(ReasoningStep).where(ReasoningStep.impact_card_id == impact_card_id)
        )
        reasoning_steps = reasoning_steps_result.scalars().all()
        
        # Fetch source analyses
        source_analyses_result = await self.db.execute(
            select(SourceCredibilityAnalysis).where(SourceCredibilityAnalysis.impact_card_id == impact_card_id)
        )
        source_analyses = source_analyses_result.scalars().all()
        
        # Fetch uncertainty detections
        uncertainty_detections_result = await self.db.execute(
            select(UncertaintyDetection).where(UncertaintyDetection.impact_card_id == impact_card_id)
        )
        uncertainty_detections = uncertainty_detections_result.scalars().all()
        
        # Build factor weights
        factor_weights = {}
        contribution_breakdown = {}
        for step in reasoning_steps:
            if step.factor_weight > 0:
                factor_weights[step.factor_name] = step.factor_weight
                contribution_breakdown[step.factor_name] = step.factor_contribution
        
        # Build source quality breakdown
        source_quality_breakdown = {"tier1": {}, "tier2": {}, "tier3": {}}
        for analysis in source_analyses:
            tier = analysis.tier_level
            if tier not in source_quality_breakdown:
                source_quality_breakdown[tier] = {}
            
            source_quality_breakdown[tier][analysis.source_url] = {
                "credibility_score": analysis.credibility_score,
                "authority_score": analysis.authority_score,
                "quality_flags": analysis.quality_flags,
                "warning_flags": analysis.warning_flags
            }
        
        # Build uncertainty summary
        uncertainty_summary = {}
        for detection in uncertainty_detections:
            uncertainty_type = detection.uncertainty_type
            uncertainty_summary[uncertainty_type] = uncertainty_summary.get(uncertainty_type, 0) + 1
        
        # Build confidence intervals (simplified)
        confidence_intervals = {}
        for step in reasoning_steps:
            confidence_intervals[step.factor_name] = {
                "lower": max(0.0, step.confidence_level - 0.1),
                "upper": min(1.0, step.confidence_level + 0.1),
                "mean": step.confidence_level
            }
        
        return ExplainabilityVisualization(
            factor_weights=factor_weights,
            contribution_breakdown=contribution_breakdown,
            source_quality_breakdown=source_quality_breakdown,
            uncertainty_summary=uncertainty_summary,
            confidence_intervals=confidence_intervals
        )