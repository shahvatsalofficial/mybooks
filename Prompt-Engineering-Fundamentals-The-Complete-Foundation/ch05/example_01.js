/**
 * OmniCorp Global Logistics Schema Enforcer Middleware
 * File: schemaEnforcer.js
 */

const { OpenAI } = require('openai');

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY || 'mock-key-for-compilation'
});

// Enforcer Schema matching the system prompt constraints
const LOGISTICS_SCHEMA = {
  type: 'object',
  required: [
    'manifest_id',
    'shipper_name',
    'origin_country_iso',
    'destination_country_iso',
    'cargo_weight_kg',
    'hazardous_materials',
    'cargo_dimensions',
    'package_count'
  ],
  properties: {
    manifest_id: { type: 'string', pattern: '^MNF-\\d{6}$' },
    shipper_name: { type: 'string', maxLength: 100 },
    origin_country_iso: { type: 'string', minLength: 2, maxLength: 2 },
    destination_country_iso: { type: 'string', minLength: 2, maxLength: 2 },
    cargo_weight_kg: { type: 'number', minimum: 0 },
    hazardous_materials: { type: 'boolean' },
    cargo_dimensions: {
      type: 'object',
      required: ['length_m', 'width_m', 'height_m'],
      properties: {
        length_m: { type: 'number', minimum: 0 },
        width_m: { type: 'number', minimum: 0 },
        height_m: { type: 'number', minimum: 0 }
      }
    },
    package_count: { type: 'integer', minimum: 1 }
  }
};

/**
 * Extracts the core JSON string from an LLM response block
 * @param {string} rawText 
 * @returns {string}
 */
function extractJSONCore(rawText) {
  let cleaned = rawText.trim();
  
  // Strip Markdown code block wrappers using escaped backticks to prevent parser split anomalies
  if (cleaned.startsWith('\x60\x60\x60')) {
    cleaned = cleaned.replace(/^\x60\x60\x60[a-zA-Z]*\n/, '');
    cleaned = cleaned.replace(/\n\x60\x60\x60$/, '');
  }
  cleaned = cleaned.trim();
  
  // Extract content between first '{' and last '}'
  const start = cleaned.indexOf('{');
  const end = cleaned.lastIndexOf('}');
  
  if (start === -1 || end === -1) {
    throw new SyntaxError('No JSON object boundaries found in raw response text.');
  }
  
  return cleaned.substring(start, end + 1);
}

/**
 * Validates a parsed object against the required schema
 * @param {Object} data 
 * @returns {boolean}
 */
function validateSchema(data) {
  // Check required root properties
  for (const key of LOGISTICS_SCHEMA.required) {
    if (!(key in data)) {
      throw new TypeError(`Missing required schema property: "${key}"`);
    }
  }

  // Validate regex patterns and types
  const manifestRegex = new RegExp(LOGISTICS_SCHEMA.properties.manifest_id.pattern);
  if (!manifestRegex.test(data.manifest_id)) {
    throw new ValueError(`Invalid manifest_id format: "${data.manifest_id}". Must match MNF-xxxxxx.`);
  }

  if (typeof data.shipper_name !== 'string' || data.shipper_name.length > 100) {
    throw new ValueError('Invalid shipper_name. Must be a string under 100 characters.');
  }

  if (data.origin_country_iso.length !== 2 || data.destination_country_iso.length !== 2) {
    throw new ValueError('Country ISO codes must be exactly 2 characters.');
  }

  if (typeof data.cargo_weight_kg !== 'number' || data.cargo_weight_kg < 0) {
    throw new ValueError('cargo_weight_kg must be a positive number.');
  }

  // Validate nested dimensions
  const dims = data.cargo_dimensions;
  if (!dims || typeof dims !== 'object') {
    throw new TypeError('cargo_dimensions must be a valid nested object.');
  }

  for (const dimKey of LOGISTICS_SCHEMA.properties.cargo_dimensions.required) {
    if (!(dimKey in dims) || typeof dims[dimKey] !== 'number' || dims[dimKey] < 0) {
      throw new ValueError(`Invalid dimension metric: "${dimKey}". Must be a positive float.`);
    }
  }

  if (!Number.isInteger(data.package_count) || data.package_count < 1) {
    throw new ValueError('package_count must be an integer greater than or equal to 1.');
  }

  return true;
}

// Custom error classes for fine-grained exception tracking
class ValueError extends Error {
  constructor(message) {
    super(message);
    this.name = 'ValueError';
  }
}

/**
 * High-reliability gateway parser with automated error-correction loop
 */
async function processManifestGateway(unstructuredText, retryCount = 0, priorError = null) {
  const maxRetries = 2;
  
  try {
    let promptPayload = unstructuredText;
    
    // Inject self-correction system prompt if this is a retry attempt
    if (priorError) {
      promptPayload = `
The previous manifest extraction failed structural validation:
<invalid_data>
${unstructuredText}
</invalid_data>

Error Details: ${priorError.name} - ${priorError.message}

Please inspect the error closely, correct any formatting discrepancies, and output ONLY the corrected JSON matching the schema. No explanations.
      `;
    }

    // Call upstream inference gateway
    const response = await openai.chat.completions.create({
      model: 'gpt-4o',
      messages: [
        { role: 'system', content: 'You are a rigid schema parsing pipeline. Output ONLY minified JSON.' },
        { role: 'user', content: promptPayload }
      ],
      temperature: 0.1 // Hard lock for maximum format determinism
    });

    const rawText = response.choices[0].message.content;
    const jsonCore = extractJSONCore(rawText);
    const parsedData = JSON.parse(jsonCore);

    // Run programmatic validation
    validateSchema(parsedData);

    console.log('Manifest parsed and validated successfully:', parsedData.manifest_id);
    return parsedData;

  } catch (error) {
    console.warn(`Gateway parsing attempt failed (Retries: ${retryCount}/${maxRetries}). Error: ${error.message}`);
    
    if (retryCount < maxRetries) {
      return await processManifestGateway(unstructuredText, retryCount + 1, error);
    } else {
      console.error('Max gateway retries reached. Manifest extraction failed.');
      throw new Error(`Gateway Compilation Failure: ${error.message}`);
    }
  }
}

module.exports = {
  processManifestGateway,
  extractJSONCore,
  validateSchema
};
