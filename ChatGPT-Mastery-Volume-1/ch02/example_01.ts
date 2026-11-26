/**
 * Production Dynamic Exemplar Vector Retriever (RA-ICL)
 * Integrates OpenAI text-embedding-3-small and Cosine Similarity Selection
 */

import OpenAI from 'openai';

export interface VectorExemplar {
  id: string;
  category: 'NOMINAL' | 'BOUNDARY_EDGE' | 'SECURITY_REJECTION';
  userInput: string;
  reasoning: string;
  structuredOutput: Record<string, any>;
  embedding?: number[];
}

export class DynamicExemplarRetriever {
  private openai: OpenAI;
  private exemplarPool: VectorExemplar[] = [];

  constructor(apiKey: string) {
    this.openai = new OpenAI({ apiKey });
  }

  /**
   * Registers exemplars and precomputes their normalized vector embeddings
   */
  public async initializePool(exemplars: Omit<VectorExemplar, 'embedding'>[]): Promise<void> {
    const inputs = exemplars.map(e => e.userInput);
    
    // Batch embedding generation via text-embedding-3-small (1536 dimensions)
    const response = await this.openai.embeddings.create({
      model: 'text-embedding-3-small',
      input: inputs,
      encoding_format: 'float'
    });

    this.exemplarPool = exemplars.map((ex, idx) => ({
      ...ex,
      embedding: response.data[idx].embedding
    }));
  }

  /**
   * Computes dot product of two unit-normalized embedding vectors
   */
  private computeCosineSimilarity(vecA: number[], vecB: number[]): number {
    let dotProduct = 0;
    for (let i = 0; i < vecA.length; i++) {
      dotProduct += vecA[i] * vecB[i];
    }
    return dotProduct;
  }

  /**
   * Dynamically retrieves a stratified Triad (1 Nominal, 1 Edge, 1 Rejection) matching user query
   */
  public async retrieveStratifiedTriad(userQuery: string): Promise<VectorExemplar[]> {
    // 1. Embed user query
    const queryRes = await this.openai.embeddings.create({
      model: 'text-embedding-3-small',
      input: userQuery
    });
    const queryVec = queryRes.data[0].embedding;

    // 2. Score all pool candidates
    const scored = this.exemplarPool.map(ex => ({
      exemplar: ex,
      score: this.computeCosineSimilarity(queryVec, ex.embedding!)
    }));

    // 3. Stratified selection: pick top match for each category
    const categories: ('NOMINAL' | 'BOUNDARY_EDGE' | 'SECURITY_REJECTION')[] = [
      'NOMINAL',
      'BOUNDARY_EDGE',
      'SECURITY_REJECTION'
    ];

    const selectedTriad: VectorExemplar[] = [];
    for (const cat of categories) {
      const candidates = scored
        .filter(s => s.exemplar.category === cat)
        .sort((a, b) => b.score - a.score);

      if (candidates.length > 0) {
        selectedTriad.push(candidates[0].exemplar);
      }
    }

    return selectedTriad;
  }
}
