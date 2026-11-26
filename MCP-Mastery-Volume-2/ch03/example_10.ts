/**
 * Enterprise MongoDB MCP Bridge with Aggregation Guards & Schema Introspection
 * Runtime: Node.js (v20+) with TypeScript & @modelcontextprotocol/sdk
 * Author: Vatsal Shah | Opportunity4u Press
 */

import { MongoClient, ReadPreference, Db } from 'mongodb';
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';

class MongoDatabaseBridge {
  private client: MongoClient;
  private db: Db | null = null;
  private dbName: string;

  constructor(uri: string, dbName: string) {
    this.dbName = dbName;
    this.client = new MongoClient(uri, {
      readPreference: ReadPreference.SECONDARY_PREFERRED,
      maxPoolSize: 20,
      serverSelectionTimeoutMS: 5000,
      connectTimeoutMS: 5000
    });
  }

  async connect(): Promise<void> {
    await this.client.connect();
    this.db = this.client.db(this.dbName);
    console.error(`Connected to MongoDB [${this.dbName}] over Secondary-Preferred Read Replica`);
  }

  getDatabase(): Db {
    if (!this.db) throw new Error('Database bridge not initialized');
    return this.db;
  }
}

// 1. Initialize MCP Server and MongoDB Bridge
const MONGO_URI = process.env.MONGODB_URI || 'mongodb://readonly_agent:pass@localhost:27017/?replicaSet=rs0';
const DB_NAME = process.env.MONGODB_DB || 'enterprise_catalog';
const bridge = new MongoDatabaseBridge(MONGO_URI, DB_NAME);

const mcp = new McpServer({
  name: 'enterprise-mongodb-bridge',
  version: '2.0.0'
});

// 2. Query Collection Tool with Aggregation Pipeline Guard
mcp.tool(
  'query_mongo_collection',
  'Execute read-only aggregation pipeline or filtered query on MongoDB collection',
  {
    collection_name: z.string().min(1).max(64).regex(/^[a-zA-Z0-9_-]+$/),
    filter: z.record(z.any()).default({}),
    projection: z.record(z.any()).optional(),
    limit: z.number().int().min(1).max(200).default(50)
  },
  async ({ collection_name, filter, projection, limit }) => {
    try {
      const db = bridge.getDatabase();
      const collection = db.collection(collection_name);

      // Guard: Neutralize JavaScript injection operator ($where)
      const serializedFilter = JSON.stringify(filter);
      if (serializedFilter.includes('$where')) {
        return {
          isError: true,
          content: [{ type: 'text', text: 'Security Exception: $where JavaScript execution is prohibited.' }]
        };
      }

      // Execute read query with hard limit and timeout
      const cursor = collection
        .find(filter, { projection: projection || { password_hash: 0, internal_token: 0 } })
        .limit(limit)
        .maxTimeMS(3000);

      const documents = await cursor.toArray();

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              status: 'success',
              collection: collection_name,
              count: documents.length,
              documents: documents
            }, null, 2)
          }
        ]
      };
    } catch (err: any) {
      return {
        isError: true,
        content: [{ type: 'text', text: `MongoDB Query Error: ${err.message}` }]
      };
    }
  }
);

// 3. Dynamic Schema Introspection Resource
mcp.resource(
  'schema',
  'mongo://schema/{collection}',
  async (uri, { collection }) => {
    const db = bridge.getDatabase();
    const collName = String(collection);
    
    // Sample first 10 documents to infer document shape
    const sampleDocs = await db.collection(collName).find().limit(10).toArray();
    const fieldMap: Record<string, string> = {};

    for (const doc of sampleDocs) {
      for (const [key, value] of Object.entries(doc)) {
        if (!fieldMap[key]) {
          fieldMap[key] = Array.isArray(value) ? 'array' : typeof value;
        }
      }
    }

    return {
      contents: [
        {
          uri: uri.href,
          mimeType: 'application/json',
          text: JSON.stringify({
            collection: collName,
            inferred_fields: fieldMap,
            sample_size: sampleDocs.length
          }, null, 2)
        }
      ]
    };
  }
);

// Launch Stdio Transport
async function run() {
  await bridge.connect();
  const transport = new StdioServerTransport();
  await mcp.connect(transport);
}

run().catch((err) => {
  console.error('Fatal startup error in MongoDB MCP Bridge:', err);
  process.exit(1);
});
