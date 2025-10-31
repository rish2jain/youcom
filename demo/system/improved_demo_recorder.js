#!/usr/bin/env node

/**
 * Improved Demo Recorder - Native video recording with better automation
 *
 * Install dependencies:
 * npm install puppeteer puppeteer-screen-recorder
 */

const puppeteer = require("puppeteer");
const { PuppeteerScreenRecorder } = require("puppeteer-screen-recorder");
const fs = require("fs").promises;
const path = require("path");
const os = require("os");

class ImprovedDemoRecorder {
  constructor(config = {}) {
    this.browser = null;
    this.page = null;
    this.recorder = null;

    // Configuration with defaults
    this.config = {
      videoDir: config.videoDir || "demo_videos",
      baseUrl: config.baseUrl || "http://localhost:3000?skip-onboarding=true",
      viewport: config.viewport || { width: 1920, height: 1080 },
      fps: config.fps || 30,
      videoBitrate: config.videoBitrate || 2000,
      aspectRatio: config.aspectRatio || "16:9",
      allowInsecureWebSecurity: config.allowInsecureWebSecurity || false,
      ...config,
    };

    this.platform = os.platform();
    this.videoPath = null;
  }

  getChromePath() {
    switch (this.platform) {
      case "darwin":
        return "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
      case "linux":
        return "/usr/bin/google-chrome";
      case "win32":
        return "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
      default:
        return null;
    }
  }

  async initialize() {
    console.log(`🚀 Initializing Demo Recorder...`);
    console.log(`   Platform: ${this.platform}`);
    console.log(
      `   Resolution: ${this.config.viewport.width}x${this.config.viewport.height}`
    );
    console.log(`   FPS: ${this.config.fps}`);

    // Create video directory
    await fs.mkdir(this.config.videoDir, { recursive: true });

    const chromePath = this.getChromePath();

    try {
      this.browser = await puppeteer.launch({
        executablePath: chromePath,
        headless: false, // Must be false for screen recording
        defaultViewport: this.config.viewport,
        protocolTimeout: 60000, // Increase timeout to 60 seconds
        args: [
          "--no-sandbox",
          "--disable-setuid-sandbox",
          `--window-size=${this.config.viewport.width},${this.config.viewport.height}`,
          "--window-position=0,0",
          "--disable-dev-shm-usage",
          "--auto-open-devtools-for-tabs=false",
          ...(this.config.allowInsecureWebSecurity
            ? ["--disable-web-security"]
            : []),
        ],
        ignoreDefaultArgs: ["--mute-audio"],
      });

      this.page = await this.browser.newPage();
      await this.page.setViewport(this.config.viewport);

      // Set up console logging from the page
      this.page.on("console", (msg) => {
        if (msg.type() === "error") {
          console.log(`   Browser Error: ${msg.text()}`);
        }
      });

      console.log("✅ Browser initialized successfully");
      return true;
    } catch (error) {
      console.error("❌ Browser initialization failed:", error.message);
      return false;
    }
  }

  async setupRecorder() {
    console.log("🎥 Setting up native video recorder...");

    const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
    this.videoPath = path.join(
      this.config.videoDir,
      `enterprise_cia_demo_${timestamp}.mp4`
    );

    try {
      this.recorder = new PuppeteerScreenRecorder(this.page, {
        followNewTab: false,
        fps: this.config.fps,
        videoFrame: {
          width: this.config.viewport.width,
          height: this.config.viewport.height,
        },
        videoCrf: 18, // Lower = better quality (18-28 recommended)
        videoCodec: "libx264",
        videoPreset: "ultrafast", // ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow
        videoBitrate: this.config.videoBitrate,
        aspectRatio: this.config.aspectRatio,
      });

      console.log("✅ Recorder configured");
      return true;
    } catch (error) {
      console.error("❌ Recorder setup failed:", error.message);
      return false;
    }
  }

  async startRecording() {
    if (!this.recorder) {
      console.error("❌ Recorder not initialized");
      return false;
    }

    try {
      await this.recorder.start(this.videoPath);
      console.log(`🎬 Recording started → ${this.videoPath}`);
      return true;
    } catch (error) {
      console.error("❌ Failed to start recording:", error.message);
      return false;
    }
  }

