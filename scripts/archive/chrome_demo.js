#!/usr/bin/env node

/**
 * Chrome Demo Script - Uses explicit Chrome path for macOS
 */

const puppeteer = require("puppeteer");
const fs = require("fs").promises;
const path = require("path");
const os = require("os");

class ChromeDemo {
  constructor() {
    this.browser = null;
    this.page = null;
    this.screenshotDir = "demo_screenshots";
    this.baseUrl = "http://localhost:3000";
    this.screenshotCounter = 1;
    this.platform = os.platform();
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
    console.log(`🚀 Starting Chrome demo on ${this.platform}...`);

    // Create directories
    await fs.mkdir(this.screenshotDir, { recursive: true });

    const chromePath = this.getChromePath();
    console.log(`🔍 Using Chrome at: ${chromePath}`);

    try {
      console.log("🌐 Launching Chrome with explicit path...");

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

      console.log("✅ Chrome launched successfully");
      return true;
    } catch (error) {
      console.error("❌ Chrome launch failed:", error.message);
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
    console.log("\n🎬 Running Enterprise CIA Demo");

    try {
      // Navigate to the application
      console.log("🌐 Navigating to Enterprise CIA...");
      await this.page.goto(this.baseUrl, {
        waitUntil: "networkidle2",
        timeout: 15000,
      });

      await this.takeScreenshot("homepage", "Enterprise CIA Dashboard");
      console.log("✅ Successfully loaded Enterprise CIA");

      await this.wait(3);

      // Get page title and content
      const title = await this.page.title();
      console.log(`📄 Page title: ${title}`);

      // Look for specific Enterprise CIA elements
      console.log("🔍 Analyzing page content...");

      try {
        // Check for watchlist elements
        const watchlistElements = await this.page.$$(
          '[data-testid*="watch"], [class*="watch"], [id*="watch"]'
        );
        console.log(
          `Found ${watchlistElements.length} watchlist-related elements`
        );

        // Check for competitor elements
        const competitorElements = await this.page.$$(
          '[data-testid*="competitor"], [class*="competitor"], [id*="competitor"]'
        );
        console.log(
          `Found ${competitorElements.length} competitor-related elements`
        );

        // Check for impact card elements
        const impactElements = await this.page.$$(
          '[data-testid*="impact"], [class*="impact"], [id*="impact"]'
        );
        console.log(`Found ${impactElements.length} impact-related elements`);

        // Look for buttons and inputs
        const buttons = await this.page.$$("button");
        const inputs = await this.page.$$("input");
        console.log(
          `Found ${buttons.length} buttons and ${inputs.length} inputs`
        );

        // Try to interact with the first few elements
        if (buttons.length > 0) {
          console.log("🖱️ Clicking first button...");
          const buttonText = await buttons[0].evaluate(
            (el) => el.textContent || el.value || "Button"
          );
          console.log(`Button text: ${buttonText}`);

          await buttons[0].click();
          await this.wait(2);
          await this.takeScreenshot("button_clicked", `Clicked: ${buttonText}`);
        }

        if (inputs.length > 0) {
          console.log("⌨️ Typing in first input...");
          await inputs[0].focus();
          await inputs[0].type("OpenAI", { delay: 100 });
          await this.wait(2);
          await this.takeScreenshot("input_filled", "Added competitor: OpenAI");
        }

        // Look for any forms to submit
        const forms = await this.page.$$("form");
        if (forms.length > 0) {
          console.log("📝 Found form, attempting to interact...");
          // Don't submit, just take a screenshot
          await this.takeScreenshot("form_ready", "Form ready for submission");
        }
      } catch (error) {
        console.log(`Interaction error: ${error.message}`);
      }

      // Take final screenshots
      await this.takeScreenshot("final_state", "Final Enterprise CIA state");

      // Scroll down to see more content
      await this.page.evaluate(() =>
        window.scrollTo(0, document.body.scrollHeight)
      );
      await this.wait(1);
      await this.takeScreenshot(
        "scrolled_view",
        "Scrolled view of application"
      );

      console.log("🎉 Demo completed successfully!");
    } catch (error) {
      console.log(`Demo error: ${error.message}`);
      await this.takeScreenshot("error", "Error state");
    }
  }

  async run() {
    const initialized = await this.initialize();

    if (!initialized) {
      console.log("❌ Could not initialize Chrome. Please check:");
      console.log("1. Chrome is installed");
      console.log("2. No other Chrome instances are running");
      console.log("3. System permissions allow Chrome automation");
      return;
    }

    try {
      await this.runDemo();
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

    console.log(`\n📸 Screenshots saved to: ${this.screenshotDir}/`);
    console.log(
      "🎬 Demo complete! Check the screenshots for the captured demo."
    );
  }
}

// Execute the demo
if (require.main === module) {
  const demo = new ChromeDemo();
  demo.run().catch(console.error);
}

module.exports = ChromeDemo;
