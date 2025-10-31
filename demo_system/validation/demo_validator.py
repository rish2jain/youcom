"""Validation utilities for demo execution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from src.langgraph_orchestrator import IncidentStateModel
from src.utils.logging import get_logger


logger = get_logger("demo.validator")


@dataclass
class ValidationCheck:
    """A single validation check."""

    name: str
    passed: bool
    message: str
    severity: str = "error"  # error, warning, info


class DemoValidator:
    """
    Validates demo execution results.

    Performs comprehensive checks on:
    - Phase completion
    - Agent participation
    - Consensus quality
    - Timeline consistency
    - Performance metrics
    """

    def __init__(self):
        self.checks: List[ValidationCheck] = []

    def validate(self, result: IncidentStateModel) -> List[ValidationCheck]:
        """
        Run all validation checks on a result.

        Args:
            result: The incident state result to validate

        Returns:
            List of validation checks with pass/fail status
        """
        self.checks = []

        # Phase completion checks
        self._check_detection(result)
        self._check_diagnosis(result)
        self._check_prediction(result)
        self._check_consensus(result)
        self._check_resolution(result)
        self._check_communication(result)

        # Cross-phase checks
        self._check_timeline_consistency(result)
        self._check_agent_coordination(result)

        return self.checks

    def _check_detection(self, result: IncidentStateModel) -> None:
        """Validate detection phase."""
        if not result.detection:
            self.checks.append(
                ValidationCheck(
                    name="detection_phase",
                    passed=False,
                    message="Detection phase did not complete",
                    severity="error",
                )
            )
            return

        rec = result.detection.primary_recommendation
        if not rec:
            self.checks.append(
                ValidationCheck(
                    name="detection_recommendation",
                    passed=False,
                    message="Detection did not produce recommendation",
                    severity="error",
                )
            )
        elif rec.confidence < 0.5:
            self.checks.append(
                ValidationCheck(
                    name="detection_confidence",
                    passed=False,
                    message=f"Detection confidence too low: {rec.confidence}",
                    severity="warning",
                )
            )
        else:
            self.checks.append(
                ValidationCheck(
                    name="detection_phase",
                    passed=True,
                    message=f"Detection completed with confidence {rec.confidence:.2f}",
                    severity="info",
                )
            )

    def _check_diagnosis(self, result: IncidentStateModel) -> None:
        """Validate diagnosis phase."""
        if not result.diagnosis:
            self.checks.append(
                ValidationCheck(
                    name="diagnosis_phase",
                    passed=False,
                    message="Diagnosis phase did not complete",
                    severity="error",
                )
            )
            return

        self.checks.append(
            ValidationCheck(
                name="diagnosis_phase",
                passed=True,
                message="Diagnosis phase completed",
                severity="info",
            )
        )

    def _check_prediction(self, result: IncidentStateModel) -> None:
        """Validate prediction phase."""
        if not result.prediction:
            self.checks.append(
                ValidationCheck(
                    name="prediction_phase",
                    passed=False,
                    message="Prediction phase did not complete",
                    severity="error",
                )
            )
            return

        rec = result.prediction.primary_recommendation
        if rec and "projected_cost" in rec.parameters:
            cost = rec.parameters["projected_cost"]
            self.checks.append(
                ValidationCheck(
                    name="prediction_phase",
                    passed=True,
                    message=f"Prediction completed with projected cost ${cost:.2f}",
                    severity="info",
                )
            )
        else:
            self.checks.append(
                ValidationCheck(
                    name="prediction_cost",
                    passed=False,
                    message="Prediction did not calculate cost",
                    severity="warning",
                )
            )

    def _check_consensus(self, result: IncidentStateModel) -> None:
        """Validate consensus phase."""
        if not result.consensus:
            self.checks.append(
                ValidationCheck(
                    name="consensus_phase",
                    passed=False,
                    message="Consensus was not reached",
                    severity="error",
                )
            )
            return

        confidence = result.consensus.final_confidence
        if confidence < 0.5:
            self.checks.append(
                ValidationCheck(
                    name="consensus_confidence",
                    passed=False,
                    message=f"Consensus confidence too low: {confidence:.2f}",
                    severity="warning",
                )
            )
        else:
            self.checks.append(
                ValidationCheck(
                    name="consensus_phase",
                    passed=True,
                    message=f"Consensus reached with confidence {confidence:.2f}",
                    severity="info",
                )
            )

    def _check_resolution(self, result: IncidentStateModel) -> None:
        """Validate resolution phase."""
        if not result.resolution:
            self.checks.append(
                ValidationCheck(
                    name="resolution_phase",
                    passed=False,
                    message="Resolution phase did not complete",
                    severity="error",
                )
            )
            return

        self.checks.append(
            ValidationCheck(
                name="resolution_phase",
                passed=True,
                message="Resolution phase completed",
                severity="info",
            )
        )

    def _check_communication(self, result: IncidentStateModel) -> None:
        """Validate communication phase."""
        if not result.communication:
            self.checks.append(
                ValidationCheck(
                    name="communication_phase",
                    passed=False,
                    message="Communication phase did not complete",
                    severity="error",
                )
            )
            return

        rec = result.communication.primary_recommendation
        if rec and "summary" in rec.parameters:
            self.checks.append(
                ValidationCheck(
                    name="communication_phase",
                    passed=True,
                    message="Communication phase completed with summary",
                    severity="info",
                )
            )
        else:
            self.checks.append(
                ValidationCheck(
                    name="communication_summary",
                    passed=False,
                    message="Communication did not generate summary",
                    severity="warning",
                )
            )

    def _check_timeline_consistency(self, result: IncidentStateModel) -> None:
        """Validate timeline consistency."""
        if not result.timeline:
            self.checks.append(
                ValidationCheck(
                    name="timeline_consistency",
                    passed=False,
                    message="Timeline is empty",
                    severity="error",
                )
            )
            return

        expected_phases = ["detection", "diagnosis", "prediction", "consensus", "resolution", "communication"]
        timeline_phases = [event.phase for event in result.timeline]

        missing_phases = [phase for phase in expected_phases if phase not in timeline_phases]
        if missing_phases:
            self.checks.append(
                ValidationCheck(
                    name="timeline_consistency",
                    passed=False,
                    message=f"Missing phases in timeline: {', '.join(missing_phases)}",
                    severity="warning",
                )
            )
        else:
            self.checks.append(
                ValidationCheck(
                    name="timeline_consistency",
                    passed=True,
                    message=f"Timeline complete with {len(result.timeline)} events",
                    severity="info",
                )
            )

    def _check_agent_coordination(self, result: IncidentStateModel) -> None:
        """Validate agent coordination."""
        agents_participated = []
        if result.detection:
            agents_participated.append("detection")
        if result.diagnosis:
            agents_participated.append("diagnosis")
        if result.prediction:
            agents_participated.append("prediction")
        if result.resolution:
            agents_participated.append("resolution")
        if result.communication:
            agents_participated.append("communication")

        if len(agents_participated) < 5:
            self.checks.append(
                ValidationCheck(
                    name="agent_coordination",
                    passed=False,
                    message=f"Only {len(agents_participated)}/5 agents participated",
                    severity="warning",
                )
            )
        else:
            self.checks.append(
                ValidationCheck(
                    name="agent_coordination",
                    passed=True,
                    message="All agents participated successfully",
                    severity="info",
                )
            )

    def generate_report(self) -> str:
        """Generate a human-readable validation report."""
        passed = sum(1 for check in self.checks if check.passed)
        total = len(self.checks)

        lines = [
            "=" * 60,
            "DEMO VALIDATION REPORT",
            "=" * 60,
            f"Checks Passed: {passed}/{total}",
            "",
        ]

        for check in self.checks:
            status = "✓" if check.passed else "✗"
            severity = check.severity.upper()
            lines.append(f"{status} [{severity}] {check.name}: {check.message}")

        return "\n".join(lines)
