/**
 * resilient_mcp_client.js — Enterprise MCP Resilient Client Wrapper
 * Implements: Execution deadlines, Decorrelated Jitter Backoff, and Circuit Breakers
 */

class CircuitBreakerOpenError extends Error {
    constructor(message) {
        super(message);
        this.name = 'CircuitBreakerOpenError';
    }
}

class ResilientMcpClient {
    constructor(targetCaller, options = {}) {
        this.caller = targetCaller; // Async function invoking actual MCP tool
        this.timeoutMs = options.timeoutMs || 3000;
        this.maxRetries = options.maxRetries || 3;
        this.baseBackoffMs = options.baseBackoffMs || 200;
        this.maxBackoffMs = options.maxBackoffMs || 2000;

        // Circuit Breaker State
        this.state = 'CLOSED'; // CLOSED, OPEN, HALF_OPEN
        this.failureCount = 0;
        this.failureThreshold = options.failureThreshold || 3;
        this.cooldownPeriodMs = options.cooldownPeriodMs || 10000;
        this.lastStateChange = Date.now();
    }

    /**
     * Executes tool call wrapped in circuit breaker, deadline, and jittered retries
     */
    async executeToolCall(toolName, params) {
        this.checkCircuitState();

        let attempt = 0;
        while (attempt <= this.maxRetries) {
            try {
                const result = await this.executeWithTimeout(toolName, params, this.timeoutMs);
                this.onSuccess();
                return result;
            } catch (err) {
                attempt++;
                this.onFailure(err);

                if (attempt > this.maxRetries || this.state === 'OPEN') {
                    throw err;
                }

                // Calculate Decorrelated Full Jitter delay
                const delay = this.calculateJitterDelay(attempt);
                console.warn(`[CLIENT-RESILIENCE] Tool '${toolName}' failed (${err.message}). Retrying in ${delay}ms (Attempt ${attempt}/${this.maxRetries})...`);
                await new Promise(resolve => setTimeout(resolve, delay));
            }
        }
    }

    executeWithTimeout(toolName, params, timeoutMs) {
        return new Promise((resolve, reject) => {
            const timer = setTimeout(() => {
                reject(new Error(`Execution deadline exceeded (${timeoutMs}ms) for tool '${toolName}'`));
            }, timeoutMs);

            this.caller(toolName, params)
                .then(res => { clearTimeout(timer); resolve(res); })
                .catch(err => { clearTimeout(timer); reject(err); });
        });
    }

    calculateJitterDelay(attempt) {
        const exponentialMax = Math.min(this.maxBackoffMs, this.baseBackoffMs * Math.pow(2, attempt));
        return Math.floor(Math.random() * exponentialMax); // Full Jitter
    }

    checkCircuitState() {
        if (this.state === 'OPEN') {
            if (Date.now() - this.lastStateChange > this.cooldownPeriodMs) {
                this.state = 'HALF_OPEN';
                this.lastStateChange = Date.now();
                console.info('[CIRCUIT-BREAKER] Cooldown elapsed. Transitioning from OPEN to HALF_OPEN.');
            } else {
                throw new CircuitBreakerOpenError('[CIRCUIT-BREAKER] Request rejected: Circuit is OPEN.');
            }
        }
    }

    onSuccess() {
        this.failureCount = 0;
        if (this.state === 'HALF_OPEN') {
            this.state = 'CLOSED';
            this.lastStateChange = Date.now();
            console.info('[CIRCUIT-BREAKER] Trial call succeeded. Transitioning from HALF_OPEN to CLOSED.');
        }
    }

    onFailure(err) {
        this.failureCount++;
        if (this.state === 'HALF_OPEN' || this.failureCount >= this.failureThreshold) {
            this.state = 'OPEN';
            this.lastStateChange = Date.now();
            console.error(`[CIRCUIT-BREAKER] Failure threshold reached (${this.failureCount}). Circuit transitioned to OPEN!`);
        }
    }
}

// ----------------------------------------------------------------------------
// Verification / Demonstration Runner
// ----------------------------------------------------------------------------
async function runVerification() {
    console.log('--- Testing Resilient MCP Client Wrapper ---');

    // Simulated flaky tool that fails on first 2 calls, succeeds on 3rd
    let invocationCounter = 0;
    const flakyToolCaller = async (name, params) => {
        invocationCounter++;
        if (invocationCounter < 3) {
            throw new Error('Simulated transient 503 database lock');
        }
        return { status: 'success', data: { rowsProcessed: 42 } };
    };

    const client = new ResilientMcpClient(flakyToolCaller);

    try {
        const response = await client.executeToolCall('query_records', { limit: 10 });
        console.log('Result received successfully:', response);
    } catch (err) {
        console.error('Call failed permanently:', err.message);
    }
}

runVerification();
