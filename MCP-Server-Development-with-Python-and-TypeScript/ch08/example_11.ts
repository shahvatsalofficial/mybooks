/**
 * recipe_8_2_custom_client.ts
 * Standalone programmatic MCP client in TypeScript.
 */

import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

async function main() {
  console.log("[Client] Initializing programmatic MCP Client...");

  // 1. Instantiate client declaring client-side capabilities
  const client = new Client(
    { name: "automated-audit-agent", version: "1.0.0" },
    {
      capabilities: {
        roots: { listChanged: true },
        sampling: {}
      }
    }
  );

  // 2. Initialize stdio client transport pointing to the server
  const transport = new StdioClientTransport({
    command: "node",
    args: ["dist/index.js"],
    stderr: "inherit" // Direct server diagnostic logs to client console
  });

  // 3. Connect and execute handshake
  console.log("[Client] Connecting transport to server subprocess...");
  await client.connect(transport);
  console.log("[Client] Handshake complete. Connected to server.");

  // 4. Discover available tools
  console.log("[Client] Querying tools/list catalog...");
  const toolsResponse = await client.listTools();
  console.log(`[Client] Discovered ${toolsResponse.tools.length} active tools:`);
  for (const t of toolsResponse.tools) {
    console.log(`  • ${t.name}: ${t.description}`);
  }

  // 5. Programmatically invoke a tool
  console.log("\n[Client] Invoking 'create_or_update_note' tool...");
  const callResult = await client.callTool({
    name: "create_or_update_note",
    arguments: {
      title: "Automated Deployment Runbook",
      content: "# Deployment Runbook\n1. Run migrations.\n2. Scale deployment pods to 10.\n3. Verify health checks.",
      tags: ["devops", "automation", "runbook"]
    }
  });

  console.log("[Client] Tool execution result received:");
  if (callResult.isError) {
    console.error("  [Execution Error]", callResult.content);
  } else {
    for (const item of callResult.content) {
      if (item.type === "text") {
        console.log(`  [Text Output]: ${item.text}`);
      }
    }
  }

  // 6. Graceful disconnect
  console.log("\n[Client] Closing client connection...");
  await client.close();
  console.log("[Client] Disconnected cleanly.");
}

main().catch((err) => {
  console.error("[Client Fatal]", err);
  process.exit(1);
});
