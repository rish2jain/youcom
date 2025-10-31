# Enterprise CIA Demo System

Automated demo orchestration and video recording system for Enterprise CIA competitive intelligence platform.

Adapted from the Incident Commander demo system for competitive intelligence use cases.

## 🎯 Purpose

This system provides:

- **Scenario-based demos**: Pre-configured intelligence scenarios with expected outcomes
- **Automated video recording**: Integration with Puppeteer recorder for demo videos
- **Timeline coordination**: Precise timing for smooth, professional demo videos
- **Validation system**: Automated checks for demo execution quality
- **Report generation**: Comprehensive execution reports with metrics

## 📁 Structure

```
demo_system_cia/
├── __init__.py                          # Package exports
├── demo_controller.py                   # Main controller
├── scenarios/                           # Demo scenarios
│   ├── __init__.py
│   ├── base.py                         # Base scenario class
│   ├── competitor_launch.py            # Product launch detection scenario
│   └── market_expansion.py             # Market expansion tracking scenario
└── README.md                           # Demo system package README
```

## 🚀 Quick Start

### 1. Basic Usage

```python
import asyncio
from demo_system_cia import EnterpriseCIADemoController
from demo_system_cia.scenarios import (
    CompetitorProductLaunchScenario,
    MarketExpansionScenario,
)

async def run_demos():
    # Initialize controller
    controller = EnterpriseCIADemoController(base_url="http://localhost:3000")

    # Register scenarios
    controller.register_scenario(CompetitorProductLaunchScenario())
    controller.register_scenario(MarketExpansionScenario())

    # Run all scenarios with video recording
    results = await controller.run_all_scenarios(record_videos=True)

    # Generate report
    report = controller.generate_report(results, output_path="demo_report.txt")
    print(report)

if __name__ == "__main__":
    asyncio.run(run_demos())
```

### 2. Run Individual Scenario

```python
# Run just one scenario
result = await controller.run_demo(
    "competitor_product_launch",
    record_video=True,
    validate=True
)

print(f"Success: {result.success}")
print(f"Duration: {result.duration_seconds}s")
print(f"Video: {result.video_path}")
```

### 3. Export Timeline for Manual Recording

```python
# Export timeline JSON for Puppeteer
timeline_path = controller.export_scenario_timeline(
    "competitor_product_launch",
    output_path="demo_videos/product_launch_timeline.json"
)

# Then use with Puppeteer recorder:
# node scripts/Claude/improved_demo_recorder.js --timeline demo_videos/product_launch_timeline.json
```

## 📋 Available Scenarios

### 1. Competitor Product Launch (`competitor_product_launch`)

**Duration**: 45 seconds
**Focus**: Detecting and analyzing product announcements
**APIs Used**: News, Search, Chat (Custom Agents), ARI

**Timeline**:

- 0:00 - Dashboard load
- 0:08 - Scroll to watchlist
- 0:12 - Highlight detected impact card
- 0:15 - Expand card details
- 0:18 - Show News API sources (12 sources)
- 0:22 - Switch to Analysis tab
- 0:27 - Show strategic assessment
- 0:32 - Show recommended actions
- 0:42 - Complete (all 4 APIs)

### 2. Market Expansion (`market_expansion`)

**Duration**: 40 seconds
**Focus**: Tracking competitor market entry moves
**APIs Used**: News, Search, Chat (Custom Agents), ARI

**Timeline**:

- 0:00 - Scroll to expansion monitoring
- 0:05 - Highlight partnership detection
- 0:10 - Click for details
- 0:13 - Show Search API enrichment
- 0:18 - Strategic threat assessment
- 0:23 - Display threat level (High)
- 0:28 - Show defensive strategies
- 0:38 - Complete analysis

## 🎬 Creating Custom Scenarios

### Step 1: Create Scenario Class

```python
from demo_system_cia.scenarios.base import CIADemoScenario
from typing import Any, Dict

class MyCustomScenario(CIADemoScenario):
    def __init__(self):
        super().__init__(
            name="my_scenario",
            description="My custom demo scenario",
            duration_seconds=30,
            expected_apis=["news", "search", "chat", "ari"]
        )

    def get_scenario_config(self) -> Dict[str, Any]:
        return {
            "competitor": "CompanyName",
            "search_terms": ["term1", "term2"],
            "analysis_focus": "custom_focus",
            "expected_insights": ["insight1", "insight2"],
            "demo_mode": False,
        }

    def get_visual_timeline(self) -> list[Dict[str, Any]]:
        return [
            {
                "timestamp": 0,
                "action": "load",
                "target": "dashboard",
                "narration": "Starting analysis..."
            },
            {
                "timestamp": 5,
                "action": "scroll",
                "target": "impact_cards",
                "distance": 400,
                "duration": 2,
                "narration": "Reviewing intelligence..."
            },
            # Add more timeline events...
        ]
```

### Step 2: Register and Run

```python
controller.register_scenario(MyCustomScenario())
result = await controller.run_demo("my_scenario")
```

## 🎥 Video Recording Integration

