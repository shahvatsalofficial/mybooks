// enterprise_mcp_gateway.ts — Production-Grade Enterprise MCP Gateway
import * as http from 'http';
import * as url from 'url';

interface ToolDefinition {
    name: string;
    description: string;
    inputSchema: Record<string, any>;
}

interface UpstreamNode {
    id: string;
    url: string;
    weight: number;
    activeRequests: number;
    failureCount: number;
    lastFailureTimestamp: number;
    circuitState: 'CLOSED' | 'OPEN' | 'HALF_OPEN';
}

interface UpstreamPool {
    namespace: string;
    nodes: UpstreamNode[];
    tools: Map<string, ToolDefinition>;
}

export class EnterpriseMCPGateway {
    private pools: Map<string, UpstreamPool> = new Map();
    private server: http.Server;
    private readonly failureThreshold = 5;
    private readonly coolDownPeriodMs = 30000;

    constructor(private port: number) {
        this.server = http.createServer(this.handleRequest.bind(this));
    }

    public registerServer(namespace: string, nodeUrl: string, tools: ToolDefinition[], weight = 100): void {
        let pool = this.pools.get(namespace);
        if (!pool) {
            pool = { namespace, nodes: [], tools: new Map() };
            this.pools.set(namespace, pool);
        }

        const nodeId = `${namespace}_${Buffer.from(nodeUrl).toString('base64').slice(0, 8)}`;
        const existingNodeIndex = pool.nodes.findIndex(n => n.url === nodeUrl);

        const node: UpstreamNode = {
            id: nodeId,
            url: nodeUrl,
            weight,
            activeRequests: 0,
            failureCount: 0,
            lastFailureTimestamp: 0,
            circuitState: 'CLOSED'
        };

        if (existingNodeIndex >= 0) {
            pool.nodes[existingNodeIndex] = node;
        } else {
            pool.nodes.push(node);
        }

        for (const tool of tools) {
            pool.tools.set(tool.name, tool);
        }

        console.log(`[REGISTRY] Registered instance ${nodeId} under namespace "${namespace}" with ${tools.length} tools.`);
    }

    private selectNodeP2C(pool: UpstreamPool): UpstreamNode | null {
        const now = Date.now();
        const availableNodes = pool.nodes.filter(node => {
            if (node.circuitState === 'OPEN') {
                if (now - node.lastFailureTimestamp > this.coolDownPeriodMs) {
                    node.circuitState = 'HALF_OPEN';
                    return true;
                }
                return false;
            }
            return true;
        });

        if (availableNodes.length === 0) return null;
        if (availableNodes.length === 1) return availableNodes[0];

        // Power of Two Choices: Sample 2 random candidates
        const idx1 = Math.floor(Math.random() * availableNodes.length);
        let idx2 = Math.floor(Math.random() * availableNodes.length);
        while (idx2 === idx1) {
            idx2 = Math.floor(Math.random() * availableNodes.length);
        }

        const node1 = availableNodes[idx1];
        const node2 = availableNodes[idx2];

        // Pick candidate with lower in-flight requests relative to weight
        const score1 = node1.activeRequests / (node1.weight / 100);
        const score2 = node2.activeRequests / (node2.weight / 100);

        return score1 <= score2 ? node1 : node2;
    }

