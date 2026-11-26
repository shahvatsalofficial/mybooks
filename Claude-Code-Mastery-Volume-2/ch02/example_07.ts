import SwaggerParser from "@apidevtools/swagger-parser";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";

export async function registerOpenApiTools(server: McpServer, openApiUrl: string) {
  const api = await SwaggerParser.validate(openApiUrl);
  console.error(`[OPENAPI] Ingested API: ${api.info.title} v${api.info.version}`);

  for (const [routePath, methods] of Object.entries(api.paths || {})) {
    for (const [httpMethod, operation] of Object.entries(methods as any)) {
      if (typeof operation !== "object" || !operation.operationId) continue;

      const toolName = `${httpMethod}_${operation.operationId}`.toLowerCase();
      const description = operation.description || operation.summary || `Executes ${httpMethod.toUpperCase()} on ${routePath}`;

      // Construct dynamic parameter schema
      const dynamicProperties: Record<string, z.ZodTypeAny> = {};
      for (const param of operation.parameters || []) {
        if (param.schema?.type === "string") {
          dynamicProperties[param.name] = z.string().describe(param.description || "");
        } else if (param.schema?.type === "integer") {
          dynamicProperties[param.name] = z.number().int().describe(param.description || "");
        }
      }

      // Register dynamically generated tool
      server.tool(toolName, description, dynamicProperties, async (args) => {
        const response = await executeHttpRequest(api.servers[0]?.url, routePath, httpMethod, args);
        return { content: [{ type: "text", text: JSON.stringify(response) }] };
      });
      console.error(`  -> Registered dynamic tool: ${toolName}`);
    }
  }
}
