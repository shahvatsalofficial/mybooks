import express from "express";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";

const app = express();
const activeTransports = new Map<string, SSEServerTransport>();

// 1. Establish Server-Sent Events GET Stream
app.get("/sse", async (req, res) => {
  console.error("[SSE CONNECT] Incoming client connection");
  
  // Set required SSE headers
  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "keep-alive");
  res.setHeader("X-Accel-Buffering", "no"); // Disable NGINX reverse proxy buffering

  const transport = new SSEServerTransport("/messages", res);
  activeTransports.set(transport.sessionId, transport);

  transport.onclose = () => {
    console.error(`[SSE DISCONNECT] Session ${transport.sessionId} terminated.`);
    activeTransports.delete(transport.sessionId);
  };

  await server.connect(transport);
});

// 2. Receive JSON-RPC POST Messages from Client
app.post("/messages", express.json(), async (req, res) => {
  const sessionId = req.query.sessionId as string;
  const transport = activeTransports.get(sessionId);

  if (!transport) {
    return res.status(404).json({ error: "Invalid or expired session ID" });
  }

  await transport.handlePostMessage(req, res);
});

app.listen(8080, () => {
  console.error("[HTTP READY] Remote MCP Gateway listening on port 8080");
});
