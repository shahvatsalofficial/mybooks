// semantic_probe_engine.js — Enterprise Semantic Health Probe Engine
const EventEmitter = require('events');

class SemanticProbeEngine extends EventEmitter {
    /**
     * @param {Object} options
     * @param {Array<Object>} options.toolRegistry - List of registered tools with synthetic executors
     * @param {number} [options.probeIntervalMs=10000] - Probing frequency
     * @param {number} [options.timeoutMs=2500] - Timeout per tool probe
     * @param {number} [options.consecutiveFailureThreshold=3] - Failures before tripping
     */
    constructor(options) {
        super();
        this.toolRegistry = options.toolRegistry || [];
        this.probeIntervalMs = options.probeIntervalMs || 10000;
        this.timeoutMs = options.timeoutMs || 2500;
        this.consecutiveFailureThreshold = options.consecutiveFailureThreshold || 3;

        // Health state tracking per tool
        this.toolStates = new Map();
        this.isOverallHealthy = true;
        this.timer = null;

        this._initStates();
    }

    _initStates() {
        for (const tool of this.toolRegistry) {
            this.toolStates.set(tool.name, {
                consecutiveFailures: 0,
                lastLatencyMs: 0,
                lastChecked: null,
                lastError: null,
                healthy: true
            });
        }
    }

    start() {
        if (this.timer) clearInterval(this.timer);
        console.log(`[SemanticProbe] Starting probe engine across ${this.toolRegistry.length} tool(s)...`);
        
        // Execute initial probe immediately
        this.runProbeCycle();
        this.timer = setInterval(() => this.runProbeCycle(), this.probeIntervalMs);
    }

    stop() {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
    }

    async runProbeCycle() {
        const results = [];
        let anyToolFailed = false;

        for (const tool of this.toolRegistry) {
            const probeResult = await this._probeSingleTool(tool);
            results.push(probeResult);

            const state = this.toolStates.get(tool.name);
            state.lastChecked = new Date().toISOString();
            state.lastLatencyMs = probeResult.latencyMs;

            if (probeResult.success) {
                state.consecutiveFailures = 0;
                state.lastError = null;
                state.healthy = true;
            } else {
                state.consecutiveFailures++;
                state.lastError = probeResult.error;
                if (state.consecutiveFailures >= this.consecutiveFailureThreshold) {
                    state.healthy = false;
                    anyToolFailed = true;
                    console.error(`[SemanticProbe] TOOL CRITICAL: '${tool.name}' failed ${state.consecutiveFailures} consecutive checks!`);
                }
            }
        }

        const previousHealth = this.isOverallHealthy;
        this.isOverallHealthy = !anyToolFailed;

        if (previousHealth !== this.isOverallHealthy) {
            this.emit('healthChange', {
                healthy: this.isOverallHealthy,
                details: Object.fromEntries(this.toolStates)
            });
        }

        return {
            overallHealthy: this.isOverallHealthy,
            probedAt: new Date().toISOString(),
            toolResults: results
        };
    }

    async _probeSingleTool(tool) {
        const start = process.hrtime.bigint();
        try {
            const executePromise = tool.syntheticProbe();
            const timeoutPromise = new Promise((_, reject) => 
                setTimeout(() => reject(new Error(`Timeout after ${this.timeoutMs}ms`)), this.timeoutMs)
            );

            const output = await Promise.race([executePromise, timeoutPromise]);
            const elapsedMs = Number(process.hrtime.bigint() - start) / 1e6;

            // Validate that the output complies with expected contract
            if (tool.validateOutput && !tool.validateOutput(output)) {
                throw new Error('Synthetic output failed schema contract validation');
            }

            return {
                toolName: tool.name,
                success: true,
                latencyMs: Math.round(elapsedMs * 100) / 100
            };
        } catch (err) {
            const elapsedMs = Number(process.hrtime.bigint() - start) / 1e6;
            return {
                toolName: tool.name,
                success: false,
                latencyMs: Math.round(elapsedMs * 100) / 100,
                error: err.message
            };
        }
    }

    getStatusSummary() {
        return {
            status: this.isOverallHealthy ? 'HEALTHY' : 'UNHEALTHY',
            timestamp: new Date().toISOString(),
            tools: Object.fromEntries(this.toolStates)
        };
    }
}

module.exports = { SemanticProbeEngine };

// Verification Simulation
if (require.main === module) {
    // Define sample tools with synthetic probe executors
    let databaseOnline = true;

    const sampleTools = [
        {
            name: 'query_account_ledger',
            syntheticProbe: async () => {
                if (!databaseOnline) throw new Error('Database connection pool drained');
                return { dryRun: true, recordCount: 1 };
            },
            validateOutput: (res) => res && res.dryRun === true
        },
        {
            name: 'calculate_fx_spread',
            syntheticProbe: async () => {
                // Simulate fast in-memory mathematical calculation
                return { spreadBps: 1.25 };
            },
            validateOutput: (res) => typeof res.spreadBps === 'number'
        }
    ];

    const engine = new SemanticProbeEngine({
        toolRegistry: sampleTools,
        probeIntervalMs: 1500,
        consecutiveFailureThreshold: 2
    });

    engine.on('healthChange', (status) => {
        console.log(`\n[EVENT] Service Health Changed! Status Healthy = ${status.healthy}`);
    });

    engine.start();

    // Trigger failure simulation after 3 seconds
    setTimeout(() => {
        console.log('\n>>> SIMULATING OUTAGE: Dropping database connection pool... <<<');
        databaseOnline = false;
    }, 3200);

    // Restore health after 7 seconds
    setTimeout(() => {
        console.log('\n>>> RESTORING SERVICE: Database connection pool recovered... <<<');
        databaseOnline = true;
    }, 7000);

    // Terminate test
    setTimeout(() => {
        engine.stop();
        console.log('\nSemantic Probe test harness completed.');
    }, 10000);
}
