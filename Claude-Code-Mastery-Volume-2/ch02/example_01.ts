import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { ListToolsRequestSchema, CallToolRequestSchema } from "@modelcontextprotocol/sdk/types.js";

const server = new Server(
  { name: "low-level-postgres", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

// Manual registration of tool discovery
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "query_db",
        description: "Executes raw SQL query",
        inputSchema: {
          type: "object",
          properties: { sql: { type: "string" } },
          required: ["sql"]
        }
      }
    ]
  };
});

// Manual registration of tool execution and parameter validation
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === "query_db") {
    const sql = (request.params.arguments as any)?.sql;
    // Manual validation logic required!
    return { content: [{ type: "text", text: "Query executed" }] };
  }
  throw new Error("Method not found");
});