  async stopRecording() {
    if (!this.recorder) {
      return false;
    }

    try {
      console.log("🛑 Stopping recording...");
      await this.recorder.stop();
      console.log("✅ Recording saved successfully");
      return true;
    } catch (error) {
      console.error("❌ Failed to stop recording:", error.message);
      return false;
    }
  }

  async wait(seconds, message = null) {
    if (message) {
      console.log(`⏳ ${message}`);
    }
    await new Promise((resolve) => setTimeout(resolve, seconds * 1000));
  }

  async smoothScroll(distance, duration = 1000) {
    await this.page.evaluate(
      async (distance, duration) => {
        const start = window.scrollY;
        const startTime = performance.now();

        return new Promise((resolve) => {
          const scroll = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // Easing function for smooth animation
            const easeInOutCubic =
              progress < 0.5
                ? 4 * progress * progress * progress
                : 1 - Math.pow(-2 * progress + 2, 3) / 2;

            window.scrollTo(0, start + distance * easeInOutCubic);

            if (progress < 1) {
              requestAnimationFrame(scroll);
            } else {
              resolve();
            }
          };

          requestAnimationFrame(scroll);
        });
      },
      distance,
      duration
    );
  }

  async clickElement(selector, waitTime = 2) {
    try {
      await this.page.waitForSelector(selector, { timeout: 5000 });
      await this.page.click(selector);
      console.log(`   ✓ Clicked: ${selector}`);
      await this.wait(waitTime);
      return true;
    } catch (error) {
      console.log(`   ⚠️  Could not click: ${selector}`);
      return false;
    }
  }

  async typeText(selector, text, delay = 100) {
    try {
      await this.page.waitForSelector(selector, { timeout: 5000 });
      await this.page.click(selector);
      await this.page.type(selector, text, { delay });
      console.log(`   ✓ Typed: "${text}"`);
      await this.wait(1);
      return true;
    } catch (error) {
      console.log(`   ⚠️  Could not type in: ${selector}`);
      return false;
    }
  }

  async runDemoSequence() {
    console.log("\n🎬 Starting Demo Sequence\n");

    try {
      // 1. Load Dashboard
      console.log("📍 Scene 1: Loading Dashboard");
      await this.page.goto(this.config.baseUrl, {
        waitUntil: "networkidle2",
        timeout: 20000,
      });
      await this.wait(3, "Dashboard loaded");

      // 2. Introduction
      console.log("\n📍 Scene 2: Welcome & Overview");
      await this.wait(4, "🎙️ Welcome to Enterprise CIA");
      await this.wait(3, "🎙️ AI-Powered Competitive Intelligence");

      // 3. You.com API Integration
      console.log("\n📍 Scene 3: You.com API Integration");
      await this.wait(3, "🎙️ Complete You.com API integration");
      await this.wait(4, "🎙️ Four APIs working together");

      // 4. Scroll through features
      console.log("\n📍 Scene 4: Feature Showcase");
      await this.smoothScroll(400, 1500);
      await this.wait(3, "🎙️ News API detects competitive signals");

      await this.smoothScroll(400, 1500);
      await this.wait(3, "🎙️ Search API enriches context");

      await this.smoothScroll(400, 1500);
      await this.wait(3, "🎙️ Custom Agents analyze impact");

      await this.smoothScroll(400, 1500);
      await this.wait(3, "🎙️ ARI synthesizes 400+ sources");

      // 5. Interaction (if elements exist)
      console.log("\n📍 Scene 5: User Interaction");
      await this.smoothScroll(-1600, 2000); // Scroll back up

      // Try to interact with the dashboard - use more specific selector
      // First try data attributes, then fallback to generic button
      const interacted = await this.clickElement(
        '[data-testid="primary-action"], [aria-label*="Generate"], button[class*="primary"]:first-of-type, button:first-of-type',
        2
      );
      if (interacted) {
        await this.wait(3, "🎙️ Exploring dashboard features");
      }

      // 6. Results & Benefits
      console.log("\n📍 Scene 6: Results");
      await this.wait(3, "🎙️ Saves 10+ hours per week");
      await this.wait(3, "🎙️ 85% accuracy, production ready");
      await this.wait(3, "🎙️ Sub-5-minute latency");

      // 7. Closing
      console.log("\n📍 Scene 7: Closing");
      const scrollHeight = await this.page.evaluate(
        () => document.body.scrollHeight
      );
      await this.smoothScroll(-scrollHeight, 2000); // Scroll to top
      await this.wait(3, "🎙️ Built for You.com Hackathon");
      await this.wait(3, "🎙️ Thank you for watching");

      console.log("\n🎉 Demo sequence completed!");
    } catch (error) {
      console.error(`\n❌ Demo error: ${error.message}`);
      throw error;
    }
  }

  async run() {
    console.log("=".repeat(60));
    console.log("ENTERPRISE CIA - AUTOMATED DEMO RECORDER");
    console.log("=".repeat(60) + "\n");

    const initialized = await this.initialize();
    if (!initialized) {
      console.log("❌ Initialization failed");
      return;
    }

    const recorderReady = await this.setupRecorder();
    if (!recorderReady) {
      console.log("❌ Recorder setup failed");
      await this.cleanup();
      return;
    }

    try {
      await this.startRecording();
      await this.runDemoSequence();
      await this.stopRecording();

      console.log("\n" + "=".repeat(60));
      console.log("✅ DEMO RECORDING COMPLETE!");
      console.log("=".repeat(60));
      console.log(`\n🎥 Video saved: ${this.videoPath}`);
      console.log(`📊 File size: ${await this.getFileSize(this.videoPath)}`);
    } catch (error) {
      console.error("\n❌ Demo recording failed:", error);
    } finally {
      await this.cleanup();
    }
  }

  async getFileSize(filePath) {
    try {
      const stats = await fs.stat(filePath);
      const fileSizeInMB = (stats.size / (1024 * 1024)).toFixed(2);
      return `${fileSizeInMB} MB`;
    } catch {
      return "Unknown";
    }
  }

  async cleanup() {
    console.log("\n🧹 Cleaning up...");
    if (this.browser) {
      await this.browser.close();
      console.log("   ✓ Browser closed");
    }
  }
}

