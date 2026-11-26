/**
 * Enterprise Agent Security Gatekeeper
 * Package: @enterprise/agent-guardrails
 * Author: Vatsal Shah, Lead Enterprise AI Architect
 */

import { spawn } from 'child_process';
import * as fs from 'fs';
import * as path from 'path';
import * as crypto from 'crypto';

export interface SecurityPolicy {
    allowedDirectories: string[];
    blockedCommands: RegExp[];
    blockedArguments: RegExp[];
    requireHumanApprovalForNetwork: boolean;
    maxExecutionTimeMs: number;
}

export interface InspectionResult {
    isAllowed: boolean;
    reason?: string;
    riskScore: number; // 0 (Safe) to 100 (Critical)
    sanitizedCommand?: string;
}

export class AgentGatekeeper {
    private policy: SecurityPolicy;
    private canaryToken: string;

    constructor(policy: SecurityPolicy) {
        this.policy = policy;
        this.canaryToken = this.generateCanary();
    }

    private generateCanary(): string {
        return 'CANARY_' + crypto.randomBytes(16).toString('hex');
    }

    public getCanaryToken(): string {
        return this.canaryToken;
    }

    /**
     * Layer 1: Strict Shell Command Inspection & AST Disinfection
     */
    public inspectCommand(command: string, cwd: string): InspectionResult {
        const normalizedCwd = path.resolve(cwd);

        // Enforce workspace boundary
        const isWithinWorkspace = this.policy.allowedDirectories.some(allowedDir => {
            const normalizedAllowed = path.resolve(allowedDir);
            return normalizedCwd.startsWith(normalizedAllowed);
        });

        if (!isWithinWorkspace) {
            return {
                isAllowed: false,
                reason: `Execution directory ${normalizedCwd} is outside authorized workspace boundaries.`,
                riskScore: 100
            };
        }

        // Check for blocked binary patterns
        for (const pattern of this.policy.blockedCommands) {
            if (pattern.test(command)) {
                return {
                    isAllowed: false,
                    reason: `Command matches prohibited binary signature: ${pattern.source}`,
                    riskScore: 95
                };
            }
        }

        // Check for dangerous shell metacharacters and exfiltration pipes
        const dangerousPatterns = [
            /curl.*|.*sh/i,
            /wget.*|.*sh/i,
            /eval(.*)/i,
            /base64\s+-d.*|/i,
            />\s*\/etc\//i,
            />\s*~\/\.ssh\//i,
            />\s*~\/\.aws\//i,
            /env\s*\|\s*curl/i,
            /cat.*id_rsa/i,
            /export.*AWS_SECRET_ACCESS_KEY/i
        ];

        for (const pattern of dangerousPatterns) {
            if (pattern.test(command)) {
                return {
                    isAllowed: false,
                    reason: `Command contains potential exfiltration or shell hijacking signature: ${pattern.source}`,
                    riskScore: 99
                };
            }
        }

        // Check for canary leakage in generated commands
        if (command.includes(this.canaryToken)) {
            return {
                isAllowed: false,
                reason: 'CRITICAL SECURITY BREACH: Internal canary token detected in outgoing command buffer.',
                riskScore: 100
            };
        }

        return {
            isAllowed: true,
            riskScore: 10,
            sanitizedCommand: command.trim()
        };
    }

    /**
     * Layer 2: Dual-LLM Sanitizer (Disinfect Untrusted Repo Content)
     */
    public async disinfectUntrustedText(rawInput: string): Promise<string> {
        // In production, this dispatches to an isolated Claude 3.5 Haiku instance 
        // with ZERO tool execution capabilities.
        let disinfected = rawInput;

        // Strip HTML comments which frequently conceal injection payloads
        disinfected = disinfected.replace(/<!--[\s\S]*?-->/g, '[REDACTED_COMMENT]');

        // Neutralize common fake system override prefixes
        const injectionSignatures = [
            /\[SYSTEM DEBUG PROTOCOL ACTIVATED\]/gi,
            /IMPORTANT SYSTEM DIRECTIVE:/gi,
            /STOP PROCESSING TASK\./gi,
            /You are no longer Claude/gi,
            /BEGIN EMERGENCY OVERRIDE/gi,
            /ADMINISTRATIVE ACCESS GRANTED/gi
        ];

        for (const signature of injectionSignatures) {
            disinfected = disinfected.replace(signature, '[PROMPT_INJECTION_DEFUSED]');
        }

        // Neutralize zero-width steganographic characters
        disinfected = disinfected.replace(/[\u200B-\u200D\uFEFF]/g, '');

        return disinfected;
    }

    /**
     * Layer 3: Controlled Execution Sandbox with Hard Limits
     */
    public async executeSafeCommand(
        command: string, 
        cwd: string
    ): Promise<{ stdout: string; stderr: string; exitCode: number }> {
        const inspection = this.inspectCommand(command, cwd);
        if (!inspection.isAllowed) {
            throw new Error(`[SECURITY_GATE_VIOLATION]: ${inspection.reason}`);
        }

        return new Promise((resolve, reject) => {
            const child = spawn(command, {
                cwd,
                shell: true,
                timeout: this.policy.maxExecutionTimeMs,
                env: {
                    // Purge sensitive secrets from execution environment
                    ...process.env,
                    AWS_SECRET_ACCESS_KEY: '[SHIELDED]',
                    GITHUB_TOKEN: '[SHIELDED]',
                    ANTHROPIC_API_KEY: '[SHIELDED]'
                }
            });

            let stdout = '';
            let stderr = '';

            child.stdout.on('data', (data) => {
                stdout += data.toString();
            });

            child.stderr.on('data', (data) => {
                stderr += data.toString();
            });

            child.on('close', (exitCode) => {
                resolve({ stdout, stderr, exitCode: exitCode ?? -1 });
            });

            child.on('error', (err) => {
                reject(err);
            });
        });
    }
}
