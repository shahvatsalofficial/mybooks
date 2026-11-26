// Core transformation logic in codemods/migrate_http_v2.ts
export function transformHttpCallSite(sourceFile: SourceFile): boolean {
  let mutated = false;
  
  sourceFile.getDescendantsOfKind(SyntaxKind.CallExpression).forEach(call => {
    const expression = call.getExpression();
    if (isHttpClientCall(expression)) {
      const args = call.getArguments();
      if (args.length === 2 && args[1].getKind() === SyntaxKind.FunctionExpression) {
        // Rewrite legacy callback pattern to async/await with try/catch wrapping
        rewriteCallbackToAsyncAwait(call);
        mutated = true;
      }
    }
  });

  return mutated;
}
