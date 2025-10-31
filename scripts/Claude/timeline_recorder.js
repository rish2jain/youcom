#!/usr/bin/env node
/**
 * Timeline-based demo recorder for Enterprise CIA
 *
 * Reads timeline JSON files from demo_system_cia and executes them with Puppeteer
 *
 * Usage:
 *   node scripts/Claude/timeline_recorder.js demo_videos/competitor_product_launch_timeline.json
 */

const fs = require("fs/promises");
const path = require("path");
const puppeteer = require("puppeteer");
const { PuppeteerScreenRecorder } = require("puppeteer-screen-recorder");

class TimelineRecorder {
  constructor(timelinePath) {
    this.timelinePath = timelinePath;
    this.timeline = null;
    this.config = {
      baseUrl: "http://localhost:3000?skip-onboarding=true",
      viewport: { width: 1920, height: 1080 },
      fps: 30,
      videoBitrate: 4000,
      aspectRatio: "16:9",
    };
    this.browser = null;
    this.page = null;
    this.recorder = null;
    this.videoPath = null;
    this.startTime = null;
  }

  async loadTimeline() {
    console.log(`📄 Loading timeline: ${this.timelinePath}`);
    const content = await fs.readFile(this.timelinePath, "utf-8");
    this.timeline = JSON.parse(content);
    console.log(`✅ Timeline loaded: ${this.timeline.scenario_name}`);
    console.log(`   Duration: ${this.timeline.duration_seconds}s`);
    console.log(`   Events: ${this.timeline.timeline.length}`);
  }

  getChromePath() {
    const paths = [
      "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
      "/Applications/Chromium.app/Contents/MacOS/Chromium",
      process.env.CHROME_PATH,
    ].filter(Boolean);

    for (const chromePath of paths) {
      try {
        require("fs").accessSync(chromePath);
        return chromePath;
      } catch (e) {}
    }

    throw new Error("Chrome/Chromium not found. Please install or set CHROME_PATH");
  }

  async setupBrowser() {
    console.log("🚀 Initializing browser...");

    const chromePath = this.getChromePath();

    this.browser = await puppeteer.launch({
      executablePath: chromePath,
      headless: false,
      defaultViewport: this.config.viewport,
      protocolTimeout: 60000,
      args: [
        "--no-sandbox",
        "--disable-setuid-sandbox",
        `--window-size=${this.config.viewport.width},${this.config.viewport.height}`,
        "--window-position=0,0",
        "--disable-dev-shm-usage",
        "--disable-web-security",
        "--auto-open-devtools-for-tabs=false",
      ],
      ignoreDefaultArgs: ["--mute-audio"],
    });

    this.page = await this.browser.newPage();
    await this.page.setViewport(this.config.viewport);

    // Set up console listener
    this.page.on("console", (msg) => {
      if (msg.type() === "error") {
        console.log(`   Browser Error: ${msg.text()}`);
      }
    });

    console.log("✅ Browser initialized");
  }

  async setupRecorder() {
    console.log("🎥 Setting up video recorder...");

    const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
    const scenarioName = this.timeline.scenario_name;
    this.videoPath = path.join(
      "demo_videos",
      `${scenarioName}_${timestamp}.mp4`
    );

    this.recorder = new PuppeteerScreenRecorder(this.page, {
      followNewTab: false,
      fps: this.config.fps,
      videoFrame: {
        width: this.config.viewport.width,
        height: this.config.viewport.height,
      },
      videoCrf: 18,
      videoCodec: "libx264",
      videoPreset: "ultrafast",
      videoBitrate: this.config.videoBitrate,
      aspectRatio: this.config.aspectRatio,
    });

    console.log("✅ Recorder configured");
  }

  async wait(seconds, message = null) {
    if (message) {
      console.log(`⏳ ${message}`);
    }
    await new Promise((resolve) => setTimeout(resolve, seconds * 1000));
  }

  async smoothScroll(distance, duration) {
    await this.page.evaluate(
      async (distance, duration) => {
        return new Promise((resolve) => {
          const startPos = window.scrollY;
          const startTime = Date.now();

          const scroll = () => {
            const elapsed = Date.now() - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // Easing function for smooth scrolling
            const eased = progress < 0.5
              ? 2 * progress * progress
              : 1 - Math.pow(-2 * progress + 2, 2) / 2;

            window.scrollTo(0, startPos + distance * eased);

            if (progress < 1) {
              requestAnimationFrame(scroll);
            } else {
              resolve();
            }
          };

          scroll();
        });
      },
      distance,
      duration
    );
  }

