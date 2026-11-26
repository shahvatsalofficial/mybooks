kubectl argo rollouts abort payments-auth-service
   ```
   Istio instantly shifts 100% of incoming production traffic back to the stable baseline pods. Zero customer requests are routed to the canary. Total duration of customer exposure: **18 seconds**.
2. **Pod Quarantine & Heap Dump Capture (Second 5)**: Before terminating the canary pods, the sentry isolates one degraded pod from the service mesh and triggers a non-destructive heap dump and thread dump via Kubernetes exec:
   ```bash
   kubectl exec payments-auth-canary-7f89d-x9z21 -- node --inspect-brk=0.0.0.0:9229 &
   ```
   The memory profile and eBPF network trace are dumped directly into a secure S3 diagnostics bucket.
3. **Automated Git Revert (Second 15)**: The agent creates a fast-forward revert commit on the production release branch:
   ```bash
   git revert --no-edit 8a4f91b && git push origin main
   ```

#### Step 4: Autonomous Incident Post-Mortem Synthesis
With production completely safeguarded, Claude Code is initialized in an offline analysis container. The agent is provided with:
- The git diff between `v2.4.0` and `v2.4.1`.
- The Prometheus telemetry time-series graph.
- The captured heap dump summary and application log traces.

Within 90 seconds, Claude diagnoses the root cause:
