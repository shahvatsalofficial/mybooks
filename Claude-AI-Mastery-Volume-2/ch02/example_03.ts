/**
 * Recipe 02.3: Production Autonomous Agent Loop with Dry-Run Gates
 * Author: Vatsal Shah (Vatsal Shah)
 * License: Apache-2.0
 */

import Anthropic from '@anthropic-ai/sdk';
import { MessageParam, ToolResultBlockParam } from '@anthropic-ai/sdk/resources';

export interface AgentActionAudit {
  step: number;
  toolName: string;
  args: Record<string, any>;
  isDryRun: boolean;
  status: 'APPROVED' | 'REJECTED' | 'EXECUTED';
}

export class GovernedAgentRuntime {
  private client: Anthropic;
  private maxSteps: number;
  private dryRunMode: boolean;
  private auditLog: AgentActionAudit[] = [];

  constructor(apiKey: string, maxSteps = 8, dryRunMode = false) {
    this.client = new Anthropic({ apiKey });
    this.maxSteps = maxSteps;
    this.dryRunMode = dryRunMode;
  }

  private isDestructiveAction(toolName: string): boolean {
    const destructiveTools = ['delete_database_record', 'scale_down_deployment', 'terminate_ec2_instance'];
    return destructiveTools.includes(toolName);
  }

  async executeAutonomousMission(
    systemPrompt: string,
    goal: string,
    availableTools: Anthropic.Tool[]
  ): Promise<{ outcome: string; auditTrail: AgentActionAudit[] }> {
    const messages: MessageParam[] = [{ role: 'user', content: goal }];
    const executedSignatures = new Set<string>();

    for (let step = 1; step <= this.maxSteps; step++) {
      const response = await this.client.messages.create({
        model: 'claude-3-5-sonnet-20241022',
        max_tokens: 3000,
        system: systemPrompt,
        tools: availableTools,
        messages: messages
      });

      // Append assistant's turn
      messages.push({ role: 'assistant', content: response.content });

      if (response.stop_reason !== 'tool_use') {
        const finalAnswer = response.content
          .filter(b => b.type === 'text')
          .map(b => (b as any).text)
          .join('\n');
        return { outcome: finalAnswer, auditTrail: this.auditLog };
      }

      // Collect tool calls
      const toolBlocks = response.content.filter(b => b.type === 'tool_use') as Anthropic.ToolUseBlock[];
      const toolResults: ToolResultBlockParam[] = [];

      for (const call of toolBlocks) {
        // Detect Infinite Loops: Reject identical repetitive calls
        const signature = `${call.name}:${JSON.stringify(call.input)}`;
        if (executedSignatures.has(signature)) {
          toolResults.push({
            type: 'tool_result',
            tool_use_id: call.id,
            content: `Execution Safety Violation: Cyclic invocation detected. You have already invoked ${call.name} with these exact parameters. Change strategy.`,
            is_error: true
          });
          continue;
        }
        executedSignatures.add(signature);

        // Enforce Dry-Run Guard for Destructive Actions
        if (this.isDestructiveAction(call.name) && this.dryRunMode) {
          this.auditLog.push({
            step,
            toolName: call.name,
            args: call.input as any,
            isDryRun: true,
            status: 'APPROVED'
          });
          toolResults.push({
            type: 'tool_result',
            tool_use_id: call.id,
            content: `[DRY-RUN SIMULATION]: Action '${call.name}' validated successfully. State modification was bypassed due to dry-run mode.`,
            is_error: false
          });
          continue;
        }

        // Concrete Handler Dispatch
        try {
          const resultPayload = await this.dispatchConcreteTool(call.name, call.input as any);
          this.auditLog.push({
            step,
            toolName: call.name,
            args: call.input as any,
            isDryRun: false,
            status: 'EXECUTED'
          });
          toolResults.push({
            type: 'tool_result',
            tool_use_id: call.id,
            content: JSON.stringify(resultPayload),
            is_error: false
          });
        } catch (err: any) {
          toolResults.push({
            type: 'tool_result',
            tool_use_id: call.id,
            content: `Runtime Error in ${call.name}: ${err.message}`,
            is_error: true
          });
        }
      }

      // Append tool results under user role
      messages.push({ role: 'user', content: toolResults });
    }

    throw new Error(`Agent exceeded maximum execution step budget (${this.maxSteps}) without achieving goal.`);
  }

  private async dispatchConcreteTool(name: string, args: Record<string, any>): Promise<any> {
    // Internal routing table
    if (name === 'inspect_service_pods') {
      return { namespace: args.namespace || 'default', runningPods: 14, unreadyPods: 0 };
    }
    return { status: 'SUCCESS', details: `Tool ${name} executed with args`, inputEcho: args };
  }
}
