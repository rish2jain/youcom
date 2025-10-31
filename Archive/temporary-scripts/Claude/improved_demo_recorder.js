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
          "--disable-web-security", // For local testing
          "--auto-open-devtools-for-tabs=false",
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
    console.log("\n🎬 Starting 2-Minute Demo Sequence\n");

    try {
      // Scene 1: Opening & Platform Introduction (0:00 - 0:20) | 20 seconds
      console.log("📍 Scene 1: Opening & Introduction (0:00-0:20)");
      await this.page.goto(this.config.baseUrl, {
        waitUntil: "networkidle2",
        timeout: 20000,
      });
      await this.wait(3, "⏱️  0:03 | Enterprise CIA");
      await this.wait(3, "⏱️  0:06 | AI-Powered Competitive Intelligence");
      await this.wait(4, "⏱️  0:10 | Transform information overload");
      await this.wait(5, "⏱️  0:15 | ...into actionable insights");
      await this.wait(5, "⏱️  0:20 | Powered by You.com APIs");

      // Scene 2: You.com API Orchestra (0:20 - 0:45) | 25 seconds
      console.log("\n📍 Scene 2: API Orchestra (0:20-0:45)");
      await this.smoothScroll(400, 2000);
      await this.wait(5, "⏱️  0:25 | Four You.com APIs working together");
      await this.wait(5, "⏱️  0:30 | News API: Real-time monitoring");
      await this.wait(5, "⏱️  0:35 | Search API: Context enrichment");
      await this.wait(5, "⏱️  0:40 | Custom Agents: Strategic analysis");
      await this.wait(5, "⏱️  0:45 | ARI: Deep synthesis");

      // Scene 3: Live Impact Cards (0:45 - 1:10) | 25 seconds
      console.log("\n📍 Scene 3: Impact Cards (0:45-1:10)");
      await this.smoothScroll(400, 2000);
      await this.wait(5, "⏱️  0:50 | Competitive intelligence in action");

      // Try to interact with Impact Card
      const clicked = await this.clickElement("button:first-of-type", 2);
      if (clicked) {
        await this.wait(3, "⏱️  0:55 | Real competitor activities");
        await this.wait(5, "⏱️  1:00 | Multi-source analysis");
        await this.wait(5, "⏱️  1:05 | AI-powered insights");
        await this.wait(5, "⏱️  1:10 | Recommended actions");
      } else {
        await this.wait(5, "⏱️  0:55 | Real competitor activities");
        await this.wait(5, "⏱️  1:00 | Multi-source analysis");
        await this.wait(5, "⏱️  1:05 | AI-powered insights");
        await this.wait(5, "⏱️  1:10 | Recommended actions");
      }

      // Scene 4: Key Features Showcase (1:10 - 1:35) | 25 seconds
      console.log("\n📍 Scene 4: Features (1:10-1:35)");
      await this.smoothScroll(400, 2000);
      await this.wait(5, "⏱️  1:15 | Automated monitoring");
      await this.smoothScroll(400, 2000);
      await this.wait(5, "⏱️  1:20 | Predictive analytics");
      await this.smoothScroll(400, 2000);
      await this.wait(5, "⏱️  1:25 | CRM integrations");
      await this.smoothScroll(400, 2000);
      await this.wait(5, "⏱️  1:30 | Executive reports");
      await this.wait(5, "⏱️  1:35 | All powered by You.com");

      // Scene 5: Results & Benefits (1:35 - 1:50) | 15 seconds
      console.log("\n📍 Scene 5: Results (1:35-1:50)");
      await this.smoothScroll(300, 1500);
      await this.wait(5, "⏱️  1:40 | Saves 10+ hours per week");
      await this.wait(5, "⏱️  1:45 | 85% accuracy, production-ready");
      await this.wait(5, "⏱️  1:50 | Sub-5-minute latency");

      // Scene 6: Closing & CTA (1:50 - 2:00) | 10 seconds
      console.log("\n📍 Scene 6: Closing (1:50-2:00)");
      const scrollHeight = await this.page.evaluate(
        () => document.body.scrollHeight
      );
      await this.smoothScroll(-scrollHeight, 2500); // Smooth scroll to top
      await this.wait(5, "⏱️  1:55 | Built for You.com Hackathon 2025");
      await this.wait(5, "⏱️  2:00 | Thank you for watching");

      console.log("\n🎉 2-Minute Demo Completed! Total: ~120 seconds");
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
        config.baseUrl = args[++i];
        break;
      case "--fps":
        config.fps = parseInt(args[++i]);
        break;
      case "--width":
        if (!config.viewport) config.viewport = {};
        config.viewport.width = parseInt(args[++i]);
        break;
      case "--height":
        if (!config.viewport) config.viewport = {};
        config.viewport.height = parseInt(args[++i]);
        break;
      case "--output":
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
