"""Base classes for Enterprise CIA demo scenarios.

Adapted from the Incident Commander demo system for competitive intelligence use cases.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional


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


class CIADemoScenario(ABC):
    """
    Abstract base class for Enterprise CIA demo scenarios.

    Each scenario defines:
    - Which competitor/company to analyze
    - What type of intelligence to gather
    - Expected API orchestration pattern
    - How to validate the results
    """

    def __init__(
        self,
        name: str,
        description: str,
        duration_seconds: int = 30,
        expected_apis: Optional[list[str]] = None,
    ):
        self.name = name
        self.description = description
        self.duration_seconds = duration_seconds
        self.expected_apis = expected_apis or ["news", "search", "chat", "ari"]

    @abstractmethod
    def get_scenario_config(self) -> Dict[str, Any]:
        """
        Get the configuration for this scenario.

        Returns:
            Dictionary containing:
                - competitor: Company name to analyze
                - search_terms: List of search terms
                - analysis_focus: What to focus on (e.g., "product launch", "market expansion")
                - expected_insights: List of expected insight types
        """
        pass

    @abstractmethod
    def get_visual_timeline(self) -> list[Dict[str, Any]]:
        """
        Get the visual timeline for video recording.

        Returns:
            List of timeline events with:
                - timestamp: When to show (in seconds)
                - action: What to do (scroll, click, highlight, wait)
                - target: What to interact with
                - narration: What to say/display
        """
        pass

    def validate_result(self, result: Dict[str, Any]) -> ValidationResult:
        """
        Validate the result of scenario execution.

        Args:
            result: Dictionary containing:
                - impact_cards: List of generated impact cards
                - api_calls: Record of API calls made
                - duration: Time taken
                - errors: Any errors encountered

        Returns:
            ValidationResult indicating success/failure
        """
        # Check if all expected APIs were called
        if "api_calls" in result:
            called_apis = set(result["api_calls"].keys())
            expected = set(self.expected_apis)
            missing = expected - called_apis

            if missing:
                return ValidationResult(
                    is_valid=False,
                    message=f"Missing API calls: {', '.join(missing)}",
                    details={"missing_apis": list(missing)},
                )

        # Check if impact cards were generated
        if "impact_cards" not in result or not result["impact_cards"]:
            return ValidationResult(
                is_valid=False,
                message="No impact cards generated",
            )

        # Check for errors
        if result.get("errors"):
            return ValidationResult(
                is_valid=False,
                message=f"Errors encountered: {len(result['errors'])}",
                details={"errors": result["errors"]},
            )

        # Check duration is reasonable
        if "duration" in result:
            if result["duration"] > self.duration_seconds * 2:
                return ValidationResult(
                    is_valid=False,
                    message=f"Took too long: {result['duration']}s (expected ~{self.duration_seconds}s)",
                    details={"duration": result["duration"]},
                )

        return ValidationResult(
            is_valid=True,
            message="Scenario executed successfully",
            details={
                "impact_cards": len(result.get("impact_cards", [])),
                "duration": result.get("duration", 0),
                "apis_called": len(result.get("api_calls", {})),
            },
        )

    def __repr__(self) -> str:
        return f"CIADemoScenario(name='{self.name}', description='{self.description}')"
