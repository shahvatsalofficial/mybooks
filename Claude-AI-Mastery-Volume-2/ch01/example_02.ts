/**
 * Recipe 01.2: Enterprise Ephemeral Prompt Caching Engine
 * Author: Vatsal Shah (Opportunity4u Press)
 * License: Apache-2.0
 */

import Anthropic from '@anthropic-ai/sdk';
import { MessageParam, TextBlockParam } from '@anthropic-ai/sdk/resources';

export interface PromptCacheConfig {
  apiKey: string;
  staticComplianceDocumentation: string;
  apiSchemaSpecification: string;
}

export class ClaudeCacheEngine {
  private client: Anthropic;
  private complianceDoc: string;
  private apiSchema: string;

  constructor(config: PromptCacheConfig) {
    this.client = new Anthropic({ apiKey: config.apiKey });
    this.complianceDoc = config.staticComplianceDocumentation;
    this.apiSchema = config.apiSchemaSpecification;
  }

  /**
   * Constructs a multi-block system prompt with explicit ephemeral cache checkpoints.
   * Checkpoint 1: Static Enterprise Compliance Handbook (~12,000 tokens)
   * Checkpoint 2: Machine-readable OpenAPI Schema (~25,000 tokens)
   */
  private buildSystemCacheBlocks(): TextBlockParam[] {
    return [
      {
        type: 'text',
        text: 'You are the Autonomous Enterprise Architect for Global Financial Systems. ' +
              'Adhere strictly to all corporate regulatory constraints and schema contracts below.'
      },
      {
        type: 'text',
        text: `--- ENTERPRISE COMPLIANCE HANDBOOK ---\n${this.complianceDoc}`,
        cache_control: { type: 'ephemeral' } // CHECKPOINT 1: Static policy
      },
      {
        type: 'text',
        text: `--- SYSTEM OPENAPI SPECIFICATIONS ---\n${this.apiSchema}`,
        cache_control: { type: 'ephemeral' } // CHECKPOINT 2: Pinned schemas
      }
    ];
  }

  /**
   * Executes a query against Claude 3.5 Sonnet leveraging cached system checkpoints.
   */
  async executeCachedTurn(
    conversationHistory: MessageParam[],
    userQuery: string
  ): Promise<{ text: string; cacheHits: number; cacheMisses: number; costSavingsPercent: number }> {
    const systemBlocks = this.buildSystemCacheBlocks();
    
    // Append the latest user query to history
    const messages: MessageParam[] = [
      ...conversationHistory,
      { role: 'user', content: userQuery }
    ];

    const response = await this.client.messages.create({
      model: 'claude-3-5-sonnet-20241022',
      max_tokens: 4096,
      temperature: 0.1,
      system: systemBlocks,
      messages: messages
    });

    const usage = response.usage as any;
    const cacheReadTokens = usage.cache_read_input_tokens || 0;
    const cacheWriteTokens = usage.cache_creation_input_tokens || 0;
    const regularInputTokens = usage.input_tokens || 0;

    // Calculate effective financial savings relative to raw baseline
    const totalInputContext = cacheReadTokens + cacheWriteTokens + regularInputTokens;
    const baselineCost = (totalInputContext / 1_000_000) * 3.00;
    const actualCost = ((regularInputTokens / 1_000_000) * 3.00) +
                       ((cacheWriteTokens / 1_000_000) * 3.75) +
                       ((cacheReadTokens / 1_000_000) * 0.30);
    
    const savingsPercent = baselineCost > 0 ? ((baselineCost - actualCost) / baselineCost) * 100 : 0;

    const textContent = response.content
      .filter(block => block.type === 'text')
      .map(block => (block as any).text)
      .join('\n');

    return {
      text: textContent,
      cacheHits: cacheReadTokens,
      cacheMisses: cacheWriteTokens,
      costSavingsPercent: Math.max(0, savingsPercent)
    };
  }
}
