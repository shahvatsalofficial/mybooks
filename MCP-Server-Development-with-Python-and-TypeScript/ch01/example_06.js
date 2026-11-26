/**
 * Filename: mcp_process_guard.js
 * Description: Production sub-process isolation and lifecycle supervisor for MCP servers.
 * Author: Vatsal Shah (MCP Mastery Series)
 * Target Runtime: Node.js 20+
 */

const { spawn } = require('child_process');
const path = require('path');

class MCPProcessGuard {
    constructor(serverScriptPath, options = {}) {
        this.serverScriptPath = serverScriptPath;
        this.maxMemoryMB = options.maxMemoryMB || 512;
        this.drainTimeoutMs = options.drainTimeoutMs || 3000;
        this.process = null;
    }

    spawnServer() {
        console.log(`[ProcessGuard] Launching isolated MCP runtime for: ${this.serverScriptPath}`);
        
        // Spawn with detached: false to link process groups, inheriting piped stdio
        this.process = spawn('node', [
            `--max-old-space-size=${this.maxMemoryMB}`,
            this.serverScriptPath
        ], {
            stdio: ['pipe', 'pipe', 'pipe'],
            env: {
                ...process.env,
                PYTHONUNBUFFERED: '1',
                NODE_ENV: 'production'
            }
        });

        const pid = this.process.pid;
        console.log(`[ProcessGuard] Server active under PID: ${pid}`);

        // Capture stderr for operational telemetry without interfering with stdout JSON-RPC
        this.process.stderr.on('data', (chunk) => {
            console.error(`[Server ${pid} STDERR]: ${chunk.toString().trim()}`);
        });

        this.process.on('exit', (code, signal) => {
            console.log(`[ProcessGuard] Server (PID ${pid}) exited with code: ${code}, signal: ${signal}`);
            this.process = null;
        });

        // Register host process hook to guarantee no orphans on exit
        const cleanExitHandler = () => this.terminateGracefully();
        process.on('SIGINT', cleanExitHandler);
        process.on('SIGTERM', cleanExitHandler);
    }

    async terminateGracefully() {
        if (!this.process) return;

        const targetPid = this.process.pid;
        console.log(`[ProcessGuard] Commencing graceful drain for PID ${targetPid}...`);

        return new Promise((resolve) => {
            let forceKillTimeout;

            const exitListener = () => {
                clearTimeout(forceKillTimeout);
                console.log(`[ProcessGuard] PID ${targetPid} drained cleanly.`);
                resolve();
            };

            this.process.once('exit', exitListener);

            // 1. Send SIGTERM to allow internal server async contexts to finish
            this.process.kill('SIGTERM');

            // 2. Set hard deadline for SIGKILL force-kill
            forceKillTimeout = setTimeout(() => {
                if (this.process) {
                    console.warn(`[ProcessGuard] PID ${targetPid} failed to drain within ${this.drainTimeoutMs}ms. Forcing SIGKILL.`);
                    this.process.removeListener('exit', exitListener);
                    this.process.kill('SIGKILL');
                    resolve();
                }
            }, this.drainTimeoutMs);
        });
    }
}

module.exports = { MCPProcessGuard };
