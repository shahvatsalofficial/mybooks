/**
 * production_sse_server.ts
 * Enterprise-grade resilient Server-Sent Events (SSE) MCP Transport Server.
 * Implements session TTL eviction, periodic keepalive heartbeats, and anti-buffering.
 */

import express, { Request, Response } from 'express';
import { randomUUID } from 'crypto';

interface SessionContext {
  sessionId: string;
  res: Response;
  createdAt: number;
  lastActivity: number;
}

export class ProductionSSEServer {
  private app = express();
  private sessions = new Map<string, SessionContext>();
  private heartbeatIntervalMs = 15000; // 15 seconds keep-alive
  private sessionTtlMs = 300000;        // 5 minutes inactivity timeout
  private timer?: NodeJS.Timeout;

  constructor(private port: number = 3001) {
    this.setupMiddleware();
    this.setupRoutes();
    this.startWatchdog();
  }

  private setupMiddleware(): void {
    // Body parser for upstream JSON-RPC POST requests
    this.app.use(express.json({ limit: '10mb' }));

    // CORS enablement for cross-origin LLM web hosts
    this.app.use((req, res, next) => {
      res.setHeader('Access-Control-Allow-Origin', '*');
      res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
      res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization, Last-Event-ID');
      if (req.method === 'OPTIONS') {
        res.sendStatus(200);
        return;
      }
      next();
    });
  }

  private setupRoutes(): void {
    // 1. Downstream EventStream initiation endpoint
    this.app.get('/sse', (req: Request, res: Response) => {
      const sessionId = randomUUID();

      // Mandatory HTTP headers for streaming SSE without proxy buffering
      res.writeHead(200, {
        'Content-Type': 'text/event-stream; charset=utf-8',
        'Cache-Control': 'no-cache, no-transform',
        'Connection': 'keep-alive',
        'X-Accel-Buffering': 'no', // Instructs Nginx / OpenResty to disable chunk buffering
      });

      // Flush headers immediately
      res.flushHeaders();

      const session: SessionContext = {
        sessionId,
        res,
        createdAt: Date.now(),
        lastActivity: Date.now(),
      };

      this.sessions.set(sessionId, session);
      console.log(`[SSE] Client connected. Session created: ${sessionId}`);

      // Emit mandatory initial 'endpoint' event per MCP specification
      const endpointUri = `/message?sessionId=${sessionId}`;
      res.write(`event: endpoint\ndata: ${endpointUri}\n\n`);

      // Handle socket disconnect
      req.on('close', () => {
        console.log(`[SSE] Socket closed for session: ${sessionId}`);
        this.sessions.delete(sessionId);
      });
    });

    // 2. Upstream JSON-RPC backchannel endpoint
    this.app.post('/message', (req: Request, res: Response) => {
      const sessionId = req.query.sessionId as string;

      if (!sessionId || !this.sessions.has(sessionId)) {
        res.status(404).json({ error: 'Session not found or expired' });
        return;
      }

      const session = this.sessions.get(sessionId)!;
      session.lastActivity = Date.now();

      const incomingRpc = req.body;
      console.log(`[SSE] Received RPC for session ${sessionId}:`, incomingRpc.method || 'Response/Ack');

      // Acknowledge receipt immediately with HTTP 202 Accepted
      res.status(202).send();

      // Process message asynchronously and push response down the SSE pipe
      this.handleRpcMessage(session, incomingRpc);
    });
  }

  private handleRpcMessage(session: SessionContext, message: any): void {
    // Example handling: If ping, reply immediately
    if (message.method === 'ping') {
      const response = {
        jsonrpc: '2.0',
        result: {},
        id: message.id,
      };
      this.sendEvent(session, 'message', response);
      return;
    }

    // Example mock tool call response
    if (message.method === 'tools/list') {
      const toolsResponse = {
        jsonrpc: '2.0',
        result: {
          tools: [
            {
              name: 'system_uptime',
              description: 'Retrieve host system uptime metrics.',
              inputSchema: { type: 'object', properties: {} },
            },
          ],
        },
        id: message.id,
      };
      this.sendEvent(session, 'message', toolsResponse);
    }
  }

  /**
   * Transmit a structured event down the client's SSE pipe
   */
  public sendEvent(session: SessionContext, eventType: string, data: any): void {
    const payload = typeof data === 'string' ? data : JSON.stringify(data);
    session.res.write(`event: ${eventType}\ndata: ${payload}\n\n`);
  }

  private startWatchdog(): void {
    this.timer = setInterval(() => {
      const now = Date.now();
      for (const [sessionId, session] of this.sessions.entries()) {
        // 1. Evict inactive dead sessions
        if (now - session.lastActivity > this.sessionTtlMs) {
          console.warn(`[SSE] Evicting stale session: ${sessionId}`);
          session.res.end();
          this.sessions.delete(sessionId);
          continue;
        }

        // 2. Emit TCP keepalive comment
        session.res.write(': keepalive\n\n');
      }
    }, this.heartbeatIntervalMs);
  }

  public listen(): void {
    this.app.listen(this.port, () => {
      console.log(`[ProductionSSEServer] Listening on port ${this.port}`);
      console.log(`[ProductionSSEServer] SSE endpoint: http://localhost:${this.port}/sse`);
    });
  }

  public shutdown(): void {
    if (this.timer) clearInterval(this.timer);
    for (const session of this.sessions.values()) {
      session.res.end();
    }
    this.sessions.clear();
  }
}

// Instantiate and start server if executed directly
if (require.main === module) {
  const server = new ProductionSSEServer(3001);
  server.listen();
}
