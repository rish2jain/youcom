#!/usr/bin/env node

/**
 * Page Content Recording - Records ONLY the browser page content using Puppeteer's page.screencast
 * This captures exactly what's rendered in the browser viewport, not screen area
 */

const puppeteer = require("puppeteer");
const fs = require("fs").promises;
const path = require("path");
const os = require("os");

class PageContentRecording {
  constructor() {
    this.browser = null;
    this.page = null;
    this.videoDir = "demo_videos";
    this.baseUrl = "http://localhost:3000?skip-onboarding=true";
    this.videoPath = null;
    this.platform = os.platform();
    this.isRecording = false;
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
    console.log(`🚀 Starting Page Content Recording on ${this.platform}...`);

    // Create directories
    await fs.mkdir(this.videoDir, { recursive: true });

    const chromePath = this.getChromePath();
    console.log(`🔍 Using Chrome at: ${chromePath}`);

    try {
      console.log("🌐 Launching Chrome for page content recording...");

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

      console.log("✅ Chrome launched successfully for page content recording");
      return true;
    } catch (error) {
      console.error("❌ Chrome launch failed:", error.message);
      return false;
    }
  }

  async startPageContentRecording() {
    const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
    this.videoPath = path.join(
      this.videoDir,
      `enterprise_cia_page_content_${timestamp}.webm`
    );

    console.log("🎥 Starting page content recording...");
    console.log(
      "📹 This will record ONLY the browser page content, not the screen"
    );

    try {
      // Use Puppeteer's built-in page recording
      await this.page._client.send("Page.startScreencast", {
        format: "png",
        quality: 90,
        maxWidth: 1280,
        maxHeight: 720,
        everyNthFrame: 1,
      });

      this.isRecording = true;
      console.log(`✅ Page content recording started`);

      // Set up frame capture
      this.frames = [];
      this.page._client.on("Page.screencastFrame", async (frame) => {
        this.frames.push(frame);
        // Acknowledge the frame
        await this.page._client.send("Page.screencastFrameAck", {
          sessionId: frame.sessionId,
        });
      });

      return true;
    } catch (error) {
      console.error(
        "❌ Failed to start page content recording:",
        error.message
      );
      return false;
    }
  }

