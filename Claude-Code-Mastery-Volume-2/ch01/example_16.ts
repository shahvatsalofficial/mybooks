import { spawn } from 'child_process';
import * as readline from 'readline';

describe('MCP Server Strict Wire Conformance Test Suite', () => {
    let serverProcess: any;
    let rl: readline.Interface;
    let messageCounter = 1;

    beforeAll((done) => {
        serverProcess = spawn('node', ['dist/server.js'], {
            stdio: ['pipe', 'pipe', 'pipe']
        });
        rl = readline.createInterface({ input: serverProcess.stdout });
        done();
    });

    afterAll(() => {
        serverProcess.stdin.end();
        serverProcess.kill('SIGTERM');
    });

    function callRpc(method: string, params: any): Promise<any> {
        return new Promise((resolve, reject) => {
            const id = messageCounter++;
            const handler = (line: string) => {
                try {
                    const parsed = JSON.parse(line);
                    if (parsed.id === id) {
                        rl.removeListener('line', handler);
                        if (parsed.error) reject(parsed.error);
                        else resolve(parsed.result);
                    }
                } catch (e) {
                    reject(new Error(`Non-JSON data emitted to stdout: ${line}`));
                }
            };
            rl.on('line', handler);
            serverProcess.stdin.write(JSON.stringify({ jsonrpc: '2.0', id, method, params }) + '\n');
        });
    }

    test('Conformance: Server rejects invalid params with standard code -32602', async () => {
        await expect(callRpc('tools/call', {
            name: 'calculate_hash',
            arguments: { invalid_field: 12345 } // Missing required 'data' field
        })).rejects.toMatchObject({
            code: -32602
        });
    });

    test('Conformance: Server emits zero non-JSON bytes to stdout stream', (done) => {
        let stdoutViolations = 0;
        const lineSpy = (line: string) => {
            try {
                JSON.parse(line);
            } catch (err) {
                stdoutViolations++;
            }
        };
        rl.on('line', lineSpy);
        
        setTimeout(() => {
            rl.removeListener('line', lineSpy);
            expect(stdoutViolations).toBe(0);
            done();
        }, 1000);
    });
});
