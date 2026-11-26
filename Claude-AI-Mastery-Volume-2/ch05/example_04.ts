/**
 * Recipe 05.4: Vitest Integration Testing Suite for MCP Servers
 * Author: Vatsal Shah (Opportunity4u Press)
 * License: Apache-2.0
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { InMemoryTransport } from '@modelcontextprotocol/sdk/inMemory.js';
import { z } from 'zod';

describe('Enterprise Kubernetes MCP Server Test Suite', () => {
  let server: McpServer;
  let client: Client;
  let serverTransport: InMemoryTransport;
  let clientTransport: InMemoryTransport;

  beforeEach(async () => {
    server = new McpServer({ name: 'test-k8s-server', version: '1.0.0' });

    server.tool('echo_test', 'Simple echo tool', { message: z.string() }, async ({ message }) => ({
      content: [{ type: 'text', text: `ECHO: ${message}` }]
    }));

    [clientTransport, serverTransport] = InMemoryTransport.createLinkedPair();
    client = new Client({ name: 'test-client', version: '1.0.0' }, { capabilities: {} });

    await Promise.all([
      server.connect(serverTransport),
      client.connect(clientTransport)
    ]);
  });

  afterEach(async () => {
    await client.close();
    await server.close();
  });

  it('correctly discovers registered tools', async () => {
    const tools = await client.listTools();
    expect(tools.tools.length).toBe(1);
    expect(tools.tools[0].name).toBe('echo_test');
  });

  it('executes tool successfully with valid parameters', async () => {
    const result = await client.callTool({
      name: 'echo_test',
      arguments: { message: 'Production Readiness Check' }
    });
    expect(result.content[0].type).toBe('text');
    expect((result.content[0] as any).text).toBe('ECHO: Production Readiness Check');
  });

  it('rejects invalid parameters with schema error code', async () => {
    await expect(
      client.callTool({
        name: 'echo_test',
        arguments: { message: 12345 as any }
      })
    ).rejects.toThrow();
  });
});
