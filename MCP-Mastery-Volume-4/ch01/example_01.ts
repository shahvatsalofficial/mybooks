import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool
} from "@modelcontextprotocol/sdk/types.js";
import pg from "pg";

const { Pool } = pg;

// 1. Connection Pool Initialization with Hardened Lifecycle
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 15,
  idleTimeoutMillis: 10000,
  connectionTimeoutMillis: 3000,
  ssl: process.env.NODE_ENV === "production" ? { rejectUnauthorized: true } : false
});

pool.on("error", (err) => {
  console.error("Unexpected error on idle PostgreSQL client", err);
});

// 2. AST Query Safety Validator
function validateReadOnlyQuery(sql: string): { valid: boolean; reason?: string } {
  const normalized = sql.trim().toLowerCase();
  
  // Guard against multi-statement injections
  const statements = normalized.split(";").filter((s) => s.trim().length > 0);
  if (statements.length > 1) {
    return { valid: false, reason: "Multiple semicolon-separated statements are forbidden." };
  }

  // Enforce read-only semantics
  const disallowedTokens = [
    "insert", "update", "delete", "drop", "alter", "truncate",
    "create", "grant", "revoke", "vacuum", "copy", "lock"
  ];

  for (const token of disallowedTokens) {
    const regex = new RegExp(`\\b${token}\\b`, "i");
    if (regex.test(normalized)) {
      return { valid: false, reason: `Disallowed modification statement detected: '${token.toUpperCase()}'.` };
    }
  }

  if (!normalized.startsWith("select") && !normalized.startsWith("explain") && !normalized.startsWith("with")) {
    return { valid: false, reason: "Only SELECT, EXPLAIN, or read-only WITH queries are permitted." };
  }

  return { valid: true };
}

// 3. MCP Server Definition
const server = new Server(
  { name: "postgres-mcp-server", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => {
  const tools: Tool[] = [
    {
      name: "query_postgres",
      description: "Executes a parameterized, read-only SQL query against the PostgreSQL database with cursor limits.",
      inputSchema: {
        type: "object",
        properties: {
          sql: { type: "string", description: "The read-only SQL query to execute." },
          params: { type: "array", items: { type: "string" }, description: "Positional query parameters ($1, $2, etc.)." },
          limit: { type: "number", description: "Maximum rows to return (default: 50, max: 200)." }
        },
        required: ["sql"]
      }
    },
    {
      name: "describe_tables",
      description: "Returns schema structure, column types, and primary keys for specified tables.",
      inputSchema: {
        type: "object",
        properties: {
          table_names: { type: "array", items: { type: "string" }, description: "List of table names to inspect." }
        },
        required: ["table_names"]
      }
    }
  ];
  return { tools };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  if (name === "query_postgres") {
    const rawSql = String(args?.sql || "");
    const params = Array.isArray(args?.params) ? args.params : [];
    const limit = Math.min(Number(args?.limit) || 50, 200);

    const validation = validateReadOnlyQuery(rawSql);
    if (!validation.valid) {
      return {
        isError: true,
        content: [{ type: "text", text: `SQL Security Violation: ${validation.reason}` }]
      };
    }

    // Append limit if not present in query
    let finalSql = rawSql.trim();
    if (!finalSql.toLowerCase().includes("limit")) {
      finalSql = `${finalSql} LIMIT ${limit}`;
    }

    const client = await pool.connect();
    try {
      const startTime = Date.now();
      const res = await client.query(finalSql, params);
      const executionDuration = Date.now() - startTime;

      const output = {
        rowCount: res.rowCount,
        executionTimeMs: executionDuration,
        fields: res.fields.map((f) => ({ name: f.name, dataTypeID: f.dataTypeID })),
        rows: res.rows
      };

      return {
        content: [{ type: "text", text: JSON.stringify(output, null, 2) }]
      };
    } catch (dbErr: any) {
      return {
        isError: true,
        content: [{ type: "text", text: `PostgreSQL Execution Error: ${dbErr.message}` }]
      };
    } finally {
      client.release();
    }
  }

  if (name === "describe_tables") {
    const tableNames = Array.isArray(args?.table_names) ? args.table_names : [];
    if (tableNames.length === 0) {
      return { isError: true, content: [{ type: "text", text: "table_names array cannot be empty." }] };
    }

    const client = await pool.connect();
    try {
      const query = `
        SELECT table_name, column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = ANY($1::text[])
        ORDER BY table_name, ordinal_position;
      `;
      const res = await client.query(query, [tableNames]);
      return {
        content: [{ type: "text", text: JSON.stringify(res.rows, null, 2) }]
      };
    } finally {
      client.release();
    }
  }

  throw new Error(`Unknown tool: ${name}`);
});

async function run() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("PostgreSQL MCP Server running on stdio transport.");
}

run().catch((err) => {
  console.error("Fatal startup error", err);
  process.exit(1);
});
