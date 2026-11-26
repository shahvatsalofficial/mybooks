/**
 * Production TypeScript Enterprise Claude Gateway
 * Author: Vatsal Shah, Lead Enterprise AI Architect
 * Publisher: Opportunity4u Press (c) 2026
 */

import Anthropic from '@anthropic-ai/sdk';
import { Response } from 'express';

export enum ClaudeTier {
  HAIKU = 'claude-3-5-haiku-20241022',
  SONNET = 'claude-3-5-sonnet-20241022',
  OPUS = 'claude-3-opus-20240229'
}

export interface StreamingRequestPayload {
  prompt: string;
  systemPrompt?: string;
  maxTokens?: number;
  temperature?: number;
  costCenter: string;
  latencySensitive?: boolean;
}

export class EnterpriseStreamingGateway {
  private client: Anthropic;

  constructor(apiKey?: string) {
    const key = apiKey || process.env.ANTHROPIC_API_KEY;
    if (!key) {
      throw new Error('FATAL: ANTHROPIC_API_KEY environment variable is missing.');
    }
    this.client = new Anthropic({ apiKey: key });
  }

  /**
   * Intelligently selects the model based on prompt characteristics and latency requirements.
   */
  public routeModel(prompt: string, latencySensitive: boolean): ClaudeTier {
    if (latencySensitive) return ClaudeTier.HAIKU;
    
    // Heuristic routing
    const lower = prompt.toLowerCase();
    const isCode = lower.includes('typescript') || lower.includes('python') || lower.includes('function');
    const isComplex = lower.includes('architect') || lower.includes('refactor') || lower.includes('audit');
    
    if (isCode || isComplex) {
      return ClaudeTier.SONNET;
    }
    
    if (prompt.length < 1200) {
      return ClaudeTier.HAIKU;
    }

    return ClaudeTier.SONNET;
  }

  /**
   * Streams model response directly to client via Server-Sent Events (SSE).
   */
  public async streamReasoningResponse(
    payload: StreamingRequestPayload,
    res: Response
  ): Promise<void> {
    const model = this.routeModel(payload.prompt, !!payload.latencySensitive);
    const startTime = Date.now();

    // Configure SSE headers
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');
    res.setHeader('x-selected-model', model);

    try {
      const systemBlocks: Anthropic.Beta.PromptCaching.PromptCachingBetaTextBlockParam[] = [];
      if (payload.systemPrompt) {
        systemBlocks.push({
          type: 'text',
          text: payload.systemPrompt,
          cache_control: payload.systemPrompt.length > 2000 ? { type: 'ephemeral' } : undefined
        });
      }

      const stream = await this.client.messages.stream({
        model: model,
        max_tokens: payload.maxTokens || 4096,
        temperature: payload.temperature ?? 0.0,
        system: systemBlocks.length > 0 ? (systemBlocks as any) : undefined,
        messages: [{ role: 'user', content: payload.prompt }]
      });

      // Stream text chunks directly
      stream.on('text', (textDelta: string) => {
        res.write(`data: ${JSON.stringify({ chunk: textDelta })}\n\n`);
      });

      const finalMessage = await stream.finalMessage();
      const durationMs = Date.now() - startTime;

      // Emit completion metadata
      const metadata = {
        status: 'COMPLETE',
        model: model,
        inputTokens: finalMessage.usage.input_tokens,
        outputTokens: finalMessage.usage.output_tokens,
        latencyMs: durationMs,
        costCenter: payload.costCenter
      };

      res.write(`data: ${JSON.stringify({ metadata })}\n\n`);
      res.write('event: done\ndata: {}\n\n');
      res.end();

    } catch (error: any) {
      console.error('[ClaudeGateway] Streaming error:', error.message);
      res.write(`event: error\ndata: ${JSON.stringify({ error: error.message })}\n\n`);
      res.end();
    }
  }
}
