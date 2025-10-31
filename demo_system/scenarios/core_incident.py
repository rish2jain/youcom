"""Core incident response demonstration scenario."""

from __future__ import annotations

from typing import Any, Dict

from src.models.incident import (
    BusinessImpact,
    Incident,
    IncidentMetadata,
    IncidentSeverity,
    IncidentStatus,
    ServiceTier,
)

from demo_system.scenarios.base import DemoScenario, ValidationResult
from src.langgraph_orchestrator import IncidentStateModel


class CoreIncidentScenario(DemoScenario):
    """
    Core incident response scenario.

    Demonstrates the complete incident lifecycle:
    - Detection of a critical service outage
    - Diagnosis of root cause
    - Prediction of business impact
    - Consensus-driven resolution
    - Stakeholder communication
    """

    def __init__(self):
        super().__init__(
            name="core_incident",
            description="Critical service outage requiring immediate response",
        )

    def create_incident(self) -> Incident:
        """Create a critical incident for demonstration."""
        return Incident(
            title="Production API Gateway Critical Outage",
            description=(
                "API Gateway experiencing complete failure with timeout errors. "
                "All customer-facing services impacted. Recent deployment detected."
            ),
            severity=IncidentSeverity.CRITICAL,
            status=IncidentStatus.DETECTED,
            business_impact=BusinessImpact(
                service_tier=ServiceTier.TIER_1,
                affected_users=50000,
                revenue_impact_per_minute=1500.0,
            ),
            metadata=IncidentMetadata(
                source_system="cloudwatch-alarms",
                tags=["api-gateway", "production", "customer-impact"],
                related_incidents=[],
            ),
        )

    def get_context(self) -> Dict[str, Any]:
        """Get context for core incident processing."""
        return {
            "telemetry_sources": [
                "cloudwatch",
                "datadog",
                "x-ray",
                "synthetic-monitors",
            ],
            "log_sources": ["api-gateway", "lambda-functions", "application"],
            "alert_count": 15,
            "deployment_in_progress": False,
            "recent_deployment_time": "2024-10-23T14:30:00Z",
            "affected_regions": ["us-east-1"],
            "customer_complaints": 250,
        }

    def validate_result(self, result: IncidentStateModel) -> ValidationResult:
        """Validate core incident response."""
        base_validation = super().validate_result(result)
        if not base_validation.is_valid:
            return base_validation

        # Check that critical severity was handled appropriately
        if not result.detection:
            return ValidationResult(
                is_valid=False,
                message="Detection phase missing",
            )

        detection_rec = result.detection.primary_recommendation
        if detection_rec and detection_rec.confidence < 0.8:
            return ValidationResult(
                is_valid=False,
                message=f"Detection confidence too low for critical incident: {detection_rec.confidence}",
            )

        # Verify consensus was reached with high confidence
        if result.consensus.final_confidence < 0.7:
            return ValidationResult(
                is_valid=False,
                message=f"Consensus confidence too low: {result.consensus.final_confidence}",
            )

        return ValidationResult(
            is_valid=True,
            message="Core incident response executed successfully",
            details={
                "detection_confidence": detection_rec.confidence if detection_rec else None,
                "consensus_confidence": result.consensus.final_confidence,
                "timeline_phases": len(result.timeline),
            },
        )
