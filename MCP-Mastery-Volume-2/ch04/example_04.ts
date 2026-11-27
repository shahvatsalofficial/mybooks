/**
 * Enterprise GraphQL MCP Bridge with Depth Limiter & Dynamic Query Stitching
 * Runtime: Node.js (v20+) with TypeScript & @modelcontextprotocol/sdk
 * Author: Vatsal Shah | Vatsal Shah
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';
import { parse, visit, DocumentNode } from 'graphql';

class GraphQlDepthLimiter {
  /**
   * Traverses GraphQL AST and calculates maximum selection nesting depth.
   */
  public static calculateQueryDepth(ast: DocumentNode): number {
    let maxDepth = 0;
    let currentDepth = 0;

    visit(ast, {
      Field: {
        enter() {
          currentDepth++;
          if (currentDepth > maxDepth) maxDepth = currentDepth;
        },
        leave() {
          currentDepth--;
        }
      }
    });

    return maxDepth;
  }
}

const GRAPHQL_ENDPOINT = process.env.GRAPHQL_ENDPOINT || 'https://graphql.internal.enterprise.com/v1';
const MAX_PERMITTED_DEPTH = 4;

const mcp = new McpServer({
  name: 'enterprise-graphql-bridge',
  version: '2.0.0'
});

// Register Type-Safe GraphQL Query Execution Tool
mcp.tool(
  'execute_graphql_query',
  'Execute validated GraphQL query against enterprise data graph with depth limiting',
  {
    query: z.string().describe('Standard GraphQL query string'),
    variables: z.record(z.any()).optional().describe('Optional query variable bindings')
  },
  async ({ query, variables }) => {
    // 1. Parse and Validate Query AST
    let documentAst: DocumentNode;
    try {
      documentAst = parse(query);
    } catch (parseErr: any) {
      return {
        isError: true,
        content: [{ type: 'text', text: `GraphQL Syntax Error: ${parseErr.message}` }]
      };
    }

    // 2. Enforce Query Depth Ceiling
    const depth = GraphQlDepthLimiter.calculateQueryDepth(documentAst);
    if (depth > MAX_PERMITTED_DEPTH) {
      return {
        isError: true,
        content: [
          {
            type: 'text',
            text: `Security Violation: Query depth of ${depth} exceeds maximum permitted depth (${MAX_PERMITTED_DEPTH}). Circular loops are prohibited.`
          }
        ]
      };
    }

    // 3. Dispatch to Upstream GraphQL Gateway
    try {
      const response = await fetch(GRAPHQL_ENDPOINT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${process.env.INTERNAL_API_KEY}`
        },
        body: JSON.stringify({ query, variables: variables || {} })
      });

      if (!response.ok) {
        return {
          isError: true,
          content: [{ type: 'text', text: `Upstream HTTP ${response.status}: ${await response.text()}` }]
        };
      }

      const result = await response.json();
      return {
        content: [{ type: 'text', text: JSON.stringify(result, null, 2) }]
      };
    } catch (netErr: any) {
      return {
        isError: true,
        content: [{ type: 'text', text: `Failed to connect to GraphQL upstream: ${netErr.message}` }]
      };
    }
  }
);

async function run() {
  const transport = new StdioServerTransport();
  await mcp.connect(transport);
  console.error('GraphQL MCP Bridge listening on stdio transport.');
}

run().catch((err) => {
  console.error('Fatal initialization error:', err);
  process.exit(1);
});
