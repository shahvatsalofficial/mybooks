// quick_tracer.js — Standalone W3C Trace Injector & Token Cost Meter
const crypto = require('crypto');

/**
 * W3C TraceContext Specification Implementation
 * Format: 00-{trace_id_32_hex}-{parent_span_id_16_hex}-{trace_flags_2_hex}
 */
class W3CTraceContext {
    static generate(sampled = true) {
        const traceId = crypto.randomBytes(16).toString('hex');
        const spanId = crypto.randomBytes(8).toString('hex');
        const flags = sampled ? '01' : '00';
        return `00-${traceId}-${spanId}-${flags}`;
    }

    static parse(header) {
        const parts = header.split('-');
        if (parts.length !== 4 || parts[0] !== '00') {
            throw new Error(`Invalid W3C traceparent header: ${header}`);
        }
        return {
            version: parts[0],
            traceId: parts[1],
            parentSpanId: parts[2],
            flags: parts[3],
            sampled: parts[3] === '01'
        };
    }

    static createChildSpan(parentHeader) {
        const parent = this.parse(parentHeader);
        const childSpanId = crypto.randomBytes(8).toString('hex');
        return {
            childHeader: `00-${parent.traceId}-${childSpanId}-${parent.flags}`,
            traceId: parent.traceId,
            spanId: childSpanId,
            parentSpanId: parent.parentSpanId
        };
    }
}

/**
 * Enterprise Token Cost Calculator
 */
class TokenCostMeter {
    static RATES = {
        'claude-3-5-sonnet': { inputPerM: 3.00, outputPerM: 15.00 },
        'gpt-4o': { inputPerM: 2.50, outputPerM: 10.00 },
        'gemini-1-5-pro': { inputPerM: 1.25, outputPerM: 5.00 }
    };

    static calculate(model, inputTokens, outputTokens) {
        const rate = this.RATES[model] || { inputPerM: 2.00, outputPerM: 8.00 };
        const inputCost = (inputTokens / 1_000_000) * rate.inputPerM;
        const outputCost = (outputTokens / 1_000_000) * rate.outputPerM;
        const totalCost = inputCost + outputCost;

        return {
            model,
            inputTokens,
            outputTokens,
            totalTokens: inputTokens + outputTokens,
            totalCostUsd: Number(totalCost.toFixed(6))
        };
    }
}

/**
 * Simulated Instrumented MCP Execution
 */
async function executeInstrumentedMcpCall(toolName, args, tenantId, model) {
    const rootTrace = W3CTraceContext.generate(true);
    const childSpan = W3CTraceContext.createChildSpan(rootTrace);
    const startTime = process.hrtime.bigint();

    console.log(`[INGRESS] Received request from tenant: ${tenantId}`);
    console.log(`[W3C TRACE] Root traceparent: ${rootTrace}`);
    console.log(`[W3C SPAN] Child span created for tool execution: ${childSpan.spanId}`);

    // Build standard MCP JSON-RPC request with OpenTelemetry metadata in _meta
    const mcpRequest = {
        jsonrpc: '2.0',
        id: crypto.randomUUID(),
        method: 'tools/call',
        params: {
            name: toolName,
            arguments: args,
            _meta: {
                traceparent: childSpan.childHeader,
                tenant_id: tenantId,
                model_invoker: model
            }
        }
    };

    console.log('\n[MCP PAYLOAD DISPATCH]:\n', JSON.stringify(mcpRequest, null, 2));

    // Simulate backend tool execution delay (e.g. database query)
    await new Promise((resolve) => setTimeout(resolve, 85));

    const endTime = process.hrtime.bigint();
    const durationMs = Number(endTime - startTime) / 1_000_000;

    // Simulate token accounting (prompt prefill + response injection)
    const simulatedInputTokens = 1420;
    const simulatedOutputTokens = 380;
    const financialReport = TokenCostMeter.calculate(model, simulatedInputTokens, simulatedOutputTokens);

    const telemetryReport = {
        traceId: childSpan.traceId,
        spanId: childSpan.spanId,
        tool: toolName,
        tenantId,
        durationMs: Number(durationMs.toFixed(2)),
        status: 'SUCCESS',
        financials: financialReport
    };

    return telemetryReport;
}

// ---------------------------------------------------------------------------
// Verification Run
// ---------------------------------------------------------------------------
(async () => {
    console.log('=== MCP OBSERVABILITY & TRACE PROPAGATION QUICK WIN ===\n');
    const result = await executeInstrumentedMcpCall(
        'query_enterprise_financials',
        { fiscal_year: 2026, quarter: 'Q3', ledger: 'EUR_OPS' },
        'tenant_acme_corp',
        'claude-3-5-sonnet'
    );

    console.log('\n[EMITTED TELEMETRY EVENT]:\n', JSON.stringify(result, null, 2));
    console.log(`\nVerification Check: Span latency ${result.durationMs}ms | Dollar cost: $${result.financials.totalCostUsd}`);
})();
