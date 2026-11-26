import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool
} from "@modelcontextprotocol/sdk/types.js";
import { JSDOM } from "jsdom";
import { Readability } from "@mozilla/readability";
import TurndownService from "turndown";
import axios from "axios";

const turndownService = new TurndownService({
  headingStyle: "atx",
  codeBlockStyle: "fenced",
  emDelimiter: "*"
});

// Configure Turndown to preserve tables and code blocks cleanly
turndownService.keep(["table", "thead", "tbody", "tr", "th", "td", "pre", "code"]);

const server = new Server(
  { name: "readability-mcp-server", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => {
  const tools: Tool[] = [
    {
      name: "extract_clean_markdown",
      description: "Extracts the core readable article content from a web page URL and converts it to token-dense Markdown, stripping ads and noise.",
      inputSchema: {
        type: "object",
        properties: {
          url: { type: "string", description: "The public HTTP or HTTPS web page URL to extract." },
          max_characters: { type: "number", description: "Maximum markdown characters to return (default: 20000).", default: 20000 }
        },
        required: ["url"]
      }
    }
  ];
  return { tools };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  if (name === "extract_clean_markdown") {
    const targetUrl = String(args?.url);
    const maxChars = Math.min(Number(args?.max_characters) || 20000, 50000);

    try {
      // 1. Fetch raw HTML with reasonable timeout and standard desktop user agent
      const response = await axios.get(targetUrl, {
        timeout: 10000,
        headers: {
          "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
          Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
      });

      const rawHtml = response.data;
      if (typeof rawHtml !== "string") {
        return { isError: true, content: [{ type: "text", text: "Response was not an HTML text document." }] };
      }

      // 2. Parse DOM and execute Mozilla Readability extraction
      const dom = new JSDOM(rawHtml, { url: targetUrl });
      const reader = new Readability(dom.window.document);
      const article = reader.parse();

      if (!article || !article.content) {
        return {
          isError: true,
          content: [{ type: "text", text: "Readability was unable to identify a main article container on this page." }]
        };
      }

      // 3. Convert clean article HTML into Markdown
      let markdown = turndownService.turndown(article.content);
      let truncated = false;

      if (markdown.length > maxChars) {
        markdown = markdown.substring(0, maxChars) + "\n\n... [TRUNCATED: Exceeded character ceiling]";
        truncated = true;
      }

      const output = {
        title: article.title,
        byline: article.byline,
        siteName: article.siteName,
        publishedTime: article.publishedTime,
        characterCount: markdown.length,
        truncated,
        markdownContent: markdown
      };

      return {
        content: [{ type: "text", text: JSON.stringify(output, null, 2) }]
      };
    } catch (err: any) {
      return { isError: true, content: [{ type: "text", text: `Extraction Failed: ${err.message}` }] };
    }
  }

  throw new Error(`Tool ${name} not found`);
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Readability Markdown MCP Server running on stdio.");
}

main().catch(console.error);