  async executeAction(event) {
    const elapsed = Date.now() - this.startTime;
    const elapsedSeconds = (elapsed / 1000).toFixed(1);

    console.log(`\n⏱️  ${elapsedSeconds}s | ${event.action}: ${event.narration || event.target}`);

    switch (event.action) {
      case "load":
        await this.page.goto(this.config.baseUrl, {
          waitUntil: "networkidle2",
          timeout: 20000,
        });
        break;

      case "wait":
        // Just pause at current position
        await this.wait(2);
        break;

      case "scroll":
        await this.smoothScroll(event.distance || 400, (event.duration || 2) * 1000);
        break;

      case "click":
        try {
          // Try to find and click the element
          const selector = this.getSelector(event.target);
          await this.page.waitForSelector(selector, { timeout: 5000 });
          await this.page.click(selector);
          await this.wait(1);
        } catch (e) {
          console.log(`   ⚠️  Could not click ${event.target}: ${e.message}`);
        }
        break;

      case "highlight":
        try {
          const selector = this.getSelector(event.target);
          await this.page.evaluate((sel) => {
            const element = document.querySelector(sel);
            if (element) {
              element.style.boxShadow = "0 0 20px 5px rgba(59, 130, 246, 0.8)";
              element.style.transition = "box-shadow 0.3s ease-in-out";
              setTimeout(() => {
                element.style.boxShadow = "";
              }, 2000);
            }
          }, selector);
          await this.wait(2);
        } catch (e) {
          console.log(`   ⚠️  Could not highlight ${event.target}`);
        }
        break;

      default:
        console.log(`   ⚠️  Unknown action: ${event.action}`);
    }
  }

  getSelector(target) {
    // Map target names to CSS selectors
    const selectorMap = {
      dashboard: "body",
      hero_section: "main",
      watchlist: '[data-testid="watchlist"], .watchlist',
      impact_card: '[data-testid="impact-card"], .impact-card, article:first-of-type',
      impact_card_expand: "button:first-of-type",
      news_tab: '[role="tab"][data-value="news"], button:contains("News")',
      analysis_tab: '[role="tab"][data-value="analysis"], button:contains("Analysis")',
      actions_tab: '[role="tab"][data-value="actions"], button:contains("Actions")',
      analysis_content: ".analysis-content",
      actions_list: ".actions-list",
    };

    return selectorMap[target] || target;
  }

  async executeTimeline() {
    console.log("\n🎬 Starting timeline execution");
    console.log(`   Scenario: ${this.timeline.description}`);
    console.log(`   Duration: ${this.timeline.duration_seconds}s\n`);

    this.startTime = Date.now();

    let lastTimestamp = 0;

    for (const event of this.timeline.timeline) {
      // Wait until the event timestamp
      const waitTime = event.timestamp - lastTimestamp;
      if (waitTime > 0) {
        await this.wait(waitTime);
      }

      // Execute the action
      await this.executeAction(event);

      lastTimestamp = event.timestamp;
    }

    // Wait a bit at the end
    await this.wait(2);

    const totalTime = ((Date.now() - this.startTime) / 1000).toFixed(1);
    console.log(`\n🎉 Timeline completed in ${totalTime}s`);
  }

  async run() {
    console.log("=" .repeat(80));
    console.log("ENTERPRISE CIA - TIMELINE RECORDER");
    console.log("=" .repeat(80));
    console.log();

    try {
      await this.loadTimeline();
      await this.setupBrowser();
      await this.setupRecorder();

      console.log(`\n🎬 Recording started → ${this.videoPath}\n`);
      await this.recorder.start(this.videoPath);

      await this.executeTimeline();

      console.log("\n🛑 Stopping recording...");
      await this.recorder.stop();
      console.log("✅ Recording saved successfully");

      // Get file stats
      const stats = require("fs").statSync(this.videoPath);
      const sizeInMB = (stats.size / (1024 * 1024)).toFixed(2);

      console.log("\n" + "=".repeat(80));
      console.log("✅ RECORDING COMPLETE!");
      console.log("=".repeat(80));
      console.log(`\n🎥 Video saved: ${this.videoPath}`);
      console.log(`📊 File size: ${sizeInMB} MB\n`);
    } catch (error) {
      console.error(`\n❌ Recording failed: ${error.message}`);
      console.error(error.stack);
      throw error;
    } finally {
      if (this.browser) {
        console.log("🧹 Cleaning up...");
        await this.browser.close();
        console.log("   ✓ Browser closed");
      }
    }
  }
}

// Main execution
async function main() {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    console.error("Usage: node timeline_recorder.js <timeline.json>");
    console.error("\nExample:");
    console.error("  node scripts/Claude/timeline_recorder.js demo_videos/competitor_product_launch_timeline.json");
    process.exit(1);
  }

  const timelinePath = args[0];

  // Check if file exists
  try {
    await fs.access(timelinePath);
  } catch (e) {
    console.error(`Error: Timeline file not found: ${timelinePath}`);
    process.exit(1);
  }

  const recorder = new TimelineRecorder(timelinePath);
  await recorder.run();
}

// Run if called directly
if (require.main === module) {
  main().catch((error) => {
    console.error("\n❌ Fatal error:", error);
    process.exit(1);
  });
}

module.exports = { TimelineRecorder };
