// AST Rewriter
   sourceFile.getDescendantsOfKind(SyntaxKind.CallExpression).forEach(call => {
     if (call.getExpression().getText() === 'axios.get') {
       call.replaceWithText(`await fetchWithTimeout(${call.getArguments().map(a => a.getText()).join(', ')})`);
     }
   });
   ```
3. **Helper Injection**: The agent writes `src/utils/fetchWithTimeout.ts` into each repository.
4. **Git Verification**: The agent runs `npm test` in each repository, verifies that all tests pass, and commits the changes.

#### Verified Production Solution
