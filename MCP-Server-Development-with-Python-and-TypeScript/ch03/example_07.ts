/**
 * recipe_3_2_database_templates.ts
 * Enterprise TypeScript MCP Resource Server exposing dynamic SQL table templates.
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
  ListResourceTemplatesRequestSchema,
  ErrorCode,
  McpError,
} from '@modelcontextprotocol/sdk/types.js';

// Mock in-memory database catalog
const DATABASE_CATALOG: Record<string, Record<string, string>> = {
  production: {
    users: 'CREATE TABLE users (id SERIAL PRIMARY KEY, email VARCHAR(255) UNIQUE, created_at TIMESTAMP);',
    orders: 'CREATE TABLE orders (id SERIAL PRIMARY KEY, user_id INT REFERENCES users(id), amount NUMERIC(10,2));',
  },
  analytics: {
    daily_revenue: 'CREATE TABLE daily_revenue (report_date DATE PRIMARY KEY, total_usd NUMERIC(14,2));',
  },
};

const server = new Server(
  {
    name: 'database-resource-server',
    version: '1.0.0',
  },
  {
    capabilities: {
      resources: {
        subscribe: true,
        listChanged: true,
      },
    },
  }
);

// 1. Advertise Dynamic RFC 6570 Resource Templates
server.setRequestHandler(ListResourceTemplatesRequestSchema, async () => {
  return {
    resourceTemplates: [
      {
        uriTemplate: 'db://{schema}/{table}/schema',
        name: 'Database Table DDL Schema',
        description: 'Exposes relational DDL schema definitions for tables across environments.',
        mimeType: 'text/x-sql',
      },
    ],
  };
});

// 2. Advertise Concrete Static Resources Currently Available
server.setRequestHandler(ListResourcesRequestSchema, async () => {
  const resources = [];
  for (const [schema, tables] of Object.entries(DATABASE_CATALOG)) {
    for (const table of Object.keys(tables)) {
      resources.push({
        uri: `db://${schema}/${table}/schema`,
        name: `${schema}.${table} DDL`,
        description: `Relational schema definition for ${schema}.${table}`,
        mimeType: 'text/x-sql',
      });
    }
  }
  return { resources };
});

// 3. Fulfill resources/read with URI Template Pattern Matching
server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  const { uri } = request.params;
  
  // RFC 6570 Pattern Matcher: db://{schema}/{table}/schema
  const pattern = /^db:\/\/([a-zA-Z0-9_-]+)\/([a-zA-Z0-9_-]+)\/schema$/;
  const match = uri.match(pattern);

  if (!match) {
    throw new McpError(
      ErrorCode.InvalidParams,
      `Unsupported or malformed resource URI: ${uri}. Expected format: db://{schema}/{table}/schema`
    );
  }

  const [, schema, table] = match;

  if (!DATABASE_CATALOG[schema] || !DATABASE_CATALOG[schema][table]) {
    throw new McpError(
      ErrorCode.InvalidParams,
      `Table '${schema}.${table}' does not exist in the catalog.`
    );
  }

  const ddl = DATABASE_CATALOG[schema][table];

  return {
    contents: [
      {
        uri,
        mimeType: 'text/x-sql',
        text: ddl,
      },
    ],
  };
});

// Bootstrap Stdio Transport
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('[DB Resource Server] Running on stdio transport.');
}

main().catch((err) => {
  console.error('[Fatal Error]', err);
  process.exit(1);
});
