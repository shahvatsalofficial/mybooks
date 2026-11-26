// sse_capability_broadcast_hub.js — Enterprise SSE Dynamic Capability Hub
const http = require('http');
const EventEmitter = require('events');

class DynamicCapabilityHub extends EventEmitter {
    /**
     * @param {Object} options
     * @param {number} [options.port=8080]
     * @param {number} [options.debounceWindowMs=500] - Coalesce rapid registry updates
     * @param {number} [options.keepAliveIntervalMs=15000] - SSE ping interval
     */
    constructor(options = {}) {
        super();
        this.port = options.port || 8080;
        this.debounceWindowMs = options.debounceWindowMs || 500;
        this.keepAliveIntervalMs = options.keepAliveIntervalMs || 15000;

        // Connected agent client SSE responses
        this.activeClients = new Map();
        this.clientIdCounter = 0;

        // Aggregated tool registry state
        this.currentTools = new Map();
        this.debounceTimer = null;
        this.keepAliveTimer = null;
        this.server = null;
    }

    start() {
        this.server = http.createServer((req, res) => this._handleRequest(req, res));
        this.server.listen(this.port, () => {
            console.log(`[SSE-Hub] Dynamic Capability Broadcast Hub listening on port ${this.port}`);
            this._startKeepAlives();
        });
    }

    stop() {
        if (this.keepAliveTimer) clearInterval(this.keepAliveTimer);
        if (this.debounceTimer) clearTimeout(this.debounceTimer);
        for (const [id, client] of this.activeClients) {
            client.res.end();
        }
        this.activeClients.clear();
        if (this.server) this.server.close();
    }

    _handleRequest(req, res) {
        const url = new URL(req.url, `http://${req.headers.host}`);

        // SSE Subscription Endpoint for Agents & IDEs
        if (url.pathname === '/sse' && req.method === 'GET') {
            const clientId = ++this.clientIdCounter;
            res.writeHead(200, {
                'Content-Type': 'text/event-stream',
                'Cache-Control': 'no-cache, no-transform',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no', // Disable proxy buffering (Nginx)
                'Access-Control-Allow-Origin': '*'
            });

            // Initial connection acknowledgment
            res.write(`event: endpoint\ndata: /message?sessionId=${clientId}\n\n`);
            this.activeClients.set(clientId, { res, connectedAt: new Date() });
            console.log(`[SSE-Hub] Agent connected (Client ID: ${clientId}). Total active: ${this.activeClients.size}`);

            req.on('close', () => {
                this.activeClients.delete(clientId);
                console.log(`[SSE-Hub] Agent disconnected (Client ID: ${clientId}). Remaining: ${this.activeClients.size}`);
            });
            return;
        }

        // Tools List Endpoint
        if (url.pathname === '/tools' && req.method === 'GET') {
            const toolList = Array.from(this.currentTools.values());
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ tools: toolList }));
            return;
        }

        res.writeHead(404, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Not Found' }));
    }

    // Called when Service Registry signals tool addition or removal
    onRegistryUpdate(incomingTools) {
        // Update local cache
        this.currentTools.clear();
        for (const tool of incomingTools) {
            this.currentTools.set(tool.name, tool);
        }

        // Debounce broadcast to coalesce bursts of container registrations
        if (this.debounceTimer) clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(() => {
            this._broadcastCapabilityChange();
        }, this.debounceWindowMs);
    }

    _broadcastCapabilityChange() {
        if (this.activeClients.size === 0) {
            console.log('[SSE-Hub] Capability change detected, but 0 active agents connected.');
            return;
        }

        const notificationPayload = JSON.stringify({
            jsonrpc: '2.0',
            method: 'notifications/tools/list_changed',
            params: {}
        });

        const sseFrame = `event: message\ndata: ${notificationPayload}\n\n`;
        console.log(`[SSE-Hub] Broadcasting 'notifications/tools/list_changed' to ${this.activeClients.size} agent(s)...`);

        for (const [id, client] of this.activeClients) {
            try {
                client.res.write(sseFrame);
            } catch (err) {
                console.error(`[SSE-Hub] Failed writing to Client ${id}:`, err.message);
                this.activeClients.delete(id);
            }
        }
    }

    _startKeepAlives() {
        this.keepAliveTimer = setInterval(() => {
            // High-efficiency SSE comment line ping
            const pingFrame = ': keepalive\n\n';
            for (const [id, client] of this.activeClients) {
                try {
                    client.res.write(pingFrame);
                } catch (e) {
                    this.activeClients.delete(id);
                }
            }
        }, this.keepAliveIntervalMs);
    }
}

module.exports = { DynamicCapabilityHub };

// Standalone Verification Harness
if (require.main === module) {
    const hub = new DynamicCapabilityHub({ port: 8991, debounceWindowMs: 200 });
    hub.start();

    // Simulate Agent Client connecting over SSE
    const clientReq = http.request({
        hostname: '127.0.0.1',
        port: 8991,
        path: '/sse',
        method: 'GET'
    }, (res) => {
        console.log('[Client-Sim] Connected to SSE Stream. Status:', res.statusCode);
        res.on('data', (chunk) => {
            const text = chunk.toString();
            console.log('[Client-Sim] Received Raw Stream Event:\n' + text.trim());
            if (text.includes('notifications/tools/list_changed')) {
                console.log('✓ SUCCESS: Client received dynamic capability update notification!');
            }
        });
    });
    clientReq.end();

    // Simulate Consul Registry update after 1 second
    setTimeout(() => {
        console.log('\n>>> Simulating Registry Event: New Tool Server Registered <<<');
        hub.onRegistryUpdate([
            { name: 'execute_sql_query', description: 'Run read-only database analytics' },
            { name: 'purge_cache_key', description: 'Evict stale Redis keys' }
        ]);
    }, 1000);

    // Clean shutdown after 2.5 seconds
    setTimeout(() => {
        hub.stop();
        console.log('Verification test complete.');
    }, 2500);
}
