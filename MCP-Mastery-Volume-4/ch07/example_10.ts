async function queryWithStrictThreshold(query: string, threshold: number = 0.75) {
  const col = await getOrCreateCollection();
  const res = await col.query({ queryTexts: [query], nResults: 10 });
  const hits: any[] = [];

  const docs = res.documents[0] || [];
  const distances = res.distances ? res.distances[0] : [];

  for (let i = 0; i < docs.length; i++) {
    const similarity = 1 - (distances[i] || 0);
    if (similarity >= threshold) {
      hits.push({ content: docs[i], similarity: Number(similarity.toFixed(4)) });
    }
  }
  return hits;
}
