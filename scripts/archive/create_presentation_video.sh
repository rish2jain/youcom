#!/bin/bash

# Create Presentation Video from Demo Screenshots
# Follows the UPDATED_DEMO_SCRIPT.md timing and narration

set -e

echo "🎬 Creating Enterprise CIA Presentation Video"
echo "==========================================="

# Check if ffmpeg is available
if ! command -v ffmpeg &> /dev/null; then
    echo "❌ ffmpeg not found. Install with:"
    echo "   macOS: brew install ffmpeg"
    echo "   Linux: sudo apt-get install ffmpeg"
    exit 1
fi

# Check if screenshots exist
if [ ! -d "demo_screenshots" ] || [ -z "$(ls -A demo_screenshots/*.png 2>/dev/null)" ]; then
    echo "❌ No screenshots found in demo_screenshots/"
    echo "   Run the demo recording first"
    exit 1
fi

# Create output directory
mkdir -p demo_videos

# Video settings
OUTPUT_VIDEO="demo_videos/enterprise_cia_presentation_$(date +%Y%m%d_%H%M%S).mp4"
RESOLUTION="1920x1080"

echo "✅ Found screenshots, creating presentation video..."

# Create video with specific timing for each screenshot
# Following the demo script timing requirements - CORRECTED SCREENSHOTS

ffmpeg -y \
  -loop 1 -t 15 -i demo_screenshots/new_01_main_dashboard.png \
  -loop 1 -t 20 -i demo_screenshots/new_02_api_architecture.png \
  -loop 1 -t 15 -i demo_screenshots/new_03_threat_analysis.png \
  -loop 1 -t 12 -i demo_screenshots/new_04_insights_section.png \
  -loop 1 -t 10 -i demo_screenshots/new_05_quick_actions.png \
  -loop 1 -t 18 -i demo_screenshots/new_06_api_orchestration_demo.png \
  -loop 1 -t 15 -i demo_screenshots/new_07_api_pipeline.png \
  -loop 1 -t 15 -i demo_screenshots/new_08_live_intelligence_alert.png \
  -loop 1 -t 12 -i demo_screenshots/new_09_demo_options.png \
  -loop 1 -t 18 -i demo_screenshots/new_10_live_api_orchestration.png \
  -filter_complex "
    [0:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setpts=PTS-STARTPTS[v0];
    [1:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setpts=PTS-STARTPTS+15/TB[v1];
    [2:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setpts=PTS-STARTPTS+35/TB[v2];
    [3:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setpts=PTS-STARTPTS+50/TB[v3];
    [4:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setpts=PTS-STARTPTS+62/TB[v4];
    [5:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setpts=PTS-STARTPTS+72/TB[v5];
    [6:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setpts=PTS-STARTPTS+90/TB[v6];
    [7:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setpts=PTS-STARTPTS+105/TB[v7];
    [8:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setpts=PTS-STARTPTS+120/TB[v8];
    [9:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setpts=PTS-STARTPTS+135/TB[v9];
    [v0][v1][v2][v3][v4][v5][v6][v7][v8][v9]concat=n=10:v=1:a=0[outv]
  " \
  -map "[outv]" \
  -c:v libx264 \
  -pix_fmt yuv420p \
  -r 30 \
  "$OUTPUT_VIDEO"

# Get video duration
duration=$(ffprobe -v quiet -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$OUTPUT_VIDEO")
duration_formatted=$(printf "%.0f" "$duration")

echo ""
echo "🎉 Presentation Video Created!"
echo "============================="
echo ""
echo "📹 Video: $OUTPUT_VIDEO"
echo "⏱️  Duration: ${duration_formatted} seconds"
echo "📐 Resolution: $RESOLUTION"
echo ""
echo "Screenshot timing:"
echo "  00:00-00:15 - Main dashboard with threat scores (15s)"
echo "  00:15-00:35 - You.com API architecture showcase (20s)"  
echo "  00:35-00:50 - Threat analysis details (15s)"
echo "  00:50-01:02 - Insights and analytics (12s)"
echo "  01:02-01:12 - Quick actions (10s)"
echo "  01:12-01:30 - API orchestration demo (18s)"
echo "  01:30-01:45 - API pipeline visualization (15s)"
echo "  01:45-02:00 - Live intelligence alert (15s)"
echo "  02:00-02:12 - Demo options (12s)"
echo "  02:12-02:30 - Live API orchestration (18s)"
echo ""
echo "Next steps:"
echo "1. Add voiceover using demo_screenshots/narration_script.md"
echo "2. Adjust timing if needed for your presentation"
echo "3. Add transitions and effects in video editor"
echo ""
echo "Ready for your hackathon presentation! 🚀"