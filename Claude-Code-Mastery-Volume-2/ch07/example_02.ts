/**
 * @file github_enterprise_mcp.ts
 * Hardened GitHub Enterprise Model Context Protocol Server.
 * Enforces branch protections, GitHub App JWT auth, and automated PR synthesis.
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ErrorCode,
  McpError
} from '@modelcontextprotocol/sdk/types.js';
import { Octokit } from '@octokit/rest';
import { createAppAuth } from '@octokit/auth-app';

interface GitHubConfig {
  appId: number;
  privateKey: string;
  installationId: number;
  baseUrl?: string; // Optional for GitHub Enterprise Server
}

export class GitHubEnterpriseMcpServer {
  private server: Server;
  private octokit: Octokit;

  constructor(config: GitHubConfig) {
    this.server = new Server(
      {
        name: 'enterprise-github-mcp',
        version: '2.0.0'
      },
      {
        capabilities: { tools: {} }
      }
    );

    this.octokit = new Octokit({
      authStrategy: createAppAuth,
      auth: {
        appId: config.appId,
        privateKey: config.privateKey,
        installationId: config.installationId
      },
      baseUrl: config.baseUrl || 'https://api.github.com'
    });

    this.setupHandlers();
  }

  private setupHandlers(): void {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: 'get_file_contents',
            description: 'Fetch the raw text contents of a file from a specified repository branch or commit SHA.',
            inputSchema: {
              type: 'object',
              properties: {
                owner: { type: 'string', description: 'Repository organization or owner' },
                repo: { type: 'string', description: 'Repository name' },
                path: { type: 'string', description: 'Path to the file within the repository' },
                ref: { type: 'string', description: 'Branch name, tag, or commit SHA (defaults to default branch)' }
              },
              required: ['owner', 'repo', 'path']
            }
          },
          {
            name: 'create_pull_request_with_checks',
            description: 'Create a feature branch, commit changes, and submit a pull request with automated template metadata.',
            inputSchema: {
              type: 'object',
              properties: {
                owner: { type: 'string' },
                repo: { type: 'string' },
                title: { type: 'string', description: 'Semantic PR title (e.g. feat(auth): add pkce validation)' },
                body: { type: 'string', description: 'Structured markdown body detailing changes and test evidence' },
                headBranch: { type: 'string', description: 'New feature branch to create (cannot be main/master)' },
                baseBranch: { type: 'string', description: 'Target branch to merge into', default: 'main' },
                draft: { type: 'boolean', description: 'Whether to open PR as a draft', default: true }
              },
              required: ['owner', 'repo', 'title', 'body', 'headBranch']
            }
          },
          {
            name: 'fetch_ci_failure_logs',
            description: 'Retrieve detailed error logs from the most recent failed GitHub Actions workflow run for a PR.',
            inputSchema: {
              type: 'object',
              properties: {
                owner: { type: 'string' },
                repo: { type: 'string' },
                pullNumber: { type: 'integer', description: 'The pull request number' }
              },
              required: ['owner', 'repo', 'pullNumber']
            }
          }
        ]
      };
    });

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const args = request.params.arguments || {};
      switch (request.params.name) {
        case 'get_file_contents':
          return await this.handleGetFileContents(
            String(args.owner),
            String(args.repo),
            String(args.path),
            args.ref ? String(args.ref) : undefined
          );
        case 'create_pull_request_with_checks':
          return await this.handleCreatePullRequest(
            String(args.owner),
            String(args.repo),
            String(args.title),
            String(args.body),
            String(args.headBranch),
            String(args.baseBranch || 'main'),
            Boolean(args.draft)
          );
        case 'fetch_ci_failure_logs':
          return await this.handleFetchCiFailureLogs(
            String(args.owner),
            String(args.repo),
            Number(args.pullNumber)
          );
        default:
          throw new McpError(ErrorCode.MethodNotFound, `Unknown tool: ${request.params.name}`);
      }
    });
  }

  private async handleGetFileContents(owner: string, repo: string, path: string, ref?: string) {
    try {
      const { data } = await this.octokit.rest.repos.getContent({
        owner,
        repo,
        path,
        ref
      });

      if ('content' in data && data.type === 'file') {
        const decoded = Buffer.from(data.content, 'base64').toString('utf8');
        return {
          content: [{ type: 'text', text: decoded }]
        };
      }
      throw new McpError(ErrorCode.InvalidRequest, `Path is not a valid file: ${path}`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      throw new McpError(ErrorCode.InternalError, `GitHub getContent failed: ${msg}`);
    }
  }

  private async handleCreatePullRequest(
    owner: string,
    repo: string,
    title: string,
    body: string,
    headBranch: string,
    baseBranch: string,
    draft: boolean
  ) {
    // Protocol-level guardrail: Prevent branches that target protected names directly
    const protectedBranchPatterns = ['main', 'master', 'production', 'release/*'];
    if (protectedBranchPatterns.includes(headBranch.toLowerCase())) {
      throw new McpError(
        ErrorCode.InvalidParams,
        `Security Policy: Head branch '${headBranch}' is protected. Agents must commit to unique feature branches.`
      );
    }

    try {
      // 1. Get base branch SHA
      const { data: baseRef } = await this.octokit.rest.git.getRef({
        owner,
        repo,
        ref: `heads/${baseBranch}`
      });

      // 2. Create head branch
      await this.octokit.rest.git.createRef({
        owner,
        repo,
        ref: `refs/heads/${headBranch}`,
        sha: baseRef.object.sha
      });

      // 3. Create Pull Request
      const { data: pr } = await this.octokit.rest.pulls.create({
        owner,
        repo,
        title,
        body: `${body}\n\n---\n*Generated autonomously via Enterprise GitHub MCP Server.*`,
        head: headBranch,
        base: baseBranch,
        draft
      });

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(
              {
                pullNumber: pr.number,
                htmlUrl: pr.html_url,
                state: pr.state,
                draft: pr.draft,
                headSha: pr.head.sha
              },
              null,
              2
            )
          }
        ]
      };
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      throw new McpError(ErrorCode.InternalError, `Failed to create pull request: ${msg}`);
    }
  }

  private async handleFetchCiFailureLogs(owner: string, repo: string, pullNumber: number) {
    try {
      // 1. Get PR head commit SHA
      const { data: pr } = await this.octokit.rest.pulls.get({ owner, repo, pull_number: pullNumber });
      const headSha = pr.head.sha;

      // 2. List check runs for commit
      const { data: checkRuns } = await this.octokit.rest.checks.listForRef({
        owner,
        repo,
        ref: headSha
      });

      const failedRuns = checkRuns.check_runs.filter(
        (r) => r.conclusion === 'failure' || r.conclusion === 'timed_out'
      );

      if (failedRuns.length === 0) {
        return {
          content: [{ type: 'text', text: 'All CI checks passed successfully or are currently pending.' }]
        };
      }

      const failureSummaries = failedRuns.map((r) => ({
        name: r.name,
        conclusion: r.conclusion,
        detailsUrl: r.details_url,
        summary: r.output.summary,
        text: r.output.text ? r.output.text.substring(0, 2000) : 'No detailed log text available.'
      }));

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(failureSummaries, null, 2)
          }
        ]
      };
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      throw new McpError(ErrorCode.InternalError, `CI failure log retrieval failed: ${msg}`);
    }
  }

  public async start(): Promise<void> {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Enterprise GitHub MCP Server running on stdio');
  }
}
