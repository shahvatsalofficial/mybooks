#!/usr/bin/env node
/**
 * Enterprise Production PostgreSQL MCP Server
 * Language: TypeScript / Node.js
 * SDK: @modelcontextprotocol/sdk v1.5.0+
 */

import { McpServer, ResourceTemplate } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import pg from "pg";

const { Pool } = pg;

// 1. Initialize PostgreSQL Connection Pool
const dbPool = new Pool({
  connectionString: process.env.DATABASE_URL || "postgres://postgres:postgres@localhost:5432/enterprise_db",
  max: 10,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 5000
});

// Guard pool initialization diagnostics to stderr
dbPool.on("error", (err) => {
  console.error("[CRITICAL DB ERROR] Unhandled pool error:", err.message);
});

// 2. Instantiate MCP High-Level Server
const server = new McpServer({
  name: "enterprise-postgres-mcp",
  version: "1.0.0"
});

// Tool 1: Execute Safe Analytical SQL Queries
server.tool(
  "execute_read_query",
  "Executes a read-only SQL query against the enterprise analytical cluster. Prohibits mutations.",
  {
    query: z.string()
      .describe("The SQL SELECT query to execute. Must begin with SELECT or WITH."),
    maxRows: z.number()
      .int()
      .min(1)
      .max(1000)
      .default(100)
      .describe("Maximum number of rows to return (capped at 1,000)")
  },
  async ({ query, maxRows }) => {
    const trimmed = query.trim().toUpperCase();
    
    // Safety Barrier: Enforce read-only constraint
    const prohibitedKeywords = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "GRANT", "REVOKE"];
    for (const kw of prohibitedKeywords) {
      if (new RegExp(`\\b${kw}\\b`, "i").test(trimmed)) {
        return {
          content: [{
            type: "text",
            text: `SECURITY ERROR: Mutation keyword '${kw}' detected. Only read-only queries are permitted.`
          }],
          isError: true
        };
      }
    }

    if (!trimmed.startsWith("SELECT") && !trimmed.startsWith("WITH") && !trimmed.startsWith("EXPLAIN")) {
      return {
        content: [{
          type: "text",
          text: "VALIDATION ERROR: Query must begin with SELECT, WITH, or EXPLAIN."
        }],
        isError: true
      };
    }

    const client = await dbPool.connect();
    try {
      // Set read-only transaction mode and execution timeout
      await client.query("BEGIN TRANSACTION READ ONLY;");
      await client.query("SET LOCAL statement_timeout = '10000';"); // 10s ceiling

      const finalQuery = `SELECT * FROM (${query.replace(/;\s*$/, "")}) AS wrapped_query LIMIT ${maxRows};`;
      const startTime = Date.now();
      const result = await client.query(finalQuery);
      const durationMs = Date.now() - startTime;
      await client.query("COMMIT;");

      const responsePayload = {
        rowCount: result.rows.length,
        executionTimeMs: durationMs,
        fields: result.fields.map(f => ({ name: f.name, dataTypeId: f.dataTypeID })),
        rows: result.rows
      };

      return {
        content: [{
          type: "text",
          text: JSON.stringify(responsePayload, null, 2)
        }]
      };
    } catch (err: any) {
      await client.query("ROLLBACK;");
      console.error("[QUERY FAILURE]", err.message);
      return {
        content: [{
          type: "text",
          text: `POSTGRES EXECUTION ERROR: ${err.message}`
        }],
        isError: true
      };
    } finally {
      client.release();
    }
  }
);

// Resource 1: Dynamic Table Schema Introspection
const tableSchemaTemplate = new ResourceTemplate(
  "postgres://schema/{table_name}",
  { list: undefined }
);

server.resource(
  "table-schema-inspector",
  tableSchemaTemplate,
  {
    description: "Inspects the DDL column structure, constraints, and data types for a database table",
    mimeType: "application/json"
  },
  async (uri, { table_name }) => {
    const client = await dbPool.connect();
    try {
      const query = `
        SELECT 
          column_name, 
          data_type, 
          is_nullable, 
          column_default
        FROM information_schema.columns 
        WHERE table_name = $1 
        ORDER BY ordinal_position;
      `;
      const res = await client.query(query, [table_name]);
      
      return {
        contents: [{
          uri: uri.href,
          text: JSON.stringify(res.rows, null, 2),
          mimeType: "application/json"
        }]
      };
    } finally {
      client.release();
    }
  }
);

// 3. Connect Transport and Launch Daemon
async function startServer() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("[SERVER READY] Enterprise PostgreSQL MCP daemon listening on STDIO.");
}

startServer().catch((err) => {
  console.error("[FATAL ERROR] Server startup failed:", err);
  process.exit(1);
});
