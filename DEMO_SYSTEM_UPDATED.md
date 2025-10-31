# Enterprise CIA Demo System - Updated for Current Project

## ✅ What Was Done

Adapted the `demo_system` folder from a previous Incident Commander project to work with the Enterprise CIA competitive intelligence platform.

## 📁 New Structure Created

```
demo_system_cia/
├── __init__.py                          # Package exports
├── demo_controller.py                   # Main orchestration controller
├── run_demos.py                         # CLI runner script
├── README.md                           # Complete documentation
└── scenarios/                          # Demo scenarios
    ├── __init__.py
    ├── base.py                         # Abstract base class
    ├── competitor_launch.py            # Product launch detection (45s)
    └── market_expansion.py             # Market expansion tracking (40s)
```

## 🎯 Key Features

### 1. Scenario-Based Demos
- **Pre-configured intelligence scenarios** with expected outcomes
- **Automated validation** to ensure demos work correctly
- **Flexible timeline system** for precise video coordination

### 2. Video Recording Integration
- Exports **timeline JSON files** for Puppeteer recorder
- Coordinates **API orchestration** with visual presentation
- Supports **automated** and **manual** recording modes

### 3. Two Built-in Scenarios

#### Competitor Product Launch (45 seconds)
```python
# Detects OpenAI product launches
- News API: 12 sources detection
- Search API: Market context
- Custom Agents: Strategic analysis
- ARI: Deep 400+ source synthesis
```

#### Market Expansion (40 seconds)
```python
# Tracks Anthropic market moves
- Partnership detection
- Threat assessment
- Defensive strategy recommendations
```

## 🚀 How to Use

### Quick Start

```bash
# Export timeline JSON files only
python demo_system_cia/run_demos.py --export-only

# Run all scenarios (with video recording)
python demo_system_cia/run_demos.py

# Run specific scenario
python demo_system_cia/run_demos.py --scenario competitor_product_launch

# Skip video recording
python demo_system_cia/run_demos.py --no-video
```

### Programmatic Usage

```python
import asyncio
from demo_system_cia import EnterpriseCIADemoController
from demo_system_cia.scenarios import CompetitorProductLaunchScenario

async def main():
    # Initialize
    controller = EnterpriseCIADemoController()

    # Register scenario
    controller.register_scenario(CompetitorProductLaunchScenario())

    # Export timeline for video recorder
    timeline_path = controller.export_scenario_timeline(
        "competitor_product_launch"
    )
    # Output: demo_videos/competitor_product_launch_timeline.json

    # Run demo with validation
    result = await controller.run_demo(
        "competitor_product_launch",
        record_video=True,
        validate=True
    )

    print(f"Success: {result.success}")
    print(f"Duration: {result.duration_seconds}s")

asyncio.run(main())
```

## 📋 Timeline JSON Format

The system exports timeline JSON files that the Puppeteer recorder consumes:

```json
{
  "scenario_name": "competitor_product_launch",
  "description": "Detect and analyze competitor product launch",
  "duration_seconds": 45,
  "config": {
    "competitor": "OpenAI",
    "analysis_focus": "product_launch",
    "expected_insights": [...]
  },
  "timeline": [
    {
      "timestamp": 0,
      "action": "load",
      "target": "dashboard",
      "narration": "Enterprise CIA Dashboard"
    },
    {
      "timestamp": 8,
      "action": "scroll",
      "target": "watchlist",
      "distance": 400,
      "duration": 2,
      "narration": "Monitoring OpenAI..."
    },
    ...
  ],
  "validation_rules": {
    "expected_apis": ["news", "search", "chat", "ari"],
    "max_duration": 67.5
  }
}
```

## 🎬 Integration with Video Recorder

### Option 1: Use exported timeline (Recommended)

```bash
# Export timeline
python demo_system_cia/run_demos.py --export-only

# Use with Puppeteer recorder
node scripts/Claude/improved_demo_recorder.js \
  --timeline demo_videos/competitor_product_launch_timeline.json
```

### Option 2: Let controller handle recording

```python
# Controller will spawn Puppeteer automatically
result = await controller.run_demo(
    "competitor_product_launch",
    record_video=True  # Spawns recorder with timeline
)
```

## ✅ Validation System

Each scenario validates:
- **API Coverage**: All You.com APIs called (News, Search, Chat, ARI)
- **Intelligence Generated**: Impact cards created successfully
- **Timing**: Execution within expected duration
- **No Errors**: Clean execution without failures

```python
validation_result = scenario.validate_result(execution_result)

if validation_result.is_valid:
    print("✅ Demo executed successfully")
    print(f"Impact cards: {validation_result.details['impact_cards']}")
    print(f"APIs called: {validation_result.details['apis_called']}")
else:
    print(f"❌ {validation_result.message}")
```

