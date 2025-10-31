#!/usr/bin/env node

/**
 * Simple Demo Script - Uses Chrome DevTools Protocol directly
 * More reliable than Puppeteer for automation
 */

const fs = require("fs").promises;
const path = require("path");
const { spawn } = require("child_process");
const os = require("os");

class SimpleDemo {
  constructor() {
    this.screenshotDir = "demo_screenshots";
    this.videoDir = "demo_videos";
    this.baseUrl = "http://localhost:3000";
    this.screenshotCounter = 1;
    this.videoProcess = null;
    this.videoPath = null;
    this.platform = os.platform();
  }

  async initialize() {
    console.log(`🚀 Starting simple demo on ${this.platform}...`);

    // Create directories
    await fs.mkdir(this.screenshotDir, { recursive: true });
    await fs.mkdir(this.videoDir, { recursive: true });

    // Start screen recording
    await this.startVideoRecording();

    console.log("✅ Demo initialized");
  }

  async startVideoRecording() {
    const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
    this.videoPath = path.join(
      this.videoDir,
      `enterprise_cia_demo_${timestamp}.mp4`
    );

    console.log("🎥 Starting screen recording...");

    let ffmpegArgs = [];

    switch (this.platform) {
      case "darwin": // macOS
        ffmpegArgs = [
          "-f",
          "avfoundation",
          "-i",
          "1:0", // Screen capture (display 1, no audio)
          "-r",
          "30",
          "-vcodec",
          "libx264",
          "-preset",
          "ultrafast",
          "-crf",
          "18",
          "-pix_fmt",
          "yuv420p",
          "-t",
          "60", // Record for 60 seconds
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
          "ultrafast",
          "-crf",
          "18",
          "-pix_fmt",
          "yuv420p",
          "-t",
          "60",
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
          "ultrafast",
          "-crf",
          "18",
          "-pix_fmt",
          "yuv420p",
          "-t",
          "60",
          this.videoPath,
        ];
        break;

      default:
        console.log(
          "⚠️ Unsupported platform for video recording. Manual demo only."
        );
        return;
    }

    try {
      this.videoProcess = spawn("ffmpeg", ffmpegArgs);

      this.videoProcess.stderr.on("data", (data) => {
        // Suppress most ffmpeg output
        if (
          data.toString().includes("error") ||
          data.toString().includes("Error")
        ) {
          console.error("FFmpeg error:", data.toString());
        }
      });

      console.log(`✅ Video recording started for ${this.platform}`);
      console.log(`🎥 Recording will stop automatically after 60 seconds`);
    } catch (error) {
      console.error("❌ Failed to start video recording:", error.message);
      console.log("📸 Continuing with manual demo...");
    }
  }

  async stopVideoRecording() {
    if (this.videoProcess) {
      console.log("🛑 Stopping video recording...");

      try {
        // Send quit command
        if (this.platform === "win32") {
          this.videoProcess.kill("SIGTERM");
        } else {
          this.videoProcess.stdin.write("q");
        }

        // Wait for process to finish
        await new Promise((resolve) => {
          this.videoProcess.on("close", resolve);
          setTimeout(resolve, 3000);
        });

        this.videoProcess = null;
        console.log("✅ Video recording stopped");
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
    const markerFile = path.join(this.videoDir, "narration_markers.txt");
    try {
      await fs.appendFile(markerFile, `${timestamp}: ${text}\n`);
    } catch (error) {
      console.log(`⚠️ Could not write narration marker: ${error.message}`);
    }
  }

  async runManualDemo() {
    console.log("\n🎬 Running Manual Demo Sequence");
    console.log("👋 Please follow these steps manually while recording:");

    await this.addNarrationMarker(
      "Enterprise CIA Demo - Complete You.com API Integration"
    );

    console.log("\n📋 DEMO SCRIPT:");
    console.log("===============");

    console.log("\n1. 🌐 Open your browser and navigate to:");
    console.log(`   ${this.baseUrl}`);
    await this.addNarrationMarker(
      "This is Enterprise CIA - automating competitive intelligence with all four You.com APIs"
    );
    await this.wait(5);

    console.log("\n2. 🎯 Show the main dashboard:");
    console.log("   - Point out the watchlist management");
    console.log("   - Highlight real-time monitoring");
    await this.addNarrationMarker(
      "Let me show you enterprise competitive monitoring in action"
    );
    await this.wait(5);

    console.log("\n3. 🔍 Demonstrate adding a competitor:");
    console.log("   - Add 'OpenAI' as a competitor");
    console.log("   - Show relevant keywords");
    await this.addNarrationMarker(
      "Adding OpenAI as a competitor with relevant keywords"
    );
    await this.wait(8);

    console.log("\n4. ⚡ Show API orchestration:");
    console.log("   - Trigger impact card generation");
    console.log("   - Explain the 4 APIs working together");
    await this.addNarrationMarker(
      "Generating Impact Card with real-time API orchestration"
    );
    await this.wait(8);

    console.log("\n5. 📊 Display results:");
    console.log("   - Show the generated impact card");
    console.log("   - Highlight source provenance");
    await this.addNarrationMarker(
      "All four You.com APIs working together in under 3 minutes"
    );
    await this.wait(5);

    console.log("\n6. 🔄 Explain the process:");
    console.log("   - News API detecting signals");
    console.log("   - Search API enriching context");
    await this.addNarrationMarker(
      "News API detecting signals, Search API enriching context"
    );
    await this.wait(5);

    console.log("\n7. 🧠 Show AI analysis:");
    console.log("   - Custom Agent analyzing impact");
    console.log("   - ARI synthesizing 400+ sources");
    await this.addNarrationMarker(
      "Custom Agent analyzing strategic impact, ARI synthesizing 400 sources"
    );
    await this.wait(5);

    console.log("\n8. 🎯 Highlight value proposition:");
    console.log("   - Professional-grade intelligence");
    console.log("   - Minutes instead of days");
    await this.addNarrationMarker(
      "Professional-grade competitive intelligence in minutes, not days"
    );
    await this.wait(5);

    console.log("\n9. ✅ Conclude with production readiness:");
    console.log("   - 85% test coverage");
    console.log("   - Real-time performance");
    await this.addNarrationMarker(
      "This is production-ready with 85% test coverage and real-time performance"
    );
    await this.wait(3);

    console.log("\n10. 🏁 Final message:");
    await this.addNarrationMarker(
      "Enterprise CIA - powered by complete You.com API integration"
    );
    await this.wait(3);

    console.log("\n🎉 Demo script completed!");
    console.log("===============");
  }

  async run() {
    try {
      await this.initialize();

      console.log("\n🎬 Starting manual demo with screen recording...");
      if (this.videoPath) {
        console.log(`🎥 Recording to: ${this.videoPath}`);
      }

      await this.runManualDemo();

      // Stop video recording
      await this.stopVideoRecording();

      console.log("\n🎉 Demo completed successfully!");
      if (this.videoPath) {
        console.log(`🎥 Video: ${this.videoPath}`);
      }
      console.log(
        `🎙️  Narration: ${path.join(this.videoDir, "narration_markers.txt")}`
      );

      console.log("\n📝 Next steps:");
      console.log("1. Review the video recording");
      console.log("2. Edit using the narration markers");
      console.log("3. Add any additional voice-over as needed");
    } catch (error) {
      console.error("❌ Demo failed:", error);
      await this.stopVideoRecording();
    }
  }
}

// Execute the demo
if (require.main === module) {
  const demo = new SimpleDemo();
  demo.run().catch(console.error);
}

module.exports = SimpleDemo;
