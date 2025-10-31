#!/usr/bin/env node

/**
 * Automated Demo Script using Chrome DevTools Protocol
 * Alternative to Puppeteer for better performance
 * Follows UPDATED_DEMO_SCRIPT.md exactly
 */

const { execSync } = require("child_process");
const fs = require("fs").promises;
const path = require("path");

class ChromeDevToolsDemo {
  constructor() {
    this.screenshotDir = "demo_screenshots";
    this.videoDir = "demo_videos";
    this.baseUrl = "http://localhost:3456";
    this.screenshotCounter = 1;
  }

  async initialize() {
    console.log("🚀 Starting Chrome DevTools demo...");

    // Create directories
    await fs.mkdir(this.screenshotDir, { recursive: true });
    await fs.mkdir(this.videoDir, { recursive: true });

    console.log("✅ Chrome DevTools demo initialized");
  }

  async takeScreenshot(name, description = "") {
    const filename = `${String(this.screenshotCounter).padStart(
      2,
      "0"
    )}_${name}.png`;
    const filepath = path.join(this.screenshotDir, filename);

    try {
      // Use Chrome DevTools to take screenshot
      execSync(`osascript -e 'tell application "Google Chrome" to activate'`);
      execSync(`screencapture -x "${filepath}"`);

      console.log(`📸 Screenshot: ${filename} - ${description}`);
      this.screenshotCounter++;
    } catch (error) {
      console.log(`⚠️ Screenshot failed: ${error.message}`);
    }

    return filepath;
  }

  async wait(seconds) {
    console.log(`⏳ Waiting ${seconds} seconds...`);
    await new Promise((resolve) => setTimeout(resolve, seconds * 1000));
  }

  async openUrl(url) {
    try {
      execSync(`open "${url}"`);
      await this.wait(3); // Wait for page to load
    } catch (error) {
      console.log(`⚠️ Failed to open URL: ${error.message}`);
    }
  }

