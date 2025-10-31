#!/usr/bin/env node

/**
 * Screenshot Video Demo - Takes screenshots of page content and combines into video
 * This guarantees we only capture the browser page content, nothing else
 */

const puppeteer = require("puppeteer");
const fs = require("fs").promises;
const path = require("path");
const { spawn } = require("child_process");
const os = require("os");

class ScreenshotVideoDemo {
  constructor() {
    this.browser = null;
    this.page = null;
    this.videoDir = "demo_videos";
    this.screenshotsDir = "demo_videos/screenshots";
    this.baseUrl = "http://localhost:3000?skip-onboarding=true";
    this.videoPath = null;
    this.platform = os.platform();
    this.fps = 10; // 10 frames per second
    this.screenshotCount = 0;
    this.isRecording = false;
    this.recordingInterval = null;
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
    console.log(`🚀 Starting Screenshot Video Demo on ${this.platform}...`);

    // Create directories
    await fs.mkdir(this.videoDir, { recursive: true });
    await fs.mkdir(this.screenshotsDir, { recursive: true });

    const chromePath = this.getChromePath();
    console.log(`🔍 Using Chrome at: ${chromePath}`);

    try {
      console.log("🌐 Launching Chrome for screenshot video...");

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
        ],
        timeout: 30000,
      });

      this.page = await this.browser.newPage();
      await this.page.setViewport({ width: 1280, height: 720 });

      console.log("✅ Chrome launched successfully for screenshot video");
      return true;
    } catch (error) {
      console.error("❌ Chrome launch failed:", error.message);
      return false;
    }
  }

  async startScreenshotRecording() {
    console.log("🎥 Starting screenshot recording...");
    console.log(`📸 Taking screenshots at ${this.fps} FPS`);
    console.log("📹 This captures ONLY the browser page content");

    this.isRecording = true;
    this.screenshotCount = 0;

    // Take screenshots at regular intervals
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
            fullPage: false, // Only capture viewport
          });

          this.screenshotCount++;

          // Show progress every 50 frames
          if (this.screenshotCount % 50 === 0) {
            console.log(`📸 Captured ${this.screenshotCount} frames`);
          }
        } catch (error) {
          console.log(`⚠️ Screenshot error: ${error.message}`);
        }
      }
    }, 1000 / this.fps); // Convert FPS to milliseconds

    console.log("✅ Screenshot recording started");
    return true;
  }

  async stopScreenshotRecording() {
    if (this.recordingInterval) {
      console.log("🛑 Stopping screenshot recording...");
      clearInterval(this.recordingInterval);
      this.recordingInterval = null;
      this.isRecording = false;

      console.log(`📸 Total frames captured: ${this.screenshotCount}`);
      console.log("✅ Screenshot recording stopped");

      return true;
    }
    return false;
  }

  async createVideoFromScreenshots() {
    const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
    this.videoPath = path.join(
      this.videoDir,
      `enterprise_cia_page_only_${timestamp}.mp4`
    );

    console.log("🎬 Creating video from screenshots...");
    console.log(`📹 Output: ${this.videoPath}`);

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
      "18",
      "-pix_fmt",
      "yuv420p",
      "-y", // Overwrite output file
      this.videoPath,
    ];

    return new Promise((resolve, reject) => {
      const ffmpeg = spawn("ffmpeg", ffmpegArgs);

      ffmpeg.stderr.on("data", (data) => {
        const message = data.toString();
        if (message.includes("frame=") && Math.random() < 0.1) {
          console.log("🎬 Creating video...");
        }
      });

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

  async cleanupScreenshots() {
    console.log("🧹 Cleaning up screenshot files...");
    try {
      const files = await fs.readdir(this.screenshotsDir);
      for (const file of files) {
        if (file.endsWith(".png")) {
          await fs.unlink(path.join(this.screenshotsDir, file));
        }
      }
      console.log("✅ Screenshot cleanup complete");
    } catch (error) {
      console.log("⚠️ Cleanup error:", error.message);
    }
  }

  async wait(seconds) {
    console.log(`⏳ Waiting ${seconds} seconds...`);
    await new Promise((resolve) => setTimeout(resolve, seconds * 1000));
  }

  async addNarrationMarker(text) {
    console.log(`🎙️  NARRATION: ${text}`);
    const timestamp = new Date().toISOString();
    const markerFile = path.join(
      this.videoDir,
      "screenshot_video_narration.txt"
    );
    try {
      await fs.appendFile(markerFile, `${timestamp}: ${text}\n`);
    } catch (error) {
      console.log(`⚠️ Could not write narration marker: ${error.message}`);
    }
  }

  async createDemoContent() {
    console.log("🎨 Creating screenshot demo content...");

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
                overflow: hidden;
                width: 100vw;
                height: 100vh;
            }
            
            .demo-container {
                width: 100%;
                height: 100%;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                padding: 30px;
                position: relative;
            }
            
            .header {
                text-align: center;
                margin-bottom: 30px;
                animation: fadeInUp 1s ease-out;
            }
            
            .logo {
                font-size: 3.5rem;
                font-weight: bold;
                margin-bottom: 15px;
                background: linear-gradient(45deg, #fff, #f0f0f0);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                text-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }
            
            .tagline {
                font-size: 1.8rem;
                margin-bottom: 8px;
                font-weight: 600;
                opacity: 0.95;
            }
            
            .subtitle {
                font-size: 1.2rem;
                opacity: 0.85;
            }
            
            .api-showcase {
                background: rgba(255, 255, 255, 0.15);
                backdrop-filter: blur(20px);
                border: 2px solid rgba(255, 255, 255, 0.2);
                border-radius: 25px;
                padding: 35px;
                text-align: center;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                animation: fadeInUp 1s ease-out 0.3s both;
                max-width: 900px;
                width: 100%;
                margin-bottom: 25px;
            }
            
            .api-title {
                font-size: 2rem;
                margin-bottom: 25px;
                font-weight: 700;
            }
            
            .api-grid {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 20px;
            }
            
            .api-item {
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                padding: 25px;
                border-radius: 18px;
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
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent);
                transition: left 0.6s;
            }
            
            .api-item:hover::before {
                left: 100%;
            }
            
            .api-item:hover {
                transform: translateY(-5px) scale(1.02);
                background: rgba(255, 255, 255, 0.2);
                box-shadow: 0 15px 30px rgba(0,0,0,0.2);
            }
            
            .api-icon {
                font-size: 2.5rem;
                margin-bottom: 12px;
                display: block;
            }
            
            .api-name {
                font-size: 1.3rem;
                margin-bottom: 10px;
                font-weight: 600;
            }
            
            .api-desc {
                opacity: 0.9;
                line-height: 1.4;
                font-size: 0.95rem;
            }
            
            .value-section {
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 15px;
                max-width: 900px;
                width: 100%;
                animation: fadeInUp 1s ease-out 0.6s both;
            }
            
            .value-item {
                text-align: center;
                padding: 20px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.2);
                transition: all 0.3s ease;
            }
            
            .value-item:hover {
                transform: translateY(-3px);
                background: rgba(255, 255, 255, 0.15);
            }
            
            .value-number {
                font-size: 2.2rem;
                font-weight: bold;
                margin-bottom: 8px;
                color: #fff;
            }
            
            .value-label {
                font-size: 0.9rem;
                font-weight: 500;
                opacity: 0.9;
            }
            
            .highlight {
                background: rgba(255, 255, 255, 0.25) !important;
                transform: translateY(-5px) scale(1.05) !important;
                box-shadow: 0 20px 40px rgba(0,0,0,0.3) !important;
            }
            
            @keyframes fadeInUp {
                from {
                    opacity: 0;
                    transform: translateY(20px);
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
            
            .floating {
                animation: float 3s ease-in-out infinite;
            }
            
            @keyframes float {
                0%, 100% { transform: translateY(0px); }
                50% { transform: translateY(-10px); }
            }
        </style>
    </head>
    <body>
        <div class="demo-container">
            <div class="header floating">
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
            
            // Start API highlighting
            setTimeout(() => {
                setInterval(highlightAPI, 2500);
            }, 2000);
            
            // Add value animations
            function animateValues() {
                document.querySelectorAll('.value-item').forEach((item, index) => {
                    setTimeout(() => {
                        item.style.transform = 'translateY(-8px)';
                        setTimeout(() => {
                            item.style.transform = 'translateY(0)';
                        }, 300);
                    }, index * 100);
                });
            }
            
            setTimeout(animateValues, 6000);
            setInterval(animateValues, 15000);
        </script>
    </body>
    </html>
    `;

    await this.page.setContent(demoHTML);
    console.log("✅ Screenshot demo content loaded");
  }

  async runScreenshotVideoDemo() {
    console.log("\n🎬 Starting Screenshot Video Demo");

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
        console.log(
          "⚠️ Live application timeout, using screenshot demo content"
        );
        await this.createDemoContent();
      }

      // Start screenshot recording
      const recordingStarted = await this.startScreenshotRecording();
      if (!recordingStarted) {
        console.log("❌ Could not start screenshot recording");
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

      console.log("🎉 Screenshot video demo completed!");
    } catch (error) {
      console.log(`Demo error: ${error.message}`);
      await this.addNarrationMarker(
        "Enterprise CIA - powered by complete You.com API integration"
      );
    } finally {
      await this.stopScreenshotRecording();
    }
  }

  async run() {
    const initialized = await this.initialize();

    if (!initialized) {
      console.log("❌ Could not initialize Chrome");
      return;
    }

    try {
      console.log(`🎬 Starting screenshot video demo...`);
      console.log(
        "📸 This captures ONLY the browser page content as screenshots"
      );

      await this.runScreenshotVideoDemo();

      // Create video from screenshots
      console.log("\n🎬 Converting screenshots to video...");
      await this.createVideoFromScreenshots();

      // Clean up screenshots
      await this.cleanupScreenshots();
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

    console.log(`\n🎉 Screenshot Video Demo Complete!`);
    if (this.videoPath) {
      console.log(`🎥 Video saved: ${this.videoPath}`);
    }
    console.log(
      `🎙️  Narration: ${path.join(
        this.videoDir,
        "screenshot_video_narration.txt"
      )}`
    );

    console.log(`\n📋 This video shows ONLY the browser page content!`);
    console.log(`✅ No desktop, dock, or other applications visible`);
  }
}

// Execute the demo
if (require.main === module) {
  const demo = new ScreenshotVideoDemo();
  demo.run().catch(console.error);
}

module.exports = ScreenshotVideoDemo;
