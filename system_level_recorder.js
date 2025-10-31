#!/usr/bin/env node

/**
 * System-Level Demo Recorder - Uses native OS screen recording
 * 
 * Best quality option - uses native screen capture APIs
 * Requires: macOS (ffmpeg with AVFoundation) or Linux (ffmpeg with x11grab)
 */

const { spawn } = require("child_process");
const puppeteer = require("puppeteer");
const fs = require("fs").promises;
const path = require("path");
const os = require("os");

class SystemLevelRecorder {
  constructor(config = {}) {
    this.browser = null;
    this.page = null;
    this.recordingProcess = null;
    
    this.config = {
      videoDir: config.videoDir || "demo_videos",
      baseUrl: config.baseUrl || "http://localhost:3000?skip-onboarding=true",
      viewport: config.viewport || { width: 1920, height: 1080 },
      fps: config.fps || 30,
      quality: config.quality || "high", // low, medium, high, ultra
      ...config
    };
    
    this.platform = os.platform();
    this.videoPath = null;
    this.windowInfo = null;
  }

  getChromePath() {
    switch (this.platform) {
      case "darwin":
        return "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
      case "linux":
        return "/usr/bin/google-chrome";
      default:
        return null;
    }
  }

  getQualitySettings() {
    const settings = {
      low: { crf: 28, preset: "veryfast", bitrate: "1000k" },
      medium: { crf: 23, preset: "fast", bitrate: "2500k" },
      high: { crf: 18, preset: "medium", bitrate: "5000k" },
      ultra: { crf: 15, preset: "slow", bitrate: "8000k" },
    };
    return settings[this.config.quality] || settings.high;
  }

  async initialize() {
    console.log(`🚀 Initializing System-Level Recorder...`);
    console.log(`   Platform: ${this.platform}`);
    console.log(`   Quality: ${this.config.quality}`);

    // Verify ffmpeg is available
    if (!await this.checkFFmpeg()) {
      console.error("❌ FFmpeg not found. Please install ffmpeg.");
      return false;
    }

    await fs.mkdir(this.config.videoDir, { recursive: true });

    const chromePath = this.getChromePath();

    try {
      this.browser = await puppeteer.launch({
        executablePath: chromePath,
        headless: false,
        defaultViewport: null, // Use system window size
        args: [
          "--no-sandbox",
          "--disable-setuid-sandbox",
          `--window-size=${this.config.viewport.width},${this.config.viewport.height}`,
          "--window-position=0,50", // Slightly below menu bar
          "--disable-dev-shm-usage",
          "--start-maximized",
        ],
      });

      this.page = await this.browser.newPage();
      await this.page.setViewport(this.config.viewport);

      console.log("✅ Browser initialized");
      
      // Wait for window to be ready
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      return true;
    } catch (error) {
      console.error("❌ Browser initialization failed:", error.message);
      return false;
    }
  }

  async checkFFmpeg() {
    return new Promise((resolve) => {
      const ffmpeg = spawn("ffmpeg", ["-version"]);
      ffmpeg.on("close", (code) => resolve(code === 0));
      ffmpeg.on("error", () => resolve(false));
    });
  }

  async getWindowInfo() {
    // On macOS, we can get window bounds via AppleScript
    if (this.platform === "darwin") {
      return {
        x: 0,
        y: 50,
        width: this.config.viewport.width,
        height: this.config.viewport.height,
      };
    }
    
    // On Linux, you might need wmctrl or xdotool
    return {
      x: 0,
      y: 0,
      width: this.config.viewport.width,
      height: this.config.viewport.height,
    };
  }

