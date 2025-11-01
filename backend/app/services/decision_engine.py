import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.action_recommendation import ActionRecommendation, ResourceEstimate
from app.schemas.action_recommendation import (
    ActionRecommendationCreate, 
    ResourceEstimateBase,
    DecisionEngineRequest,
    DecisionEngineResponse
)
from app.services.action_templates import ActionTemplateManager, ActionCategory, ActionPriority, BudgetImpact

logger = logging.getLogger(__name__)

class DecisionEngine:
    """
    Core Decision Engine that transforms risk scores and intelligence into actionable recommendations.
    
    This service implements rule-based action generation for competitor scenarios,
    with categorization, resource estimation, and confidence scoring.
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.template_manager = ActionTemplateManager()

    
    async def generate_recommendations(
        self, 
        request: DecisionEngineRequest
    ) -> DecisionEngineResponse:
        """
        Generate action recommendations based on risk score and context.
        
        Args:
            request: Decision engine request with risk score and context
            
        Returns:
            DecisionEngineResponse with generated recommendations
        """
        start_time = time.time()
        
        try:
            # Determine risk category
            risk_category = self._categorize_risk(request.risk_score)
            
            # Get base templates for risk score
            base_templates = self.template_manager.get_templates_for_risk_score(request.risk_score)
            
            # Generate recommendations from templates
            recommendations = []
            for template in base_templates:
                recommendation = self._create_recommendation_from_template(
                    template, request
                )
                recommendations.append(recommendation)
            
            # Add context-specific recommendations
            context_recommendations = self._generate_context_specific_recommendations(request)
            recommendations.extend(context_recommendations)
            
            # Sort by overall score (descending)
            recommendations.sort(key=lambda x: x.overall_score, reverse=True)
            
            # Limit to top 3 recommendations
            recommendations = recommendations[:3]
            
            processing_time = int((time.time() - start_time) * 1000)
            
            # Calculate overall confidence
            confidence_level = self._calculate_overall_confidence(recommendations, request)
            
            # Generate reasoning summary
            reasoning_summary = self._generate_reasoning_summary(
                recommendations, request, risk_category
            )
            
            return DecisionEngineResponse(
                recommendations=recommendations,
                total_recommendations=len(recommendations),
                processing_time_ms=processing_time,
                confidence_level=confidence_level,
                reasoning_summary=reasoning_summary
            )
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            raise
    
    def _categorize_risk(self, risk_score: int) -> str:
        """Categorize risk score into risk levels."""
        if risk_score >= 90:
            return "critical"
        elif risk_score >= 80:
            return "high"
        elif risk_score >= 70:
            return "medium"
        else:
            return "low"
    
    def _create_recommendation_from_template(
        self, 
        template: Dict[str, Any], 
        request: DecisionEngineRequest
    ) -> ActionRecommendationCreate:
        """Create a recommendation from a template, customizing based on context."""
        
        # Calculate scores
        confidence_score = self._calculate_confidence_score(template, request)
        impact_score = self._calculate_impact_score(template, request)
        effort_score = self._calculate_effort_score(template)
        overall_score = self._calculate_overall_score(confidence_score, impact_score, effort_score)
        
        # Customize description with competitor name
        description = template["description"].replace(
            "Competitor", f"{request.competitor_name}"
        )
        
        # Add context-specific reasoning
        reasoning = template["reasoning"].copy()
        if request.key_insights:
            reasoning.append(f"Key insight: {request.key_insights[0]}")
        
        # Generate evidence links from context
        evidence_links = self._generate_evidence_links(request)
        
        return ActionRecommendationCreate(
            impact_card_id=0,  # Will be set when saving
            title=template["title"],
            description=description,
            category=template["category"],
            priority=template["priority"],
            timeline=template["timeline"],
            estimated_hours=template.get("estimated_hours"),
            team_members_required=template.get("team_members_required"),
            budget_impact=template["budget_impact"],
            dependencies=template.get("dependencies", []),
            confidence_score=confidence_score,
            impact_score=impact_score,
            effort_score=effort_score,
            overall_score=overall_score,
            reasoning=reasoning,
            evidence_links=evidence_links
        )
    
    def _generate_context_specific_recommendations(
        self, 
        request: DecisionEngineRequest
    ) -> List[ActionRecommendationCreate]:
        """Generate recommendations based on specific context and impact areas."""
        recommendations = []
        
        # Generate recommendations based on impact areas
        for impact_area in request.impact_areas:
            if impact_area["impact_score"] > 70:
                rec = self._create_impact_area_recommendation(impact_area, request)
                if rec:
                    recommendations.append(rec)
        
        return recommendations
    
    def _create_impact_area_recommendation(
        self, 
        impact_area: Dict[str, Any], 
        request: DecisionEngineRequest
    ) -> Optional[ActionRecommendationCreate]:
        """Create recommendation specific to an impact area."""
        
        # Get template for impact area
        template = self.template_manager.get_impact_area_template(impact_area["area"])
        if not template:
            return None
        
        # Calculate complexity factor based on impact score
        complexity_factor = impact_area["impact_score"] / 100
        
        # Get resource estimates
        budget_impact = BudgetImpact(template["budget_impact"])
        category = ActionCategory(template["category"])
        resources = self.template_manager.estimate_resources(
            category, budget_impact, complexity_factor
        )
        
        # Calculate scores based on impact area
        confidence_score = min(0.9, request.confidence_score / 100 + 0.1)
        impact_score = impact_area["impact_score"] / 100
        effort_score = self._calculate_effort_score_from_resources(resources)
        overall_score = self._calculate_overall_score(confidence_score, impact_score, effort_score)
        
        # Customize template with competitor name
        title = template["title"].format(competitor_name=request.competitor_name)
        description = template["description"].format(competitor_name=request.competitor_name)
        
        return ActionRecommendationCreate(
            impact_card_id=0,
            title=title,
            description=description,
            category=template["category"],
            priority=template["priority"],
            timeline=template["timeline"],
            estimated_hours=resources["estimated_hours"],
            team_members_required=resources["team_members_required"],
            budget_impact=template["budget_impact"],
            dependencies=template["dependencies"],
            confidence_score=confidence_score,
            impact_score=impact_score,
            effort_score=effort_score,
            overall_score=overall_score,
            reasoning=[
                f"High impact detected in {impact_area['area']} area",
                impact_area["description"]
            ] + template["reasoning"],
            evidence_links=self._generate_evidence_links(request)
        )
    
    def _calculate_confidence_score(
        self, 
        template: Dict[str, Any], 
        request: DecisionEngineRequest
    ) -> float:
        """Calculate confidence score for a recommendation."""
        base_confidence = 0.7
        
        # Adjust based on request confidence
        confidence_adjustment = (request.confidence_score / 100) * 0.3
        
        # Adjust based on risk score (higher risk = higher confidence in need for action)
        risk_adjustment = (request.risk_score / 100) * 0.2
        
        return min(1.0, base_confidence + confidence_adjustment + risk_adjustment)
    
    def _calculate_impact_score(
        self, 
        template: Dict[str, Any], 
        request: DecisionEngineRequest
    ) -> float:
        """Calculate expected impact score for a recommendation."""
        # Base impact based on category
        category_impact = {
            "immediate": 0.8,
            "short-term": 0.7,
            "strategic": 0.9
        }
        
        base_impact = category_impact.get(template["category"], 0.6)
        
        # Adjust based on risk score
        risk_adjustment = (request.risk_score / 100) * 0.3
        
        return min(1.0, base_impact + risk_adjustment)
    
    def _calculate_effort_score(self, template: Dict[str, Any]) -> float:
        """Calculate effort score (inverse of difficulty) for a recommendation."""
        # Base effort based on estimated hours and team size
        hours = template.get("estimated_hours", 40)
        team_size = template.get("team_members_required", 2)
        
        # Normalize effort (lower hours and team size = higher effort score)
        effort_factor = 1.0 - min(0.8, (hours * team_size) / 500)
        
        return max(0.2, effort_factor)
    
    def _calculate_effort_score_from_resources(self, resources: Dict[str, Any]) -> float:
        """Calculate effort score from resource estimates."""
        hours = resources.get("estimated_hours", 40)
        team_size = resources.get("team_members_required", 2)
        
        # Normalize effort (lower hours and team size = higher effort score)
        effort_factor = 1.0 - min(0.8, (hours * team_size) / 500)
        
        return max(0.2, effort_factor)
    
    def _calculate_overall_score(
        self, 
        confidence: float, 
        impact: float, 
        effort: float
    ) -> float:
        """Calculate overall recommendation score."""
        # Weighted combination: impact (50%), confidence (30%), effort (20%)
        return (impact * 0.5) + (confidence * 0.3) + (effort * 0.2)
    
    def _generate_evidence_links(
        self, 
        request: DecisionEngineRequest
    ) -> List[Dict[str, str]]:
        """Generate evidence links from request context."""
        evidence_links = []
        
        # Add context-based evidence if available
        if request.context and "sources" in request.context:
            for source in request.context["sources"][:3]:  # Limit to top 3
                evidence_links.append({
                    "title": source.get("title", "Supporting Evidence"),
                    "url": source.get("url", ""),
                    "source": source.get("source", "Unknown")
                })
        
        return evidence_links
    
    def _calculate_overall_confidence(
        self, 
        recommendations: List[ActionRecommendationCreate], 
        request: DecisionEngineRequest
    ) -> float:
        """Calculate overall confidence level for the recommendation set."""
        if not recommendations:
            return 0.0
        
        # Average confidence of all recommendations
        avg_confidence = sum(rec.confidence_score for rec in recommendations) / len(recommendations)
        
        # Adjust based on request confidence
        request_confidence = request.confidence_score / 100
        
        # Weighted average
        return (avg_confidence * 0.7) + (request_confidence * 0.3)
    
    def _generate_reasoning_summary(
        self, 
        recommendations: List[ActionRecommendationCreate], 
        request: DecisionEngineRequest,
        risk_category: str
    ) -> str:
        """Generate a summary of the reasoning behind the recommendations."""
        
        summary_parts = [
            f"Based on {risk_category} risk score of {request.risk_score}, "
            f"generated {len(recommendations)} strategic recommendations."
        ]
        
        if request.key_insights:
            summary_parts.append(
                f"Key insight driving recommendations: {request.key_insights[0]}"
            )
        
        if recommendations:
            top_rec = recommendations[0]
            summary_parts.append(
                f"Top priority: {top_rec.title} ({top_rec.category} action, "
                f"{top_rec.timeline} timeline)."
            )
        
        return " ".join(summary_parts)

    async def save_recommendations(
        self, 
        recommendations: List[ActionRecommendationCreate], 
        impact_card_id: int
    ) -> List[ActionRecommendation]:
        """Save recommendations to database."""
        saved_recommendations = []
        
        for rec_data in recommendations:
            # Set the impact card ID
            rec_data.impact_card_id = impact_card_id
            
            # Create database record
            db_recommendation = ActionRecommendation(
                impact_card_id=rec_data.impact_card_id,
                title=rec_data.title,
                description=rec_data.description,
                category=rec_data.category,
                priority=rec_data.priority,
                timeline=rec_data.timeline,
                estimated_hours=rec_data.estimated_hours,
                team_members_required=rec_data.team_members_required,
                budget_impact=rec_data.budget_impact,
                dependencies=rec_data.dependencies,
                confidence_score=rec_data.confidence_score,
                impact_score=rec_data.impact_score,
                effort_score=rec_data.effort_score,
                overall_score=rec_data.overall_score,
                reasoning=rec_data.reasoning,
                evidence_links=rec_data.evidence_links,
                okr_alignment=rec_data.okr_alignment,
                status=rec_data.status or "pending",
                assigned_to=rec_data.assigned_to,
                owner_type=rec_data.owner_type
            )
            
            self.db.add(db_recommendation)
            await self.db.flush()  # Get the ID
            
            # Create resource estimate if provided
            if rec_data.resource_estimate:
                resource_estimate = ResourceEstimate(
                    action_recommendation_id=db_recommendation.id,
                    **rec_data.resource_estimate.model_dump()
                )
                self.db.add(resource_estimate)
            
            saved_recommendations.append(db_recommendation)
        
        await self.db.commit()
        
        # Refresh to get relationships
        for rec in saved_recommendations:
            await self.db.refresh(rec)
        
        return saved_recommendations