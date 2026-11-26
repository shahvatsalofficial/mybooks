/**
 * Enterprise Node.js / TypeScript OpenAI Streaming Gateway
 * Features AbortController propagation, backpressure buffers, and full jitter retry.
 */
import OpenAI from "openai";
import { IncomingMessage, ServerResponse } from "http";

export interface GatewayConfig {
  apiKey: string;
  projectId: string;
  timeoutMs: number;
  maxRetries: number;
}

export class TypeScriptEnterpriseGateway {
  private client: OpenAI;
  private maxRetries: number;

  constructor(config: GatewayConfig) {
    this.maxRetries = config.maxRetries;
    this.client = new OpenAI({
      apiKey: config.apiKey,
      project: config.projectId,
      timeout: config.timeoutMs,
      maxRetries: 0 // Native retry disabled to enforce custom jitter algorithm
    });
  }

  private calculateJitterBackoff(attempt: number, baseMs: number = 1000, capMs: number = 20000): number {
    const exponential = Math.min(capMs, baseMs * Math.pow(2, attempt));
    return Math.random() * exponential;
  }

  public async streamCompletionToClient(
    model: string,
    messages: OpenAI.Chat.Completions.ChatCompletionMessageParam[],
    clientRes: ServerResponse,
    abortSignal?: AbortSignal
  ): Promise<void> {
    let attempt = 0;

    while (true) {
      const internalAbort = new AbortController();
      if (abortSignal) {
        abortSignal.addEventListener("abort", () => internalAbort.abort());
      }

      try {
        const stream = await this.client.chat.completions.create(
          {
            model,
            messages,
            stream: true,
            stream_options: { include_usage: true }
          },
          { signal: internalAbort.signal }
        );

        // Configure SSE headers on downstream HTTP response
        clientRes.writeHead(200, {
          "Content-Type": "text/event-stream",
          "Cache-Control": "no-cache",
          "Connection": "keep-alive"
        });

        for await (const chunk of stream) {
          if (abortSignal?.aborted) {
            internalAbort.abort();
            break;
          }

          const content = chunk.choices[0]?.delta?.content || "";
          if (content) {
            const ok = clientRes.write(`data: ${JSON.stringify({ content })}\n\n`);
            // Handle backpressure: if internal buffer full, wait for drain event
            if (!ok) {
              await new Promise((resolve) => clientRes.once("drain", resolve));
            }
          }

          if (chunk.usage) {
            clientRes.write(`data: ${JSON.stringify({ usage: chunk.usage })}\n\n`);
          }
        }

        clientRes.write("data: [DONE]\n\n");
        clientRes.end();
        return;

      } catch (err: any) {
        attempt++;
        if (attempt > this.maxRetries || internalAbort.signal.aborted) {
          clientRes.writeHead(500, { "Content-Type": "application/json" });
          clientRes.end(JSON.stringify({ error: "Upstream OpenAI Gateway Exhaustion", details: err.message }));
          return;
        }

        const waitMs = this.calculateJitterBackoff(attempt);
        console.warn(`[Gateway] Attempt ${attempt} failed. Backing off for ${waitMs.toFixed(0)}ms. Error: ${err.message}`);
        await new Promise((resolve) => setTimeout(resolve, waitMs));
      }
    }
  }
}
