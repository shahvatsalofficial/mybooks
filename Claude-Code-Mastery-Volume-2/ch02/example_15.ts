export async function executeWithDecorrelatedJitter<T>(
  operation: () => Promise<T>,
  maxRetries: number = 4,
  baseDelayMs: number = 300,
  maxDelayMs: number = 10000
): Promise<T> {
  let attempt = 0;
  let currentDelay = baseDelayMs;

  while (attempt < maxRetries) {
    try {
      return await operation();
    } catch (err: any) {
      attempt++;
      if (attempt >= maxRetries) throw err;

      // Calculate decorrelated jitter delay
      currentDelay = Math.min(maxDelayMs, Math.floor(Math.random() * (currentDelay * 3 - baseDelayMs) + baseDelayMs));
      console.error(`[RETRY BARRIER] Attempt ${attempt} failed: ${err.message}. Retrying in ${currentDelay}ms...`);
      await new Promise((resolve) => setTimeout(resolve, currentDelay));
    }
  }
  throw new Error("Unreachable retry threshold");
}