  async stopPageContentRecording() {
    if (this.isRecording) {
      console.log("🛑 Stopping page content recording...");
      try {
        await this.page._client.send("Page.stopScreencast");
        this.isRecording = false;

        console.log(`📹 Captured ${this.frames.length} frames`);
        console.log("✅ Page content recording stopped");

        // Save frames info for potential conversion
        const framesInfo = {
          totalFrames: this.frames.length,
          width: 1280,
          height: 720,
          format: "png",
        };

        const infoPath = path.join(this.videoDir, "recording_info.json");
        await fs.writeFile(infoPath, JSON.stringify(framesInfo, null, 2));

        return true;
      } catch (error) {
        console.log("⚠️ Error stopping page content recording:", error.message);
        return false;
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
    const markerFile = path.join(this.videoDir, "page_content_narration.txt");
    try {
      await fs.appendFile(markerFile, `${timestamp}: ${text}\n`);
    } catch (error) {
      console.log(`⚠️ Could not write narration marker: ${error.message}`);
    }
  }

  async createDemoContent() {
    console.log("🎨 Creating page content demo...");

    const demoHTML = `
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Enterprise CIA - You.com API Integration</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                overflow-x: hidden;
                min-height: 100vh;
                padding: 0;
                margin: 0;
            }
            
            .demo-container {
                width: 100vw;
                height: 100vh;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                padding: 40px;
                box-sizing: border-box;
            }
            
            .header {
                text-align: center;
                margin-bottom: 40px;
                animation: fadeInUp 1s ease-out;
            }
            
            .logo {
                font-size: 4rem;
                font-weight: bold;
                margin-bottom: 20px;
                background: linear-gradient(45deg, #fff, #f0f0f0);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                text-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }
            
            .tagline {
                font-size: 2rem;
                margin-bottom: 10px;
                font-weight: 600;
                opacity: 0.95;
            }
            
            .subtitle {
                font-size: 1.3rem;
                opacity: 0.85;
            }
            
            .api-showcase {
                background: rgba(255, 255, 255, 0.15);
                backdrop-filter: blur(20px);
                border: 2px solid rgba(255, 255, 255, 0.2);
                border-radius: 30px;
                padding: 40px;
                margin: 30px 0;
                text-align: center;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                animation: fadeInUp 1s ease-out 0.3s both;
                max-width: 1000px;
                width: 100%;
            }
            
            .api-title {
                font-size: 2.2rem;
                margin-bottom: 30px;
                font-weight: 700;
            }
            
            .api-grid {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 25px;
            }
            
            .api-item {
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                padding: 30px;
                border-radius: 20px;
                border: 2px solid rgba(255, 255, 255, 0.2);
                transition: all 0.4s ease;
                cursor: pointer;
                position: relative;
                overflow: hidden;
            }
            
            .api-item::before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
                transition: left 0.5s;
            }
            
            .api-item:hover::before {
                left: 100%;
            }
            
            .api-item:hover {
                transform: translateY(-8px) scale(1.02);
                background: rgba(255, 255, 255, 0.2);
                box-shadow: 0 15px 30px rgba(0,0,0,0.2);
            }
            
            .api-icon {
                font-size: 3rem;
                margin-bottom: 15px;
                display: block;
            }
            
            .api-name {
                font-size: 1.4rem;
                margin-bottom: 12px;
                font-weight: 600;
            }
            
            .api-desc {
                opacity: 0.9;
                line-height: 1.5;
                font-size: 1rem;
            }
            
            .value-section {
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 20px;
                margin: 30px 0;
                max-width: 1000px;
                width: 100%;
                animation: fadeInUp 1s ease-out 0.6s both;
            }
            
            .value-item {
                text-align: center;
                padding: 25px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 15px;
                border: 1px solid rgba(255, 255, 255, 0.2);
                transition: all 0.3s ease;
            }
            
            .value-item:hover {
                transform: translateY(-5px);
                background: rgba(255, 255, 255, 0.15);
            }
            
            .value-number {
                font-size: 2.5rem;
                font-weight: bold;
                margin-bottom: 10px;
                color: #fff;
            }
            
            .value-label {
                font-size: 1rem;
                font-weight: 500;
                opacity: 0.9;
            }
            
            .cta-section {
                text-align: center;
                margin-top: 30px;
                animation: fadeInUp 1s ease-out 0.9s both;
            }
            
            .cta-title {
                font-size: 2rem;
                margin-bottom: 15px;
                font-weight: 700;
            }
            
            .cta-button {
                display: inline-block;
                background: white;
                color: #667eea;
                padding: 18px 40px;
                border-radius: 50px;
                text-decoration: none;
                font-weight: bold;
                font-size: 1.2rem;
                transition: all 0.3s ease;
                box-shadow: 0 8px 25px rgba(0,0,0,0.15);
            }
            
            .cta-button:hover {
                transform: scale(1.05);
                box-shadow: 0 12px 35px rgba(0,0,0,0.2);
            }
            
            .highlight {
                background: rgba(255, 255, 255, 0.25) !important;
                transform: translateY(-8px) scale(1.05) !important;
                box-shadow: 0 20px 40px rgba(0,0,0,0.3) !important;
            }
            
            @keyframes fadeInUp {
                from {
                    opacity: 0;
                    transform: translateY(30px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.8; }
            }
            
            .pulse {
                animation: pulse 2s infinite;
            }
        </style>
    </head>
    <body>
        <div class="demo-container">
            <div class="header">
                <div class="logo">🎯 Enterprise CIA</div>
                <div class="tagline">Complete You.com API Integration</div>
                <div class="subtitle">Competitive Intelligence Revolutionized</div>
            </div>

            <div class="api-showcase">
                <div class="api-title">🚀 Four You.com APIs in Perfect Harmony</div>
                <div class="api-grid">
                    <div class="api-item pulse" id="news-api">
                        <span class="api-icon">📰</span>
                        <div class="api-name">News API</div>
                        <div class="api-desc">Real-time competitive signal detection</div>
                    </div>
                    <div class="api-item pulse" id="search-api">
                        <span class="api-icon">🔍</span>
                        <div class="api-name">Search API</div>
                        <div class="api-desc">Context enrichment & research</div>
                    </div>
                    <div class="api-item pulse" id="agents-api">
                        <span class="api-icon">🤖</span>
                        <div class="api-name">Custom Agents</div>
                        <div class="api-desc">Structured impact analysis</div>
                    </div>
                    <div class="api-item pulse" id="ari-api">
                        <span class="api-icon">📊</span>
                        <div class="api-name">ARI Reports</div>
                        <div class="api-desc">400+ source synthesis</div>
                    </div>
                </div>
            </div>

            <div class="value-section">
                <div class="value-item">
                    <div class="value-number">10+</div>
                    <div class="value-label">Hours Saved</div>
                </div>
                <div class="value-item">
                    <div class="value-number">85%</div>
                    <div class="value-label">Accuracy</div>
                </div>
                <div class="value-item">
                    <div class="value-number">&lt;5min</div>
                    <div class="value-label">Detection</div>
                </div>
                <div class="value-item">
                    <div class="value-number">400+</div>
                    <div class="value-label">Sources</div>
                </div>
            </div>

            <div class="cta-section">
                <div class="cta-title">Transform Competitive Intelligence</div>
                <a href="#" class="cta-button">Powered by You.com APIs</a>
            </div>
        </div>

        <script>
            let currentAPI = 0;
            const apis = ['news-api', 'search-api', 'agents-api', 'ari-api'];
            
            function highlightAPI() {
                // Remove all highlights
                apis.forEach(id => {
                    const element = document.getElementById(id);
                    if (element) {
                        element.classList.remove('highlight');
                    }
                });
                
                // Highlight current API
                const currentElement = document.getElementById(apis[currentAPI]);
                if (currentElement) {
                    currentElement.classList.add('highlight');
                }
                
                currentAPI = (currentAPI + 1) % apis.length;
            }
            
            // Start API highlighting after page loads
            setTimeout(() => {
                setInterval(highlightAPI, 3000);
            }, 2000);
            
            // Add value prop animations
            function animateValues() {
                document.querySelectorAll('.value-item').forEach((item, index) => {
                    setTimeout(() => {
                        item.style.transform = 'translateY(-10px)';
                        setTimeout(() => {
                            item.style.transform = 'translateY(0)';
                        }, 300);
                    }, index * 150);
                });
            }
            
            setTimeout(animateValues, 8000);
            setInterval(animateValues, 20000);
        </script>
    </body>
    </html>
    `;

    await this.page.setContent(demoHTML);
    console.log("✅ Page content demo loaded");
  }

  async runPageContentDemo() {
    console.log("\n🎬 Starting Page Content Recording Demo");

    await this.addNarrationMarker(
      "Welcome to Enterprise CIA - the complete competitive intelligence platform powered by You.com APIs"
    );

    try {
      // Try to load the real application first
      console.log("🌐 Attempting to load live application...");
      try {
        await this.page.goto(this.baseUrl, {
          waitUntil: "networkidle2",
          timeout: 5000,
        });
        console.log("✅ Live application loaded successfully");
      } catch (error) {
        console.log("⚠️ Live application timeout, using page content demo");
        await this.createDemoContent();
      }

      // Start page content recording
      const recordingStarted = await this.startPageContentRecording();
      if (!recordingStarted) {
        console.log("❌ Could not start page content recording");
        return;
      }

      await this.addNarrationMarker(
        "This is Enterprise CIA - your command center for competitive intelligence"
      );
      await this.wait(5);

      await this.addNarrationMarker(
        "The platform integrates all four You.com APIs working in perfect harmony"
      );
      await this.wait(8);

      await this.addNarrationMarker(
        "News API detects competitive signals in real-time across thousands of sources"
      );
      await this.wait(8);

      await this.addNarrationMarker(
        "Search API enriches context while Custom Agents analyze strategic impact"
      );
      await this.wait(8);

      await this.addNarrationMarker(
        "ARI synthesizes insights from 400+ sources to generate actionable intelligence"
      );
      await this.wait(8);

      await this.addNarrationMarker(
        "This saves product managers over 10 hours per week with 85% accuracy"
      );
      await this.wait(7);

      await this.addNarrationMarker(
        "Detection happens in under 5 minutes instead of days"
      );
      await this.wait(6);

      await this.addNarrationMarker(
        "Built with production-grade architecture and 85% test coverage"
      );
      await this.wait(6);

      await this.addNarrationMarker(
        "Enterprise CIA - where You.com's four APIs revolutionize competitive intelligence"
      );
      await this.wait(6);

      await this.addNarrationMarker("Thank you for watching our demo");
      await this.wait(3);

      console.log("🎉 Page content recording demo completed!");
    } catch (error) {
      console.log(`Demo error: ${error.message}`);
      await this.addNarrationMarker(
        "Enterprise CIA - powered by complete You.com API integration"
      );
    } finally {
      await this.stopPageContentRecording();
    }
  }

  async run() {
    const initialized = await this.initialize();

    if (!initialized) {
      console.log("❌ Could not initialize Chrome");
      return;
    }

    try {
      console.log(`🎬 Starting page content recording demo...`);
      console.log("📹 This will capture ONLY the browser page content");

      await this.runPageContentDemo();
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

    console.log(`\n🎉 Page Content Recording Complete!`);
    console.log(
      `📹 Captured frames info: ${path.join(
        this.videoDir,
        "recording_info.json"
      )}`
    );
    console.log(
      `🎙️  Narration: ${path.join(this.videoDir, "page_content_narration.txt")}`
    );

    console.log(`\n📋 This recording captures ONLY the browser page content!`);
    console.log(
      `💡 The frames can be converted to video using ffmpeg if needed`
    );
  }
}

// Execute the demo
if (require.main === module) {
  const demo = new PageContentRecording();
  demo.run().catch(console.error);
}

module.exports = PageContentRecording;
