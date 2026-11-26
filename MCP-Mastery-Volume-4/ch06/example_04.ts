import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool
} from "@modelcontextprotocol/sdk/types.js";
import puppeteer from "puppeteer-extra";
import StealthPlugin from "puppeteer-extra-plugin-stealth";
import { Browser } from "puppeteer";

puppeteer.use(StealthPlugin());

let activeBrowser: Browser | null = null;
let lastActiveTime = Date.now();

// Lazy Browser Launcher with Auto-Shutdown Reaper
async function getBrowserInstance(): Promise<Browser> {
  lastActiveTime = Date.now();
  if (activeBrowser && activeBrowser.connected) {
    return activeBrowser;
  }

  activeBrowser = await puppeteer.launch({
    headless: "new",
    args: [
      "--no-sandbox",
      "--disable-setuid-sandbox",
      "--disable-dev-shm-usage",
      "--disable-gpu",
      "--window-size=1920,1080"
    ]
  });

  return activeBrowser;
}

// Scheduled Zombie Browser Sweep: Close idle browser after 3 minutes
setInterval(async () => {
  if (activeBrowser && Date.now() - lastActiveTime > 180000) {
    console.error("Reaping idle headless Chromium instance to reclaim RAM...");
    await activeBrowser.close().catch(() => {});
    activeBrowser = null;
  }
}, 30000);

const server = new Server(
  { name: "puppeteer-stealth-mcp", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => {
  const tools: Tool[] = [
    {
      name: "scrape_spa_page",
      description: "Launches headless stealth Chromium to render dynamic client-side SPAs, awaiting network idle.",
      inputSchema: {
        type: "object",
        properties: {
          url: { type: "string", description: "Target SPA URL to render." },
          wait_for_selector: { type: "string", description: "Optional CSS selector to await before capturing DOM." },
          capture_screenshot: { type: "boolean", description: "Whether to capture a base64 viewport screenshot.", default: false }
        },
        required: ["url"]
      }
    }
  ];
  return { tools };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  if (name === "scrape_spa_page") {
    const targetUrl = String(args?.url);
    const waitForSelector = args?.wait_for_selector ? String(args.wait_for_selector) : null;
    const captureScreenshot = Boolean(args?.capture_screenshot);

    let page: any = null;
    try {
      const browser = await getBrowserInstance();
      page = await browser.newPage();

      // Configure viewport and standard headers
      await page.setViewport({ width: 1440, height: 900 });
      await page.setUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36");

      // Navigate awaiting network idle (max 2 network connections for 500ms)
      await page.goto(targetUrl, { waitUntil: "networkidle2", timeout: 20000 });

      if (waitForSelector) {
        await page.waitForSelector(waitForSelector, { timeout: 10000 });
      }

      // Extract title and body text directly from rendered DOM
      const pageTitle = await page.title();
      const extractedText = await page.evaluate(() => {
        // Remove scripts, styles, and SVG trees from innerText
        const elementsToRemove = document.querySelectorAll("script, style, noscript, svg");
        elementsToRemove.forEach((el) => el.remove());
        return document.body ? document.body.innerText : "";
      });

      let screenshotBase64: string | null = null;
      if (captureScreenshot) {
        const screenshotBuf = (await page.screenshot({ encoding: "base64", type: "jpeg", quality: 75 })) as string;
        screenshotBase64 = `data:image/jpeg;base64,${screenshotBuf}`;
      }

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify({
              url: targetUrl,
              title: pageTitle,
              textLength: extractedText.length,
              renderedText: extractedText.substring(0, 15000), // Cap at 15KB
              screenshot: screenshotBase64
            }, null, 2)
          }
        ]
      };
    } catch (err: any) {
      return { isError: true, content: [{ type: "text", text: `Puppeteer Stealth Error: ${err.message}` }] };
    } finally {
      if (page) {
        await page.close().catch(() => {});
      }
    }
  }

  throw new Error(`Tool ${name} not found`);
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Puppeteer Stealth MCP Server initialized on stdio.");
}

main().catch(console.error);
