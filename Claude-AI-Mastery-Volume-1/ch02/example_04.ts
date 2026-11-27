/**
 * Enterprise TypeScript XML Prompt Engine with Zod Schema Validation
 * Author: Vatsal Shah, Lead Enterprise AI Architect
 * Publisher: Vatsal Shah (c) 2026
 */

import Anthropic from '@anthropic-ai/sdk';
import { z } from 'zod';

// Define target output schema using Zod
export const SecurityAuditSchema = z.object({
  targetModule: z.string().describe('Name of the audited module'),
  findingsCount: z.number().int().nonnegative(),
  riskScore: z.enum(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']),
  vulnerabilities: z.array(
    z.object({
      cweId: z.string(),
      description: z.string(),
      remediationPatch: z.string()
    })
  ),
  isApprovedForRelease: z.boolean()
});

export type SecurityAuditResult = z.infer<typeof SecurityAuditSchema>;

export class TypeScriptPromptEngine {
  private client: Anthropic;

  constructor(apiKey?: string) {
    this.client = new Anthropic({ apiKey: apiKey || process.env.ANTHROPIC_API_KEY });
  }

  public compilePrompt(
    persona: string,
    guidelines: string[],
    sourceCode: string
  ): { system: string; user: string } {
    const system = `<system_persona>\n${persona}\n</system_persona>\n\n` +
      `<guidelines>\n${guidelines.map((g, i) => `  <rule id="${i+1}">${g}</rule>`).join('\n')}\n</guidelines>\n\n` +
      `<output_contract>\n` +
      `Emit final answer strictly inside <structured_output>...</structured_output> as valid JSON matching schema.\n` +
      `</output_contract>`;

    const user = `<source_under_audit>\n${sourceCode}\n</source_under_audit>\n\n` +
      `<user_query>Perform a thorough security audit of the provided source code.</user_query>`;

    return { system, user };
  }

  public async executeAudit(
    persona: string,
    guidelines: string[],
    sourceCode: string
  ): Promise<SecurityAuditResult> {
    const { system, user } = this.compilePrompt(persona, guidelines, sourceCode);

    const response = await this.client.messages.create({
      model: 'claude-3-5-sonnet-20241022',
      max_tokens: 4096,
      temperature: 0.0,
      system: system,
      messages: [
        { role: 'user', content: user },
        { role: 'assistant', content: '<thinking>\n' }
      ]
    });

    const rawText = (response.content[0] as any).text;
    
    // Extract JSON block
    const match = rawText.match(/<structured_output>([\s\S]*?)<\/structured_output>/);
    if (!match) {
      throw new Error(`Model failed to emit <structured_output> tags. Raw text: ${rawText.slice(0, 150)}`);
    }

    const parsedJson = JSON.parse(match[1].trim());
    return SecurityAuditSchema.parse(parsedJson);
  }
}
