// n8n Function Node: Token Auditor
const tokensUsed = items[0].json.usage.total_tokens;
const model = items[0].json.model;
const costPer1k = (model === 'gpt-4o') ? 0.015 : 0.00015; // Example rates
const totalCost = (tokensUsed / 1000) * costPer1k;

return {
  json: {
    workflow_cost: totalCost,
    timestamp: new Date(),
    margin_impact: (price_charged - totalCost)
  }
};
