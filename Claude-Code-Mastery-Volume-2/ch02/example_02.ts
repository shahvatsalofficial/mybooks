import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";

const server = new McpServer({
  name: "enterprise-postgres",
  version: "2.0.0"
});

// Fluent, type-safe tool declaration with automatic Zod JSON Schema conversion
server.tool(
  "query_db",
  "Executes raw SQL query against production cluster",
  { sql: z.string().describe("The SQL query string to execute") },
  async ({ sql }) => {
    // sql is automatically inferred as a strictly typed string!
    return {
      content: [{ type: "text", text: `Executing: ${sql}` }]
    };
  }
);
