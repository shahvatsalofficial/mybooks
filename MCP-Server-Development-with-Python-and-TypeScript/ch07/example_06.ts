/**
 * recipe_7_1_mcp_server_zod.ts
 * Enterprise TypeScript MCP Server using high-level McpServer and Zod.
 */

import { McpServer, ResourceTemplate } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const server = new McpServer({
  name: "enterprise-cloud-tools",
  version: "1.0.0"
});

// Mock cluster inventory
const CLUSTER_DATA: Record<string, { status: string; nodes: number; region: string }> = {
  "us-east": { status: "ONLINE", nodes: 24, region: "us-east-1" },
  "eu-west": { status: "DEGRADED", nodes: 12, region: "eu-west-1" }
};

// ─── PRIMITIVE 1: TOOLS ────────────────────────────────────────────────────────
server.tool(
  "scale_cluster",
  {
    cluster_id: z.string().describe("Target cluster name (e.g. us-east)"),
    target_nodes: z.number().int().min(1).max(100).describe("Target node count between 1 and 100")
  },
  async ({ cluster_id, target_nodes }) => {
    console.error(`[Tools] Scaling cluster ${cluster_id} to ${target_nodes} nodes...`);

    if (!CLUSTER_DATA[cluster_id]) {
      return {
        content: [{ type: "text", text: `Error: Cluster '${cluster_id}' does not exist.` }],
        isError: true
      };
    }

    CLUSTER_DATA[cluster_id].nodes = target_nodes;
    return {
      content: [{ type: "text", text: `Successfully scaled cluster ${cluster_id} to ${target_nodes} nodes.` }],
      isError: false
    };
  }
);

// ─── PRIMITIVE 2: RESOURCES ────────────────────────────────────────────────────
server.resource(
  "cluster-status",
  new ResourceTemplate("k8s://clusters/{cluster_id}/status", { list: undefined }),
  async (uri, { cluster_id }) => {
    console.error(`[Resources] Reading status for cluster: ${cluster_id}`);
    const data = CLUSTER_DATA[cluster_id as string];

    if (!data) {
      throw new Error(`Cluster '${cluster_id}' not found.`);
    }

    return {
      contents: [
        {
          uri: uri.href,
          mimeType: "text/markdown",
          text: `# Cluster Status: ${cluster_id}\n- Status: ${data.status}\n- Nodes: ${data.nodes}\n- Region: ${data.region}`
        }
      ]
    };
  }
);

// ─── PRIMITIVE 3: PROMPTS ──────────────────────────────────────────────────────
server.prompt(
  "investigate_cluster_outage",
  {
    cluster_id: z.string().describe("Cluster experiencing degraded performance")
  },
  ({ cluster_id }) => {
    const data = CLUSTER_DATA[cluster_id] || { status: "UNKNOWN", nodes: 0, region: "unknown" };

    return {
      messages: [
        {
          role: "user",
          content: {
            type: "text",
            text: `You are a Principal Reliability Architect. Investigate the degraded status of cluster '${cluster_id}'. Formulate an immediate incident response runbook.`
          }
        },
        {
          role: "user",
          content: {
            type: "resource",
            resource: {
              uri: `k8s://clusters/${cluster_id}/status`,
              mimeType: "text/markdown",
              text: `Status: ${data.status}\nNodes: ${data.nodes}\nRegion: ${data.region}`
            }
          }
        }
      ]
    };
  }
);

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("[Server] Enterprise Cloud Tools MCP Server running on stdio.");
}

main().catch((err) => {
  console.error("[Fatal Error]", err);
  process.exit(1);
});
