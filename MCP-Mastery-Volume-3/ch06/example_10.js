// exercise2_dynamic_registry.js — Working Solution for Exercise 2
const assert = require('assert');
const EventEmitter = require('events');

class InMemoryDynamicRegistry extends EventEmitter {
    constructor(debounceMs = 150) {
        super();
        this.debounceMs = debounceMs;
        this.services = new Map();
        this.debounceTimer = null;
        this.broadcastCount = 0;
    }

    register(serviceId, tools) {
        this.services.set(serviceId, { tools, updatedAt: Date.now() });
        this._triggerDebouncedBroadcast();
    }

    deregister(serviceId) {
        if (this.services.has(serviceId)) {
            this.services.delete(serviceId);
            this._triggerDebouncedBroadcast();
        }
    }

    getAggregatedTools() {
        const toolMap = new Map();
        for (const [, service] of this.services) {
            for (const tool of service.tools) {
                toolMap.set(tool.name, tool);
            }
        }
        return Array.from(toolMap.values());
    }

    _triggerDebouncedBroadcast() {
        if (this.debounceTimer) clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(() => {
            this.broadcastCount++;
            const tools = this.getAggregatedTools();
            this.emit('tools_changed', { broadcastId: this.broadcastCount, totalTools: tools.length });
        }, this.debounceMs);
    }
}

// Verification Test Harness
async function verifyExercise2() {
    console.log('Testing Exercise 2: Debounced Capability Broadcasting...');
    const registry = new InMemoryDynamicRegistry(100);

    let notificationReceived = 0;
    registry.on('tools_changed', (evt) => {
        notificationReceived++;
        console.log(`[Event Received] Broadcast #${evt.broadcastId} — Total Available Tools: ${evt.totalTools}`);
    });

    // Burst register 5 services within 30ms
    console.log('Registering 5 services in rapid succession...');
    registry.register('srv-1', [{ name: 'read_file' }]);
    registry.register('srv-2', [{ name: 'write_file' }]);
    registry.register('srv-3', [{ name: 'git_status' }]);
    registry.register('srv-4', [{ name: 'git_commit' }]);
    registry.register('srv-5', [{ name: 'run_tests' }]);

    // Wait 250ms for debounce timer to fire
    await new Promise(r => setTimeout(r, 250));

    // Assert that exactly 1 broadcast occurred despite 5 rapid registrations
    assert.strictEqual(notificationReceived, 1, `Expected exactly 1 broadcast, received ${notificationReceived}`);
    assert.strictEqual(registry.getAggregatedTools().length, 5, 'Expected 5 aggregated tools');

    console.log('✓ Exercise 2 PASSED! Debounce successfully coalesced burst registrations into 1 broadcast.');
}

verifyExercise2();
