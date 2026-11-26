import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool
} from "@modelcontextprotocol/sdk/types.js";
import { App, LogLevel } from "@slack/bolt";

const app = new App({
  token: process.env.SLACK_BOT_TOKEN, // xoxb-...
  appToken: process.env.SLACK_APP_TOKEN, // xapp-...
  socketMode: true,
  logLevel: LogLevel.WARN
});

const server = new Server(
  { name: "slack-socket-mcp", version: "1.0.0" },
  { capabilities: { tools: {}, resources: {} } }
);

// In-Memory cache of recent channel conversations
const channelHistoryCache = new Map<string, { user: string; text: string; ts: string }[]>();

// Register Bolt Socket Mode Event Listeners
app.message(async ({ message, say }) => {
  if (message.subtype === undefined || message.subtype === "bot_message") {
    const textMsg = (message as any).text || "";
    const channel = (message as any).channel;
    const user = (message as any).user || "bot";
    const ts = (message as any).ts;

    if (!channelHistoryCache.has(channel)) {
      channelHistoryCache.set(channel, []);
    }
    const history = channelHistoryCache.get(channel)!;
    history.push({ user, text: textMsg, ts });
    if (history.length > 50) history.shift(); // Keep last 50 messages
  }
});

server.setRequestHandler(ListToolsRequestSchema, async () => {
  const tools: Tool[] = [
    {
      name: "post_slack_message",
      description: "Posts a formatted message or threaded reply to a designated Slack channel.",
      inputSchema: {
        type: "object",
        properties: {
          channel_id: { type: "string", description: "Slack channel ID (e.g. 'C0123456789')." },
          text: { type: "string", description: "Plaintext fallback message." },
          thread_ts: { type: "string", description: "Optional thread timestamp to reply inside a thread." }
        },
        required: ["channel_id", "text"]
      }
    },
    {
      name: "post_approval_request_card",
      description: "Posts an interactive Block Kit approval card with Approve/Reject buttons.",
      inputSchema: {
        type: "object",
        properties: {
          channel_id: { type: "string", description: "Target Slack channel ID." },
          action_title: { type: "string", description: "Action requiring human approval (e.g. 'Deploy to Production')." },
          details_markdown: { type: "string", description: "Markdown details explaining the action." },
          action_id: { type: "string", description: "Unique tracking ID for the approval." }
        },
        required: ["channel_id", "action_title", "details_markdown", "action_id"]
      }
    },
    {
      name: "get_channel_recent_history",
      description: "Reads the last 20 cached messages from a Slack channel to reconstruct context.",
      inputSchema: {
        type: "object",
        properties: {
          channel_id: { type: "string", description: "Slack channel ID." }
        },
        required: ["channel_id"]
      }
    }
  ];
  return { tools };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  const channelId = String(args?.channel_id);

  if (name === "post_slack_message") {
    const text = String(args?.text);
    const threadTs = args?.thread_ts ? String(args.thread_ts) : undefined;

    try {
      const res = await app.client.chat.postMessage({
        channel: channelId,
        text,
        thread_ts: threadTs
      });
      return {
        content: [{ type: "text", text: `Message posted successfully to channel ${channelId} (ts: ${res.ts}).` }]
      };
    } catch (err: any) {
      return { isError: true, content: [{ type: "text", text: `Slack Post Error: ${err.message}` }] };
    }
  }

  if (name === "post_approval_request_card") {
    const actionTitle = String(args?.action_title);
    const details = String(args?.details_markdown);
    const actionId = String(args?.action_id);

    try {
      const res = await app.client.chat.postMessage({
        channel: channelId,
        text: `Approval Required: ${actionTitle}`,
        blocks: [
          {
            type: "header",
            text: { type: "plain_text", text: `⚠️ Human Approval Required: ${actionTitle}` }
          },
          {
            type: "section",
            text: { type: "mrkdwn", text: details }
          },
          {
            type: "actions",
            elements: [
              {
                type: "button",
                text: { type: "plain_text", text: "Approve Action" },
                style: "primary",
                value: actionId,
                action_id: "mcp_approve_action"
              },
              {
                type: "button",
                text: { type: "plain_text", text: "Reject / Abort" },
                style: "danger",
                value: actionId,
                action_id: "mcp_reject_action"
              }
            ]
          }
        ]
      });

      return {
        content: [{ type: "text", text: `Approval card posted to ${channelId} (ts: ${res.ts}). Waiting for human button click.` }]
      };
    } catch (err: any) {
      return { isError: true, content: [{ type: "text", text: `Slack Card Error: ${err.message}` }] };
    }
  }

  if (name === "get_channel_recent_history") {
    const history = channelHistoryCache.get(channelId) || [];
    return {
      content: [{ type: "text", text: JSON.stringify(history.slice(-20), null, 2) }]
    };
  }

  throw new Error(`Tool ${name} not found`);
});

async function run() {
  await app.start();
  console.error("Slack Bolt Socket Mode client connected.");
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Slack MCP Server running on stdio.");
}

run().catch(console.error);
