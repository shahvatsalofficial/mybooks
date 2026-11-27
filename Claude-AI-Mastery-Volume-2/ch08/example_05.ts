/**
 * Recipe 08.5: Dynamic Prompt Cache Pinning & Cost Optimizer
 * Author: Vatsal Shah (Vatsal Shah)
 * License: Apache-2.0
 */

import Anthropic from '@anthropic-ai/sdk';

export interface OptimizedPromptPayload {
  system: Array<{
    type: 'text';
    text: string;
    cache_control?: { type: 'ephemeral' };
  }>;
  messages: Anthropic.MessageParam[];
}

export class PromptCacheOptimizer {
  /**
   * Pins static system directives and documentation to ephemeral prompt cache breakpoints.
   */
  public static buildCachedSystemPrompt(
    immutableEnterpriseDirectives: string,
    toolDefinitionsJson: string,
    dynamicTenantContext: string
  ): OptimizedPromptPayload['system'] {
    return [
      {
        type: 'text',
        text: immutableEnterpriseDirectives,
        // Breakpoint 1: Static enterprise policies (cached for 5 minutes across all tenants)
        cache_control: { type: 'ephemeral' },
      },
      {
        type: 'text',
        text: toolDefinitionsJson,
        // Breakpoint 2: Large API schemas and OpenAPI specs (cached across tenants)
        cache_control: { type: 'ephemeral' },
      },
      {
        type: 'text',
        text: dynamicTenantContext, // Dynamic tenant info (NOT cached to avoid cache misses)
      },
    ];
  }

  public static calculateCostSavings(usage: Anthropic.Usage): {
    standardCostUsd: number;
    actualCostUsd: number;
    dollarsSavedUsd: number;
    savingsPercent: number;
  } {
    const inputTokens = usage.input_tokens;
    const cacheReadTokens = (usage as any).cache_read_input_tokens || 0;
    const cacheWriteTokens = (usage as any).cache_creation_input_tokens || 0;
    const outputTokens = usage.output_tokens;

    // Rates for Claude 3.5 Sonnet: Input $3/M, Cache Read $0.30/M, Cache Write $3.75/M, Output $15/M
    const totalInput = inputTokens + cacheReadTokens + cacheWriteTokens;
    const standardCost = (totalInput / 1_000_000) * 3.0 + (outputTokens / 1_000_000) * 15.0;

    const actualCost =
      (inputTokens / 1_000_000) * 3.0 +
      (cacheReadTokens / 1_000_000) * 0.30 +
      (cacheWriteTokens / 1_000_000) * 3.75 +
      (outputTokens / 1_000_000) * 15.0;

    const saved = standardCost - actualCost;
    const pct = standardCost > 0 ? (saved / standardCost) * 100 : 0;

    return {
      standardCostUsd: Number(standardCost.toFixed(4)),
      actualCostUsd: Number(actualCost.toFixed(4)),
      dollarsSavedUsd: Number(saved.toFixed(4)),
      savingsPercent: Number(pct.toFixed(2)),
    };
  }
}
