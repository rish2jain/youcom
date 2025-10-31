#!/bin/bash

# Enterprise CIA Demo Runner
# Automatically detects capabilities and runs the best available demo

set -e

echo "🎬 Enterprise CIA Demo Runner"
echo "============================"

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
    echo "📦 Installing Puppeteer..."
    npm install puppeteer --save-dev
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

# Create directories
mkdir -p demo_screenshots demo_videos

echo ""
echo "🎯 Demo Options:"
echo "1. Full automated demo with video recording (recommended)"
echo "2. Cross-platform demo (works on all OS)"
echo "3. Guided demo with manual steps"
echo "4. Screenshots only"
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
echo "   📸 Screenshots: demo_screenshots/"
echo "   🎥 Videos: demo_videos/"
echo "   🎙️  Narration markers: demo_videos/narration_markers.txt"
echo ""
echo "Next steps:"
echo "1. Review the captured content"
echo "2. Use narration markers to add voiceover"
echo "3. Edit video to match UPDATED_DEMO_SCRIPT.md timing"