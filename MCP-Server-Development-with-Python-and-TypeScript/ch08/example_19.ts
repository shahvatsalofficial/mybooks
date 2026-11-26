import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { z } from "zod";

interface ChildServerConfig {
  id: string;
  command: string;
  args: string[];
}

class MultiServerProxy {
  private virtualServer = new McpServer({ name: "virtual-proxy", version: "1.0.0" });
  private childClients = new Map<string, Client>();

  async attachChild(cfg: ChildServerConfig) {
    const client = new Client({ name: `proxy-to-${cfg.id}`, version: "1.0.0" }, { capabilities: {} });
    const transport = new StdioClientTransport({ command: cfg.command, args: cfg.args });
    await client.connect(transport);
    this.childClients.set(cfg.id, client);

    // Ingest child tools and register in virtual server
    const { tools } = await client.listTools();
    for (const tool of tools) {
      const namespacedName = `${cfg.id}__${tool.name}`;
      console.error(`[Proxy] Registering virtual tool: ${namespacedName}`);

      this.virtualServer.tool(
        namespacedName,
        tool.description || "",
        { payload: z.any() },
        async (args) => {
          // Forward call to child client
          return await client.callTool({
            name: tool.name,
            arguments: args.payload || {}
          });
        }
      );
    }
  }

  async start() {
    const transport = new StdioServerTransport();
    await this.virtualServer.connect(transport);
    console.error("[Proxy] Virtual Multi-Server Proxy online on stdio.");
  }
}
