/**
 * recipe_7_2_lowlevel_dynamic_server.ts
 * Low-Level MCP Server with manual schema registration and list_changed events.
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  ListToolsRequestSchema,
  CallToolRequestSchema,
  ErrorCode,
  McpError
} from "@modelcontextprotocol/sdk/types.js";

interface ToolDefinition {
  name: string;
  description: string;
  inputSchema: Record<string, any>;
  handler: (args: any) => Promise<string>;
}

const TOOL_CATALOG: Map<string, ToolDefinition> = new Map();

// Initialize Low-Level Server with explicit tools capability
const server = new Server(
  { name: "dynamic-extensible-server", version: "1.0.0" },
  { capabilities: { tools: { listChanged: true } } }
);

// Register base tool
TOOL_CATALOG.set("system_ping", {
  name: "system_ping",
  description: "Returns sub-millisecond network timestamp.",
  inputSchema: { type: "object", properties: {}, additionalProperties: false },
  handler: async () => `PONG: ${Date.now()}`
});

// Handler for tools/list
server.setRequestHandler(ListToolsRequestSchema, async () => {
  const tools = Array.from(TOOL_CATALOG.values()).map((t) => ({
    name: t.name,
    description: t.description,
    inputSchema: t.inputSchema
  }));
  return { tools };
});

// Handler for tools/call
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  const tool = TOOL_CATALOG.get(name);

  if (!tool) {
    throw new McpError(ErrorCode.MethodNotFound, `Tool '${name}' not recognized.`);
  }

  try {
    const output = await tool.handler(args || {});
    return {
      content: [{ type: "text", text: output }],
      isError: false
    };
  } catch (err: any) {
    return {
      content: [{ type: "text", text: `ToolExecutionError: ${err.message}` }],
      isError: true
    };
  }
});

// Function to dynamically register a tool and notify client
export async function addDynamicTool(tool: ToolDefinition) {
  TOOL_CATALOG.set(tool.name, tool);
  console.error(`[Registry] Dynamically registered tool: ${tool.name}`);

  // Emit protocol notification to inform client host
  await server.notification({
    method: "notifications/tools/list_changed",
    params: {}
  });
}

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("[Server] Low-level server listening on stdio.");
}

main().catch(console.error);
