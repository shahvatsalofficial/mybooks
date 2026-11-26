# Regenerate primary key to sever all unauthorized access
   az cognitiveservices account keys regenerate \
     --name aoai-prod-eastus2-01 \
     --resource-group rg-ai-prod \
     --key-name key1
   ```
2. **Switch Gateway Ingress to Secondary Key**:
   Update Key Vault secret reference `aoai-active-key` to point to `key2`.
3. **Flush Ingress Caches**:
   Restart all APIM gateway instances to force immediate re-authentication.

### 3. Forensic Triage ($T+5\text{ to }T+30\text{ minutes}$)
1. Execute KQL query to identify all anomalous calls originating from outside approved corporate CIDRs:
   ```kql
   AzureDiagnostics
   | where ResourceProvider == "MICROSOFT.COGNITIVESERVICES"
   | where TimeGenerated >= ago(24h)
   | where not(ipv4_is_in_range(CallerIPAddress, "10.0.0.0/8"))
   | project TimeGenerated, OperationName, CallerIPAddress, ResultSignature, properties_s
   | order by TimeGenerated desc
   ```
2. Export all IP addresses to Azure Sentinel Threat Intelligence.
3. Prepare regulatory incident report for GDPR Article 33 disclosure within 72 hours if customer PII exfiltration is detected.


---

## 26. Production Azure API Management (APIM) Policy Definition

Enterprise ingress gateways enforce security through immutable APIM XML policies. The following policy validates JWT signatures, enforces rate limiting, scrubs sensitive internal headers, and logs audit events to Event Hub.
