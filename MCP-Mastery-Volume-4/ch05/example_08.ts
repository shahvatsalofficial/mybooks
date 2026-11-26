// Query Complexity Governor for Federated GraphQL
export function evaluateGraphQLComplexity(queryAst: any): { score: number; allowed: boolean; reason?: string } {
  let totalScore = 0;
  const MAX_PERMITTED_SCORE = 250;

  function traverse(node: any, multiplier: number) {
    if (!node || !node.selectionSet) return;
    for (const selection of node.selectionSet.selections) {
      if (selection.kind === "Field") {
        const fieldName = selection.name.value;
        const isList = selection.arguments?.some((arg: any) => arg.name.value === "first" || arg.name.value === "limit");
        const listLimit = isList
          ? Number(selection.arguments.find((arg: any) => arg.name.value === "first" || arg.name.value === "limit")?.value?.value || 10)
          : 1;

        const fieldCost = isList ? 5 : 1;
        totalScore += fieldCost * multiplier;

        if (selection.selectionSet) {
          traverse(selection, multiplier * listLimit);
        }
      }
    }
  }

  traverse(queryAst.definitions[0], 1);

  if (totalScore > MAX_PERMITTED_SCORE) {
    return {
      score: totalScore,
      allowed: false,
      reason: `Query complexity score (${totalScore}) exceeds enterprise ceiling (${MAX_PERMITTED_SCORE}). Reduce nested field selection or list limits.`
    };
  }

  return { score: totalScore, allowed: true };
}
