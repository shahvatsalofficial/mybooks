// test_sliding_limiter.js — Exercise 2 Working Solution
const assert = require('assert');

class InMemorySlidingLimiter {
    constructor(limit = 10, windowMs = 1000) {
        this.limit = limit;
        this.windowMs = windowMs;
        this.timestamps = [];
    }

    tryAcquire() {
        const now = Date.now();
        const clearBefore = now - this.windowMs;
        this.timestamps = this.timestamps.filter(t => t > clearBefore);

        if (this.timestamps.length < this.limit) {
            this.timestamps.push(now);
            return { allowed: true, remaining: this.limit - this.timestamps.length };
        } else {
            const oldest = this.timestamps[0];
            const retryAfterSec = Math.ceil(((oldest + this.windowMs) - now) / 1000);
            return { allowed: false, remaining: 0, retryAfterSec: Math.max(1, retryAfterSec) };
        }
    }
}

// Execute 50 concurrent requests
const limiter = new InMemorySlidingLimiter(10, 2000);
let allowedCount = 0;
let deniedCount = 0;

for (let i = 0; i < 50; i++) {
    const res = limiter.tryAcquire();
    if (res.allowed) allowedCount++;
    else deniedCount++;
}

assert.strictEqual(allowedCount, 10, `Error: Expected exactly 10 allowed calls, got ${allowedCount}`);
assert.strictEqual(deniedCount, 40, `Error: Expected exactly 40 denied calls, got ${deniedCount}`);

console.log('Exercise 2 Verification: PASSED! Sliding Window Rate Limiter enforced exact 10/40 boundary.');
