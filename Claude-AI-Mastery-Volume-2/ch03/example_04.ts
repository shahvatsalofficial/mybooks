/**
 * Recipe 03.4: Resilient SSE Client with State Resumption
 * Author: Vatsal Shah (Vatsal Shah)
 * License: Apache-2.0
 */

export interface ResilientStreamOptions {
  url: string;
  payload: Record<string, any>;
  onToken: (token: string) => void;
  onError: (error: Error) => void;
  onComplete: () => void;
  maxReconnectAttempts?: number;
}

export class ResilientSSEClient {
  private lastDeliveredSeqId = 0;
  private isTerminated = false;
  private reconnectAttempts = 0;

  constructor(private options: ResilientStreamOptions) {}

  public async connect(): Promise<void> {
    const maxAttempts = this.options.maxReconnectAttempts || 5;

    while (!this.isTerminated && this.reconnectAttempts < maxAttempts) {
      try {
        const headers: Record<string, string> = {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream'
        };
        if (this.lastDeliveredSeqId > 0) {
          headers['Last-Event-ID'] = String(this.lastDeliveredSeqId);
        }

        const resp = await fetch(this.options.url, {
          method: 'POST',
          headers,
          body: JSON.stringify({ ...this.options.payload, lastSeq: this.lastDeliveredSeqId })
        });

        if (!resp.ok || !resp.body) {
          throw new Error(`HTTP ${resp.status} - Stream connection failed`);
        }

        this.reconnectAttempts = 0; // Reset backoff on success
        const reader = resp.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) {
            this.isTerminated = true;
            this.options.onComplete();
            return;
          }

          buffer += decoder.decode(value, { stream: true });
          const parts = buffer.split('\n\n');
          buffer = parts.pop() || '';

          for (const rawEvent of parts) {
            const lines = rawEvent.split('\n');
            let seqId = 0;
            let data = '';

            for (const line of lines) {
              if (line.startsWith('id: ')) {
                seqId = parseInt(line.substring(4), 10);
              } else if (line.startsWith('data: ')) {
                data = line.substring(6);
              }
            }

            if (seqId > this.lastDeliveredSeqId) {
              this.lastDeliveredSeqId = seqId;
            }

            if (data && data !== '[DONE]') {
              const parsed = JSON.parse(data);
              if (parsed.text) {
                this.options.onToken(parsed.text);
              }
            }
          }
        }
      } catch (err: any) {
        this.reconnectAttempts++;
        const backoffMs = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 16000);
        console.warn(`SSE stream disconnected. Reconnecting in ${backoffMs}ms (Attempt ${this.reconnectAttempts}/${maxAttempts})...`);
        await new Promise(r => setTimeout(r, backoffMs));
      }
    }

    if (!this.isTerminated) {
      this.options.onError(new Error('Exceeded maximum reconnection attempts. Stream aborted.'));
    }
  }

  public abort(): void {
    this.isTerminated = true;
  }
}
