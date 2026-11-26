// token_accountant.ts — Atomic Multi-Tenant Token Accounting Engine
import Redis from 'ioredis';

export interface TokenUsage {
    inputTokens: number;
    outputTokens: number;
    cachedInputTokens?: number;
}

export class TokenAccountant {
    private redis: Redis;

    // Rate card per 1,000,000 tokens in USD
    private static PRICING: Record<string, { input: number; output: number; cacheRead: number }> = {
        'claude-3-5-sonnet': { input: 3.00, output: 15.00, cacheRead: 0.30 },
        'gpt-4o': { input: 2.50, output: 10.00, cacheRead: 1.25 },
        'gemini-1-5-pro': { input: 1.25, output: 5.00, cacheRead: 0.3125 }
    };

    constructor(redisUrl: string = 'redis://127.0.0.1:6379') {
        this.redis = new Redis(redisUrl);
        this.registerLuaScript();
    }

    private registerLuaScript(): void {
        this.redis.defineCommand('recordTokenExpense', {
            numberOfKeys: 1,
            lua: `
                local tenantKey = KEYS[1]
                local costUsd = tonumber(ARGV[1])
                local tokenCount = tonumber(ARGV[2])
                local hardBudget = tonumber(ARGV[3])

                local currentCost = tonumber(redis.call('HGET', tenantKey, 'cost_usd') or '0')
                if hardBudget > 0 and (currentCost + costUsd) > hardBudget then
                    return -1 -- Quota exceeded
                end

                local newCost = redis.call('HINCRBYFLOAT', tenantKey, 'cost_usd', costUsd)
                redis.call('HINCRBY', tenantKey, 'tokens_total', tokenCount)
                return newCost
            `
        });
    }

    public calculateCostUsd(model: string, usage: TokenUsage): number {
        const rates = TokenAccountant.PRICING[model] || { input: 2.00, output: 8.00, cacheRead: 0.50 };
        const regularInput = usage.inputTokens - (usage.cachedInputTokens || 0);
        const inputCost = (regularInput / 1_000_000) * rates.input;
        const cacheCost = ((usage.cachedInputTokens || 0) / 1_000_000) * rates.cacheRead;
        const outputCost = (usage.outputTokens / 1_000_000) * rates.output;

        return Number((inputCost + cacheCost + outputCost).toFixed(6));
    }

    public async recordAndEnforceQuota(
        tenantId: string,
        model: string,
        usage: TokenUsage,
        hardMonthlyBudgetUsd: number = 5000.00
    ): Promise<{ allowed: boolean; newMonthlySpendUsd: number }> {
        const costUsd = this.calculateCostUsd(model, usage);
        const totalTokens = usage.inputTokens + usage.outputTokens;
        const dateKey = new Date().toISOString().slice(0, 7); // Format: YYYY-MM
        const tenantKey = `mcp:billing:${tenantId}:${dateKey}`;

        // Execute atomic Lua command
        const result = await (this.redis as any).recordTokenExpense(
            tenantKey,
            costUsd,
            totalTokens,
            hardMonthlyBudgetUsd
        );

        if (result === -1) {
            return { allowed: false, newMonthlySpendUsd: hardMonthlyBudgetUsd };
        }

        return { allowed: true, newMonthlySpendUsd: Number(result) };
    }
}