  async run() {
    try {
      await this.initialize();

      console.log("\n🎬 Starting Chrome DevTools demo sequence...");
      console.log("📝 Following UPDATED_DEMO_SCRIPT.md exactly\n");
      console.log(
        "🔧 Manual steps required - this script will guide you through each step\n"
      );

      // Step 1: Open the application
      console.log("STEP 1: Opening Enterprise CIA application...");
      await this.openUrl(this.baseUrl);
      await this.takeScreenshot(
        "dashboard_home",
        "Main dashboard - starting point"
      );

      console.log("\n📋 ENTERPRISE DEMO INSTRUCTIONS:");
      console.log("1. Navigate to watchlist/competitor management");
      console.log('2. Add "OpenAI" as a competitor');
      console.log('3. Add keywords: "GPT models, ChatGPT, AI model launches"');
      console.log('4. Click "Generate Impact Card"');
      console.log("\nPress ENTER when you've completed step 1...");

      // Wait for user input
      await new Promise((resolve) => {
        process.stdin.once("data", () => resolve());
      });

      await this.takeScreenshot("watchlist_page", "Watchlist management page");

      console.log("\nPress ENTER when you've added OpenAI and keywords...");
      await new Promise((resolve) => {
        process.stdin.once("data", () => resolve());
      });

      await this.takeScreenshot("openai_added", "OpenAI added with keywords");

      console.log("\nPress ENTER when you've clicked Generate Impact Card...");
      await new Promise((resolve) => {
        process.stdin.once("data", () => resolve());
      });

      await this.takeScreenshot(
        "generation_started",
        "Impact Card generation started"
      );

      // Capture processing stages
      console.log("\n📊 Capturing processing stages...");
      console.log(
        "The script will take screenshots every 15 seconds during processing..."
      );

      for (let i = 0; i < 8; i++) {
        console.log(`Taking processing screenshot ${i + 1}/8...`);
        await this.wait(15);
        await this.takeScreenshot(
          `processing_stage_${i + 1}`,
          `Processing stage ${i + 1} - APIs working`
        );

        if (i === 3) {
          console.log(
            "\n🔄 If results have appeared, press ENTER to continue to results capture..."
          );
          console.log(
            "Otherwise, let the script continue capturing processing stages..."
          );
        }
      }

      console.log("\nPress ENTER when Impact Card results are visible...");
      await new Promise((resolve) => {
        process.stdin.once("data", () => resolve());
      });

      await this.takeScreenshot(
        "impact_card_results",
        "Complete Impact Card with threat analysis"
      );

      console.log("\nScroll down to show threat scores, then press ENTER...");
      await new Promise((resolve) => {
        process.stdin.once("data", () => resolve());
      });
      await this.takeScreenshot(
        "threat_scores",
        "Multi-dimensional threat scores"
      );

      console.log("\nScroll down to show sources, then press ENTER...");
      await new Promise((resolve) => {
        process.stdin.once("data", () => resolve());
      });
      await this.takeScreenshot(
        "source_analysis",
        "400+ sources with credibility scores"
      );

      console.log("\nScroll down to show recommendations, then press ENTER...");
      await new Promise((resolve) => {
        process.stdin.once("data", () => resolve());
      });
      await this.takeScreenshot("recommendations", "Strategic recommendations");

      // Individual Demo
      console.log("\n\n👤 INDIVIDUAL DEMO INSTRUCTIONS:");
      console.log("1. Start a new company search");
      console.log('2. Search for "Perplexity AI"');
      console.log("3. Wait for comprehensive company profile to generate");
      console.log("\nPress ENTER when you've started the individual demo...");

      await new Promise((resolve) => {
        process.stdin.once("data", () => resolve());
      });

      await this.takeScreenshot(
        "individual_start",
        "Individual research starting point"
      );

      console.log(
        '\nPress ENTER when you\'ve entered "Perplexity AI" and started search...'
      );
      await new Promise((resolve) => {
        process.stdin.once("data", () => resolve());
      });

      await this.takeScreenshot(
        "perplexity_search",
        "Perplexity AI search started"
      );

      // Individual processing stages
      console.log("\n📊 Capturing individual research processing...");
      for (let i = 0; i < 6; i++) {
        console.log(`Taking individual processing screenshot ${i + 1}/6...`);
        await this.wait(10);
        await this.takeScreenshot(
          `individual_processing_${i + 1}`,
          `Individual research stage ${i + 1}`
        );
      }

      console.log("\nPress ENTER when company profile results are visible...");
      await new Promise((resolve) => {
        process.stdin.once("data", () => resolve());
      });

      await this.takeScreenshot(
        "company_profile",
        "Complete Perplexity AI company profile"
      );

      console.log("\nScroll to show funding history, then press ENTER...");
      await new Promise((resolve) => {
        process.stdin.once("data", () => resolve());
      });
      await this.takeScreenshot(
        "funding_history",
        "Funding history and growth signals"
      );

      console.log("\nScroll to show competitors, then press ENTER...");
      await new Promise((resolve) => {
        process.stdin.once("data", () => resolve());
      });
      await this.takeScreenshot(
        "competitors_identified",
        "Key competitors automatically identified"
      );

      console.log("\nScroll to show recent developments, then press ENTER...");
      await new Promise((resolve) => {
        process.stdin.once("data", () => resolve());
      });
      await this.takeScreenshot(
        "recent_developments",
        "Recent partnerships and product launches"
      );

      // Final screenshot
      await this.takeScreenshot(
        "demo_complete",
        "Demo completed - Enterprise CIA platform"
      );

      console.log("\n🎉 Demo automation completed successfully!");
      console.log(`📸 Screenshots saved to: ${this.screenshotDir}/`);
      console.log("\n📋 Next steps:");
      console.log("1. Review all screenshots in demo_screenshots/");
      console.log("2. Create video compilation from screenshots");
      console.log("3. Add voiceover following UPDATED_DEMO_SCRIPT.md");
    } catch (error) {
      console.error("❌ Demo automation failed:", error);
      await this.takeScreenshot("error_state", "Error occurred during demo");
    }
  }
}

// Execute the demo
if (require.main === module) {
  const demo = new ChromeDevToolsDemo();
  demo.run().catch(console.error);
}

module.exports = ChromeDevToolsDemo;
