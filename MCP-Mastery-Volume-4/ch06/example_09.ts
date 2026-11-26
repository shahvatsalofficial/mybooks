// Reciprocal Rank Fusion Algorithm for Multi-Engine Search
export function computeReciprocalRankFusion(
  providerResultSets: { source: string; hits: { url: string; title: string; snippet: string }[] }[],
  k: number = 60
): { url: string; title: string; snippet: string; rrfScore: number; sources: string[] }[] {
  const scoreMap = new Map<string, { title: string; snippet: string; score: number; sources: Set<string> }>();

  for (const resultSet of providerResultSets) {
    resultSet.hits.forEach((hit, index) => {
      const rank = index + 1; // 1-indexed
      const contribution = 1 / (k + rank);

      if (!scoreMap.has(hit.url)) {
        scoreMap.set(hit.url, {
          title: hit.title,
          snippet: hit.snippet,
          score: contribution,
          sources: new Set([resultSet.source])
        });
      } else {
        const entry = scoreMap.get(hit.url)!;
        entry.score += contribution;
        entry.sources.add(resultSet.source);
        // Retain the longer, more informative snippet if available
        if (hit.snippet.length > entry.snippet.length) {
          entry.snippet = hit.snippet;
        }
      }
    });
  }

  // Sort descending by RRF score
  const sorted = Array.from(scoreMap.entries()).map(([url, data]) => ({
    url,
    title: data.title,
    snippet: data.snippet,
    rrfScore: Number(data.score.toFixed(5)),
    sources: Array.from(data.sources)
  }));

  sorted.sort((a, b) => b.rrfScore - a.rrfScore);
  return sorted;
}
