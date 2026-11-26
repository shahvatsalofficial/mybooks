import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import axios from "axios";
import * as cheerio from "cheerio";

const mcpServer = new Server(
  { name: "duckduckgo-search-mcp", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

mcpServer.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "ddg_privacy_search",
        description: "Executes an anonymous web search via DuckDuckGo without tracking or API key requirements.",
        inputSchema: {
          type: "object",
          properties: {
            query: { type: "string", description: "Search query string." },
            max_results: { type: "number", description: "Maximum search hits to return (max: 15).", default: 8 }
          },
          required: ["query"]
        }
      }
    ]
  };
});

mcpServer.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  if (name === "ddg_privacy_search") {
    const query = String(args?.query);
    const maxResults = Math.min(Number(args?.max_results) || 8, 15);

    try {
      const response = await axios.post(
        "https://html.duckduckgo.com/html/",
        new URLSearchParams({ q: query }),
        {
          headers: {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded",
            Accept: "text/html"
          },
          timeout: 8000
        }
      );

      const $ = cheerio.load(response.data);
      const results: { title: string; url: string; snippet: string }[] = [];

      $(".result").each((_, element) => {
        if (results.length >= maxResults) return false;

        const titleEl = $(element).find(".result__title .result__a");
        const snippetEl = $(element).find(".result__snippet");
        const rawHref = titleEl.attr("href") || "";

        // Unpack DuckDuckGo redirect URL (/l/?uddg=...)
        let targetUrl = rawHref;
        if (rawHref.includes("uddg=")) {
          const match = rawHref.match(/uddg=([^&]+)/);
          if (match) targetUrl = decodeURIComponent(match[1]);
        }

        const title = titleEl.text().trim();
        const snippet = snippetEl.text().trim();

        if (title && targetUrl && !targetUrl.includes("duckduckgo.com")) {
          results.push({ title, url: targetUrl, snippet });
        }
      });

      return {
        content: [{ type: "text", text: JSON.stringify(results, null, 2) }]
      };
    } catch (err: any) {
      return { isError: true, content: [{ type: "text", text: `DuckDuckGo Search Failed: ${err.message}` }] };
    }
  }

  throw new Error(`Tool ${name} not found`);
});

async function run() {
  const transport = new StdioServerTransport();
  await mcpServer.connect(transport);
  console.error("DuckDuckGo Privacy Search MCP Server running on stdio.");
}

run().catch(console.error);
