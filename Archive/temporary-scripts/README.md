# Archived Temporary Scripts and Files

**Archived on**: October 31, 2025  
**Reason**: Cleanup of temporary development files and duplicates

## Files Archived

### High Priority - Development Artifacts

- **`claude_package.json`** - Duplicate package.json for demo recording (superseded by main package.json)
- **`quick_start.sh`** - Development setup script (functionality moved to proper scripts)
- **`.checkpoints/`** - Development checkpoint system (not part of core application)
- **`.qodo/`** - Development tool directory (external tooling)

### Claude Development Directory

- **`scripts/Claude/`** - Complete directory containing:
  - `improved_demo_recorder.js` - Duplicate of `demo/system/improved_demo_recorder.js`
  - `system_level_recorder.js` - Duplicate of `demo/system/system_level_recorder.js`
  - `package.json` - Duplicate package configuration
  - `quick_start.sh` - Duplicate setup script

### Duplicate Demo Scripts

- **`scripts/record-demo.js`** - Older version (23,803 bytes, Oct 31 08:53)
- **`scripts/record-demo-enhanced.js`** - Older version (17,919 bytes, Oct 31 09:24)
- **`scripts/record_demo.py`** - Python version (6,636 bytes, Oct 24 09:14)
- **`scripts/setup-demo.sh`** - Redundant with `demo/start_demo.sh`
- **`scripts/run_demo.sh`** - Redundant with demo system
- **`scripts/setup_enhancements_demo.py`** - Temporary enhancement setup script

## Active Versions (Kept)

### Demo System (Current)

- **`demo/system/improved_demo_recorder.js`** - Current version (12,141 bytes, Oct 31 09:56)
- **`demo/system/system_level_recorder.js`** - Current version (12,658 bytes, Oct 31 09:57)
- **`demo/start_demo.sh`** - Main demo startup script

### Essential Scripts (Kept)

- **`scripts/deploy.sh`** - Deployment script
- **`scripts/seed_demo_data.py`** - Data seeding utility
- **`scripts/setup_complete_integration.py`** - Integration setup
- **`scripts/verify_integration.py`** - Integration verification
- **`run_tests.sh`** - Test runner script

## Cache Files Cleaned

- Removed all `__pycache__/` directories
- Removed all `.DS_Store` files

## .gitignore Updates

- Added `.checkpoints/` to prevent future accumulation

## Restoration Instructions

If any of these files are needed:

1. Check if functionality exists in current active versions
2. Copy from this archive directory
3. Update paths and dependencies as needed

## Notes

- All archived files were development artifacts or duplicates
- Core functionality is preserved in the organized demo system
- No production code or essential configuration was archived
