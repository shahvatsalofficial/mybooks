transport.onclose = () => {
       console.error(`[DISCONNECT] Session ${sessionId} closed. Releasing resources.`);
       cleanupSession(sessionId);
     };
     ```
  2. **Automated Heartbeat Sweep**: Implemented a 30-second ping interval to detect stale TCP sockets and terminate zombie sessions immediately.
</div>

<div class="postmortem-card">
  <div class="postmortem-badge">INCIDENT POST-MORTEM</div>
  
  ### Security Incident 2.2: Silent Parameter Dropping via Zod Schema Strip Default
  
  * **Incident Date**: March 19, 2026
  * **Severity**: Severity-2 (Deployment of unverified code changes to staging)
  * **Affected Systems**: GitHub Enterprise MCP Integration
  * **Root Cause**: Zod’s default behavior of stripping undeclared object properties in nested schemas
  
  #### 1. Incident Overview
  An automated CI agent used an internal GitHub MCP server to trigger blue/green canary deployments. The tool accepted a nested parameter `deploymentConfig`. A model invocation passed an optional parameter `canaryPercentage: 10`. However, the deployment script proceeded with a 100% rollout!
  
  #### 2. Root Cause Analysis
  The server author defined the schema as:
  ```typescript
  const DeploymentConfigSchema = z.object({
    environment: z.string()
  });
  ```
  By default, Zod objects operate in `.strip()` mode, silently discarding any properties not explicitly enumerated in the schema. Because `canaryPercentage` was omitted from the schema definition, Zod stripped it from the arguments object before passing it to the handler. The handler received only `{ environment: "staging" }`, defaulting to a full 100% rollout.
  
  #### 3. Corrective Actions & Architectural Remediation
  1. **Standardize on `.strict()` for Tool Schemas**: Configured all enterprise tool parameter schemas with `z.object({...}).strict()`, causing Zod to reject any unexpected parameters with an explicit error rather than silently stripping them.
</div>

<div class="postmortem-card">
  <div class="postmortem-badge">INCIDENT POST-MORTEM</div>
  
  ### Security Incident 2.3: ReDoS (Regular Expression Denial of Service) in Parameter Validation
  
  * **Incident Date**: April 8, 2026
  * **Severity**: Severity-2 (Complete CPU freeze of terminal developer agent)
  * **Affected Systems**: Local File Search MCP Server
  * **Root Cause**: Catastrophic backtracking in poorly constructed regular expression inside Zod schema refinement
  
  #### 1. Incident Overview
  A developer created a file-filtering tool accepting a `globPattern` argument, validated using a naive custom regex: `/^([a-zA-Z0-9_]+)*\.[a-z]+$/`. During a complex refactoring session, Claude Code generated a speculative pattern containing 45 repeated underscores followed by an exclamation point. The server’s Node.js event loop immediately spiked to 100% CPU on a single core and froze indefinitely.
  
  #### 2. Root Cause Analysis
  V8’s Irregexp engine suffered catastrophic polynomial backtracking. Because Node.js is single-threaded, the synchronous regex computation blocked the event loop, preventing any incoming or outgoing JSON-RPC messages from being processed.
  
  #### 3. Corrective Actions & Architectural Remediation
  1. **Enforce Linear-Time Regex Engines**: Migrated all complex string validation to Google’s `re2` engine (`re2` npm package), which guarantees $\mathcal{O}(N)$ execution time regardless of input size.
  2. **Worker Thread Offloading**: Offloaded CPU-heavy AST traversals and regex matching into Node.js `worker_threads` to keep the main event loop responsive.
</div>

## 9. Comparison Decision Matrix

The following comprehensive decision matrix contrasts the three primary architectural patterns for building TypeScript MCP servers:

| Architectural Dimension | High-Level `McpServer` | Low-Level `Server` Primitive | Custom In-House Framework |
| :--- | :--- | :--- | :--- |
| **Development Velocity** | Extremely Fast (Fluent API) | Medium (High boilerplate) | Slow (High maintenance) |
| **Type Safety & Validation** | Native Zod with auto JSON Schema | Manual validation required | Custom validation stubs |
| **Dynamic Resource Templates**| Built-in (`ResourceTemplate`) | Manual URI regex parsing | Custom router required |
| **Maintenance Burden** | Minimal (Standard SDK updates) | Low | High |
| **Custom Middleware Support** | Standard | High (Full packet intercept) | Total Control |
| **Recommended For...** | 95% of enterprise production tools | Bespoke protocol proxies & gateways | Niche embedded environments |

---

## 10. Certification Note & Industry Practice Tips

### 10.1 Architect Guidelines & Defense-in-Depth Rules

> ### 💡 Anthropic Certified MCP Developer Practice Tip
> 
> When packaging and distributing TypeScript MCP servers:
> 1. **Ensure the Shebang is Exact**: The very first line of your compiled JavaScript entry file MUST be `#!/usr/bin/env node`. Without this line, executing the server via `npx` on Unix/Linux systems will fail with `Exec format error`.
> 2. **Set File Permissions**: Verify that your build pipeline assigns execute permissions (`chmod +x dist/index.js`) prior to `npm publish`.
> 3. **Avoid Interactive Prompts**: Never use interactive terminal prompt libraries (like `inquirer` or `prompts`) inside an MCP server. The server’s `stdin` is dedicated exclusively to JSON-RPC traffic. Attempting to prompt the user on `stdin` will deadlock the agent.
> 4. **Quarantine `console.log`**: Override `console.log` in your server initialization to redirect to `console.error` as an insurance policy against errant third-party library loggers.

