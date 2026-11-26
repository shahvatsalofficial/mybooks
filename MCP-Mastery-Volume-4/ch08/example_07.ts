import { spawn, ChildProcessWithoutNullStreams } from "child_process";
import readline from "readline";

export class McpTestHarness {
  private process: ChildProcessWithoutNullStreams;
  private rl: readline.Interface;
  private pendingRequests = new Map<number, (res: any) => void>();
  private nextId = 1;

  constructor(serverScriptPath: string, env: Record<string, string> = {}) {
    this.process = spawn("node", [serverScriptPath], {
      env: { ...process.env, ...env },
      stdio: ["pipe", "pipe", "pipe"]
    });

    this.rl = readline.createInterface({
      input: this.process.stdout,
      terminal: false
    });

    this.rl.on("line", (line) => {
      try {
        const json = JSON.parse(line);
        if (json.id && this.pendingRequests.has(json.id)) {
          const resolver = this.pendingRequests.get(json.id)!;
          this.pendingRequests.delete(json.id);
          resolver(json);
        }
      } catch {
        // Ignore non-JSON lines (e.g. logging)
      }
    });
  }

  // Send JSON-RPC 2.0 Request over stdio
  async sendRequest(method: string, params: any = {}): Promise<any> {
    const id = this.nextId++;
    const payload = JSON.stringify({ jsonrpc: "2.0", id, method, params });

    return new Promise((resolve) => {
      this.pendingRequests.set(id, resolve);
      this.process.stdin.write(payload + "\n");
    });
  }

  // Execute standard handshake test
  async assertInitialize(): Promise<boolean> {
    const res = await this.sendRequest("initialize", {
      protocolVersion: "2024-11-05",
      capabilities: {},
      clientInfo: { name: "test-client", version: "1.0.0" }
    });
    return res.result?.protocolVersion !== undefined;
  }

  async close() {
    this.process.kill();
  }
}
