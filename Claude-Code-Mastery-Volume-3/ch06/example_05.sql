SELECT * FROM customer_ledger WHERE id > :last_seen_id ORDER BY id ASC LIMIT 5000;
  ```
* Hard statement timeouts enforced on all migration connections: `SET statement_timeout = '5000ms'`.
* Backfill queries must execute strictly against **Read-Only Replicas**, never primary transactional databases.

---

## 6.5 Case Study 5: The ThreadLocal Memory Leak in Migrated Asynchronous Services

**Incident Date**: April 2026  
**Impact**: Cross-tenant data leak; critical regulatory report to financial compliance authorities.

#### The Genesis
An autonomous refactoring agent was tasked with modernizing a synchronous Java Spring MVC service into a modern asynchronous, non-blocking service using Spring WebFlux and Project Reactor.

In the legacy Spring MVC architecture, each HTTP request was serviced by a dedicated thread under the classic **Thread-Per-Request Model**. The legacy codebase stored the authenticated user’s session context in a standard Java `ThreadLocal` variable:
