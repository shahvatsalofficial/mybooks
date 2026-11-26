#!/usr/bin/env node
/**
 * mcp_chaos_proxy.js — Enterprise MCP Chaos Engineering Proxy
 * Intercepts JSON-RPC 2.0 communication over stdio and injects configurable faults:
 * - Latency injection (Gaussian / Exponential jitter)
 * - Probabilistic packet/call drops (Simulating network drops & zombie processes)
 * - Schema corruption & payload mangling
 * - Synthetic JSON-RPC 2.0 error responses
 */

const { spawn } = require('child_process');
const readline = require('readline');

// ============================================================================
// Chaos Injection Configuration Profile
// ============================================================================
const CHAOS_CONFIG = {
    enabled: process.env.MCP_CHAOS_ENABLED === 'true',
    // Latency injection rules
    latency: {
        enabled: true,
        probability: 0.35,        // 35% of tool calls experience latency
        baseDelayMs: 1500,        // 1.5 second base delay
        jitterMaxMs: 4500,        // Up to an additional 4.5 seconds (simulates P99 spikes)
        targetMethods: ['tools/call']
    },
    // Probabilistic request drops
    drop: {
        enabled: true,
        probability: 0.10,        // 10% of tool calls dropped entirely (simulates hang)
        targetMethods: ['tools/call']
    },
    // Schema corruption faults
    corruptSchema: {
        enabled: false,           // Toggle to test client schema resilience
        probability: 0.20,
        targetMethods: ['tools/list']
    },
    // Synthetic error injection
    syntheticError: {
        enabled: true,
        probability: 0.15,        // 15% rate of synthetic JSON-RPC errors
        code: -32603,
        message: 'ChaosProxy: Injected synthetic downstream service failure',
        targetMethods: ['tools/call']
    }
};

// Parse command-line arguments to locate target MCP server
const args = process.argv.slice(2);
if (args.length === 0) {
    console.error('Usage: node mcp_chaos_proxy.js <target_command> [args...]');
    process.exit(1);
}

const targetCommand = args[0];
const targetArgs = args.slice(1);

// Spawn backend MCP server
const serverProcess = spawn(targetCommand, targetArgs, {
    stdio: ['pipe', 'pipe', 'inherit'],
    env: { ...process.env, CHAOS_PROXY_ACTIVE: 'true' }
});

serverProcess.on('exit', (code, signal) => {
    process.exit(code || 0);
});

// Setup line-by-line reading for JSON-RPC messages over stdio
const clientRl = readline.createInterface({ input: process.stdin, terminal: false });
const serverRl = readline.createInterface({ input: serverProcess.stdout, terminal: false });

/**
 * Calculates randomized delay with exponential jitter
 */
function calculateDelay() {
    const jitter = Math.floor(Math.random() * CHAOS_CONFIG.latency.jitterMaxMs);
    return CHAOS_CONFIG.latency.baseDelayMs + jitter;
}

/**
 * Evaluates whether a fault should fire based on configured probability
 */
function shouldInject(rule) {
    if (!CHAOS_CONFIG.enabled || !rule.enabled) return false;
    return Math.random() < rule.probability;
}

/**
 * Mutates tool list schemas to simulate upstream contract breaking changes
 */
function mutateToolSchemas(responseObj) {
    if (responseObj.result && Array.isArray(responseObj.result.tools)) {
        responseObj.result.tools = responseObj.result.tools.map(tool => {
            const mutated = { ...tool };
            // Corrupt parameter names or drop required properties
            if (mutated.inputSchema && mutated.inputSchema.properties) {
                const keys = Object.keys(mutated.inputSchema.properties);
                if (keys.length > 0) {
                    const targetKey = keys[0];
                    mutated.inputSchema.properties[`corrupted_${targetKey}`] = mutated.inputSchema.properties[targetKey];
                    delete mutated.inputSchema.properties[targetKey];
                }
            }
            return mutated;
        });
    }
    return responseObj;
}

// ----------------------------------------------------------------------------
// Client-to-Server Pipeline (Requests & Notifications)
// ----------------------------------------------------------------------------
clientRl.on('line', (line) => {
    if (!line.trim()) return;

    let message;
    try {
        message = JSON.parse(line);
    } catch (err) {
        // Pass unparseable data directly to backend
        serverProcess.stdin.write(line + '\n');
        return;
    }

    const method = message.method || '';

    // Check for dropped request fault
    if (CHAOS_CONFIG.drop.targetMethods.includes(method) && shouldInject(CHAOS_CONFIG.drop)) {
        process.stderr.write(`[CHAOS-PROXY] INJECTED FAULT: Dropped request id=${message.id} method=${method}\n`);
        // Intentionally drop request; do not forward to backend
        return;
    }

    // Check for synthetic error injection
    if (CHAOS_CONFIG.syntheticError.targetMethods.includes(method) && shouldInject(CHAOS_CONFIG.syntheticError)) {
        process.stderr.write(`[CHAOS-PROXY] INJECTED FAULT: Synthetic error for id=${message.id} method=${method}\n`);
        const errorResponse = {
            jsonrpc: '2.0',
            id: message.id,
            error: {
                code: CHAOS_CONFIG.syntheticError.code,
                message: CHAOS_CONFIG.syntheticError.message,
                data: { injectedBy: 'mcp_chaos_proxy.js', timestamp: new Date().toISOString() }
            }
        };
        process.stdout.write(JSON.stringify(errorResponse) + '\n');
        return;
    }

    // Check for latency injection
    if (CHAOS_CONFIG.latency.targetMethods.includes(method) && shouldInject(CHAOS_CONFIG.latency)) {
        const delay = calculateDelay();
        process.stderr.write(`[CHAOS-PROXY] INJECTED FAULT: Delaying request id=${message.id} by ${delay}ms\n`);
        setTimeout(() => {
            serverProcess.stdin.write(JSON.stringify(message) + '\n');
        }, delay);
        return;
    }

    // Normal forward
    serverProcess.stdin.write(JSON.stringify(message) + '\n');
});

// ----------------------------------------------------------------------------
// Server-to-Client Pipeline (Responses & Server Notifications)
// ----------------------------------------------------------------------------
serverRl.on('line', (line) => {
    if (!line.trim()) return;

    let message;
    try {
        message = JSON.parse(line);
    } catch (err) {
        process.stdout.write(line + '\n');
        return;
    }

    // Check for schema corruption on tools/list response
    if (shouldInject(CHAOS_CONFIG.corruptSchema) && message.result && message.result.tools) {
        process.stderr.write(`[CHAOS-PROXY] INJECTED FAULT: Corrupting tools/list schema payload\n`);
        const corrupted = mutateToolSchemas(message);
        process.stdout.write(JSON.stringify(corrupted) + '\n');
        return;
    }

    // Normal forward
    process.stdout.write(JSON.stringify(message) + '\n');
});
