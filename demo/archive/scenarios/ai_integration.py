"""AI services integration demonstration scenario."""

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


class AIIntegrationScenario(DemoScenario):
    """
    AWS AI services integration demonstration.

    This scenario highlights:
    - Multi-agent LangGraph orchestration
    - AWS Bedrock integration for intelligent decision-making
    - Byzantine fault-tolerant consensus
    - Real-time agent coordination
    - Adaptive response based on incident characteristics
    """

    def __init__(self):
        super().__init__(
            name="ai_integration",
            description="Complex incident requiring multi-agent AI coordination",
        )

    def create_incident(self) -> Incident:
        """Create an incident that showcases AI capabilities."""
        return Incident(
            title="Distributed System Cascade Failure",
            description=(
                "Multiple microservices experiencing cascading failures. "
                "Root cause unclear. Memory leak suspected in user-service. "
                "Database connection pool exhaustion detected. "
                "Load balancer health checks failing intermittently."
            ),
            severity=IncidentSeverity.HIGH,
            status=IncidentStatus.DETECTED,
            business_impact=BusinessImpact(
                service_tier=ServiceTier.TIER_1,
                affected_users=15000,
                revenue_impact_per_minute=800.0,
            ),
            metadata=IncidentMetadata(
                source_system="distributed-tracing",
                tags=["microservices", "cascade-failure", "complex", "memory-leak"],
                related_incidents=["INC-2024-1015", "INC-2024-1022"],
            ),
        )

    def get_context(self) -> Dict[str, Any]:
        """Get context showcasing AI integration."""
        return {
            "telemetry_sources": [
                "cloudwatch",
                "x-ray-traces",
                "prometheus",
                "jaeger",
            ],
            "log_sources": [
                "user-service",
                "order-service",
                "payment-service",
                "database",
            ],
            "alert_count": 23,
            "distributed_trace_data": {
                "trace_ids": ["abc123", "def456", "ghi789"],
                "error_rate_increase": 0.45,
                "latency_p99_ms": 8500,
            },
            "anomaly_detection": {
                "memory_usage_anomaly": True,
                "connection_pool_anomaly": True,
                "cpu_anomaly": False,
            },
            "related_incidents": [
                {
                    "id": "INC-2024-1015",
                    "resolution": "Increased connection pool size",
                    "success": True,
                },
                {
                    "id": "INC-2024-1022",
                    "resolution": "Memory leak patch deployed",
                    "success": True,
                },
            ],
            "ai_features_enabled": {
                "anomaly_detection": True,
                "root_cause_analysis": True,
                "predictive_scaling": True,
                "automated_remediation": False,  # Requires approval
            },
        }

    def validate_result(self, result: IncidentStateModel) -> ValidationResult:
        """Validate AI integration scenario."""
        base_validation = super().validate_result(result)
        if not base_validation.is_valid:
            return base_validation

        # Verify all agents participated
        required_agents = ["detection", "diagnosis", "prediction", "resolution", "communication"]
        for agent_name in required_agents:
            agent_result = getattr(result, agent_name, None)
            if not agent_result:
                return ValidationResult(
                    is_valid=False,
                    message=f"Agent {agent_name} did not participate",
                )

        # Verify diagnosis agent identified issues
        if not result.diagnosis:
            return ValidationResult(
                is_valid=False,
                message="Diagnosis phase did not complete",
            )

        diagnosis_rec = result.diagnosis.primary_recommendation
        if not diagnosis_rec:
            return ValidationResult(
                is_valid=False,
                message="No diagnosis recommendation generated",
            )

        # Verify consensus was reached with multiple agent inputs
        if not result.consensus:
            return ValidationResult(
                is_valid=False,
                message="Consensus was not achieved",
            )

        # Check consensus method used
        consensus_method = result.consensus.consensus_method
        if consensus_method not in {"pbft", "weighted_fallback"}:
            return ValidationResult(
                is_valid=False,
                message=f"Unexpected consensus method: {consensus_method}",
            )

        # Verify timeline shows multi-agent coordination
        if len(result.timeline) < 6:  # Expect events from all phases
            return ValidationResult(
                is_valid=False,
                message=f"Timeline too short: {len(result.timeline)} events",
            )

        # Verify communication includes all necessary information
        if not result.communication:
            return ValidationResult(
                is_valid=False,
                message="Communication phase did not complete",
            )

        comm_rec = result.communication.primary_recommendation
        if not comm_rec or "summary" not in comm_rec.parameters:
            return ValidationResult(
                is_valid=False,
                message="Communication summary not generated",
            )

        return ValidationResult(
            is_valid=True,
            message="AI integration scenario validated successfully",
            details={
                "agents_participated": required_agents,
                "consensus_method": consensus_method,
                "consensus_confidence": result.consensus.final_confidence,
                "timeline_events": len(result.timeline),
                "diagnosis_action": diagnosis_rec.action_type.value,
                "communication_channels": comm_rec.parameters.get("channels", []),
            },
        )
