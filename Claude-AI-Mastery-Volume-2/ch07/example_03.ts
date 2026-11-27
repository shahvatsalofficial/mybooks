/**
 * Recipe 07.3: Slack Incident War Room MCP Bridge with Interactive Approvals
 * Author: Vatsal Shah (Vatsal Shah)
 * License: Apache-2.0
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { WebClient } from '@slack/web-api';
import { z } from 'zod';

const slackClient = new WebClient(process.env.SLACK_BOT_TOKEN);
const server = new McpServer({ name: 'slack-incident-bridge', version: '2.0.0' });

server.tool(
  'post_incident_diagnostic_card',
  'Posts a high-priority diagnostic status card with interactive approval buttons to an active incident channel.',
  {
    channelId: z.string().min(5).describe('Slack Channel ID (e.g. C0123456789)'),
    title: z.string().min(5).describe('Incident or Remediation Title'),
    diagnosticSummary: z.string().min(10).describe('Technical findings and metrics'),
    actionRequired: z.string().describe('Proposed operational action (e.g. Restart Pod, Failover DB)'),
    severity: z.enum(['P1_CRITICAL', 'P2_HIGH', 'P3_MODERATE', 'INFO'])
  },
  async ({ channelId, title, diagnosticSummary, actionRequired, severity }) => {
    const colorMap = {
      P1_CRITICAL: '#DC2626',
      P2_HIGH: '#F59E0B',
      P3_MODERATE: '#3B82F6',
      INFO: '#10B981'
    };

    try {
      const response = await slackClient.chat.postMessage({
        channel: channelId,
        text: `[${severity}] ${title}`,
        attachments: [
          {
            color: colorMap[severity],
            blocks: [
              {
                type: 'header',
                text: { type: 'plain_text', text: `🚨 [${severity}] ${title}`, emoji: true }
              },
              {
                type: 'section',
                text: { type: 'mrkdwn', text: `*Telemetry & Diagnostics:*\n${diagnosticSummary}` }
              },
              {
                type: 'section',
                text: { type: 'mrkdwn', text: `*Proposed Automated Action:*\n\`${actionRequired}\`` }
              },
              {
                type: 'actions',
                elements: [
                  {
                    type: 'button',
                    text: { type: 'plain_text', text: '✅ Approve Remediation', emoji: true },
                    style: 'primary',
                    value: `approve_${Date.now()}`,
                    action_id: 'approve_mcp_remediation'
                  },
                  {
                    type: 'button',
                    text: { type: 'plain_text', text: '❌ Reject & Abort', emoji: true },
                    style: 'danger',
                    value: `reject_${Date.now()}`,
                    action_id: 'reject_mcp_remediation'
                  }
                ]
              }
            ]
          }
        ]
      });

      return {
        content: [{ type: 'text', text: `Diagnostic Card dispatched to channel ${channelId}. Message TS: ${response.ts}` }]
      };
    } catch (err: any) {
      return {
        isError: true,
        content: [{ type: 'text', text: `Slack API Failure: ${err.message}` }]
      };
    }
  }
);

async function run() {
  await server.connect(new StdioServerTransport());
}
run();