  async startRecording() {
    console.log("🎥 Starting system-level recording...");
    
    const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
    this.videoPath = path.join(
      this.config.videoDir,
      `enterprise_cia_system_${timestamp}.mp4`
    );

    this.windowInfo = await this.getWindowInfo();
    const quality = this.getQualitySettings();

    let ffmpegArgs = [];

    if (this.platform === "darwin") {
      // macOS - Use AVFoundation
      ffmpegArgs = [
        "-f", "avfoundation",
        "-capture_cursor", "1",
        "-capture_mouse_clicks", "1",
        "-framerate", this.config.fps.toString(),
        "-i", "1:", // Screen 1, no audio
        "-vf", `crop=${this.windowInfo.width}:${this.windowInfo.height}:${this.windowInfo.x}:${this.windowInfo.y}`,
        "-c:v", "libx264",
        "-preset", quality.preset,
        "-crf", quality.crf.toString(),
        "-pix_fmt", "yuv420p",
        "-y",
        this.videoPath,
      ];
    } else if (this.platform === "linux") {
      // Linux - Use x11grab
      const display = process.env.DISPLAY || ":0";
      ffmpegArgs = [
        "-f", "x11grab",
        "-framerate", this.config.fps.toString(),
        "-video_size", `${this.windowInfo.width}x${this.windowInfo.height}`,
        "-i", `${display}+${this.windowInfo.x},${this.windowInfo.y}`,
        "-c:v", "libx264",
        "-preset", quality.preset,
        "-crf", quality.crf.toString(),
        "-pix_fmt", "yuv420p",
        "-y",
        this.videoPath,
      ];
    } else {
      console.error("❌ Unsupported platform for system recording");
      return false;
    }

    return new Promise((resolve, reject) => {
      this.recordingProcess = spawn("ffmpeg", ffmpegArgs);

      // Give ffmpeg time to start
      setTimeout(() => {
        if (this.recordingProcess && !this.recordingProcess.killed) {
          console.log(`✅ Recording started → ${this.videoPath}`);
          resolve(true);
        } else {
          reject(new Error("FFmpeg failed to start"));
        }
      }, 2000);

      this.recordingProcess.stderr.on("data", (data) => {
        // Suppress ffmpeg output (it's verbose)
        // Uncomment for debugging: console.log(`FFmpeg: ${data}`);
      });

      this.recordingProcess.on("error", (error) => {
        console.error("❌ Recording error:", error.message);
        reject(error);
      });
    });
  }

  async stopRecording() {
    if (!this.recordingProcess) {
      return false;
    }

    return new Promise((resolve) => {
      console.log("🛑 Stopping recording...");

      // Send 'q' to gracefully stop ffmpeg
      this.recordingProcess.stdin.write("q");
      
      // Also send SIGINT as backup
      setTimeout(() => {
        if (this.recordingProcess && !this.recordingProcess.killed) {
          this.recordingProcess.kill("SIGINT");
        }
      }, 1000);

      this.recordingProcess.on("close", () => {
        console.log("✅ Recording stopped");
        this.recordingProcess = null;
        resolve(true);
      });

      // Force kill after 5 seconds if graceful shutdown fails
      setTimeout(() => {
        if (this.recordingProcess && !this.recordingProcess.killed) {
          console.log("⚠️  Force stopping recording...");
          this.recordingProcess.kill("SIGKILL");
          this.recordingProcess = null;
          resolve(true);
        }
      }, 5000);
    });
  }

  async wait(seconds, message = null) {
    if (message) {
      console.log(`⏳ ${message}`);
    }
    await new Promise((resolve) => setTimeout(resolve, seconds * 1000));
  }

