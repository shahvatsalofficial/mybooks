/**
 * Multi-Tenant MCP Server with AsyncLocalStorage & S3 Virtual Prefix Isolation
 * Runtime: Node.js (v20+) with TypeScript & @modelcontextprotocol/sdk
 * Author: Vatsal Shah | Vatsal Shah
 */

import { AsyncLocalStorage } from 'node:async_hooks';
import express, { Request, Response, NextFunction } from 'express';
import { S3Client, GetObjectCommand, ListObjectsV2Command } from '@aws-sdk/client-s3';
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { SSEServerTransport } from '@modelcontextprotocol/sdk/server/sse.js';
import { z } from 'zod';

interface TenantContext {
  tenantId: string;
  userId: string;
  planTier: 'STARTER' | 'ENTERPRISE';
}

// 1. Initialize Thread-Safe Asynchronous Context Store
const tenantStorage = new AsyncLocalStorage<TenantContext>();

function getActiveTenant(): TenantContext {
  const ctx = tenantStorage.getStore();
  if (!ctx) {
    throw new Error('Fatal: Accessing tenant storage outside of an active async request boundary');
  }
  return ctx;
}

// 2. S3 Storage Bridge with Path Traversal Guard
class TenantS3StorageBridge {
  private s3: S3Client;
  private bucketName: string;

  constructor(bucketName: string) {
    this.bucketName = bucketName;
    this.s3 = new S3Client({ region: process.env.AWS_REGION || 'us-east-1' });
  }

  private resolveTenantKey(relativeKey: string): string {
    const { tenantId } = getActiveTenant();

    // Sanitize and normalize relative key
    const normalized = relativeKey.replace(/\\/g, '/').replace(/^\/+/, '');
    
    // Prevent path traversal attempts
    if (normalized.includes('..') || normalized.includes('//')) {
      throw new Error(`Security Exception: Path traversal detected in key: '${relativeKey}'`);
    }

    // Force strict tenant prefix scoping: "tenants/{tenantId}/{normalized}"
    return `tenants/${tenantId}/${normalized}`;
  }

  async readAsset(relativeKey: string): Promise<string> {
    const fullKey = this.resolveTenantKey(relativeKey);
    console.log(`[Storage Bridge] Fetching isolated key: s3://${this.bucketName}/${fullKey}`);

    const command = new GetObjectCommand({
      Bucket: this.bucketName,
      Key: fullKey
    });

    const response = await this.s3.send(command);
    if (!response.Body) {
      throw new Error(`Asset '${relativeKey}' returned empty body`);
    }
    return await response.Body.transformToString('utf8');
  }
}

// 3. Initialize MCP Server & S3 Bridge
const storageBridge = new TenantS3StorageBridge(process.env.STORAGE_BUCKET || 'enterprise-ai-assets-prod');
const mcp = new McpServer({
  name: 'multitenant-storage-gateway',
  version: '2.0.0'
});

// Register Tenant-Partitioned Tool
mcp.tool(
  'read_tenant_document',
  'Read a private configuration or document asset from the tenant storage pool',
  {
    document_path: z.string().min(1).describe('Relative path to document, e.g. policies/security.json')
  },
  async ({ document_path }) => {
    try {
      const content = await storageBridge.readAsset(document_path);
      const active = getActiveTenant();

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              status: 'success',
              tenant_id: active.tenantId,
              path: document_path,
              payload: content
            }, null, 2)
          }
        ]
      };
    } catch (err: any) {
      return {
        isError: true,
        content: [{ type: 'text', text: `Failed to read asset: ${err.message}` }]
      };
    }
  }
);

// 4. Express HTTP / SSE Transport Pipeline with AsyncLocalStorage Scoping
const app = express();

function tenantContextMiddleware(req: Request, res: Response, next: NextFunction): void {
  const tenantId = req.header('X-Tenant-ID');
  const userId = req.header('X-User-ID') || 'anonymous-agent';

  if (!tenantId) {
    res.status(400).json({
      jsonrpc: '2.0',
      error: { code: -32602, message: 'Invalid Request: X-Tenant-ID header is required' },
      id: null
    });
    return;
  }

  const context: TenantContext = {
    tenantId: tenantId.trim(),
    userId: userId.trim(),
    planTier: req.header('X-Plan-Tier') === 'STARTER' ? 'STARTER' : 'ENTERPRISE'
  };

  // Run downstream handlers strictly within the AsyncLocalStorage context
  tenantStorage.run(context, () => {
    next();
  });
}

app.use(tenantContextMiddleware);

let activeTransport: SSEServerTransport | null = null;

app.get('/sse', async (req: Request, res: Response) => {
  activeTransport = new SSEServerTransport('/messages', res);
  await mcp.connect(activeTransport);
});

app.post('/messages', async (req: Request, res: Response) => {
  if (!activeTransport) {
    res.status(400).send('Active SSE session missing');
    return;
  }
  await activeTransport.handlePostMessage(req, res);
});

const PORT = 3000;
app.listen(PORT, () => {
  console.log(`🚀 Multi-Tenant MCP Storage Server running on port ${PORT}`);
});
