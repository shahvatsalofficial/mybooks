// solution_check_semver.js — Solution for Exercise 1
function inspectSemverCompliance(clientVersion, registeredVersions) {
  const versionMeta = registeredVersions[clientVersion];

  if (!versionMeta) {
    return {
      action: 'REJECT',
      statusCode: 400,
      rpcError: { code: -32000, message: `Unknown version: ${clientVersion}` }
    };
  }

  if (versionMeta.status === 'ACTIVE') {
    return {
      action: 'ALLOW',
      statusCode: 200,
      headers: {
        'X-MCP-Version': clientVersion
      }
    };
  }

  if (versionMeta.status === 'DEPRECATED') {
    return {
      action: 'ALLOW',
      statusCode: 200,
      headers: {
        'X-MCP-Version': clientVersion,
        'Deprecation': '@true',
        'Sunset': versionMeta.sunsetDate,
        'Link': `</tools/${versionMeta.tool}/v${versionMeta.successor}>; rel="successor-version"`,
        'Warning': `299 - "Version ${clientVersion} is deprecated and will sunset on ${versionMeta.sunsetDate}"`
      }
    };
  }

  if (versionMeta.status === 'EOL') {
    return {
      action: 'REJECT',
      statusCode: 410,
      headers: {
        'Link': `</tools/${versionMeta.tool}/v${versionMeta.successor}>; rel="successor-version"`
      },
      rpcError: {
        code: -32001,
        message: `Version ${clientVersion} is End-of-Life. Upgrade to ${versionMeta.successor}`
      }
    };
  }
}

// Verification Test Case
const REGISTRY_SAMPLE = {
  '1.0.0': { tool: 'crm:lookup', status: 'EOL', successor: '2.0.0' },
  '2.0.0': { tool: 'crm:lookup', status: 'DEPRECATED', sunsetDate: '2026-12-31T00:00:00Z', successor: '2.1.0' },
  '2.1.0': { tool: 'crm:lookup', status: 'ACTIVE' }
};

console.log('Test ACTIVE:', inspectSemverCompliance('2.1.0', REGISTRY_SAMPLE).action); // ALLOW
console.log('Test DEPRECATED Warning:', inspectSemverCompliance('2.0.0', REGISTRY_SAMPLE).headers.Warning);
console.log('Test EOL Status:', inspectSemverCompliance('1.0.0', REGISTRY_SAMPLE).statusCode); // 410
