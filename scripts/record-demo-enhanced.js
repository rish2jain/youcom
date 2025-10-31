#!/usr/bin/env node

/**
 * Enhanced Enterprise CIA Demo Recorder
 * Records a comprehensive demo by navigating and showcasing features
 * Uses scrolling and section highlighting instead of unreliable clicking
 */

const puppeteer = require("puppeteer");
const fs = require("fs");
const path = require("path");
const { exec } = require("child_process");
const { promisify } = require("util");

const execPromise = promisify(exec);

class EnhancedDemoRecorder {
  constructor(options = {}) {
    this.baseUrl = options.url || "http://localhost:3000?skip-onboarding=true";
    this.mode = options.mode || "full";
    this.fps = options.fps || 30;
    this.quality = options.quality || "high";
    this.outputDir = options.output || "demo_videos";
    this.cleanupScreenshots = options.cleanup !== false;
    this.headless = options.headless || false;

    // Quality presets (adjusted for reliable screenshot-based recording)
    this.qualityPresets = {
      low: { fps: 8, crf: 28, preset: "faster", resolution: { width: 1280, height: 720 } },
      medium: { fps: 12, crf: 23, preset: "medium", resolution: { width: 1280, height: 720 } },
      high: { fps: 15, crf: 18, preset: "slow", resolution: { width: 1920, height: 1080 } },
    };

    // Apply quality preset
    if (this.qualityPresets[this.quality]) {
      const preset = this.qualityPresets[this.quality];
      this.fps = options.fps || preset.fps;
      this.crf = preset.crf;
      this.preset = preset.preset;
      this.resolution = preset.resolution;
    }

    this.browser = null;
    this.page = null;
    this.screenshotDir = path.join(this.outputDir, "screenshots");
    this.frameCount = 0;
    this.recording = false;
    this.recordingInterval = null;
    this.narrations = [];
    this.startTime = null;
  }

  // Wait for specified seconds
  async wait(seconds) {
    await new Promise((resolve) => setTimeout(resolve, seconds * 1000));
  }

  // Add narration marker with timestamp
  async addNarration(text) {
    const elapsed = this.startTime ? (Date.now() - this.startTime) / 1000 : 0;
    const timestamp = new Date().toISOString();
    this.narrations.push({ time: Math.floor(elapsed), timestamp, text });
    console.log(`🎙️  [${Math.floor(elapsed)}s] ${text}`);
  }

  // Smooth scroll to reveal content
  async scrollToReveal(selector, description) {
    try {
      await this.page.evaluate((sel) => {
        const element = document.querySelector(sel);
        if (element) {
          element.scrollIntoView({ behavior: "smooth", block: "center" });
        }
      }, selector);
      await this.wait(1.5); // Wait for smooth scroll
      console.log(`✅ Revealed: ${description}`);
      return true;
    } catch (error) {
      console.log(`⚠️  Could not reveal: ${description}`);
      return false;
    }
  }

  // Scroll page by pixels
  async scrollBy(pixels, duration = 1) {
    await this.page.evaluate((px) => {
      window.scrollBy({ top: px, behavior: "smooth" });
    }, pixels);
    await this.wait(duration);
  }

  // Scroll to specific position
  async scrollTo(position, duration = 1) {
    await this.page.evaluate((pos) => {
      window.scrollTo({ top: pos, behavior: "smooth" });
    }, position);
    await this.wait(duration);
  }

  // Highlight element with animation
  async highlightElement(selector) {
    try {
      await this.page.evaluate((sel) => {
        const element = document.querySelector(sel);
        if (element) {
          element.style.outline = "4px solid #3B82F6";
          element.style.outlineOffset = "4px";
          setTimeout(() => {
            element.style.outline = "";
            element.style.outlineOffset = "";
          }, 2000);
        }
      }, selector);
      await this.wait(1);
      return true;
    } catch (error) {
      return false;
    }
  }

  // Setup directories
  async setupDirectories() {
    if (!fs.existsSync(this.outputDir)) {
      fs.mkdirSync(this.outputDir, { recursive: true });
    }
    if (!fs.existsSync(this.screenshotDir)) {
      fs.mkdirSync(this.screenshotDir, { recursive: true });
    }
  }

  // Detect Chrome executable path
  getChromePath() {
    const platform = process.platform;
    const paths = {
      darwin: [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
      ],
      linux: ["/usr/bin/google-chrome", "/usr/bin/chromium-browser", "/usr/bin/chromium"],
      win32: [
        "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
      ],
    };

    const platformPaths = paths[platform] || [];
    for (const chromePath of platformPaths) {
      if (fs.existsSync(chromePath)) {
        return chromePath;
      }
    }
    return null;
  }

  // Launch browser
  async launch() {
    console.log("🌐 Launching Chrome...");
    const chromePath = this.getChromePath();

    const launchOptions = {
      headless: this.headless ? "new" : false,
      args: [
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-dev-shm-usage",
        `--window-size=${this.resolution.width},${this.resolution.height}`,
      ],
    };

    if (chromePath) {
      launchOptions.executablePath = chromePath;
    }

    this.browser = await puppeteer.launch(launchOptions);
    this.page = await this.browser.newPage();
    await this.page.setViewport(this.resolution);
    console.log("✅ Chrome launched successfully");
  }

  // Navigate with better error handling
  async navigateTo(url, description) {
    console.log(`🌐 Navigating to: ${description}`);
    try {
      await this.page.goto(url, {
        waitUntil: "domcontentloaded",
        timeout: 30000,
      });
      await this.wait(2); // Extra time for rendering
      console.log(`✅ Loaded: ${description}`);
      return true;
    } catch (error) {
      console.log(`⚠️  Navigation failed: ${error.message}`);
      return false;
    }
  }

  // Start recording with more reliable frame capture
  async startRecording() {
    console.log(`\n🎥 Starting recording at ${this.fps} FPS...`);
    this.recording = true;
    this.startTime = Date.now();
    this.frameCount = 0;
    this.screenshotQueue = [];
    this.processingScreenshot = false;

    // Capture screenshots in a loop instead of setInterval for reliability
    this.captureLoop();

    console.log("✅ Recording started\n");
  }

  // Continuous capture loop
  async captureLoop() {
    const targetFrameTime = 1000 / this.fps;
    let lastFrameTime = Date.now();

    while (this.recording) {
      const now = Date.now();
      const elapsed = now - lastFrameTime;

      if (elapsed >= targetFrameTime) {
        try {
          const filename = path.join(
            this.screenshotDir,
            `frame_${String(this.frameCount).padStart(6, "0")}.png`
          );

          // Synchronous screenshot to ensure all frames are captured
          await this.page.screenshot({
            path: filename,
            type: 'png',
            fullPage: false,
            captureBeyondViewport: false,
            omitBackground: false
          });

          this.frameCount++;
          lastFrameTime = now - (elapsed - targetFrameTime); // Adjust for overshoot
        } catch (error) {
          // Continue recording even on errors
        }
      }

      // Adaptive delay to maintain frame rate
      const nextWait = Math.max(5, targetFrameTime - (Date.now() - lastFrameTime));
      await new Promise(resolve => setTimeout(resolve, nextWait));
    }
  }

  // Stop recording
  async stopRecording() {
    console.log("\n🛑 Stopping recording...");
    this.recording = false;

    // Wait a moment for any pending screenshots to complete
    await this.wait(0.5);

    const duration = this.startTime ? (Date.now() - this.startTime) / 1000 : 0;
    console.log(
      `📸 Captured ${this.frameCount} frames (${Math.floor(duration)} seconds)`
    );
    console.log("✅ Recording stopped\n");
  }

  // Full demonstration scenario
  async fullDemo() {
    await this.addNarration(
      "Welcome to Enterprise CIA - the complete competitive intelligence automation platform"
    );
    await this.wait(3);

    await this.addNarration(
      "Built exclusively for the You.com Hackathon, orchestrating all 4 You.com APIs"
    );
    await this.wait(3);

    // Scroll to show top alerts
    await this.addNarration(
      "The dashboard displays real-time competitive threats from your industry"
    );
    await this.scrollBy(300, 2);
    await this.wait(2);

    await this.addNarration(
      "Each threat is scored by severity - this OpenAI alert shows a 9.8/10 risk score"
    );
    await this.highlightElement(".border-red-200");
    await this.wait(2);

    // Scroll to recent intelligence
    await this.scrollBy(400, 2);
    await this.addNarration(
      "Recent intelligence reports show comprehensive analysis from over 400 sources"
    );
    await this.wait(2);

    await this.addNarration(
      "The News API monitors thousands of sources for competitive signals"
    );
    await this.wait(2);

    // Scroll to insights
    await this.scrollBy(400, 2);
    await this.addNarration(
      "Key insights reveal a 40% increase in competitor activity this week"
    );
    await this.wait(2);

    await this.addNarration(
      "The Search API enriches context with real-time market intelligence"
    );
    await this.wait(2);

    // Scroll to quick actions
    await this.scrollBy(300, 2);
    await this.addNarration(
      "Quick actions provide one-click access to monitoring, research, and analytics"
    );
    await this.wait(2);

    await this.addNarration(
      "Custom Agents analyze strategic impact using structured extraction"
    );
    await this.wait(2);

    // Scroll back to top smoothly
    await this.scrollTo(0, 2);
    await this.addNarration(
      "ARI synthesizes deep insights delivering results in under 5 minutes instead of days"
    );
    await this.wait(3);

    await this.addNarration(
      "With 85% accuracy and complete source provenance for every insight"
    );
    await this.wait(2);

    await this.addNarration(
      "Product managers save over 10 hours per week with automated intelligence"
    );
    await this.wait(3);

    await this.addNarration(
      "Built with production-grade architecture: async Python backend, Next.js frontend"
    );
    await this.wait(3);

    await this.addNarration(
      "Real-time updates via WebSocket, Redis caching, and circuit breaker resilience"
    );
    await this.wait(3);

    await this.addNarration(
      "Comprehensive test coverage at 85%, ready for enterprise deployment"
    );
    await this.wait(3);

    await this.addNarration(
      "Enterprise CIA - where You.com's four APIs revolutionize competitive intelligence"
    );
    await this.wait(3);

    await this.addNarration("Thank you for watching our demonstration");
    await this.wait(2);
  }

  // Quick demonstration scenario
  async quickDemo() {
    await this.addNarration("Enterprise CIA: Competitive Intelligence Automation");
    await this.wait(2);

    await this.addNarration("Real-time threat monitoring with all 4 You.com APIs");
    await this.scrollBy(300, 2);
    await this.wait(2);

    await this.addNarration("Comprehensive intelligence from 400+ sources");
    await this.scrollBy(400, 2);
    await this.wait(2);

    await this.addNarration("Automated insights save 10+ hours per week");
    await this.scrollBy(300, 2);
    await this.wait(2);

    await this.addNarration("Production-ready with 85% test coverage");
    await this.scrollTo(0, 2);
    await this.wait(2);

    await this.addNarration("Transform information overload into actionable intelligence");
    await this.wait(2);
  }

  // Custom demo based on duration
  async customDemo(duration) {
    const segments = Math.floor(duration / 10);
    for (let i = 0; i < segments; i++) {
      await this.addNarration(`Demonstrating Enterprise CIA features - segment ${i + 1}`);
      await this.scrollBy(200 + i * 100, 1);
      await this.wait(3);
    }
    await this.scrollTo(0, 1);
    await this.addNarration("Demo complete");
    await this.wait(2);
  }

  // Create video from screenshots
  async createVideo() {
    console.log("🎬 Creating video from screenshots...");
    const timestamp = new Date().toISOString().replace(/[:.]/g, "-").split("T")[0] +
                     "T" + new Date().toTimeString().split(" ")[0].replace(/:/g, "-");
    const outputFile = path.join(
      this.outputDir,
      `enterprise_cia_${this.mode}_${timestamp}.mp4`
    );

    console.log(`   Output: ${outputFile}`);

    const ffmpegCommand = `ffmpeg -framerate ${this.fps} -pattern_type glob -i "${this.screenshotDir}/frame_*.png" -c:v libx264 -crf ${this.crf} -preset ${this.preset} -pix_fmt yuv420p -y "${outputFile}"`;

    try {
      await execPromise(ffmpegCommand);
      console.log("✅ Video created successfully");

      // Save narration markers
      const narrationFile = path.join(this.outputDir, `narration_${this.mode}.txt`);
      const narrationText = this.narrations
        .map((n) => `[${n.time}s] ${n.timestamp}: ${n.text}`)
        .join("\n");
      fs.writeFileSync(narrationFile, narrationText);
      console.log(`📝 Narration markers saved: ${narrationFile}`);

      return outputFile;
    } catch (error) {
      console.error("❌ FFmpeg error:", error.message);
      throw error;
    }
  }

