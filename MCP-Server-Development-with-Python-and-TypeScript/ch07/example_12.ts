// Stdio Guard: Redirect rogue console.log calls to stderr
   console.log = (...args: any[]) => {
     process.stderr.write(`[LOG REDIRECT] ${args.join(" ")}\n`);
   };
   ```
2. **ESLint AST Rule**: Enforced `no-console: ["error", { allow: ["error", "warn"] }]` in ESLint configurations across all MCP server repositories.
3. **Automated Headless Stdio Verifier**: Added a GitHub Actions workflow that executes `node dist/index.js`, reads the first 10 emitted lines, and verifies that 100% of bytes on stdout are strictly valid JSON-RPC envelopes.

---

### Post-Mortem 07.02: The Unhandled SSE Connection Leak

| Metadata | Details |
| :--- | :--- |
| **Date** | March 4, 2026 |
| **Incident Severity** | P1 (Cloud Runtime Exhaustion) |
| **Impact** | Enterprise MCP gateway pods on AWS EKS crashed with `EMFILE: too many open files` and `MaxListenersExceededWarning`, causing rolling 502 Bad Gateway outages. |
| **Root Cause** | The Express `/sse` route handler did not register a listener on `res.on('close')`. Disconnected clients left dangling `SSEServerTransport` instances and open socket listeners in Node.js memory. |
| **Resolution Time** | 45 minutes |

#### Incident Summary

An enterprise engineering organization hosted an MCP server as a centralized cloud service using Express and `SSEServerTransport`. During the morning rush, developers launched Cursor and Claude Desktop, which connected to `https://mcp.internal.corp/sse`.

Throughout the day, developers closed and reopened their laptops, toggled VPN connections, and restarted their IDEs. Every time a client disconnected, the TCP connection was terminated by AWS load balancers.

However, the Express server implementation lacked a cleanup listener on the response object:
