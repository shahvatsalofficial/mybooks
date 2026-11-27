#!/usr/bin/env node
/**
 * Recipe 07.2: Chroot Sandboxed Filesystem MCP Server
 * Author: Vatsal Shah (Vatsal Shah)
 * License: Apache-2.0
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';
import * as fs from 'fs';
import * as path from 'path';

// Define sandboxed virtual root directory
const RAW_ROOT = process.env.MCP_WORKSPACE_ROOT || process.cwd();
const SANDBOX_ROOT = fs.realpathSync(path.resolve(RAW_ROOT));

// Sensitive file exclusion blocklist
const SENSITIVE_FILE_PATTERNS = [
  /^\.env/i,
  /\.pem$/i,
  /\.key$/i,
  /id_rsa/i,
  /credentials\.json/i,
  /^\.git\//i,
  /secret/i
];

const server = new McpServer({
  name: 'sandboxed-filesystem-mcp',
  version: '2.4.0',
});

function resolveSafePath(userPath: string): string {
  // Normalize and resolve absolute logical path
  const normalized = path.normalize(userPath).replace(/^(\.\.(\/|\\|$))+/, '');
  const resolved = path.resolve(SANDBOX_ROOT, normalized);

  // Logical containment check
  if (!resolved.startsWith(SANDBOX_ROOT)) {
    throw new Error(`Security Violation: Path '${userPath}' attempts to escape sandbox root.`);
  }

  // Symlink dereference check: verify physical disk location
  if (fs.existsSync(resolved)) {
    const realPhysicalPath = fs.realpathSync(resolved);
    if (!realPhysicalPath.startsWith(SANDBOX_ROOT)) {
      throw new Error(`Security Violation: Symlink '${userPath}' targets external path '${realPhysicalPath}'.`);
    }
  }

  // File exclusion check
  const relPath = path.relative(SANDBOX_ROOT, resolved);
  for (const pattern of SENSITIVE_FILE_PATTERNS) {
    if (pattern.test(relPath) || pattern.test(path.basename(resolved))) {
      throw new Error(`Security Violation: Access to protected configuration file '${relPath}' is forbidden.`);
    }
  }

  return resolved;
}

server.tool(
  'read_sandboxed_file',
  'Reads the text content of a file within the designated workspace sandbox.',
  {
    relativePath: z.string().describe('File path relative to the workspace root.'),
    maxBytes: z.number().int().positive().default(1048576).describe('Maximum byte ceiling (default 1MB).')
  },
  async ({ relativePath, maxBytes }) => {
    try {
      const safePath = resolveSafePath(relativePath);
      if (!fs.existsSync(safePath)) {
        return {
          isError: true,
          content: [{ type: 'text', text: `Error: File '${relativePath}' does not exist.` }],
        };
      }

      const stat = fs.statSync(safePath);
      if (stat.isDirectory()) {
        return {
          isError: true,
          content: [{ type: 'text', text: `Error: Path '${relativePath}' is a directory, not a file.` }],
        };
      }

      if (stat.size > maxBytes) {
        return {
          isError: true,
          content: [{ type: 'text', text: `Error: File size (${stat.size} bytes) exceeds maximum ceiling (${maxBytes} bytes).` }],
        };
      }

      const data = fs.readFileSync(safePath, 'utf-8');
      return {
        content: [{ type: 'text', text: data }],
      };
    } catch (err: any) {
      return {
        isError: true,
        content: [{ type: 'text', text: `Access Denied: ${err.message}` }],
      };
    }
  }
);

server.tool(
  'list_sandboxed_directory',
  'Lists directory contents within the designated workspace sandbox.',
  {
    relativeDir: z.string().default('.').describe('Directory path relative to workspace root.')
  },
  async ({ relativeDir }) => {
    try {
      const safeDir = resolveSafePath(relativeDir);
      const entries = fs.readdirSync(safeDir, { withFileTypes: true });

      const files = entries.map((entry) => ({
        name: entry.name,
        isDirectory: entry.isDirectory(),
        isSymbolicLink: entry.isSymbolicLink()
      }));

      return {
        content: [{ type: 'text', text: JSON.stringify(files, null, 2) }]
      };
    } catch (err: any) {
      return {
        isError: true,
        content: [{ type: 'text', text: `Access Denied: ${err.message}` }]
      };
    }
  }
);

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error(`[Filesystem MCP] Sandbox initialized at: ${SANDBOX_ROOT}`);
}

main().catch((err) => {
  console.error('Fatal initialization error:', err);
  process.exit(1);
});
