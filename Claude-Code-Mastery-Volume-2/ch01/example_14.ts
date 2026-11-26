import { spawn } from 'child_process';
import * as readline from 'readline';

interface JsonRpcMessage {
    jsonrpc: '2.0';
    id?: number | string;
    method?: string;
    params?: any;
    result?: any;
    error?: any;
}

export class RawMcpProtocolTracer {
    private process: any;
    private rl: readline.Interface;
    private requestId = 1;
    private pendingRequests = new Map<number | string, (res: any) => void>();

    constructor(serverCommand: string, args: string[]) {
        // 1. Spawn server with piped stdio. stderr is inherited for debug visibility.
        this.process = spawn(serverCommand, args, {
            stdio: ['pipe', 'pipe', 'inherit'],
            env: { ...process.env, NODE_ENV: 'production' }
        });

        // 2. Wrap stdout in readline interface to guarantee line-by-line JSON framing
        this.rl = readline.createInterface({
            input: this.process.stdout,
            terminal: false
        });

        this.rl.on('line', (line) => {
            if (!line.trim()) return;
            try {
                const message: JsonRpcMessage = JSON.parse(line);
                console.log('\x1b[36m[RECV wire]\x1b[0m', JSON.stringify(message, null, 2));
                
                if (message.id !== undefined && this.pendingRequests.has(message.id)) {
                    const callback = this.pendingRequests.get(message.id)!;
                    this.pendingRequests.delete(message.id);
                    callback(message);
                }
            } catch (err) {
                console.error('\x1b[31m[FATAL: Framing Parse Error]\x1b[0m Raw buffer:', line);
            }
        });
    }

    public send(method: string, params?: any): Promise<JsonRpcMessage> {
        return new Promise((resolve) => {
            const id = this.requestId++;
            const envelope: JsonRpcMessage = {
                jsonrpc: '2.0',
                id,
                method,
                params
            };

            this.pendingRequests.set(id, resolve);
            const wirePayload = JSON.stringify(envelope) + '\n';
            console.log('\x1b[35m[SEND wire]\x1b[0m', JSON.stringify(envelope, null, 2));
            this.process.stdin.write(wirePayload);
        });
    }

    public notify(method: string, params?: any): void {
        const envelope: JsonRpcMessage = {
            jsonrpc: '2.0',
            method,
            params
        };
        const wirePayload = JSON.stringify(envelope) + '\n';
        console.log('\x1b[33m[NOTIFY wire]\x1b[0m', JSON.stringify(envelope, null, 2));
        this.process.stdin.write(wirePayload);
    }

    public async executeProtocolLifecycle() {
        console.log('--- PHASE 1: INITIALIZATION HANDSHAKE ---');
        const initResponse = await this.send('initialize', {
            protocolVersion: '2024-11-05',
            capabilities: { roots: { listChanged: true } },
            clientInfo: { name: 'diagnostic-tracer', version: '1.0.0' }
        });

        // Transmit initialized notification to complete handshake
        this.notify('notifications/initialized');

        console.log('--- PHASE 2: DISCOVERY ---');
        const toolsList = await this.send('tools/list', {});
        console.log('Discovered Tools Count:', toolsList.result?.tools?.length);

        console.log('--- PHASE 3: EXECUTION ---');
        const toolCallResult = await this.send('tools/call', {
            name: 'echo_telemetry',
            arguments: { payload: 'Sovereign MCP Test Vector' }
        });
        console.log('Execution Result:', toolCallResult.result);

        // Terminate cleanly
        this.process.stdin.end();
    }
}
