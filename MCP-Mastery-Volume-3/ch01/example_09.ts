// test_circuit_breaker.test.ts — Native Node.js Automated Test Suite
import { test, describe, beforeEach, afterEach } from 'node:test';
import * as assert from 'node:assert/strict';
import * as http from 'node:http';
import { EnterpriseMCPGateway } from './enterprise_mcp_gateway';

describe('MCP Gateway Circuit Breaker State Machine Verification', () => {
    let mockWorker: http.Server;
    let gateway: EnterpriseMCPGateway;
    let shouldWorkerFail = false;
    let workerHitCount = 0;

    const WORKER_PORT = 9181;
    const GATEWAY_PORT = 9180;

    beforeEach(async () => {
        workerHitCount = 0;
        shouldWorkerFail = false;

        // Create mock upstream worker
        mockWorker = http.createServer((req, res) => {
            workerHitCount++;
            if (shouldWorkerFail) {
                res.writeHead(500, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ error: 'Internal Database Failure' }));
            } else {
                res.writeHead(200, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ jsonrpc: '2.0', id: 1, result: { output: 'success' } }));
            }
        });

        await new Promise<void>(resolve => mockWorker.listen(WORKER_PORT, resolve));

        gateway = new EnterpriseMCPGateway(GATEWAY_PORT);
        gateway.registerServer('test_ns', `http://127.0.0.1:${WORKER_PORT}`, [
            { name: 'test_ns.execute', description: 'Test tool', inputSchema: { type: 'object' } }
        ], 100);

        gateway.start();
    });

    afterEach(async () => {
        await new Promise<void>(resolve => mockWorker.close(() => resolve()));
        // Close gateway server
        (gateway as any).server.close();
    });

    test('Circuit transitions CLOSED -> OPEN after 5 consecutive upstream failures', async () => {
        shouldWorkerFail = true;

        // Trigger 5 consecutive failures to breach threshold
        for (let i = 0; i < 5; i++) {
            const res = await makeRpcCall(GATEWAY_PORT, 'test_ns.execute');
            assert.equal(res.status, 502, `Expected 502 Bad Gateway on attempt ${i + 1}`);
        }

        assert.equal(workerHitCount, 5, 'Upstream worker should have been called exactly 5 times');

        // 6th call should trip circuit breaker: Gateway must fast-fail 503 without hitting worker
        const trippedRes = await makeRpcCall(GATEWAY_PORT, 'test_ns.execute');
        assert.equal(trippedRes.status, 503, 'Tripped circuit breaker must return 503 Service Unavailable');
        assert.match(trippedRes.body.error.message, /Circuits Open/i);
        assert.equal(workerHitCount, 5, 'Worker hit count must remain 5 (Fast perimeter rejection)');
    });
});

async function makeRpcCall(port: number, toolName: string): Promise<{ status: number; body: any }> {
    return new Promise((resolve, reject) => {
        const payload = JSON.stringify({
            jsonrpc: '2.0',
            id: 1,
            method: 'tools/call',
            params: { name: toolName, arguments: {} }
        });

        const req = http.request({
            hostname: '127.0.0.1',
            port,
            path: '/mcp',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(payload)
            }
        }, res => {
            let data = '';
            res.on('data', chunk => { data += chunk; });
            res.on('end', () => {
                try {
                    resolve({ status: res.statusCode || 500, body: JSON.parse(data) });
                } catch {
                    resolve({ status: res.statusCode || 500, body: data });
                }
            });
        });

        req.on('error', reject);
        req.write(payload);
        req.end();
    });
}
