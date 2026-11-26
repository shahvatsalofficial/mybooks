terraform plan -detailed-exitcode -no-color -out=drift.plan
   ```
   * **Exit Code `0`**: Clean. S3 remote state exactly matches physical AWS infrastructure.
   * **Exit Code `1`**: Error during graph calculation or provider API authentication.
   * **Exit Code `2`**: **Drift Detected.** The physical infrastructure has diverged from Git.
3. **Forensic Attribution**: If drift is detected, the pipeline queries AWS CloudTrail using `lookup_events` to determine the `userIdentity.arn` of the operator who executed the out-of-band mutation.
4. **Self-Healing Reconciliation**: Depending on policy severity:
   * **Low-Severity Drift**: An automated pull request is opened to backport the changes into Git.
   * **High-Severity / Unauthorized Mutation**: The GitOps engine automatically executes `terraform apply -auto-approve` to overwrite manual changes and restore canonical Git state in under 180 seconds.

---

## 1.5 Production Automation: Multi-Account State Lock Auditor & Orphan Lock Purger

When a CI/CD runner dies abruptly (e.g., spot instance termination, OOM crash, or pipeline cancellation), the DynamoDB Lock Table retains the lock record. Subsequent pipeline runs fail permanently with `Error acquiring the state lock`.

The following production-grade Python script automates orphan lock discovery, inspects lock age, validates active pipeline status, and cleanly releases stale locks.