  // Cleanup screenshots
  async cleanup() {
    if (this.cleanupScreenshots) {
      console.log("\n🧹 Cleaning up screenshots...");
      const files = fs.readdirSync(this.screenshotDir);
      files.forEach((file) => {
        fs.unlinkSync(path.join(this.screenshotDir, file));
      });
      fs.rmdirSync(this.screenshotDir);
      console.log(`✅ Deleted ${files.length} screenshot files`);
    }
  }

  // Close browser
  async close() {
    console.log("\n🔒 Closing browser...");
    if (this.browser) {
      await this.browser.close();
      console.log("✅ Browser closed\n");
    }
  }

  // Main recording workflow
  async record() {
    try {
      console.log("\n🚀 Enterprise CIA Demo Recorder");
      console.log(`   Mode: ${this.mode} | Quality: ${this.quality} | FPS: ${this.fps}\n`);
      console.log(`   Platform: ${process.platform}\n`);

      await this.setupDirectories();
      await this.launch();

      const success = await this.navigateTo(this.baseUrl, "Enterprise CIA Dashboard");
      if (!success) {
        throw new Error("Failed to load application");
      }

      await this.startRecording();

      // Run appropriate demo scenario
      console.log(`🎬 Running ${this.mode.charAt(0).toUpperCase() + this.mode.slice(1)} Demo...\n`);

      if (this.mode === "quick") {
        await this.quickDemo();
      } else if (this.mode === "full") {
        await this.fullDemo();
      } else if (this.mode === "custom") {
        const duration = process.argv.includes("--duration")
          ? parseInt(process.argv[process.argv.indexOf("--duration") + 1])
          : 60;
        await this.customDemo(duration);
      }

      await this.stopRecording();
      const videoFile = await this.createVideo();
      await this.cleanup();

      console.log(`\n🎉 Recording complete!`);
      console.log(`   Video: ${videoFile}`);
      console.log(`   Narration: ${path.join(this.outputDir, `narration_${this.mode}.txt`)}\n`);
    } catch (error) {
      console.error("\n❌ Recording failed:", error.message);
      throw error;
    } finally {
      await this.close();
    }
  }
}

// CLI argument parsing
function parseArgs() {
  const args = process.argv.slice(2);
  const options = {
    mode: "full",
    quality: "high",
    url: null,
    output: "demo_videos",
    cleanup: true,
    headless: false,
    fps: null,
  };

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    switch (arg) {
      case "--mode":
        options.mode = args[++i];
        break;
      case "--quality":
        options.quality = args[++i];
        break;
      case "--url":
        options.url = args[++i];
        break;
      case "--output":
        options.output = args[++i];
        break;
      case "--no-cleanup":
        options.cleanup = false;
        break;
      case "--headless":
        options.headless = true;
        break;
      case "--fps":
        options.fps = parseInt(args[++i]);
        break;
      case "--help":
        console.log(`
Enhanced Enterprise CIA Demo Recorder

Usage: node record-demo-enhanced.js [options]

Options:
  --mode <quick|full|custom>    Recording mode (default: full)
  --quality <low|medium|high>   Video quality preset (default: high)
  --fps <number>                Frames per second (overrides quality preset)
  --url <url>                   Application URL (default: http://localhost:3000)
  --output <dir>                Output directory (default: demo_videos)
  --no-cleanup                  Keep screenshot frames after video creation
  --headless                    Run browser in headless mode
  --duration <seconds>          Duration for custom mode (default: 60)
  --help                        Show this help message

Examples:
  node record-demo-enhanced.js --mode quick
  node record-demo-enhanced.js --mode full --quality high
  node record-demo-enhanced.js --mode custom --duration 90
  node record-demo-enhanced.js --headless --no-cleanup
        `);
        process.exit(0);
    }
  }

  return options;
}

// Run if called directly
if (require.main === module) {
  const options = parseArgs();
  const recorder = new EnhancedDemoRecorder(options);
  recorder.record().catch((error) => {
    console.error("\n💥 Fatal error:", error);
    process.exit(1);
  });
}

module.exports = EnhancedDemoRecorder;
