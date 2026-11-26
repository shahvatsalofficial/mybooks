const { OpenAI } = require('openai');
const openai = new OpenAI();

/**
 * Enterprise API Gateway Proxy Middleware
 * Analyzes incoming request telemetry and returns routing decisions.
 * 
 * @param {Object} req - Incoming HTTP Request Object
 * @returns {Object} Validated Routing Decision Payload
 */
async function inspectAndRouteRequest(req) {
    const rawTelemetry = `
Host: ${req.headers['host'] || 'unknown'}
Authorization: ${req.headers['authorization'] || 'null'}
Body: ${JSON.stringify(req.body || {})}
`.trim();

    const systemPrompt = `You are the Principal Security Architect... [System Prompt Here]`;

    try {
        // Execute dynamic prompt with Trailing Suffix Injection
        const response = await openai.chat.completions.create({
            model: 'gpt-4o-mini',
            messages: [
                { role: 'system', content: systemPrompt },
                { role: 'user', content: `Analyze the incoming HTTP gateway request below and generate the correct JSON output:\n\nInput Request:\n${rawTelemetry}\n\nOutput Payload:` }
            ],
            temperature: 0.0, // Force strict deterministic decoding
            max_tokens: 250
        });

        const rawOutput = response.choices[0].message.content.trim();
        
        // Fail-Safe: strip any accidental markdown backtick wrappers
        let cleanedJSON = rawOutput;
        if (rawOutput.startsWith('\x60\x60\x60')) {
            cleanedJSON = rawOutput.replace(/^\x60\x60\x60(?:json)?\n?|\x60\x60\x60$/g, '').trim();
        }

        const routingPayload = JSON.parse(cleanedJSON);

        // Verify schema compliance
        const requiredKeys = ['exploit_detected', 'exploit_signature', 'tenant_routing_key', 'auth_token_extracted', 'routing_status', 'confidence_score'];
        for (const key of requiredKeys) {
            if (!(key in routingPayload)) {
                throw new Error(`Missing mandatory schema key: ${key}`);
            }
        }

        console.log('[GATEWAY SUCCESS] Security Analysis Complete:', routingPayload);
        return {
            status: 200,
            exploitDetected: routingPayload.exploit_detected === 'true',
            signature: routingPayload.exploit_signature,
            tenant: routingPayload.tenant_routing_key,
            authToken: routingPayload.auth_token_extracted,
            statusAction: routingPayload.routing_status,
            confidence: routingPayload.confidence_score
        };

    } catch (error) {
        // Fallback: If AI fails or outputs invalid JSON, route to Quarantine out of abundance of caution
        console.error('[GATEWAY CRITICAL FAILURE] Security analysis pipeline broken. Routing to quarantine as fail-safe:', error.message);
        return {
            status: 500,
            exploitDetected: true,
            signature: `PARSER_EXCEPTION: ${error.message}`,
            tenant: 'unknown_quarantine',
            authToken: 'null',
            statusAction: 'quarantine',
            confidence: 1.00
        };
    }
}
