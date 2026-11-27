/**
 * Recipe 04.2: Enterprise Zero-Trust Security Interceptor for MCP Clients
 * Author: Vatsal Shah (Vatsal Shah)
 * License: Apache-2.0
 */

import path from 'path';

export interface SecurityPolicy {
  allowedTools: Set<string>;
  requireManualConfirmation: Set<string>;
  allowedPathPrefixes: string[];
}

export class McpSecurityGate {
  private policy: SecurityPolicy;

  constructor(policy: SecurityPolicy) {
    this.policy = policy;
  }

  public validateToolInvocation(toolName: string, args: Record<string, any>): boolean {
    // 1. Whitelist Verification
    if (!this.policy.allowedTools.has(toolName)) {
      throw new Error(`Security Violation: Tool '${toolName}' is not permitted by organizational policy.`);
    }

    // 2. Canonical Path Containment (Prevent Directory Traversal)
    if (args.filePath && typeof args.filePath === 'string') {
      const canonicalPath = path.resolve(args.filePath);
      const isContained = this.policy.allowedPathPrefixes.some((prefix) =>
        canonicalPath.startsWith(path.resolve(prefix))
      );
      if (!isContained) {
        throw new Error(`Path Traversal Blocked: Path '${args.filePath}' violates containment boundary.`);
      }
    }

    // 3. Human Confirmation Gate for Destructive Actions
    if (this.policy.requireManualConfirmation.has(toolName)) {
      console.warn(`[SECURITY GATE] Tool '${toolName}' requires interactive administrator approval.`);
      // In production, integrate with Slack, Webhook, or interactive UI confirmation
    }

    return true;
  }
}
