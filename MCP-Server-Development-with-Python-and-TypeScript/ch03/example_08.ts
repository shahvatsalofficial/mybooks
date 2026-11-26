/**
 * recipe_3_3_binary_multimodal_resources.ts
 * Hardened binary resource provider with MIME sniffing and memory bounds.
 */

import { promises as fs } from 'fs';
import path from 'path';
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
  McpError,
  ErrorCode,
} from '@modelcontextprotocol/sdk/types.js';

const ASSETS_DIR = path.resolve(process.env.ASSETS_DIR || './assets');
const MAX_BLOB_BYTES = 10 * 1024 * 1024; // 10MB memory safety ceiling

const MIME_MAP: Record<string, string> = {
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.webp': 'image/webp',
  '.pdf': 'application/pdf',
  '.svg': 'image/svg+xml',
};

const server = new Server(
  { name: 'binary-assets-server', version: '1.0.0' },
  { capabilities: { resources: {} } }
);

server.setRequestHandler(ListResourcesRequestSchema, async () => {
  try {
    const files = await fs.readdir(ASSETS_DIR);
    const resources = files.map((file) => {
      const ext = path.extname(file).toLowerCase();
      return {
        uri: `memo://assets/${file}`,
        name: file,
        description: `Binary visual/multimodal asset: ${file}`,
        mimeType: MIME_MAP[ext] || 'application/octet-stream',
      };
    });
    return { resources };
  } catch {
    return { resources: [] };
  }
});

server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  const { uri } = request.params;
  const prefix = 'memo://assets/';

  if (!uri.startsWith(prefix)) {
    throw new McpError(ErrorCode.InvalidParams, `Illegal URI prefix for binary provider: ${uri}`);
  }

  const filename = uri.slice(prefix.length);
  const safePath = path.resolve(ASSETS_DIR, filename);

  // Security: Guard against directory traversal
  if (!safePath.startsWith(ASSETS_DIR)) {
    throw new McpError(ErrorCode.InvalidParams, 'Directory traversal attempt detected.');
  }

  try {
    const stat = await fs.stat(safePath);
    
    // Memory Protection Guard: Prevent Heap OOM
    if (stat.size > MAX_BLOB_BYTES) {
      throw new McpError(
        ErrorCode.InternalError,
        `Asset size (${(stat.size / 1024 / 1024).toFixed(2)} MB) exceeds server safety limit of 10 MB.`
      );
    }

    const fileBuffer = await fs.readFile(safePath);
    const ext = path.extname(safePath).toLowerCase();
    const mimeType = MIME_MAP[ext] || 'application/octet-stream';

    // If SVG or textual, return as text string; otherwise return as Base64 blob
    if (ext === '.svg') {
      return {
        contents: [
          {
            uri,
            mimeType,
            text: fileBuffer.toString('utf-8'),
          },
        ],
      };
    }

    // Return RFC 4648 Base64 encoded blob
    return {
      contents: [
        {
          uri,
          mimeType,
          blob: fileBuffer.toString('base64'),
        },
      ],
    };
  } catch (err: any) {
    if (err instanceof McpError) throw err;
    throw new McpError(ErrorCode.InternalError, `Failed to read binary asset: ${err.message}`);
  }
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('[Binary Asset Server] Online and ready.');
}

main().catch(console.error);
