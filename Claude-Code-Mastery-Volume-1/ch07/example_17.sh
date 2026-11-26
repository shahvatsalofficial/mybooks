git worktree add /tmp/worktrees/repo_checkout_042 -b security/http-client-v2
   ```
2. Executed the AST codemod script to transform all call sites.
3. Updated `package.json` to pin `@enterprise/http-client` to `^2.0.0`.
4. Invoked the repository’s native compiler:
   ```bash
   npm install && npm run build
   ```
5. If the compiler encountered an edge case that the deterministic codemod could not resolve—such as a custom monkey-patched wrapper or dynamic reflection—the worker passed the exact compiler error diagnostic to an interactive instance of Claude Code:
   ```bash
   claude --fix-compiler-errors --file=src/legacy/custom_wrapper.ts
   ```
   Claude inspected the TypeScript diagnostic, applied the necessary domain-specific adjustments, and re-ran the build until `tsc --noEmit` exited with status code `0`.

#### Step 3: Automated PR Dispatch & CI Verification
Once the repository compiled cleanly and passed 100% of its native unit and integration test suites, the worker committed the changes using a standardized enterprise commit template:
