import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool
} from "@modelcontextprotocol/sdk/types.js";
import { Octokit } from "@octokit/rest";

const octokit = new Octokit({
  auth: process.env.GITHUB_PERSONAL_ACCESS_TOKEN
});

const server = new Server(
  { name: "github-pr-mcp-server", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

// High-Entropy Secret Scanner for Added Lines
function scanLineForSecrets(line: string): string[] {
  const findings: string[] = [];
  const rules = [
    { name: "AWS Access Key", regex: /\bAKIA[0-9A-Z]{16}\b/ },
    { name: "GitHub Personal Access Token", regex: /\bghp_[0-9a-zA-Z]{36}\b/ },
    { name: "Generic High-Entropy Secret", regex: /\b(?=[a-zA-Z0-9]{32,45}\b)[a-zA-Z0-9]*[A-Z][a-zA-Z0-9]*[0-9][a-zA-Z0-9]*\b/ },
    { name: "RSA / EC Private Key Header", regex: /-----BEGIN (?:RSA |EC )?PRIVATE KEY-----/ }
  ];

  for (const rule of rules) {
    if (rule.regex.test(line)) {
      findings.push(rule.name);
    }
  }
  return findings;
}

// Token-Optimized Diff Parser
interface DiffHunk {
  file: string;
  addedLines: { lineNum: number; content: string }[];
  secretAlerts: { lineNum: number; rule: string }[];
}

function parseUnifiedDiff(rawDiff: string): DiffHunk[] {
  const files: DiffHunk[] = [];
  const fileSections = rawDiff.split(/^diff --git /m).filter(Boolean);

  for (const section of fileSections) {
    const lines = section.split("\n");
    const fileHeaderMatch = lines[0].match(/a\/(.+?) b\/(.+?)$/);
    if (!fileHeaderMatch) continue;

    const filename = fileHeaderMatch[2];
    const hunk: DiffHunk = { file: filename, addedLines: [], secretAlerts: [] };

    let currentNewLine = 0;

    for (const line of lines) {
      if (line.startsWith("@@ ")) {
        // Parse hunk header: @@ -old,len +new,len @@
        const match = line.match(/\+(\d+)/);
        if (match) currentNewLine = parseInt(match[1], 10) - 1;
        continue;
      }

      if (line.startsWith("+") && !line.startsWith("+++")) {
        currentNewLine++;
        const addedContent = line.substring(1);
        hunk.addedLines.push({ lineNum: currentNewLine, content: addedContent });

        const secrets = scanLineForSecrets(addedContent);
        for (const s of secrets) {
          hunk.secretAlerts.push({ lineNum: currentNewLine, rule: s });
        }
      } else if (!line.startsWith("-")) {
        currentNewLine++;
      }
    }

    if (hunk.addedLines.length > 0) {
      files.push(hunk);
    }
  }

  return files;
}

server.setRequestHandler(ListToolsRequestSchema, async () => {
  const tools: Tool[] = [
    {
      name: "get_pull_request_diff",
      description: "Fetches and parses a GitHub Pull Request diff into line-precise hunks with automated secret scanning.",
      inputSchema: {
        type: "object",
        properties: {
          owner: { type: "string", description: "Repository owner (organization or user)." },
          repo: { type: "string", description: "Repository name." },
          pull_number: { type: "number", description: "Pull request number." }
        },
        required: ["owner", "repo", "pull_number"]
      }
    },
    {
      name: "create_pull_request_review",
      description: "Submits a formal review comment or approval on a GitHub Pull Request with line-anchored comments.",
      inputSchema: {
        type: "object",
        properties: {
          owner: { type: "string", description: "Repository owner." },
          repo: { type: "string", description: "Repository name." },
          pull_number: { type: "number", description: "Pull request number." },
          commit_id: { type: "string", description: "SHA of the latest commit on the pull request." },
          body: { type: "string", description: "Overall review summary markdown." },
          event: { type: "string", enum: ["COMMENT", "APPROVE", "REQUEST_CHANGES"], default: "COMMENT" },
          comments: {
            type: "array",
            items: {
              type: "object",
              properties: {
                path: { type: "string", description: "Relative file path." },
                line: { type: "number", description: "Line number in the diff to anchor comment." },
                body: { type: "string", description: "Inline comment text." }
              },
              required: ["path", "line", "body"]
            },
            description: "Array of inline review comments."
          }
        },
        required: ["owner", "repo", "pull_number", "commit_id", "body"]
      }
    }
  ];
  return { tools };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  const owner = String(args?.owner);
  const repo = String(args?.repo);
  const pullNumber = Number(args?.pull_number);

  if (name === "get_pull_request_diff") {
    try {
      const prData = await octokit.rest.pulls.get({
        owner,
        repo,
        pull_number: pullNumber,
        mediaType: { format: "diff" }
      });

      const parsedHunks = parseUnifiedDiff(prData.data as unknown as string);

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify({
              owner,
              repo,
              pullNumber,
              totalModifiedFiles: parsedHunks.length,
              files: parsedHunks
            }, null, 2)
          }
        ]
      };
    } catch (err: any) {
      return { isError: true, content: [{ type: "text", text: `GitHub API Error: ${err.message}` }] };
    }
  }

  if (name === "create_pull_request_review") {
    const commitId = String(args?.commit_id);
    const body = String(args?.body);
    const event = String(args?.event || "COMMENT");
    const comments = Array.isArray(args?.comments) ? args.comments : [];

    try {
      const response = await octokit.rest.pulls.createReview({
        owner,
        repo,
        pull_number: pullNumber,
        commit_id: commitId,
        body,
        event: event as any,
        comments: comments.map((c: any) => ({
          path: c.path,
          line: c.line,
          body: c.body
        }))
      });

      return {
        content: [
          {
            type: "text",
            text: `Successfully submitted pull request review. Review ID: ${response.data.id}, Status: ${response.data.state}`
          }
        ]
      };
    } catch (err: any) {
      return { isError: true, content: [{ type: "text", text: `GitHub Review Submission Error: ${err.message}` }] };
    }
  }

  throw new Error(`Tool ${name} not found`);
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("GitHub PR Review MCP Server initialized.");
}

main().catch(console.error);
