"""Base classes for demo scenarios."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict

from src.langgraph_orchestrator import IncidentStateModel
from src.models.incident import Incident


@dataclass
class ValidationResult:
    """Result of scenario validation."""

    is_valid: bool
    message: str
    details: Dict[str, Any] = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_valid": self.is_valid,
            "message": self.message,
            "details": self.details,
        }


class DemoScenario(ABC):
    """
    Abstract base class for demo scenarios.

    Each scenario defines:
    - How to create an incident
    - What context to provide
    - How to validate the results
    """

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def create_incident(self) -> Incident:
        """Create an incident for this scenario."""
        pass

    @abstractmethod
    def get_context(self) -> Dict[str, Any]:
        """Get the context for incident processing."""
        pass

    def validate_result(self, result: IncidentStateModel) -> ValidationResult:
        """
        Validate the result of scenario execution.

        Default implementation checks basic requirements.
        Override for scenario-specific validation.
        """
        if not result.detection:
            return ValidationResult(
                is_valid=False,
                message="Detection phase did not complete",
            )

        if not result.consensus:
            return ValidationResult(
                is_valid=False,
                message="Consensus phase did not complete",
            )

        if not result.resolution:
            return ValidationResult(
                is_valid=False,
                message="Resolution phase did not complete",
            )

        if not result.communication:
            return ValidationResult(
                is_valid=False,
                message="Communication phase did not complete",
            )

        return ValidationResult(
            is_valid=True,
            message="All phases completed successfully",
            details={
                "timeline_events": len(result.timeline),
                "consensus_confidence": result.consensus.final_confidence,
            },
        )

    def __repr__(self) -> str:
        return f"DemoScenario(name='{self.name}', description='{self.description}')"
