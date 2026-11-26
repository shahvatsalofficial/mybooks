// Two-Stage Cross-Encoder Reranking Pipeline
import { CohereClient } from "cohere-ai";

const cohere = new CohereClient({ token: process.env.COHERE_API_KEY });

export async function executeTwoStageRerank(
  query: string,
  candidateDocs: { id: string; text: string }[],
  topN: number = 5
): Promise<{ id: string; text: string; relevanceScore: number }[]> {
  if (candidateDocs.length === 0) return [];

  const response = await cohere.v2.rerank({
    model: "rerank-v3.5",
    query,
    documents: candidateDocs.map((d) => d.text),
    topN,
    returnDocuments: false
  });

  return response.results.map((r) => ({
    id: candidateDocs[r.index].id,
    text: candidateDocs[r.index].text,
    relevanceScore: Number(r.relevanceScore.toFixed(4))
  }));
}
