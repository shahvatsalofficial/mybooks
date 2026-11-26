const { OpenAI } = require('openai');
const openai = new OpenAI();

/**
 * Enterprise CX Persona Router Middleware
 * Inspects incoming customer query metadata and returns a persona routing profile.
 * 
 * @param {Object} customerProfile - Incoming Customer Metadata
 * @returns {Object} Validated Persona Routing Decision
 */
async function determinePersonaRouting(customerProfile) {
    const rawTelemetry = `
User Tier: ${customerProfile.tier || 'retail_standard'}
Sentiment Score: ${customerProfile.sentiment || '0.00'}
Query: "${customerProfile.query || ''}"
`.trim();

    const systemPrompt = `You are the Master Persona Router at OmniCorp. Your task is to ingest raw user support queries, evaluate their customer tier and sentiment, dynamically select the correct tone and persona configuration, and output a validated, style-compliant JSON routing payload. You must execute your classification with clinical, mathematical precision.

<classification_rules>
- TARGET_PERSONA RULES:
  * "Executive_Sovereign": Target this if the user is a VIP corporate tenant or shows an account tier of "enterprise_platinum". The style must be exceptionally formal, risk-averse, objective, and polite. Prohibit contractions.
  * "Agile_Engineer": Target this if the user is a developer or queries contain technical code blocks, API exceptions, or database logs. The style must be direct, minified, high-density, and action-oriented. No conversational preambles.
  * "Empathetic_Support": Target this if the user is a standard retail account or exhibits high frustration/negative sentiment. The style must be warm, reassuring, proactive, and highly accessible. Use contractions.
</classification_rules>

<execution_constraints>
- You must output a single, raw, minified JSON object matching the output schema.
- Do NOT include any markdown code wrappers (such as triple backticks JSON), do NOT include preambles, introductory text, or post-logs. Start with '{' and end with '}'.
- Avoid trailing commas. Ensure double quotes are properly escaped to prevent parsing failures.
</execution_constraints>

<output_schema>
{
  "determined_persona": "Executive_Sovereign" | "Agile_Engineer" | "Empathetic_Support",
  "formality_slider_value": float (from 0.00 to 1.00),
  "conciseness_slider_value": float (from 0.00 to 1.00),
  "active_vocabulary_rules": string[],
  "routing_status": "forward_to_agent" | "auto_resolve",
  "confidence_score": float (from 0.00 to 1.00)
}
</output_schema>`;

    try {
        // Execute API call with Trailing Suffix Injection to force JSON output
        const response = await openai.chat.completions.create({
            model: 'gpt-4o-mini',
            messages: [
                { role: 'system', content: systemPrompt },
                { role: 'user', content: `Analyze the incoming customer telemetry below and generate the correct JSON output:\n\nInput Context:\n${rawTelemetry}\n\nOutput Payload:` }
            ],
            temperature: 0.0, // Force strict deterministic styling decisions
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
        const requiredKeys = ['determined_persona', 'formality_slider_value', 'conciseness_slider_value', 'active_vocabulary_rules', 'routing_status', 'confidence_score'];
        for (const key of requiredKeys) {
            if (!(key in routingPayload)) {
                throw new Error(`Missing mandatory schema key: ${key}`);
            }
        }

        console.log('[PERSONA ROUTER SUCCESS] Style Analysis Complete:', routingPayload);
        return {
            status: 200,
            persona: routingPayload.determined_persona,
            formality: routingPayload.formality_slider_value,
            conciseness: routingPayload.conciseness_slider_value,
            rules: routingPayload.active_vocabulary_rules,
            action: routingPayload.routing_status,
            confidence: routingPayload.confidence_score
        };

    } catch (error) {
        // Fallback: If style parser breaks, default to Empathetic Support to ensure a polite user experience
        console.error('[PERSONA ROUTER FAILURE] Style engine broke. Routing to Empathetic_Support as fail-safe:', error.message);
        return {
            status: 500,
            persona: 'Empathetic_Support',
            formality: 0.50,
            conciseness: 0.50,
            rules: ['Use standard polite English', 'Avoid technical jargon'],
            action: 'forward_to_agent',
            confidence: 1.00
        };
    }
}
