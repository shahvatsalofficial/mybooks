import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";

// Define Zod Input Validation Schema
const ExecuteQuerySchema = z.object({
  query: z.string().min(5).max(500),
  limit: z.number().min(1).max(100).default(10)
});

const server = new Server(
  { name: "enterprise-database-mcp", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

// Register Available Tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "execute_read_query",
        description: "Executes a sanitized read-only SQL query against the analytics replica.",
        inputSchema: {
          type: "object",
          properties: {
            query: { type: "string", description: "SELECT query string." },
            limit: { type: "number", default: 10 }
          },
          required: ["query"]
        }
      }
    ]
  };
});

// Handle Tool Execution
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === "execute_read_query") {
    try {
      const args = ExecuteQuerySchema.parse(request.params.arguments);
      
      // Enforce Read-Only Query Protection
      if (!args.query.trim().toUpperCase().startsWith("SELECT")) {
        throw new Error("SECURITY_VIOLATION: Only SELECT queries are permitted.");
      }

      // Execute query against database replica
      const mockResult = [{ id: 101, status: "COMPLETED", latency_ms: 12.4 }];
      
      return {
        content: [{ type: "text", text: JSON.stringify(mockResult) }]
      };
    } catch (err: any) {
      return {
        isError: true,
        content: [{ type: "text", text: `TOOL_EXECUTION_ERROR: ${err.message}` }]
      };
    }
  }
  throw new Error(`Tool not found: ${request.params.name}`);
});

// Start Stdio Transport Engine
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("MCP Database Tool Server running on Stdio transport.");
}

main().catch(console.error);
