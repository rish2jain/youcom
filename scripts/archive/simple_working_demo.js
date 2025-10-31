#!/usr/bin/env node

/**
 * Simple Working Demo - Just record the actual dashboard without complications
 */

const puppeteer = require("puppeteer");
const fs = require("fs").promises;
const path = require("path");
const { spawn } = require("child_process");
const os = require("os");

class SimpleWorkingDemo {
  constructor() {
    this.browser = null;
    this.page = null;
    this.videoDir = "demo_videos";
    this.screenshotsDir = "demo_videos/screenshots";
    this.baseUrl = "http://localhost:3000?skip-onboarding=true";
    this.videoPath = null;
    this.platform = os.platform();
    this.fps = 10;
    this.screenshotCount = 0;
    this.isRecording = false;
    this.recordingInterval = null;
  }

  getChromePath() {
    switch (this.platform) {
      case "darwin":
        return "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
      default:
        return null;
    }
  }

  async initialize() {
    console.log(`🚀 Starting Simple Working Demo...`);

    // Create directories
    await fs.mkdir(this.videoDir, { recursive: true });
    await fs.mkdir(this.screenshotsDir, { recursive: true });

    const chromePath = this.getChromePath();

    try {
      this.browser = await puppeteer.launch({
        executablePath: chromePath,
        headless: false,
        defaultViewport: { width: 1280, height: 720 },
        args: [
          "--no-sandbox",
          "--disable-setuid-sandbox",
          "--window-size=1280,720",
          "--window-position=50,50",
        ],
        timeout: 30000,
      });

      this.page = await this.browser.newPage();
      await this.page.setViewport({ width: 1280, height: 720 });

      console.log("✅ Chrome launched successfully");
      return true;
    } catch (error) {
      console.error("❌ Chrome launch failed:", error.message);
      return false;
    }
  }

  async startRecording() {
    console.log("🎥 Starting recording...");
    this.isRecording = true;
    this.screenshotCount = 0;

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

          if (this.screenshotCount % 50 === 0) {
            console.log(`📸 Captured ${this.screenshotCount} frames`);
          }
        } catch (error) {
          console.log(`⚠️ Screenshot error: ${error.message}`);
        }
      }
    }, 1000 / this.fps);

    console.log("✅ Recording started");
    return true;
  }

  async stopRecording() {
    if (this.recordingInterval) {
      console.log("🛑 Stopping recording...");
      clearInterval(this.recordingInterval);
      this.recordingInterval = null;
      this.isRecording = false;

      console.log(`📸 Total frames: ${this.screenshotCount}`);
      return true;
    }
    return false;
  }

  async createVideo() {
    const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
    this.videoPath = path.join(
      this.videoDir,
      `enterprise_cia_working_${timestamp}.mp4`
    );

    console.log("🎬 Creating video...");

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
      "20",
      "-pix_fmt",
      "yuv420p",
      "-y",
      this.videoPath,
    ];

    return new Promise((resolve, reject) => {
      const ffmpeg = spawn("ffmpeg", ffmpegArgs);

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

  async wait(seconds) {
    console.log(`⏳ Waiting ${seconds} seconds...`);
    await new Promise((resolve) => setTimeout(resolve, seconds * 1000));
  }

  async runDemo() {
    console.log("\n🎬 Starting Demo");

    try {
      // Load the dashboard
      console.log("🌐 Loading dashboard...");
      await this.page.goto(this.baseUrl, {
        waitUntil: "domcontentloaded",
        timeout: 15000,
      });

      await this.wait(3);
      console.log("✅ Dashboard loaded");

      // Start recording
      await this.startRecording();

      // Demo sequence - 2 minutes
      console.log("🎙️ Welcome to Enterprise CIA");
      await this.wait(5);

      console.log("🎙️ Complete You.com API integration");
      await this.wait(8);

      // Scroll through the page
      await this.page.evaluate(() => window.scrollBy(0, 300));
      await this.wait(3);

      console.log("🎙️ News API detects competitive signals");
      await this.wait(8);

      await this.page.evaluate(() => window.scrollBy(0, 300));
      await this.wait(3);

      console.log("🎙️ Search API enriches context");
      await this.wait(8);

      await this.page.evaluate(() => window.scrollBy(0, 300));
      await this.wait(3);

      console.log("🎙️ Custom Agents analyze impact");
      await this.wait(8);

      await this.page.evaluate(() => window.scrollBy(0, 300));
      await this.wait(3);

      console.log("🎙️ ARI synthesizes 400+ sources");
      await this.wait(8);

      // Try to click something
      try {
        const buttons = await this.page.$$("button, a[href]");
        if (buttons.length > 0) {
          await buttons[0].click();
          await this.wait(3);
        }
      } catch (error) {
        console.log("No clickable elements found");
      }

      console.log("🎙️ Saves 10+ hours per week");
      await this.wait(8);

      await this.page.evaluate(() => window.scrollTo(0, 0));
      await this.wait(3);

      console.log("🎙️ 85% accuracy, production ready");
      await this.wait(8);

      console.log("🎙️ Thank you for watching");
      await this.wait(5);

      console.log("🎉 Demo completed!");
    } catch (error) {
      console.log(`Demo error: ${error.message}`);
    } finally {
      await this.stopRecording();
    }
  }

  async run() {
    const initialized = await this.initialize();

    if (!initialized) {
      console.log("❌ Could not initialize");
      return;
    }

    try {
      await this.runDemo();

      if (this.screenshotCount > 0) {
        await this.createVideo();
      } else {
        console.log("❌ No screenshots captured");
      }
    } catch (error) {
      console.error("❌ Demo failed:", error);
    } finally {
      if (this.browser) {
        console.log("🔒 Closing Chrome...");
        await this.browser.close();
      }
    }

    console.log(`\n🎉 Demo Complete!`);
    if (this.videoPath) {
      console.log(`🎥 Video: ${this.videoPath}`);
    }
  }
}

// Execute the demo
if (require.main === module) {
  const demo = new SimpleWorkingDemo();
  demo.run().catch(console.error);
}

module.exports = SimpleWorkingDemo;
