/**
 * Recipe 03.6: Token Egress Rate Shaper & Backpressure Pacer
 * Author: Vatsal Shah (Opportunity4u Press)
 * License: Apache-2.0
 */

import { Transform, TransformCallback } from 'node:stream';

export interface RateShaperOptions {
  tokensPerSecond?: number; // Target human reading velocity (default: 35 tokens/s)
  maxBufferSize?: number;   // Maximum allowed backlog before pausing upstream
}

export class TokenRateShaper extends Transform {
  private readonly intervalMs: number;
  private readonly maxBufferSize: number;
  private tokenQueue: string[] = [];
  private isDraining: boolean = false;
  private timer: NodeJS.Timeout | null = null;

  constructor(options: RateShaperOptions = {}) {
    super({ objectMode: true, highWaterMark: 16 });
    const tps = options.tokensPerSecond || 35;
    this.intervalMs = Math.floor(1000 / tps);
    this.maxBufferSize = options.maxBufferSize || 250;
  }

  _transform(chunk: string, encoding: BufferEncoding, callback: TransformCallback): void {
    this.tokenQueue.push(chunk);

    // Apply backpressure if local token backlog exceeds safety threshold
    if (this.tokenQueue.length >= this.maxBufferSize) {
      this.isDraining = true;
    }

    if (!this.timer) {
      this.scheduleNextEmission();
    }

    // Acknowledge chunk ingestion to upstream if buffer is healthy
    if (!this.isDraining) {
      callback();
    } else {
      // Hold callback until buffer drains back below 50%
      this.once('drain_backlog', () => callback());
    }
  }

  private scheduleNextEmission(): void {
    this.timer = setTimeout(() => {
      if (this.tokenQueue.length > 0) {
        const token = this.tokenQueue.shift()!;
        this.push(token);

        // Check if backpressure can be released
        if (this.isDraining && this.tokenQueue.length < this.maxBufferSize / 2) {
          this.isDraining = false;
          this.emit('drain_backlog');
        }
      }

      if (this.tokenQueue.length > 0) {
        this.scheduleNextEmission();
      } else {
        this.timer = null;
      }
    }, this.intervalMs);
  }

  _flush(callback: TransformCallback): void {
    // Drain any remaining tokens before finalizing stream
    const drainInterval = setInterval(() => {
      if (this.tokenQueue.length === 0) {
        clearInterval(drainInterval);
        if (this.timer) clearTimeout(this.timer);
        callback();
      }
    }, 10);
  }
}
