// test_dereference.js — Exercise 2 Working Solution
const assert = require('assert');

function dereferenceSchema(schema) {
    const rootDefs = schema.$defs || schema.definitions || {};
    function inlineRef(node) {
        if (node === null || typeof node !== 'object') return node;
        if (Array.isArray(node)) return node.map(inlineRef);
        if (node.$ref && typeof node.$ref === 'string') {
            const refPath = node.$ref.replace(/^#\/(\$defs|definitions)\//, '');
            if (rootDefs[refPath]) {
                return inlineRef(JSON.parse(JSON.stringify(rootDefs[refPath])));
            }
        }
        const res = {};
        for (const [k, v] of Object.entries(node)) {
            if (k !== '$defs' && k !== 'definitions') res[k] = inlineRef(v);
        }
        return res;
    }
    return inlineRef(schema);
}

// Input Schema with $defs
const inputSchema = {
    $defs: {
        GeoLocation: {
            type: 'object',
            properties: {
                latitude: { type: 'number' },
                longitude: { type: 'number' }
            },
            required: ['latitude', 'longitude']
        }
    },
    type: 'object',
    properties: {
        site_id: { type: 'string' },
        coordinates: { $ref: '#/$defs/GeoLocation' }
    },
    required: ['site_id', 'coordinates']
};

const resolved = dereferenceSchema(inputSchema);

// Assertions
assert.strictEqual(resolved.$defs, undefined, 'Error: $defs must be stripped');
assert.strictEqual(resolved.properties.coordinates.type, 'object', 'Error: coordinates type must be object');
assert.strictEqual(resolved.properties.coordinates.properties.latitude.type, 'number', 'Error: nested property missing');

console.log('Exercise 2 Verification: PASSED! AST Dereferencer successfully resolved all references.');
