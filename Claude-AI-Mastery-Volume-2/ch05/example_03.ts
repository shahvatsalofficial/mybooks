/**
 * Recipe 05.3: Enterprise Dual-Transport TypeScript MCP Server
 * Author: Vatsal Shah (Vatsal Shah)
 * License: Apache-2.0
 */

import express from 'express';
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { SSEServerTransport } from '@modelcontextprotocol/sdk/server/sse.js';
import { z } from 'zod';

const server = new McpServer({
  name: 'enterprise-hybrid-gateway',
  version: '1.0.0'
});

// Register Core Diagnostic Tool
server.tool(
  'ping_host',
  'Performs synthetic roundtrip latency test against a target hostname.',
  { target: z.string().min(3) },
  async ({ target }) => ({
    content: [{ type: 'text', text: `Host ${target} reachable. Roundtrip: 14.2ms` }]
  })
);

async function startServer() {
  const mode = process.env.MCP_TRANSPORT_MODE || 'stdio';

  if (mode === 'stdio') {
    const transport = new StdioServerTransport();
    await server.connect(transport);
    console.error('[MCP GATEWAY] Initialized on stdio pipe.');
  } else if (mode === 'sse') {
    const app = express();
    const port = parseInt(process.env.PORT || '3000', 10);
    let sseTransport: SSEServerTransport | null = null;

    app.get('/sse', async (req, res) => {
      console.error('[MCP SSE] Client connected to /sse stream.');
      sseTransport = new SSEServerTransport('/messages', res);
      await server.connect(sseTransport);
    });

    app.post('/messages', async (req, res) => {
      if (!sseTransport) {
        res.status(400).send('SSE transport session not initialized.');
        return;
      }
      await sseTransport.handlePostMessage(req, res);
    });

    app.listen(port, () => {
      console.error(`[MCP GATEWAY] Remote SSE Server listening on port ${port}.`);
    });
  }
}

startServer().catch((err) => {
  console.error('Fatal bootstrapping error:', err);
  process.exit(1);
});
