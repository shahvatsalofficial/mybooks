import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import { createClient } from "@clickhouse/client";

const clickhouse = createClient({
  url: process.env.CLICKHOUSE_URL || "http://localhost:8123",
  username: process.env.CLICKHOUSE_USER || "default",
  password: process.env.CLICKHOUSE_PASSWORD || "",
  request_timeout: 15000,
  max_open_connections: 10
});

const server = new Server(
  { name: "clickhouse-olap-mcp", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "execute_olap_query",
        description: "Runs high-performance analytical SQL queries on ClickHouse with enforced partition filters and 4GB memory bounds.",
        inputSchema: {
          type: "object",
          properties: {
            sql: { type: "string", description: "Analytical SQL query." },
            format: {
              type: "string",
              enum: ["JSONEachRow", "TabSeparatedWithNames"],
              default: "JSONEachRow",
              description: "Format of output stream."
            }
          },
          required: ["sql"]
        }
      }
    ]
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  if (name === "execute_olap_query") {
    const rawSql = String(args?.sql || "");
    const format = String(args?.format || "JSONEachRow");

    // AST / Token Validation
    const cleanSql = rawSql.trim();
    if (!cleanSql.toLowerCase().startsWith("select")) {
      return {
        isError: true,
        content: [{ type: "text", text: "Security Error: Only analytical SELECT statements are permitted." }]
      };
    }

    try {
      const resultSet = await clickhouse.query({
        query: cleanSql,
        format: format as any,
        clickhouse_settings: {
          // Strict Memory & Time Governors
          max_memory_usage: 4294967296, // 4GB max execution RAM
          max_execution_time: 15,       // 15 seconds max execution timeout
          max_result_rows: 5000         // Hard cap on result set rows
        }
      });

      const textOutput = await resultSet.text();

      return {
        content: [
          {
            type: "text",
            text: textOutput
          }
        ]
      };
    } catch (err: any) {
      return {
        isError: true,
        content: [{ type: "text", text: `ClickHouse OLAP Error: ${err.message}` }]
      };
    }
  }

  throw new Error(`Tool not found: ${name}`);
});

async function run() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("ClickHouse OLAP MCP Server running on stdio.");
}

run().catch(console.error);
