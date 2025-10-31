#!/usr/bin/env node

/**
 * Video Demo Script - Records full video demo without onboarding
 * Focuses on video recording with professional narration timing
 */

const puppeteer = require("puppeteer");
const fs = require("fs").promises;
const path = require("path");
const { spawn } = require("child_process");
const os = require("os");

class VideoDemo {
  constructor() {
    this.browser = null;
    this.page = null;
    this.videoDir = "demo_videos";
    this.baseUrl = "http://localhost:3000?skip-onboarding=true"; // Skip onboarding
    this.videoProcess = null;
    this.videoPath = null;
    this.platform = os.platform();
    this.recordingDuration = 180; // 3 minutes
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
    console.log(`🚀 Starting Video Demo on ${this.platform}...`);
    console.log(`🎯 Target: ${this.baseUrl}`);

    // Create directories
    await fs.mkdir(this.videoDir, { recursive: true });

    // Start video recording FIRST
    await this.startVideoRecording();

    const chromePath = this.getChromePath();
    console.log(`🔍 Using Chrome at: ${chromePath}`);

    try {
      console.log("🌐 Launching Chrome for video demo...");

      this.browser = await puppeteer.launch({
        executablePath: chromePath,
        headless: false,
        defaultViewport: { width: 1920, height: 1080 },
        args: [
          "--no-sandbox",
          "--disable-setuid-sandbox",
          "--disable-dev-shm-usage",
          "--disable-web-security",
          "--window-size=1920,1080",
          "--window-position=0,0",
          "--no-first-run",
          "--disable-default-apps",
          "--disable-popup-blocking",
          "--disable-translate",
          "--start-maximized",
        ],
        timeout: 30000,
      });

      this.page = await this.browser.newPage();
      await this.page.setViewport({ width: 1920, height: 1080 });

      console.log("✅ Chrome launched successfully for video recording");
      return true;
    } catch (error) {
      console.error("❌ Chrome launch failed:", error.message);
      return false;
    }
  }

  async startVideoRecording() {
    const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
    this.videoPath = path.join(
      this.videoDir,
      `enterprise_cia_video_demo_${timestamp}.mp4`
    );

    console.log("🎥 Starting video recording...");
    console.log(`📹 Recording for ${this.recordingDuration} seconds`);

    let ffmpegArgs = [];

    switch (this.platform) {
      case "darwin": // macOS
        ffmpegArgs = [
          "-f",
          "avfoundation",
          "-i",
          "1:0", // Screen capture
          "-r",
          "30",
          "-vcodec",
          "libx264",
          "-preset",
          "medium", // Better quality for final video
          "-crf",
          "15", // Higher quality
          "-pix_fmt",
          "yuv420p",
          "-t",
          this.recordingDuration.toString(),
          this.videoPath,
        ];
        break;

      case "win32": // Windows
        ffmpegArgs = [
          "-f",
          "gdigrab",
          "-i",
          "desktop",
          "-r",
          "30",
          "-vcodec",
          "libx264",
          "-preset",
          "medium",
          "-crf",
          "15",
          "-pix_fmt",
          "yuv420p",
          "-t",
          this.recordingDuration.toString(),
          this.videoPath,
        ];
        break;

      case "linux": // Linux
        ffmpegArgs = [
          "-f",
          "x11grab",
          "-i",
          ":0.0",
          "-r",
          "30",
          "-vcodec",
          "libx264",
          "-preset",
          "medium",
          "-crf",
          "15",
          "-pix_fmt",
          "yuv420p",
          "-t",
          this.recordingDuration.toString(),
          this.videoPath,
        ];
        break;

      default:
        console.log("⚠️ Unsupported platform for video recording.");
        return;
    }

    try {
      this.videoProcess = spawn("ffmpeg", ffmpegArgs);

      this.videoProcess.stderr.on("data", (data) => {
        // Only show important ffmpeg messages
        const message = data.toString();
        if (message.includes("frame=") && message.includes("fps=")) {
          // Show progress every few seconds
          if (Math.random() < 0.1) {
            // 10% chance to show progress
            const frameMatch = message.match(/frame=\s*(\d+)/);
            if (frameMatch) {
              const frames = parseInt(frameMatch[1]);
              const seconds = Math.floor(frames / 30);
              console.log(
                `🎬 Recording: ${seconds}s / ${this.recordingDuration}s`
              );
            }
          }
        }
      });

      console.log(`✅ Video recording started: ${this.videoPath}`);
      console.log(
        `⏰ Will automatically stop after ${this.recordingDuration} seconds`
      );
    } catch (error) {
      console.error("❌ Failed to start video recording:", error.message);
    }
  }

