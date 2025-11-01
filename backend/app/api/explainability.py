"""
Explainability Engine API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any
import logging

from app.database import get_db
from app.models.impact_card import ImpactCard
from app.models.explainability import ReasoningStep, SourceCredibilityAnalysis, UncertaintyDetection
from app.services.explainability_engine import ExplainabilityEngine
from app.schemas.explainability import (
    EnhancedExplainability, ExplainabilityVisualization, 
    HumanValidationRequest, HumanValidationResponse,
    ReasoningStep as ReasoningStepSchema,
    SourceCredibilityAnalysis as SourceCredibilityAnalysisSchema,
    UncertaintyDetection as UncertaintyDetectionSchema
)

router = APIRouter(prefix="/explainability", tags=["explainability"])
logger = logging.getLogger(__name__)

@router.post("/generate/{impact_card_id}")
async def generate_explainability(
    impact_card_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate enhanced explainability for an impact card.
    This creates detailed reasoning chains, source analyses, and uncertainty detections.
    """
    # Verify impact card exists
    result = await db.execute(select(ImpactCard).where(ImpactCard.id == impact_card_id))
    impact_card = result.scalar_one_or_none()
    
    if not impact_card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Impact Card not found"
        )
    
    try:
        logger.info(f"🔍 Generating explainability for impact card {impact_card_id}")
        
        # Initialize explainability engine
        explainability_engine = ExplainabilityEngine(db)
        
        # Extract analysis and source data from impact card
        explainability = impact_card.explainability or {}
        analysis_data = {
            "risk_score": impact_card.risk_score,
            "risk_level": impact_card.risk_level,
            "confidence_score": impact_card.confidence_score,
            "impact_areas": impact_card.impact_areas,
            "key_insights": impact_card.key_insights,
            "reasoning": explainability.get("reasoning")
        }
        
        source_data = {
            "source_quality": impact_card.source_quality or {},
            "total_sources": impact_card.total_sources,
            "source_breakdown": impact_card.source_breakdown or {}
        }
        
        # Generate reasoning chain
        reasoning_steps = await explainability_engine.generate_reasoning_chain(
            impact_card_id, analysis_data, source_data
        )
        
        # Analyze source quality
        source_analyses = await explainability_engine.analyze_source_quality(
            impact_card_id, source_data
        )
        
        # Detect uncertainty
        uncertainty_detections = await explainability_engine.detect_uncertainty(
            impact_card_id, analysis_data, reasoning_steps, source_analyses
        )
        
        # Update impact card explainability field
        enhanced_explainability = {
            "reasoning": analysis_data.get("reasoning"),
            "impact_areas": analysis_data.get("impact_areas", []),
            "key_insights": analysis_data.get("key_insights", []),
            "source_summary": source_data.get("source_quality", {}),
            "enhanced_available": True,
            "reasoning_steps_count": len(reasoning_steps),
            "source_analyses_count": len(source_analyses),
            "uncertainty_detections_count": len(uncertainty_detections),
            "human_validation_recommended": any(d.human_validation_required for d in uncertainty_detections)
        }
        
        impact_card.explainability = enhanced_explainability
        await db.commit()
        
        logger.info(f"✅ Generated explainability with {len(reasoning_steps)} reasoning steps, "
                   f"{len(source_analyses)} source analyses, and {len(uncertainty_detections)} uncertainty detections")
        
        return {
            "message": "Explainability generated successfully",
            "impact_card_id": impact_card_id,
            "reasoning_steps_count": len(reasoning_steps),
            "source_analyses_count": len(source_analyses),
            "uncertainty_detections_count": len(uncertainty_detections),
            "human_validation_recommended": enhanced_explainability["human_validation_recommended"]
        }
        
    except Exception as e:
        logger.error(f"❌ Error generating explainability: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate explainability: {str(e)}"
        )

@router.get("/{impact_card_id}", response_model=EnhancedExplainability)
async def get_explainability(
    impact_card_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get complete explainability data for an impact card"""
    # Verify impact card exists
    result = await db.execute(select(ImpactCard).where(ImpactCard.id == impact_card_id))
    impact_card = result.scalar_one_or_none()
    
    if not impact_card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Impact Card not found"
        )
    
    try:
        explainability_engine = ExplainabilityEngine(db)
        enhanced_explainability = await explainability_engine.build_enhanced_explainability(impact_card_id)
        
        # Add basic explainability data from impact card
        explainability = impact_card.explainability or {}
        enhanced_explainability.reasoning = explainability.get("reasoning")
        enhanced_explainability.impact_areas = impact_card.impact_areas or []
        enhanced_explainability.key_insights = impact_card.key_insights or []
        enhanced_explainability.source_summary = impact_card.source_quality or {}
        
        return enhanced_explainability
        
    except Exception as e:
        logger.error(f"❌ Error retrieving explainability: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve explainability: {str(e)}"
        )

@router.get("/{impact_card_id}/reasoning-steps", response_model=List[ReasoningStepSchema])
async def get_reasoning_steps(
    impact_card_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get reasoning steps for an impact card"""
    # Verify impact card exists
    result = await db.execute(select(ImpactCard).where(ImpactCard.id == impact_card_id))
    impact_card = result.scalar_one_or_none()
    
    if not impact_card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Impact Card not found"
        )
    
    # Get reasoning steps
    steps_result = await db.execute(
        select(ReasoningStep)
        .where(ReasoningStep.impact_card_id == impact_card_id)
        .order_by(ReasoningStep.step_order)
    )
    steps = steps_result.scalars().all()
    
    return steps

