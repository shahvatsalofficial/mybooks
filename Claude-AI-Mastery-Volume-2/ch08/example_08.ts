// FATAL FLAW: Timestamp at index 0 invalidates entire prompt cache for every call!
const systemPrompt = `Current Timestamp: ${new Date().toISOString()}\n${LEGAL_CORPUS_TEXT}`;
