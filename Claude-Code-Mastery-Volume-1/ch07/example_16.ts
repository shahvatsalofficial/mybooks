// Preserving Trivia During AST Node Mutation
function replaceWithPreservedTrivia(oldNode: Node, newNodeText: string): void {
  const leadingTrivia = oldNode.getLeadingCommentRanges().map(r => r.getText()).join('\n');
  const trailingTrivia = oldNode.getTrailingCommentRanges().map(r => r.getText()).join('\n');
  
  oldNode.replaceWithText(`${leadingTrivia}\n${newNodeText}\n${trailingTrivia}`);
}
