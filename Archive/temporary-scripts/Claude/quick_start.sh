#!/bin/bash

# Quick Start Script for Demo Recording
# This script helps you get started with demo recording quickly

set -e

echo "🎬 Enterprise CIA - Demo Recorder Setup"
echo "========================================"
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed"
    echo "   Please install Node.js from https://nodejs.org/"
    exit 1
fi

echo "✅ Node.js found: $(node --version)"

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed"
    exit 1
fi

echo "✅ npm found: $(npm --version)"

# Check if FFmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️  FFmpeg not found"
    echo ""
    echo "FFmpeg is required for video recording."
    echo "Install it with:"
    echo ""
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "  brew install ffmpeg"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "  sudo apt install ffmpeg"
    fi
    echo ""
    read -p "Continue without FFmpeg? (not recommended) [y/N]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✅ FFmpeg found: $(ffmpeg -version | head -n1)"
fi

echo ""
echo "📦 Installing dependencies..."
echo ""

# Install npm dependencies
if ! npm install; then
    echo "❌ Error: npm install failed" >&2
    echo "Please run 'npm install' manually to install required dependencies" >&2
    exit 1
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "🎯 Quick Start Options:"
echo ""
echo "1. Standard HD Recording (Recommended for hackathon):"
echo "   npm run record:hd"
echo ""
echo "2. Quick Test Recording (720p, fast):"
echo "   npm run record:quick"
echo ""
echo "3. Maximum Quality (macOS/Linux only):"
echo "   npm run record:system:ultra"
echo ""
echo "4. Custom Recording:"
echo "   node improved_demo_recorder.js --fps 60 --width 1920 --height 1080"
echo ""
echo "📚 Documentation:"
echo "   - Setup Guide: DEMO_RECORDER_GUIDE.md"
echo "   - Comparison: RECORDER_COMPARISON.md"
echo ""
echo "💡 Tip: Make sure your dashboard is running at http://localhost:3000"
echo "        before starting the recording!"
echo ""
read -p "Start a test recording now? [y/N]: " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🚀 Starting quick test recording..."
    npm run record:quick
fi
