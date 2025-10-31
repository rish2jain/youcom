#!/usr/bin/env node

/**
 * Enterprise CIA Demo Recorder
 * Comprehensive end-to-end video recording solution using Puppeteer
 *
 * Features:
 * - Multiple recording modes (screenshots, direct video)
 * - Cross-platform support (macOS, Linux, Windows)
 * - Configurable demo scenarios
 * - Progress tracking and narration markers
 * - Error handling with graceful fallbacks
 * - High-quality video output
 *
 * Usage:
 *   node scripts/record-demo.js [options]
 *
 * Options:
 *   --mode <quick|full|custom>     Demo mode (default: full)
 *   --duration <seconds>           Recording duration (default: 180)
 *   --fps <number>                 Frames per second (default: 15)
 *   --quality <low|medium|high>    Video quality (default: high)
 *   --url <url>                    Custom URL to record (default: localhost:3000)
 *   --output <path>                Output directory (default: demo_videos)
 *   --no-cleanup                   Keep screenshot frames after video creation
 *   --headless                     Run browser in headless mode
 *   --help                         Show this help message
 */

const puppeteer = require("puppeteer");
const fs = require("fs").promises;
const path = require("path");
const { spawn } = require("child_process");
const os = require("os");

class EnterpriseCIARecorder {
  constructor(options = {}) {
    // Configuration
    this.mode = options.mode || "full";
    this.duration = options.duration || 180;
    this.fps = options.fps || 15;
    this.quality = options.quality || "high";
    this.baseUrl = options.url || "http://localhost:3000?skip-onboarding=true";
    this.outputDir = options.output || "demo_videos";
    this.cleanup = options.cleanup !== false;
    this.headless = options.headless || false;

    // State
    this.browser = null;
    this.page = null;
    this.screenshotsDir = path.join(this.outputDir, "screenshots");
    this.videoPath = null;
    this.platform = os.platform();
    this.screenshotCount = 0;
    this.isRecording = false;
    this.recordingInterval = null;
    this.narrationMarkers = [];

    // Quality presets
    this.qualityPresets = {
      low: {
        fps: 10,
        crf: 28,
        preset: "faster",
        resolution: { width: 1280, height: 720 },
      },
      medium: {
        fps: 15,
        crf: 23,
        preset: "medium",
        resolution: { width: 1280, height: 720 },
      },
      high: {
        fps: 30,
        crf: 18,
        preset: "slow",
        resolution: { width: 1920, height: 1080 },
      },
    };

    // Apply quality preset
    const preset = this.qualityPresets[this.quality];
    this.fps = options.fps || preset.fps;
    this.crf = preset.crf;
    this.ffmpegPreset = preset.preset;
    this.resolution = preset.resolution;

    // Demo scenarios
    this.scenarios = {
      quick: this.quickDemo.bind(this),
      full: this.fullDemo.bind(this),
      custom: this.customDemo.bind(this),
    };
  }

  /**
   * Get Chrome executable path for current platform
   */
  getChromePath() {
    const paths = {
      darwin: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
      win32: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
      linux: "/usr/bin/google-chrome",
    };
    return paths[this.platform] || null;
  }

