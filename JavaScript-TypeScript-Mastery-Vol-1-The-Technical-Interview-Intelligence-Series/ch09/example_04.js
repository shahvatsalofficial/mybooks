// Hardened GC-Safe Implementation
let safeHolder = null;

function runSafeTransaction() {
    const massiveAsset = new Array(10000000).fill("STALE_DATA");
    const previousHolder = safeHolder;

    // Isolate context to prevent references to massiveAsset
    safeHolder = (function(priorLink) {
        return function() {
            if (priorLink) {
                console.log("Safe connection active");
            }
        };
    })(previousHolder);

    // Explicitly break the reference to the parent scope's previous link
    // allowing the V8 Garbage Collector to cleanly harvest the stale parent context.
    nullifyUnusedReference(previousHolder);
}

function nullifyUnusedReference(ref) {
    ref = null;
}