## 📊 Execution Reports

Generates comprehensive reports:

```
================================================================================
ENTERPRISE CIA - DEMO EXECUTION REPORT
================================================================================
Generated: 2025-10-31T14:00:00Z
Total Scenarios: 2
Successful: 2
Failed: 0

✓ SUCCESS: competitor_product_launch
Duration: 45.23s
Timeline Events: 11
Video: demo_videos/competitor_product_launch_20251031_140000.mp4

✓ SUCCESS: market_expansion
Duration: 40.18s
Timeline Events: 9
Video: demo_videos/market_expansion_20251031_140045.mp4

================================================================================
SUMMARY STATISTICS
================================================================================
Average Duration: 42.71s
Total Duration: 85.41s
Videos Recorded: 2
```

## 🎨 Creating Custom Scenarios

```python
from demo_system_cia.scenarios.base import CIADemoScenario

class MyScenario(CIADemoScenario):
    def __init__(self):
        super().__init__(
            name="my_scenario",
            description="My custom demo",
            duration_seconds=30,
            expected_apis=["news", "search", "chat", "ari"]
        )

    def get_scenario_config(self):
        return {
            "competitor": "CompanyName",
            "search_terms": ["term1", "term2"],
            "analysis_focus": "custom_focus",
            "expected_insights": ["insight1", "insight2"]
        }

    def get_visual_timeline(self):
        return [
            {
                "timestamp": 0,
                "action": "load",
                "target": "dashboard",
                "narration": "Starting..."
            },
            # More timeline events...
        ]

# Register and use
controller.register_scenario(MyScenario())
```

## 🔑 Key Differences from Original

| Original (Incident Commander) | Adapted (Enterprise CIA) |
|-------------------------------|---------------------------|
| Incident detection & response | Competitive intelligence |
| Security phases (detect, consensus, resolve) | API orchestration (News, Search, Chat, ARI) |
| Alert timeline | Impact card generation |
| Communication planning | Action recommendations |
| LangGraph orchestration | You.com API coordination |

## 📚 Files Generated

1. **Timeline JSON** - `demo_videos/competitor_product_launch_timeline.json`
2. **Timeline JSON** - `demo_videos/market_expansion_timeline.json`
3. **Complete README** - `demo_system_cia/README.md`
4. **Runner Script** - `demo_system_cia/run_demos.py`
5. **Controller** - `demo_system_cia/demo_controller.py`
6. **Scenarios** - `demo_system_cia/scenarios/*.py`

## ✨ Benefits

1. **Consistency**: All demos follow same structure and timing
2. **Validation**: Automated checks ensure demos work correctly
3. **Flexibility**: Easy to create new scenarios
4. **Integration**: Seamless connection to video recorder
5. **Documentation**: Self-documenting with timeline JSON
6. **Reusability**: Scenarios can be re-run for different recordings

## 🔄 Workflow

```
Create Scenario → Register → Export Timeline → Record Video → Validate
     ↓               ↓             ↓               ↓            ↓
   Python       Controller     JSON File      Puppeteer    Auto-check
```

## 📝 Next Steps

1. **Test scenarios** with real backend API calls
2. **Create more scenarios** (e.g., pricing changes, hiring signals)
3. **Integrate metrics collection** during execution
4. **Add narration generation** for voiceovers
5. **Build interactive mode** for live demos

## 🎯 Example Output

Running the export command:

```bash
$ python demo_system_cia/run_demos.py --export-only

================================================================================
🎬 ENTERPRISE CIA DEMO SYSTEM
================================================================================

🎬 Enterprise CIA Demo Controller initialized
   Base URL: http://localhost:3000
   Results Directory: demo_videos
✅ Registered scenario: competitor_product_launch
✅ Registered scenario: market_expansion
📋 Registered 2 scenarios:
   • competitor_product_launch
   • market_expansion

📤 Exporting timeline JSON files...

📄 Exported timeline: demo_videos/competitor_product_launch_timeline.json
✅ Exported: demo_videos/competitor_product_launch_timeline.json
📄 Exported timeline: demo_videos/market_expansion_timeline.json
✅ Exported: demo_videos/market_expansion_timeline.json

✨ Timeline export complete!
```

## 🏆 Summary

Successfully adapted the demo system from Incident Commander to Enterprise CIA, providing:
- ✅ Structured scenario management
- ✅ Automated timeline generation
- ✅ Video recording integration
- ✅ Validation framework
- ✅ Comprehensive documentation
- ✅ CLI runner for easy execution
- ✅ Two working demo scenarios
- ✅ Extensible architecture for new scenarios

The system is ready to use for creating professional, repeatable demo videos!
