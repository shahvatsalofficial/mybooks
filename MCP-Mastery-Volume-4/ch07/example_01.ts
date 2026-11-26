import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool
} from "@modelcontextprotocol/sdk/types.js";
import { ChromaClient, DefaultEmbeddingFunction } from "chromadb";
import path from "path";
import os from "os";

// Initialize Chroma client connecting to local embedded or container instance
const chroma = new ChromaClient({
  path: process.env.CHROMA_SERVER_URL || "http://localhost:8000"
});

const embedder = new DefaultEmbeddingFunction();

let collection: any = null;

async function getOrCreateCollection() {
  if (!collection) {
    collection = await chroma.getOrCreateCollection({
      name: "agent_long_term_memory",
      embeddingFunction: embedder,
      metadata: { "hnsw:space": "cosine" }
    });
  }
  return collection;
}

const server = new Server(
  { name: "chroma-local-mcp", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => {
  const tools: Tool[] = [
    {
      name: "store_memory",
      description: "Stores an observation, runbook, or project decision into local vector memory with metadata tags.",
      inputSchema: {
        type: "object",
        properties: {
          id: { type: "string", description: "Unique memory identifier (e.g. 'doc-auth-architecture')." },
          content: { type: "string", description: "Text content to embed and persist." },
          category: { type: "string", description: "Category tag (e.g. 'architecture', 'incident', 'user_preference').", default: "general" }
        },
        required: ["id", "content"]
      }
    },
    {
      name: "query_memory",
      description: "Executes semantic vector similarity search across local memory to retrieve relevant past context.",
      inputSchema: {
        type: "object",
        properties: {
          query_text: { type: "string", description: "Natural language query to search." },
          top_k: { type: "number", description: "Number of nearest neighbors to return (max: 10).", default: 5 },
          category_filter: { type: "string", description: "Optional category filter." }
        },
        required: ["query_text"]
      }
    }
  ];
  return { tools };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  const col = await getOrCreateCollection();

  if (name === "store_memory") {
    const id = String(args?.id);
    const content = String(args?.content);
    const category = String(args?.category || "general");

    try {
      await col.upsert({
        ids: [id],
        documents: [content],
        metadatas: [{ category, storedAt: new Date().toISOString() }]
      });

      return {
        content: [{ type: "text", text: `Successfully embedded and stored memory '${id}' in category '${category}'.` }]
      };
    } catch (err: any) {
      return { isError: true, content: [{ type: "text", text: `Chroma Store Error: ${err.message}` }] };
    }
  }

  if (name === "query_memory") {
    const queryText = String(args?.query_text);
    const topK = Math.min(Number(args?.top_k) || 5, 10);
    const categoryFilter = args?.category_filter ? String(args.category_filter) : undefined;

    try {
      const queryParams: any = {
        queryTexts: [queryText],
        nResults: topK
      };

      if (categoryFilter) {
        queryParams.where = { category: categoryFilter };
      }

      const results = await col.query(queryParams);

      const hits: any[] = [];
      const ids = results.ids[0] || [];
      const docs = results.documents[0] || [];
      const metadatas = results.metadatas[0] || [];
      const distances = results.distances ? results.distances[0] : [];

      for (let i = 0; i < ids.length; i++) {
        hits.push({
          id: ids[i],
          cosineDistance: distances[i] !== undefined ? Number(distances[i].toFixed(4)) : null,
          similarityScore: distances[i] !== undefined ? Number((1 - distances[i]).toFixed(4)) : null,
          metadata: metadatas[i],
          contentSnippet: docs[i]
        });
      }

      return {
        content: [{ type: "text", text: JSON.stringify({ query: queryText, totalMatches: hits.length, matches: hits }, null, 2) }]
      };
    } catch (err: any) {
      return { isError: true, content: [{ type: "text", text: `Chroma Query Error: ${err.message}` }] };
    }
  }

  throw new Error(`Tool ${name} not found`);
});

async function main() {
  await getOrCreateCollection();
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Chroma Local Memory MCP Server running on stdio.");
}

main().catch(console.error);
