/**
 * MCP Server-Sent Events (SSE) Transport with Enterprise mTLS Identity Binding
 * Runtime: Node.js (v20+) with TypeScript and @modelcontextprotocol/sdk
 * Author: Vatsal Shah | Vatsal Shah
 */

import https from 'node:https';
import fs from 'node:fs';
import path from 'node:path';
import express, { Request, Response, NextFunction } from 'express';
import { TLSSocket } from 'node:tls';
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { SSEServerTransport } from '@modelcontextprotocol/sdk/server/sse.js';
import { z } from 'zod';

interface SpiffeIdentity {
  trustDomain: string;
  namespace: string;
  serviceAccount: string;
  rawUri: string;
}

interface AuthenticatedRequest extends Request {
  clientIdentity?: SpiffeIdentity;
}

// 1. SPIFFE URI Parser Helper
function parseSpiffeUri(uri: string): SpiffeIdentity | null {
  const match = uri.match(/^spiffe:\/\/([^\/]+)\/ns\/([^\/]+)\/sa\/([^\/]+)$/);
  if (!match) return null;
  return {
    trustDomain: match[1],
    namespace: match[2],
    serviceAccount: match[3],
    rawUri: uri
  };
}

// 2. mTLS Authentication Middleware
function enforceMtls(req: AuthenticatedRequest, res: Response, next: NextFunction): void {
  const socket = req.socket as TLSSocket;

  if (!socket.authorized) {
    res.status(401).json({
      jsonrpc: '2.0',
      error: {
        code: -32001,
        message: 'Unauthorized: Valid X.509 client certificate required for mTLS transport.'
      },
      id: null
    });
    return;
  }

  const cert = socket.getPeerCertificate(true);
  if (!cert || !cert.subjectaltname) {
    res.status(403).json({
      jsonrpc: '2.0',
      error: {
        code: -32003,
        message: 'Forbidden: Client certificate missing Subject Alternative Name (SAN).'
      },
      id: null
    });
    return;
  }

  // Extract URI SAN (SPIFFE ID)
  const sanEntries = cert.subjectaltname.split(', ');
  let spiffeId: SpiffeIdentity | null = null;

  for (const entry of sanEntries) {
    if (entry.startsWith('URI:spiffe://')) {
      spiffeId = parseSpiffeUri(entry.replace('URI:', ''));
      if (spiffeId) break;
    }
  }

  if (!spiffeId) {
    res.status(403).json({
      jsonrpc: '2.0',
      error: {
        code: -32003,
        message: 'Forbidden: No compliant SPIFFE ID found in client certificate SAN entries.'
      },
      id: null
    });
    return;
  }

  // Attach verified identity to request lifecycle
  req.clientIdentity = spiffeId;
  next();
}

// 3. Initialize Express & MCP Server
const app = express();
const mcp = new McpServer({
  name: 'enterprise-filesystem-storage-mcp',
  version: '2.0.0'
});

// Register production tool with Zod schema validation
mcp.tool(
  'read_secure_cloud_resource',
  'Retrieve encrypted cloud asset metadata by bucket and object key',
  {
    bucket_name: z.string().min(3).max(63).regex(/^[a-z0-9.-]+$/),
    object_key: z.string().min(1).max(1024),
    decrypt_payload: z.boolean().default(false)
  },
  async ({ bucket_name, object_key, decrypt_payload }) => {
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            status: 'success',
            bucket: bucket_name,
            key: object_key,
            sha256: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
            decrypted: decrypt_payload,
            timestamp: new Date().toISOString()
          }, null, 2)
        }
      ]
    };
  }
);

// Map SSE endpoints behind mTLS barrier
let activeTransport: SSEServerTransport | null = null;

app.get('/sse', enforceMtls, async (req: AuthenticatedRequest, res: Response) => {
  console.log(`[mTLS Connected] Client SPIFFE: ${req.clientIdentity?.rawUri}`);
  activeTransport = new SSEServerTransport('/messages', res);
  await mcp.connect(activeTransport);
});

app.post('/messages', enforceMtls, async (req: AuthenticatedRequest, res: Response) => {
  if (!activeTransport) {
    res.status(400).send('No active SSE session established');
    return;
  }
  await activeTransport.handlePostMessage(req, res);
});

// 4. Launch Secure HTTPS Server with Client Certificate Enforcement
const tlsOptions: https.ServerOptions = {
  key: fs.readFileSync(path.join(__dirname, 'certs', 'server-key.pem')),
  cert: fs.readFileSync(path.join(__dirname, 'certs', 'server-cert.pem')),
  ca: fs.readFileSync(path.join(__dirname, 'certs', 'corporate-ca-chain.pem')),
  requestCert: true,        // Force client certificate negotiation
  rejectUnauthorized: true, // Reject handshakes that fail CA chain validation
  minVersion: 'TLSv1.3'     // Enforce modern TLS 1.3 specification
};

const PORT = 8443;
https.createServer(tlsOptions, app).listen(PORT, () => {
  console.log(`🔒 Production MCP Server listening over mTLS on port ${PORT}`);
});
