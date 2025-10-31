"""Simplified demo controller for Incident Commander presentations.

This module provides a streamlined approach to running incident response
demonstrations, reducing complexity while maintaining core functionality.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional

from src.langgraph_orchestrator import IncidentResponseGraph
from src.models.incident import Incident
from src.utils.logging import get_logger

from demo_system.metrics.real_time_collector import MetricsCollector
from demo_system.scenarios.base import DemoScenario


logger = get_logger("demo.simplified")


class DemoExecutionResult:
    """Results from a demo scenario execution."""

    def __init__(
        self,
        scenario_name: str,
        success: bool,
        duration_seconds: float,
        metrics: Dict[str, any],
        timeline: List[Dict[str, any]],
        error: Optional[str] = None,
    ):
        self.scenario_name = scenario_name
        self.success = success
        self.duration_seconds = duration_seconds
        self.metrics = metrics
        self.timeline = timeline
        self.error = error
        self.timestamp = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, any]:
        """Convert result to dictionary for serialization."""
        return {
            "scenario_name": self.scenario_name,
            "success": self.success,
            "duration_seconds": round(self.duration_seconds, 2),
            "metrics": self.metrics,
            "timeline": self.timeline,
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
        }

    def __str__(self) -> str:
        """Human-readable summary of execution result."""
        status = "✓ SUCCESS" if self.success else "✗ FAILED"
        lines = [
            f"\n{status}: {self.scenario_name}",
            f"Duration: {self.duration_seconds:.2f}s",
            f"Timeline Events: {len(self.timeline)}",
        ]

        if self.metrics:
            lines.append("\nMetrics:")
            for key, value in self.metrics.items():
                if isinstance(value, (int, float)):
                    lines.append(f"  {key}: {value}")
                else:
                    lines.append(f"  {key}: {str(value)[:50]}")

        if self.error:
            lines.append(f"\nError: {self.error}")

        return "\n".join(lines)


class SimplifiedDemoController:
    """
    Simplified demo controller for Incident Commander.

    This controller provides a reliable, easy-to-use interface for running
    demonstration scenarios. It focuses on:
    - Clear scenario execution
    - Real-time metrics collection
    - Automated validation
    - Reliable presentation output
    """

    def __init__(self):
        self.scenarios: Dict[str, DemoScenario] = {}
        self.metrics_collector = MetricsCollector()
        self.graph = IncidentResponseGraph()
        logger.info("SimplifiedDemoController initialized")

    def register_scenario(self, scenario: DemoScenario) -> None:
        """Register a demo scenario."""
        self.scenarios[scenario.name] = scenario
        logger.info(f"Registered scenario: {scenario.name}")

    def list_scenarios(self) -> List[str]:
        """List all available scenario names."""
        return list(self.scenarios.keys())

    async def run_demo(
        self,
        scenario_name: str,
        *,
        collect_metrics: bool = True,
        validate: bool = True,
    ) -> DemoExecutionResult:
        """
        Execute a demo scenario with metrics collection.

        Args:
            scenario_name: Name of the scenario to run
            collect_metrics: Whether to collect real-time metrics
            validate: Whether to validate the results

        Returns:
            DemoExecutionResult with execution details and metrics

        Raises:
            KeyError: If scenario_name is not found
        """
        if scenario_name not in self.scenarios:
            available = ", ".join(self.scenarios.keys())
            raise KeyError(
                f"Scenario '{scenario_name}' not found. Available: {available}"
            )

        scenario = self.scenarios[scenario_name]
        logger.info(f"Starting demo scenario: {scenario_name}")

        start_time = asyncio.get_event_loop().time()

        try:
            # Start metrics collection
            if collect_metrics:
                self.metrics_collector.start_collection(scenario_name)

            # Generate incident for scenario
            incident = scenario.create_incident()
            context = scenario.get_context()

            # Execute the incident through the LangGraph orchestration
            result = await self.graph.run(incident, context=context)

            # Stop metrics collection
            if collect_metrics:
                collected_metrics = self.metrics_collector.stop_collection()
            else:
                collected_metrics = {}

            # Extract timeline
            timeline = [event.model_dump(mode="python") for event in result.timeline]

            # Validate results if requested
            if validate:
                validation_result = scenario.validate_result(result)
                if not validation_result.is_valid:
                    logger.warning(
                        f"Validation failed: {validation_result.message}",
                        extra={"scenario": scenario_name},
                    )
                collected_metrics["validation"] = validation_result.to_dict()

            # Calculate duration
            duration = asyncio.get_event_loop().time() - start_time

            # Create execution result
            execution_result = DemoExecutionResult(
                scenario_name=scenario_name,
                success=True,
                duration_seconds=duration,
                metrics=collected_metrics,
                timeline=timeline,
            )

            logger.info(
                f"Demo scenario completed successfully: {scenario_name}",
                extra={"duration_seconds": duration},
            )

            return execution_result

        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            logger.error(
                f"Demo scenario failed: {scenario_name}",
                extra={"error": str(e), "duration_seconds": duration},
                exc_info=True,
            )

            # Stop metrics collection on error
            if collect_metrics:
                try:
                    collected_metrics = self.metrics_collector.stop_collection()
                except Exception:
                    collected_metrics = {}

            return DemoExecutionResult(
                scenario_name=scenario_name,
                success=False,
                duration_seconds=duration,
                metrics=collected_metrics,
                timeline=[],
                error=str(e),
            )

    async def run_all_scenarios(self) -> List[DemoExecutionResult]:
        """
        Run all registered scenarios in sequence.

        Returns:
            List of DemoExecutionResult for each scenario
        """
        logger.info(f"Running all {len(self.scenarios)} demo scenarios")

        results = []
        for scenario_name in self.scenarios:
            result = await self.run_demo(scenario_name)
            results.append(result)

        success_count = sum(1 for r in results if r.success)
        logger.info(
            f"Completed all scenarios: {success_count}/{len(results)} successful"
        )

        return results

    def generate_report(self, results: List[DemoExecutionResult]) -> str:
        """
        Generate a formatted report from demo results.

        Args:
            results: List of execution results

        Returns:
            Formatted report string
        """
        lines = [
            "=" * 80,
            "INCIDENT COMMANDER - DEMO EXECUTION REPORT",
            "=" * 80,
            f"Generated: {datetime.now(timezone.utc).isoformat()}",
            f"Total Scenarios: {len(results)}",
            f"Successful: {sum(1 for r in results if r.success)}",
            f"Failed: {sum(1 for r in results if not r.success)}",
            "",
        ]

        for result in results:
            lines.append(str(result))
            lines.append("")

        # Summary statistics
        if results:
            avg_duration = sum(r.duration_seconds for r in results) / len(results)
            lines.extend(
                [
                    "=" * 80,
                    "SUMMARY STATISTICS",
                    "=" * 80,
                    f"Average Duration: {avg_duration:.2f}s",
                    f"Total Duration: {sum(r.duration_seconds for r in results):.2f}s",
                ]
            )

        return "\n".join(lines)
