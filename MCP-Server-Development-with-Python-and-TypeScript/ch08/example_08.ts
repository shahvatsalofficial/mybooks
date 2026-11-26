import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { SSEClientTransport } from "@modelcontextprotocol/sdk/client/sse.js";

class ResilientMcpClient {
  private client: Client;
  private url: URL;
  private maxRetries = 5;

  constructor(serverUrl: string) {
    this.url = new URL(serverUrl);
    this.client = new Client({ name: "resilient-client", version: "1.0.0" }, { capabilities: {} });
  }

  async connectWithBackoff() {
    let attempt = 0;
    const baseDelay = 200;
    const maxDelay = 30000;

    while (attempt < this.maxRetries) {
      try {
        console.error(`[Client] Connection attempt ${attempt + 1}/${this.maxRetries}...`);
        const transport = new SSEClientTransport(this.url);
        await this.client.connect(transport);
        console.error("[Client] Connected successfully to remote MCP gateway.");
        return;
      } catch (err: any) {
        attempt++;
        if (attempt >= this.maxRetries) {
          throw new Error(`Failed to connect after ${this.maxRetries} attempts: ${err.message}`);
        }

        // Full jitter backoff formula
        const expDelay = Math.min(maxDelay, baseDelay * Math.pow(2, attempt));
        const jitterDelay = Math.random() * expDelay;
        console.error(`[Client] Connection failed (${err.message}). Retrying in ${Math.round(jitterDelay)}ms...`);
        await new Promise((r) => setTimeout(r, jitterDelay));
      }
    }
  }
}