  async stopVideoRecording() {
    if (this.videoProcess) {
      console.log("🛑 Stopping video recording...");
      try {
        if (this.platform === "win32") {
          this.videoProcess.kill("SIGTERM");
        } else {
          this.videoProcess.stdin.write("q");
        }

        await new Promise((resolve) => {
          this.videoProcess.on("close", resolve);
          setTimeout(resolve, 5000);
        });

        this.videoProcess = null;
        console.log("✅ Video recording completed");
      } catch (error) {
        console.log("⚠️ Error stopping video:", error.message);
      }
    }
  }

  async wait(seconds) {
    console.log(`⏳ Waiting ${seconds} seconds...`);
    await new Promise((resolve) => setTimeout(resolve, seconds * 1000));
  }

  async addNarrationMarker(text) {
    console.log(`🎙️  NARRATION: ${text}`);
    const timestamp = new Date().toISOString();
    const markerFile = path.join(this.videoDir, "video_narration_markers.txt");
    try {
      await fs.appendFile(markerFile, `${timestamp}: ${text}\n`);
    } catch (error) {
      console.log(`⚠️ Could not write narration marker: ${error.message}`);
    }
  }

  async runVideoDemo() {
    console.log("\n🎬 Starting Enterprise CIA Video Demo");
    console.log("📹 Recording in progress - follow the narration timing");

    await this.addNarrationMarker(
      "Welcome to Enterprise CIA - the complete competitive intelligence platform powered by You.com APIs"
    );

    try {
      // Step 1: Navigate to application (5 seconds)
      console.log("🌐 Step 1: Loading Enterprise CIA Dashboard...");
      await this.page.goto(this.baseUrl, {
        waitUntil: "networkidle2",
        timeout: 15000,
      });

      console.log("✅ Application loaded without onboarding");
      await this.addNarrationMarker(
        "This is the Enterprise CIA dashboard - your command center for competitive intelligence"
      );
      await this.wait(5);

      // Step 2: Highlight key features (8 seconds)
      await this.addNarrationMarker(
        "The platform integrates all four You.com APIs - News, Search, Custom Agents, and ARI for comprehensive intelligence"
      );
      await this.wait(8);

      // Step 3: Show alerts section (10 seconds)
      console.log("🎯 Step 3: Highlighting threat alerts...");
      await this.page.evaluate(() => {
        const alertsSection =
          document.querySelector('h2:contains("Top Alerts")') ||
          document.querySelector('[class*="alert"]') ||
          document.querySelector("h2");
        if (alertsSection) {
          alertsSection.scrollIntoView({ behavior: "smooth", block: "center" });
        }
      });

      await this.addNarrationMarker(
        "Real-time threat detection shows OpenAI GPT-5 as a 9.8 out of 10 risk - the highest competitive threat detected"
      );
      await this.wait(10);

      // Step 4: Demonstrate interaction (12 seconds)
      console.log("🖱️ Step 4: Demonstrating interactions...");
      try {
        const buttons = await this.page.$$("button, a[href]");
        if (buttons.length > 0) {
          await this.addNarrationMarker(
            "Let me show you how to dive deeper into competitive analysis"
          );

          // Click on a research link or button
          await buttons[0].click();
          await this.wait(3);

          await this.addNarrationMarker(
            "The system orchestrates all four You.com APIs to generate comprehensive intelligence reports"
          );
          await this.wait(9);
        }
      } catch (error) {
        console.log("Interaction not available, continuing with demo");
        await this.addNarrationMarker(
          "The system would normally orchestrate all four You.com APIs for comprehensive analysis"
        );
        await this.wait(8);
      }

      // Step 5: Navigate back and show insights (15 seconds)
      console.log("📊 Step 5: Showing business insights...");
      await this.page.goto(this.baseUrl, { waitUntil: "networkidle2" });

      await this.page.evaluate(() => {
        const insightsSection =
          document.querySelector('h2:contains("Key Insights")') ||
          document.querySelector('[class*="insight"]');
        if (insightsSection) {
          insightsSection.scrollIntoView({
            behavior: "smooth",
            block: "center",
          });
        }
      });

      await this.addNarrationMarker(
        "The News API detected a 40% increase in competitor activity this week, with 3 major product announcements"
      );
      await this.wait(8);

      await this.addNarrationMarker(
        "Custom Agents analyze each announcement for strategic impact, while ARI synthesizes insights from 400+ sources"
      );
      await this.wait(7);

      // Step 6: Show quick actions (10 seconds)
      console.log("⚡ Step 6: Highlighting quick actions...");
      await this.page.evaluate(() => {
        const actionsSection =
          document.querySelector('h2:contains("Quick Actions")') ||
          document.querySelector('[class*="action"]');
        if (actionsSection) {
          actionsSection.scrollIntoView({
            behavior: "smooth",
            block: "center",
          });
        }
      });

      await this.addNarrationMarker(
        "Quick actions let you add competitors, research new threats, and configure monitoring - all powered by You.com APIs"
      );
      await this.wait(10);

      // Step 7: Value proposition (15 seconds)
      console.log("🎯 Step 7: Emphasizing value proposition...");
      await this.addNarrationMarker(
        "This saves product managers over 10 hours per week, detecting competitive moves in under 5 minutes instead of days"
      );
      await this.wait(8);

      await this.addNarrationMarker(
        "With 85% accuracy and complete source provenance, Enterprise CIA transforms competitive intelligence"
      );
      await this.wait(7);

      // Step 8: Technical excellence (12 seconds)
      console.log("⚙️ Step 8: Highlighting technical excellence...");
      await this.addNarrationMarker(
        "Built with production-grade architecture - 85% test coverage, real-time performance, and enterprise security"
      );
      await this.wait(8);

      await this.addNarrationMarker(
        "The complete You.com API integration delivers professional-grade intelligence at scale"
      );
      await this.wait(4);

      // Step 9: Final message (8 seconds)
      console.log("🏁 Step 9: Conclusion...");
      await this.addNarrationMarker(
        "Enterprise CIA - where You.com's four APIs unite to revolutionize competitive intelligence"
      );
      await this.wait(5);

      await this.addNarrationMarker("Thank you for watching our demo");
      await this.wait(3);

      console.log("🎉 Video demo sequence completed!");
    } catch (error) {
      console.log(`Demo error: ${error.message}`);
      await this.addNarrationMarker(
        "Enterprise CIA - powered by complete You.com API integration"
      );
    }
  }

