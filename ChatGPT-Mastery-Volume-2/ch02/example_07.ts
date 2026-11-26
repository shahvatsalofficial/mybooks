import { z } from "zod";
import OpenAI from "openai";
import { zodResponseFormat } from "openai/helpers/zod";

const openai = new OpenAI();

// Define Enterprise Risk Schema in Zod
export const FinancialRiskReportSchema = z.object({
  report_id: z.string().describe("Unique cryptographic UUIDv4 audit report identifier"),
  portfolio_symbol: z.string().describe("Primary equity portfolio identifier"),
  risk_level: z.enum(["LOW", "ELEVATED", "CRITICAL"]),
  var_95_daily_pct: z.number().min(0).max(100).describe("95% 1-day Value at Risk (VaR) percentage"),
  stress_test_findings: z.array(z.string()).describe("List of simulated macro scenario failures"),
  remediation_steps: z.array(z.string()).describe("Prioritized hedge rebalancing actions")
}).strict(); // Crucial: .strict() enforces additionalProperties: false

export type FinancialRiskReport = z.infer<typeof FinancialRiskReportSchema>;

export async function generateRiskReport(auditData: string): Promise<FinancialRiskReport> {
  const completion = await openai.beta.chat.completions.parse({
    model: "gpt-4o",
    messages: [
      { role: "system", content: "You are an institutional financial risk auditor." },
      { role: "user", content: auditData }
    ],
    response_format: zodResponseFormat(FinancialRiskReportSchema, "risk_report")
  });

  const parsedReport = completion.choices[0].message.parsed;
  if (!parsedReport) {
    throw new Error("Fatal: Schema parsing returned null from OpenAI Gateway.");
  }
  return parsedReport;
}
