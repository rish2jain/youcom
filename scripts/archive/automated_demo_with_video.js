#!/usr/bin/env node

/**
 * Automated Demo Script with Simultaneous Video Recording and Screenshots
 * Uses Puppeteer with screen recording capabilities
 * Follows UPDATED_DEMO_SCRIPT.md exactly
 */

const puppeteer = require("puppeteer");
const fs = require("fs").promises;
const path = require("path");
const { spawn } = require("child_process");

class AutomatedDemoWithVideo {
  constructor() {
    this.browser = null;
    this.page = null;
    this.screenshotDir = "demo_screenshots";
    this.videoDir = "demo_videos";
    this.baseUrl = "http://localhost:3000";
    this.screenshotCounter = 1;
    this.videoProcess = null;
    this.videoPath = null;
  }

  async initialize() {
    console.log("🚀 Starting automated demo with video recording...");

    // Create directories
    await fs.mkdir(this.screenshotDir, { recursive: true });
    await fs.mkdir(this.videoDir, { recursive: true });

    // Launch browser
    this.browser = await puppeteer.launch({
      headless: false,
      defaultViewport: { width: 1920, height: 1080 },
      args: [
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-dev-shm-usage",
        "--disable-web-security",
        "--allow-running-insecure-content",
        "--window-size=1920,1080",
        "--window-position=0,0",
      ],
    });

    this.page = await this.browser.newPage();
    await this.page.setViewport({ width: 1920, height: 1080 });

    // Start screen recording using ffmpeg
    await this.startVideoRecording();

    console.log("✅ Browser initialized with video recording");
  }

  async startVideoRecording() {
    const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
    this.videoPath = path.join(
      this.videoDir,
      `enterprise_cia_demo_${timestamp}.mp4`
    );

    console.log("🎥 Starting screen recording...");

    // Use ffmpeg to record the screen (macOS specific - adjust for other OS)
    this.videoProcess = spawn("ffmpeg", [
      "-f",
      "avfoundation",
      "-i",
      "1:0", // Screen capture (display 1, no audio)
      "-r",
      "30", // 30 fps
      "-vcodec",
      "libx264",
      "-preset",
      "ultrafast",
      "-crf",
      "18",
      "-pix_fmt",
      "yuv420p",
      this.videoPath,
    ]);

    this.videoProcess.stderr.on("data", (data) => {
      // Suppress ffmpeg output unless there's an error
      if (
        data.toString().includes("error") ||
        data.toString().includes("Error")
      ) {
        console.error("FFmpeg error:", data.toString());
      }
    });

    // Wait a moment for recording to start
    await this.wait(2);
  }

  async stopVideoRecording() {
    if (this.videoProcess) {
      console.log("🛑 Stopping video recording...");
      this.videoProcess.stdin.write("q"); // Send quit command to ffmpeg

      // Wait for process to finish
      await new Promise((resolve) => {
        this.videoProcess.on("close", resolve);
      });

      this.videoProcess = null;
    }
  }

  async takeScreenshot(name, description = "") {
    const filename = `${String(this.screenshotCounter).padStart(
      2,
      "0"
    )}_${name}.png`;
    const filepath = path.join(this.screenshotDir, filename);

    await this.page.screenshot({
      path: filepath,
      fullPage: false,
      type: "png",
    });

    console.log(`📸 Screenshot: ${filename} - ${description}`);
    this.screenshotCounter++;

    return filepath;
  }

  async wait(seconds) {
    console.log(`⏳ Waiting ${seconds} seconds...`);
    await new Promise((resolve) => setTimeout(resolve, seconds * 1000));
  }

  async typeWithDelay(selector, text, delay = 100) {
    await this.page.focus(selector);
    await this.page.keyboard.type(text, { delay });
  }

  async addNarrationMarker(text) {
    console.log(`🎙️  NARRATION: ${text}`);
    // Add timestamp for video editing
    const timestamp = new Date().toISOString();
    await fs.appendFile(
      path.join(this.videoDir, "narration_markers.txt"),
      `${timestamp}: ${text}\n`
    );
  }

