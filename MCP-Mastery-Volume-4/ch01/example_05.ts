import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ListResourcesRequestSchema,
  ReadResourceRequestSchema
} from "@modelcontextprotocol/sdk/types.js";
import { MongoClient, ObjectId } from "mongodb";

const client = new MongoClient(process.env.MONGODB_URI || "mongodb://localhost:27017", {
  maxPoolSize: 20,
  minPoolSize: 5,
  serverSelectionTimeoutMS: 5000
});

const server = new Server(
  { name: "mongodb-mcp-server", version: "1.0.0" },
  { capabilities: { tools: {}, resources: {} } }
);

// Clean BSON serializer to prevent token inflation
function sanitizeBsonDocument(doc: any): any {
  if (!doc || typeof doc !== "object") return doc;
  if (doc instanceof ObjectId) return doc.toHexString();
  if (doc instanceof Date) return doc.toISOString();
  if (Array.isArray(doc)) return doc.map(sanitizeBsonDocument);

  const clean: Record<string, any> = {};
  for (const [key, val] of Object.entries(doc)) {
    // Exclude internal binary hashes or gigantic subtrees unless requested
    if (key.startsWith("_bin_") || key === "__v") continue;
    clean[key] = sanitizeBsonDocument(val);
  }
  return clean;
}

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "find_documents",
        description: "Executes a filtered find query on a MongoDB collection with projection and token limits.",
        inputSchema: {
          type: "object",
          properties: {
            database: { type: "string", description: "Target database name." },
            collection: { type: "string", description: "Target collection name." },
            filter: { type: "object", description: "MongoDB JSON filter expression." },
            projection: { type: "object", description: "Field projection object ({ field: 1 })." },
            limit: { type: "number", description: "Max documents to return (max: 50)." }
          },
          required: ["database", "collection"]
        }
      },
      {
        name: "aggregate_pipeline",
        description: "Executes a read-only aggregation pipeline. Modifying stages ($out, $merge) are blocked.",
        inputSchema: {
          type: "object",
          properties: {
            database: { type: "string", description: "Target database name." },
            collection: { type: "string", description: "Target collection name." },
            pipeline: { type: "array", items: { type: "object" }, description: "Aggregation pipeline stages." }
          },
          required: ["database", "collection", "pipeline"]
        }
      }
    ]
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  const dbName = String(args?.database || "admin");
  const collName = String(args?.collection || "");

  const db = client.db(dbName);
  const coll = db.collection(collName);

  if (name === "find_documents") {
    const filter = (args?.filter as Record<string, any>) || {};
    const projection = (args?.projection as Record<string, any>) || {};
    const limit = Math.min(Number(args?.limit) || 20, 50);

    const cursor = coll.find(filter, { projection }).limit(limit);
    const docs = await cursor.toArray();
    const sanitized = docs.map(sanitizeBsonDocument);

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({ count: sanitized.length, documents: sanitized }, null, 2)
        }
      ]
    };
  }

  if (name === "aggregate_pipeline") {
    const pipeline = Array.isArray(args?.pipeline) ? args.pipeline : [];

    // Enforce read-only aggregation: Block $out and $merge
    for (const stage of pipeline) {
      const stageKeys = Object.keys(stage);
      if (stageKeys.includes("$out") || stageKeys.includes("$merge")) {
        return {
          isError: true,
          content: [{ type: "text", text: "Security Violation: Aggregation stages $out and $merge are forbidden." }]
        };
      }
    }

    const cursor = coll.aggregate(pipeline, { maxTimeMS: 8000 });
    const docs = await cursor.toArray();
    const sanitized = docs.map(sanitizeBsonDocument);

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({ count: sanitized.length, results: sanitized }, null, 2)
        }
      ]
    };
  }

  throw new Error(`Tool ${name} not found`);
});

// Dynamic Resource Provider: Expose Database Schemas as Resources
server.setRequestHandler(ListResourcesRequestSchema, async () => {
  const adminDb = client.db().admin();
  const dbs = await adminDb.listDatabases();
  const resources = [];

  for (const dbInfo of dbs.databases) {
    if (["admin", "local", "config"].includes(dbInfo.name)) continue;
    resources.push({
      uri: `mcp://mongodb/databases/${dbInfo.name}/schema`,
      name: `Schema for ${dbInfo.name}`,
      mimeType: "application/json"
    });
  }

  return { resources };
});

server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  const uri = request.params.uri;
  const match = uri.match(/^mcp:\/\/mongodb\/databases\/([^/]+)\/schema$/);
  if (!match) throw new Error(`Invalid resource URI: ${uri}`);

  const targetDb = client.db(match[1]);
  const collections = await targetDb.listCollections().toArray();

  const schemaInfo: Record<string, any> = {};
  for (const c of collections) {
    // Sample first document to infer schema
    const sample = await targetDb.collection(c.name).findOne();
    schemaInfo[c.name] = {
      type: c.type,
      sampleKeys: sample ? Object.keys(sample) : []
    };
  }

  return {
    contents: [
      {
        uri,
        mimeType: "application/json",
        text: JSON.stringify(schemaInfo, null, 2)
      }
    ]
  };
});

async function main() {
  await client.connect();
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("MongoDB MCP Server initialized.");
}

main().catch((err) => {
  console.error("Fatal MongoDB startup error", err);
  process.exit(1);
});
