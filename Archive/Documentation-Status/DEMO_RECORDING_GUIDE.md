# Demo Recording Guide

Complete guide for recording high-quality demo videos of the Enterprise CIA platform.

## Quick Start

```bash
# Install dependencies (if not already done)
npm install

# Record a quick 60-second demo
npm run record:quick

# Record a full 3-minute demo
npm run record:full

# Record with custom settings
npm run record:custom -- --duration 120 --quality high

# Show all options
npm run record:help
```

## Prerequisites

### Required Software

1. **Node.js and npm** (already installed)
2. **Google Chrome** - The script uses Puppeteer with Chrome
3. **FFmpeg** - For video creation from screenshots

#### Install FFmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

**Windows:**
Download from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)

### Verify Installation

```bash
# Check FFmpeg
ffmpeg -version

# Check Chrome (macOS)
ls "/Applications/Google Chrome.app"
```

## Recording Modes

### 1. Quick Mode (60 seconds)
Fast overview of key features, perfect for social media or quick presentations.

```bash
npm run record:quick
```

**What it includes:**
- Platform introduction (5s)
- API integration showcase (8s)
- Real-time threat detection (8s)
- Intelligence synthesis (8s)
- Value proposition (8s)
- Technical highlights (8s)
- Closing (7s)

### 2. Full Mode (180 seconds)
Comprehensive demonstration with detailed feature walkthrough.

```bash
npm run record:full
```

**What it includes:**
- Introduction (30s)
- API orchestration overview (30s)
- Feature exploration with navigation (60s)
- Value proposition (30s)
- Technical excellence (30s)

### 3. Custom Mode
Record for a specific duration with custom settings.

```bash
# Custom duration
npm run record:custom -- --duration 120

# Custom with specific settings
npm run record -- --mode custom --duration 90 --quality medium
```

## Configuration Options

### Quality Presets

**High Quality (Default)**
- Resolution: 1920x1080 (Full HD)
- FPS: 30
- Encoding: CRF 18 (visually lossless)
- Best for: Final presentations, YouTube uploads

```bash
npm run record -- --quality high
```

**Medium Quality**
- Resolution: 1280x720 (HD)
- FPS: 15
- Encoding: CRF 23 (good quality)
- Best for: Quick previews, social media

```bash
npm run record -- --quality medium
```

**Low Quality**
- Resolution: 1280x720 (HD)
- FPS: 10
- Encoding: CRF 28 (smaller file size)
- Best for: Testing, drafts

```bash
npm run record -- --quality low
```

### Advanced Options

```bash
# Custom FPS (overrides quality preset)
npm run record -- --fps 24

# Custom URL (for different environments)
npm run record -- --url http://localhost:3000

# Keep screenshot frames (for manual editing)
npm run record -- --no-cleanup

# Custom output directory
npm run record -- --output my_videos

# Headless mode (no visible browser)
npm run record -- --headless

# Combine multiple options
npm run record -- --mode full --quality high --fps 30 --no-cleanup
```

## Output Files

All recordings are saved to the `demo_videos/` directory:

```
demo_videos/
├── enterprise_cia_full_2025-10-31T08-30-00.mp4  # Video file
├── narration_full.txt                            # Narration markers
└── screenshots/                                  # Frames (if --no-cleanup)
    ├── frame_000000.png
    ├── frame_000001.png
    └── ...
```

### Narration Markers File

The narration file contains timestamps for adding voiceover:

```
[0s] 2025-10-31T08:30:00: Welcome to Enterprise CIA
[5s] 2025-10-31T08:30:05: Powered by all four You.com APIs
[13s] 2025-10-31T08:30:13: Real-time threat detection
...
```

Use these markers to sync your voiceover in video editing software.

## Workflow Recommendations

### 1. For Quick Demos (Social Media, Slack)

```bash
# Record quick demo
npm run record:quick

# Output: ~60s video, ~10-20MB
# Perfect for: Twitter, LinkedIn, Slack channels
```

### 2. For Presentations (Hackathons, Pitches)

```bash
# Record full demo in high quality
npm run record:full --quality high

# Output: ~180s video, ~50-80MB
# Perfect for: Presentations, YouTube, detailed walkthroughs
```

### 3. For Custom Editing

```bash
# Record with frame preservation
npm run record:full -- --quality high --no-cleanup

# This keeps all screenshot frames for:
# - Frame-by-frame editing
# - Custom transitions
# - Adding annotations
```

### 4. Production Workflow

```bash
# 1. Start your development server
npm run dev

# 2. In another terminal, record
npm run record:full -- --quality high --no-cleanup

# 3. Review the video
open demo_videos/enterprise_cia_full_*.mp4

# 4. Add voiceover using narration markers
# 5. Edit in your video editor
# 6. Export final version
```

## Troubleshooting

### Chrome Not Found

**Error:** `Chrome launch failed: Could not find Chrome executable`

**Solution:**
1. Ensure Google Chrome is installed
2. The script looks for Chrome in standard locations:
   - macOS: `/Applications/Google Chrome.app`
   - Linux: `/usr/bin/google-chrome`
   - Windows: `C:\Program Files\Google\Chrome\Application\chrome.exe`

### FFmpeg Not Found

**Error:** `ffmpeg not found`

**Solution:**
Install FFmpeg using the commands in Prerequisites section above.

### Application Not Loading

**Error:** `Failed to load application`

**Solution:**
1. Ensure your development server is running:
   ```bash
   npm run dev
   ```
