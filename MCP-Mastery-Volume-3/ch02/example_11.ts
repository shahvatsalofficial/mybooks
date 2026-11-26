// Exercise 3 Working Architecture Extension
export function classifyRequestTier(prompt: string, toolCount: number): 'low_cost' | 'frontier' {
    const hasCodeBlock = prompt.includes('`' + '`' + '`');
    const isLongContext = prompt.length > 800;
    const isMultiTool = toolCount > 5;

    if (hasCodeBlock || isLongContext || isMultiTool) {
        return 'frontier'; // Claude 3.5 Sonnet / GPT-4o
    }
    return 'low_cost';     // GPT-4o-mini / Gemini 1.5 Flash
}
