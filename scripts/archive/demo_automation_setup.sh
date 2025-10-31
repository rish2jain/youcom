#!/bin/bash

# Demo Automation Setup Script
# Sets up everything needed for automated demo recording

set -e

echo "🚀 Setting up Enterprise CIA Demo Automation"
echo "============================================="

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm first."
    exit 1
fi

echo "✅ Node.js and npm are available"

# Install Puppeteer if not already installed
echo "📦 Installing Puppeteer..."
npm install puppeteer --save-dev

# Create demo directories
echo "📁 Creating demo directories..."
mkdir -p demo_screenshots
mkdir -p demo_videos
mkdir -p demo_exports

# Make scripts executable
echo "🔧 Making scripts executable..."
chmod +x scripts/automated_demo.js
chmod +x scripts/automated_demo_chrome.js
chmod +x scripts/demo_automation_setup.sh

# Check if the application is running
echo "🔍 Checking if application is running..."
if curl -s http://localhost:3456 > /dev/null; then
    echo "✅ Application is running on http://localhost:3456"
else
    echo "⚠️  Application is not running on http://localhost:3456"
    echo "   Please start the application with: npm run dev"
    echo "   Then run the demo script with: npm run demo:record"
fi

echo ""
echo "🎬 Demo Automation Setup Complete!"
echo "=================================="
echo ""
echo "Available commands:"
echo "  npm run demo:record     - Run automated demo with video recording"
echo "  node scripts/automated_demo_cross_platform.js - Cross-platform video demo"
echo "  node scripts/automated_demo_chrome.js - Run guided demo with manual steps"
echo ""
echo "Before running the demo:"
echo "1. Make sure your application is running: npm run dev"
echo "2. Make sure your backend is running with demo data"
echo "3. Test that You.com APIs are working"
echo ""
echo "Demo will follow UPDATED_DEMO_SCRIPT.md exactly:"
echo "- Enterprise competitive monitoring (90 seconds)"
echo "- Individual company research (60 seconds)"
echo "- Technical architecture showcase"
echo ""
echo "Screenshots will be saved to: demo_screenshots/"
echo "Videos will be saved to: demo_videos/"
echo ""
echo "Ready to record your hackathon demo! 🎥"