// CLI execution
if (require.main === module) {
  // Parse command line arguments
  const args = process.argv.slice(2);
  const config = {};

  // Simple argument parser
  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case "--url":
        if (i + 1 >= args.length || args[i + 1].startsWith("--")) {
          console.error("Error: --url requires a value");
          process.exit(1);
        }
        config.baseUrl = args[++i];
        break;
      case "--fps":
        if (i + 1 >= args.length || args[i + 1].startsWith("--")) {
          console.error("Error: --fps requires a value");
          process.exit(1);
        }
        const fps = parseInt(args[++i], 10);
        if (!isFinite(fps) || fps <= 0 || fps > 120) {
          console.error("Error: --fps must be a number between 1 and 120");
          process.exit(1);
        }
        config.fps = fps;
        break;
      case "--width":
        if (i + 1 >= args.length || args[i + 1].startsWith("--")) {
          console.error("Error: --width requires a value");
          process.exit(1);
        }
        if (!config.viewport) config.viewport = {};
        const width = parseInt(args[++i], 10);
        if (!isFinite(width) || width <= 0) {
          console.error("Error: --width must be a positive integer");
          process.exit(1);
        }
        config.viewport.width = width;
        break;
      case "--height":
        if (i + 1 >= args.length || args[i + 1].startsWith("--")) {
          console.error("Error: --height requires a value");
          process.exit(1);
        }
        if (!config.viewport) config.viewport = {};
        const height = parseInt(args[++i], 10);
        if (!isFinite(height) || height <= 0) {
          console.error("Error: --height must be a positive integer");
          process.exit(1);
        }
        config.viewport.height = height;
        break;
      case "--output":
        if (i + 1 >= args.length || args[i + 1].startsWith("--")) {
          console.error("Error: --output requires a value");
          process.exit(1);
        }
        config.videoDir = args[++i];
        break;
      case "--help":
        console.log(`
Usage: node improved_demo_recorder.js [options]

Options:
  --url <url>        Dashboard URL (default: http://localhost:3000?skip-onboarding=true)
  --fps <number>     Frames per second (default: 30)
  --width <pixels>   Video width (default: 1920)
  --height <pixels>  Video height (default: 1080)
  --output <dir>     Output directory (default: demo_videos)
  --help            Show this help message

Example:
  node improved_demo_recorder.js --url http://localhost:3000 --fps 60 --width 2560 --height 1440
        `);
        process.exit(0);
    }
  }

  const recorder = new ImprovedDemoRecorder(config);
  recorder.run().catch((error) => {
    console.error("Fatal error:", error);
    process.exit(1);
  });
}

module.exports = ImprovedDemoRecorder;