@router.get("/{impact_card_id}/source-analyses", response_model=List[SourceCredibilityAnalysisSchema])
async def get_source_analyses(
    impact_card_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get source credibility analyses for an impact card"""
    # Verify impact card exists
    result = await db.execute(select(ImpactCard).where(ImpactCard.id == impact_card_id))
    impact_card = result.scalar_one_or_none()
    
    if not impact_card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Impact Card not found"
        )
    
    # Get source analyses
    analyses_result = await db.execute(
        select(SourceCredibilityAnalysis)
        .where(SourceCredibilityAnalysis.impact_card_id == impact_card_id)
        .order_by(SourceCredibilityAnalysis.credibility_score.desc())
    )
    analyses = analyses_result.scalars().all()
    
    return analyses

@router.get("/{impact_card_id}/uncertainty-detections", response_model=List[UncertaintyDetectionSchema])
async def get_uncertainty_detections(
    impact_card_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get uncertainty detections for an impact card"""
    # Verify impact card exists
    result = await db.execute(select(ImpactCard).where(ImpactCard.id == impact_card_id))
    impact_card = result.scalar_one_or_none()
    
    if not impact_card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Impact Card not found"
        )
    
    # Get uncertainty detections
    detections_result = await db.execute(
        select(UncertaintyDetection)
        .where(UncertaintyDetection.impact_card_id == impact_card_id)
        .order_by(UncertaintyDetection.validation_priority.desc(), UncertaintyDetection.uncertainty_level.desc())
    )
    detections = detections_result.scalars().all()
    
    return detections

@router.get("/{impact_card_id}/visualization", response_model=ExplainabilityVisualization)
async def get_explainability_visualization(
    impact_card_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get visualization data for explainability dashboard"""
    # Verify impact card exists
    result = await db.execute(select(ImpactCard).where(ImpactCard.id == impact_card_id))
    impact_card = result.scalar_one_or_none()
    
    if not impact_card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Impact Card not found"
        )
    
    try:
        explainability_engine = ExplainabilityEngine(db)
        visualization_data = await explainability_engine.create_visualization_data(impact_card_id)
        return visualization_data
        
    except Exception as e:
        logger.error(f"❌ Error creating visualization data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create visualization data: {str(e)}"
        )

@router.post("/{impact_card_id}/validate")
async def request_human_validation(
    impact_card_id: int,
    request: HumanValidationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Request human validation for uncertain analysis components"""
    # Verify impact card exists
    result = await db.execute(select(ImpactCard).where(ImpactCard.id == impact_card_id))
    impact_card = result.scalar_one_or_none()
    
    if not impact_card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Impact Card not found"
        )
    
    # Verify uncertainty detections exist
    for uncertainty_id in request.uncertainty_ids:
        uncertainty_result = await db.execute(
            select(UncertaintyDetection).where(UncertaintyDetection.id == uncertainty_id)
        )
        uncertainty = uncertainty_result.scalar_one_or_none()
        
        if not uncertainty:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Uncertainty detection {uncertainty_id} not found"
            )
        
        if uncertainty.impact_card_id != impact_card_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Uncertainty detection {uncertainty_id} does not belong to impact card {impact_card_id}"
            )
    
    # In a real implementation, this would create a validation request
    # and notify human validators. For now, we'll just return a success response.
    
    logger.info(f"🔍 Human validation requested for impact card {impact_card_id} "
               f"with {len(request.uncertainty_ids)} uncertainty detections")
    
    return {
        "message": "Human validation request submitted successfully",
        "impact_card_id": impact_card_id,
        "uncertainty_ids": request.uncertainty_ids,
        "validation_priority": request.validation_priority,
        "requested_by": request.requested_by,
        "estimated_completion": "2-4 hours"  # Placeholder
    }

@router.post("/validate/{uncertainty_id}")
async def submit_human_validation(
    uncertainty_id: int,
    response: HumanValidationResponse,
    db: AsyncSession = Depends(get_db)
):
    """Submit human validation response for an uncertainty detection"""
    # Get uncertainty detection
    result = await db.execute(select(UncertaintyDetection).where(UncertaintyDetection.id == uncertainty_id))
    uncertainty = result.scalar_one_or_none()
    
    if not uncertainty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Uncertainty detection not found"
        )
    
    try:
        # Update uncertainty detection with validation results
        uncertainty.is_resolved = True
        uncertainty.resolution_method = "human_validation"
        uncertainty.resolved_by = response.validated_by
        uncertainty.resolved_at = response.validated_at
        
        # In a real implementation, this would also update the impact card
        # with corrected values if the validation found issues
        
        await db.commit()
        
        logger.info(f"✅ Human validation completed for uncertainty {uncertainty_id} "
                   f"by {response.validated_by}")
        
        return {
            "message": "Human validation submitted successfully",
            "uncertainty_id": uncertainty_id,
            "is_valid": response.is_valid,
            "validated_by": response.validated_by,
            "resolution_status": "resolved"
        }
        
    except Exception as e:
        logger.error(f"❌ Error submitting human validation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit human validation: {str(e)}"
        )