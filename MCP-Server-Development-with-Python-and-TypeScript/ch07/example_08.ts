/**
 * recipe_7_3_express_sse_server.ts
 * Hardened Express SSE Server with multi-client session routing and cleanup.
 */

import express from "express";
import cors from "cors";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import { z } from "zod";

const app = express();
app.use(cors({ origin: "*" })); // Restrict in production enterprise environments

const mcpServer = new McpServer({
  name: "remote-sse-server",
  version: "1.0.0"
});

mcpServer.tool(
  "calculate_checksum",
  { input_data: z.string().describe("Raw string to hash") },
  async ({ input_data }) => {
    const crypto = await import("crypto");
    const hash = crypto.createHash("sha256").update(input_data).digest("hex");
    return { content: [{ type: "text", text: `SHA256: ${hash}` }] };
  }
);

// Map of active client SSE sessions: sessionId -> SSEServerTransport
const activeSessions: Map<string, SSEServerTransport> = new Map();

// ─── GET /sse: CLIENT EVENTSTREAM HANDSHAKE ────────────────────────────────────
app.get("/sse", async (req, res) => {
  console.error("[SSE] Inbound connection established from client.");

  // Instantiate transport binding the HTTP response socket
  const transport = new SSEServerTransport("/messages", res);
  const sessionId = transport.sessionId;

  activeSessions.set(sessionId, transport);
  console.error(`[SSE] Registered session: ${sessionId} (Active: ${activeSessions.size})`);

  // Handle client disconnection and socket closure
  res.on("close", () => {
    console.error(`[SSE] Client socket closed. Reaping session: ${sessionId}`);
    activeSessions.delete(sessionId);
    console.error(`[SSE] Remaining active sessions: ${activeSessions.size}`);
  });

  // Connect transport to the MCP server
  await mcpServer.connect(transport);
});

// ─── POST /messages: INCOMING JSON-RPC COMMAND GATEWAY ─────────────────────────
app.post("/messages", async (req, res) => {
  const sessionId = req.query.sessionId as string;

  if (!sessionId) {
    return res.status(400).send("Missing required 'sessionId' query parameter.");
  }

  const transport = activeSessions.get(sessionId);
  if (!transport) {
    console.error(`[POST /messages] Session not found: ${sessionId}`);
    return res.status(404).send(`Session '${sessionId}' not found or has expired.`);
  }

  // Forward request body to transport handler
  await transport.handlePostMessage(req, res);
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
  console.error(`[Express] MCP SSE Server online at http://localhost:${PORT}/sse`);
});
