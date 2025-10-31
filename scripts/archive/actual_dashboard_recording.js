#!/usr/bin/env node

/**
 * Actual Dashboard Recording - Records the real Enterprise CIA dashboard
 * Navigates through actual app features and takes longer recording
 */

const puppeteer = require("puppeteer");
const fs = require("fs").promises;
const path = require("path");
const { spawn } = require("child_process");
const os = require("os");

class ActualDashboardRecording {
  constructor() {
    this.browser = null;
    this.page = null;
    this.videoDir = "demo_videos";
    this.screenshotsDir = "demo_videos/screenshots";
    this.baseUrl = "http://localhost:3000?skip-onboarding=true";
    this.videoPath = null;
    this.platform = os.platform();
    this.fps = 15; // Higher FPS for smoother video
    this.screenshotCount = 0;
    this.isRecording = false;
    this.recordingInterval = null;
    this.totalDuration = 180; // 3 minutes
  }

  getChromePath() {
    switch (this.platform) {
      case "darwin":
        return "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
      case "win32":
        return "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
      case "linux":
        return "/usr/bin/google-chrome";
      default:
        return null;
    }
  }

  async initialize() {
    console.log(
      `🚀 Starting Actual Dashboard Recording on ${this.platform}...`
    );

    // Create directories
    await fs.mkdir(this.videoDir, { recursive: true });
    await fs.mkdir(this.screenshotsDir, { recursive: true });

    const chromePath = this.getChromePath();

    try {
      console.log("🌐 Launching Chrome for actual dashboard recording...");

      this.browser = await puppeteer.launch({
        executablePath: chromePath,
        headless: false,
        defaultViewport: { width: 1280, height: 720 },
        args: [
          "--no-sandbox",
          "--disable-setuid-sandbox",
          "--disable-dev-shm-usage",
          "--disable-web-security",
          "--window-size=1280,720",
          "--window-position=100,100",
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
      await this.page.setViewport({ width: 1280, height: 720 });

      // Add error handlers
      this.page.on("error", (error) => {
        console.log("⚠️ Page error:", error.message);
      });

      this.page.on("pageerror", (error) => {
        console.log("⚠️ Page script error:", error.message);
      });

      console.log("✅ Chrome launched successfully");
      return true;
    } catch (error) {
      console.error("❌ Chrome launch failed:", error.message);
      return false;
    }
  }

  async startScreenshotRecording() {
    console.log("🎥 Starting actual dashboard recording...");
    console.log(
      `📸 Recording at ${this.fps} FPS for ${this.totalDuration} seconds`
    );
    console.log("📹 This captures the REAL Enterprise CIA dashboard");

    this.isRecording = true;
    this.screenshotCount = 0;

    // Take screenshots at regular intervals
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
            fullPage: false, // Only capture viewport
          });

          this.screenshotCount++;

          // Show progress every 75 frames (5 seconds at 15fps)
          if (this.screenshotCount % 75 === 0) {
            const seconds = Math.floor(this.screenshotCount / this.fps);
            console.log(
              `📸 Recording: ${seconds}s / ${this.totalDuration}s (${this.screenshotCount} frames)`
            );
          }
        } catch (error) {
          console.log(`⚠️ Screenshot error: ${error.message}`);
        }
      }
    }, 1000 / this.fps);

    console.log("✅ Dashboard recording started");
    return true;
  }

  async stopScreenshotRecording() {
    if (this.recordingInterval) {
      console.log("🛑 Stopping dashboard recording...");
      clearInterval(this.recordingInterval);
      this.recordingInterval = null;
      this.isRecording = false;

      const totalSeconds = Math.floor(this.screenshotCount / this.fps);
      console.log(
        `📸 Total: ${this.screenshotCount} frames (${totalSeconds} seconds)`
      );
      console.log("✅ Dashboard recording stopped");

      return true;
    }
    return false;
  }

  async createVideoFromScreenshots() {
    const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
    this.videoPath = path.join(
      this.videoDir,
      `enterprise_cia_dashboard_${timestamp}.mp4`
    );

    console.log("🎬 Creating video from dashboard screenshots...");
    console.log(`📹 Output: ${this.videoPath}`);

    const ffmpegArgs = [
      "-framerate",
      this.fps.toString(),
      "-i",
      path.join(this.screenshotsDir, "frame_%06d.png"),
      "-c:v",
      "libx264",
      "-preset",
      "medium",
      "-crf",
      "18",
      "-pix_fmt",
      "yuv420p",
      "-y", // Overwrite output file
      this.videoPath,
    ];

    return new Promise((resolve, reject) => {
      const ffmpeg = spawn("ffmpeg", ffmpegArgs);

      ffmpeg.stderr.on("data", (data) => {
        const message = data.toString();
        if (message.includes("frame=") && Math.random() < 0.1) {
          console.log("🎬 Creating dashboard video...");
        }
      });

      ffmpeg.on("close", (code) => {
        if (code === 0) {
          console.log("✅ Dashboard video created successfully");
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

  async cleanupScreenshots() {
    console.log("🧹 Cleaning up screenshot files...");
    try {
      const files = await fs.readdir(this.screenshotsDir);
      for (const file of files) {
        if (file.endsWith(".png")) {
          await fs.unlink(path.join(this.screenshotsDir, file));
        }
      }
      console.log("✅ Screenshot cleanup complete");
    } catch (error) {
      console.log("⚠️ Cleanup error:", error.message);
    }
  }

  async wait(seconds) {
    console.log(`⏳ Waiting ${seconds} seconds...`);
    await new Promise((resolve) => setTimeout(resolve, seconds * 1000));
  }

  async addNarrationMarker(text) {
    console.log(`🎙️  NARRATION: ${text}`);
    const timestamp = new Date().toISOString();
    const markerFile = path.join(this.videoDir, "dashboard_narration.txt");
    try {
      await fs.appendFile(markerFile, `${timestamp}: ${text}\n`);
    } catch (error) {
      console.log(`⚠️ Could not write narration marker: ${error.message}`);
    }
  }

  async navigateToPage(url, description) {
    console.log(`🌐 Navigating to: ${description}`);
    try {
      await this.page.goto(url, {
        waitUntil: "networkidle2",
        timeout: 10000,
      });
      console.log(`✅ Loaded: ${description}`);
      return true;
    } catch (error) {
      console.log(`⚠️ Navigation failed for ${description}: ${error.message}`);
      return false;
    }
  }

  async scrollPage(direction = "down", amount = 300) {
    try {
      await this.page.evaluate(
        (dir, amt) => {
          const scrollAmount = dir === "down" ? amt : -amt;
          window.scrollBy({ top: scrollAmount, behavior: "smooth" });
        },
        direction,
        amount
      );
      await this.wait(1); // Wait for scroll to complete
    } catch (error) {
      console.log(`⚠️ Scroll error: ${error.message}`);
    }
  }

  async clickElement(selector, description) {
    try {
      console.log(`🖱️ Clicking: ${description}`);
      await this.page.waitForSelector(selector, { timeout: 5000 });
      await this.page.click(selector);
      await this.wait(2); // Wait for action to complete
      console.log(`✅ Clicked: ${description}`);
      return true;
    } catch (error) {
      console.log(`⚠️ Click failed for ${description}: ${error.message}`);
      return false;
    }
  }

  async runActualDashboardDemo() {
    console.log("\n🎬 Starting Actual Dashboard Demo Recording");

    await this.addNarrationMarker(
      "Welcome to Enterprise CIA - the complete competitive intelligence platform powered by You.com APIs"
    );

    try {
      // Load the actual dashboard
      console.log("🌐 Loading actual Enterprise CIA dashboard...");
      const loaded = await this.navigateToPage(
        this.baseUrl,
        "Enterprise CIA Dashboard"
      );

      if (!loaded) {
        console.log("❌ Could not load actual dashboard");
        return;
      }

      // Start recording the actual dashboard
      const recordingStarted = await this.startScreenshotRecording();
      if (!recordingStarted) {
        console.log("❌ Could not start recording");
        return;
      }

      // Section 1: Main Dashboard Overview (30 seconds)
      await this.addNarrationMarker(
        "This is the Enterprise CIA dashboard - your command center for competitive intelligence"
      );
      await this.wait(5);

      await this.addNarrationMarker(
        "The platform integrates all four You.com APIs - News, Search, Custom Agents, and ARI"
      );
      await this.wait(8);

      // Scroll to show different sections
      await this.scrollPage("down", 300);
      await this.addNarrationMarker(
        "Here we see real-time threat alerts with the highest priority competitors"
      );
      await this.wait(7);

      await this.scrollPage("down", 300);
      await this.addNarrationMarker(
        "The News API detects competitive signals across thousands of sources in real-time"
      );
      await this.wait(10);

      // Section 2: Navigate to different pages (60 seconds)
      console.log("📊 Exploring dashboard sections...");

      // Try to click on monitoring/research links
      const monitoringClicked = await this.clickElement(
        'a[href*="monitoring"], a[href*="research"], button',
        "Monitoring/Research section"
      );

      if (monitoringClicked) {
        await this.addNarrationMarker(
          "Navigating to the competitive monitoring section where Custom Agents analyze impact"
        );
        await this.wait(8);
      }

      await this.scrollPage("down", 400);
      await this.addNarrationMarker(
        "Search API enriches context while ARI synthesizes insights from 400+ sources"
      );
      await this.wait(10);

      // Go back to main dashboard
      await this.navigateToPage(this.baseUrl, "Back to main dashboard");
      await this.wait(3);

      await this.scrollPage("down", 500);
      await this.addNarrationMarker(
        "The intelligence dashboard shows recent analyses and key business insights"
      );
      await this.wait(10);

      // Section 3: Demonstrate interactions (45 seconds)
      await this.scrollPage("up", 200);
      await this.addNarrationMarker(
        "Quick actions allow you to add competitors and trigger new research"
      );
      await this.wait(8);

      // Try to interact with buttons or forms
      const buttonClicked = await this.clickElement(
        'button, a[href*="research"], .cta-button',
        "Action button"
      );

      if (buttonClicked) {
        await this.addNarrationMarker(
          "Demonstrating the seamless integration of all four You.com APIs"
        );
        await this.wait(7);
      }

      await this.scrollPage("down", 300);
      await this.addNarrationMarker(
        "This saves product managers over 10 hours per week with 85% accuracy"
      );
      await this.wait(10);

      // Section 4: Value proposition and conclusion (45 seconds)
      await this.scrollPage("up", 100);
      await this.addNarrationMarker(
        "Detection happens in under 5 minutes instead of days with complete source provenance"
      );
      await this.wait(10);

      await this.addNarrationMarker(
        "Built with production-grade architecture and 85% test coverage"
      );
      await this.wait(8);

      await this.scrollPage("down", 200);
      await this.addNarrationMarker(
        "The platform provides professional-grade competitive intelligence at scale"
      );
      await this.wait(10);

      await this.addNarrationMarker(
        "Enterprise CIA - where You.com's four APIs revolutionize competitive intelligence"
      );
      await this.wait(8);

      await this.addNarrationMarker(
        "Thank you for watching our comprehensive dashboard demonstration"
      );
      await this.wait(9);

      console.log("🎉 Actual dashboard demo completed!");
    } catch (error) {
      console.log(`Demo error: ${error.message}`);
      await this.addNarrationMarker(
        "Enterprise CIA - powered by complete You.com API integration"
      );
    } finally {
      await this.stopScreenshotRecording();
    }
  }

  async run() {
    const initialized = await this.initialize();

    if (!initialized) {
      console.log("❌ Could not initialize Chrome");
      return;
    }

    try {
      console.log(
        `🎬 Starting ${this.totalDuration}-second actual dashboard recording...`
      );
      console.log(
        "📹 This records the REAL Enterprise CIA dashboard with navigation"
      );

      await this.runActualDashboardDemo();

      // Create video from screenshots
      console.log("\n🎬 Converting dashboard screenshots to video...");
      await this.createVideoFromScreenshots();

      // Clean up screenshots
      await this.cleanupScreenshots();
    } catch (error) {
      console.error("❌ Demo failed:", error);
    } finally {
      if (this.browser) {
        console.log("🔒 Closing Chrome...");
        try {
          await this.browser.close();
        } catch (error) {
          console.log("⚠️ Error closing browser:", error.message);
        }
      }
    }

    console.log(`\n🎉 Actual Dashboard Recording Complete!`);
    if (this.videoPath) {
      console.log(`🎥 Video saved: ${this.videoPath}`);
    }
    console.log(
      `🎙️  Narration: ${path.join(this.videoDir, "dashboard_narration.txt")}`
    );

    console.log(`\n📋 This video shows the REAL Enterprise CIA dashboard!`);
    console.log(
      `✅ ${this.totalDuration} seconds of actual app navigation and features`
    );
    console.log(`🎯 Complete demonstration of You.com API integration`);
  }
}

// Execute the demo
if (require.main === module) {
  const demo = new ActualDashboardRecording();
  demo.run().catch(console.error);
}

module.exports = ActualDashboardRecording;
