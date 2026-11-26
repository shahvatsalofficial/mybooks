const { OpenAI } = require('openai');
const openai = new OpenAI();

async function processAndRouteTicket(rawTicketText) {
    const systemPrompt = `You are a Principal Technical Support Router... [System Prompt Here]`;
    
    try {
        const response = await openai.chat.completions.create({
            model: 'gpt-4o-mini',
            messages: [
                { role: 'system', content: systemPrompt },
                { role: 'user', content: `Input Ticket:\n"${rawTicketText}"\n\nOutput Payload:` }
            ],
            temperature: 0.0, // Force maximum deterministic output
            max_tokens: 300
        });

        const rawOutput = response.choices[0].message.content.trim();
        
        // Fail-Safe: Regex-based recovery in case model wraps output in markdown fences
        let cleanedJSON = rawOutput;
        if (rawOutput.startsWith('\x60\x60\x60')) {
            cleanedJSON = rawOutput.replace(/^\x60\x60\x60(?:json)?\n?|\x60\x60\x60$/g, '').trim();
        }

        const parsedPayload = JSON.parse(cleanedJSON);

        // Schema validation guard
        if (parsedPayload.error === 'INVALID_INPUT') {
            console.error('[ALERT] Invalid or empty ticket submitted.');
            return { status: 400, message: 'Invalid Input' };
        }

        console.log('[SUCCESS] Parsed Routing Payload:', parsedPayload);
        return {
            status: 200,
            destination: parsedPayload.routing_destination,
            urgency: parsedPayload.urgency_level,
            reason: parsedPayload.primary_reason_prose,
            confidence: parsedPayload.confidence_score
        };

    } catch (error) {
        // Fallback execution block to prevent production service crashes
        console.error('[CRITICAL FAILURE] Parsing pipeline failed. Routing to manual review queue:', error.message);
        return {
            status: 500,
            destination: 'manual_review',
            urgency: 'high',
            reason: `System parser failure: ${error.message}`
        };
    }
}