    private async handleRequest(req: http.IncomingMessage, res: http.ServerResponse): Promise<void> {
        if (req.method !== 'POST') {
            res.writeHead(405, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ error: 'Method Not Allowed' }));
            return;
        }

        let body = '';
        req.on('data', chunk => { body += chunk; });
        req.on('end', async () => {
            try {
                const rpc = JSON.parse(body);

                // Handle capability discovery: Synthesize unified tools/list across all pools
                if (rpc.method === 'tools/list') {
                    const aggregatedTools: ToolDefinition[] = [];
                    for (const pool of this.pools.values()) {
                        for (const tool of pool.tools.values()) {
                            aggregatedTools.push(tool);
                        }
                    }

                    res.writeHead(200, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({
                        jsonrpc: '2.0',
                        id: rpc.id,
                        result: { tools: aggregatedTools }
                    }));
                    return;
                }

                // Handle tool invocation: Namespace routing
                if (rpc.method === 'tools/call') {
                    const toolName: string = rpc.params?.name || '';
                    const namespace = toolName.includes('.') ? toolName.split('.')[0] : toolName.split('_')[0];
                    const pool = this.pools.get(namespace);

                    if (!pool) {
                        res.writeHead(404, { 'Content-Type': 'application/json' });
                        res.end(JSON.stringify({
                            jsonrpc: '2.0',
                            id: rpc.id,
                            error: { code: -32601, message: `Unknown tool namespace: ${namespace}` }
                        }));
                        return;
                    }

                    const targetNode = this.selectNodeP2C(pool);
                    if (!targetNode) {
                        res.writeHead(503, { 'Content-Type': 'application/json' });
                        res.end(JSON.stringify({
                            jsonrpc: '2.0',
                            id: rpc.id,
                            error: { code: -32603, message: `All upstream workers in "${namespace}" are unavailable (Circuits Open)` }
                        }));
                        return;
                    }

                    // Increment in-flight tracking
                    targetNode.activeRequests++;
                    const startTime = Date.now();

                    try {
                        const upstreamResponse = await this.forwardPayload(targetNode.url, body);
                        
                        // Execution success: reset failure counter
                        if (targetNode.circuitState === 'HALF_OPEN') {
                            targetNode.circuitState = 'CLOSED';
                            targetNode.failureCount = 0;
                        }

                        res.writeHead(200, { 'Content-Type': 'application/json' });
                        res.end(upstreamResponse);
                    } catch (error: any) {
                        targetNode.failureCount++;
                        targetNode.lastFailureTimestamp = Date.now();

                        if (targetNode.failureCount >= this.failureThreshold) {
                            targetNode.circuitState = 'OPEN';
                            console.error(`[CIRCUIT BREAKER] Tripped OPEN for node ${targetNode.id}. Consecutive failures: ${targetNode.failureCount}`);
                        }

                        res.writeHead(502, { 'Content-Type': 'application/json' });
                        res.end(JSON.stringify({
                            jsonrpc: '2.0',
                            id: rpc.id,
                            error: { code: -32603, message: `Upstream dispatch failure: ${error.message}` }
                        }));
                    } finally {
                        targetNode.activeRequests--;
                        const duration = Date.now() - startTime;
                        console.log(`[METRICS] Tool: ${toolName} | Node: ${targetNode.id} | Duration: ${duration}ms | Active: ${targetNode.activeRequests}`);
                    }
                    return;
                }

                // Default pass-through for initialize and ping
                res.writeHead(200, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ jsonrpc: '2.0', id: rpc.id, result: { status: 'healthy' } }));

            } catch (err: any) {
                res.writeHead(400, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ jsonrpc: '2.0', id: null, error: { code: -32700, message: 'Invalid JSON payload' } }));
            }
        });
    }

    private forwardPayload(targetUrl: string, payload: string): Promise<string> {
        return new Promise((resolve, reject) => {
            const parsed = url.parse(targetUrl);
            const req = http.request({
                hostname: parsed.hostname,
                port: parsed.port,
                path: parsed.path,
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Content-Length': Buffer.byteLength(payload)
                },
                timeout: 15000
            }, res => {
                let data = '';
                res.on('data', chunk => { data += chunk; });
                res.on('end', () => resolve(data));
            });

            req.on('error', reject);
            req.on('timeout', () => {
                req.destroy(new Error('Upstream timeout after 15000ms'));
            });

            req.write(payload);
            req.end();
        });
    }

    public start(): void {
        this.server.listen(this.port, () => {
            console.log(`[ENTERPRISE GATEWAY] Active and listening on port ${this.port}`);
        });
    }
}

// Module Execution Entrypoint
if (require.main === module) {
    const gateway = new EnterpriseMCPGateway(8080);

    // Register initial tool worker pools
    gateway.registerServer('postgres', 'http://127.0.0.1:8081/mcp', [
        { name: 'postgres.query', description: 'Run SQL Query', inputSchema: { type: 'object' } }
    ], 100);

    gateway.registerServer('k8s', 'http://127.0.0.1:8082/mcp', [
        { name: 'k8s.get_pods', description: 'List Kubernetes Pods', inputSchema: { type: 'object' } }
    ], 100);

    gateway.start();
}