  /**
   * Initialize browser and create necessary directories
   */
  async initialize() {
    console.log(`\n🚀 Enterprise CIA Demo Recorder`);
    console.log(
      `   Mode: ${this.mode} | Quality: ${this.quality} | Duration: ${this.duration}s`
    );
    console.log(`   Platform: ${this.platform} | FPS: ${this.fps}\n`);

    // Create directories
    await fs.mkdir(this.outputDir, { recursive: true });
    await fs.mkdir(this.screenshotsDir, { recursive: true });

    const chromePath = this.getChromePath();

    try {
      console.log("🌐 Launching Chrome...");

      this.browser = await puppeteer.launch({
        executablePath: chromePath,
        headless: this.headless,
        defaultViewport: this.resolution,
        args: [
          "--no-sandbox",
          "--disable-setuid-sandbox",
          "--disable-dev-shm-usage",
          "--disable-web-security",
          `--window-size=${this.resolution.width},${this.resolution.height}`,
          "--window-position=50,50",
          "--no-first-run",
          "--disable-default-apps",
          "--disable-popup-blocking",
          "--disable-translate",
          "--disable-background-timer-throttling",
          "--disable-renderer-backgrounding",
          "--disable-backgrounding-occluded-windows",
        ],
        timeout: 30000,
      });

      this.page = await this.browser.newPage();
      await this.page.setViewport(this.resolution);

      // Add error handlers
      this.page.on("error", (error) => {
        console.log("⚠️  Page error:", error.message);
      });

      this.page.on("pageerror", (error) => {
        console.log("⚠️  Page script error:", error.message);
      });

      console.log("✅ Chrome launched successfully");
      return true;
    } catch (error) {
      console.error("❌ Chrome launch failed:", error.message);
      return false;
    }
  }

  /**
   * Start screenshot-based recording
   */
  async startRecording() {
    console.log(`\n🎥 Starting recording at ${this.fps} FPS...`);
    this.isRecording = true;
    this.screenshotCount = 0;
    const startTime = Date.now();

    this.recordingInterval = setInterval(async () => {
      if (this.isRecording && this.page) {
        try {
          const filename = `frame_${String(this.screenshotCount).padStart(
            6,
            "0"
          )}.png`;
          const filepath = path.join(this.screenshotsDir, filename);

          await this.page.screenshot({
            path: filepath,
            type: "png",
            fullPage: false,
          });

          this.screenshotCount++;

          // Progress indicator every 5 seconds
          if (this.screenshotCount % (this.fps * 5) === 0) {
            const elapsed = Math.floor((Date.now() - startTime) / 1000);
            const progress = Math.floor((elapsed / this.duration) * 100);
            console.log(
              `📸 Recording: ${elapsed}s / ${this.duration}s (${progress}%)`
            );
          }
        } catch (error) {
          console.log(`⚠️  Screenshot error: ${error.message}`);
        }
      }
    }, 1000 / this.fps);

    console.log("✅ Recording started");
    return true;
  }

  /**
   * Stop recording
   */
  async stopRecording() {
    if (this.recordingInterval) {
      console.log("\n🛑 Stopping recording...");
      clearInterval(this.recordingInterval);
      this.recordingInterval = null;
      this.isRecording = false;

      const totalSeconds = Math.floor(this.screenshotCount / this.fps);
      console.log(
        `📸 Captured ${this.screenshotCount} frames (${totalSeconds} seconds)`
      );
      console.log("✅ Recording stopped");
      return true;
    }
    return false;
  }

  /**
   * Create video from screenshots using ffmpeg
   */
  async createVideo() {
    const timestamp = new Date()
      .toISOString()
      .replace(/[:.]/g, "-")
      .slice(0, 19);
    this.videoPath = path.join(
      this.outputDir,
      `enterprise_cia_${this.mode}_${timestamp}.mp4`
    );

    console.log("\n🎬 Creating video from screenshots...");
    console.log(`   Output: ${this.videoPath}`);

    const ffmpegArgs = [
      "-framerate",
      this.fps.toString(),
      "-i",
      path.join(this.screenshotsDir, "frame_%06d.png"),
      "-c:v",
      "libx264",
      "-preset",
      this.ffmpegPreset,
      "-crf",
      this.crf.toString(),
      "-pix_fmt",
      "yuv420p",
      "-vf",
      `scale=${this.resolution.width}:${this.resolution.height}`,
      "-y",
      this.videoPath,
    ];

    return new Promise((resolve, reject) => {
      const ffmpeg = spawn("ffmpeg", ffmpegArgs, {
        stdio: ["ignore", "pipe", "pipe"],
      });

      let lastProgress = 0;
      ffmpeg.stderr.on("data", (data) => {
        const message = data.toString();
        // Parse ffmpeg progress
        if (message.includes("frame=")) {
          const frameMatch = message.match(/frame=\s*(\d+)/);
          if (frameMatch) {
            const currentFrame = parseInt(frameMatch[1]);
            const progress = Math.floor(
              (currentFrame / this.screenshotCount) * 100
            );
            if (progress > lastProgress && progress % 10 === 0) {
              console.log(`   Progress: ${progress}%`);
              lastProgress = progress;
            }
          }
        }
      });

      ffmpeg.on("close", (code) => {
        if (code === 0) {
          console.log("✅ Video created successfully");
          resolve(true);
        } else {
          console.error(`❌ FFmpeg failed with code ${code}`);
          reject(new Error(`FFmpeg failed with code ${code}`));
        }
      });

      ffmpeg.on("error", (error) => {
        console.error("❌ FFmpeg error:", error.message);
        reject(error);
      });
    });
  }

