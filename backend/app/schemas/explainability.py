"""
Enhanced explainability schemas for transparent AI reasoning
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class ReasoningStepBase(BaseModel):
    """Base schema for reasoning steps"""
    step_order: int = Field(ge=1, description="Order in the reasoning chain")
    step_type: str = Field(description="Type of reasoning step")
    step_name: str = Field(description="Human-readable step name")
    factor_name: str = Field(description="Name of the factor being analyzed")
    factor_weight: float = Field(ge=0.0, le=1.0, description="Importance weight of this factor")
    factor_contribution: float = Field(description="Contribution to final risk score")
    evidence_sources: List[Dict[str, Any]] = Field(default_factory=list, description="Supporting evidence")
    reasoning_text: str = Field(description="Detailed explanation of reasoning")
    confidence_level: float = Field(ge=0.0, le=1.0, description="Confidence in this step")
    uncertainty_flags: List[str] = Field(default_factory=list, description="Uncertainty indicators")
    conflicting_evidence: List[Dict[str, Any]] = Field(default_factory=list, description="Contradicting evidence")

class ReasoningStep(ReasoningStepBase):
    """Complete reasoning step with ID and timestamps"""
    id: int
    impact_card_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ReasoningStepCreate(ReasoningStepBase):
    """Schema for creating new reasoning steps"""
    impact_card_id: int

class SourceCredibilityAnalysisBase(BaseModel):
    """Base schema for source credibility analysis"""
    source_url: str = Field(description="URL of the source")
    source_title: Optional[str] = Field(None, description="Title of the source")
    source_type: str = Field(description="Type of source (news, search, research)")
    tier_level: str = Field(description="Credibility tier (tier1, tier2, tier3)")
    credibility_score: float = Field(ge=0.0, le=1.0, description="Overall credibility score")
    authority_score: float = Field(ge=0.0, le=1.0, description="Domain authority score")
    recency_score: float = Field(ge=0.0, le=1.0, description="Recency score")
    relevance_score: float = Field(ge=0.0, le=1.0, description="Relevance score")
    validation_method: str = Field(description="How credibility was determined")
    quality_flags: List[str] = Field(default_factory=list, description="Quality indicators")
    warning_flags: List[str] = Field(default_factory=list, description="Warning indicators")
    conflicts_with: List[int] = Field(default_factory=list, description="Conflicting source IDs")
    conflict_severity: str = Field(default="none", description="Severity of conflicts")

class SourceCredibilityAnalysis(SourceCredibilityAnalysisBase):
    """Complete source credibility analysis with ID and timestamps"""
    id: int
    impact_card_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class SourceCredibilityAnalysisCreate(SourceCredibilityAnalysisBase):
    """Schema for creating new source credibility analyses"""
    impact_card_id: int

class UncertaintyDetectionBase(BaseModel):
    """Base schema for uncertainty detection"""
    uncertainty_type: str = Field(description="Type of uncertainty detected")
    uncertainty_level: str = Field(description="Level of uncertainty (low, medium, high, critical)")
    confidence_threshold: float = Field(ge=0.0, le=1.0, description="Threshold that triggered detection")
    affected_components: List[str] = Field(default_factory=list, description="Affected analysis components")
    uncertainty_description: str = Field(description="Human-readable description")
    human_validation_required: bool = Field(default=False, description="Whether human validation is needed")
    recommended_actions: List[str] = Field(default_factory=list, description="Recommended actions")
    validation_priority: str = Field(default="medium", description="Priority for validation")
    is_resolved: bool = Field(default=False, description="Whether uncertainty is resolved")
    resolution_method: Optional[str] = Field(None, description="How uncertainty was resolved")
    resolved_by: Optional[str] = Field(None, description="Who resolved the uncertainty")
    resolved_at: Optional[datetime] = Field(None, description="When uncertainty was resolved")

class UncertaintyDetection(UncertaintyDetectionBase):
    """Complete uncertainty detection with ID and timestamps"""
    id: int
    impact_card_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class UncertaintyDetectionCreate(UncertaintyDetectionBase):
    """Schema for creating new uncertainty detections"""
    impact_card_id: int

class EnhancedExplainability(BaseModel):
    """Enhanced explainability with detailed reasoning chains"""
    reasoning: Optional[str] = Field(None, description="Overall reasoning summary")
    impact_areas: List[Dict[str, Any]] = Field(default_factory=list, description="Impact areas analyzed")
    key_insights: List[str] = Field(default_factory=list, description="Key insights discovered")
    source_summary: Optional[Dict[str, Any]] = Field(None, description="Source quality summary")
    
    # Enhanced explainability components
    reasoning_chain: List[ReasoningStep] = Field(default_factory=list, description="Detailed reasoning steps")
    source_analyses: List[SourceCredibilityAnalysis] = Field(default_factory=list, description="Source credibility analyses")
    uncertainty_detections: List[UncertaintyDetection] = Field(default_factory=list, description="Detected uncertainties")
    
    # Summary metrics
    overall_confidence: float = Field(ge=0.0, le=1.0, description="Overall confidence in analysis")
    source_quality_score: float = Field(ge=0.0, le=1.0, description="Overall source quality")
    uncertainty_level: str = Field(default="low", description="Overall uncertainty level")
    human_validation_recommended: bool = Field(default=False, description="Whether human validation is recommended")

class ExplainabilityVisualization(BaseModel):
    """Data structure for explainability visualization"""
    factor_weights: Dict[str, float] = Field(default_factory=dict, description="Factor importance weights")
    contribution_breakdown: Dict[str, float] = Field(default_factory=dict, description="Risk score contributions")
    source_quality_breakdown: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Source quality by tier")
    uncertainty_summary: Dict[str, int] = Field(default_factory=dict, description="Uncertainty counts by type")
    confidence_intervals: Dict[str, Dict[str, float]] = Field(default_factory=dict, description="Confidence intervals")
    
class HumanValidationRequest(BaseModel):
    """Request for human validation of uncertain analysis"""
    impact_card_id: int
    uncertainty_ids: List[int] = Field(description="IDs of uncertainties to validate")
    validation_priority: str = Field(default="medium", description="Priority level")
    requested_by: str = Field(description="User requesting validation")
    validation_notes: Optional[str] = Field(None, description="Additional notes for validator")

class HumanValidationResponse(BaseModel):
    """Response from human validation"""
    uncertainty_id: int
    is_valid: bool = Field(description="Whether the analysis is valid")
    corrected_values: Optional[Dict[str, Any]] = Field(None, description="Corrected values if invalid")
    validation_notes: str = Field(description="Validation notes")
    validated_by: str = Field(description="Who performed the validation")
    validated_at: datetime = Field(description="When validation was performed")