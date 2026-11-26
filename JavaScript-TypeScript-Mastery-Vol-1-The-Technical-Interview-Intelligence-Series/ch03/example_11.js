// Vulnerable Implementation: Closure Reference Trap
function setupDiagnosticManager() {
    // A heavy array representing system metrics
    const massivePayload = new Array(5000000).fill('METRIC_DATA');
    
    return {
        // VULNERABILITY: This closure references massivePayload, keeping it alive in memory
        runQuickCheck: function() {
            if (massivePayload.length > 0) {
                return 'SYSTEM_OK';
            }
            return 'SYSTEM_FAILED';
        },
        
        // This closure does not reference massivePayload, but because it is declared
        // in the same lexical scope, it shares the same parent scope context object in memory
        getSystemUptime: function() {
            return Date.now();
        }
    };
}

// VULNERABILITY: Even if we only call getSystemUptime(), massivePayload remains in memory
const diagnostics = setupDiagnosticManager();
console.log(diagnostics.getSystemUptime());
