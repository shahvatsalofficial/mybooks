// test_merkle_tamper.js — Exercise 2 Working Solution
const assert = require('assert');
const crypto = require('crypto');

function sha256(buf) {
    return crypto.createHash('sha256').update(buf).digest();
}

function computeMerkleRoot(events) {
    const leaves = events.map(e => sha256(JSON.stringify(e)));
    const h01 = sha256(Buffer.concat([leaves[0], leaves[1]]));
    const h23 = sha256(Buffer.concat([leaves[2], leaves[3]]));
    return sha256(Buffer.concat([h01, h23])).toString('hex');
}

// 1. Generate Ed25519 Keys
const { publicKey, privateKey } = crypto.generateKeyPairSync('ed25519');

// 2. Original Events
const events = [
    { id: 1, action: 'TOOL_INGRESS', tool: 'db:query' },
    { id: 2, action: 'POLICY_DECISION', allowed: true },
    { id: 3, action: 'VAULT_LEASE', leaseId: 'v-1234' },
    { id: 4, action: 'EXECUTION_RESULT', rows: 42 }
];

const originalRoot = computeMerkleRoot(events);
const signature = crypto.sign(null, Buffer.from(originalRoot, 'hex'), privateKey);

// Assert valid signature on untampered data
const isValidBefore = crypto.verify(null, Buffer.from(originalRoot, 'hex'), publicKey, signature);
assert.strictEqual(isValidBefore, true, 'Error: Original signature must be valid');

// 3. Simulate Tampering on Event 1 (Altering rows returned from 42 to 0)
const tamperedEvents = JSON.parse(JSON.stringify(events));
tamperedEvents[3].rows = 0; // Malicious audit log alteration

const tamperedRoot = computeMerkleRoot(tamperedEvents);

// Assert that tampered root does NOT match original signature
const isValidAfter = crypto.verify(null, Buffer.from(tamperedRoot, 'hex'), publicKey, signature);
assert.strictEqual(isValidAfter, false, 'Error: Tampered data must fail signature verification');

console.log('Exercise 2 Verification: PASSED! Merkle Tree tamper detection successfully caught unauthorized mutation.');
