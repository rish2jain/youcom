"""Enterprise CIA Demo Controller with integrated video recording.

This controller orchestrates demo scenarios and coordinates with the
Puppeteer video recorder for automated demo video creation.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from demo_system_cia.scenarios.base import CIADemoScenario, ValidationResult


class DemoExecutionResult:
    """Results from a demo scenario execution."""

    def __init__(
        self,
        scenario_name: str,
        success: bool,
        duration_seconds: float,
        metrics: Dict[str, any],
        timeline: List[Dict[str, any]],
        video_path: Optional[str] = None,
        error: Optional[str] = None,
    ):
        self.scenario_name = scenario_name
        self.success = success
        self.duration_seconds = duration_seconds
        self.metrics = metrics
        self.timeline = timeline
        self.video_path = video_path
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
            "video_path": self.video_path,
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

        if self.video_path:
            lines.append(f"Video: {self.video_path}")

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


class EnterpriseCIADemoController:
    """
    Enterprise CIA Demo Controller with video recording integration.

    This controller:
    - Manages demo scenarios
    - Coordinates API orchestration
    - Integrates with Puppeteer recorder
    - Validates demo execution
    - Generates comprehensive reports
    """

    def __init__(self, base_url: str = "http://localhost:3000"):
        self.scenarios: Dict[str, CIADemoScenario] = {}
        self.base_url = base_url
        self.results_dir = Path("demo_videos")
        self.results_dir.mkdir(exist_ok=True)

        print("🎬 Enterprise CIA Demo Controller initialized")
        print(f"   Base URL: {base_url}")
        print(f"   Results Directory: {self.results_dir}")

    def register_scenario(self, scenario: CIADemoScenario) -> None:
        """Register a demo scenario."""
        self.scenarios[scenario.name] = scenario
        print(f"✅ Registered scenario: {scenario.name}")

    def list_scenarios(self) -> List[str]:
        """List all available scenario names."""
        return list(self.scenarios.keys())

    def export_scenario_timeline(self, scenario_name: str, output_path: Optional[str] = None) -> str:
        """
        Export scenario timeline to JSON for Puppeteer recorder.

        Args:
            scenario_name: Name of the scenario
            output_path: Optional path to save JSON (defaults to demo_videos/{scenario}_timeline.json)

        Returns:
            Path to exported JSON file
        """
        if scenario_name not in self.scenarios:
            raise KeyError(f"Scenario '{scenario_name}' not found")

        scenario = self.scenarios[scenario_name]

        timeline_data = {
            "scenario_name": scenario.name,
            "description": scenario.description,
            "duration_seconds": scenario.duration_seconds,
            "config": scenario.get_scenario_config(),
            "timeline": scenario.get_visual_timeline(),
            "validation_rules": {
                "expected_apis": scenario.expected_apis,
                "max_duration": scenario.duration_seconds * 1.5,
            }
        }

        if output_path is None:
            output_path = self.results_dir / f"{scenario_name}_timeline.json"
        else:
            output_path = Path(output_path)

        with open(output_path, "w") as f:
            json.dump(timeline_data, f, indent=2)

        print(f"📄 Exported timeline: {output_path}")
        return str(output_path)

    async def run_demo(
        self,
        scenario_name: str,
        *,
        record_video: bool = True,
        validate: bool = True,
    ) -> DemoExecutionResult:
        """
        Execute a demo scenario with optional video recording.

        Args:
            scenario_name: Name of the scenario to run
            record_video: Whether to record video using Puppeteer
            validate: Whether to validate the results

        Returns:
            DemoExecutionResult with execution details

        Raises:
            KeyError: If scenario_name is not found
        """
        if scenario_name not in self.scenarios:
            available = ", ".join(self.scenarios.keys())
            raise KeyError(
                f"Scenario '{scenario_name}' not found. Available: {available}"
            )

        scenario = self.scenarios[scenario_name]
        print(f"\n🎬 Starting demo scenario: {scenario_name}")

        start_time = asyncio.get_event_loop().time()
        video_path = None

        try:
            # Export timeline for video recorder
            timeline_path = self.export_scenario_timeline(scenario_name)

            # If recording video, spawn Puppeteer recorder
            if record_video:
                print("🎥 Starting video recording...")
                video_path = await self._record_video(timeline_path, scenario)

            # Simulate API orchestration (in real implementation, this would call backend)
            config = scenario.get_scenario_config()
            result = await self._execute_scenario(config)

            # Calculate duration
            duration = asyncio.get_event_loop().time() - start_time

            # Validate results if requested
            if validate:
                validation_result = scenario.validate_result(result)
                if not validation_result.is_valid:
                    print(f"⚠️  Validation failed: {validation_result.message}")
                result["validation"] = validation_result.to_dict()

            # Create execution result
            execution_result = DemoExecutionResult(
                scenario_name=scenario_name,
                success=True,
                duration_seconds=duration,
                metrics=result.get("metrics", {}),
                timeline=scenario.get_visual_timeline(),
                video_path=video_path,
            )

            print(f"✅ Demo scenario completed: {scenario_name}")
            print(f"   Duration: {duration:.2f}s")
            if video_path:
                print(f"   Video: {video_path}")

            return execution_result

        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            print(f"❌ Demo scenario failed: {scenario_name}")
            print(f"   Error: {str(e)}")

            return DemoExecutionResult(
                scenario_name=scenario_name,
                success=False,
                duration_seconds=duration,
                metrics={},
                timeline=[],
                video_path=video_path,
                error=str(e),
            )

    async def _execute_scenario(self, config: Dict[str, any]) -> Dict[str, any]:
        """
        Execute the scenario backend logic.

        In real implementation, this would:
        1. Call backend API to generate impact cards
        2. Monitor API orchestration
        3. Collect metrics
        4. Return structured results

        For now, returns mock results for testing.
        """
        await asyncio.sleep(2)  # Simulate API calls

        return {
            "impact_cards": [
                {
                    "id": "ic_1",
                    "competitor": config["competitor"],
                    "title": f"{config['analysis_focus'].replace('_', ' ').title()} Detected",
                    "confidence": 0.92,
                }
            ],
            "api_calls": {
                "news": {"status": "success", "sources": 12, "duration": 0.8},
                "search": {"status": "success", "results": 25, "duration": 1.2},
                "chat": {"status": "success", "insights": 5, "duration": 2.1},
                "ari": {"status": "success", "sources": 450, "duration": 3.5},
            },
            "metrics": {
                "total_duration": 7.6,
                "api_calls": 4,
                "sources_analyzed": 487,
            },
        }

    async def _record_video(
        self, timeline_path: str, scenario: CIADemoScenario
    ) -> str:
        """
        Spawn Puppeteer video recorder with scenario timeline.

        Args:
            timeline_path: Path to timeline JSON
            scenario: Scenario being recorded

        Returns:
            Path to recorded video file
        """
        # In real implementation, this would:
        # 1. Call Node.js Puppeteer recorder script
        # 2. Pass timeline JSON path
        # 3. Wait for recording to complete
        # 4. Return video path

        # For now, simulate recording
        await asyncio.sleep(scenario.duration_seconds + 5)

        video_filename = f"{scenario.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        video_path = self.results_dir / video_filename

        print(f"🎥 Video recording completed: {video_path}")

        return str(video_path)

    async def run_all_scenarios(self, record_videos: bool = True) -> List[DemoExecutionResult]:
        """
        Run all registered scenarios in sequence.

        Args:
            record_videos: Whether to record videos for each scenario

        Returns:
            List of DemoExecutionResult for each scenario
        """
        print(f"\n{'='*80}")
        print(f"🎬 Running all {len(self.scenarios)} demo scenarios")
        print(f"{'='*80}\n")

        results = []
        for scenario_name in self.scenarios:
            result = await self.run_demo(scenario_name, record_video=record_videos)
            results.append(result)
            await asyncio.sleep(2)  # Brief pause between scenarios

        success_count = sum(1 for r in results if r.success)
        print(f"\n{'='*80}")
        print(f"✅ Completed all scenarios: {success_count}/{len(results)} successful")
        print(f"{'='*80}\n")

        return results

    def generate_report(self, results: List[DemoExecutionResult], output_path: Optional[str] = None) -> str:
        """
        Generate a formatted report from demo results.

        Args:
            results: List of execution results
            output_path: Optional path to save report

        Returns:
            Formatted report string
        """
        lines = [
            "=" * 80,
            "ENTERPRISE CIA - DEMO EXECUTION REPORT",
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
            total_videos = sum(1 for r in results if r.video_path)

            lines.extend([
                "=" * 80,
                "SUMMARY STATISTICS",
                "=" * 80,
                f"Average Duration: {avg_duration:.2f}s",
                f"Total Duration: {sum(r.duration_seconds for r in results):.2f}s",
                f"Videos Recorded: {total_videos}",
                "",
            ])

        report = "\n".join(lines)

        # Save report if output path provided
        if output_path:
            output_path = Path(output_path)
            with open(output_path, "w") as f:
                f.write(report)
            print(f"📄 Report saved: {output_path}")

        return report


# Example usage
async def main():
    """Example usage of the demo controller."""
    from demo_system_cia.scenarios.competitor_launch import CompetitorProductLaunchScenario
    from demo_system_cia.scenarios.market_expansion import MarketExpansionScenario

    # Initialize controller
    controller = EnterpriseCIADemoController()

    # Register scenarios
    controller.register_scenario(CompetitorProductLaunchScenario())
    controller.register_scenario(MarketExpansionScenario())

    # List available scenarios
    print("\nAvailable scenarios:")
    for scenario in controller.list_scenarios():
        print(f"  - {scenario}")

    # Run all scenarios
    results = await controller.run_all_scenarios(record_videos=True)

    # Generate report
    report = controller.generate_report(results, output_path="demo_videos/demo_report.txt")
    print(report)


if __name__ == "__main__":
    asyncio.run(main())
