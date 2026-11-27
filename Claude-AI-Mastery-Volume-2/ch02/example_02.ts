/**
 * Recipe 02.2: TypeScript Strict Tool Choice & Zod Schema Pipeline
 * Author: Vatsal Shah (Vatsal Shah)
 * License: Apache-2.0
 */

import Anthropic from '@anthropic-ai/sdk';
import { z } from 'zod';

// Define strict domain validation schema using Zod
export const FinancialRecordSchema = z.object({
  transactionId: z.string().uuid(),
  amount: z.number().positive(),
  currency: z.enum(['USD', 'EUR', 'GBP', 'JPY']),
  merchantCategory: z.string().min(2),
  riskScore: z.number().min(0).max(100),
  isFlaggedForAudit: z.boolean()
});

export type FinancialRecord = z.infer<typeof FinancialRecordSchema>;

export class StructuredExtractor {
  private client: Anthropic;

  constructor(apiKey?: string) {
    this.client = new Anthropic({ apiKey: apiKey || process.env.ANTHROPIC_API_KEY });
  }

  /**
   * Forces Claude to extract structured data conforming exactly to the Zod schema.
   */
  async extractVerifiedRecord(unstructuredDocumentText: string): Promise<FinancialRecord> {
    const toolDefinition: Anthropic.Tool = {
      name: 'submit_verified_transaction',
      description: 'Ingests verified financial transaction data into enterprise ledger.',
      input_schema: {
        type: 'object',
        properties: {
          transactionId: { type: 'string', format: 'uuid', description: 'Canonical UUID v4' },
          amount: { type: 'number', minimum: 0.01, description: 'Positive monetary value' },
          currency: { type: 'string', enum: ['USD', 'EUR', 'GBP', 'JPY'] },
          merchantCategory: { type: 'string', description: 'Standard MCC description' },
          riskScore: { type: 'number', minimum: 0, maximum: 100, description: 'Calculated risk index' },
          isFlaggedForAudit: { type: 'boolean', description: 'Audit flag status' }
        },
        required: ['transactionId', 'amount', 'currency', 'merchantCategory', 'riskScore', 'isFlaggedForAudit']
      }
    };

    const response = await this.client.messages.create({
      model: 'claude-3-5-sonnet-20241022',
      max_tokens: 1024,
      temperature: 0.0, // Zero temperature guarantees deterministic extraction
      tools: [toolDefinition],
      // CRITICAL: Force Claude to call this specific tool, bypassing natural language chatter
      tool_choice: { type: 'tool', name: 'submit_verified_transaction' },
      messages: [
        {
          role: 'user',
          content: `Extract the transaction details from the following audit log:\n\n${unstructuredDocumentText}`
        }
      ]
    });

    const toolUseBlock = response.content.find(block => block.type === 'tool_use');
    if (!toolUseBlock || toolUseBlock.type !== 'tool_use') {
      throw new Error('Fatal Extraction Failure: Model did not return expected tool_use block.');
    }

    // Validate raw model output through Zod runtime parser
    const validatedData = FinancialRecordSchema.parse(toolUseBlock.input);
    return validatedData;
  }
}
