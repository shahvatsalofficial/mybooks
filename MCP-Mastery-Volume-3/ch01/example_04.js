// upstream_mtls_client.js — Cryptographically Secure Internal Dispatcher
const https = require('https');
const fs = require('fs');
const path = require('path');

class SecureUpstreamDispatcher {
    constructor(config) {
        // Load internal enterprise CA root and gateway identity certs
        this.caCert = fs.readFileSync(config.caCertPath);
        this.clientCert = fs.readFileSync(config.clientCertPath);
        this.clientKey = fs.readFileSync(config.clientKeyPath);

        // Dedicated HTTPS Agent enforcing Mutual TLS
        this.agent = new https.Agent({
            ca: this.caCert,
            cert: this.clientCert,
            key: this.clientKey,
            rejectUnauthorized: true, // Fatal error on invalid upstream certs
            checkServerIdentity: (host, cert) => {
                // Strict SPIFFE SAN validation
                const spiffeSan = cert.subjectaltname
                    ?.split(', ')
                    .find(san => san.startsWith('URI:spiffe://'));

                if (!spiffeSan || !spiffeSan.includes('/mcp/tool-servers/')) {
                    throw new Error(`Untrusted SPIFFE ID presented by upstream: ${spiffeSan}`);
                }
                return undefined; // Identity verification passed
            },
            keepAlive: true,
            maxSockets: 250,
            maxFreeSockets: 50,
            timeout: 30000
        });
    }

    async dispatchToolCall(targetUrl, jsonRpcBody, tenantContext) {
        return new Promise((resolve, reject) => {
            const parsedUrl = new URL(targetUrl);

            const options = {
                hostname: parsedUrl.hostname,
                port: parsedUrl.port || 443,
                path: parsedUrl.pathname,
                method: 'POST',
                agent: this.agent,
                headers: {
                    'Content-Type': 'application/json',
                    'Content-Length': Buffer.byteLength(jsonRpcBody),
                    'X-MCP-Tenant-ID': tenantContext.tenantId,
                    'X-MCP-Caller-Identity': tenantContext.callerSpiffeId,
                    'X-Correlation-ID': tenantContext.correlationId
                }
            };

            const req = https.request(options, (res) => {
                let responseData = '';
                res.on('data', chunk => { responseData += chunk; });
                res.on('end', () => {
                    if (res.statusCode >= 200 && res.statusCode < 300) {
                        resolve(JSON.parse(responseData));
                    } else {
                        reject(new Error(`Upstream returned HTTP ${res.statusCode}: ${responseData}`));
                    }
                });
            });

            req.on('error', (err) => {
                reject(new Error(`mTLS Transport Error to ${targetUrl}: ${err.message}`));
            });

            req.setTimeout(10000, () => {
                req.destroy(new Error(`Upstream connection timed out after 10000ms`));
            });

            req.write(jsonRpcBody);
            req.end();
        });
    }
}

module.exports = { SecureUpstreamDispatcher };
