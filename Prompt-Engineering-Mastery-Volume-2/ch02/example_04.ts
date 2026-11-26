export interface EmbeddingVector {
  text: string;
  vector: number[];
}

export interface SemanticClusterResult {
  electedSummary: string;
  consensusShare: number;
  totalClusters: number;
  clusterDistributions: { label: string; count: number }[];
}

export class SemanticConsensusAggregator {
  private cosineSimilarity(a: number[], b: number[]): number {
    let dot = 0.0;
    let normA = 0.0;
    let normB = 0.0;
    for (let i = 0; i < a.length; i++) {
      dot += a[i] * b[i];
      normA += a[i] * a[i];
      normB += b[i] * b[i];
    }
    return dot / (Math.sqrt(normA) * Math.sqrt(normB) + 1e-9);
  }

  public aggregateClusters(
    items: EmbeddingVector[],
    similarityThreshold: number = 0.88
  ): SemanticClusterResult {
    const clusters: EmbeddingVector[][] = [];

    for (const item of items) {
      let matched = false;
      for (const cluster of clusters) {
        // Compare against cluster representative (centroid/first element)
        const sim = this.cosineSimilarity(item.vector, cluster[0].vector);
        if (sim >= similarityThreshold) {
          cluster.push(item);
          matched = true;
          break;
        }
      }
      if (!matched) {
        clusters.push([item]);
      }
    }

    // Sort clusters by size
    clusters.sort((a, b) => b.length - a.length);
    const winningCluster = clusters[0];
    const consensusShare = winningCluster.length / items.length;

    return {
      electedSummary: winningCluster[0].text,
      consensusShare: Math.round(consensusShare * 1000) / 1000,
      totalClusters: clusters.length,
      clusterDistributions: clusters.map((c, idx) => ({
        label: `Cluster_${idx + 1}`,
        count: c.length
      }))
    };
  }
}
