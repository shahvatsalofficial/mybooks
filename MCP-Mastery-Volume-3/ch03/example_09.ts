// Exercise 3 Working Architecture Schema
export interface McpTelemetryEvent {
    eventId: string;
    timestampIso: string;
    tenantId: string;
    traceId: string;
    spanId: string;
    toolName: string;
    modelInvoker: string;
    durationMs: number;
    tokens: {
        input: number;
        output: number;
        cached: number;
    };
    financialsUsd: number;
    statusCode: 'SUCCESS' | 'ERROR';
    errorType?: string;
}
