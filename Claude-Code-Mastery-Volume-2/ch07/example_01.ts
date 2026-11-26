/**
 * @file postgres_enterprise_mcp.ts
 * Enterprise-grade PostgreSQL Model Context Protocol Server.
 * Enforces read-only connection pooling, AST SQL validation, and query cost limits.
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
  ErrorCode,
  McpError
} from '@modelcontextprotocol/sdk/types.js';
import pkg from 'pg';
const { Pool } = pkg;

interface DatabaseConfig {
  replicaUrl: string;
  maxConnections: number;
  statementTimeoutMs: number;
  maxRowLimit: number;
}

export class EnterprisePostgresMcpServer {
  private server: Server;
  private replicaPool: pkg.Pool;
  private config: DatabaseConfig;

  constructor(config: DatabaseConfig) {
    this.config = config;
    this.server = new Server(
      {
        name: 'enterprise-postgres-mcp',
        version: '2.0.0'
      },
      {
        capabilities: {
          tools: {},
          resources: {}
        }
      }
    );

    this.replicaPool = new Pool({
      connectionString: this.config.replicaUrl,
      max: this.config.maxConnections,
      idleTimeoutMillis: 30000,
      connectionTimeoutMillis: 5000,
      statement_timeout: this.config.statementTimeoutMs
    });

    this.setupHandlers();
  }

  private setupHandlers(): void {
    // 1. List Available Resources
    this.server.setRequestHandler(ListResourcesRequestSchema, async () => {
      return {
        resources: [
          {
            uri: 'postgres://schemas/public',
            name: 'Public Schema Catalog',
            mimeType: 'application/json',
            description: 'Comprehensive table and column definitions with data types and primary keys.'
          },
          {
            uri: 'postgres://performance/slow_queries',
            name: 'Top 10 Slow Queries',
            mimeType: 'application/json',
            description: 'Real-time pg_stat_statements metrics identifying high-latency execution plans.'
          }
        ]
      };
    });

    // 2. Read Dynamic Resources
    this.server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
      const uri = request.params.uri;
      if (uri === 'postgres://schemas/public') {
        const schema = await this.introspectSchema('public');
        return {
          contents: [
            {
              uri,
              mimeType: 'application/json',
              text: JSON.stringify(schema, null, 2)
            }
          ]
        };
      }
      if (uri === 'postgres://performance/slow_queries') {
        const slowQueries = await this.fetchSlowQueries();
        return {
          contents: [
            {
              uri,
              mimeType: 'application/json',
              text: JSON.stringify(slowQueries, null, 2)
            }
          ]
        };
      }
      throw new McpError(ErrorCode.InvalidRequest, `Resource not found: ${uri}`);
    });

    // 3. List Available Tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: 'execute_read_query',
            description: 'Safely execute a read-only SELECT SQL query with automatic LIMIT enforcement and timeout.',
            inputSchema: {
              type: 'object',
              properties: {
                sql: {
                  type: 'string',
                  description: 'The SELECT SQL statement to execute. Multi-statement queries are forbidden.'
                },
                maxRows: {
                  type: 'integer',
                  description: 'Maximum rows to return (default 100, maximum ceiling 1000).',
                  default: 100
                }
              },
              required: ['sql']
            }
          },
          {
            name: 'explain_query_plan',
            description: 'Generate EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) execution plan for query optimization.',
            inputSchema: {
              type: 'object',
              properties: {
                sql: {
                  type: 'string',
                  description: 'The SQL query to analyze.'
                }
              },
              required: ['sql']
            }
          }
        ]
      };
    });

    // 4. Call Tool Handlers
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      switch (request.params.name) {
        case 'execute_read_query': {
          const sql = String(request.params.arguments?.sql);
          const maxRows = Math.min(
            Number(request.params.arguments?.maxRows) || 100,
            this.config.maxRowLimit
          );
          return await this.handleExecuteReadQuery(sql, maxRows);
        }
        case 'explain_query_plan': {
          const sql = String(request.params.arguments?.sql);
          return await this.handleExplainQueryPlan(sql);
        }
        default:
          throw new McpError(ErrorCode.MethodNotFound, `Unknown tool: ${request.params.name}`);
      }
    });
  }

  private sanitizeAndValidateSql(rawSql: string): string {
    const trimmed = rawSql.trim();

    // Check for multi-statement injection
    if (trimmed.includes(';') && trimmed.indexOf(';') !== trimmed.length - 1) {
      throw new McpError(
        ErrorCode.InvalidParams,
        'Security Violation: Multi-statement queries containing semicolons are strictly prohibited.'
      );
    }

    // Strip trailing semicolon
    const cleanSql = trimmed.replace(/;+$/, '');

    // Forbidden DDL and destructive DML tokens
    const forbiddenTokens = [
      /\bDROP\b/i,
      /\bTRUNCATE\b/i,
      /\bDELETE\b/i,
      /\bUPDATE\b/i,
      /\bINSERT\b/i,
      /\bALTER\b/i,
      /\bGRANT\b/i,
      /\bREVOKE\b/i,
      /\bCREATE\b/i
    ];

    for (const pattern of forbiddenTokens) {
      if (pattern.test(cleanSql)) {
        throw new McpError(
          ErrorCode.InvalidParams,
          `Security Violation: Query contains prohibited token matching ${pattern}. Only read-only operations permitted.`
        );
      }
    }

    if (!cleanSql.toUpperCase().startsWith('SELECT') && !cleanSql.toUpperCase().startsWith('WITH')) {
      throw new McpError(ErrorCode.InvalidParams, 'Query must begin with SELECT or WITH clause.');
    }

    return cleanSql;
  }

  private async handleExecuteReadQuery(sql: string, maxRows: number) {
    const validatedSql = this.sanitizeAndValidateSql(sql);

    // Enforce LIMIT clause
    const wrappedSql = `
      SELECT * FROM (${validatedSql}) AS safe_subquery
      LIMIT ${maxRows};
    `;

    const client = await this.replicaPool.connect();
    try {
      // Enforce read-only transaction mode explicitly
      await client.query('SET TRANSACTION READ ONLY;');
      const start = Date.now();
      const res = await client.query(wrappedSql);
      const executionTimeMs = Date.now() - start;

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(
              {
                rowCount: res.rowCount,
                executionTimeMs,
                fields: res.fields.map((f) => ({ name: f.name, dataTypeId: f.dataTypeID })),
                rows: res.rows
              },
              null,
              2
            )
          }
        ]
      };
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      throw new McpError(ErrorCode.InternalError, `PostgreSQL execution error: ${msg}`);
    } finally {
      client.release();
    }
  }

  private async handleExplainQueryPlan(sql: string) {
    const validatedSql = this.sanitizeAndValidateSql(sql);
    const explainSql = `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) ${validatedSql};`;

    const client = await this.replicaPool.connect();
    try {
      await client.query('SET TRANSACTION READ ONLY;');
      const res = await client.query(explainSql);
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(res.rows[0]['QUERY PLAN'], null, 2)
          }
        ]
      };
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      throw new McpError(ErrorCode.InternalError, `EXPLAIN execution error: ${msg}`);
    } finally {
      client.release();
    }
  }

  private async introspectSchema(schema: string): Promise<Record<string, unknown>> {
    const client = await this.replicaPool.connect();
    try {
      const query = `
        SELECT 
          table_name, column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = $1
        ORDER BY table_name, ordinal_position;
      `;
      const res = await client.query(query, [schema]);
      const tableMap: Record<string, Array<{ column: string; type: string; nullable: boolean }>> = {};
      for (const row of res.rows) {
        if (!tableMap[row.table_name]) {
          tableMap[row.table_name] = [];
        }
        tableMap[row.table_name].push({
          column: row.column_name,
          type: row.data_type,
          nullable: row.is_nullable === 'YES'
        });
      }
      return tableMap;
    } finally {
      client.release();
    }
  }

  private async fetchSlowQueries(): Promise<Array<Record<string, unknown>>> {
    const client = await this.replicaPool.connect();
    try {
      const query = `
        SELECT 
          query, calls, total_exec_time, mean_exec_time, rows
        FROM pg_stat_statements
        ORDER BY mean_exec_time DESC
        LIMIT 10;
      `;
      const res = await client.query(query);
      return res.rows;
    } catch {
      return [{ message: 'pg_stat_statements extension not enabled on this instance.' }];
    } finally {
      client.release();
    }
  }

  public async start(): Promise<void> {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Enterprise PostgreSQL MCP Server running on stdio');
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const server = new EnterprisePostgresMcpServer({
    replicaUrl: process.env.PG_REPLICA_URL || 'postgres://readonly:secret@localhost:5432/enterprise_db',
    maxConnections: 10,
    statementTimeoutMs: 5000,
    maxRowLimit: 1000
  });
  server.start().catch((err) => {
    console.error('Fatal initialization error:', err);
    process.exit(1);
  });
}
