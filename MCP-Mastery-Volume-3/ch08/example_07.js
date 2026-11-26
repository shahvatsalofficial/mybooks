/**
 * mcp_canary_analyzer.js — Automated Canary Analysis (ACA) for MCP Deployments
 * Collects latency metrics from Baseline and Canary versions, executes statistical
 * evaluation, and issues automated Canary Promotion or Automated Rollback directives.
 */

class McpCanaryAnalyzer {
    constructor(options = {}) {
        this.maxAllowedP99DegradationPercent = options.maxAllowedP99Degradation || 15.0; // Max 15% latency increase
        this.maxAllowedErrorRate = options.maxAllowedErrorRate || 0.02; // Max 2% error rate
    }

    /**
     * Calculates statistical percentiles (P50, P90, P99)
     */
    calculateStats(samples) {
        if (!samples || samples.length === 0) return { count: 0, p50: 0, p90: 0, p99: 0 };
        const sorted = [...samples].sort((a, b) => a - b);
        const p50 = sorted[Math.floor(sorted.length * 0.50)];
        const p90 = sorted[Math.floor(sorted.length * 0.90)];
        const p99 = sorted[Math.floor(sorted.length * 0.99)];
        return { count: sorted.length, p50, p90, p99 };
    }

    /**
     * Evaluates whether Canary meets acceptance criteria against Baseline
     */
    evaluateCanary(baselineLatencies, canaryLatencies, canaryErrors, totalCanaryCalls) {
        const baselineStats = this.calculateStats(baselineLatencies);
        const canaryStats = this.calculateStats(canaryLatencies);
        const canaryErrorRate = totalCanaryCalls > 0 ? (canaryErrors / totalCanaryCalls) : 0.0;

        const p99IncreasePercent = ((canaryStats.p99 - baselineStats.p99) / baselineStats.p99) * 100;

        console.log('===============================================================');
        console.log('[ACA-ENGINE] AUTOMATED CANARY ANALYSIS REPORT:');
        console.log(`  Baseline (n=${baselineStats.count}): P50=${baselineStats.p50}ms | P90=${baselineStats.p90}ms | P99=${baselineStats.p99}ms`);
        console.log(`  Canary   (n=${canaryStats.count}): P50=${canaryStats.p50}ms | P90=${canaryStats.p90}ms | P99=${canaryStats.p99}ms`);
        console.log(`  Canary Error Rate: ${(canaryErrorRate * 100).toFixed(2)}% (Threshold: ${(this.maxAllowedErrorRate * 100).toFixed(2)}%)`);
        console.log(`  Canary P99 Shift : ${p99IncreasePercent > 0 ? '+' : ''}${p99IncreasePercent.toFixed(1)}% (Threshold: +${this.maxAllowedP99DegradationPercent}%)`);
        console.log('===============================================================');

        // Decision logic
        if (canaryErrorRate > this.maxAllowedErrorRate) {
            return {
                verdict: 'ROLLBACK',
                reason: `Canary error rate (${(canaryErrorRate * 100).toFixed(2)}%) breached threshold.`
            };
        }

        if (p99IncreasePercent > this.maxAllowedP99DegradationPercent) {
            return {
                verdict: 'ROLLBACK',
                reason: `Canary P99 latency increased by ${p99IncreasePercent.toFixed(1)}%, exceeding limit of ${this.maxAllowedP99DegradationPercent}%.`
            };
        }

        return {
            verdict: 'PROMOTE',
            reason: 'Canary passed all statistical latency and error constraints.'
        };
    }
}

// ----------------------------------------------------------------------------
// Verification / Demonstration Runner
// ----------------------------------------------------------------------------
function runAcaVerification() {
    const analyzer = new McpCanaryAnalyzer();

    // Generate baseline latencies (Normal distribution ~45ms, P99 ~110ms)
    const baseline = Array.from({ length: 500 }, () => Math.floor(40 + Math.random() * 20));
    baseline.push(110, 115, 120); // Add tail

    // Scenario A: Canary with severe tail latency degradation (P99 ~280ms)
    console.log('--- Testing Degraded Canary Scenario ---');
    const degradedCanary = Array.from({ length: 500 }, () => Math.floor(42 + Math.random() * 25));
    degradedCanary.push(260, 275, 290); // Heavy tail degradation

    const resultA = analyzer.evaluateCanary(baseline, degradedCanary, 1, 503);
    console.log(`DECISION: ${resultA.verdict} | REASON: ${resultA.reason}\n`);

    // Scenario B: Healthy Canary matching baseline
    console.log('--- Testing Healthy Canary Scenario ---');
    const healthyCanary = Array.from({ length: 500 }, () => Math.floor(39 + Math.random() * 21));
    healthyCanary.push(108, 112, 118);

    const resultB = analyzer.evaluateCanary(baseline, healthyCanary, 0, 503);
    console.log(`DECISION: ${resultB.verdict} | REASON: ${resultB.reason}`);
}

runAcaVerification();
