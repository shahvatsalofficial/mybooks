/**
 * recipe_8_3_mcp_conformance.test.ts
 * Enterprise CI/CD protocol conformance test suite for MCP servers.
 */

import { describe, it, expect, beforeAll, afterAll } from "vitest";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

describe("MCP Server Protocol Conformance Test Suite", () => {
  let client: Client;
  let transport: StdioClientTransport;

  beforeAll(async () => {
    client = new Client(
      { name: "conformance-runner", version: "1.0.0" },
      { capabilities: {} }
    );

    transport = new StdioClientTransport({
      command: "node",
      args: ["dist/index.js"]
    });

    await client.connect(transport);
  });

  afterAll(async () => {
    await client.close();
  });

  it("should complete initialize handshake and advertise server capabilities", () => {
    const caps = client.getServerCapabilities();
    expect(caps).toBeDefined();
    expect(caps?.tools).toBeDefined();
  });

  it("should expose valid tools adhering to JSON Schema Draft 2020-12", async () => {
    const { tools } = await client.listTools();
    expect(tools.length).toBeGreaterThan(0);

    for (const tool of tools) {
      expect(tool.name).toMatch(/^[a-zA-Z0-9_-]+$/);
      expect(tool.description).toBeDefined();
      expect(tool.inputSchema.type).toBe("object");
      expect(tool.inputSchema.properties).toBeDefined();
    }
  });

  it("should trap invalid arguments and return isError: true without crashing", async () => {
    // Intentionally send invalid payload missing required arguments
    const result = await client.callTool({
      name: "create_or_update_note",
      arguments: {
        title: "" // Invalid: fails min_length=1
      }
    });

    // CRITICAL PROTOCOL ASSERTION: Must return isError: true, NOT throw -32602
    expect(result.isError).toBe(true);
    expect(result.content[0].type).toBe("text");
    expect(result.content[0].text).toContain("Title cannot be blank");
  });
});
