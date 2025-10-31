#!/usr/bin/env node

/**
 * Working Demo Script - Uses Puppeteer with better Chrome configuration
 */

const puppeteer = require("puppeteer");
const fs = require("fs").promises;
const path = require("path");
const os = require("os");

class WorkingDemo {
  constructor() {
    this.browser = null;
    this.page = null;
    this.screenshotDir = "demo_screenshots";
    this.baseUrl = "http://localhost:3000";
    this.screenshotCounter = 1;
    this.platform = os.platform();
  }

  async initialize() {
    console.log(`🚀 Starting working demo on ${this.platform}...`);

    // Create directories
    await fs.mkdir(this.screenshotDir, { recursive: true });

    try {
      console.log("🌐 Launching browser with minimal configuration...");

      // Use a much simpler browser configuration
      this.browser = await puppeteer.launch({
        headless: false,
        defaultViewport: null,
        args: [
          "--no-sandbox",
          "--disable-setuid-sandbox",
          "--disable-dev-shm-usage",
          "--start-maximized",
        ],
        ignoreDefaultArgs: ["--disable-extensions"],
        timeout: 60000,
      });

      const pages = await this.browser.pages();
      this.page = pages[0] || (await this.browser.newPage());

      console.log("✅ Browser launched successfully");
      return true;
    } catch (error) {
      console.error("❌ Browser launch failed:", error.message);
      return false;
    }
  }

  async takeScreenshot(name, description = "") {
    if (!this.page) {
      console.log(`⚠️ Cannot take screenshot - page not available`);
      return null;
    }

    try {
      const filename = `${String(this.screenshotCounter).padStart(
        2,
        "0"
      )}_${name}.png`;
      const filepath = path.join(this.screenshotDir, filename);

      await this.page.screenshot({
        path: filepath,
        fullPage: false,
      });

      console.log(`📸 Screenshot: ${filename} - ${description}`);
      this.screenshotCounter++;
      return filepath;
    } catch (error) {
      console.log(`⚠️ Screenshot failed: ${error.message}`);
      return null;
    }
  }

  async wait(seconds) {
    console.log(`⏳ Waiting ${seconds} seconds...`);
    await new Promise((resolve) => setTimeout(resolve, seconds * 1000));
  }

  async runDemo() {
    console.log("\n🎬 Running Demo Sequence");

    try {
      // Navigate to the application
      console.log("🌐 Navigating to application...");
      await this.page.goto(this.baseUrl, {
        waitUntil: "networkidle0",
        timeout: 30000,
      });

      await this.takeScreenshot("01_homepage", "Enterprise CIA Homepage");
      console.log("✅ Successfully loaded the application");

      await this.wait(3);

      // Try to find and interact with elements
      console.log("🔍 Looking for interactive elements...");

      try {
        // Look for buttons
        const buttons = await this.page.$$("button");
        console.log(`Found ${buttons.length} buttons`);

        if (buttons.length > 0) {
          console.log("🖱️ Clicking first button...");
          await buttons[0].click();
          await this.wait(2);
          await this.takeScreenshot("02_button_click", "After clicking button");
        }

        // Look for inputs
        const inputs = await this.page.$$("input");
        console.log(`Found ${inputs.length} input fields`);

        if (inputs.length > 0) {
          console.log("⌨️ Typing in first input...");
          await inputs[0].focus();
          await inputs[0].type("OpenAI", { delay: 100 });
          await this.wait(2);
          await this.takeScreenshot("03_input_typing", "After typing in input");
        }

        // Look for links
        const links = await this.page.$$("a");
        console.log(`Found ${links.length} links`);
      } catch (error) {
        console.log(`Interaction error: ${error.message}`);
      }

      // Take some final screenshots
      await this.takeScreenshot("04_final_state", "Final application state");

      console.log("🎉 Demo completed successfully!");
    } catch (error) {
      console.log(`Demo error: ${error.message}`);
      await this.takeScreenshot("error", "Error state");
    }
  }

  async run() {
    const initialized = await this.initialize();

    if (!initialized) {
      console.log("❌ Could not initialize browser. Exiting.");
      return;
    }

    try {
      await this.runDemo();
    } catch (error) {
      console.error("❌ Demo failed:", error);
    } finally {
      if (this.browser) {
        console.log("🔒 Closing browser...");
        await this.browser.close();
      }
    }

    console.log(`📸 Screenshots saved to: ${this.screenshotDir}/`);
  }
}

// Execute the demo
if (require.main === module) {
  const demo = new WorkingDemo();
  demo.run().catch(console.error);
}

module.exports = WorkingDemo;
