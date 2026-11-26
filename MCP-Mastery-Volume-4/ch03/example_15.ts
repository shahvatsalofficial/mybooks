class RateLimitedQueue {
  private queue: (() => Promise<void>)[] = [];
  private isPaused: boolean = false;

  async enqueue<T>(fn: () => Promise<T>): Promise<T> {
    return new Promise<T>((resolve, reject) => {
      this.queue.push(async () => {
        try {
          const res = await fn();
          resolve(res);
        } catch (err: any) {
          if (err.status === 403 && err.response?.headers?.["x-ratelimit-remaining"] === "0") {
            const resetTime = Number(err.response.headers["x-ratelimit-reset"]) * 1000;
            const waitMs = Math.max(resetTime - Date.now(), 1000);
            this.pause(waitMs);
            // Re-enqueue failed operation
            this.queue.unshift(this.queue.pop()!);
          } else {
            reject(err);
          }
        }
      });
      this.processNext();
    });
  }

  private pause(durationMs: number) {
    this.isPaused = true;
    setTimeout(() => {
      this.isPaused = false;
      this.processNext();
    }, durationMs);
  }

  private async processNext() {
    if (this.isPaused || this.queue.length === 0) return;
    const task = this.queue.shift();
    if (task) await task();
    this.processNext();
  }
}
