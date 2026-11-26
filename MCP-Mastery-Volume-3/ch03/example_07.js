// test_trace_repair.js — Exercise 2 Working Solution
const assert = require('assert');
const crypto = require('crypto');

function sanitizeOrGenerateTraceContext(rawHeader) {
    const w3cRegex = /^00-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$/;
    if (rawHeader && w3cRegex.test(rawHeader)) {
        const matches = rawHeader.match(w3cRegex);
        return {
            traceparent: rawHeader,
            traceId: matches[1],
            spanId: matches[2],
            isRegenerated: false
        };
    }

    // Malformed or missing: generate fresh valid W3C header
    const newTraceId = crypto.randomBytes(16).toString('hex');
    const newSpanId = crypto.randomBytes(8).toString('hex');
    const validHeader = `00-${newTraceId}-${newSpanId}-01`;

    return {
        traceparent: validHeader,
        traceId: newTraceId,
        spanId: newSpanId,
        isRegenerated: true
    };
}

// 1. Test invalid trace header
const badHeader = 'invalid-legacy-trace-string-999';
const result1 = sanitizeOrGenerateTraceContext(badHeader);
assert.strictEqual(result1.isRegenerated, true, 'Error: Malformed header must be regenerated');
assert.strictEqual(result1.traceId.length, 32, 'Error: Trace ID must be 32 hex characters');

// 2. Test valid W3C header
const goodHeader = '00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01';
const result2 = sanitizeOrGenerateTraceContext(goodHeader);
assert.strictEqual(result2.isRegenerated, false, 'Error: Valid header must be preserved');
assert.strictEqual(result2.traceId, '4bf92f3577b34da6a3ce929d0e0e4736');

console.log('Exercise 2 Verification: PASSED! W3C TraceContext Sanitizer functioning perfectly.');
