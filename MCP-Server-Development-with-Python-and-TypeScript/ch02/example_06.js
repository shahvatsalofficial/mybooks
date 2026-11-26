// FLAWED INGESTION CONFIGURATION:
   const proc = spawn('python', ['-m', 'mcp_indexer'], {
     stdio: ['pipe', 'pipe', 'pipe'] // stdin, stdout, stderr all piped
   });
   // The developer listened to stdout:
   proc.stdout.on('data', handleStdoutData);
   // THE FATAL MISTAKE: No listener was registered on proc.stderr!
   ```
4. On the Linux kernel version running on the Kubernetes nodes, the anonymous pipe buffer capacity for unread descriptors is exactly 65,536 bytes (64 KB).
5. As the indexing tool scanned thousands of source files, the AST library generated hundreds of verbose debug lines to `stderr`. Because the host process never attached a `.on('data')` handler to `proc.stderr`, the kernel pipe buffer gradually filled.
6. Once the 65,536th byte was reached, the Linux kernel put the child process into an uninterruptible sleep state (`S` state) waiting for buffer capacity to free up.
7. Meanwhile, the host MCP client was awaiting a JSON-RPC response from the child process on `stdout` before sending the next instruction.
8. **The Deadlock**: The server could not write to `stdout` because it was blocked trying to write to `stderr`. The client would not drain `stderr` because it was synchronously waiting for `stdout`. Both processes sat frozen in mutual deadlock.

#### Remediation and Prevention Protocols

1. **Immediate Patch**: The host process supervisor was patched to attach an active drain listener to `proc.stderr` immediately upon invocation:
   ```javascript
   proc.stderr.on('data', (chunk) => {
     logger.debug(`[Server Stderr] ${chunk.toString('utf8')}`);
   });
   ```
2. **Alternative Zero-Buffer Redirection**: Where host logging is unnecessary, configure `stdio: ['pipe', 'pipe', 'inherit']` or redirect child `stderr` directly to `/dev/null` or a rolling log file descriptor (`fs.openSync('/tmp/mcp_err.log', 'a')`).
3. **Environment Variable Enforcement**: All Python MCP subprocesses are now launched with `PYTHONUNBUFFERED=1` and `LOGLEVEL=WARNING` to minimize extraneous I/O emissions.
4. **Automated Deadlock Smoke Test**: Added a synthetic test to CI/CD pipelines that forces an MCP server to emit 1 MB of continuous `stderr` logs prior to returning a tool response. Any client wrapper that deadlocks under this condition fails the build.

---

### Post-Mortem 02.02: The 60-Second AWS ALB Idle Timeout Severance

| Metadata | Details |
| :--- | :--- |
| **Date** | January 9, 2026 |
| **Incident Severity** | P1 (Intermittent Tool Failure & Duplicate Transactions) |
| **Impact** | 22% of heavy data-warehouse analytics tool executions failed midway with broken pipes, triggering automated agent retries that duplicated downstream report generation jobs. |
| **Root Cause** | Default AWS Application Load Balancer (ALB) 60-second idle connection timeout dropping silent SSE streams during long tool runs. |
| **Resolution Time** | 1 hour 15 minutes |

#### Incident Summary

An enterprise deployed a centralized MCP server behind an AWS Application Load Balancer to provide agents with a `run_warehouse_query` tool. The tool executed complex Snowflake SQL aggregations taking between 75 and 110 seconds.

Users reported that Claude and autonomous agents repeatedly threw `TransportClosedError: The underlying Server-Sent Events stream was terminated unexpectedly` after exactly 60 seconds of waiting. Believing the query had failed, the autonomous agents initiated automated retries, submitting the identical query two or three times. This incurred massive computational charges and created duplicate data snapshots in S3 buckets.

#### Root Cause Analysis (RCA)

Investigation into AWS CloudWatch Access Logs revealed:
1. The client opened GET `/sse` successfully (`status 200`).
2. The client issued POST `/message?sessionId=...` with tool `run_warehouse_query`. The server returned HTTP 202 Accepted.
3. The server handed the SQL query to Snowflake and awaited completion.
4. During this 90-second execution window, **zero bytes were transmitted over the open GET `/sse` HTTP connection**.
5. The intermediate AWS Application Load Balancer enforces a strict default **Idle Timeout of 60 seconds**. If neither client nor server transmits a packet across an established TCP socket within 60 seconds, the ALB terminates the connection, silently sending a `TCP RST` packet to both sides.
6. At second 60, the client’s `EventSource` received the RST and transitioned to `CLOSED`.
7. At second 88, the Snowflake query finished. The MCP server attempted to write the JSON-RPC result into the response object:
   ```typescript
   res.write(`event: message\ndata: ${JSON.stringify(rpcResult)}\n\n`);
   ```
8. The operating system kernel raised `EPIPE` (Broken pipe) / `ECONNRESET`. The result was lost in the ether.
