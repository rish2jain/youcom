# Archived Demo Scripts

This folder contains legacy demo recording scripts that have been replaced by the comprehensive `record-demo.js` script.

## Why These Were Archived

All scripts in this folder were **redundant implementations** attempting to solve the same problem: recording demo videos of the Enterprise CIA platform. They were archived on October 31, 2025, because:

1. **Duplication** - Multiple scripts doing essentially the same thing with minor variations
2. **Inconsistency** - Different approaches to the same problem (screenshots, direct recording, ffmpeg variations)
3. **Maintenance burden** - Too many scripts to maintain and update
4. **Complexity** - Difficult to choose which script to use for what purpose

## Replacement Solution

All functionality has been consolidated into:

**`scripts/record-demo.js`** - Comprehensive demo recorder with:
- Multiple recording modes (quick, full, custom)
- Quality presets (low, medium, high)
- Cross-platform support
- Error handling and fallbacks
- Configurable options
- Progress tracking
- Narration markers

See `DEMO_RECORDING_GUIDE.md` for complete usage instructions.

## Archive Contents

### Demo Recording Scripts (18 files)
These scripts used Puppeteer with various screenshot and video recording approaches:

- `actual_dashboard_recording.js` - Dashboard navigation with screenshots
- `automated_demo.js` - Basic automation attempt
- `automated_demo_chrome.js` - Chrome-specific version
- `automated_demo_cross_platform.js` - Cross-platform attempt #1
- `automated_demo_cross_platform_fixed.js` - Cross-platform attempt #2
- `automated_demo_with_video.js` - Video + screenshots hybrid
- `chrome_demo.js` - Simple Chrome launcher
- `complete_demo.js` - "Complete" solution attempt
- `page_content_recording.js` - Page content focused
- `robust_dashboard_recording.js` - Error handling focused
- `robust_video_demo.js` - Video creation focused
- `screenshot_video_demo.js` - Screenshot to video conversion
- `simple_demo.js` - Simplified version #1
- `simple_working_demo.js` - Simplified version #2
- `video_demo.js` - Direct video recording attempt
- `window_focused_demo.js` - Window focus handling
- `window_recording_demo.js` - Window-based recording
- `working_demo.js` - Another "working" version

### Shell Scripts (3 files)
Bash scripts for automation and setup:

- `create_demo_video.sh` - FFmpeg video creation
- `create_presentation_video.sh` - Presentation video from screenshots
- `demo_automation_setup.sh` - Initial setup automation

## If You Need to Reference Archived Scripts

While these scripts are archived, they contain useful code patterns if you need to:

1. **Add new recording features** - Look at how different scripts handled browser automation
2. **Debug issues** - See how various approaches solved specific problems
3. **Understand evolution** - See how the solution evolved over time

## Restoration

If you need to restore any archived script:

```bash
# Copy from archive
cp scripts/archive/script_name.js scripts/

# Make executable if needed
chmod +x scripts/script_name.js
```

However, we recommend extending `record-demo.js` instead of restoring archived scripts.

## History

**Created:** Various dates in October 2025
**Archived:** October 31, 2025
**Reason:** Consolidation into comprehensive solution
**Replacement:** `scripts/record-demo.js`

---

For current demo recording, use: `npm run record:help`
