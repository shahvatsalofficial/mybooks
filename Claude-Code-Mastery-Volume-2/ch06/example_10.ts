export class DistributedTokenBucket {
  private capacity: number;
  private refillRatePerSec: number;
  private currentTokens: number;
  private lastRefillTimestamp: number;

  constructor(capacity: number, refillRatePerSec: number) {
    this.capacity = capacity;
    this.refillRatePerSec = refillRatePerSec;
    this.currentTokens = capacity;
    this.lastRefillTimestamp = Date.now();
  }

  async acquire(tokensRequested: number, priority: 'critical' | 'speculative' = 'critical'): Promise<void> {
    this.refill();
    if (this.currentTokens >= tokensRequested) {
      this.currentTokens -= tokensRequested;
      return;
    }
    const waitTimeMs = Math.ceil(((tokensRequested - this.currentTokens) / this.refillRatePerSec) * 1000);
    await new Promise((resolve) => setTimeout(resolve, waitTimeMs));
    return this.acquire(tokensRequested, priority);
  }

  private refill(): void {
    const now = Date.now();
    const elapsedSeconds = (now - this.lastRefillTimestamp) / 1000;
    this.currentTokens = Math.min(this.capacity, this.currentTokens + elapsedSeconds * this.refillRatePerSec);
    this.lastRefillTimestamp = now;
  }
}
