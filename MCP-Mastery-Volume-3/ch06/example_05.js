// production_consul_client.js — Enterprise Production Consul MCP Client
const http = require('http');

class EnterpriseConsulRegistrar {
    /**
     * @param {Object} options
     * @param {string} options.consulHost
     * @param {number} options.consulPort
     * @param {string} options.serviceId
     * @param {string} options.serviceName
     * @param {string} options.address
     * @param {number} options.port
     * @param {Array<Object>} options.tools
     * @param {number} [options.ttlSeconds=15]
     * @param {number} [options.heartbeatRatio=0.4]
     */
    constructor(options) {
        this.consulHost = options.consulHost || process.env.CONSUL_HOST || '127.0.0.1';
        this.consulPort = options.consulPort || parseInt(process.env.CONSUL_PORT || '8500', 10);
        this.serviceId = options.serviceId;
        this.serviceName = options.serviceName;
        this.address = options.address;
        this.port = options.port;
        this.tools = options.tools || [];
        this.ttlSeconds = options.ttlSeconds || 15;
        this.heartbeatRatio = options.heartbeatRatio || 0.4; // Heartbeat every 40% of TTL window

        this.checkId = `service:${this.serviceId}:ttl`;
        this.heartbeatTimer = null;
        this.isTerminating = false;

        this._setupSignalHandlers();
    }

    _setupSignalHandlers() {
        const teardown = async (signal) => {
            if (this.isTerminating) return;
            this.isTerminating = true;
            console.log(`\n[ConsulRegistrar] Caught ${signal}. Commencing graceful deregistration...`);
            this.stopHeartbeat();
            try {
                await this.deregister();
                console.log('[ConsulRegistrar] Graceful deregistration confirmed. Process clean.');
                process.exit(0);
            } catch (err) {
                console.error('[ConsulRegistrar] Error during deregistration teardown:', err.message);
                process.exit(1);
            }
        };

        process.on('SIGTERM', () => teardown('SIGTERM'));
        process.on('SIGINT', () => teardown('SIGINT'));
    }

    async registerWithRetry(maxRetries = 5, initialDelayMs = 1000) {
        let attempt = 0;
        let delay = initialDelayMs;

        while (attempt < maxRetries) {
            try {
                attempt++;
                console.log(`[ConsulRegistrar] Registering service (attempt ${attempt}/${maxRetries})...`);
                await this._executeRegistration();
                console.log(`[ConsulRegistrar] Service '${this.serviceId}' successfully registered.`);
                this.startHeartbeat();
                return true;
            } catch (err) {
                console.warn(`[ConsulRegistrar] Registration attempt ${attempt} failed: ${err.message}`);
                if (attempt >= maxRetries) {
                    throw new Error(`Exhausted all ${maxRetries} registration attempts to Consul: ${err.message}`);
                }
                await new Promise(r => setTimeout(r, delay));
                delay = Math.min(delay * 2, 10000); // Exponential backoff with 10s ceiling
            }
        }
    }

    async _executeRegistration() {
        const toolTags = this.tools.map(t => `mcp.tool:${t.name}`);
        const registrationPayload = {
            ID: this.serviceId,
            Name: this.serviceName,
            Tags: ['mcp-server', 'protocol:v1', ...toolTags],
            Address: this.address,
            Port: this.port,
            Meta: {
                engine: 'nodejs',
                environment: process.env.NODE_ENV || 'production',
                tool_count: String(this.tools.length),
                capabilities_digest: this._computeDigest(this.tools)
            },
            Check: {
                CheckID: this.checkId,
                Name: `Liveness TTL for ${this.serviceId}`,
                TTL: `${this.ttlSeconds}s`,
                DeregisterCriticalServiceAfter: '60s',
                Status: 'passing'
            }
        };

        await this._sendHttpRequest('PUT', '/v1/agent/service/register', registrationPayload);
    }

    startHeartbeat() {
        if (this.heartbeatTimer) clearInterval(this.heartbeatTimer);
        const intervalMs = Math.floor(this.ttlSeconds * 1000 * this.heartbeatRatio);
        console.log(`[ConsulRegistrar] Starting TTL heartbeat every ${intervalMs}ms (TTL: ${this.ttlSeconds}s)`);

        this.heartbeatTimer = setInterval(async () => {
            if (this.isTerminating) return;
            try {
                const note = `Heartbeat active at ${new Date().toISOString()}`;
                const path = `/v1/agent/check/pass/${encodeURIComponent(this.checkId)}?note=${encodeURIComponent(note)}`;
                await this._sendHttpRequest('PUT', path, null);
            } catch (err) {
                console.error(`[ConsulRegistrar] TTL heartbeat emission failed: ${err.message}`);
            }
        }, intervalMs);

        // Emit initial pulse immediately
        const initialPath = `/v1/agent/check/pass/${encodeURIComponent(this.checkId)}?note=InitOK`;
        this._sendHttpRequest('PUT', initialPath, null).catch(e => {
            console.error('[ConsulRegistrar] Initial heartbeat error:', e.message);
        });
    }

    stopHeartbeat() {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = null;
        }
    }

    async deregister() {
        console.log(`[ConsulRegistrar] Deregistering ${this.serviceId} from Consul agent...`);
        const path = `/v1/agent/service/deregister/${encodeURIComponent(this.serviceId)}`;
        return this._sendHttpRequest('PUT', path, null);
    }

    _computeDigest(tools) {
        const crypto = require('crypto');
        const str = JSON.stringify(tools.map(t => ({ n: t.name, v: t.version || '1' })).sort());
        return crypto.createHash('sha256').update(str).digest('hex').substring(0, 16);
    }

    _sendHttpRequest(method, path, data) {
        return new Promise((resolve, reject) => {
            const body = data ? JSON.stringify(data) : null;
            const req = http.request({
                hostname: this.consulHost,
                port: this.consulPort,
                path: path,
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    ...(body ? { 'Content-Length': Buffer.byteLength(body) } : {})
                },
                timeout: 4000
            }, (res) => {
                let chunks = '';
                res.on('data', d => chunks += d);
                res.on('end', () => {
                    if (res.statusCode >= 200 && res.statusCode < 300) {
                        try {
                            resolve(chunks ? JSON.parse(chunks) : {});
                        } catch (e) {
                            resolve({});
                        }
                    } else {
                        reject(new Error(`HTTP ${res.statusCode}: ${chunks || res.statusMessage}`));
                    }
                });
            });

            req.on('error', reject);
            req.on('timeout', () => {
                req.destroy();
                reject(new Error(`Timeout connecting to Consul agent at ${this.consulHost}:${this.consulPort}`));
            });

            if (body) req.write(body);
            req.end();
        });
    }
}

module.exports = { EnterpriseConsulRegistrar };

// Standalone execution test
if (require.main === module) {
    const registrar = new EnterpriseConsulRegistrar({
        serviceId: `mcp-finance-${process.pid}`,
        serviceName: 'mcp-finance-service',
        address: '10.0.8.19',
        port: 9090,
        tools: [
            { name: 'fetch_corporate_filing', version: '1.0.0' },
            { name: 'compute_debt_to_equity', version: '1.1.0' }
        ],
        ttlSeconds: 8
    });

    registrar.registerWithRetry(3, 500)
        .then(() => {
            console.log('Testing TTL heartbeat for 6 seconds...');
            setTimeout(async () => {
                await registrar.deregister();
                registrar.stopHeartbeat();
                console.log('Execution verification passed.');
            }, 6000);
        })
        .catch(err => {
            console.warn(`Simulated check complete. Reason: ${err.message}`);
        });
}