  /**
   * Cleanup screenshot files
   */
  async cleanupScreenshots() {
    if (!this.cleanup) {
      console.log("⏭️  Skipping screenshot cleanup (--no-cleanup flag)");
      return;
    }

    console.log("\n🧹 Cleaning up screenshots...");
    try {
      const files = await fs.readdir(this.screenshotsDir);
      let deletedCount = 0;
      for (const file of files) {
        if (file.endsWith(".png")) {
          await fs.unlink(path.join(this.screenshotsDir, file));
          deletedCount++;
        }
      }
      console.log(`✅ Deleted ${deletedCount} screenshot files`);
    } catch (error) {
      console.log("⚠️  Cleanup error:", error.message);
    }
  }

  /**
   * Save narration markers to file
   */
  async saveNarrationMarkers() {
    const markerFile = path.join(this.outputDir, `narration_${this.mode}.txt`);
    const content = this.narrationMarkers
      .map(
        ({ timestamp, text, elapsed }) => `[${elapsed}s] ${timestamp}: ${text}`
      )
      .join("\n");

    await fs.writeFile(markerFile, content);
    console.log(`📝 Narration markers saved: ${markerFile}`);
  }

  /**
   * Utility: Wait for specified seconds
   */
  async wait(seconds) {
    await new Promise((resolve) => setTimeout(resolve, seconds * 1000));
  }

  /**
   * Utility: Add narration marker with timestamp
   */
  async addNarration(text) {
    const timestamp = new Date().toISOString();
    const elapsed = Math.floor(this.screenshotCount / this.fps);
    this.narrationMarkers.push({ timestamp, text, elapsed });
    console.log(`🎙️  [${elapsed}s] ${text}`);
  }

  /**
   * Utility: Navigate to URL
   */
  async navigateTo(url, description) {
    console.log(`🌐 Navigating to: ${description}`);
    try {
      await this.page.goto(url, {
        waitUntil: "domcontentloaded",
        timeout: 30000,
      });
      // Give the page extra time to fully render
      await this.wait(3);
      console.log(`✅ Loaded: ${description}`);
      return true;
    } catch (error) {
      console.log(`⚠️  Navigation failed: ${error.message}`);
      return false;
    }
  }

  /**
   * Utility: Scroll page
   */
  async scroll(direction = "down", amount = 300) {
    try {
      await this.page.evaluate(
        (dir, amt) => {
          const scrollAmount = dir === "down" ? amt : -amt;
          window.scrollBy({ top: scrollAmount, behavior: "smooth" });
        },
        direction,
        amount
      );
      await this.wait(1);
    } catch (error) {
      console.log(`⚠️  Scroll error: ${error.message}`);
    }
  }

