// Vulnerable Non-TCO Recursion (Fails on large input, throwing Stack Overflow)
function recursiveAccumulateBad(n) {
    if (n <= 1) return 1;
    return n + recursiveAccumulateBad(n - 1); // Not tail call: must perform addition AFTER return
}

// Hardened TCO Recursion (Safe)
"use strict";
function recursiveAccumulateOptimized(n, accumulator = 0) {
    if (n <= 0) return accumulator;
    return recursiveAccumulateOptimized(n - 1, accumulator + n); // Tail Call Position!
}
