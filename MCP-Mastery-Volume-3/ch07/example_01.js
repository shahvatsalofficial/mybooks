// quick_semver_gateway.js — Standalone MCP SemVer Negotiation & Governance Interceptor
const http = require('http');

/**
 * Enterprise Tool Catalog with SemVer Lifecycle Definitions
 */
const TOOL_REGISTRY = {
  'crm:lookup_customer': {
    versions: {
      '1.0.0': {
        status: 'EOL',
        sunsetDate: '2026-01-01T00:00:00Z',
        successor: '2.0.0',
        schema: {
          type: 'object',
          properties: {
            custId: { type: 'string' }
          },
          required: ['custId']
        }
      },
      '2.0.0': {
        status: 'DEPRECATED',
        sunsetDate: '2026-12-31T23:59:59Z',
        successor: '2.1.0',
        schema: {
          type: 'object',
          properties: {
            customer_id: { type: 'string', pattern: '^CUST-[0-9]{6}$' }
          },
          required: ['customer_id']
        }
      },
      '2.1.0': {
        status: 'ACTIVE',
        schema: {
          type: 'object',
          properties: {
            customer_id: { type: 'string', pattern: '^CUST-[0-9]{6}$' },
            include_billing_history: { type: 'boolean', default: false }
          },
          required: ['customer_id']
        }
      }
    }
  }
};

/**
 * Minimal SemVer Comparator: Checks if version satisfies constraint
 */
function compareSemver(v1, v2) {
  const p1 = v1.split('.').map(Number);
  const p2 = v2.split('.').map(Number);
  for (let i = 0; i < 3; i++) {
    if (p1[i] > p2[i]) return 1;
    if (p1[i] < p2[i]) return -1;
  }
  return 0;
}

/**
 * Validates request arguments against tool JSON schema
 */
function validateSchema(schema, data) {
  if (schema.type === 'object') {
    if (typeof data !== 'object' || data === null) {
      return { valid: false, error: 'Expected object parameters' };
    }
    for (const req of schema.required || []) {
      if (!(req in data)) {
        return { valid: false, error: `Missing required parameter: '${req}'` };
      }
    }
    for (const [key, prop] of Object.entries(schema.properties || {})) {
      if (key in data) {
        if (prop.type === 'string' && typeof data[key] !== 'string') {
          return { valid: false, error: `Parameter '${key}' must be string` };
        }
        if (prop.pattern && !new RegExp(prop.pattern).test(data[key])) {
          return { valid: false, error: `Parameter '${key}' does not match pattern ${prop.pattern}` };
        }
        if (prop.type === 'boolean' && typeof data[key] !== 'boolean') {
          return { valid: false, error: `Parameter '${key}' must be boolean` };
        }
      }
    }
  }
  return { valid: true };
}

const server = http.createServer((req, res) => {
  if (req.method !== 'POST' || req.url !== '/mcp/v1') {
    res.writeHead(404, { 'Content-Type': 'application/json' });
    return res.end(JSON.stringify({ error: 'Endpoint not found' }));
  }

  let body = '';
  req.on('data', chunk => { body += chunk; });
  req.on('end', () => {
    let rpc;
    try {
      rpc = JSON.parse(body);
    } catch (err) {
      res.writeHead(400, { 'Content-Type': 'application/json' });
      return res.end(JSON.stringify({ jsonrpc: '2.0', id: null, error: { code: -32700, message: 'Parse error' } }));
    }

    const requestedVersion = req.headers['accept-mcp-version'] || '2.1.0';
    const clientApp = req.headers['x-client-application'] || 'unknown-agent';

    if (rpc.method === 'tools/call') {
      const toolName = rpc.params?.name;
      const toolDef = TOOL_REGISTRY[toolName];

      if (!toolDef) {
        res.writeHead(404, { 'Content-Type': 'application/json' });
        return res.end(JSON.stringify({
          jsonrpc: '2.0',
          id: rpc.id,
          error: { code: -32601, message: `Tool '${toolName}' not found in registry` }
        }));
      }

      // Check requested version availability
      const versionDef = toolDef.versions[requestedVersion];
      if (!versionDef) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        return res.end(JSON.stringify({
          jsonrpc: '2.0',
          id: rpc.id,
          error: { code: -32000, message: `Unsupported tool version: ${requestedVersion}` }
        }));
      }

      // Enforce Lifecycle Policy
      if (versionDef.status === 'EOL') {
        res.writeHead(410, {
          'Content-Type': 'application/json',
          'Link': `</mcp/v1/tools/${toolName}/v${versionDef.successor}>; rel="successor-version"`
        });
        return res.end(JSON.stringify({
          jsonrpc: '2.0',
          id: rpc.id,
          error: {
            code: -32001,
            message: `Version ${requestedVersion} is End-of-Life. Upgrade to ${versionDef.successor}`
          }
        }));
      }

      // Validate schema constraints
      const validation = validateSchema(versionDef.schema, rpc.params.arguments || {});
      if (!validation.valid) {
        res.writeHead(422, { 'Content-Type': 'application/json' });
        return res.end(JSON.stringify({
          jsonrpc: '2.0',
          id: rpc.id,
          error: { code: -32602, message: `Invalid params: ${validation.error}` }
        }));
      }

      // Build response headers with RFC 8594 deprecation tracking
      const responseHeaders = {
        'Content-Type': 'application/json',
        'X-MCP-Version': requestedVersion
      };

      if (versionDef.status === 'DEPRECATED') {
        responseHeaders['Deprecation'] = '@true';
        responseHeaders['Sunset'] = versionDef.sunsetDate;
        responseHeaders['Link'] = `</mcp/v1/tools/${toolName}/v${versionDef.successor}>; rel="successor-version"`;
        responseHeaders['Warning'] = `299 - "Tool schema version ${requestedVersion} is deprecated and will sunset on ${versionDef.sunsetDate}"`;
        console.warn(`[GOVERNANCE WARNING] Client '${clientApp}' invoked deprecated version ${requestedVersion} of '${toolName}'`);
      }

      res.writeHead(200, responseHeaders);
      return res.end(JSON.stringify({
        jsonrpc: '2.0',
        id: rpc.id,
        result: {
          status: 'success',
          data: {
            customerId: rpc.params.arguments.customer_id,
            name: 'Apex Global Enterprises',
            tier: 'Enterprise Platinum',
            versionExecuted: requestedVersion
          }
        }
      }));
    }

    res.writeHead(400, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ jsonrpc: '2.0', id: rpc.id, error: { code: -32600, message: 'Invalid Request' } }));
  });
});

server.listen(8080, () => {
  console.log('[MCP GOVERNANCE] SemVer Gateway active on port 8080');
});
