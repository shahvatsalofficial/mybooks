// minimal_gateway.js — Lightweight MCP Routing Reverse Proxy
const http = require('http');
const url = require('url');

// Static routing table mapping tool prefixes to backend port locations
const ROUTING_TABLE = {
    'db': 'http://127.0.0.1:8081',
    'k8s': 'http://127.0.0.1:8082',
    'git': 'http://127.0.0.1:8083'
};

const DEFAULT_BACKEND = 'http://127.0.0.1:8081';

const server = http.createServer(async (req, res) => {
    const parsedUrl = url.parse(req.url, true);

    // Only process POST requests carrying JSON-RPC payloads
    if (req.method !== 'POST') {
        res.writeHead(405, { 'Content-Type': 'application/json' });
        return res.end(JSON.stringify({ error: 'Method Not Allowed' }));
    }

    let rawBody = '';
    req.on('data', chunk => { rawBody += chunk; });
    req.on('end', async () => {
        try {
            const jsonRpcPayload = JSON.parse(rawBody);
            let targetBackend = DEFAULT_BACKEND;

            // Inspect tool invocation method
            if (jsonRpcPayload.method === 'tools/call') {
                const toolName = jsonRpcPayload.params?.name || '';
                const prefix = toolName.split('_')[0]; // e.g. "db_query" -> "db"
                if (ROUTING_TABLE[prefix]) {
                    targetBackend = ROUTING_TABLE[prefix];
                }
            }

            console.log(`[GATEWAY ROUTE] Method: ${jsonRpcPayload.method} | Target: ${targetBackend}`);

            // Proxy the payload to the designated upstream backend
            const backendUrl = new URL(req.url, targetBackend);
            const upstreamReq = http.request(backendUrl, {
                method: 'POST',
                headers: {
                    ...req.headers,
                    'host': backendUrl.host,
                    'x-forwarded-for': req.socket.remoteAddress,
                    'x-mcp-gateway': 'v1.0'
                }
            }, (upstreamRes) => {
                res.writeHead(upstreamRes.statusCode, upstreamRes.headers);
                upstreamRes.pipe(res);
            });

            upstreamReq.on('error', (err) => {
                res.writeHead(502, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({
                    jsonrpc: '2.0',
                    id: jsonRpcPayload.id || null,
                    error: { code: -32603, message: `Upstream gateway error: ${err.message}` }
                }));
            });

            upstreamReq.write(rawBody);
            upstreamReq.end();

        } catch (parseError) {
            res.writeHead(400, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({
                jsonrpc: '2.0',
                id: null,
                error: { code: -32700, message: 'Parse error: Invalid JSON payload' }
            }));
        }
    });
});

const PORT = 8080;
server.listen(PORT, () => {
    console.log(`[MCP GATEWAY] Ingress reverse proxy active on http://127.0.0.1:${PORT}`);
});