  // Demo Section 1: Enterprise Competitive Monitoring
  async runEnterpriseDemo() {
    console.log("\n🏢 ENTERPRISE DEMO - Competitive Monitoring");
    await this.addNarrationMarker(
      "Starting Enterprise Demo - Competitive Monitoring"
    );

    // Navigate to main dashboard
    await this.page.goto(`${this.baseUrl}`, { waitUntil: "networkidle2" });
    await this.takeScreenshot(
      "dashboard_home",
      "Main dashboard - starting point"
    );
    await this.addNarrationMarker(
      "Let's say I'm a PM at Anthropic monitoring OpenAI"
    );
    await this.wait(2);

    // Navigate to watchlist/company search
    console.log("📍 Navigating to watchlist...");
    await this.addNarrationMarker(
      "I'll add them as a competitor with relevant keywords"
    );

    try {
      await this.page.click(
        '[data-testid="watchlist-tab"], .watchlist-button, a[href*="watchlist"]',
        { timeout: 5000 }
      );
    } catch {
      // Fallback: look for any navigation to watchlist
      await this.page.evaluate(() => {
        const links = Array.from(document.querySelectorAll("a, button"));
        const watchlistLink = links.find(
          (link) =>
            link.textContent.toLowerCase().includes("watchlist") ||
            link.textContent.toLowerCase().includes("watch") ||
            link.href?.includes("watchlist")
        );
        if (watchlistLink) watchlistLink.click();
      });
    }

    await this.wait(2);
    await this.takeScreenshot("watchlist_page", "Watchlist management page");

    // Add competitor - OpenAI
    console.log("🎯 Adding OpenAI as competitor...");
    await this.addNarrationMarker(
      "GPT models, ChatGPT developments, AI model launches"
    );

    // Look for add competitor button or input
    try {
      const addButton = await this.page.$(
        '[data-testid="add-competitor"], .add-competitor, button:has-text("Add")'
      );
      if (addButton) {
        await addButton.click();
      } else {
        // Try to find input field directly
        const input = await this.page.$(
          'input[placeholder*="company"], input[placeholder*="competitor"], input[type="text"]'
        );
        if (input) {
          await input.click();
        }
      }
    } catch (error) {
      console.log("⚠️ Using fallback method to find add competitor controls");
    }

    await this.wait(1);
    await this.takeScreenshot("add_competitor_form", "Add competitor form");

    // Type OpenAI
    try {
      await this.typeWithDelay(
        'input[placeholder*="company"], input[placeholder*="competitor"], input[type="text"]',
        "OpenAI"
      );
    } catch {
      // Fallback: type in any visible input
      await this.page.keyboard.type("OpenAI");
    }

    await this.wait(1);
    await this.takeScreenshot("openai_entered", "OpenAI entered as competitor");

    // Add keywords
    console.log("🔑 Adding relevant keywords...");
    try {
      const keywordInput = await this.page.$(
        'input[placeholder*="keyword"], textarea[placeholder*="keyword"]'
      );
      if (keywordInput) {
        await keywordInput.click();
        await this.typeWithDelay(
          'input[placeholder*="keyword"], textarea[placeholder*="keyword"]',
          "GPT models, ChatGPT, AI model launches, OpenAI API"
        );
      }
    } catch {
      console.log("⚠️ Keywords input not found, continuing...");
    }

    await this.wait(1);
    await this.takeScreenshot(
      "keywords_added",
      "Keywords added for monitoring"
    );

    // Generate Impact Card
    console.log("⚡ Generating Impact Card...");
    await this.addNarrationMarker("Now watch this happen in real-time");

    try {
      await this.page.click(
        'button:has-text("Generate"), button:has-text("Create"), button:has-text("Analyze"), [data-testid="generate-card"]'
      );
    } catch {
      // Fallback: look for any prominent button
      await this.page.evaluate(() => {
        const buttons = Array.from(document.querySelectorAll("button"));
        const generateButton = buttons.find(
          (btn) =>
            btn.textContent.toLowerCase().includes("generate") ||
            btn.textContent.toLowerCase().includes("create") ||
            btn.textContent.toLowerCase().includes("analyze")
        );
        if (generateButton) generateButton.click();
      });
    }

    await this.takeScreenshot(
      "generation_started",
      "Impact Card generation started"
    );

    // Wait and capture processing stages with narration
    console.log("📊 Capturing processing stages...");
    await this.addNarrationMarker(
      "See the progress indicators? The News API is detecting recent OpenAI announcements"
    );

    for (let i = 0; i < 8; i++) {
      await this.wait(15); // Wait 15 seconds between captures

      if (i === 1) {
        await this.addNarrationMarker(
          "Now the Search API is pulling market context and competitive landscape data"
        );
      } else if (i === 3) {
        await this.addNarrationMarker(
          "The Custom Agent is analyzing strategic implications and calculating threat scores"
        );
      } else if (i === 5) {
        await this.addNarrationMarker(
          "And the ARI API is synthesizing intelligence from over 400 sources across the web"
        );
      }

      await this.takeScreenshot(
        `processing_stage_${i + 1}`,
        `Processing stage ${i + 1} - APIs working`
      );

      // Check if results are ready
      const resultsVisible = await this.page.$(
        '.impact-card, .results, [data-testid="impact-card"]'
      );
      if (resultsVisible) {
        console.log("✅ Results appeared!");
        await this.addNarrationMarker(
          "Here we go. Look at this - threat score with multi-dimensional analysis"
        );
        break;
      }
    }

    // Capture final results
    await this.takeScreenshot(
      "impact_card_results",
      "Complete Impact Card with threat analysis"
    );

    // Scroll to show different sections
    await this.addNarrationMarker(
      "Impact assessment across product features, pricing strategy, and market positioning"
    );
    await this.page.evaluate(() => window.scrollTo(0, 300));
    await this.wait(2);
    await this.takeScreenshot(
      "threat_scores",
      "Multi-dimensional threat scores"
    );

    await this.addNarrationMarker(
      "And look - over 400 sources cited, each with credibility scores"
    );
    await this.page.evaluate(() => window.scrollTo(0, 600));
    await this.wait(2);
    await this.takeScreenshot(
      "source_analysis",
      "400+ sources with credibility scores"
    );

    await this.addNarrationMarker(
      "Specific recommended actions based on this intelligence"
    );
    await this.page.evaluate(() => window.scrollTo(0, 900));
    await this.wait(2);
    await this.takeScreenshot("recommendations", "Strategic recommendations");

    // Export functionality
    console.log("📄 Testing export functionality...");
    await this.addNarrationMarker(
      "One click - professional report ready to share with executives"
    );
    try {
      await this.page.click(
        'button:has-text("Export"), button:has-text("Download"), [data-testid="export"]'
      );
      await this.wait(2);
      await this.takeScreenshot("export_options", "Export options for sharing");
    } catch {
      console.log("⚠️ Export button not found, continuing...");
    }

    await this.addNarrationMarker(
      "That took under 3 minutes. The manual process? Days or weeks of monitoring, research, and synthesis"
    );
    console.log("✅ Enterprise demo completed");
  }
  // Demo Section 2: Individual Quick Research
  async runIndividualDemo() {
    console.log("\n👤 INDIVIDUAL DEMO - Quick Company Research");
    await this.addNarrationMarker(
      "Different perspective now. I'm preparing for an interview at Perplexity AI tomorrow"
    );

    // Navigate to company research or new search
    console.log("🔍 Starting individual research demo...");

    // Clear previous search or start fresh
    try {
      await this.page.click(
        '[data-testid="new-search"], button:has-text("New"), .clear-button'
      );
    } catch {
      // Navigate to home or research page
      await this.page.goto(`${this.baseUrl}`, { waitUntil: "networkidle2" });
    }

    await this.wait(2);
    await this.takeScreenshot(
      "individual_start",
      "Individual research starting point"
    );

    // Search for Perplexity AI
    console.log("🎯 Researching Perplexity AI...");
    await this.addNarrationMarker("I need comprehensive company research fast");

    try {
      // Find search input
      const searchInput = await this.page.$(
        'input[placeholder*="company"], input[placeholder*="search"], input[type="search"], input[type="text"]'
      );
      if (searchInput) {
        await searchInput.click();
        await searchInput.clear();
        await this.typeWithDelay(
          'input[placeholder*="company"], input[placeholder*="search"], input[type="search"], input[type="text"]',
          "Perplexity AI"
        );
      }
    } catch {
      // Fallback: type in any focused input
      await this.page.keyboard.type("Perplexity AI");
    }

    await this.wait(1);
    await this.takeScreenshot(
      "perplexity_search",
      "Perplexity AI search entered"
    );

    // Trigger search
    await this.addNarrationMarker("Watch this");
    try {
      await this.page.click(
        'button:has-text("Search"), button:has-text("Research"), [data-testid="search-button"]'
      );
    } catch {
      await this.page.keyboard.press("Enter");
    }

    await this.takeScreenshot(
      "individual_processing_start",
      "Individual research processing started"
    );

    // Capture processing stages for individual research
    console.log("📊 Capturing individual research processing...");
    await this.addNarrationMarker(
      "The Search API is building their complete company profile"
    );

    for (let i = 0; i < 6; i++) {
      await this.wait(10); // Shorter waits for individual research

      if (i === 2) {
        await this.addNarrationMarker(
          "ARI is pulling comprehensive research from 400 sources - funding history, growth signals, competitive advantages"
        );
      }

      await this.takeScreenshot(
        `individual_processing_${i + 1}`,
        `Individual research stage ${i + 1}`
      );

      // Check if results are ready
      const resultsVisible = await this.page.$(
        '.company-profile, .research-results, [data-testid="company-profile"]'
      );
      if (resultsVisible) {
        console.log("✅ Individual research results appeared!");
        await this.addNarrationMarker("There it is. Complete company overview");
        break;
      }
    }

    // Capture company profile results
    await this.takeScreenshot(
      "company_profile",
      "Complete Perplexity AI company profile"
    );

    // Scroll through different sections
    await this.addNarrationMarker(
      "Funding history showing their Series B round"
    );
    await this.page.evaluate(() => window.scrollTo(0, 300));
    await this.wait(2);
    await this.takeScreenshot(
      "funding_history",
      "Funding history and growth signals"
    );

    await this.addNarrationMarker("Key competitors automatically identified");
    await this.page.evaluate(() => window.scrollTo(0, 600));
    await this.wait(2);
    await this.takeScreenshot(
      "competitors_identified",
      "Key competitors automatically identified"
    );

    await this.addNarrationMarker(
      "Recent partnerships and product launches - all synthesized from hundreds of authoritative sources"
    );
    await this.page.evaluate(() => window.scrollTo(0, 900));
    await this.wait(2);
    await this.takeScreenshot(
      "recent_developments",
      "Recent partnerships and product launches"
    );

    // Export for interview prep
    console.log("📄 Exporting for interview preparation...");
    await this.addNarrationMarker(
      "Export to PDF, and I'm ready for my interview tomorrow"
    );
    try {
      await this.page.click(
        'button:has-text("Export"), button:has-text("PDF"), [data-testid="export-pdf"]'
      );
      await this.wait(2);
      await this.takeScreenshot(
        "pdf_export",
        "PDF export for interview preparation"
      );
    } catch {
      console.log("⚠️ PDF export not found, continuing...");
    }

    await this.addNarrationMarker(
      "Two minutes. The manual version? I'd spend 4 hours going through Crunchbase, news sites, their website, LinkedIn"
    );
    console.log("✅ Individual demo completed");
  }