  /**
   * Utility: Click element
   */
  async click(selector, description, timeout = 5000) {
    try {
      console.log(`🖱️  Clicking: ${description}`);
      await this.page.waitForSelector(selector, { timeout });
      await this.page.click(selector);
      await this.wait(2);
      console.log(`✅ Clicked: ${description}`);
      return true;
    } catch (error) {
      console.log(`⚠️  Click failed: ${error.message}`);
      return false;
    }
  }

  /**
   * Demo Scenario: Quick (60 seconds)
   */
  async quickDemo() {
    console.log("\n🎬 Running Quick Demo (60s)...\n");

    await this.addNarration(
      "Welcome to Enterprise CIA - Competitive Intelligence Automated"
    );
    await this.wait(5);

    await this.addNarration(
      "Powered by all four You.com APIs working together"
    );
    await this.wait(8);

    await this.scroll("down", 400);
    await this.addNarration("Real-time threat detection with 85% accuracy");
    await this.wait(8);

    await this.scroll("down", 400);
    await this.addNarration("Comprehensive intelligence from 400+ sources");
    await this.wait(8);

    await this.scroll("down", 400);
    await this.addNarration("Saves product managers 10+ hours per week");
    await this.wait(8);

    await this.scroll("up", 200);
    await this.addNarration("Production-ready with 85% test coverage");
    await this.wait(8);

    await this.addNarration("Thank you for watching");
    await this.wait(7);
  }

  /**
   * Demo Scenario: Full (180 seconds)
   */
  async fullDemo() {
    console.log("\n🎬 Running Full Demo (180s)...\n");

    // Section 1: Introduction (30s)
    await this.addNarration(
      "Welcome to Enterprise CIA - the complete competitive intelligence platform"
    );
    await this.wait(5);

    await this.addNarration(
      "This platform orchestrates all four You.com APIs: News, Search, Custom Agents, and ARI"
    );
    await this.wait(10);

    await this.scroll("down", 300);
    await this.addNarration(
      "Let's explore how these APIs work together to deliver real-time competitive intelligence"
    );
    await this.wait(10);

    // Section 2: Features Overview (60s)
    await this.scroll("down", 400);
    await this.addNarration(
      "The News API continuously monitors thousands of sources for competitive signals"
    );
    await this.wait(10);

    await this.scroll("down", 400);
    await this.addNarration(
      "Search API enriches context with market data and background information"
    );
    await this.wait(10);

    await this.scroll("down", 400);
    await this.addNarration(
      "Custom Agents analyze strategic impact using structured extraction"
    );
    await this.wait(10);

    await this.scroll("down", 400);
    await this.addNarration(
      "ARI synthesizes deep insights from over 400 sources per report"
    );
    await this.wait(10);

    // Try to interact with the dashboard
    const clicked = await this.click(
      'button, a[href*="research"], .cta-button',
      "Interactive element"
    );
    if (clicked) {
      await this.addNarration(
        "Demonstrating seamless navigation and API integration"
      );
      await this.wait(10);
    }

    // Section 3: Value Proposition (45s)
    await this.scroll("up", 200);
    await this.addNarration(
      "This intelligent orchestration delivers results in under 5 minutes instead of days"
    );
    await this.wait(10);

    await this.addNarration(
      "With 85% accuracy and complete source provenance for every insight"
    );
    await this.wait(10);

    await this.scroll("down", 300);
    await this.addNarration(
      "Product managers save over 10 hours per week with automated intelligence"
    );
    await this.wait(10);

    // Section 4: Technical Excellence (45s)
    await this.addNarration(
      "Built with production-grade architecture: async Python backend, Next.js frontend"
    );
    await this.wait(10);

    await this.scroll("down", 200);
    await this.addNarration(
      "Real-time progress updates via WebSocket, Redis caching, and circuit breakers"
    );
    await this.wait(10);

    await this.addNarration(
      "Comprehensive test coverage at 85%, ready for enterprise deployment"
    );
    await this.wait(10);

    await this.scroll("up", 500);
    await this.addNarration(
      "Enterprise CIA - where You.com's four APIs revolutionize competitive intelligence"
    );
    await this.wait(10);

    await this.addNarration("Thank you for watching our demonstration");
    await this.wait(5);
  }

