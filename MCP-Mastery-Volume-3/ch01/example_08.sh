ulimit -n 65535
   sysctl -w net.ipv4.tcp_max_syn_backlog=8192
   sysctl -w net.core.somaxconn=8192
   ```
3. **Adaptive Backpressure Shedding**: When active in-flight requests exceed 85% of buffer capacity, the gateway sheds load early by returning clean JSON-RPC rate limit errors (`-32000: Rate limit exceeded; retry after 250ms`) rather than buffering connections until memory exhaustion.

---

## 1.10 Where This Breaks: Common Pitfalls & Edge Cases

When deploying MCP Gateways under high throughput, systems engineers frequently encounter four failure modes:

### 1. Zombie Server-Sent Events (SSE) Streams
If an AI client terminates its TCP connection abruptly (e.g., a developer closes their laptop lid or an agent process is killed), standard Node.js and Go HTTP servers do not automatically detect the broken socket until the next active write attempt. The Gateway continues holding upstream worker connections open, silently draining capacity.  
*Resolution*: Configure TCP Keep-Alives on all ingress sockets (`socket.setKeepAlive(true, 15000)`) and monitor the `req.on('close')` event to immediately abort upstream child tasks via `AbortController`.

### 2. Radical Namespace Collisions
If two independent teams register servers that both provide a tool named `search_records`, the Gateway's capability aggregation creates an ambiguous routing collision. The last registered server silently overwrites the previous tool definition in the global catalog.  
*Resolution*: Enforce mandatory namespace prefixes at registration time (`team_finance.search_records`, `team_crm.search_records`). The gateway must reject registration attempts that contain bare or conflicting tool identifiers.

### 3. Distributed Clock Drift in Lease Expiry
If upstream servers use system wall-clock timestamps (`Date.now()`) to compute registration expirations across different virtual machines, clock drift (even by 2–3 seconds) causes healthy instances to be prematurely culled from the routing table.  
*Resolution*: Use monotonically increasing counters or rely strictly on centralized Redis key TTL expiration rather than evaluating client-reported wall timestamps.

### 4. Payload Bloat in tools/list
When an enterprise connects 80 specialized tool servers each providing 15 tools with exhaustive JSON Schema parameters, the synthesized `tools/list` response can exceed 4 Megabytes. Transferring and parsing this payload on every initialization degrades AI client responsiveness.  
*Resolution*: Implement GZIP/Brotli compression at the Gateway ingress, and leverage tool filtering by injecting client authorization scopes so each user only downloads schemas for the tools they have permission to execute.

---

## 1.11 Hands-On Architecture Exercises

### Check Exercise (5 Minutes)
**Question**: An AI client sends a JSON-RPC request to the Gateway calling tool `"crm_update_contact"`. The Gateway has two healthy replicas in pool `"crm"`:
- Node A: In-flight requests = 14, Weight = 100
- Node B: In-flight requests = 8, Weight = 50

Under the Power of Two Choices (P2C) algorithm weighted scoring formula ($\text{Score} = \text{InFlight} / (\text{Weight} / 100)$), which node will the Gateway dispatch the request to?

*Solution*:
- Score for Node A: $14 / (100 / 100) = 14 / 1.0 = 14.0$
- Score for Node B: $8 / (50 / 100) = 8 / 0.5 = 16.0$
- The lower score represents lower load relative to capacity. Node A has a score of 14.0 vs Node B's 16.0. **The Gateway dispatches the request to Node A.**

### Build Exercise (20 Minutes)
**Objective**: Enhance `minimal_gateway.js` from Section 1.2 to support an active health check probe.  
**Requirements**:
1. Implement a background timer running every 5,000 milliseconds.
2. The timer issues an HTTP GET to `/health` on all registered backends.
3. If an upstream backend returns anything other than HTTP 200 within 1,000 milliseconds, mark that backend unhealthy and temporarily route requests to a secondary fallback URL.

*Solution Code*:
