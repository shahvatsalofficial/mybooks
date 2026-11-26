/**
 * Recipe 05.5: Production Coding Assistant MCP Server with Prometheus Metrics
 * Author: Vatsal Shah (Opportunity4u Press)
 * License: Apache-2.0
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';
import * as client from 'prom-client';

// Prometheus Metrics Instrumentation
const register = new client.Registry();
client.collectDefaultMetrics({ register });

const toolInvocationCounter = new client.Counter({
  name: 'mcp_tool_invocations_total',
  help: 'Total count of MCP tool calls processed',
  labelNames: ['tool_name', 'status'],
  registers: [register],
});

const toolExecutionDuration = new client.Histogram({
  name: 'mcp_tool_execution_duration_seconds',
  help: 'Execution latency of MCP tools',
  labelNames: ['tool_name'],
  buckets: [0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
  registers: [register],
});

const server = new McpServer({
  name: 'enterprise-code-assistant',
  version: '3.0.0',
});

server.tool(
  'analyze_ast_syntax',
  'Validates TypeScript AST syntax without executing code.',
  { sourceCode: z.string().min(1) },
  async ({ sourceCode }) => {
    const endTimer = toolExecutionDuration.startTimer({ tool_name: 'analyze_ast_syntax' });
    try {
      // Simulate static AST analysis
      const nodeCount = sourceCode.split('\n').length;
      toolInvocationCounter.inc({ tool_name: 'analyze_ast_syntax', status: 'SUCCESS' });
      return {
        content: [{ type: 'text', text: JSON.stringify({ valid: true, linesParsed: nodeCount }) }],
      };
    } catch (err: any) {
      toolInvocationCounter.inc({ tool_name: 'analyze_ast_syntax', status: 'ERROR' });
      return {
        isError: true,
        content: [{ type: 'text', text: `Syntax Failure: ${err.message}` }],
      };
    } finally {
      endTimer();
    }
  }
);
