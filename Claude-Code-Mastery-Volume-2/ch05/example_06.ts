import { test, expect, describe } from "vitest";
import { AutonomousReActEngine, ToolDefinition } from "./react_engine";
import { z } from "zod";

describe("AutonomousReActEngine State Machine Audits", () => {
  const dummyTool: ToolDefinition = {
    name: "ping",
    description: "Diagnostic ping",
    schema: z.object({ count: z.number().max(5) }),
    execute: async (args) => `PONG ${args.count}`
  };

  test("should halt immediately when financial budget is exhausted", async () => {
    const engine = new AutonomousReActEngine({
      maxSteps: 10,
      maxCostUsd: 0.05,
      costPer1kTokens: 0.03
    });
    engine.registerTool(dummyTool);

    const mockLlm = {
      generateTurn: async () => ({
        thought: "Pinging network...",
        action: { name: "ping", args: { count: 1 } }
      })
    };

    await expect(engine.executeLoop("Test budget ceiling", mockLlm))
      .rejects.toThrow("CIRCUIT_BREAKER: Budget limit exceeded");
  });

  test("should detect and terminate cyclic tool oscillations", async () => {
    const engine = new AutonomousReActEngine({
      maxSteps: 10,
      maxCostUsd: 5.0,
      costPer1kTokens: 0.001
    });
    engine.registerTool(dummyTool);

    // Mock LLM repeatedly emits identical tool call
    const mockLlm = {
      generateTurn: async () => ({
        thought: "Repeating identical action...",
        action: { name: "ping", args: { count: 3 } }
      })
    };

    await expect(engine.executeLoop("Test anti-oscillation", mockLlm))
      .rejects.toThrow("CIRCUIT_BREAKER: Oscillation detected");
  });

  test("should return verified final answer upon successful goal attainment", async () => {
    const engine = new AutonomousReActEngine({
      maxSteps: 5,
      maxCostUsd: 5.0,
      costPer1kTokens: 0.001
    });
    engine.registerTool(dummyTool);

    let turns = 0;
    const mockLlm = {
      generateTurn: async () => {
        turns++;
        if (turns === 1) {
          return { thought: "Running ping check...", action: { name: "ping", args: { count: 1 } } };
        }
        return { thought: "Ping verified.", answer: "Network verified operational." };
      }
    };

    const result = await engine.executeLoop("Verify network", mockLlm);
    expect(result).toBe("Network verified operational.");
  });
});