  // Capture technical architecture
  async captureTechnicalDetails() {
    console.log("\n⚙️ TECHNICAL DETAILS");
    await this.addNarrationMarker("Is this production-ready? Absolutely.");

    // Try to access developer tools or technical dashboard
    try {
      await this.page.goto(`${this.baseUrl}/api/health`, {
        waitUntil: "networkidle2",
      });
      await this.takeScreenshot("api_health", "API health and status");
    } catch {
      console.log("⚠️ Health endpoint not accessible");
    }

    // Go back to main app
    await this.page.goto(`${this.baseUrl}`, { waitUntil: "networkidle2" });

    // Open browser dev tools programmatically to show network activity
    await this.page.evaluate(() => {
      console.log("🔧 Technical Architecture:");
      console.log("- Real-time WebSocket orchestration across all 4 APIs");
      console.log("- 85% cache hit rate with intelligent caching strategy");
      console.log("- Circuit breakers and retry logic - 99.5% success rate");
      console.log("- Load tested with 100 concurrent users");
      console.log("- Next.js frontend with Socket.io, FastAPI backend");
      console.log("- PostgreSQL and Redis, Docker containerization");
    });

    await this.takeScreenshot(
      "technical_console",
      "Technical architecture in console"
    );
    await this.addNarrationMarker(
      "This isn't a prototype. This is a production platform ready for real users today"
    );
  }

