// streaming_multiplexer.ts — Real-time Chunk Stitching & Event Multiplexing
import { EventEmitter } from 'events';

export interface ToolCallDeltaEvent {
    callId: string;
    toolName: string;
    rawArguments: string;
    parsedArguments: Record<string, any> | null;
    isComplete: boolean;
}

export class StreamingMultiplexer extends EventEmitter {
    private bufferMap: Map<string, { toolName: string; rawArgs: string }> = new Map();

    /**
     * Ingests an OpenAI SSE chunk fragment
     */
    public handleOpenAiChunk(chunk: any): void {
        const delta = chunk.choices?.[0]?.delta;
        if (!delta || !delta.tool_calls) return;

        for (const tc of delta.tool_calls) {
            const index = tc.index ?? 0;
            const callKey = `call_${index}`;

            if (!this.bufferMap.has(callKey)) {
                this.bufferMap.set(callKey, {
                    toolName: tc.function?.name || 'unknown_tool',
                    rawArgs: ''
                });
                this.emit('tool_call_start', { callId: callKey, toolName: tc.function?.name });
            }

            const current = this.bufferMap.get(callKey)!;
            if (tc.function?.name && current.toolName === 'unknown_tool') {
                current.toolName = tc.function.name;
            }

            if (tc.function?.arguments) {
                current.rawArgs += tc.function.arguments;
                const partialParsed = this.tryRepairAndParseJson(current.rawArgs);

                this.emit('tool_call_delta', {
                    callId: callKey,
                    toolName: current.toolName,
                    rawArguments: current.rawArgs,
                    parsedArguments: partialParsed,
                    isComplete: false
                } as ToolCallDeltaEvent);
            }
        }
    }

    /**
     * Finalizes the stream and emits complete tool calls
     */
    public finalizeStream(): void {
        for (const [callId, data] of this.bufferMap.entries()) {
            let finalArgs: Record<string, any> = {};
            try {
                finalArgs = JSON.parse(data.rawArgs);
            } catch (err) {
                // Final parse fallback
                finalArgs = this.tryRepairAndParseJson(data.rawArgs) || {};
            }

            this.emit('tool_call_ready', {
                callId,
                toolName: data.toolName,
                rawArguments: data.rawArgs,
                parsedArguments: finalArgs,
                isComplete: true
            } as ToolCallDeltaEvent);
        }
        this.bufferMap.clear();
    }

    /**
     * Synthetically closes dangling JSON string quotes and braces
     */
    private tryRepairAndParseJson(incomplete: string): Record<string, any> | null {
        if (!incomplete || incomplete.trim() === '') return null;

        let repaired = incomplete.trim();

        // 1. If inside an open string, close it
        let openQuotes = 0;
        for (let i = 0; i < repaired.length; i++) {
            if (repaired[i] === '"' && (i === 0 || repaired[i - 1] !== '\\')) {
                openQuotes++;
            }
        }
        if (openQuotes % 2 !== 0) {
            repaired += '"';
        }

        // 2. Count open and closed curly braces
        let openBraces = 0;
        let inString = false;
        for (let i = 0; i < repaired.length; i++) {
            const char = repaired[i];
            if (char === '"' && (i === 0 || repaired[i - 1] !== '\\')) {
                inString = !inString;
            }
            if (!inString) {
                if (char === '{') openBraces++;
                if (char === '}') openBraces--;
            }
        }

        // Append required closing braces
        while (openBraces > 0) {
            repaired += '}';
            openBraces--;
        }

        try {
            return JSON.parse(repaired);
        } catch {
            return null;
        }
    }
}