### 10.2 Comprehensive Production Hardening Checklist for TypeScript MCP Servers
Enterprise platform engineering groups must audit all custom TypeScript servers against this 15-point checklist before certification:

1. **Shebang Header**: Does the entrypoint file begin with `#!/usr/bin/env node` on line 1?
2. **Execute Permissions**: Has `chmod +x` been committed to the repository for the binary script?
3. **Strict Stderr Isolation**: Are all internal loggers explicitly configured to output to `stderr`?
4. **Zod `.strict()` Configuration**: Do all tool input schemas enforce strict property filtering to catch hallucinations?
5. **Semantic Property Descriptions**: Does every single parameter include a comprehensive `.describe()` string?
6. **Explicit Enum Constraining**: Are multi-choice string options restricted via `z.enum()` rather than open strings?
7. **Read-Only Transaction Guardrails**: Do analytical database tools wrap queries in explicit read-only transactions?
8. **Statement Execution Timeouts**: Do SQL tools enforce strict server-side timeouts (`statement_timeout = '10000'`)?
9. **Row Count Pagination Caps**: Do resource handlers enforce hard ceiling limits (maximum 1,000 items)?
10. **SSE Session Eviction**: Are disconnected SSE client sessions evicted from memory maps immediately via `transport.onclose`?
11. **Linear-Time Regex Validation**: Are untrusted string filters evaluated using Re2 or timeout-protected matchers?
12. **Hermetic Dependency Bundling**: Does the build pipeline compile dependencies into a clean `dist/` bundle via `tsup`?
13. **Graceful Signal Handling**: Does the process intercept `SIGINT` and `SIGTERM` to cleanly close connection pools?
14. **Idempotency Token Ingestion**: Do destructive operational tools accept deduplication keys?
15. **AST Verification**: Are code refactoring tools grounded in AST validation rather than speculative string replaces?

### 10.3 Anthropic Certification Scenario Drills for TypeScript Developers

#### Scenario A: The Runaway Database Query
* **Problem**: A developer runs Claude Code to optimize a database index. The model generates a query joining four multi-million row tables without an index, consuming 100% database CPU and hanging the terminal agent.
* **Architectural Remedy**: Implement `statement_timeout` inside the MCP server’s connection checkout pipeline. When PostgreSQL aborts the query after 5 seconds, the server catches the timeout error and returns `isError: true` with the message: `"Query exceeded 5,000ms timeout ceiling. Please inspect query plan using EXPLAIN ANALYZE before executing full scan."` This allows Claude Code to diagnose the missing index autonomously.

#### Scenario B: The Accidental Secret Leak
* **Problem**: A developer configures an MCP server connecting to an internal GitHub enterprise instance. When an API call fails with 401 Unauthorized, the server returns the raw Axios error object, which includes the `Authorization: Bearer ghp_secret...` header in the response payload.
* **Architectural Remedy**: Implement an error sanitization middleware that scrubs any string matching common token patterns (`ghp_`, `sk-ant-`, `AKIA`) before embedding error text into JSON-RPC content blocks.

#### Scenario C: The Deadlocked Sub-Process Worker Pool
* **Problem**: An enterprise AST analyzer MCP server spawns background Node.js `worker_threads` to parse heavy files. When a worker thread encounters an uncaught exception, it terminates without sending an IPC message back to the main thread. The tool call promise remains unresolved, hanging Claude Code indefinitely.
* **Architectural Remedy**: Wrap all background worker invocations with an explicit `Promise.race([workerPromise, timeoutPromise(15000)])`. Attach `worker.on("error")` and `worker.on("exit")` handlers that reject the tool call with an actionable diagnostic message if the thread exits unexpectedly.

#### Scenario D: Cross-Origin Resource Sharing (CORS) Rejection in Web MCP Clients
* **Problem**: An enterprise builds a web-based agent interface connecting to a remote SSE MCP server running on a separate internal domain. The browser blocks incoming SSE streams with a CORS violation error.
* **Architectural Remedy**: Configure the Express/Fastify gateway to emit explicit CORS headers: `Access-Control-Allow-Origin: https://agent.corp.internal`, `Access-Control-Allow-Methods: GET, POST, OPTIONS`, and `Access-Control-Allow-Headers: Content-Type, Authorization, Last-Event-ID`. Handle HTTP `OPTIONS` pre-flight checks with a 204 No Content status.

#### Scenario E: The Inadvertent stdout Contamination via NPM Package Update
* **Problem**: An MCP server author updates an analytics package dependency. The new minor version logs an ASCII banner (`"Acme Analytics Engine v3.2 Initialized!"`) to `process.stdout` during module import, crashing the client with `SyntaxError: Unexpected token 'A'`.
* **Architectural Remedy**: Implement pre-import standard stream hijacking at the very top of `src/index.ts`:
