import { createClient } from "redis";
import crypto from "crypto";

export interface IdempotencyResult<T> {
  isDuplicate: boolean;
  result: T;
}

export class IdempotencyBarrier {
  private redis: ReturnType<typeof createClient>;
  private readonly defaultTtlSeconds: number;

  constructor(redisClient: ReturnType<typeof createClient>, defaultTtlSeconds = 3600) {
    this.redis = redisClient;
    this.defaultTtlSeconds = defaultTtlSeconds;
  }

  /**
   * Generates a deterministic hash from tool name and arguments.
   */
  public computeFingerprint(toolName: string, args: Record<string, unknown>, sessionId = "global"): string {
    // Sort keys to ensure deterministic serialization
    const sortedKeys = Object.keys(args).sort();
    const normalizedPayload = sortedKeys.map(k => [k, args[k]]);
    const rawString = `${sessionId}:${toolName}:${JSON.stringify(normalizedPayload)}`;
    return crypto.createHash("sha256").update(rawString).digest("hex");
  }

  /**
   * Executes an action with distributed locking and cached result replay.
   */
  public async executeWithBarrier<T>(
    idempotencyKey: string,
    action: () => Promise<T>
  ): Promise<IdempotencyResult<T>> {
    const lockKey = `lock:idempotency:${idempotencyKey}`;
    const dataKey = `data:idempotency:${idempotencyKey}`;

    // 1. Check if result already exists in cache
    const cachedData = await this.redis.get(dataKey);
    if (cachedData) {
      return {
        isDuplicate: true,
        result: JSON.parse(cachedData) as T
      };
    }

    // 2. Acquire distributed lock with 60s auto-expiry to prevent concurrent duplicate execution
    const acquired = await this.redis.set(lockKey, "LOCKED", {
      NX: true,
      EX: 60
    });

    if (!acquired) {
      // Another thread/process is currently executing this exact operation!
      throw new Error("OPERATION_IN_PROGRESS: Identical operation is currently processing. Please wait.");
    }

    try {
      // 3. Execute the actual underlying business logic
      const result = await action();

      // 4. Cache the serialized result
      await this.redis.set(dataKey, JSON.stringify(result), {
        EX: this.defaultTtlSeconds
      });

      return {
        isDuplicate: false,
        result
      };
    } finally {
      // 5. Release distributed execution lock
      await this.redis.del(lockKey);
    }
  }
}
