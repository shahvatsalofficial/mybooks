import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import { ListToolsRequestSchema, CallToolRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import { createClient } from "redis";
import express from "express";

const redisSubscriber = createClient({ url: process.env.REDIS_URL || "redis://localhost:6379" });
const redisCommander = redisSubscriber.duplicate();

const app = express();
app.use(express.json());

const mcpServer = new Server(
  { name: "redis-pubsub-mcp", version: "1.0.0" },
  { capabilities: { tools: {}, prompts: {} } }
);

// Map of active SSE client transports
const activeTransports = new Map<string, SSEServerTransport>();

mcpServer.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "redis_publish",
        description: "Publishes a structured message to a specified Redis channel.",
        inputSchema: {
          type: "object",
          properties: {
            channel: { type: "string", description: "Redis channel name." },
            payload: { type: "object", description: "Message payload as JSON." }
          },
          required: ["channel", "payload"]
        }
      },
      {
        name: "redis_get_key",
        description: "Reads a cached string or JSON value from Redis by key with TTL check.",
        inputSchema: {
          type: "object",
          properties: {
            key: { type: "string", description: "Target cache key." }
          },
          required: ["key"]
        }
      }
    ]
  };
});

mcpServer.setRequestHandler(CallToolRequestSchema, async (req) => {
  const { name, arguments: args } = req.params;

  if (name === "redis_publish") {
    const channel = String(args?.channel);
    const payload = JSON.stringify(args?.payload || {});
    const receivers = await redisCommander.publish(channel, payload);
    return {
      content: [{ type: "text", text: `Published to '${channel}'. Active receivers: ${receivers}` }]
    };
  }

  if (name === "redis_get_key") {
    const key = String(args?.key);
    const value = await redisCommander.get(key);
    const ttl = await redisCommander.ttl(key);

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({ key, value: value ? JSON.parse(value) : null, ttlSeconds: ttl })
        }
      ]
    };
  }

  throw new Error(`Tool ${name} not supported`);
});

// SSE Handshake Endpoint for Web Clients & Agent Hubs
app.get("/sse", async (req, res) => {
  const transport = new SSEServerTransport("/messages", res);
  const sessionId = Math.random().toString(36).substring(2);
  activeTransports.set(sessionId, transport);

  req.on("close", () => {
    activeTransports.delete(sessionId);
  });

  await mcpServer.connect(transport);
});

app.post("/messages", async (req, res) => {
  // Dispatches POST messages to the matching SSE transport
  const sessionId = String(req.query.sessionId);
  const transport = activeTransports.get(sessionId);
  if (transport) {
    await transport.handlePostMessage(req, res);
  } else {
    res.status(404).send("Session expired or invalid");
  }
});

// Wire Redis Pub/Sub events directly into MCP resource notifications
async function start() {
  await redisSubscriber.connect();
  await redisCommander.connect();

  await redisSubscriber.pSubscribe("mcp:events:*", (message, channel) => {
    // Notify all connected MCP clients of resource changes
    for (const [id, transport] of activeTransports.entries()) {
      transport.send({
        jsonrpc: "2.0",
        method: "notifications/resources/updated",
        params: { uri: `mcp://redis/channels/${channel}` }
      });
    }
  });

  app.listen(8080, () => {
    console.error("Redis Pub/Sub MCP SSE server listening on port 8080.");
  });
}

start().catch(console.error);
