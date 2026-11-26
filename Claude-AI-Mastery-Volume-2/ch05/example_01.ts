/**
 * Recipe 05.1: Enterprise SRE Kubernetes Diagnostics MCP Server
 * Author: Vatsal Shah (Opportunity4u Press)
 * License: Apache-2.0
 */

import { McpServer, ResourceTemplate } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';

const server = new McpServer({
  name: 'enterprise-k8s-sre-server',
  version: '2.0.0',
});

// ═══════════════════════════════════════════════════════════════════════
// 1. Production Tools (Actions with Zod Validation)
// ═══════════════════════════════════════════════════════════════════════

server.tool(
  'restart_deployment',
  'Triggers a zero-downtime rolling restart of a Kubernetes deployment.',
  {
    namespace: z.string().min(2).default('production'),
    deploymentName: z.string().min(2),
    reason: z.string().min(5),
  },
  async ({ namespace, deploymentName, reason }) => {
    // In production, execute via @kubernetes/client-node
    console.error(`[AUDIT] User triggered rolling restart for ${deploymentName} in ${namespace}. Reason: ${reason}`);

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            status: 'SUCCESS',
            action: 'ROLLING_RESTART_TRIGGERED',
            deployment: deploymentName,
            namespace,
            timestamp: new Date().toISOString(),
          }),
        },
      ],
    };
  }
);

// ═══════════════════════════════════════════════════════════════════════
// 2. Dynamic Resource Templates (Read-Only Telemetry)
// ═══════════════════════════════════════════════════════════════════════

server.resource(
  'pod-logs',
  new ResourceTemplate('k8s://{namespace}/pods/{podName}/logs', { list: undefined }),
  async (uri, { namespace, podName }) => {
    // Simulate log retrieval
    const syntheticLogs = `2026-10-01T12:00:00Z [INFO] Initializing worker thread on ${podName}\n` +
                          `2026-10-01T12:00:02Z [WARN] Database pool connection latency high (142ms)\n` +
                          `2026-10-01T12:00:05Z [INFO] Health check HTTP 200 OK`;

    return {
      contents: [
        {
          uri: uri.href,
          text: syntheticLogs,
          mimeType: 'text/plain',
        },
      ],
    };
  }
);

// ═══════════════════════════════════════════════════════════════════════
// 3. Reusable Parameterized Prompt Template
// ═══════════════════════════════════════════════════════════════════════

server.prompt(
  'incident_retrospective',
  'Generates a standardized post-mortem retrospective from raw metrics.',
  {
    serviceName: z.string(),
    outageDurationMinutes: z.string(),
  },
  ({ serviceName, outageDurationMinutes }) => {
    return {
      messages: [
        {
          role: 'user',
          content: {
            type: 'text',
            text: `Please construct a blameless post-mortem retrospective for service '${serviceName}' which experienced an outage lasting ${outageDurationMinutes} minutes. Follow Google SRE guidelines and analyze Root Cause, Timeline, Impact, and Action Items.`,
          },
        },
      ],
    };
  }
);

// ═══════════════════════════════════════════════════════════════════════
// 4. Transport Binding & Server Bootstrapping
// ═══════════════════════════════════════════════════════════════════════

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('Enterprise K8s SRE MCP Server running on stdio transport.');
}

main().catch((error) => {
  console.error('Fatal initialization error:', error);
  process.exit(1);
});
