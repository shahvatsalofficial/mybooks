// resilient_router.ts — Multi-Provider Resilient MCP Router with Hedging
import { McpToolDefinition, SchemaTranspiler } from './schema_transpiler';

export type ProviderName = 'claude' | 'openai' | 'gemini';

export interface ProviderHealth {
    consecutiveFailures: number;
    circuitOpenUntil: number; // Unix timestamp ms
}

export class ResilientMcpRouter {
    private healthState: Map<ProviderName, ProviderHealth> = new Map([
        ['claude', { consecutiveFailures: 0, circuitOpenUntil: 0 }],
        ['openai', { consecutiveFailures: 0, circuitOpenUntil: 0 }],
        ['gemini', { consecutiveFailures: 0, circuitOpenUntil: 0 }]
    ]);

    constructor(
        private readonly hedgingDelayMs: number = 1500,
        private readonly circuitCooldownMs: number = 30000
    ) {}

    /**
     * Checks if a provider circuit is closed and healthy
     */
    public isAvailable(provider: ProviderName): boolean {
        const state = this.healthState.get(provider)!;
        if (Date.now() < state.circuitOpenUntil) {
            return false; // Circuit is OPEN
        }
        return true;
    }

    public recordSuccess(provider: ProviderName): void {
        const state = this.healthState.get(provider)!;
        state.consecutiveFailures = 0;
        state.circuitOpenUntil = 0;
    }

    public recordFailure(provider: ProviderName): void {
        const state = this.healthState.get(provider)!;
        state.consecutiveFailures++;
        if (state.consecutiveFailures >= 3) {
            state.circuitOpenUntil = Date.now() + this.circuitCooldownMs;
            console.warn(`[CIRCUIT BREAKER] Tripped OPEN for provider: ${provider}. Cooldown: ${this.circuitCooldownMs}ms`);
        }
    }

    /**
     * Executes prompt across providers with dynamic speculative hedging
     */
    public async dispatchWithHedging(
        prompt: string,
        tools: McpToolDefinition[],
        mockCaller: (provider: ProviderName, payload: any, signal: AbortSignal) => Promise<any>
    ): Promise<{ provider: ProviderName; response: any }> {
        const primary: ProviderName = this.isAvailable('claude') ? 'claude' : 'openai';
        const fallback: ProviderName = primary === 'claude' && this.isAvailable('openai') ? 'openai' : 'gemini';

        const primaryController = new AbortController();
        const fallbackController = new AbortController();

        const primaryPayload = this.preparePayload(primary, prompt, tools);
        const fallbackPayload = this.preparePayload(fallback, prompt, tools);

        console.log(`[ROUTER] Dispatching primary request to: ${primary}`);
        const primaryPromise = mockCaller(primary, primaryPayload, primaryController.signal)
            .then((res) => {
                this.recordSuccess(primary);
                fallbackController.abort(); // Cancel hedge
                return { provider: primary, response: res };
            })
            .catch((err) => {
                this.recordFailure(primary);
                throw err;
            });

        // Initialize speculative hedging timer
        const hedgeTimerPromise = new Promise<{ provider: ProviderName; response: any }>((_, reject) => {
            const timer = setTimeout(async () => {
                if (!fallbackController.signal.aborted) {
                    console.log(`[ROUTER] Hedging SLA reached (${this.hedgingDelayMs}ms). Firing speculative hedge to: ${fallback}`);
                    try {
                        const hedgeRes = await mockCaller(fallback, fallbackPayload, fallbackController.signal);
                        this.recordSuccess(fallback);
                        primaryController.abort(); // Cancel primary
                        _({ provider: fallback, response: hedgeRes });
                    } catch (hedgeErr) {
                        this.recordFailure(fallback);
                        reject(hedgeErr);
                    }
                }
            }, this.hedgingDelayMs);

            primaryPromise.finally(() => clearTimeout(timer));
        });

        return Promise.race([primaryPromise, hedgeTimerPromise]);
    }

    private preparePayload(provider: ProviderName, prompt: string, tools: McpToolDefinition[]): any {
        switch (provider) {
            case 'claude':
                return {
                    messages: [{ role: 'user', content: prompt }],
                    tools: tools.map((t) => SchemaTranspiler.toAnthropic(t))
                };
            case 'openai':
                return {
                    messages: [{ role: 'user', content: prompt }],
                    tools: tools.map((t) => SchemaTranspiler.toOpenAi(t))
                };
            case 'gemini':
                return {
                    contents: [{ role: 'user', parts: [{ text: prompt }] }],
                    tools: [{ functionDeclarations: tools.map((t) => SchemaTranspiler.toGemini(t)) }]
                };
        }
    }
}
