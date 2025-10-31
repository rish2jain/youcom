#!/bin/bash

# Create Demo Video from Screenshots
# Compiles screenshots into a video following the demo script timing

set -e

echo "🎥 Creating Demo Video from Screenshots"
echo "======================================"

# Check if ffmpeg is installed (for video recording)
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️  ffmpeg is not installed - video recording will be disabled"
    echo "   Install with: brew install ffmpeg (macOS) or apt-get install ffmpeg (Linux)"
    echo "   Demo will continue with screenshots only"
else
    echo "✅ ffmpeg is available for video recording"
fi

# Check if screenshots directory exists
if [ ! -d "demo_screenshots" ]; then
    echo "❌ demo_screenshots directory not found."
    echo "   Run the demo automation first: npm run demo:record"
    exit 1
fi

# Count screenshots
screenshot_count=$(ls demo_screenshots/*.png 2>/dev/null | wc -l)
if [ "$screenshot_count" -eq 0 ]; then
    echo "❌ No screenshots found in demo_screenshots/"
    echo "   Run the demo automation first: npm run demo:record"
    exit 1
fi

echo "✅ Found $screenshot_count screenshots"

# Create video directory
mkdir -p demo_videos

# Video settings
OUTPUT_VIDEO="demo_videos/enterprise_cia_demo_$(date +%Y%m%d_%H%M%S).mp4"
FRAMERATE=0.5  # 0.5 fps = 2 seconds per screenshot

echo "🎬 Creating video with $screenshot_count screenshots at $FRAMERATE fps..."

# Create video from screenshots
ffmpeg -y \
    -framerate $FRAMERATE \
    -pattern_type glob \
    -i 'demo_screenshots/*.png' \
    -c:v libx264 \
    -pix_fmt yuv420p \
    -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2" \
    "$OUTPUT_VIDEO"

echo "✅ Video created: $OUTPUT_VIDEO"

# Create a faster version for quick review
QUICK_VIDEO="demo_videos/enterprise_cia_demo_quick_$(date +%Y%m%d_%H%M%S).mp4"
QUICK_FRAMERATE=2  # 2 fps = 0.5 seconds per screenshot

echo "🎬 Creating quick review version at $QUICK_FRAMERATE fps..."

ffmpeg -y \
    -framerate $QUICK_FRAMERATE \
    -pattern_type glob \
    -i 'demo_screenshots/*.png' \
    -c:v libx264 \
    -pix_fmt yuv420p \
    -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2" \
    "$QUICK_VIDEO"

echo "✅ Quick video created: $QUICK_VIDEO"

# Get video duration
duration=$(ffprobe -v quiet -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$OUTPUT_VIDEO")
duration_formatted=$(printf "%.1f" "$duration")

echo ""
echo "🎉 Demo Video Creation Complete!"
echo "==============================="
echo ""
echo "Videos created:"
echo "  📹 Main demo: $OUTPUT_VIDEO (${duration_formatted}s)"
echo "  ⚡ Quick review: $QUICK_VIDEO"
echo ""
echo "Next steps:"
echo "1. Review the video to ensure it follows UPDATED_DEMO_SCRIPT.md"
echo "2. Add voiceover using your preferred video editing software"
echo "3. Adjust timing if needed (current: 2 seconds per screenshot)"
echo ""
echo "Demo script timing guide:"
echo "- THE HOOK: 30 seconds"
echo "- THE PROBLEM: 90 seconds"
echo "- THE SOLUTION: 90 seconds"
echo "- ENTERPRISE DEMO: 90 seconds"
echo "- INDIVIDUAL DEMO: 60 seconds"
echo "- RESULTS: 45 seconds"
echo "- TECHNICAL: 45 seconds"
echo "- MARKET: 30 seconds"
echo "- WHY THIS WINS: 60 seconds"
echo "- THE CLOSE: 30 seconds"
echo ""
echo "Total target: 9 minutes"