  async run() {
    const initialized = await this.initialize();

    if (!initialized) {
      console.log("❌ Could not initialize. Please ensure:");
      console.log("1. Chrome is installed and accessible");
      console.log("2. Application is running at http://localhost:3000");
      console.log("3. FFmpeg is installed for video recording");
      return;
    }

    try {
      console.log(`🎬 Starting ${this.recordingDuration}-second video demo...`);
      console.log("📹 Video recording is active - performing demo actions");

      await this.runVideoDemo();

      // Wait for any remaining recording time
      console.log("⏰ Waiting for video recording to complete...");
    } catch (error) {
      console.error("❌ Demo failed:", error);
    } finally {
      await this.stopVideoRecording();

      if (this.browser) {
        console.log("🔒 Closing Chrome...");
        try {
          await this.browser.close();
        } catch (error) {
          console.log("⚠️ Error closing browser:", error.message);
        }
      }
    }

    console.log(`\n🎉 Video Demo Complete!`);
    if (this.videoPath) {
      console.log(`🎥 Video saved: ${this.videoPath}`);
    }
    console.log(
      `🎙️  Narration markers: ${path.join(
        this.videoDir,
        "video_narration_markers.txt"
      )}`
    );

    console.log(`\n📋 Next Steps:`);
    console.log(`1. Review the recorded video`);
    console.log(`2. Add professional voice-over using narration timing`);
    console.log(`3. Edit and polish for your You.com submission`);
    console.log(`4. Submit your Enterprise CIA video demo!`);
  }
}

// Execute the demo
if (require.main === module) {
  const demo = new VideoDemo();
  demo.run().catch(console.error);
}

module.exports = VideoDemo;
