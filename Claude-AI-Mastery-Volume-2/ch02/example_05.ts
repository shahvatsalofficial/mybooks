/**
 * Recipe 02.5: Dynamic Tool Schema Registry & Hot-Reloading Engine
 * Author: Vatsal Shah (Opportunity4u Press)
 * License: Apache-2.0
 */

import { z } from 'zod';
import { EventEmitter } from 'node:events';

export interface RegisteredToolDefinition {
  name: string;
  description: string;
  inputSchema: Record<string, any>;
  zodValidator: z.ZodType<any>;
  executor: (args: any) => Promise<any>;
  version: string;
  enabled: boolean;
}

export class DynamicToolRegistry extends EventEmitter {
  private tools: Map<string, RegisteredToolDefinition> = new Map();

  public registerTool(tool: RegisteredToolDefinition): void {
    const isUpdate = this.tools.has(tool.name);
    this.tools.set(tool.name, tool);
    console.log(`[TOOL REGISTRY] Tool '${tool.name}' (v${tool.version}) ${isUpdate ? 'hot-reloaded' : 'registered'}.`);
    this.emit('tools_changed', this.getEnabledTools());
  }

  public deregisterTool(name: string): boolean {
    const deleted = this.tools.delete(name);
    if (deleted) {
      console.log(`[TOOL REGISTRY] Tool '${name}' deregistered.`);
      this.emit('tools_changed', this.getEnabledTools());
    }
    return deleted;
  }

  public getEnabledTools(): Array<{ name: string; description: string; input_schema: Record<string, any> }> {
    return Array.from(this.tools.values())
      .filter((t) => t.enabled)
      .map((t) => ({
        name: t.name,
        description: t.description,
        input_schema: t.inputSchema,
      }));
  }

  public async executeTool(name: string, rawArgs: Record<string, any>): Promise<any> {
    const tool = this.tools.get(name);
    if (!tool) {
      throw new Error(`ToolNotFoundError: Tool '${name}' is not registered in active registry.`);
    }

    if (!tool.enabled) {
      throw new Error(`ToolDisabledError: Tool '${name}' is temporarily disabled by administrative policy.`);
    }

    // 1. Runtime validation with compiled Zod schema
    const parseResult = tool.zodValidator.safeParse(rawArgs);
    if (!parseResult.success) {
      const formattedErrors = parseResult.error.errors.map((e) => `${e.path.join('.')}: ${e.message}`).join('; ');
      throw new Error(`SchemaValidationError: Invalid arguments for tool '${name}': ${formattedErrors}`);
    }

    // 2. Execute business logic with guaranteed type-safe parameters
    return await tool.executor(parseResult.data);
  }
}
