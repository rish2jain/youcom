# Enterprise CIA Demo Assets

**Last Updated**: October 31, 2025  
**Status**: Consolidated demo media and system files

## 📁 Directory Structure

This directory contains all demo-related assets for the Enterprise CIA platform, organized by type:

```
demo/
├── README.md                          # This file
├── videos/                            # Demo videos and timelines
│   ├── *.mp4                         # Recorded demo videos
│   ├── *_timeline.json               # Timeline configurations
│   ├── narration_full.txt            # Narration scripts
│   └── archive/                      # Archived video materials
├── screenshots/                       # Demo screenshots
│   └── archive/                      # Archived screenshot materials
├── system/                           # Demo orchestration system
│   ├── __init__.py                   # Python package
│   ├── demo_controller.py            # Main demo controller
│   ├── run_demos.py                  # Demo execution script
│   ├── improved_demo_recorder.js     # Enhanced Puppeteer recorder
│   ├── system_level_recorder.js      # System-level recording script
│   ├── scenarios/                    # Demo scenario definitions
│   └── __pycache__/                  # Python cache
├── start_demo.sh                     # Quick demo startup script
└── archive/                          # Legacy demo system
    ├── __init__.py                   # Legacy Python package
    ├── simplified_demo.py            # Legacy demo script
    ├── metrics/                      # Legacy metrics system
    ├── scenarios/                    # Legacy scenarios
    └── validation/                   # Legacy validation
```

## 🎬 Videos Directory

Contains recorded demo videos and their associated configuration files:

### Current Videos

- **competitor_product_launch_2025-10-31T14-17-33-150Z.mp4**: Product launch detection demo
- **competitor_product_launch_timeline.json**: Timeline configuration for product launch demo
- **market_expansion_timeline.json**: Timeline configuration for market expansion demo
- **narration_full.txt**: Complete narration script for demos

### Usage

```bash
# Play demo video
open demo/videos/competitor_product_launch_2025-10-31T14-17-33-150Z.mp4

# Use timeline for recording
node scripts/record-demo.js --timeline demo/videos/competitor_product_launch_timeline.json
```

## 📸 Screenshots Directory

Contains demo screenshots and visual assets:

### Structure

- **archive/**: Historical screenshot materials
- Future screenshots should be organized by demo type

### Usage

```bash
# Add new screenshots
mkdir demo/screenshots/product_launch/
# Save screenshots with descriptive names
```

## 🤖 System Directory

Contains the active demo orchestration system (moved from demo_system_cia/):

### Key Files

- **demo_controller.py**: Main orchestration controller
- **run_demos.py**: Execution script for automated demos
- **scenarios/**: Demo scenario definitions

### Usage

```python
# Run automated demos
cd demo/system
python run_demos.py

# Use in code
from demo.system import EnterpriseCIADemoController
controller = EnterpriseCIADemoController()
```

### Documentation

See **[docs/development/DEMO_SYSTEM.md](../docs/development/DEMO_SYSTEM.md)** for complete documentation.

## 🗄️ Archive Directory

Contains legacy demo system files (moved from demo_system/):

### Contents

- **simplified_demo.py**: Legacy demo script
- **metrics/**: Legacy metrics collection
- **scenarios/**: Legacy scenario definitions
- **validation/**: Legacy validation system

### Status

These files are preserved for reference but the active system is in `system/`.

## 🚀 Quick Start

### Demo Startup Script

```bash
# Quick demo environment startup
./demo/start_demo.sh
```

### Recording Scripts

- **improved_demo_recorder.js**: Enhanced Puppeteer recorder with timeline support
- **system_level_recorder.js**: System-level recording capabilities

```bash
# Use enhanced recorder
cd demo/system
node improved_demo_recorder.js --timeline ../videos/my_timeline.json
```

### Recording New Demo Video

```bash
# 1. Create timeline configuration
cp demo/videos/competitor_product_launch_timeline.json demo/videos/my_demo_timeline.json

# 2. Edit timeline for your demo
# Edit demo/videos/my_demo_timeline.json

# 3. Record video
node scripts/record-demo.js --timeline demo/videos/my_demo_timeline.json

# 4. Video will be saved to demo/videos/
```

### Running Automated Demo

```bash
# Navigate to system directory
cd demo/system

# Run all scenarios
python run_demos.py

# Run specific scenario
python -c "
import asyncio
from demo_controller import EnterpriseCIADemoController

async def run():
    controller = EnterpriseCIADemoController()
    result = await controller.run_demo('competitor_product_launch')
    print(f'Success: {result.success}')

asyncio.run(run())
"
```

### Taking Screenshots

```bash
# Use browser dev tools or screenshot tools
# Save to appropriate subdirectory in demo/screenshots/

# For automated screenshots during demos
# See demo/system/demo_controller.py
```

## 📋 File Naming Conventions

### Videos

- Format: `{scenario_name}_{timestamp}.mp4`
- Example: `competitor_product_launch_2025-10-31T14-17-33-150Z.mp4`

### Timelines

- Format: `{scenario_name}_timeline.json`
- Example: `competitor_product_launch_timeline.json`

### Screenshots

- Format: `{demo_type}_{step_number}_{description}.png`
- Example: `product_launch_01_dashboard_overview.png`

## 🔧 Integration

### With Documentation

- Demo guides reference files in this directory
- See **[docs/user/DEMO_GUIDE.md](../docs/user/DEMO_GUIDE.md)** for usage instructions

### With Scripts

- Recording scripts in `scripts/` use timeline files from `demo/videos/`
- Demo system integrates with main application for live demos

### With Main Application

- Demo system can control the main application for automated recording
- Screenshots and videos can be used in presentations and documentation

## 📊 Maintenance

### Adding New Content

1. **Videos**: Save to `demo/videos/` with proper naming
2. **Screenshots**: Organize in `demo/screenshots/` by demo type
3. **System Updates**: Modify files in `demo/system/`
4. **Archive Old Content**: Move outdated files to appropriate archive directories

### Cleanup Guidelines

- Keep only current, relevant demo materials in main directories
- Archive outdated content rather than deleting
- Maintain clear naming conventions
- Update this README when adding new categories

## 🎯 Related Documentation

- **[Demo Guide](../docs/user/DEMO_GUIDE.md)**: Complete demo preparation guide
- **[Demo System](../docs/development/DEMO_SYSTEM.md)**: Technical documentation for demo orchestration
- **[Quick Start](../docs/setup/QUICK_START.md)**: Getting started with the platform

---

**Enterprise CIA Demo Assets** - Organized media and automation for professional demonstrations
