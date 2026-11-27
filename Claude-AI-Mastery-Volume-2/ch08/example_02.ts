/**
 * Recipe 08.2: Enterprise Three-State Circuit Breaker with Decorrelated Jitter
 * Author: Vatsal Shah (Vatsal Shah)
 * License: Apache-2.0
 */

export enum CircuitState {
  CLOSED = 'CLOSED',       // Normal healthy execution
  OPEN = 'OPEN',           // Tripped; failing fast locally
  HALF_OPEN = 'HALF_OPEN', // Probing upstream canary recovery
}

export class ClaudeCircuitBreaker {
  private state: CircuitState = CircuitState.CLOSED;
  private consecutiveFailures: number = 0;
  private consecutiveSuccesses: number = 0;
  private readonly failureThreshold: number;
  private readonly recoveryThreshold: number;
  private readonly resetTimeoutMs: number;
  private nextProbeTimestamp: number = 0;
  private lastSleepMs: number = 1000;

  constructor(failureThreshold = 5, recoveryThreshold = 3, resetTimeoutMs = 30000) {
    this.failureThreshold = failureThreshold;
    this.recoveryThreshold = recoveryThreshold;
    this.resetTimeoutMs = resetTimeoutMs;
  }

  public getState(): CircuitState {
    return this.state;
  }

  public canExecute(): boolean {
    const now = Date.now();
    if (this.state === CircuitState.OPEN) {
      if (now >= this.nextProbeTimestamp) {
        console.warn('[CIRCUIT BREAKER] Transitioning to HALF_OPEN to dispatch canary request.');
        this.state = CircuitState.HALF_OPEN;
        return true;
      }
      return false; // Fail fast locally to protect upstream and internal threads
    }
    return true;
  }

  public recordSuccess(): void {
    if (this.state === CircuitState.HALF_OPEN) {
      this.consecutiveSuccesses += 1;
      console.log(`[CIRCUIT BREAKER] Canary probe succeeded (${this.consecutiveSuccesses}/${this.recoveryThreshold}).`);
      if (this.consecutiveSuccesses >= this.recoveryThreshold) {
        this.state = CircuitState.CLOSED;
        this.consecutiveFailures = 0;
        this.consecutiveSuccesses = 0;
        this.lastSleepMs = 1000;
        console.log('[CIRCUIT BREAKER] Upstream fully verified healthy. Resetting to CLOSED.');
      }
    } else {
      this.consecutiveFailures = 0;
    }
  }

  public recordFailure(is5xxOr529: boolean): void {
    if (!is5xxOr529) return;

    this.consecutiveFailures += 1;
    this.consecutiveSuccesses = 0;
    console.error(`[CIRCUIT BREAKER] Consecutive upstream failure recorded: ${this.consecutiveFailures}/${this.failureThreshold}`);

    if (this.consecutiveFailures >= this.failureThreshold || this.state === CircuitState.HALF_OPEN) {
      this.state = CircuitState.OPEN;
      this.nextProbeTimestamp = Date.now() + this.resetTimeoutMs;
      console.error(`[CIRCUIT BREAKER] Breaker TRIPPED to OPEN! Failing fast locally for next ${this.resetTimeoutMs / 1000}s.`);
    }
  }

  public getDecorrelatedJitterSleepMs(attempt: number, baseMs = 1000, capMs = 30000): number {
    // Formula: min(cap, uniform(base, last_sleep * 3))
    const maxSleep = Math.min(capMs, this.lastSleepMs * 3);
    const sleep = baseMs + Math.random() * (maxSleep - baseMs);
    this.lastSleepMs = Math.floor(sleep);
    return this.lastSleepMs;
  }
}