  /**
   * Demo Scenario: Custom (user-defined duration)
   */
  async customDemo() {
    console.log("\n🎬 Running Custom Demo...\n");

    await this.addNarration("Starting custom demo recording");
    await this.wait(5);

    // Just record the dashboard for the specified duration
    const remainingTime = this.duration - 10; // Reserve 5s at start and 5s at end
    const intervals = Math.floor(remainingTime / 15); // 15-second intervals

    for (let i = 0; i < intervals; i++) {
      await this.scroll("down", 300);
      await this.wait(7);
      await this.scroll("up", 100);
      await this.wait(8);
    }

    await this.addNarration("Custom demo recording complete");
    await this.wait(5);
  }

  /**
   * Run the complete recording workflow
   */
  async run() {
    const initialized = await this.initialize();

    if (!initialized) {
      console.log("❌ Initialization failed");
      return false;
    }

    try {
      // Navigate to the application
      const loaded = await this.navigateTo(
        this.baseUrl,
        "Enterprise CIA Dashboard"
      );
      if (!loaded) {
        console.log("❌ Failed to load application");
        return false;
      }

      // Wait for page to settle
      await this.wait(3);

      // Start recording
      const recordingStarted = await this.startRecording();
      if (!recordingStarted) {
        console.log("❌ Failed to start recording");
        return false;
      }

      // Run the selected demo scenario
      const scenario = this.scenarios[this.mode];
      if (scenario) {
        await scenario();
      } else {
        console.log(`⚠️  Unknown mode: ${this.mode}, running full demo`);
        await this.fullDemo();
      }

      // Stop recording
      await this.stopRecording();

      // Create video from screenshots
      await this.createVideo();

      // Save narration markers
      await this.saveNarrationMarkers();

      // Cleanup screenshots
      await this.cleanupScreenshots();

      return true;
    } catch (error) {
      console.error("\n❌ Recording failed:", error);
      return false;
    } finally {
      if (this.browser) {
        console.log("\n🔒 Closing browser...");
        try {
          await this.browser.close();
        } catch (error) {
          console.log("⚠️  Error closing browser:", error.message);
        }
      }
    }
  }

  /**
   * Display summary of recording
   */
  async displaySummary() {
    console.log("\n" + "=".repeat(60));
    console.log("🎉 Recording Complete!");
    console.log("=".repeat(60));

    if (this.videoPath) {
      const stats = await fs.stat(this.videoPath);
      const sizeMB = (stats.size / 1024 / 1024).toFixed(2);
      console.log(`\n📹 Video: ${this.videoPath}`);
      console.log(`   Size: ${sizeMB} MB`);
      console.log(
        `   Resolution: ${this.resolution.width}x${this.resolution.height}`
      );
      console.log(`   FPS: ${this.fps}`);
      console.log(`   Quality: ${this.quality}`);
    }

    const narrationFile = path.join(
      this.outputDir,
      `narration_${this.mode}.txt`
    );
    console.log(`\n📝 Narration: ${narrationFile}`);
    console.log(`   Markers: ${this.narrationMarkers.length}`);

    console.log("\n💡 Next steps:");
    console.log("   1. Review the video");
    console.log("   2. Add voiceover using narration markers");
    console.log("   3. Edit and enhance in your video editor");

    console.log("\n✨ Ready for your presentation!\n");
  }
}

/**
 * Parse command-line arguments
 */
