/**
 * Enterprise AI Governance & Audit Logger Proxy
 * Stack: Node.js 20+ / TypeScript 5.4 / Express / Crypto / Zod
 */

import express, { Request, Response, NextFunction } from "express";
import crypto from "crypto";
import { z } from "zod";

const app = express();
app.use(express.json({ limit: "4mb" }));

// 1. Immutable Audit Record Schema
const AuditRecordSchema = z.object({
  audit_id: z.string().uuid(),
  timestamp: z.string().datetime(),
  agent_identity: z.string(),
  action_name: z.string(),
  sanitized_payload: z.record(z.unknown()),
  redaction_count: z.number().int(),
  payload_sha256: z.string(),
  compliance_flags: z.array(z.string())
});

type AuditRecord = z.infer<typeof AuditRecordSchema>;

// 2. High-Performance Regex PII Scrubbing Engine
const PII_PATTERNS = [
  { name: "US_SSN", regex: /\b\d{3}-\d{2}-\d{4}\b/g, mask: "[REDACTED_SSN]" },
  { name: "CREDIT_CARD", regex: /\b(?:\d{4}[-\s]?){3}\d{4}\b/g, mask: "[REDACTED_CC]" },
  { name: "EMAIL_ADDR", regex: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g, mask: "[REDACTED_EMAIL]" },
  { name: "PHONE_NUMBER", regex: /\b(?:\+?1[-. ]?)?\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})\b/g, mask: "[REDACTED_PHONE]" }
];

function sanitizeObjectRecursive(obj: any): { sanitized: any; totalRedactions: number; flags: string[] } {
  let totalRedactions = 0;
  const flags: Set<string> = new Set();

  function scrubString(str: string): string {
    let result = str;
    for (const pattern of PII_PATTERNS) {
      const matches = str.match(pattern.regex);
      if (matches) {
        totalRedactions += matches.length;
        flags.add(pattern.name);
        result = result.replace(pattern.regex, pattern.mask);
      }
    }
    return result;
  }

  function walk(current: any): any {
    if (typeof current === "string") {
      return scrubString(current);
    } else if (Array.isArray(current)) {
      return current.map(item => walk(item));
    } else if (typeof current === "object" && current !== null) {
      const scrubbedObj: Record<string, any> = {};
      for (const [key, val] of Object.entries(current)) {
        scrubbedObj[key] = walk(val);
      }
      return scrubbedObj;
    }
    return current;
  }

  const sanitized = walk(obj);
  return { sanitized, totalRedactions, flags: Array.from(flags) };
}

// 3. Enterprise Audit Proxy Middleware
app.post("/api/v1/governance/dispatch", (req: Request, res: Response): void => {
  const agentId = req.headers["x-agent-identity"] as string || "unknown-agent";
  const actionName = req.headers["x-action-name"] as string || "unspecified-action";

  const rawPayload = req.body;
  const { sanitized, totalRedactions, flags } = sanitizeObjectRecursive(rawPayload);

  // Compute SHA-256 Digest for Non-Repudiation
  const payloadJson = JSON.stringify(sanitized);
  const hash = crypto.createHash("sha256").update(payloadJson).digest("hex");

  const auditRecord: AuditRecord = {
    audit_id: crypto.randomUUID(),
    timestamp: new Date().toISOString(),
    agent_identity: agentId,
    action_name: actionName,
    sanitized_payload: sanitized,
    redaction_count: totalRedactions,
    payload_sha256: hash,
    compliance_flags: flags
  };

  // Log to Enterprise Audit Store / SIEM (Splunk / Datadog)
  console.log(`[AUDIT LOG] ${auditRecord.audit_id} | Agent: ${agentId} | PII Redactions: ${totalRedactions}`);

  // In production: Forward sanitized payload to downstream microservice
  res.status(200).json({
    status: "DISPATCHED_AND_AUDITED",
    audit_id: auditRecord.audit_id,
    sha256_fingerprint: hash,
    pii_redacted: totalRedactions > 0,
    compliance_flags: flags,
    forwarded_data: sanitized
  });
});

export default app;
