import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";

const server = new McpServer({
  name: "deployment-orchestrator",
  version: "1.0.0"
});

server.tool(
  "trigger_deployment",
  {
    service_id: z.string()
      .min(3, "Service identifier must be at least 3 characters")
      .max(64, "Service identifier cannot exceed 64 characters")
      .regex(/^[a-z0-9-]+$/, "Must contain only lowercase alphanumeric characters and hyphens")
      .describe("Unique microservice name to deploy"),
    replicas: z.number().int()
      .min(1, "Must deploy at least 1 replica")
      .max(100, "Maximum replica ceiling is 100 pods")
      .default(3)
      .describe("Target number of container instances"),
    environment: z.enum(["development", "staging", "production"])
      .default("staging")
      .describe("Target deployment infrastructure tier"),
    dry_run: z.boolean()
      .default(false)
      .describe("If true, simulates deployment without applying changes")
  },
  async ({ service_id, replicas, environment, dry_run }) => {
    // TypeScript automatically infers the exact types of arguments!
    // service_id: string
    // replicas: number
    // environment: "development" | "staging" | "production"
    // dry_run: boolean
    
    return {
      content: [
        {
          type: "text",
          text: `Deployment scheduled: ${service_id} (${replicas} pods) -> ${environment}. Dry-run: ${dry_run}`
        }
      ]
    };
  }
);
