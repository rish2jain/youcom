"""
Tests for the Explainability API endpoints
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from unittest.mock import patch, AsyncMock

from app.models.impact_card import ImpactCard
from app.models.explainability import ReasoningStep, SourceCredibilityAnalysis, UncertaintyDetection


class TestExplainabilityAPI:
    """Test cases for Explainability API endpoints"""

    @pytest.mark.asyncio
    async def test_generate_explainability_success(
        self, 
        client: AsyncClient, 
        db_session: AsyncSession,
        impact_card: ImpactCard
    ):
        """Test successful explainability generation"""
        
        with patch('app.api.explainability.ExplainabilityEngine') as mock_engine_class:
            # Mock the engine methods
            mock_engine = AsyncMock()
            mock_engine_class.return_value = mock_engine
            
            mock_engine.generate_reasoning_chain.return_value = [
                AsyncMock(id=1, step_type="source_assessment"),
                AsyncMock(id=2, step_type="impact_analysis")
            ]
            mock_engine.analyze_source_quality.return_value = [
                AsyncMock(id=1, credibility_score=0.8)
            ]
            mock_engine.detect_uncertainty.return_value = [
                AsyncMock(id=1, human_validation_required=True)
            ]
            
            response = await client.post(f"/api/v1/explainability/generate/{impact_card.id}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Explainability generated successfully"
            assert data["impact_card_id"] == impact_card.id
            assert data["reasoning_steps_count"] == 2
            assert data["source_analyses_count"] == 1
            assert data["uncertainty_detections_count"] == 1
            assert data["human_validation_recommended"] is True

    @pytest.mark.asyncio
    async def test_generate_explainability_not_found(
        self, 
        client: AsyncClient, 
        db_session: AsyncSession
    ):
        """Test explainability generation for non-existent impact card"""
        
        response = await client.post("/api/v1/explainability/generate/99999")
        
        assert response.status_code == 404
        assert "Impact Card not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_generate_explainability_error(
        self, 
        client: AsyncClient, 
        db_session: AsyncSession,
        impact_card: ImpactCard
    ):
        """Test explainability generation with service error"""
        
        with patch('app.api.explainability.ExplainabilityEngine') as mock_engine_class:
            mock_engine = AsyncMock()
            mock_engine_class.return_value = mock_engine
            mock_engine.generate_reasoning_chain.side_effect = Exception("Service error")
            
            response = await client.post(f"/api/v1/explainability/generate/{impact_card.id}")
            
            assert response.status_code == 500
            assert "Failed to generate explainability" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_explainability_success(
        self, 
        client: AsyncClient, 
        db_session: AsyncSession,
        impact_card: ImpactCard
    ):
        """Test successful explainability retrieval"""
        
        # Create test data
        reasoning_step = ReasoningStep(
            impact_card_id=impact_card.id,
            step_order=1,
            step_type="source_assessment",
            step_name="Test Step",
            factor_name="Test Factor",
            factor_weight=0.5,
            factor_contribution=25.0,
            evidence_sources=[],
            reasoning_text="Test reasoning",
            confidence_level=0.8,
            uncertainty_flags=[],
            conflicting_evidence=[]
        )
        db_session.add(reasoning_step)
        
        source_analysis = SourceCredibilityAnalysis(
            impact_card_id=impact_card.id,
            source_url="https://example.com",
            source_title="Test Source",
            source_type="news",
            tier_level="tier1",
            credibility_score=0.9,
            authority_score=0.9,
            recency_score=0.8,
            relevance_score=0.85,
            validation_method="test method",
            quality_flags=["high_quality"],
            warning_flags=[],
            conflicts_with=[],
            conflict_severity="none"
        )
        db_session.add(source_analysis)
        
        uncertainty_detection = UncertaintyDetection(
            impact_card_id=impact_card.id,
            uncertainty_type="test_uncertainty",
            uncertainty_level="medium",
            confidence_threshold=0.6,
            affected_components=["test_component"],
            uncertainty_description="Test uncertainty",
            human_validation_required=False,
            recommended_actions=["test_action"],
            validation_priority="medium",
            is_resolved=False
        )
        db_session.add(uncertainty_detection)
        
        await db_session.commit()
        
        response = await client.get(f"/api/v1/explainability/{impact_card.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["reasoning_chain"]) == 1
        assert len(data["source_analyses"]) == 1
        assert len(data["uncertainty_detections"]) == 1
        assert 0.0 <= data["overall_confidence"] <= 1.0
        assert 0.0 <= data["source_quality_score"] <= 1.0

    @pytest.mark.asyncio
    async def test_get_explainability_not_found(
        self, 
        client: AsyncClient, 
        db_session: AsyncSession
    ):
        """Test explainability retrieval for non-existent impact card"""
        
        response = await client.get("/api/v1/explainability/99999")
        
        assert response.status_code == 404
        assert "Impact Card not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_reasoning_steps(
        self, 
        client: AsyncClient, 
        db_session: AsyncSession,
        impact_card: ImpactCard
    ):
        """Test reasoning steps retrieval"""
        
        # Create test reasoning steps
        step1 = ReasoningStep(
            impact_card_id=impact_card.id,
            step_order=1,
            step_type="source_assessment",
            step_name="Step 1",
            factor_name="Factor 1",
            factor_weight=0.3,
            factor_contribution=15.0,
            evidence_sources=[],
            reasoning_text="Step 1 reasoning",
            confidence_level=0.8,
            uncertainty_flags=[],
            conflicting_evidence=[]
        )
        
        step2 = ReasoningStep(
            impact_card_id=impact_card.id,
            step_order=2,
            step_type="impact_analysis",
            step_name="Step 2",
            factor_name="Factor 2",
            factor_weight=0.4,
            factor_contribution=20.0,
            evidence_sources=[],
            reasoning_text="Step 2 reasoning",
            confidence_level=0.7,
            uncertainty_flags=[],
            conflicting_evidence=[]
        )
        
        db_session.add_all([step1, step2])
        await db_session.commit()
        
        response = await client.get(f"/api/v1/explainability/{impact_card.id}/reasoning-steps")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["step_order"] == 1  # Should be ordered by step_order
        assert data[1]["step_order"] == 2

    @pytest.mark.asyncio
    async def test_get_source_analyses(
        self, 
        client: AsyncClient, 
        db_session: AsyncSession,
        impact_card: ImpactCard
    ):
        """Test source analyses retrieval"""
        
        # Create test source analyses
        analysis1 = SourceCredibilityAnalysis(
            impact_card_id=impact_card.id,
            source_url="https://high-credibility.com",
            source_title="High Credibility Source",
            source_type="news",
            tier_level="tier1",
            credibility_score=0.95,
            authority_score=0.9,
            recency_score=0.8,
            relevance_score=0.85,
            validation_method="tier analysis",
            quality_flags=["authoritative"],
            warning_flags=[],
            conflicts_with=[],
            conflict_severity="none"
        )
        
        analysis2 = SourceCredibilityAnalysis(
            impact_card_id=impact_card.id,
            source_url="https://low-credibility.com",
            source_title="Low Credibility Source",
            source_type="search",
            tier_level="tier3",
            credibility_score=0.3,
            authority_score=0.2,
            recency_score=0.6,
            relevance_score=0.4,
            validation_method="tier analysis",
            quality_flags=[],
            warning_flags=["low_credibility"],
            conflicts_with=[],
            conflict_severity="none"
        )
        
        db_session.add_all([analysis1, analysis2])
        await db_session.commit()
        
        response = await client.get(f"/api/v1/explainability/{impact_card.id}/source-analyses")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        # Should be ordered by credibility_score desc
        assert data[0]["credibility_score"] >= data[1]["credibility_score"]

    @pytest.mark.asyncio
    async def test_get_uncertainty_detections(
        self, 
        client: AsyncClient, 
        db_session: AsyncSession,
        impact_card: ImpactCard
    ):
        """Test uncertainty detections retrieval"""
        
        # Create test uncertainty detections
        detection1 = UncertaintyDetection(
            impact_card_id=impact_card.id,
            uncertainty_type="critical_uncertainty",
            uncertainty_level="critical",
            confidence_threshold=0.3,
            affected_components=["risk_score"],
            uncertainty_description="Critical uncertainty detected",
            human_validation_required=True,
            recommended_actions=["immediate_review"],
            validation_priority="urgent",
            is_resolved=False
        )
        
        detection2 = UncertaintyDetection(
            impact_card_id=impact_card.id,
            uncertainty_type="medium_uncertainty",
            uncertainty_level="medium",
            confidence_threshold=0.6,
            affected_components=["source_quality"],
            uncertainty_description="Medium uncertainty detected",
            human_validation_required=False,
            recommended_actions=["monitor"],
            validation_priority="medium",
            is_resolved=False
        )
        
        db_session.add_all([detection1, detection2])
        await db_session.commit()
        
        response = await client.get(f"/api/v1/explainability/{impact_card.id}/uncertainty-detections")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        # Should be ordered by priority and level
        assert data[0]["validation_priority"] == "urgent"

    @pytest.mark.asyncio
    async def test_get_visualization_data(
        self, 
        client: AsyncClient, 
        db_session: AsyncSession,
        impact_card: ImpactCard
    ):
        """Test visualization data retrieval"""
        
        # Create test data
        reasoning_step = ReasoningStep(
            impact_card_id=impact_card.id,
            step_order=1,
            step_type="impact_analysis",
            step_name="Test Step",
            factor_name="Test Factor",
            factor_weight=0.5,
            factor_contribution=25.0,
            evidence_sources=[],
            reasoning_text="Test reasoning",
            confidence_level=0.8,
            uncertainty_flags=[],
            conflicting_evidence=[]
        )
        db_session.add(reasoning_step)
        
        source_analysis = SourceCredibilityAnalysis(
            impact_card_id=impact_card.id,
            source_url="https://example.com",
            source_title="Test Source",
            source_type="news",
            tier_level="tier1",
            credibility_score=0.9,
            authority_score=0.9,
            recency_score=0.8,
            relevance_score=0.85,
            validation_method="test method",
            quality_flags=["high_quality"],
            warning_flags=[],
            conflicts_with=[],
            conflict_severity="none"
        )
        db_session.add(source_analysis)
        
        await db_session.commit()
        
        response = await client.get(f"/api/v1/explainability/{impact_card.id}/visualization")
        
        assert response.status_code == 200
        data = response.json()
        assert "factor_weights" in data
        assert "contribution_breakdown" in data
        assert "source_quality_breakdown" in data
        assert "uncertainty_summary" in data
        assert "confidence_intervals" in data

    @pytest.mark.asyncio
    async def test_request_human_validation(
        self, 
        client: AsyncClient, 
        db_session: AsyncSession,
        impact_card: ImpactCard
    ):
        """Test human validation request"""
        
        # Create test uncertainty detection
        detection = UncertaintyDetection(
            impact_card_id=impact_card.id,
            uncertainty_type="test_uncertainty",
            uncertainty_level="high",
            confidence_threshold=0.5,
            affected_components=["test_component"],
            uncertainty_description="Test uncertainty",
            human_validation_required=True,
            recommended_actions=["review"],
            validation_priority="high",
            is_resolved=False
        )
        db_session.add(detection)
        await db_session.commit()
        await db_session.refresh(detection)
        
        request_data = {
            "impact_card_id": impact_card.id,
            "uncertainty_ids": [detection.id],
            "validation_priority": "high",
            "requested_by": "test_user",
            "validation_notes": "Please review this uncertainty"
        }
        
        response = await client.post(
            f"/api/v1/explainability/{impact_card.id}/validate",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Human validation request submitted successfully"
        assert data["impact_card_id"] == impact_card.id
        assert data["uncertainty_ids"] == [detection.id]
        assert data["validation_priority"] == "high"

    @pytest.mark.asyncio
    async def test_request_validation_invalid_uncertainty(
        self, 
        client: AsyncClient, 
        db_session: AsyncSession,
        impact_card: ImpactCard
    ):
        """Test validation request with invalid uncertainty ID"""
        
        request_data = {
            "impact_card_id": impact_card.id,
            "uncertainty_ids": [99999],  # Non-existent ID
            "validation_priority": "high",
            "requested_by": "test_user"
        }
        
        response = await client.post(
            f"/api/v1/explainability/{impact_card.id}/validate",
            json=request_data
        )
        
        assert response.status_code == 404
        assert "Uncertainty detection 99999 not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_submit_human_validation(
        self, 
        client: AsyncClient, 
        db_session: AsyncSession,
        impact_card: ImpactCard
    ):
        """Test human validation submission"""
        
        # Create test uncertainty detection
        detection = UncertaintyDetection(
            impact_card_id=impact_card.id,
            uncertainty_type="test_uncertainty",
            uncertainty_level="high",
            confidence_threshold=0.5,
            affected_components=["test_component"],
            uncertainty_description="Test uncertainty",
            human_validation_required=True,
            recommended_actions=["review"],
            validation_priority="high",
            is_resolved=False
        )
        db_session.add(detection)
        await db_session.commit()
        await db_session.refresh(detection)
        
        validation_data = {
            "uncertainty_id": detection.id,
            "is_valid": True,
            "corrected_values": {"test_field": "corrected_value"},
            "validation_notes": "Validation completed successfully",
            "validated_by": "expert_user",
            "validated_at": "2025-10-31T12:00:00Z"
        }
        
        response = await client.post(
            f"/api/v1/explainability/validate/{detection.id}",
            json=validation_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Human validation submitted successfully"
        assert data["uncertainty_id"] == detection.id
        assert data["is_valid"] is True
        assert data["resolution_status"] == "resolved"
        
        # Verify database update
        await db_session.refresh(detection)
        assert detection.is_resolved is True
        assert detection.resolution_method == "human_validation"
        assert detection.resolved_by == "expert_user"

    @pytest.mark.asyncio
    async def test_submit_validation_not_found(
        self, 
        client: AsyncClient, 
        db_session: AsyncSession
    ):
        """Test validation submission for non-existent uncertainty"""
        
        validation_data = {
            "uncertainty_id": 99999,
            "is_valid": True,
            "validation_notes": "Test validation",
            "validated_by": "expert_user",
            "validated_at": "2025-10-31T12:00:00Z"
        }
        
        response = await client.post(
            "/api/v1/explainability/validate/99999",
            json=validation_data
        )
        
        assert response.status_code == 404
        assert "Uncertainty detection not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_api_error_handling(
        self, 
        client: AsyncClient, 
        db_session: AsyncSession,
        impact_card: ImpactCard
    ):
        """Test API error handling"""
        
        with patch('app.api.explainability.ExplainabilityEngine') as mock_engine_class:
            mock_engine = AsyncMock()
            mock_engine_class.return_value = mock_engine
            mock_engine.build_enhanced_explainability.side_effect = Exception("Database error")
            
            response = await client.get(f"/api/v1/explainability/{impact_card.id}")
            
            assert response.status_code == 500
            assert "Failed to retrieve explainability" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_validation_request_wrong_impact_card(
        self, 
        client: AsyncClient, 
        db_session: AsyncSession,
        impact_card: ImpactCard
    ):
        """Test validation request with uncertainty from different impact card"""
        
        # Create another impact card
        other_impact_card = ImpactCard(
            competitor_name="Other Competitor",
            risk_score=50,
            risk_level="medium",
            confidence_score=70,
            impact_areas=[],
            key_insights=[],
            recommended_actions=[],
            total_sources=0,
            source_breakdown={},
            api_usage={},
            raw_data={}
        )
        db_session.add(other_impact_card)
        await db_session.commit()
        await db_session.refresh(other_impact_card)
        
        # Create uncertainty for the other impact card
        detection = UncertaintyDetection(
            impact_card_id=other_impact_card.id,  # Different impact card
            uncertainty_type="test_uncertainty",
            uncertainty_level="high",
            confidence_threshold=0.5,
            affected_components=["test_component"],
            uncertainty_description="Test uncertainty",
            human_validation_required=True,
            recommended_actions=["review"],
            validation_priority="high",
            is_resolved=False
        )
        db_session.add(detection)
        await db_session.commit()
        await db_session.refresh(detection)
        
        request_data = {
            "impact_card_id": impact_card.id,  # Original impact card
            "uncertainty_ids": [detection.id],  # But uncertainty from other card
            "validation_priority": "high",
            "requested_by": "test_user"
        }
        
        response = await client.post(
            f"/api/v1/explainability/{impact_card.id}/validate",
            json=request_data
        )
        
        assert response.status_code == 400
        assert "does not belong to impact card" in response.json()["detail"]