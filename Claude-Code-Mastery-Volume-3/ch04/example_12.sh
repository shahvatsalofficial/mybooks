kubectl get claudeagentdaemons -A -o wide
   ```
4. **Automated Garbage Collection & Cascading Deletion**:
   When the task reaches a terminal state (`Completed` or `Failed`), the operator sets an `OwnerReference` linking the temporary PVC, config maps, and gVisor pods directly to the parent CRD. When the parent CRD is deleted or archived by the retention policy, the Kubernetes garbage collector automatically deletes all associated storage and network resources, preventing resource leaks across the cluster.

---

## 5.7 Autonomous Telemetry & Distributed Tracing with OpenTelemetry

When an autonomous agent operates interactively in a developer’s terminal, the developer acts as the real-time observer. When an agent executes in headless CI/CD across thousands of automated runs, lack of deep observability turns the system into an opaque black box. If an agent begins failing to resolve pull requests or generates syntactically invalid code, engineers cannot diagnose whether the root cause was an ambiguous prompt, a network timeout to the foundation model, a misconfigured compiler flag, or an edge-case hallucination.

To eliminate this opacity, enterprise agent architectures mandate full-stack **Distributed Tracing using OpenTelemetry (OTel)**.

### The Hierarchical OpenTelemetry Span Tree
An autonomous agent execution is modeled not as flat log lines, but as a deeply nested, causal hierarchy of OpenTelemetry spans:
