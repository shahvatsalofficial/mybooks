// HardenedWebSocketQueue.ts
// Resilient memory-throttled message buffer processor

export class HardenedWebSocketQueue {
    private messageBuffer: any[] = [];
    private maxBufferSize = 500;

    public receiveMessage(payload: string) {
        try {
            const data = JSON.parse(payload);
            
            // Enforce strict upper bound on message buffer to prevent OOM
            if (this.messageBuffer.length >= this.maxBufferSize) {
                // Drop oldest 10% of messages to prioritize memory safety
                this.messageBuffer.splice(0, Math.floor(this.maxBufferSize * 0.1));
            }
            
            this.messageBuffer.push(data);
        } catch (err) {
            console.error("[WS] Failed to compile payload", err);
        }
    }

    public flushAndDrain(): any[] {
        // Create a shallow copy of the active buffer
        const chunk = [...this.messageBuffer];
        
        // Clear references in the original array to allow GC harvesting
        this.messageBuffer = [];
        
        return chunk;
    }
}
