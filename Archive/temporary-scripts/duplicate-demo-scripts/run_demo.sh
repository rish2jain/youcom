#!/bin/bash

# Enterprise CIA Demo Runner
# Automatically detects capabilities and runs the best available demo

set -e

echo "🎬 Enterprise CIA Demo Runner"
echo "============================"

# Check if curl is available
if ! command -v curl >/dev/null 2>&1; then
    echo "❌ curl is required but not installed"
    echo "   Please install curl or check application manually"
    exit 1
fi

# Check if application is running
echo "🔍 Checking application status..."
if ! curl -s http://localhost:3000 > /dev/null; then
    echo "❌ Application is not running on http://localhost:3000"
    echo "   Please start the application first:"
    echo "   npm run dev"
    exit 1
fi

echo "✅ Application is running"

# Check if Node.js and npm are available
if ! command -v node &> /dev/null || ! command -v npm &> /dev/null; then
    echo "❌ Node.js or npm not found"
    exit 1
fi

# Check if Puppeteer is installed
if ! npm list puppeteer &> /dev/null; then
    echo "📦 Puppeteer is required for demo recording."
    echo "   Install it? (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "Installing Puppeteer..."
        npm install puppeteer --save-dev
    else
        echo "❌ Puppeteer is required. Install manually with: npm install puppeteer --save-dev"
        exit 1
    fi
fi

# Check if ffmpeg is available for video recording
VIDEO_AVAILABLE=false
if command -v ffmpeg &> /dev/null; then
    echo "✅ ffmpeg available - video recording enabled"
    VIDEO_AVAILABLE=true
else
    echo "⚠️  ffmpeg not available - screenshots only"
    echo "   Install ffmpeg for video recording:"
    echo "   macOS: brew install ffmpeg"
    echo "   Linux: sudo apt-get install ffmpeg"
    echo "   Windows: Download from https://ffmpeg.org/"
fi

# Define output directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUTPUT_DIR="$SCRIPT_DIR"

# Create directories
mkdir -p "$OUTPUT_DIR"/demo_screenshots "$OUTPUT_DIR"/demo_videos

echo ""
echo "🎯 Demo Options:"
echo "1. Full automated demo with video recording (recommended)"
echo "2. Cross-platform demo (works on all OS)"
echo ""

# Auto-select best option
if [ "$VIDEO_AVAILABLE" = true ]; then
    echo "🚀 Running full automated demo with video recording..."
    node scripts/automated_demo_with_video.js
else
    echo "🚀 Running cross-platform demo (screenshots + limited video)..."
    node scripts/automated_demo_cross_platform.js
fi

echo ""
echo "🎉 Demo completed!"
echo "📁 Check the following directories:"
echo "   📸 Screenshots: $OUTPUT_DIR/demo_screenshots/"
echo "   🎥 Videos: $OUTPUT_DIR/demo_videos/"
if [ -f "$OUTPUT_DIR/demo_videos/narration_markers.txt" ]; then
    echo "   🎙️  Narration markers: $OUTPUT_DIR/demo_videos/narration_markers.txt"
fi
echo ""
echo "Next steps:"
echo "1. Review the captured content"
echo "2. Use narration markers to add voiceover"
echo "3. Edit video to match UPDATED_DEMO_SCRIPT.md timing"