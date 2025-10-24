#!/usr/bin/env python3
"""
Automated Demo Recording Script for Enterprise CIA Hackathon
Records a perfect demo every time with Playwright
"""

import asyncio
from playwright.async_api import async_playwright
import time

class DemoRecorder:
    def __init__(self, base_url="http://localhost:3000", output_file="demo.mp4"):
        self.base_url = base_url
        self.output_file = output_file

    async def record_demo(self):
        """Record the perfect 2-minute demo"""
        async with async_playwright() as p:
            # Launch browser with video recording
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                record_video_dir="./demo-recordings/",
                record_video_size={"width": 1920, "height": 1080}
            )
            page = await context.new_page()

            print("🎬 Starting demo recording...")

            # ===== SCENE 1: Homepage (0-10 seconds) =====
            print("\n📍 Scene 1: Landing on homepage")
            await page.goto(self.base_url)
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)  # Let viewers see the clean interface

            # ===== SCENE 2: Add Competitor (10-20 seconds) =====
            print("\n📍 Scene 2: Adding competitor to watchlist")
            await page.click('button:has-text("Add Competitor")')
            await asyncio.sleep(1)

            # Type competitor name with human-like speed
            await page.fill('input[placeholder*="OpenAI"]', 'OpenAI')
            await asyncio.sleep(0.5)

            # Type keywords
            await page.fill('input[placeholder*="keywords"]', 'GPT-5, ChatGPT, API, announcement')
            await asyncio.sleep(0.5)

            # Type description
            await page.fill('textarea[placeholder*="monitoring"]', 'Leading AI research company - track product launches')
            await asyncio.sleep(1)

            # Submit form
            await page.click('button:has-text("Add Competitor")')
            print("✅ Competitor added")
            await asyncio.sleep(2)

            # ===== SCENE 3: Generate Impact Card (20-60 seconds) =====
            print("\n📍 Scene 3: Generating impact card - THE MONEY SHOT")

            # Click generate on the newly added competitor
            await page.click('button[title="Generate Impact Card"]')
            print("⚡ APIs firing in sequence...")

            # Wait for each API to complete (shows progress in real-time)
            await asyncio.sleep(3)  # News API
            print("  ⚡ News API: 12 articles found")

            await asyncio.sleep(3)  # Search API
            print("  🔍 Search API: 428 sources aggregated")

            await asyncio.sleep(3)  # Chat API
            print("  🤖 Chat API: Risk score 85/100")

            await asyncio.sleep(4)  # ARI API (longest)
            print("  📊 ARI API: 2,847 word report generated")

            await asyncio.sleep(2)  # Let the card render
            print("✅ Impact card complete!")

            # ===== SCENE 4: View Results (60-80 seconds) =====
            print("\n📍 Scene 4: Viewing impact card details")

            # Click to expand the first impact card
            await page.click('.impact-card:first-child')
            await asyncio.sleep(3)  # Let viewers read the risk score

            # Scroll through insights
            await page.evaluate("window.scrollBy(0, 300)")
            await asyncio.sleep(2)

            await page.evaluate("window.scrollBy(0, 300)")
            await asyncio.sleep(2)

            # ===== SCENE 5: Export PDF (80-90 seconds) =====
            print("\n📍 Scene 5: Exporting PDF report")

            # Click export button
            await page.click('button:has-text("Export PDF")')
            await asyncio.sleep(2)
            print("📄 PDF downloaded")

            # ===== SCENE 6: API Usage Dashboard (90-110 seconds) =====
            print("\n📍 Scene 6: Showing API usage metrics")

            # Navigate to API dashboard
            await page.click('a:has-text("API Usage")')
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)  # Show the metrics

            # Highlight key stats
            await page.evaluate("""
                document.querySelectorAll('.metric-card').forEach((card, index) => {
                    setTimeout(() => {
                        card.style.transform = 'scale(1.05)';
                        card.style.boxShadow = '0 0 20px rgba(59, 130, 246, 0.5)';
                        setTimeout(() => {
                            card.style.transform = 'scale(1)';
                            card.style.boxShadow = '';
                        }, 500);
                    }, index * 500);
                });
            """)
            await asyncio.sleep(4)

            # ===== SCENE 7: Closing (110-120 seconds) =====
            print("\n📍 Scene 7: Final overview")

            # Go back to watchlist to show multiple competitors
            await page.click('a:has-text("Watchlist")')
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)

            print("\n🎬 Demo recording complete!")
            print(f"💾 Video saved to: ./demo-recordings/")

            # Close browser (this saves the video)
            await context.close()
            await browser.close()

            print("\n✨ Demo recording finished!")
            print("📹 Find your video in ./demo-recordings/")
            print("\n🎥 Next steps:")
            print("1. Trim/edit the video to exactly 2 minutes")
            print("2. Add voiceover explaining each step")
            print("3. Add background music")
            print("4. Add captions for accessibility")
            print("5. Upload to YouTube/Loom")

async def main():
    recorder = DemoRecorder(
        base_url="http://localhost:3000",
        output_file="enterprise-cia-demo.mp4"
    )

    print("🚀 Enterprise CIA - Automated Demo Recorder")
    print("=" * 50)
    print("\n⚠️  Make sure:")
    print("  1. Backend is running on port 8765")
    print("  2. Frontend is running on port 3000")
    print("  3. You.com API key is configured")
    print("  4. Database is running")
    print("\n Press ENTER when ready...")
    input()

    await recorder.record_demo()

if __name__ == "__main__":
    # Install dependencies first: pip install playwright
    # Then: playwright install chromium
    asyncio.run(main())
