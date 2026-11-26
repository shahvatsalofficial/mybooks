// solution_stretch_shadow.js — Solution for Exercise 3: Shadow Execution Proxy
const EventEmitter = require('events');

class ShadowTelemetry extends EventEmitter {}
const telemetry = new ShadowTelemetry();

telemetry.on('drift_detected', (event) => {
  console.error('[TELEMETRY ALERT] Schema Drift Detected in Candidate Version!');
  console.error(JSON.stringify(event, null, 2));
});

telemetry.on('shadow_success', (event) => {
  console.log(`[TELEMETRY] Shadow execution validated cleanly for tool '${event.tool}' (${event.latencyMs}ms)`);
});

function createShadowExecutionProxy(toolName, activeHandler, candidateHandler, argumentAdapter) {
  return async function handleToolInvocation(rpcParams, headers) {
    const startTime = Date.now();

    // 1. Execute canonical active handler synchronously for client response
    const activeResult = await activeHandler(rpcParams.arguments);

    // 2. Asynchronously fire-and-forget candidate shadow execution
    setImmediate(async () => {
      const shadowStart = Date.now();
      try {
        // Adapt arguments to new candidate schema structure if necessary
        const adaptedArgs = argumentAdapter ? argumentAdapter(rpcParams.arguments) : rpcParams.arguments;
        const candidateResult = await candidateHandler(adaptedArgs);
        const shadowDuration = Date.now() - shadowStart;

        // Perform structural type assertion comparison
        const activeKeys = Object.keys(activeResult).sort();
        const candidateKeys = Object.keys(candidateResult).sort();

        const missingInCandidate = activeKeys.filter(k => !(k in candidateResult));
        if (missingInCandidate.length > 0) {
          telemetry.emit('drift_detected', {
            tool: toolName,
            error: 'Candidate output is missing fields present in active output',
            missingKeys: missingInCandidate,
            activeResult,
            candidateResult
          });
          return;
        }

        // Compare types
        for (const key of activeKeys) {
          if (typeof activeResult[key] !== typeof candidateResult[key]) {
            telemetry.emit('drift_detected', {
              tool: toolName,
              error: `Type mismatch for key '${key}'`,
              expectedType: typeof activeResult[key],
              actualType: typeof candidateResult[key]
            });
            return;
          }
        }

        telemetry.emit('shadow_success', {
          tool: toolName,
          latencyMs: shadowDuration
        });
      } catch (err) {
        telemetry.emit('drift_detected', {
          tool: toolName,
          error: 'Candidate handler threw unhandled exception during shadow execution',
          exceptionMessage: err.message
        });
      }
    });

    // Return active result immediately to client
    return activeResult;
  };
}

// Verification Test Case
async function testShadowProxy() {
  const activeTool = async (args) => ({ account_id: args.id, balance: 1250.50, active: true });
  const faultyCandidateTool = async (args) => ({ account_id: args.id, balance: "1250.50" }); // Type mismatch: string balance

  const proxy = createShadowExecutionProxy('billing:get_balance', activeTool, faultyCandidateTool);

  console.log('[CLIENT] Invoking tool through shadow proxy...');
  const res = await proxy({ arguments: { id: 'ACC-992' } });
  console.log('[CLIENT] Received immediate response:', res);

  // Allow setImmediate queue to flush
  await new Promise(r => setTimeout(r, 100));
}

testShadowProxy();
