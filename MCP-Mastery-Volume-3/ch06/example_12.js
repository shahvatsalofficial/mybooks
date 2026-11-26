// exercise3_canary_router.js — Working Solution for Exercise 3
const assert = require('assert');

class MCPCanaryRouter {
    constructor(canaryWeightPercent = 20, errorThreshold = 2) {
        this.canaryWeightPercent = canaryWeightPercent;
        this.errorThreshold = errorThreshold;
        this.canaryErrors = 0;
        this.isRolledBack = false;
    }

    routeSession(sessionId) {
        if (this.isRolledBack || this.canaryWeightPercent <= 0) {
            return { version: 'v1.0.0-prod', isCanary: false };
        }

        // Deterministic hash of sessionId to 0-99
        let hash = 0;
        for (let i = 0; i < sessionId.length; i++) {
            hash = (hash << 5) - hash + sessionId.charCodeAt(i);
            hash |= 0;
        }
        const bucket = Math.abs(hash) % 100;

        if (bucket < this.canaryWeightPercent) {
            return { version: 'v1.1.0-canary', isCanary: true };
        }
        return { version: 'v1.0.0-prod', isCanary: false };
    }

    recordResult(isCanary, rpcResponse) {
        if (!isCanary) return;

        // Inspect for -32602 Invalid params schema errors
        if (rpcResponse && rpcResponse.error && rpcResponse.error.code === -32602) {
            this.canaryErrors++;
            console.warn(`[CanaryRouter] Schema error detected on Canary! Count: ${this.canaryErrors}/${this.errorThreshold}`);

            if (this.canaryErrors >= this.errorThreshold) {
                this.isRolledBack = true;
                this.canaryWeightPercent = 0;
                console.error('[CanaryRouter] CRITICAL: Error threshold breached! CANARY ROLLED BACK TO 0%.');
            }
        }
    }
}

// Verification Test Harness
function verifyExercise3() {
    console.log('Testing Exercise 3: Canary Router with Automated Error Rollback...');
    const router = new MCPCanaryRouter(50, 2); // 50% canary for testing, 2 error limit

    // Find a session ID that routes to Canary
    let canarySession = null;
    for (let i = 0; i < 100; i++) {
        const id = `session-agent-${i}`;
        if (router.routeSession(id).isCanary) {
            canarySession = id;
            break;
        }
    }
    assert(canarySession !== null, 'Failed finding canary session');

    // Verify initial routing
    const initialRoute = router.routeSession(canarySession);
    assert.strictEqual(initialRoute.version, 'v1.1.0-canary');
    console.log(`Session ${canarySession} routed to Canary.`);

    // Record error 1
    router.recordResult(true, { error: { code: -32602, message: 'Invalid params: extra field' } });
    assert.strictEqual(router.isRolledBack, false);

    // Record error 2 (Breaches threshold)
    router.recordResult(true, { error: { code: -32602, message: 'Invalid params: type mismatch' } });
    assert.strictEqual(router.isRolledBack, true, 'Router should have triggered rollback');

    // Verify session now re-routes to production v1.0.0
    const rolledBackRoute = router.routeSession(canarySession);
    assert.strictEqual(rolledBackRoute.version, 'v1.0.0-prod', 'Rolled back session must route to prod');

    console.log('✓ Exercise 3 PASSED! Router successfully executed automated safety rollback.');
}

verifyExercise3();
