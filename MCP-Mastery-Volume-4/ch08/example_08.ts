import { McpTestHarness } from "./mcp-test-harness.js";
import assert from "assert";

async function runTests() {
  const harness = new McpTestHarness("./dist/index.js", {
    DATABASE_URL: "postgresql://localhost:5432/test"
  });

  console.log("Testing Initialize Handshake...");
  const initOk = await harness.assertInitialize();
  assert.strictEqual(initOk, true, "Initialize handshake failed.");

  console.log("Testing tools/list...");
  const listRes = await harness.sendRequest("tools/list");
  assert(Array.isArray(listRes.result.tools), "tools/list did not return an array.");
  console.log(`Discovered ${listRes.result.tools.length} active tools.`);

  await harness.close();
  console.log("All MCP Integration Tests PASSED!");
}

runTests().catch(console.error);
