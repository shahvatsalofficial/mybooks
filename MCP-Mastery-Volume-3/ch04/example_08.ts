// Exercise 3 Working Architecture Extension
export class ToolChainAnalyzer {
    private static DANGEROUS_TRANSITIONS: Record<string, string[]> = {
        'read_source': ['external_sink', 'network_post', 'send_message'],
        'db_dump': ['file_export', 'http_post']
    };

    public static requiresHumanApproval(lastToolCategory: string, nextToolCategory: string): boolean {
        const forbiddenSinks = this.DANGEROUS_TRANSITIONS[lastToolCategory];
        if (forbiddenSinks && forbiddenSinks.includes(nextToolCategory)) {
            return true; // Tripping HITL circuit breaker
        }
        return false;
    }
}
