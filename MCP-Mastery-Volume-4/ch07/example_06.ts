export interface RankedDocument {
  id: string;
  content: string;
  denseRank?: number;
  sparseRank?: number;
  rrfScore?: number;
}

export class HybridReranker {
  // Compute RRF score: Score(d) = sum(1 / (k + rank(d)))
  static fuseRanks(
    denseHits: { id: string; content: string }[],
    sparseHits: { id: string; content: string }[],
    k: number = 60
  ): RankedDocument[] {
    const docMap = new Map<string, RankedDocument>();

    // Index dense ranks
    denseHits.forEach((hit, idx) => {
      const rank = idx + 1;
      docMap.set(hit.id, {
        id: hit.id,
        content: hit.content,
        denseRank: rank,
        rrfScore: 1 / (k + rank)
      });
    });

    // Index sparse ranks and add to RRF score
    sparseHits.forEach((hit, idx) => {
      const rank = idx + 1;
      const contribution = 1 / (k + rank);

      if (docMap.has(hit.id)) {
        const existing = docMap.get(hit.id)!;
        existing.sparseRank = rank;
        existing.rrfScore = (existing.rrfScore || 0) + contribution;
      } else {
        docMap.set(hit.id, {
          id: hit.id,
          content: hit.content,
          sparseRank: rank,
          rrfScore: contribution
        });
      }
    });

    const rankedList = Array.from(docMap.values());
    rankedList.sort((a, b) => (b.rrfScore || 0) - (a.rrfScore || 0));
    return rankedList;
  }
}
