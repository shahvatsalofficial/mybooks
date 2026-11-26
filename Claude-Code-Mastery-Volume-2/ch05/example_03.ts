import { z } from "zod";
import crypto from "crypto";

export interface ToolDefinition {
  name: string;
  description: string;
  schema: z.ZodSchema;
  execute: (args: any) => Promise<string>;
}

export interface ReActEngineConfig {
  maxSteps: number;
  maxCostUsd: number;
  costPer1kTokens: number;
}

export class AutonomousReActEngine {
  private tools: Map<string, ToolDefinition> = new Map();
  private stateHistory: string[] = [];
  private totalCost = 0;

  constructor(private config: ReActEngineConfig) {}

  public registerTool(tool: ToolDefinition): void {
    this.tools.set(tool.name, tool);
  }

  /**
   * Executes an autonomous reasoning and action loop to achieve a verified goal.
   */
  public async executeLoop(
    goal: string,
    llmClient: { generateTurn: (history: any[]) => Promise<{ thought: string; action?: { name: string; args: any }; answer?: string }> }
  ): Promise<string> {
    const history: any[] = [
      { role: "system", content: `You are an autonomous software agent. Achieve goal: "${goal}". Verify with tests.` }
    ];

    for (let step = 1; step <= this.config.maxSteps; step++) {
      // 1. Check Financial Circuit Breaker
      if (this.totalCost >= this.config.maxCostUsd) {
        throw new Error(`CIRCUIT_BREAKER: Budget limit exceeded ($${this.totalCost.toFixed(2)} >= $${this.config.maxCostUsd})`);
      }

      // 2. Generate LLM Reasoning & Action
      const turn = await llmClient.generateTurn(history);
      this.totalCost += (800 / 1000) * this.config.costPer1kTokens; // Track token expenditure

      // 3. Check for Task Completion
      if (turn.answer && !turn.action) {
        return turn.answer;
      }

      if (!turn.action) {
        throw new Error("REASONING_ERROR: Model failed to emit an action or a final answer.");
      }

      // 4. Validate Tool Exists
      const tool = this.tools.get(turn.action.name);
      if (!tool) {
        const errorMsg = `ERROR: Tool '${turn.action.name}' does not exist. Approved tools: ${Array.from(this.tools.keys()).join(", ")}`;
        history.push({ role: "system", content: errorMsg });
        continue;
      }

      // 5. Schema Validation Gate
      const validationResult = tool.schema.safeParse(turn.action.args);
      if (!validationResult.success) {
        const errorMsg = `SCHEMA_ERROR: Invalid arguments for '${turn.action.name}': ${validationResult.error.message}`;
        history.push({ role: "system", content: errorMsg });
        continue;
      }

      // 6. Anti-Oscillation Fingerprint Check
      const fingerprint = crypto.createHash("sha256")
        .update(`${turn.action.name}:${JSON.stringify(turn.action.args)}`)
        .digest("hex");
        
      if (this.stateHistory.filter(h => h === fingerprint).length >= 2) {
        throw new Error(`CIRCUIT_BREAKER: Oscillation detected on action '${turn.action.name}'. Loop aborted.`);
      }
      this.stateHistory.push(fingerprint);

      // 7. Execute Action
      let observation: string;
      try {
        observation = await tool.execute(validationResult.data);
      } catch (err: any) {
        observation = `TOOL_EXECUTION_FAILED: ${err.message}`;
      }

      // 8. Truncate Observation (Max 16KB)
      if (observation.length > 16384) {
        observation = observation.slice(0, 16384) + "\n\n... [TRUNCATED TO PRESERVE CONTEXT] ...";
      }

      // 9. Append Step to Trajectory
      history.push({ role: "assistant", content: `Thought: ${turn.thought}\nAction: ${turn.action.name}(${JSON.stringify(turn.action.args)})` });
      history.push({ role: "system", content: `Observation: ${observation}` });
    }

    throw new Error(`CIRCUIT_BREAKER: Maximum iteration ceiling reached (${this.config.maxSteps} steps).`);
  }
}
