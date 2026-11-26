/**
 * Recipe 04.3: Official TypeScript MCP Client with Dynamic Discovery
 * Author: Vatsal Shah (Opportunity4u Press)
 * License: Apache-2.0
 */

import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { SSEClientTransport } from '@modelcontextprotocol/sdk/client/sse.js';

export class EnterpriseMcpClient {
  private client: Client;
  private transport: SSEClientTransport;

  constructor(serverUrl: string, authToken?: string) {
    this.transport = new SSEClientTransport(new URL(serverUrl), {
      requestInit: {
        headers: authToken ? { Authorization: `Bearer ${authToken}` } : {}
      }
    });

    this.client = new Client(
      { name: 'EnterpriseGatewayClient', version: '2.0.0' },
      { capabilities: { roots: { listChanged: true } } }
    );
  }

  async connectAndDiscover(): Promise<{ tools: string[]; resources: string[] }> {
    await this.client.connect(this.transport);
    console.log('Connected to remote MCP Server over SSE.');

    // Enumerate Tools
    const toolsResult = await this.client.listTools();
    const toolNames = toolsResult.tools.map(t => t.name);

    // Enumerate Resources
    const resourcesResult = await this.client.listResources();
    const resourceUris = resourcesResult.resources.map(r => r.uri);

    return { tools: toolNames, resources: resourceUris };
  }

  async callTool(name: string, args: Record<string, any>): Promise<any> {
    const result = await this.client.callTool({ name, arguments: args });
    return result.content;
  }

  async close(): Promise<void> {
    await this.client.close();
  }
}