The demo controller exports timeline JSON files that the Puppeteer recorder uses:

```json
{
  "scenario_name": "competitor_product_launch",
  "description": "Detect and analyze competitor product launch announcements",
  "duration_seconds": 45,
  "config": {
    "competitor": "OpenAI",
    "analysis_focus": "product_launch"
  },
  "timeline": [
    {
      "timestamp": 0,
      "action": "load",
      "target": "dashboard",
      "narration": "Enterprise CIA Dashboard"
    },
    ...
  ],
  "validation_rules": {
    "expected_apis": ["news", "search", "chat", "ari"],
    "max_duration": 67.5
  }
}
```

## ✅ Validation System

Each scenario has built-in validation that checks:

- **API Coverage**: All expected You.com APIs were called
- **Impact Cards**: Intelligence was generated successfully
- **Duration**: Execution completed within reasonable time
- **Errors**: No failures during execution

```python
validation_result = scenario.validate_result(result)

if validation_result.is_valid:
    print("✅ Demo executed successfully")
else:
    print(f"❌ Validation failed: {validation_result.message}")
    print(f"Details: {validation_result.details}")
```

## 📊 Metrics and Reporting

The system generates comprehensive reports:

```
================================================================================
ENTERPRISE CIA - DEMO EXECUTION REPORT
================================================================================
Generated: 2025-10-31T10:00:00.000Z
Total Scenarios: 2
Successful: 2
Failed: 0

✓ SUCCESS: competitor_product_launch
Duration: 45.23s
Timeline Events: 11
Video: demo_videos/competitor_product_launch_20251031_100000.mp4

Metrics:
  total_duration: 7.6
  api_calls: 4
  sources_analyzed: 487

✓ SUCCESS: market_expansion
Duration: 40.18s
Timeline Events: 9
Video: demo_videos/market_expansion_20251031_100045.mp4

Metrics:
  total_duration: 6.8
  api_calls: 4
  sources_analyzed: 412

================================================================================
SUMMARY STATISTICS
================================================================================
Average Duration: 42.71s
Total Duration: 85.41s
Videos Recorded: 2
```

## 🔧 Configuration

### Controller Options

```python
controller = EnterpriseCIADemoController(
    base_url="http://localhost:3000"  # Frontend URL
)
```

### Scenario Options

```python
class MyScenario(CIADemoScenario):
    def __init__(self):
        super().__init__(
            name="scenario_name",              # Unique identifier
            description="What this demos",      # Human-readable description
            duration_seconds=45,                # Expected duration
            expected_apis=["news", "search"]    # APIs that should be called
        )
```

## 🎯 Timeline Actions

Available actions for visual timeline:

| Action      | Description       | Parameters                              |
| ----------- | ----------------- | --------------------------------------- |
| `load`      | Navigate to URL   | `target`: page name                     |
| `scroll`    | Smooth scroll     | `distance`: pixels, `duration`: seconds |
| `click`     | Click element     | `target`: element selector              |
| `highlight` | Highlight element | `target`: element selector              |
| `wait`      | Pause at position | `target`: context name                  |

## 📝 Best Practices

### 1. Timing

- Keep scenarios **under 60 seconds** for viewer attention
- Allow **3-5 seconds** for viewers to read content
- **2-3 seconds** for transitions between sections
- Build **5-10 second buffer** for narration

### 2. Narration

- **First 10 seconds**: Hook the viewer
- **Middle section**: Show key features
- **Last 10 seconds**: Strong conclusion
- Use **action verbs** and **present tense**

### 3. Visual Flow

- Start with **familiar context** (dashboard)
- **Zoom in** on specific features
- Show **progression** (detection → analysis → action)
- End with **summary** or **return to overview**

### 4. Validation

- Always validate **API coverage**
- Check for **expected data** in results
- Verify **timing bounds**
- Test with **real API calls** before recording

## 🔄 Integration with Existing System

This demo system complements the existing:

- `scripts/Claude/improved_demo_recorder.js` - Puppeteer recorder
- `scripts/Claude/demo_timeline_2min.md` - Manual timeline guide
- `demo_videos/` - Output directory

The Python controller generates timeline JSON files that the Node.js recorder consumes.

## 🚀 Future Enhancements

Potential improvements:

- [ ] Real backend API integration
- [ ] Live metrics collection during demos
- [ ] A/B testing for different demo styles
- [ ] Automated narration generation
- [ ] Multi-language support
- [ ] Interactive demo mode (user-controlled)

## 📚 Related Documentation

- `/scripts/Claude/demo_timeline_2min.md` - Manual 2-minute demo timeline
- `/scripts/Claude/improved_demo_recorder.js` - Puppeteer video recorder
- `/DEMO_RECORDING_GUIDE.md` - Complete recording guide

## 🤝 Contributing

To add new scenarios:

1. Create class inheriting from `CIADemoScenario`
2. Implement `get_scenario_config()` and `get_visual_timeline()`
3. Register with controller
4. Test execution and validation
5. Export timeline and record video

## 📄 License

Part of the Enterprise CIA project for You.com Hackathon 2025.