2. Wait for the server to start completely
3. Check that it's accessible at http://localhost:3000
4. Try with a custom URL:
   ```bash
   npm run record -- --url http://localhost:3000
   ```

### Low Frame Rate

**Issue:** Video appears choppy

**Solution:**
1. Use higher FPS:
   ```bash
   npm run record -- --fps 30
   ```
2. Or use high quality preset:
   ```bash
   npm run record -- --quality high
   ```

### Large File Size

**Issue:** Video file is too large

**Solution:**
1. Use medium or low quality:
   ```bash
   npm run record -- --quality medium
   ```
2. Reduce duration:
   ```bash
   npm run record:quick
   ```
3. Use custom FPS:
   ```bash
   npm run record -- --fps 15
   ```

### Recording Stops Early

**Issue:** Recording ends before completing the demo

**Solution:**
1. Check console for errors
2. Increase timeout in the script if navigation is slow
3. Use custom duration:
   ```bash
   npm run record -- --duration 240
   ```

## Tips for Best Results

### Before Recording

1. **Clear browser cache and cookies**
2. **Close unnecessary applications** (free up RAM and CPU)
3. **Disable notifications** (prevent interruptions)
4. **Check your development server** is running smoothly
5. **Test the demo scenario** manually first

### During Recording

1. **Don't interact with your computer** - let the script run
2. **Disable screen savers** and sleep mode
3. **Ensure stable internet connection** if fetching live data
4. **Monitor console output** for any warnings or errors

### After Recording

1. **Review the video immediately** to catch any issues
2. **Check narration markers** align with video content
3. **Add voiceover** using the narration file timestamps
4. **Edit and enhance** in your preferred video editor
5. **Export in appropriate format** for your platform

## Advanced Usage

### Custom Demo Scenarios

You can modify `scripts/record-demo.js` to add custom demo scenarios:

```javascript
// Add new scenario in the scenarios object
this.scenarios = {
  quick: this.quickDemo.bind(this),
  full: this.fullDemo.bind(this),
  custom: this.customDemo.bind(this),
  myCustomDemo: this.myCustomDemo.bind(this), // Add here
};

// Implement the scenario
async myCustomDemo() {
  await this.addNarration("My custom opening");
  await this.wait(5);
  // ... your custom actions
}
```

### Integration with CI/CD

For automated demo generation in CI/CD pipelines:

```yaml
# .github/workflows/demo-recording.yml
- name: Record Demo
  run: |
    npm install
    npm run dev &
    sleep 10  # Wait for server
    npm run record:quick -- --headless
```

### Batch Recording

Record multiple versions at once:

```bash
#!/bin/bash
# record-all.sh

echo "Recording quick demo..."
npm run record:quick -- --quality high

echo "Recording full demo..."
npm run record:full -- --quality high

echo "Recording custom demo..."
npm run record -- --mode custom --duration 120 --quality medium

echo "All recordings complete!"
```

## Video Editing Recommendations

### Recommended Tools

1. **DaVinci Resolve** (Free, Professional)
   - Import video and narration markers
   - Add voiceover with precise timing
   - Color correction and effects
   - Export in various formats

2. **iMovie** (macOS, Free)
   - Simple editing interface
   - Good for basic cuts and transitions
   - Easy voiceover recording

3. **Premiere Pro** (Professional)
   - Advanced editing features
   - Multi-track audio/video
   - Professional effects

### Editing Workflow

1. **Import the video** into your editor
2. **Import the narration markers** file
3. **Record voiceover** using the timing marks
4. **Add transitions** between scenes (optional)
5. **Color correction** if needed
6. **Add title cards**:
   - Opening: "Enterprise CIA"
   - Features: API names and descriptions
   - Closing: Contact/website info
7. **Add background music** (optional, low volume)
8. **Export settings**:
   - Format: MP4 (H.264)
   - Resolution: 1920x1080 or 1280x720
   - Frame rate: Match original (30fps or 15fps)
   - Bitrate: 8-10 Mbps for high quality

## FAQ

**Q: Can I record without Chrome?**
A: No, the script requires Chrome for Puppeteer. However, you can modify it to use Chromium.

**Q: Can I record in 4K?**
A: Yes, modify the resolution in the script, but note this will significantly increase file size.

**Q: How do I add my own narration?**
A: Use the narration markers file as a guide and record audio in your video editor, syncing with the timestamps.

**Q: Can I pause and resume recording?**
A: No, each recording is a single continuous session. Record multiple shorter clips instead.

**Q: Why use screenshots instead of direct screen recording?**
A: Screenshots provide reliable cross-platform recording, consistent frame rates, and easier post-processing.

**Q: Can I customize the demo actions?**
A: Yes, edit the demo scenario methods in `scripts/record-demo.js`.

**Q: How do I record a specific page or feature?**
A: Use custom mode with a specific URL:
   ```bash
   npm run record -- --mode custom --url http://localhost:3000/research
   ```

## Support

For issues or questions:
1. Check the console output for error messages
2. Review this guide's Troubleshooting section
3. Verify all prerequisites are installed
4. Check that your development server is running
5. Try with default settings first before customizing

## Summary of Commands

```bash
# Quick commands
npm run record:quick          # 60s quick demo
npm run record:full           # 180s full demo
npm run record:help           # Show help

# Custom recording
npm run record -- [options]

# Common examples
npm run record -- --mode full --quality high
npm run record -- --mode quick --fps 30
npm run record -- --mode custom --duration 120
npm run record -- --quality medium --no-cleanup
```

Happy recording! 🎥
