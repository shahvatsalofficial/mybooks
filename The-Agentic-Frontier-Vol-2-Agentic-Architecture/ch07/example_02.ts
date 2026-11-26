import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListResourcesRequestSchema,
  ListToolsRequestSchema,
  ReadResourceRequestSchema
} from "@modelcontextprotocol/sdk/types.js";

// Initialize Enterprise MCP Server
const server = new Server(
  {
    name: "EnterpriseMetricsMCPServer",
    version: "1.0.0"
  },
  {
    capabilities: {
      resources: {},
      tools: {}
    }
  }
);

// 1. Expose Tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "query_financial_ledger",
        description: "Executes a read-only SQL query against the audited financial ledger.",
        inputSchema: {
          type: "object",
          properties: {
            account_id: { type: "string", description: "Target Customer Account ID" },
            fiscal_year: { type: "number", description: "Fiscal Year (e.g. 2026)" }
          },
          required: ["account_id", "fiscal_year"]
        }
      }
    ]
  };
});

// 2. Handle Tool Execution
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === "query_financial_ledger") {
    const { account_id, fiscal_year } = request.params.arguments as { account_id: string; fiscal_year: number };
    
    // Simulate database lookup
    const ledgerData = {
      account_id,
      fiscal_year,
      total_revenue_usd: 1420500.00,
      compliance_status: "AUDITED_VERIFIED"
    };

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(ledgerData, null, 2)
        }
      ]
    };
  }
  throw new Error(`Tool not found: ${request.params.name}`);
});

// 3. Start Stdio Transport
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Enterprise Metrics MCP Server running on stdio");
}

main().catch((error) => {
  console.error("Fatal error starting MCP Server:", error);
  process.exit(1);
});