  async smoothScroll(distance, duration = 1000) {
    await this.page.evaluate(async (distance, duration) => {
      const start = window.scrollY;
      const startTime = performance.now();
      
      return new Promise((resolve) => {
        const scroll = (currentTime) => {
          const elapsed = currentTime - startTime;
          const progress = Math.min(elapsed / duration, 1);
          
          const easeInOutCubic = progress < 0.5
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
    }, distance, duration);
  }

  async runDemoSequence() {
    console.log("\n🎬 Starting Demo Sequence\n");

    try {
      console.log("📍 Scene 1: Loading Dashboard");
      await this.page.goto(this.config.baseUrl, {
        waitUntil: "networkidle2",
        timeout: 20000,
      });
      await this.wait(4, "Dashboard loaded");

      console.log("\n📍 Scene 2: Introduction");
      await this.wait(5, "🎙️ Enterprise CIA - AI-Powered Competitive Intelligence");

      console.log("\n📍 Scene 3: You.com Integration");
      await this.wait(4, "🎙️ Complete You.com API integration");
      await this.smoothScroll(400, 1500);
      await this.wait(3);

      console.log("\n📍 Scene 4: Features");
      await this.wait(3, "🎙️ News API - Real-time monitoring");
      await this.smoothScroll(400, 1500);
      await this.wait(3, "🎙️ Search API - Context enrichment");
      await this.smoothScroll(400, 1500);
      await this.wait(3, "🎙️ Custom Agents - Impact analysis");
      await this.smoothScroll(400, 1500);
      await this.wait(3, "🎙️ ARI - Deep research reports");

      console.log("\n📍 Scene 5: Results");
      await this.smoothScroll(-1600, 2000);
      await this.wait(3, "🎙️ 10+ hours saved per week");
      await this.wait(3, "🎙️ 85% accuracy, production-ready");
      await this.wait(3, "🎙️ Sub-5-minute latency");

      console.log("\n📍 Scene 6: Closing");
      await this.wait(3, "🎙️ Built for You.com Hackathon");
      await this.wait(3, "🎙️ Thank you!");

      console.log("\n🎉 Demo completed!");
    } catch (error) {
      console.error(`\n❌ Demo error: ${error.message}`);
      throw error;
    }
  }

  async run() {
    console.log("=".repeat(60));
    console.log("SYSTEM-LEVEL DEMO RECORDER");
    console.log("=".repeat(60) + "\n");

    if (this.platform !== "darwin" && this.platform !== "linux") {
      console.error("❌ System recording only supported on macOS and Linux");
      console.log("💡 Use improved_demo_recorder.js for cross-platform support");
      return;
    }

    const initialized = await this.initialize();
    if (!initialized) {
      return;
    }

    try {
      const recordingStarted = await this.startRecording();
      if (!recordingStarted) {
        throw new Error("Failed to start recording");
      }

      await this.runDemoSequence();
      await this.stopRecording();

      // Wait for file to be fully written
      await this.wait(2);

      console.log("\n" + "=".repeat(60));
      console.log("✅ RECORDING COMPLETE!");
      console.log("=".repeat(60));
      console.log(`\n🎥 Video: ${this.videoPath}`);
      
      const stats = await fs.stat(this.videoPath);
      const sizeMB = (stats.size / (1024 * 1024)).toFixed(2);
      console.log(`📊 Size: ${sizeMB} MB`);
      
    } catch (error) {
      console.error("\n❌ Recording failed:", error.message);
      if (this.recordingProcess) {
        await this.stopRecording();
      }
    } finally {
      await this.cleanup();
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
  const args = process.argv.slice(2);
  const config = {};

  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case "--url":
        config.baseUrl = args[++i];
        break;
      case "--fps":
        config.fps = parseInt(args[++i]);
        break;
      case "--quality":
        config.quality = args[++i]; // low, medium, high, ultra
        break;
      case "--output":
        config.videoDir = args[++i];
        break;
      case "--help":
        console.log(`
System-Level Demo Recorder - Maximum Quality

Usage: node system_level_recorder.js [options]

Options:
  --url <url>        Dashboard URL
  --fps <number>     Frames per second (default: 30)
  --quality <level>  low, medium, high, ultra (default: high)
  --output <dir>     Output directory
  --help            Show this help

Requirements:
  - macOS or Linux
  - FFmpeg with AVFoundation (macOS) or x11grab (Linux)

Examples:
  node system_level_recorder.js --quality ultra --fps 60
  node system_level_recorder.js --url http://localhost:3000 --quality high
        `);
        process.exit(0);
    }
  }

  const recorder = new SystemLevelRecorder(config);
  recorder.run().catch(console.error);
}

module.exports = SystemLevelRecorder;
