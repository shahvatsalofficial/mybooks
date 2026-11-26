import { Pinecone } from "@pinecone-database/pinecone";
import { QdrantClient } from "@qdrant/js-client-rest";

export class DualVectorBridge {
  private pinecone: Pinecone | null = null;
  private qdrant: QdrantClient | null = null;

  constructor() {
    if (process.env.PINECONE_API_KEY) {
      this.pinecone = new Pinecone({ apiKey: process.env.PINECONE_API_KEY });
    }
    if (process.env.QDRANT_URL) {
      this.qdrant = new QdrantClient({
        url: process.env.QDRANT_URL,
        apiKey: process.env.QDRANT_API_KEY
      });
    }
  }

  // Query Pinecone Index with Metadata Filter
  async queryPinecone(
    indexName: string,
    vector: number[],
    topK: number = 5,
    filter: Record<string, any> = {}
  ) {
    if (!this.pinecone) throw new Error("Pinecone API key not configured.");
    const index = this.pinecone.index(indexName);

    const response = await index.query({
      vector,
      topK,
      filter: Object.keys(filter).length > 0 ? filter : undefined,
      includeMetadata: true
    });

    return response.matches.map((m) => ({
      id: m.id,
      score: m.score,
      metadata: m.metadata
    }));
  }

  // Query Qdrant Collection with Payload Filter
  async queryQdrant(
    collectionName: string,
    vector: number[],
    limit: number = 5,
    mustFilters: { key: string; matchValue: string }[] = []
  ) {
    if (!this.qdrant) throw new Error("Qdrant client not configured.");

    const filterObj = mustFilters.length > 0 ? {
      must: mustFilters.map((f) => ({ key: f.key, match: { value: f.matchValue } }))
    } : undefined;

    const response = await this.qdrant.search(collectionName, {
      vector,
      limit,
      filter: filterObj,
      with_payload: true
    });

    return response.map((r) => ({
      id: r.id,
      score: r.score,
      payload: r.payload
    }));
  }
}
