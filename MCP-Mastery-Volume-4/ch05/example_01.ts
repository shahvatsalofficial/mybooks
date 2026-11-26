import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool
} from "@modelcontextprotocol/sdk/types.js";
import SwaggerParser from "@apidevtools/swagger-parser";
import axios, { AxiosInstance } from "axios";
import https from "https";
import fs from "fs";

const OPENAPI_SPEC_URL = process.env.OPENAPI_SPEC_URL || "https://petstore.swagger.io/v2/swagger.json";
const TARGET_API_BASE_URL = process.env.TARGET_API_BASE_URL || "";

// Configurable Mutual TLS (mTLS) Client Credentials
const httpsAgent = new https.Agent({
  cert: process.env.CLIENT_CERT_PATH ? fs.readFileSync(process.env.CLIENT_CERT_PATH) : undefined,
  key: process.env.CLIENT_KEY_PATH ? fs.readFileSync(process.env.CLIENT_KEY_PATH) : undefined,
  rejectUnauthorized: process.env.NODE_ENV === "production"
});

const apiClient: AxiosInstance = axios.create({
  timeout: 10000,
  httpsAgent
});

interface CompiledEndpoint {
  toolName: string;
  method: "get" | "post" | "put" | "delete" | "patch";
  pathTemplate: string;
  summary: string;
  inputSchema: any;
}

const compiledEndpoints = new Map<string, CompiledEndpoint>();

// Normalizes path to valid tool identifier (e.g. "/users/{id}" -> "get_users_by_id")
function generateToolName(method: string, pathStr: string, operationId?: string): string {
  if (operationId) {
    return operationId.replace(/[^a-zA-Z0-9_]/g, "_").toLowerCase();
  }
  const cleanPath = pathStr.replace(/\{([^}]+)\}/g, "by_$1").replace(/[^a-zA-Z0-9_]/g, "_");
  return `${method.toLowerCase()}_${cleanPath}`.replace(/_+/g, "_").replace(/^_|_$/g, "");
}

// Compile OpenAPI Spec into MCP Tools
async function compileOpenApiSpec(): Promise<Tool[]> {
  const api: any = await SwaggerParser.dereference(OPENAPI_SPEC_URL);
  const tools: Tool[] = [];
  compiledEndpoints.clear();

  const paths = api.paths || {};
  for (const [pathStr, pathItem] of Object.entries(paths)) {
    const methods = ["get", "post", "put", "delete", "patch"] as const;
    for (const method of methods) {
      const op = (pathItem as any)[method];
      if (!op) continue;

      const toolName = generateToolName(method, pathStr, op.operationId);
      const properties: Record<string, any> = {};
      const requiredFields: string[] = [];

      // Parse Path & Query Parameters
      if (Array.isArray(op.parameters)) {
        for (const p of op.parameters) {
          properties[p.name] = {
            type: p.schema?.type || p.type || "string",
            description: p.description || `Parameter: ${p.name} (${p.in})`
          };
          if (p.required) requiredFields.push(p.name);
        }
      }

      // Parse JSON Request Body (OpenAPI 3.x)
      if (op.requestBody?.content?.["application/json"]?.schema) {
        properties["requestBody"] = op.requestBody.content["application/json"].schema;
        if (op.requestBody.required) requiredFields.push("requestBody");
      }

      const inputSchema = {
        type: "object",
        properties,
        required: requiredFields.length > 0 ? requiredFields : undefined
      };

      compiledEndpoints.set(toolName, {
        toolName,
        method,
        pathTemplate: pathStr,
        summary: op.summary || op.description || `Invokes ${method.toUpperCase()} on ${pathStr}`,
        inputSchema
      });

      tools.push({
        name: toolName,
        description: `${op.summary || op.description || ""} [${method.toUpperCase()} ${pathStr}]`.trim(),
        inputSchema
      });
    }
  }

  return tools;
}

const server = new Server(
  { name: "openapi-proxy-mcp", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => {
  const tools = await compileOpenApiSpec();
  return { tools };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  const endpoint = compiledEndpoints.get(name);

  if (!endpoint) {
    throw new Error(`Tool '${name}' not recognized in compiled OpenAPI specification.`);
  }

  // Interpolate Path Parameters
  let resolvedPath = endpoint.pathTemplate;
  const queryParams: Record<string, any> = {};
  const bodyPayload = args?.requestBody;

  if (args) {
    for (const [k, v] of Object.entries(args)) {
      if (k === "requestBody") continue;
      if (resolvedPath.includes(`{${k}}`)) {
        resolvedPath = resolvedPath.replace(`{${k}}`, encodeURIComponent(String(v)));
      } else {
        queryParams[k] = v;
      }
    }
  }

  const baseUrl = TARGET_API_BASE_URL || OPENAPI_SPEC_URL.substring(0, OPENAPI_SPEC_URL.lastIndexOf("/"));
  const fullUrl = `${baseUrl.replace(/\/$/, "")}/${resolvedPath.replace(/^\//, "")}`;

  try {
    const startTime = Date.now();
    const res = await apiClient.request({
      method: endpoint.method,
      url: fullUrl,
      params: queryParams,
      data: bodyPayload,
      headers: {
        "User-Agent": "MCP-OpenAPI-Proxy/1.0.0",
        Accept: "application/json"
      }
    });
    const duration = Date.now() - startTime;

    // Response Token Budget Governor: Truncate large payloads
    let rawOutput = JSON.stringify(res.data, null, 2);
    let truncated = false;
    const MAX_CHAR_CEILING = 32000; // ~8,000 tokens maximum

    if (rawOutput.length > MAX_CHAR_CEILING) {
      rawOutput = rawOutput.substring(0, MAX_CHAR_CEILING) + "\n\n... [TRUNCATED: Response exceeded 32KB ceiling]";
      truncated = true;
    }

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({
            status: res.status,
            statusText: res.statusText,
            executionDurationMs: duration,
            truncated,
            data: rawOutput.startsWith("{") || rawOutput.startsWith("[") ? JSON.parse(rawOutput.split("... [TRUNCATED")[0] || "{}") : rawOutput
          }, null, 2)
        }
      ]
    };
  } catch (err: any) {
    const errorDetails = err.response?.data ? JSON.stringify(err.response.data) : err.message;
    return {
      isError: true,
      content: [{ type: "text", text: `API Request Failed (HTTP ${err.response?.status || "Unknown"}): ${errorDetails}` }]
    };
  }
});

async function main() {
  await compileOpenApiSpec();
  console.error(`Compiled ${compiledEndpoints.size} OpenAPI endpoints into MCP tools.`);
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("OpenAPI Proxy MCP Server running on stdio.");
}

main().catch(console.error);
