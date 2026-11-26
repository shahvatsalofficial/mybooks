import OpenAI from 'openai';
import { z } from 'zod';
import { zodResponseFormat } from 'openai/helpers/zod';

const openai = new OpenAI();

// Define schema using Zod for compile-time TypeScript type safety
const TelemetryAuditSchema = z.object({
  service_name: z.string(),
  health_status: z.enum(['HEALTHY', 'DEGRADED', 'CRITICAL']),
  metrics: z.object({
    cpu_utilization_percent: z.number().min(0).max(100),
    memory_rss_bytes: z.number().int(),
    active_connections: z.number().int()
  }),
  alert_flags: z.array(z.string()),
  remediation_recommendation: z.string().nullable()
});

async function runTelemetryAudit(rawTelemetryLogs: string) {
  const completion = await openai.beta.chat.completions.parse({
    model: 'gpt-4o-2024-08-06',
    messages: [
      {
        role: 'system',
        content: 'You are an autonomous SRE telemetry parsing engine. Ingest raw log streams and emit structured metrics.'
      },
      {
        role: 'user',
        content: rawTelemetryLogs
      }
    ],
    response_format: zodResponseFormat(TelemetryAuditSchema, 'telemetry_audit'),
    temperature: 0.0 // Strictly deterministic
  });

  // Type-safe, guaranteed non-null parsed object
  const auditResult = completion.choices[0].message.parsed;
  console.log(`Parsed service ${auditResult.service_name} with status: ${auditResult.health_status}`);
  return auditResult;
}
