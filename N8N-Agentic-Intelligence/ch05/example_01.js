// n8n Code Node: Reciprocal Rank Fusion
const k = 60; // Smoothing constant
const vectorResults = items[0].json.vector_results;
const keywordResults = items[0].json.keyword_results;

let scores = {};

// Score Vector Results
vectorResults.forEach((doc, index) => {
    const id = doc.metadata.id;
    scores[id] = (scores[id] || 0) + (1 / (k + (index + 1)));
});

// Score Keyword Results
keywordResults.forEach((doc, index) => {
    const id = doc.metadata.id;
    scores[id] = (scores[id] || 0) + (1 / (k + (index + 1)));
});

// Merge and Sort
const fusedResults = Object.keys(scores)
    .map(id => {
        const doc = vectorResults.find(d => d.metadata.id === id) || 
                    keywordResults.find(d => d.metadata.id === id);
        return { ...doc, rrf_score: scores[id] };
    })
    .sort((a, b) => b.rrf_score - a.rrf_score);

return fusedResults.slice(0, 5); // Return Top 5
