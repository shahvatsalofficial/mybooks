import { chromium, Browser, BrowserContext } from "playwright";

export class PlaywrightSessionManager {
  private browser: Browser | null = null;
  private context: BrowserContext | null = null;

  async initializeSession(storageStatePath?: string) {
    this.browser = await chromium.launch({ headless: true });
    this.context = await this.browser.newContext({
      viewport: { width: 1440, height: 900 },
      storageState: storageStatePath
    });
  }

  async openTab(url: string) {
    if (!this.context) throw new Error("Context not initialized.");
    const page = await this.context.newPage();
    await page.goto(url, { waitUntil: "domcontentloaded" });
    return page;
  }

  async persistSessionState(outputPath: string) {
    if (this.context) {
      await this.context.storageState({ path: outputPath });
    }
  }

  async close() {
    if (this.browser) await this.browser.close();
  }
}
