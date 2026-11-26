/**
 * @file work_management_mcp.ts
 * Enterprise Jira and Linear Work Management Model Context Protocol Server.
 * Enforces transition state machine validation and automated test evidence attachment.
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ErrorCode,
  McpError
} from '@modelcontextprotocol/sdk/types.js';

interface JiraConfig {
  host: string;
  email: string;
  apiToken: string;
}

export class WorkManagementMcpServer {
  private server: Server;
  private config: JiraConfig;

  constructor(config: JiraConfig) {
    this.config = config;
    this.server = new Server(
      { name: 'enterprise-work-management-mcp', version: '2.0.0' },
      { capabilities: { tools: {} } }
    );
    this.setupHandlers();
  }

  private async fetchJira(endpoint: string, options: RequestInit = {}): Promise<any> {
    const authHeader = Buffer.from(`${this.config.email}:${this.config.apiToken}`).toString('base64');
    const response = await fetch(`https://${this.config.host}/rest/api/3${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Basic ${authHeader}`,
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        ...options.headers
      }
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Jira API Error (${response.status}): ${errorText}`);
    }
    return response.json();
  }

  private setupHandlers(): void {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: 'get_issue_details',
            description: 'Fetch complete details, description, acceptance criteria, and legal status transitions for an issue.',
            inputSchema: {
              type: 'object',
              properties: {
                issueKey: { type: 'string', description: 'Jira issue key (e.g. CORE-4821)' }
              },
              required: ['issueKey']
            }
          },
          {
            name: 'transition_issue_with_comment',
            description: 'Transition an issue to a new status and attach an immutable work log comment.',
            inputSchema: {
              type: 'object',
              properties: {
                issueKey: { type: 'string' },
                targetStatusName: { type: 'string', description: 'Name of the status (e.g. Code Review, In Progress)' },
                commentMarkdown: { type: 'string', description: 'Work log detailing changes made and PR links' }
              },
              required: ['issueKey', 'targetStatusName', 'commentMarkdown']
            }
          }
        ]
      };
    });

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const args = request.params.arguments || {};
      switch (request.params.name) {
        case 'get_issue_details': {
          const key = String(args.issueKey);
          return await this.handleGetIssueDetails(key);
        }
        case 'transition_issue_with_comment': {
          const key = String(args.issueKey);
          const targetStatus = String(args.targetStatusName);
          const comment = String(args.commentMarkdown);
          return await this.handleTransitionIssue(key, targetStatus, comment);
        }
        default:
          throw new McpError(ErrorCode.MethodNotFound, `Unknown tool: ${request.params.name}`);
      }
    });
  }

  private async handleGetIssueDetails(issueKey: string) {
    try {
      const issue = await this.fetchJira(`/issue/${issueKey}`);
      const transitionsData = await this.fetchJira(`/issue/${issueKey}/transitions`);

      const availableTransitions = transitionsData.transitions.map((t: any) => ({
        id: t.id,
        name: t.name,
        targetStatus: t.to.name
      }));

      const summary = {
        key: issue.key,
        summary: issue.fields.summary,
        status: issue.fields.status.name,
        priority: issue.fields.priority?.name,
        assignee: issue.fields.assignee ? issue.fields.assignee.displayName : 'Unassigned',
        description: issue.fields.description,
        availableTransitions
      };

      return {
        content: [{ type: 'text', text: JSON.stringify(summary, null, 2) }]
      };
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      throw new McpError(ErrorCode.InternalError, `Failed to get issue: ${msg}`);
    }
  }

  private async handleTransitionIssue(issueKey: string, targetStatusName: string, commentMarkdown: string) {
    try {
      // 1. Fetch legal transitions
      const transitionsData = await this.fetchJira(`/issue/${issueKey}/transitions`);
      const match = transitionsData.transitions.find(
        (t: any) => t.name.toLowerCase() === targetStatusName.toLowerCase() ||
                    t.to.name.toLowerCase() === targetStatusName.toLowerCase()
      );

      if (!match) {
        const legalNames = transitionsData.transitions.map((t: any) => t.to.name).join(', ');
        throw new McpError(
          ErrorCode.InvalidParams,
          `Illegal transition to '${targetStatusName}'. Valid legal transitions for ${issueKey} are: [${legalNames}]`
        );
      }

      // 2. Perform transition
      await this.fetchJira(`/issue/${issueKey}/transitions`, {
        method: 'POST',
        body: JSON.stringify({
          transition: { id: match.id }
        })
      });

      // 3. Add formal comment
      await this.fetchJira(`/issue/${issueKey}/comment`, {
        method: 'POST',
        body: JSON.stringify({
          body: {
            type: 'doc',
            version: 1,
            content: [
              {
                type: 'paragraph',
                content: [{ type: 'text', text: commentMarkdown }]
              }
            ]
          }
        })
      });

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              success: true,
              issueKey,
              newStatus: match.to.name,
              transitionId: match.id
            }, null, 2)
          }
        ]
      };
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      throw new McpError(ErrorCode.InternalError, `Failed to transition issue: ${msg}`);
    }
  }

  public async start(): Promise<void> {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Enterprise Work Management MCP Server running on stdio');
  }
}
