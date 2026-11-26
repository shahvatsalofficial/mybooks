import { HfInference } from "@huggingface/inference";
import crypto from "crypto";

const hf = new HfInference(process.env.HUGGINGFACE_API_KEY);
const DEFAULT_MODEL = process.env.HF_EMBEDDING_MODEL || "BAAI/bge-large-en-v1.5";

// In-Memory LRU Cache for Embeddings: textHash -> vector
const embeddingCache = new Map<string, number[]>();

// L2 Vector Normalization: Ensures ||v|| = 1.0 so dot-product equals cosine similarity
export function l2Normalize(vector: number[]): number[] {
  const norm = Math.sqrt(vector.reduce((sum, val) => sum + val * val, 0));
  if (norm === 0) return vector;
  return vector.map((val) => val / norm);
}

export async function generateNormalizedEmbedding(text: string, model: string = DEFAULT_MODEL): Promise<number[]> {
  const hash = crypto.createHash("sha256").update(`${model}:${text}`).digest("hex");
  if (embeddingCache.has(hash)) {
    return embeddingCache.get(hash)!;
  }

  const response: any = await hf.featureExtraction({
    model,
    inputs: text
  });

  // Handle nested array response for single input
  const rawVector: number[] = Array.isArray(response[0]) ? response[0] : response;
  const normalized = l2Normalize(rawVector);

  embeddingCache.set(hash, normalized);
  if (embeddingCache.size > 1000) {
    const oldestKey = embeddingCache.keys().next().value;
    if (oldestKey) embeddingCache.delete(oldestKey);
  }

  return normalized;
}
