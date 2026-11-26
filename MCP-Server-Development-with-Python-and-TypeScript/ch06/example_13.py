async with httpx.AsyncClient(timeout=10.0) as client:
       response = await client.post("https://ci-runner.internal.corp/build", json={"repo": repo})
   ```
2. **Synchronous Fallback Rule**: Developers were trained on FastMCP’s offloading architecture: if a library is purely synchronous, declare the function as standard `def` (without `async`), allowing FastMCP to offload the execution to its worker thread pool automatically.
3. **Static Linting Gate**: Enforced `ruff check --select ASYNC` in git pre-commit hooks to reject any pull request containing synchronous socket or file I/O inside `async def` blocks.

---

### Post-Mortem 06.02: The Leaked Connection Pool Crash

| Metadata | Details |
| :--- | :--- |
| **Date** | March 29, 2026 |
| **Incident Severity** | P2 (Backend Database Outage) |
| **Impact** | Staging PostgreSQL database cluster hit `FATAL: remaining connection slots are reserved for non-replication superuser connections`, blocking all microservices. |
| **Root Cause** | An MCP tool instantiated a new `asyncpg.create_pool()` inside the tool handler body on every invocation rather than utilizing FastMCP lifespan management. |
| **Resolution Time** | 20 minutes |

#### Incident Summary

A team implemented a database inspection tool using FastMCP. The developer initialized the connection pool directly inside the tool function:
