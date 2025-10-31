#!/usr/bin/env python3
"""Simple script to run Enterprise CIA demo scenarios.

Usage:
    python demo_system_cia/run_demos.py                    # Run all scenarios
    python demo_system_cia/run_demos.py --scenario competitor_product_launch  # Run one
    python demo_system_cia/run_demos.py --no-video         # Skip video recording
    python demo_system_cia/run_demos.py --export-only      # Just export timelines
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from demo_system_cia import EnterpriseCIADemoController
from demo_system_cia.scenarios import (
    CompetitorProductLaunchScenario,
    MarketExpansionScenario,
)


async def main():
    parser = argparse.ArgumentParser(
        description="Run Enterprise CIA demo scenarios"
    )
    parser.add_argument(
        "--scenario",
        type=str,
        help="Specific scenario to run (default: all)",
        choices=["competitor_product_launch", "market_expansion", "all"],
        default="all",
    )
    parser.add_argument(
        "--no-video",
        action="store_true",
        help="Skip video recording",
    )
    parser.add_argument(
        "--export-only",
        action="store_true",
        help="Only export timeline JSON files, don't run demos",
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default="http://localhost:3000",
        help="Frontend base URL (default: http://localhost:3000)",
    )
    parser.add_argument(
        "--report",
        type=str,
        help="Path to save execution report",
        default="demo_videos/demo_report.txt",
    )

    args = parser.parse_args()

    print("\n" + "=" * 80)
    print("🎬 ENTERPRISE CIA DEMO SYSTEM")
    print("=" * 80 + "\n")

    # Initialize controller
    controller = EnterpriseCIADemoController(base_url=args.base_url)

    # Register scenarios
    scenarios = {
        "competitor_product_launch": CompetitorProductLaunchScenario(),
        "market_expansion": MarketExpansionScenario(),
    }

    for scenario in scenarios.values():
        controller.register_scenario(scenario)

    print(f"📋 Registered {len(scenarios)} scenarios:")
    for name in controller.list_scenarios():
        print(f"   • {name}")
    print()

    # Export-only mode
    if args.export_only:
        print("📤 Exporting timeline JSON files...\n")
        for scenario_name in controller.list_scenarios():
            timeline_path = controller.export_scenario_timeline(scenario_name)
            print(f"✅ Exported: {timeline_path}")
        print("\n✨ Timeline export complete!")
        return

    # Run scenarios
    record_videos = not args.no_video

    if args.scenario == "all":
        print(f"🎬 Running all scenarios (video recording: {record_videos})\n")
        results = await controller.run_all_scenarios(record_videos=record_videos)
    else:
        print(f"🎬 Running scenario: {args.scenario} (video recording: {record_videos})\n")
        result = await controller.run_demo(
            args.scenario,
            record_video=record_videos,
            validate=True,
        )
        results = [result]

    # Generate report
    print("\n" + "=" * 80)
    print("📊 GENERATING REPORT")
    print("=" * 80 + "\n")

    report = controller.generate_report(results, output_path=args.report)
    print(report)

    # Summary
    success_count = sum(1 for r in results if r.success)
    total = len(results)

    print("\n" + "=" * 80)
    if success_count == total:
        print(f"✅ SUCCESS: All {total} scenarios completed")
    else:
        print(f"⚠️  PARTIAL SUCCESS: {success_count}/{total} scenarios succeeded")
    print("=" * 80 + "\n")

    # Exit with appropriate code
    sys.exit(0 if success_count == total else 1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
