"""Business impact demonstration scenario."""

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


class BusinessImpactScenario(DemoScenario):
    """
    Business impact calculation and ROI demonstration.

    This scenario showcases:
    - Business impact assessment
    - Cost per minute calculations
    - Projected downtime and revenue loss
    - ROI metrics for autonomous response
    """

    def __init__(self):
        super().__init__(
            name="business_impact",
            description="High-impact incident with significant revenue implications",
        )

    def create_incident(self) -> Incident:
        """Create an incident with significant business impact."""
        return Incident(
            title="E-commerce Checkout Service Degradation",
            description=(
                "Checkout service experiencing latency spikes and intermittent failures. "
                "Conversion rate dropped by 35%. Payment processing delays reported."
            ),
            severity=IncidentSeverity.HIGH,
            status=IncidentStatus.DETECTED,
            business_impact=BusinessImpact(
                service_tier=ServiceTier.TIER_1,
                affected_users=25000,
                revenue_impact_per_minute=2500.0,  # $2,500/minute
                sla_breach_penalty=50000.0,  # $50k penalty if SLA breached
            ),
            metadata=IncidentMetadata(
                source_system="real-user-monitoring",
                tags=["checkout", "revenue-critical", "customer-experience"],
                related_incidents=[],
            ),
        )

    def get_context(self) -> Dict[str, Any]:
        """Get context emphasizing business metrics."""
        return {
            "telemetry_sources": ["datadog", "new-relic", "rum"],
            "log_sources": ["checkout-service", "payment-gateway"],
            "alert_count": 8,
            "business_metrics": {
                "baseline_conversion_rate": 0.045,
                "current_conversion_rate": 0.029,
                "average_order_value": 125.50,
                "hourly_transaction_volume": 1200,
            },
            "sla_status": {
                "current_availability": 0.92,
                "sla_target": 0.995,
                "time_to_breach_minutes": 15,
            },
            "peak_hours": True,
            "black_friday_preparation": False,
        }

    def validate_result(self, result: IncidentStateModel) -> ValidationResult:
        """Validate business impact scenario results."""
        base_validation = super().validate_result(result)
        if not base_validation.is_valid:
            return base_validation

        # Verify prediction agent calculated business impact
        if not result.prediction:
            return ValidationResult(
                is_valid=False,
                message="Prediction phase did not complete",
            )

        prediction_rec = result.prediction.primary_recommendation
        if not prediction_rec:
            return ValidationResult(
                is_valid=False,
                message="No prediction recommendation generated",
            )

        # Check that cost prediction was performed
        if "projected_cost" not in prediction_rec.parameters:
            return ValidationResult(
                is_valid=False,
                message="Cost prediction missing from parameters",
            )

        projected_cost = prediction_rec.parameters.get("projected_cost", 0)
        if projected_cost <= 0:
            return ValidationResult(
                is_valid=False,
                message=f"Invalid projected cost: ${projected_cost}",
            )

        # Verify consensus considered business impact
        if result.consensus.final_confidence < 0.6:
            return ValidationResult(
                is_valid=False,
                message="Consensus confidence too low for business-critical incident",
            )

        return ValidationResult(
            is_valid=True,
            message="Business impact scenario validated successfully",
            details={
                "projected_cost": projected_cost,
                "expected_duration_minutes": prediction_rec.parameters.get("expected_minutes", 0),
                "consensus_confidence": result.consensus.final_confidence,
                "roi_demonstrated": projected_cost > 1000,  # Demonstrates ROI
            },
        )
