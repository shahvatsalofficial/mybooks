import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import { LinearClient } from "@linear/sdk";

const linear = new LinearClient({
  apiKey: process.env.LINEAR_API_KEY
});

const mcpServer = new Server(
  { name: "linear-mcp-server", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

mcpServer.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "linear_search_issues",
        description: "Searches Linear issues by query text, team key, or cycle state with compact field projection.",
        inputSchema: {
          type: "object",
          properties: {
            query: { type: "string", description: "Search text query." },
            team_key: { type: "string", description: "Team identifier (e.g. 'ENG', 'INFRA')." },
            limit: { type: "number", description: "Maximum issues to return (max: 25).", default: 10 }
          },
          required: ["query"]
        }
      },
      {
        name: "linear_create_issue",
        description: "Creates a new issue in Linear with title, description markdown, and priority.",
        inputSchema: {
          type: "object",
          properties: {
            team_key: { type: "string", description: "Target team key (e.g. 'ENG')." },
            title: { type: "string", description: "Issue title." },
            description: { type: "string", description: "Detailed issue description in markdown." },
            priority: { type: "number", enum: [0, 1, 2, 3, 4], description: "Priority: 0=None, 1=Urgent, 2=High, 3=Medium, 4=Low." }
          },
          required: ["team_key", "title"]
        }
      }
    ]
  };
});

mcpServer.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  if (name === "linear_search_issues") {
    const query = String(args?.query);
    const limit = Math.min(Number(args?.limit) || 10, 25);

    try {
      const issues = await linear.issues({
        filter: {
          searchableContent: { containsIgnoreCase: query }
        },
        first: limit
      });

      const cleanIssues = await Promise.all(
        issues.nodes.map(async (i) => {
          const state = await i.state;
          const assignee = await i.assignee;
          return {
            identifier: i.identifier,
            title: i.title,
            priority: i.priorityLabel,
            state: state?.name || "Unknown",
            assignee: assignee?.name || "Unassigned",
            url: i.url
          };
        })
      );

      return {
        content: [{ type: "text", text: JSON.stringify(cleanIssues, null, 2) }]
      };
    } catch (err: any) {
      return { isError: true, content: [{ type: "text", text: `Linear API Error: ${err.message}` }] };
    }
  }

  if (name === "linear_create_issue") {
    const teamKey = String(args?.team_key);
    const title = String(args?.title);
    const description = String(args?.description || "");
    const priority = Number(args?.priority || 0);

    try {
      const teams = await linear.teams({ filter: { key: { eq: teamKey } } });
      const team = teams.nodes[0];
      if (!team) {
        return { isError: true, content: [{ type: "text", text: `Team '${teamKey}' not found.` }] };
      }

      const issuePayload = await linear.createIssue({
        teamId: team.id,
        title,
        description,
        priority
      });

      const issue = await issuePayload.issue;
      return {
        content: [{ type: "text", text: `Successfully created Linear issue ${issue?.identifier}: ${issue?.url}` }]
      };
    } catch (err: any) {
      return { isError: true, content: [{ type: "text", text: `Linear Create Issue Error: ${err.message}` }] };
    }
  }

  throw new Error(`Tool ${name} not found`);
});

async function run() {
  const transport = new StdioServerTransport();
  await mcpServer.connect(transport);
  console.error("Linear MCP Server initialized on stdio.");
}

run().catch(console.error);
