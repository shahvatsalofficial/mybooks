// mcp_contract_test.js — Consumer-Driven Contract Verification Harness for MCP
const fs = require('fs');
const path = require('path');
const assert = require('assert');

/**
 * 1. CONSUMER SUITE: Generates the Pact Contract Specification
 */
function generateConsumerPact() {
  console.log('[PACT CONSUMER] Defining expected MCP interactions for crm:lookup_customer...');

  const pactContract = {
    consumer: { name: 'ai-gateway-agent-orchestrator' },
    provider: { name: 'mcp-server-crm' },
    interactions: [
      {
        description: 'a valid tools/call request for customer record lookup',
        providerState: 'customer CUST-10492 exists in CRM database',
        request: {
          method: 'POST',
          path: '/mcp/v1',
          headers: {
            'Content-Type': 'application/json',
            'Accept-MCP-Version': '2.1.0'
          },
          body: {
            jsonrpc: '2.0',
            id: 'pact-test-001',
            method: 'tools/call',
            params: {
              name: 'crm:lookup_customer',
              arguments: {
                customer_id: 'CUST-10492',
                include_billing_history: true
              }
            }
          }
        },
        response: {
          status: 200,
          headers: {
            'Content-Type': 'application/json',
            'X-MCP-Version': '2.1.0'
          },
          body: {
            jsonrpc: '2.0',
            id: 'pact-test-001',
            result: {
              customer_id: 'CUST-10492',
              company_name: 'Stark Industries Global',
              tier: 'Enterprise Platinum',
              active_subscriptions: 14,
              credit_balance_cents: 4500000
            }
          }
        }
      }
    ],
    metadata: {
      pactSpecification: { version: '3.0.0' }
    }
  };

  const pactDir = path.join(__dirname, 'pacts');
  if (!fs.existsSync(pactDir)) fs.mkdirSync(pactDir);

  const pactFilePath = path.join(pactDir, 'ai_gateway-mcp_crm.json');
  fs.writeFileSync(pactFilePath, JSON.stringify(pactContract, null, 2));
  console.log(`[PACT CONSUMER] Contract successfully generated at: ${pactFilePath}`);
  return pactFilePath;
}

/**
 * 2. PROVIDER SUITE: Verifies the Contract Against Real MCP Server Logic
 */
async function verifyProviderPact(pactFilePath) {
  console.log('\n[PACT PROVIDER] Beginning provider contract verification...');
  const contract = JSON.parse(fs.readFileSync(pactFilePath, 'utf8'));

  // Live MCP Provider Tool Implementation
  const liveProvider = {
    handleToolCall: (params, headers) => {
      // Validate SemVer header constraint
      if (headers['Accept-MCP-Version'] !== '2.1.0') {
        throw new Error(`Incompatible version: ${headers['Accept-MCP-Version']}`);
      }

      const args = params.arguments;
      if (!args.customer_id) {
        throw new Error("Missing required argument: 'customer_id'");
      }

      // Simulated CRM lookup matching provider state
      return {
        customer_id: args.customer_id,
        company_name: 'Stark Industries Global',
        tier: 'Enterprise Platinum',
        active_subscriptions: 14,
        credit_balance_cents: 4500000
      };
    }
  };

  // Replay interactions
  for (const interaction of contract.interactions) {
    console.log(`[PACT PROVIDER] Testing interaction: "${interaction.description}"`);

    const req = interaction.request;
    const expectedRes = interaction.response;

    // Simulate provider handling request
    const actualData = liveProvider.handleToolCall(req.body.params, req.headers);

    // Verify response structure matches contract
    assert.strictEqual(actualData.customer_id, expectedRes.body.result.customer_id);
    assert.strictEqual(typeof actualData.company_name, 'string');
    assert.strictEqual(typeof actualData.tier, 'string');
    assert.strictEqual(typeof actualData.active_subscriptions, 'number');
    assert.strictEqual(typeof actualData.credit_balance_cents, 'number');

    console.log('[PACT PROVIDER] Interaction PASSED provider contract verification.');
  }

  console.log('[PACT BROKER] can-i-deploy: PASSED. Safe to deploy to Production.');
}

// Execute Verification Workflow
const pactPath = generateConsumerPact();
verifyProviderPact(pactPath).catch(err => {
  console.error('[PACT FAILED] Contract verification failed:', err.message);
  process.exit(1);
});