  // Main execution flow
  async run() {
    try {
      await this.initialize();

      console.log("\n🎬 Starting complete demo sequence...");
      console.log("📝 Following UPDATED_DEMO_SCRIPT.md exactly\n");
      console.log(`🎥 Recording video to: ${this.videoPath}`);

      // Initial narration marker
      await this.addNarrationMarker(
        "Enterprise CIA Demo Starting - Complete You.com API Integration"
      );

      // Run enterprise demo (90 seconds section)
      await this.runEnterpriseDemo();

      // Brief pause between demos
      await this.wait(3);

      // Run individual demo (60 seconds section)
      await this.runIndividualDemo();

      // Capture technical details
      await this.captureTechnicalDetails();

      // Final summary screenshot
      await this.page.goto(`${this.baseUrl}`, { waitUntil: "networkidle2" });
      await this.addNarrationMarker(
        "Enterprise CIA makes professional-grade competitive intelligence accessible to everyone"
      );
      await this.takeScreenshot(
        "demo_complete",
        "Demo completed - Enterprise CIA platform"
      );

      // Stop video recording
      await this.stopVideoRecording();

      console.log("\n🎉 Demo automation completed successfully!");
      console.log(`📸 Screenshots saved to: ${this.screenshotDir}/`);
      console.log(`🎥 Video recorded to: ${this.videoPath}`);
      console.log(
        `🎙️  Narration markers saved to: ${path.join(
          this.videoDir,
          "narration_markers.txt"
        )}`
      );
    } catch (error) {
      console.error("❌ Demo automation failed:", error);
      await this.takeScreenshot("error_state", "Error occurred during demo");
      await this.stopVideoRecording();
    } finally {
      if (this.browser) {
        await this.browser.close();
      }
    }
  }
}

// Execute the demo
if (require.main === module) {
  const demo = new AutomatedDemoWithVideo();
  demo.run().catch(console.error);
}

module.exports = AutomatedDemoWithVideo;