function parseArgs() {
  const args = process.argv.slice(2);
  const options = {
    mode: "full",
    duration: 180,
    fps: null,
    quality: "high",
    url: null,
    output: "demo_videos",
    cleanup: true,
    headless: false,
  };

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    const nextArg = args[i + 1];

    switch (arg) {
      case "--mode":
        options.mode = nextArg;
        i++;
        break;
      case "--duration":
        options.duration = parseInt(nextArg);
        i++;
        break;
      case "--fps":
        options.fps = parseInt(nextArg);
        i++;
        break;
      case "--quality":
        options.quality = nextArg;
        i++;
        break;
      case "--url":
        options.url = nextArg;
        i++;
        break;
      case "--output":
        options.output = nextArg;
        i++;
        break;
      case "--no-cleanup":
        options.cleanup = false;
        break;
      case "--headless":
        options.headless = true;
        break;
      case "--help":
        showHelp();
        process.exit(0);
        break;
    }
  }

  // Adjust duration based on mode if not explicitly set
  if (!args.includes("--duration")) {
    if (options.mode === "quick") options.duration = 60;
    else if (options.mode === "full") options.duration = 180;
  }

  return options;
}

/**
 * Show help message
 */
function showHelp() {
  console.log(`
Enterprise CIA Demo Recorder
============================

Usage:
  node scripts/record-demo.js [options]

Options:
  --mode <quick|full|custom>     Demo mode (default: full)
                                 - quick: 60s overview
                                 - full: 180s comprehensive demo
                                 - custom: user-defined duration

  --duration <seconds>           Recording duration (default: 180)
  --fps <number>                 Frames per second (default: varies by quality)
  --quality <low|medium|high>    Video quality preset (default: high)
                                 - low: 720p, 10fps, CRF 28
                                 - medium: 720p, 15fps, CRF 23
                                 - high: 1080p, 30fps, CRF 18

  --url <url>                    Custom URL to record (default: localhost:3000)
  --output <path>                Output directory (default: demo_videos)
  --no-cleanup                   Keep screenshot frames after video creation
  --headless                     Run browser in headless mode
  --help                         Show this help message

Examples:
  # Quick 60-second demo in high quality
  node scripts/record-demo.js --mode quick --quality high

  # Full 3-minute demo with custom FPS
  node scripts/record-demo.js --mode full --fps 24

  # Custom duration demo
  node scripts/record-demo.js --mode custom --duration 120

  # Record from different URL
  node scripts/record-demo.js --url http://localhost:3000

  # Keep screenshots for manual editing
  node scripts/record-demo.js --no-cleanup
`);
}

/**
 * Main execution
 */
async function main() {
  const options = parseArgs();

  // Validate dependencies
  try {
    await fs.access(path.join(__dirname, "..", "node_modules", "puppeteer"));
  } catch (error) {
    console.error("❌ Puppeteer not found. Install dependencies:");
    console.error("   npm install");
    process.exit(1);
  }

  // Check ffmpeg
  const { spawn: checkSpawn } = require("child_process");

  const checkFFmpeg = () => {
    return new Promise((resolve) => {
      const ffmpegCheck = checkSpawn("ffmpeg", ["-version"]);

      ffmpegCheck.on("close", (code) => {
        resolve(code === 0);
      });

      ffmpegCheck.on("error", () => {
        resolve(false);
      });
    });
  };

  const ffmpegAvailable = await checkFFmpeg();

  if (!ffmpegAvailable) {
    console.error("❌ ffmpeg not found. Install it:");
    console.error("   macOS: brew install ffmpeg");
    console.error("   Linux: sudo apt-get install ffmpeg");
    console.error("   Windows: Download from https://ffmpeg.org/");
    process.exit(1);
  }

  // Run the recorder
  const recorder = new EnterpriseCIARecorder(options);
  const success = await recorder.run();

  if (success) {
    await recorder.displaySummary();
    process.exit(0);
  } else {
    console.error("\n❌ Recording failed");
    process.exit(1);
  }
}

// Execute if run directly
if (require.main === module) {
  main().catch((error) => {
    console.error("Fatal error:", error);
    process.exit(1);
  });
}

module.exports = EnterpriseCIARecorder;
